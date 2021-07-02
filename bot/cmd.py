import discord
from discord.ext import commands


class Cog(commands.Cog):
    def __init__(self, bot):
        super().__init__()

        self.bot = bot

    @property
    def loop(self):
        return self.bot.loop

    @property
    def db(self):
        return self.bot.pool

    @property
    def cfg(self):
        return self.bot.get_cog("Config")

    @property
    def session(self):
        return self.bot.session


class Context(commands.Context):
    def __init__(self, **attrs):
        super().__init__(**attrs)

        self.prompt_message = None

    async def send(self, content=None, **kwargs):
        can_read_history = self.channel.permissions_for(self.me).read_message_history

        if "reference" not in kwargs and can_read_history:
            kwargs = dict(kwargs, reference=self.message)

        return await super().send(content, **kwargs)

    async def prompt(
        self,
        content=None,
        *,
        embed=None,
        files=None,
        allowed_mentions=None,
    ):
        if embed.color is discord.Embed.Empty:
            embed.color = 0x58b9ff

        if self.prompt_message:
            try:
                await self.prompt_message.edit(
                    content=content,
                    embed=embed,
                    allowed_mentions=allowed_mentions,
                )
            except discord.NotFound:
                pass
            else:
                return self.prompt_message

        self.prompt_message = await self.send(
            content=content,
            embed=embed,
            files=files,
            allowed_mentions=allowed_mentions,
        )
        return self.prompt_message
