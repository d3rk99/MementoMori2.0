from __future__ import annotations

import logging
from pathlib import Path
from typing import Set

from adapters.file_manager import read_lines, write_lines

logger = logging.getLogger(__name__)


class BanlistService:
    def __init__(self, ban_path: Path, whitelist_path: Path) -> None:
        self.ban_path = ban_path
        self.whitelist_path = whitelist_path
        self.banned: Set[str] = set(read_lines(self.ban_path))
        self.whitelist: Set[str] = set(read_lines(self.whitelist_path))
        logger.info(
            "Ban/whitelist loaded",
            extra={"ban_count": len(self.banned), "whitelist_count": len(self.whitelist)},
        )

    def _persist(self) -> None:
        write_lines(self.ban_path, sorted(self.banned))
        write_lines(self.whitelist_path, sorted(self.whitelist))

    def add_to_whitelist_and_ban(self, steam64: str) -> None:
        self.whitelist.add(steam64)
        self.banned.add(steam64)
        self._persist()
        logger.info("User validated and banned until VC join", extra={"steam64": steam64})

    def add_ban(self, steam64: str) -> None:
        if steam64 not in self.banned:
            self.banned.add(steam64)
            self._persist()
            logger.info("User banned", extra={"steam64": steam64})

    def remove_ban(self, steam64: str) -> None:
        if steam64 in self.banned:
            self.banned.remove(steam64)
            self._persist()
            logger.info("User unbanned", extra={"steam64": steam64})

    def is_banned(self, steam64: str) -> bool:
        return steam64 in self.banned
