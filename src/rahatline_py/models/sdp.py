from typing import Any, Dict
from dataclasses import dataclass

@dataclass
class SessionDescription:
    sdp: str
    type: str

    @classmethod
    def Load(cls, data: Dict[str, Any]) -> 'SessionDescription':
        return cls(sdp=data['sdp'], type=data['type'])
