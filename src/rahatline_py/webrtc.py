import asyncio
import logging
from typing import List
from .models.turn_info import TurnInfo
from .models import SessionDescription
from typing import Optional, List, Callable, Dict, Any, Coroutine
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate, MediaStreamTrack, RTCRtpTransceiver
from aiortc.contrib.media import MediaRelay


class RahatLineWebRTCConnection:
    def __init__(self, turns: List[TurnInfo]):
        self._pc = RTCPeerConnection()
        config = {
            "iceServers": [
                {
                    "urls": turn["urls"],
                    "username": turn["username"],
                    "credential": turn["credential"]
                } for turn in turns
            ],
            "iceTransportPolicy": "relay"
        }
        self._pc._configuration = config

        self._pc.createDataChannel('empty')
        
        # self._tracks: List[MediaStreamTrack] = []
        # self.OnRemoveTrack: Optional[Callable[[str, str], None]] = None
        self.OnConnectionStateChanged: Optional[Callable[[str], None]] = None
        self.OnIceCandidate: Optional[Callable[[RTCIceCandidate], None]] = None
        self.OnNewTrack: Callable[[MediaStreamTrack, str, Any], Coroutine[None, None, None]] = None


        loop = asyncio.get_event_loop()
        self.future = loop.create_future()
        
        @self._pc.on("icegatheringstatechange")
        def on_icegatheringstatechange():
            if self.future.done(): return
            if self._pc.iceGatheringState == "complete":
                self.future.set_result(None)
        

        @self._pc.on('track')
        async def on_track(track: MediaStreamTrack):
            await self.OnNewTrack(track)
            # self.OnNewTrack(track)
            # while True:
            #     r = await track.recv()
            #     print(r)
            

        @self._pc.on("connectionstatechange")
        def on_connectionstatechange():
            self.OnConnectionStateChanged(self._pc.connectionState)


    # def Connect(self): self._pc.c



    async def negotiate(self, server_offer: Optional[SessionDescription] = None) -> RTCSessionDescription:
        if server_offer is None:
            return await self._create_offer()
        else:
            return await self._create_answer(RTCSessionDescription(sdp=server_offer.sdp, type=server_offer.type))
    

    def AddTrack(self, track: MediaStreamTrack):
        return self._pc.addTransceiver(track)
    
    def RemoveTrack(self, rtpSender: RTCRtpTransceiver):
        rtpSender.stop()



    async def complete_local_negotiation(self, server_answer: RTCSessionDescription):
        await self._pc.setRemoteDescription(server_answer)

        
    async def _create_offer(self) -> RTCSessionDescription:
        offer = await self._pc.createOffer()
        await self._pc.setLocalDescription(offer)
        
        # Wait for ICE gathering to complete
        if self._pc.iceGatheringState != "complete":
            await self.future
        
        if not self._pc.localDescription:
            raise Exception("Local description is empty")
        
        return self._pc.localDescription
    
    async def _create_answer(self, server_offer: RTCSessionDescription) -> RTCSessionDescription:
        await self._pc.setRemoteDescription(server_offer)
        answer = await self._pc.createAnswer()
        await self._pc.setLocalDescription(answer)
        
        if not self._pc.localDescription:
            raise Exception("Local description is empty")
        
        return self._pc.localDescription
    
        