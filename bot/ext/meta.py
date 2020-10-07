import collections
import typing

import discord
from bot.ext import config
from bot.utils import cog, paginators, wrap_in_code
from discord.ext import commands
from discord.utils import get


class Meta(cog.Cog):
    """Commands related to the bot itself"""

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
            configurable = get(config.configurables, name=option.lower())
            if configurable is None:
                raise commands.UserInputError(
                    f"Option {wrap_in_code(option)} not found"
                )

            if new_value:
                await commands.has_guild_permissions(manage_guild=True).predicate(ctx)

                try:
                    parsed_value = config.resolve_value(configurable.type, new_value)
                    await self.cfg.set_value(ctx.guild, configurable, parsed_value)
                except:
                    raise commands.BadArgument(
                        f"Value {wrap_in_code(new_value)} is does not fit"
                        f" expected type {config.type_names[configurable.type]}"
                    )

            value = (
                parsed_value
                if new_value is not None
                else await self.cfg.get_value(ctx.guild, configurable)
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
        paginator = paginators.FieldPaginator(self.bot, base_embed=embed)

        for configurable in config.configurables:
            paginator.add_field(
                name=configurable.name.capitalize(),
                value=configurable.description,
            )

        await paginator.send(target=ctx.channel, owner=ctx.author)

    @commands.command()
    @commands.cooldown(3, 8, commands.BucketType.channel)
    async def about(self, ctx: commands.Context):
        """Gives information about this bot"""

        app_info = await self.bot.application_info()

        embed = discord.Embed(title="About", description=self.bot.description)

        embed.add_field(
            name="Links",
            value="[Support server](https://discohook.app/discord)"
            "\n[Invite link](https://discohook.app/bot)"
            "\n[Source code](https://github.com/discohook/bot)",
            inline=False,
        )

        embed.add_field(
            name="Owner",
            value=f"[{app_info.owner}](https://discord.com/users/{app_info.owner.id})",
            inline=False,
        )

        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(3, 8, commands.BucketType.channel)
    async def invite(self, ctx: commands.Context):
        """Sends the bot invite and support server links"""

        await ctx.send(
            embed=discord.Embed(
                title="Invite",
                description="[Support server](https://discohook.app/discord)"
                "\n[Invite link](https://discohook.app/bot)",
            )
        )

    @commands.command()
    @commands.cooldown(3, 8, commands.BucketType.channel)
    async def data(self, ctx: commands.Context):
        """Manage data stored by Discobot"""

        await ctx.send(
            embed=discord.Embed(
                title="Data management",
                description="As of now, this bot does not store data about you."
                "\nIt does however store data about this server, you can delete"
                " it by kicking me from the server.",
            )
        )


def setup(bot: commands.Bot):
    meta = Meta(bot)
    bot.add_cog(meta)
