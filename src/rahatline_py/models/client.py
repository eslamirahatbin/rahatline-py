from typing import Any
from dataclasses import dataclass

@dataclass
class Client:
    id: Any
    muted: Any
    peerConnectionStatus: Any
    payload: Any
    voiceChannels: Any
    microphoneEnabled: Any
    currentVoiceChannel: Any
    addedTracks: Any
    addedTracksLen: Any
    isSystemUser: Any