import math
import sys
import traceback

import discord
from bot.utils import cog, wrap_in_code
from discord.ext import commands
from discord.utils import escape_markdown

ignored_errors = [
    commands.CommandNotFound,
    commands.DisabledCommand,
    commands.NotOwner,
]

error_types = [
    (
        commands.MissingRequiredArgument,
        "Missing argument",
        lambda e: f"The {wrap_in_code(e.param.name)} argument is required, please read help for more info.",
    ),
    (
        commands.TooManyArguments,
        "Too many arguments",
        "Too many arguments were provided, please read help for more info.",
    ),
    (
        commands.MessageNotFound,
        "Message not found",
        lambda e: f"Could not find message for {wrap_in_code(e.argument)}.",
    ),
    (
        commands.MemberNotFound,
        "Message not found",
        lambda e: f"Could not find member for {wrap_in_code(e.argument)}.",
    ),
    (
        commands.UserNotFound,
        "Message not found",
        lambda e: f"Could not find user for {wrap_in_code(e.argument)}.",
    ),
    (
        commands.ChannelNotFound,
        "Message not found",
        lambda e: f"Could not find channel for {wrap_in_code(e.argument)}.",
    ),
    (
        (commands.EmojiNotFound, commands.PartialEmojiConversionFailure),
        "Message not found",
        lambda e: f"Could not find emoji for {wrap_in_code(e.argument)}.",
    ),
    (
        commands.ChannelNotReadable,
        "Message not found",
        lambda e: f"Could not read messages in {e.argument.mention}.",
    ),
    (
        commands.RoleNotFound,
        "Message not found",
        lambda e: f"Could not find role for {wrap_in_code(e.argument)}.",
    ),
    (
        (commands.BadArgument, commands.BadUnionArgument),
        "Bad argument",
        "An argument you provided was invalid or not found, please read help for more info.",
    ),
    (
        commands.ArgumentParsingError,
        "Argument parsing failed",
        "Failed to parse arguments, please check for quote marks.",
    ),
    (
        commands.UserInputError,
        "Bad user input",
        "Details are unknown, please read help for more info.",
    ),
    (
        commands.MissingPermissions,
        "Missing permissions",
        lambda e: f"You are missing permissions: {', '.join(wrap_in_code(perm) for perm in e.missing_perms)}.",
    ),
    (
        commands.BotMissingPermissions,
        "Missing permissions",
        lambda e: f"I am missing permissions: {', '.join(wrap_in_code(perm) for perm in e.missing_perms)}.",
    ),
    (
        commands.PrivateMessageOnly,
        "Invalid context",
        "This command can only be used in DMs",
    ),
    (
        commands.NoPrivateMessage,
        "Invalid context",
        "This command can only be used in servers",
    ),
    (
        commands.CheckFailure,
        "Check failure",
        "A condition failed, please read help for more info.",
    ),
    (
        commands.CommandOnCooldown,
        "Cooldown",
        lambda e: f"You're on cooldown, you can use this command again in {math.ceil(e.retry_after)} {'second' if math.ceil(e.retry_after) == 1 else 'seconds'}.",
    ),
    (
        commands.MaxConcurrencyReached,
        "Command already running",
        lambda e: f"This command is at its maximum capacity, please wait for any commands to finish.",
    ),
]


class Errors(cog.Cog):
    """Error handlers"""

    async def report_error(self, error, *, fields):
        exception = "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )

        print(exception, file=sys.stderr)

        embed = discord.Embed(
            title="Unhandled error", description=wrap_in_code(exception, block="py")
        )
        for field in fields:
            embed.add_field(**field)

        info = await self.bot.application_info()
        await info.owner.send(embed=embed)

    async def on_error(self, event, *args, **kwargs):
        error = sys.exc_info()[1]

        await self.report_error(
            error,
            fields=[
                {
                    "name": "Event",
                    "value": f"```{event}```",
                    "inline": False,
                },
                *(
                    {
                        "name": f"args[{index!r}]",
                        "value": wrap_in_code(repr(arg), block=True),
                        "inline": False,
                    }
                    for index, arg in enumerate(args)
                ),
                *(
                    {
                        "name": f"kwargs[{index!r}]",
                        "value": wrap_in_code(repr(arg), block=True),
                        "inline": False,
                    }
                    for index, arg in kwargs.items()
                ),
            ],
        )

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        if str(error).startswith("The global check "):
            try:
                await self.bot.global_check(ctx)
            except commands.CommandError as exc:
                error = exc

        error = getattr(error, "original", error)

        if isinstance(error, tuple(ignored_errors)):
            return

        if isinstance(error, commands.BotMissingPermissions):
            if "send_messages" in error.missing_perms:
                try:
                    await ctx.author.send(
                        "Hey, I don't have permission to send messages in"
                        f" {escape_markdown(ctx.guild)}, {ctx.channel.mention}."
                        " Please notify an administrator about this.",
                    )
                except discord.HTTPException:
                    pass
                return
            if (
                "embed_links" in error.missing_perms
                or "attach_files" in error.missing_perms
            ):
                await ctx.send(
                    "I don't have permission to embed links or attach files"
                    " in this channel. Please notify an administrator about"
                    " this.",
                )
                return

        else:
            for error_type, title, description in error_types:
                if isinstance(error, error_type):
                    await ctx.send(
                        embed=discord.Embed(
                            title=title,
                            description=description(error)
                            if callable(description)
                            else description,
                        ),
                    )

                    break

            else:
                await ctx.send(
                    embed=discord.Embed(
                        title="Error",
                        description="An unknown error has occured, please report this.",
                    )
                )

                await self.report_error(
                    error,
                    fields=[
                        {
                            "name": "Message",
                            "value": ctx.message.content,
                            "inline": False,
                        },
                    ],
                )


def setup(bot):
    bot.add_cog(Errors(bot))
