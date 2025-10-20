import discord
from discord.ext import commands

import utils


class Help(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command('help')

    @commands.command()
    async def help(self, ctx, *, help_command: str = None):
        """
        Shows this menu
        - `command` (optional): The command to show help for.
        """
        if help_command is None:
            # Generic Help Menu
            embed = discord.Embed(
                title="r/help",
                description="Use r/help *command* to see help for a specific command",
                color=utils.REDDIT_RED
            )

            for command in self.bot.commands:
                if not command.hidden:
                    embed.add_field(
                        name=f"r/{command.name}",
                        value="",
                        inline=False
                    )

        else:
            command = self.bot.get_command(help_command)
            if command is None:
                embed = discord.Embed(
                    title="Help",
                    description=f"The command `r/{help_command}` doesn't exist.",
                    color=utils.REDDIT_RED
                )

            else:
                embed = discord.Embed(
                    title=f"r/{command.name}",
                    description=command.help or "No description available",
                    color=utils.REDDIT_RED
                )

                if command.aliases:
                    embed.add_field(
                        name="Aliases",
                        value=", ".join(command.aliases),
                        inline=False
                    )

        await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(Help(bot))
