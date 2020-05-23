import base64
import io
import json

import discord
from discord.ext import commands

from .utils import converter


class Messages(commands.Cog):
    """Message helpers"""

    @commands.command()
    async def link(
        self, ctx: commands.Context, msg: converter.GuildMessageConverter,
    ):
        """Sends a link to recreate a given message in Discohook"""

        msg_data = {}

        if len(msg.content) > 0:
            msg_data["content"] = msg.content

        msg_data["username"] = msg.author.display_name
        msg_data["avatar_url"] = str(msg.author.avatar_url_as(format="webp"))

        embeds = [embed.to_dict() for embed in msg.embeds if embed.type == "rich"]

        for embed in embeds:
            embed.pop("type")

        if len(embeds) > 0:
            msg_data["embeds"] = embeds

        msg_json = json.dumps({"message": msg_data}, separators=(",", ":"))
        msg_b64 = (
            base64.urlsafe_b64encode(msg_json.encode("utf-8"))
            .decode("utf-8")
            .replace("=", "")
        )
        url = f"https://discohook.org/?message={msg_b64}"

        if len(url) > 512:
            await ctx.send(
                embed=discord.Embed(title="URL too long for embed"),
                file=discord.File(io.StringIO(url), filename="url.txt"),
            )
        else:
            await ctx.send(embed=discord.Embed(title="Message", url=url))


def setup(bot):
    bot.add_cog(Messages(bot))
