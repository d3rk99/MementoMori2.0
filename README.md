# DeathWatcher Bot

DeathWatcher is a Discord bot built with **discord.py 2.x** to enforce DayZ hardcore rules based on live Detailed Logs (LJSON). It automatically tracks player deaths, manages DayZ `ban.txt` / `whitelist.txt`, and gates server access through Discord voice channels.

## Features
- Tails the newest `dl_YYYYMMDD_HHMMSS.ljson` file from the DayZ Detailed Logs directory and persists the cursor to resume after restarts.
- Detects `PLAYER_DEATH` events, records `aliveSec`, and enforces a configurable dead timer with automatic role swaps and voice disconnections.
- Manages `ban.txt` and `whitelist.txt` with atomic writes and keeps players banned until they enter their assigned private voice channel.
 - Automatic private voice channel provisioning under an online category; channels are cleaned up when empty.
 - Periodic revive task plus admin override detection (granting the Alive role force-revives the user).
 - JSON user database and cache for log offsets.
  - `!validate @discord_member <steam64>` command for admins to add a user to whitelist + ban list until they join their private VC.

## Project layout
```
src/
  bot/death_watcher_bot.py   # Discord bot behavior
  services/                  # User DB + ban/whitelist helpers
  watchers/log_watcher.py    # Robust log tailer with cache persistence
  adapters/file_manager.py   # Atomic file utilities
  models/                    # User and cache dataclasses
  main.py                    # Entrypoint to start the bot
config.example.json          # Copy to config.json and fill in IDs/token
```

## Setup
1. Install Python 3.10+ and create a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `config.example.json` to `config.json` and fill in your bot token, guild/role/channel IDs, and DayZ paths.
4. Ensure the bot has the following Discord intents and permissions:
   - Gateway Intents: **Members**, **Voice States** (Message Content not required).
   - Permissions: Manage Roles, Move Members, Manage Channels, Read/Send Messages in the bot spam channel.
5. Run the bot:
   ```bash
   python -m src.main
   ```

## Configuration notes
- `path_to_logs_directory` should contain DayZ Detailed Logs; the bot always picks the newest `dl_*.ljson` file.
- `userdata_db_path` and `path_to_cache` are JSON files persisted between runs.
- `ban_duration_days` controls how long a user stays dead.
- Set `verbose_logs` to `true` for debug-level logging.

## Test plan (manual)
- [ ] Start the bot with a fresh config and verify it creates `data` directory files.
- [ ] Trigger a `PLAYER_DEATH` line in the newest log file; confirm the user is marked dead, banned, roles swapped, and disconnected.
- [ ] Join the **Click to Join** voice channel as a validated alive user; confirm a private VC is created and ban entry removed.
- [ ] Leave the private VC; confirm the user is re-banned and the empty channel is deleted.
- [ ] Wait past `deadUntil` or grant the Alive role manually; confirm the user is revived, unbanned, and roles swapped back.
