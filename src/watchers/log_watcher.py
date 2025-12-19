from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Awaitable, Callable, Optional

from adapters.file_manager import read_json, write_json
from models.cache import CacheState

logger = logging.getLogger(__name__)

DeathCallback = Callable[[dict], Awaitable[None]]


class LogWatcher:
    def __init__(self, logs_dir: Path, cache_path: Path, callback: DeathCallback, archive_old: bool = False):
        self.logs_dir = logs_dir
        self.cache_path = cache_path
        self.callback = callback
        self.cache = CacheState.from_dict(read_json(cache_path, {}))
        self.buffer = ""
        self.archive_old = archive_old
        self.running = False

    def _write_cache(self) -> None:
        write_json(self.cache_path, self.cache.to_dict())

    def _latest_log_file(self) -> Optional[Path]:
        files = sorted(self.logs_dir.glob("dl_*.ljson"))
        return files[-1] if files else None

    def _switch_log_if_needed(self) -> None:
        latest = self._latest_log_file()
        if not latest:
            return
        latest_name = latest.name
        if self.cache.activeLogFile != latest_name:
            logger.info("Switching to latest log file", extra={"file": latest_name})
            self.cache.activeLogFile = latest_name
            self.cache.byteOffset = 0
            self.buffer = ""
            if self.archive_old:
                for f in self.logs_dir.glob("dl_*.ljson"):
                    if f.name != latest_name:
                        try:
                            f.unlink()
                        except OSError:
                            logger.warning("Failed to remove old log", extra={"file": f.name})

    async def run(self) -> None:
        self.running = True
        while self.running:
            self._switch_log_if_needed()
            if not self.cache.activeLogFile:
                await asyncio.sleep(2)
                continue
            log_path = self.logs_dir / self.cache.activeLogFile
            await self._tail_file(log_path)
            await asyncio.sleep(1)

    async def _tail_file(self, log_path: Path) -> None:
        if not log_path.exists():
            return
        try:
            with log_path.open("r", encoding="utf-8") as f:
                f.seek(self.cache.byteOffset)
                data = f.read()
                if not data:
                    return
                self.cache.byteOffset = f.tell()
        except OSError:
            logger.exception("Failed reading log file", extra={"path": str(log_path)})
            return

        self.buffer += data
        lines = self.buffer.split("\n")
        self.buffer = lines.pop()  # last partial line kept
        for line in lines:
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                logger.warning("Skipping malformed line", extra={"line": line[:80]})
                continue
            await self._handle_event(payload)
        self._write_cache()

    async def _handle_event(self, payload: dict) -> None:
        event = payload.get("event")
        if event != "PLAYER_DEATH":
            return
        await self.callback(payload)
        ts = payload.get("ts")
        if ts:
            self.cache.lastSeenTs = ts
