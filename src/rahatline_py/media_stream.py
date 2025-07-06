from typing import Optional
from av.frame import Frame
from av.packet import Packet
from .models import Client
from aiortc import MediaStreamTrack

class RlMediaStreamTrack(MediaStreamTrack):
    def __init__(self):
        super().__init__()
        self._track  = None
        self._client = None
    
    @staticmethod
    def Init(track: MediaStreamTrack, client: Client = None)->'RlMediaStreamTrack':
        self = RlMediaStreamTrack()
        self._track = track
        self._client = client
        return self

    @property
    def Client(self)-> Client|None: self._client

    async def read(self)->Frame | Packet: return await self._track.recv()

    async def recv(self): 
        pass