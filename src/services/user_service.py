from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Optional

from adapters.file_manager import read_json, write_json
from models.user import UserRecord

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.users: Dict[str, UserRecord] = {}
        self._load()

    def _load(self) -> None:
        payload = read_json(self.path, {})
        self.users = {k: UserRecord.from_dict(v) for k, v in payload.items()}
        logger.info("User DB loaded", extra={"count": len(self.users)})

    def save(self) -> None:
        write_json(self.path, {k: v.to_dict() for k, v in self.users.items()})
        logger.debug("User DB saved", extra={"count": len(self.users)})

    def get_by_discord(self, discord_id: int) -> Optional[UserRecord]:
        for user in self.users.values():
            if user.discordId == discord_id:
                return user
        return None

    def ensure_user(self, steam64: str, discord_id: int) -> UserRecord:
        if steam64 not in self.users:
            self.users[steam64] = UserRecord(steam64=steam64, discordId=discord_id)
        return self.users[steam64]

    def mark_validated(self, steam64: str, discord_id: int) -> UserRecord:
        user = self.ensure_user(steam64, discord_id)
        user.validatedAt = datetime.now(timezone.utc).isoformat()
        return user

    def mark_death(self, steam64: str, death_ts: str, alive_sec: Optional[int], ban_duration_days: int) -> Optional[UserRecord]:
        user = self.users.get(steam64)
        if not user:
            logger.warning("Death event for unknown user", extra={"steam64": steam64})
            return None
        user.isDead = True
        user.deadUntil = (datetime.now(timezone.utc) + timedelta(days=ban_duration_days)).isoformat()
        user.lastDeathAt = death_ts
        user.lastAliveSec = alive_sec
        return user

    def mark_revive(self, steam64: str) -> Optional[UserRecord]:
        user = self.users.get(steam64)
        if not user:
            return None
        user.isDead = False
        user.deadUntil = None
        return user
