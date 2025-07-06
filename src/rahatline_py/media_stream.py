from .models import Client
from aiortc import MediaStreamTrack

class RlMediaStreamTrack(MediaStreamTrack):
    def __init__(self, track: MediaStreamTrack, client: Client = None):
        super().__init__()
        self._track = track
        self._client = client
    
    @property
    def Client(self)-> Client|None: self._client


    async def recv(self):
        data = await self._track.recv()
