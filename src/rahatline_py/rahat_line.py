import jwt
import asyncio
import logging
from .models import *
from typing import Optional, List, Callable
from .ws_signaling import WebSocketSignaling
from .webrtc import RahatLineWebRTCConnection
from aiortc import RTCIceCandidate, MediaStreamTrack
from .completion_source import FutureCompletionSource

class RahatLine:

    def __init__(self, signaling: WebSocketSignaling):
        self._signaling = signaling

        self._my_id: str = ""
        self._signaling = signaling
        # self._peer_connection: Optional[RTCPeerConnection] = None
        self._connection_state: str = "new"
        # self._media_streams: List[RlMediaStream] = []
        self._connect_to_peer_promise = FutureCompletionSource()

        # Event handlers
        self.client_leave: Optional[Callable[[Client], None]] = None
        self.new_client_connected: Optional[Callable[[Client], None]] = None
        # self.on_new_audio_stream: Optional[Callable[[RlAudioStream], None]] = None
        # self.on_new_video_stream: Optional[Callable[[RlVideoStream], None]] = None
        # self.on_video_stream_closed: Optional[Callable[[RlVideoStream], None]] = None
        # self.on_audio_stream_closed: Optional[Callable[[RlAudioStream], None]] = None
        self.on_connection_state_changed: Optional[Callable[[str], None]] = None

        self._bootstrap_signaling(signaling)


    @staticmethod
    def Initialize(address: str, port: int, roomId: str, jwt_secret: str, protocol = 'ws', path: str = "/ws", systemId: str = 'python-agent')->'RahatLine':
        token = jwt.encode({"roomId": roomId,"isSystem": True,"clientPayload": systemId,}, jwt_secret, "HS256")

        ws = WebSocketSignaling(address, port, token, path, protocol)
        return RahatLine(ws)
    
    async def Connect(self)-> str:
        try:
            info = await self._signaling.Connect()
            self._connect_to_peer_promise = FutureCompletionSource()
            self._bootstrap_peer_connection(info)
            
            await self._start_local_negotiation()
            await self._connect_to_peer_promise.Promise
            
            self._my_id = info.id
            return info.id
        except Exception as e:
            logging.error(f"Connection error: {e}")
            raise
    
    def close(self):
        if self._peer_connection:
            asyncio.create_task(self._peer_connection.close())
        if self._signaling:
            self._signaling.close()

    async def _start_local_negotiation(self):
        sdp = await self._peer_connection.negotiate()
        await self._signaling.SendMyOffer(SessionDescription(sdp.sdp, sdp.type))

    async def _on_ice_candidate(self, ice: RTCIceCandidate):
        await self._signaling.SendMyIceCandidate(ice)

    def _on_new_track(self, stream: MediaStreamTrack):
        if "_" not in stream.id:
            return
            
        client_id = stream.id.split("_")[0]
        client = next((c for c in self._signaling.clients if c.id == client_id), None)
        if not client:
            return
        


    def _on_connection_state_changed(self, state: str):
        self._connection_state = state
        
        if not self._connect_to_peer_promise.Promise.done():
            if state == "connected":
                self._connect_to_peer_promise.Resolve(None)
            elif state != "connecting":
                self._connect_to_peer_promise.Reject("failed to connect")
                
        if self.on_connection_state_changed:
            self.on_connection_state_changed(state)

    async def _on_server_offer(self, sdp: SessionDescription):
        offer = SessionDescription(sdp.sdp, sdp.type)
        answer = await self._peer_connection.negotiate(offer)
        await self._signaling.SendMyAnswer(SessionDescription(answer.sdp, answer.type))

    async def _on_server_answer(self, answer: SessionDescription):
        await self._peer_connection.complete_local_negotiation(SessionDescription(answer.sdp, answer.type))

    def _bootstrap_signaling(self, signaling):
        signaling.OnNewClientJoined = lambda c: (
            self.new_client_connected(c) 
            if self.new_client_connected and self.my_id and c.id != self.my_id 
            else None
        )
        
        signaling.OnClientLeave = lambda c: (
            self.client_leave(c) 
            if self.client_leave 
            else None
        )
        
        signaling.OnServerSendOffer = lambda sdp: (
            asyncio.create_task(self._on_server_offer(sdp)))
        
        signaling.OnServerSendAnswer = lambda answer: (
            asyncio.create_task(self._on_server_answer(answer)))

    def _bootstrap_peer_connection(self, info: ClientInfo):
        self._peer_connection = RahatLineWebRTCConnection(info.turn)
        
        self._peer_connection.OnIceCandidate = lambda ice: self._on_ice_candidate(ice)
        self._peer_connection.OnConnectionStateChanged = lambda s: self._on_connection_state_changed(s)
        self._peer_connection.OnNewTrack = lambda stream: self._on_new_track(stream)




