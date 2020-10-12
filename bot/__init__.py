import re

import aiohttp
import discord
from discord.ext import commands
from discord.utils import get

from bot.ext import config
from bot.utils import wrap_in_code

initial_extensions = (
    "jishaku",
    "bot.ext.config",
    "bot.ext.meta",
    "bot.ext.help",
    "bot.ext.errors",
    "bot.ext.markdown",
    "bot.ext.utilities",
    "bot.ext.webhooks",
    "bot.ext.reactions",
)


class Bot(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(
            command_prefix=self.get_prefix_list,
            description="Discohook's official bot.",
            help_command=None,
            activity=discord.Game(name="discohook.app | d.help"),
            allowed_mentions=discord.AllowedMentions.none(),
            intents=discord.Intents(
                guilds=True,
                messages=True,
                emojis=True,
                reactions=True,
            ),
            member_cache_flags=discord.MemberCacheFlags.none(),
            max_messages=None,
            guild_subscriptions=False,
        )

        for extension in initial_extensions:
            self.load_extension(extension)

    async def get_prefix_list(self, bot, message):
        cfg = self.get_cog("Config")

        prefix = (
            await cfg.get_value(message.guild, get(config.configurables, name="prefix"))
            if message.guild
            else "d."
        )

        return (
            f"<@!{bot.user.id}> ",
            f"<@{bot.user.id}> ",
            f"{prefix} ",
            prefix,
        )

    async def start(self, *args, **kwargs):
        self.session = aiohttp.ClientSession()
        await super().start(*args, **kwargs)

    async def close(self):
        await self.session.close()
        await super().close()

    async def on_ready(self):
        print(f"Ready as {self.user} ({self.user.id})")

    async def on_message(self, message):
        if message.author.bot:
            return

        cfg = self.get_cog("Config")

        if re.fullmatch(rf"<@!?{self.user.id}>", message.content):
            embed = discord.Embed(title="Prefix", description="My prefix is `d.`")

            if message.guild:
                prefix = await cfg.get_value(
                    message.guild, get(config.configurables, name="prefix")
                )
                embed.description = f"My prefix is {wrap_in_code(prefix)}"

            await message.channel.send(embed=embed)

        await self.process_commands(message)

    async def on_error(self, event, *args, **kwargs):
        errors = self.get_cog("Errors")
        if errors:
            await errors.on_error(event, *args, **kwargs)
