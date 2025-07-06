from typing import List
from .turn_info import TurnInfo
from dataclasses import dataclass

@dataclass
class ClientInfo: 
    id: str
    bitrate: int
    channels: int
    turn: List[TurnInfo]