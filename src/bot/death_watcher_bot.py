from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

import discord
from discord.ext import commands, tasks

from ..config import Config
from ..services.user_service import UserService
from ..services.banlist_service import BanlistService
from ..watchers.log_watcher import LogWatcher

logger = logging.getLogger(__name__)


class DeathWatcherBot(commands.Bot):
    def __init__(self, config: Config):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = False
        intents.voice_states = True
        super().__init__(command_prefix="!", intents=intents)
        self.config = config
        self.user_service = UserService(config.userdata_db_path)
        self.banlist_service = BanlistService(config.ban_txt_path, config.whitelist_txt_path)
        self.log_watcher = LogWatcher(
            config.path_to_logs_directory, config.path_to_cache, self._on_death_event
        )
        self.bg_task = None
        self.add_command(self.validate_user)

    async def setup_hook(self) -> None:
        self.bg_task = asyncio.create_task(self.log_watcher.run())
        self.revive_task.start()
        logger.info("Bot setup complete", extra=self.config.to_sanitized_dict())

    async def close(self) -> None:
        if self.bg_task:
            self.log_watcher.running = False
            self.bg_task.cancel()
        await super().close()

    async def on_ready(self):
        logger.info("Bot connected", extra={"user": str(self.user)})

    async def _on_death_event(self, payload: dict) -> None:
        player = payload.get("player", {})
        steam64 = str(player.get("steamId"))
        alive_sec = player.get("aliveSec")
        death_ts = payload.get("ts")
        user = self.user_service.mark_death(steam64, death_ts, alive_sec, self.config.ban_duration_days)
        if not user:
            return
        self.user_service.save()
        self.banlist_service.add_ban(steam64)

        member = await self._fetch_member(user.discordId)
        if not member:
            return
        await self._swap_roles_on_death(member)
        await member.edit(voice_channel=None, reason="DayZ death enforcement")
        await self._log_to_spam(f"{member.mention} died in DayZ. Steam64={steam64}")

    async def _fetch_member(self, discord_id: int) -> Optional[discord.Member]:
        guild = self.get_guild(self.config.guild_id)
        if not guild:
            try:
                guild = await self.fetch_guild(self.config.guild_id)
            except discord.HTTPException:
                return None
        return guild.get_member(discord_id) or await guild.fetch_member(discord_id)

    async def _swap_roles_on_death(self, member: discord.Member) -> None:
        alive_role = member.guild.get_role(self.config.alive_role_id)
        dead_role = member.guild.get_role(self.config.dead_role_id)
        if alive_role:
            await member.remove_roles(alive_role, reason="Death state")
        if dead_role and dead_role not in member.roles:
            await member.add_roles(dead_role, reason="Death state")

    async def _swap_roles_on_revive(self, member: discord.Member) -> None:
        alive_role = member.guild.get_role(self.config.alive_role_id)
        dead_role = member.guild.get_role(self.config.dead_role_id)
        if dead_role:
            await member.remove_roles(dead_role, reason="Revived")
        if alive_role and alive_role not in member.roles:
            await member.add_roles(alive_role, reason="Revived")

    async def _log_to_spam(self, message: str) -> None:
        channel = self.get_channel(self.config.bot_spam_channel_id)
        if channel:
            await channel.send(message)

    @commands.command(name="validate")
    async def validate_user(self, ctx: commands.Context, member: discord.Member, steam64: str):
        if not any(role.id == self.config.admin_role_id for role in ctx.author.roles):
            await ctx.reply("You do not have permission to validate users.")
            return
        user = self.user_service.mark_validated(steam64, member.id)
        self.user_service.save()
        self.banlist_service.add_to_whitelist_and_ban(steam64)
        await ctx.reply(f"Validated {member.mention} with steam64={steam64}. Added to whitelist and banned until VC join.")

    async def on_member_update(self, before: discord.Member, after: discord.Member):
        # Admin override via Alive role grant
        before_alive = self.config.alive_role_id in [r.id for r in before.roles]
        after_alive = self.config.alive_role_id in [r.id for r in after.roles]
        if after_alive and not before_alive:
            user = self.user_service.get_by_discord(after.id)
            if user and user.isDead:
                self.user_service.mark_revive(user.steam64)
                self.user_service.save()
                self.banlist_service.remove_ban(user.steam64)
                await self._swap_roles_on_revive(after)
                await self._log_to_spam(f"{after.mention} revived by admin override")

    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        user = self.user_service.get_by_discord(member.id)
        if not user or not user.validatedAt:
            return

        join_channel = self.config.join_vc_id
        # Joining click-to-join
        if after.channel and after.channel.id == join_channel:
            if user.isDead and user.deadUntil:
                dead_until = datetime.fromisoformat(user.deadUntil)
                if dead_until > datetime.now(timezone.utc):
                    await self._log_to_spam(
                        f"{member.mention} attempted to join while dead until {dead_until.isoformat()}"
                    )
                    return
            private_channel = await self._get_or_create_private_vc(member, user)
            await member.move_to(private_channel, reason="DayZ join flow")
            self.banlist_service.remove_ban(user.steam64)
            return

        # Leaving private VC
        if before.channel and user.privateVcId and before.channel.id == user.privateVcId:
            if not after.channel or after.channel.id != join_channel:
                self.banlist_service.add_ban(user.steam64)
                if before.channel and len(before.channel.members) == 0:
                    await before.channel.delete(reason="Private VC cleanup")
                    user.privateVcId = None
                    self.user_service.save()

    async def _get_or_create_private_vc(self, member: discord.Member, user) -> discord.VoiceChannel:
        guild = member.guild
        channel = None
        if user.privateVcId:
            channel = guild.get_channel(user.privateVcId)
        if channel is None:
            category = guild.get_channel(self.config.online_category_id)
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(connect=False, view_channel=False),
                member: discord.PermissionOverwrite(connect=True, view_channel=True, speak=True),
            }
            channel = await guild.create_voice_channel(
                name=f"{member.id}",
                category=category,
                overwrites=overwrites,
                reason="DayZ private VC",
            )
            user.privateVcId = channel.id
            self.user_service.save()
        return channel

    @tasks.loop(minutes=1)
    async def revive_task(self):
        now = datetime.now(timezone.utc)
        for user in list(self.user_service.users.values()):
            if user.isDead and user.deadUntil:
                try:
                    dead_until = datetime.fromisoformat(user.deadUntil)
                except ValueError:
                    continue
                if dead_until <= now:
                    user.isDead = False
                    user.deadUntil = None
                    self.user_service.save()
                    self.banlist_service.remove_ban(user.steam64)
                    member = await self._fetch_member(user.discordId)
                    if member:
                        await self._swap_roles_on_revive(member)
                        await self._log_to_spam(f"{member.mention} revived (timer)")

    @revive_task.before_loop
    async def before_revive_task(self):
        await self.wait_until_ready()


async def run_bot(config: Config):
    logging.basicConfig(
        level=logging.DEBUG if config.verbose_logs else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )
    bot = DeathWatcherBot(config)
    await bot.start(config.token)
