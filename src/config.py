from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class Config:
    token: str
    guild_id: int
    alive_role_id: int
    dead_role_id: int
    admin_role_id: int
    join_vc_id: int
    online_category_id: int
    bot_spam_channel_id: int
    path_to_logs_directory: Path
    userdata_db_path: Path
    path_to_cache: Path
    ban_txt_path: Path
    whitelist_txt_path: Path
    ban_duration_days: int = 3
    verbose_logs: bool = False

    @classmethod
    def load(cls, path: Path) -> "Config":
        data = json.loads(Path(path).read_text())
        return cls(
            token=data["token"],
            guild_id=int(data["guild_id"]),
            alive_role_id=int(data["alive_role_id"]),
            dead_role_id=int(data["dead_role_id"]),
            admin_role_id=int(data["admin_role_id"]),
            join_vc_id=int(data["join_vc_id"]),
            online_category_id=int(data["online_category_id"]),
            bot_spam_channel_id=int(data["bot_spam_channel_id"]),
            path_to_logs_directory=Path(data["path_to_logs_directory"]),
            userdata_db_path=Path(data["userdata_db_path"]),
            path_to_cache=Path(data["path_to_cache"]),
            ban_txt_path=Path(data["ban_txt_path"]),
            whitelist_txt_path=Path(data["whitelist_txt_path"]),
            ban_duration_days=int(data.get("ban_duration_days", 3)),
            verbose_logs=bool(data.get("verbose_logs", False)),
        )

    def ensure_paths(self) -> None:
        self.path_to_logs_directory.mkdir(parents=True, exist_ok=True)
        self.userdata_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.path_to_cache.parent.mkdir(parents=True, exist_ok=True)
        self.ban_txt_path.parent.mkdir(parents=True, exist_ok=True)
        self.whitelist_txt_path.parent.mkdir(parents=True, exist_ok=True)

    def to_sanitized_dict(self) -> Dict[str, Any]:
        result = self.__dict__.copy()
        result["token"] = "***redacted***"
        for key, value in list(result.items()):
            if isinstance(value, Path):
                result[key] = str(value)
        return result
