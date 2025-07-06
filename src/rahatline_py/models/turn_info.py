from typing import List
from dataclasses import dataclass

@dataclass
class TurnInfo:
    username: str
    credential: str
    urls: List[str]