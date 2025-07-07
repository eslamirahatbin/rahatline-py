import asyncio
import numpy as np
import whisper
import noisereduce as nr
import soundfile as sf
from av.audio.frame import AudioFrame
import librosa
from threading import Thread
from queue import Queue

import sys
import os

# اضافه کردن مسیر بالایی به path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from aiortc import MediaStreamTrack
from rahatline_py import RahatLine, RlMediaStreamTrack

model = whisper.load_model("turbo", in_memory=True, device='cuda').to('cuda')



# صف برای فریم‌های آماده ترجمه
transcription_queue = Queue()

# تنظیمات
duration_seconds = 5
sample_rate = 48000
channels = 2
collected = []
collected_samples = 0

def collect_and_enqueue_for_transcription(frame):
    global collected_samples

    raw = frame.to_ndarray().flatten()
    try:
        samples = raw.reshape(-1, channels).astype(np.float32) / 32768.0
    except ValueError:
        print("[!] خطا در تبدیل فریم به numpy")
        return

    collected.append(samples)
    collected_samples += samples.shape[0]

    if collected_samples >= duration_seconds * sample_rate:
        audio = np.concatenate(collected, axis=0)
        mono = np.mean(audio, axis=1)
        transcription_queue.put(mono.copy())  # ← بنداز تو صف

        collected.clear()
        collected_samples = 0

def transcription_worker():
    while True:
        mono = transcription_queue.get()
        if mono is None:
            break
        try:
            resampled = librosa.resample(mono, orig_sr=sample_rate, target_sr=16000)
            result = model.transcribe(resampled, beam_size=10, temperature=0.3, language="fa")
            print("📝 نتیجه:", result["text"])
        except Exception as e:
            print("[!] خطا در whisper:", e)

# راه‌اندازی ترد جداگانه
thread = Thread(target=transcription_worker, daemon=True)
thread.start()


ROOM_ID = '1'
JWT_SECRET = 'Key-Must-Be-at-least-32-bytes-in-length!'
# model = whisper.load_model("medium").to('cuda')

async def main():
    conn = RahatLine.Initialize('178.252.132.186', 8080, ROOM_ID, JWT_SECRET)

    async def track(s: MediaStreamTrack):
        while True:
            frame = await s.recv()
            collect_and_enqueue_for_transcription(frame)


    conn.on_new_stream = lambda s: track(s)

    id = await conn.Connect()
    print(id)

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt: pass

asyncio.run(main())