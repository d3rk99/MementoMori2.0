import asyncio
import logging
from pathlib import Path

from config import Config
from bot.death_watcher_bot import run_bot


def main():
    config_path = Path("config.json")
    config = Config.load(config_path)
    config.ensure_paths()
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_bot(config))


if __name__ == "__main__":
    main()
