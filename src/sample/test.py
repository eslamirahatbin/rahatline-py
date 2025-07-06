import asyncio
from aiortc import MediaStreamTrack
from rahatline_py import RahatLine, RlMediaStreamTrack



ROOM_ID = '1'
JWT_SECRET = 'Key-Must-Be-at-least-32-bytes-in-length!'

async def main():
    conn = RahatLine.Initialize('localhost', 8080, ROOM_ID, JWT_SECRET)

    async def track(s: MediaStreamTrack):
        while True:
            r = await s.recv()
            print(r)

    conn.on_new_stream = lambda s: track(s)

    id = await conn.Connect()
    print(id)

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt: pass

asyncio.run(main())