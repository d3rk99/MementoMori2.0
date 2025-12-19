from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class UserRecord:
    steam64: str
    discordId: int
    validatedAt: Optional[str] = None
    isDead: bool = False
    deadUntil: Optional[str] = None
    lastAliveSec: Optional[int] = None
    lastDeathAt: Optional[str] = None
    privateVcId: Optional[int] = None
    lastVoiceState: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "UserRecord":
        return cls(
            steam64=str(data["steam64"]),
            discordId=int(data["discordId"]),
            validatedAt=data.get("validatedAt"),
            isDead=bool(data.get("isDead", False)),
            deadUntil=data.get("deadUntil"),
            lastAliveSec=data.get("lastAliveSec"),
            lastDeathAt=data.get("lastDeathAt"),
            privateVcId=data.get("privateVcId"),
            lastVoiceState=data.get("lastVoiceState"),
        )

    def to_dict(self) -> dict:
        return {
            "steam64": self.steam64,
            "discordId": self.discordId,
            "validatedAt": self.validatedAt,
            "isDead": self.isDead,
            "deadUntil": self.deadUntil,
            "lastAliveSec": self.lastAliveSec,
            "lastDeathAt": self.lastDeathAt,
            "privateVcId": self.privateVcId,
            "lastVoiceState": self.lastVoiceState,
        }
