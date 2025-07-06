import json
import asyncio
import logging
import websockets
from .models import *
from .completion_source import FutureCompletionSource
from typing import  Optional, List, Callable, Dict, Any


class WebSocketSignaling: 
    def __init__(self, address: str, port: int, token: str, url: str, protocol: str):
        self._clients_lock = asyncio.Lock()
        token_query = f"&token={token}" if "?" in url else f"?token={token}"
        self._url = f"{protocol}://{address}{f':{port}' if port not in [443, 80] else ''}{url}{token_query}"
        
        self._ws_connection = None

        self.OnCloseConnection: Optional[Callable[[], None]] = None
        self.OnClientLeave: Optional[Callable[[Client], None]] = None
        self.OnNewClientJoined: Optional[Callable[[Client], None]] = None
        self.OnServerSendOffer: Optional[Callable[[SessionDescription], None]] = None
        self.OnJoinedInRoom: Optional[Callable[[NewClientJoinedToRoom], None]] = None
        self.OnServerSendAnswer: Optional[Callable[[SessionDescription], None]] = None
        self.OnClientChangeMicrophoneStatus: Optional[Callable[[bool, Client], None]] = None
        

    async def Connect(self) -> ClientInfo:
        try:
            self._ws_connection = await websockets.connect(self._url)
            self._connection_promise_source = FutureCompletionSource()
            asyncio.create_task(self._listen_for_messages())
            
            return await self._connection_promise_source.Promise
        except Exception as e:
            if self._connection_promise_source:
                self._connection_promise_source.Reject(str(e))
            raise

    def Close(self):
        self._ws_connection.close()

        
    async def _listen_for_messages(self) -> None:
        try:
            async for message in self._ws_connection:
                await self._on_message(message)
        except websockets.exceptions.ConnectionClosed:
            if self.OnCloseConnection:
                self.OnCloseConnection()
    
    async def _on_message(self, message: str) -> None:
        try:
            model = MessageModel(**json.loads(message))
            
            if model.issue == "client_id":
                await self._on_websocket_client_info_event(model.value)
            elif model.issue == "server_answer" and self.OnServerSendAnswer:
                self.OnServerSendAnswer(SessionDescription.Load(model.value))
            elif model.issue == "server_offer" and self.OnServerSendOffer:
                self.OnServerSendOffer(SessionDescription.Load(model.value))
            elif model.issue == "new_client":
                await self._on_websocket_new_client_joined_event(model.value)
            elif model.issue == "leave_client":
                await self._on_websocket_client_leave_event(model.value)
            elif model.issue == "join_room":
                await self._join_to_room_completed(model.value)
        except Exception as e:
            logging.error(f"Error processing message: {e}")


            
    async def SendMyOffer(self, sdp: SessionDescription) -> None:
        msg = MessageModel(issue="my_offer", value=sdp.__dict__)
        await self._send_message(msg)
    
    async def SendMyAnswer(self, sdp: SessionDescription) -> None:
        msg = MessageModel(issue="my_answer", value=sdp.__dict__)
        await self._send_message(msg)
    
    async def SendMyIceCandidate(self, ice: Dict[str, Any]) -> None:
        msg = MessageModel(
            issue="ice",
            value={
                "sdp": ice.get("candidate"),
                "sdpMid": ice.get("sdpMid"),
                "sdpMLineIndex": ice.get("sdpMLineIndex")
            }
        )
        await self._send_message(msg)
    
    async def _listen_for_messages(self) -> None:
        try:
            async for message in self._ws_connection:
                await self._on_message(message)
        except websockets.exceptions.ConnectionClosed:
            if self.OnCloseConnection:
                self.OnCloseConnection()


    async def _on_websocket_client_info_event(self, info: Dict[str, Any]) -> None:
        self._client_info = ClientInfo(**info)
    
    async def _on_websocket_new_client_joined_event(self, client_data: Dict[str, Any]) -> None:
        async with self._clients_lock:
            client = Client(**client_data)
            self._clients.append(client)
        
        if self.OnNewClientJoined:
            self.OnNewClientJoined(client)
    
    async def _on_websocket_client_leave_event(self, client_data: Dict[str, Any]) -> None:
        async with self._clients_lock:
            client = next((c for c in self._clients if c.id == client_data["id"]), None)
            if client:
                self._clients = [c for c in self._clients if c.id != client_data["id"]]
        
        if client and self.OnClientLeave:
            self.OnClientLeave(client)
    
    async def _join_to_room_completed(self, room_data: Dict[str, Any]) -> None:
        if self._connection_promise_source:
            async with self._clients_lock:
                self._clients = [Client(**c) for c in room_data.get("clients", [])]
            
            if self._client_info and self._connection_promise_source:
                self._connection_promise_source.Resolve(self._client_info)
        else:
            raise Exception("Connection promise is null or undefined.")
    
    async def _send_message(self, msg: MessageModel) -> None:
        if self._ws_connection:
            await self._ws_connection.send(json.dumps(msg.__dict__))