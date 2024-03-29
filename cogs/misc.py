from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from utils import Bot, GuildContext


class Misc(commands.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @commands.command()
    async def ping(self, ctx: GuildContext) -> None:
        """Returns the bots ping"""
        await ctx.send(f"Pong! `**{round(self.bot.latency * 1000)}**`")

    @commands.command()
    async def github(self, ctx: GuildContext) -> None:
        """Returns the bots github"""
        await ctx.send("<https://github.com/ImVaskel/diaranks>")

    @commands.command()
    async def uptime(self, ctx: GuildContext) -> None:
        """Returns the uptime in a fancy discord format"""
        await ctx.send(discord.utils.format_dt(self.bot.start_time, style="R"))


async def setup(bot: Bot) -> None:
    await bot.add_cog(Misc(bot))
