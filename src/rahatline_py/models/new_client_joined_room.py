from typing import Any
from dataclasses import dataclass

@dataclass
class NewClientJoinedToRoom:
    id: str
    clients: Any