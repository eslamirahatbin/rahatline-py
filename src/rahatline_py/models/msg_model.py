from typing import Any
from dataclasses import dataclass

@dataclass
class MessageModel:
    issue: str
    value: Any