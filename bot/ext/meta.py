import asyncio
import collections
import itertools
import re
import typing

import discord
from bot.utils import paginators, wrap_in_code
from discord.ext import commands
from discord.utils import get

Configurable = collections.namedtuple(
    "Configurable", ["name", "description", "column", "type"]
)

configurables = [
    Configurable(
        name="prefix",
        description="Prefix specific to server, mention prefix will always work.",
        column="prefix",
        type=str,
    ),
    Configurable(
        name="private",
        description="Make certain sensitive commands private to server moderators.",
        column="commands_private",
        type=bool,
    ),
]

type_names = {str: "text", bool: "boolean", int: "number"}


class Meta(commands.Cog):
    """Commands related to the bot itself"""

    def __init__(self, bot):
        self.bot = bot

    def _resolve_value(self, expected_type, raw_value):
        type_name = type_names[expected_type]
        escaped_value = wrap_in_code(raw_value)

        if expected_type is bool:
            lowered = raw_value.lower()
            if lowered in ("yes", "y", "true", "t", "1", "enable", "on"):
                return True
            elif lowered in ("no", "n", "false", "f", "0", "disable", "off"):
                return False
            else:
                raise commands.BadArgument(
                    f"Value {escaped_value} is not a {type_name}"
                )
        else:
            try:
                return expected_type(raw_value)
            except:
                raise commands.BadArgument(
                    f"Value {escaped_value} is not a {type_name}"
                )

    async def _config_get(self, guild, configurable):
        return await self.bot.db.fetchval(
            """
            SELECT {} FROM guild_config
            WHERE guild_id = $1
            """.format(
                configurable.column
            ),
            guild.id,
        )

    async def _config_set(self, guild, configurable, new_value):
        await self.bot.db.execute(
            """
            UPDATE guild_config
            SET {} = $2
            WHERE guild_id = $1
            """.format(
                configurable.column
            ),
            guild.id,
            new_value,
        )

    @commands.group(invoke_without_command=True)
    @commands.cooldown(3, 8, commands.BucketType.channel)
    @commands.guild_only()
    async def config(
        self,
        ctx: commands.Context,
        option: typing.Optional[str],
        *,
        new_value: typing.Optional[str],
    ):
        """Manages server configuration for bot"""

        command = f"{ctx.prefix}{self.config.qualified_name}"

        if option:
            configurable = get(configurables, name=option.lower())
            if configurable is None:
                raise commands.UserInputError(
                    f"Option {wrap_in_code(option)} not found"
                )

            if new_value:
                await commands.has_guild_permissions(manage_guild=True).predicate(ctx)

                parsed_value = self._resolve_value(configurable.type, new_value)
                await self._config_set(ctx.guild, configurable, parsed_value)

            value = (
                parsed_value
                if new_value is not None
                else await self._config_get(ctx.guild, configurable)
            )
            value = (
                ("yes" if value else "no") if isinstance(value, bool) else str(value)
            )
            value = wrap_in_code(value)

            set_configurable_signature = wrap_in_code(
                f"{command} {configurable.name} <new value>"
            )
            message = (
                f"Option {configurable.name} has been set to {value}."
                if new_value is not None
                else f"Option {configurable.name} is currently set to {value}."
                f"\nUse {set_configurable_signature} to set it."
            )

            await ctx.send(
                embed=discord.Embed(title="Configuration", description=message)
            )
            return

        get_signature = wrap_in_code(f"{command} <option>")
        set_signature = wrap_in_code(f"{command} <option> <new value>")

        embed = discord.Embed(
            title="Configuration",
            description="Command to manage the bot's configuration for a server."
            f"\nTo get the value of an option use {get_signature}."
            f"\nTo set the value of an option use {set_signature}."
            "\nList of options can be found below:",
        )
        embed.set_footer(
            text="Page {current_page}/{total_pages}, "
            "showing option {first_field}..{last_field}/{total_fields}"
        )
        paginator = paginators.FieldPaginator(ctx.bot, base_embed=embed)

        for configurable in configurables:
            paginator.add_field(
                name=configurable.name.capitalize(),
                value=configurable.description,
            )

        await paginator.send(target=ctx.channel, owner=ctx.author)

    @commands.command()
    @commands.cooldown(3, 8, commands.BucketType.channel)
    async def about(self, ctx: commands.Context):
        """Gives information about this bot"""

        delete_data_signature = wrap_in_code(
            f"{ctx.prefix}{self.deletemydata.qualified_name} {self.deletemydata.signature}"
        )

        embed = discord.Embed(title="About", description=self.bot.description)
        embed.add_field(
            name="Privacy and Security",
            value=f"Want your data deleted? Use the {delete_data_signature} command to get more info."
            "\nHave a security issue? Join the support server and DM vivi#1111.",
        )

        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(3, 8, commands.BucketType.channel)
    async def invite(self, ctx: commands.Context):
        """Gives information about this bot"""

        await ctx.send(
            embed=discord.Embed(title="Invite", description=self.bot.description)
        )

    @commands.command()
    @commands.cooldown(3, 8, commands.BucketType.channel)
    async def deletemydata(self, ctx: commands.Context):
        """Gives information on how to delete your data"""

        await ctx.send(
            embed=discord.Embed(
                title="Delete my data",
                description="As of now, this bot stores zero data specific to users."
                "\nIf you are a server owner you can delete data specific to this server by kicking or banning me.",
            )
        )


def setup(bot: commands.Bot):
    meta = Meta(bot)
    bot.add_cog(meta)
