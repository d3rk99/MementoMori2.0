from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class CacheState:
    activeLogFile: Optional[str] = None
    byteOffset: int = 0
    lastSeenTs: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "CacheState":
        return cls(
            activeLogFile=data.get("activeLogFile"),
            byteOffset=int(data.get("byteOffset", 0)),
            lastSeenTs=data.get("lastSeenTs"),
        )

    def to_dict(self) -> dict:
        return {
            "activeLogFile": self.activeLogFile,
            "byteOffset": self.byteOffset,
            "lastSeenTs": self.lastSeenTs,
        }
