from datetime import datetime
import logging
import operator
from typing import TYPE_CHECKING, Any, Dict, List, Union, Optional

import asyncpg
import discord
import yaml
from discord.ext import commands
from discord.ext.commands.errors import ExtensionError

from .config import Config


class Bot(commands.Bot):
    if TYPE_CHECKING:
        owner_ids: list[int]
        db: asyncpg.Pool

    def __init__(self) -> None:
        with open("./config.yaml") as fs:
            self.config: Config = yaml.load(fs, Loader=yaml.Loader)

        self.logger = logging.getLogger(__name__)
        self.start_time = datetime.now()

        activity = self.config["bot"]["activity"]

        if activity["type"] == "gaming":
            activity = discord.Game(name=activity["text"])
        else:
            activity = discord.Activity(
                type=getattr(
                    discord.ActivityType,
                    activity["type"],
                    discord.ActivityType.watching,
                ),
                name=activity["text"],
            )

        super().__init__(
            **self.config.get("bot").get("config"),
            activity=activity,
            allowed_mentions=discord.AllowedMentions.none(),
            intents=discord.Intents.all(),
        )

        self.roles: Dict[int, int] = {}  # Level, Role ID
        self.xp: Dict[int, int] = {}  # User ID, XP
        self.blacklist: List[int] = []  # list of blacklisted channel ids

        self._configure_logging()

        self.error_color = discord.Color.red()

    async def _ainit(self) -> None:
        rows = await self.db.fetch("SELECT * FROM levels")
        for row in rows:
            self.xp[row["id"]] = row["xp"]

        rows = await self.db.fetch("SELECT * FROM roles")
        for row in rows:
            self.roles[row["level"]] = row["id"]

        rows = await self.db.fetch("SELECT * FROM blacklist")
        for row in rows:
            self.blacklist.append(row["id"])

    async def _load_extensions(self) -> None:
        for extension in self.config["bot"]["extensions"]:
            try:
                await self.load_extension(extension)
                self.logger.info(f"Loaded extension {extension}")
            except ExtensionError as e:
                self.logger.error(
                    f"Failed to load extension {extension} \n{e}", exc_info=True
                )

    async def setup_hook(self) -> None:
        await self._ainit()
        await self._load_extensions()

    def _configure_logging(self) -> None:
        config = self.config["bot"]["logging"]

        logger = logging.getLogger()
        logger.setLevel(getattr(logging, config["level"], logging.INFO))
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(config["format"]))
        logger.addHandler(handler)

    def run(self, token=None) -> None:
        return super().run(token or self.config["bot"]["token"])

    async def start(self, token=None) -> None:
        return await super().start(token or self.config["bot"]["token"])

    async def on_message(self, message: discord.Message) -> None:
        if message.guild is None or message.author.bot:
            return

        return await super().on_message(message)

    def get_sorted_leaderboard(self) -> list[tuple[int, int]]:
        return sorted(self.xp.items(), key=operator.itemgetter(1), reverse=True)

    def get_user_position(self, user: Union[int, discord.User]) -> int:
        if isinstance(user, discord.User):
            user = user.id

        leaderboard = self.get_sorted_leaderboard()

        for index, entry in enumerate(leaderboard, start=1):
            if entry[0] == user:
                return index
        else:
            return 0
