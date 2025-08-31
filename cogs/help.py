import discord
from discord.ext import commands


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command('help')

    @commands.command()
    async def help(self, ctx, *, help_command: str = None):
        if help_command is None:
            # Generic Help Menu
            embed = discord.Embed(
                title="r/help",
                description="Use r/help *command* to see help for a specific command",
                color=0xED001C
            )

            for command in self.bot.commands:
                if not command.hidden:
                    embed.add_field(
                        name=f"r/{command.name}",
                        value=command.help or "No description available",
                        inline=False
                    )

        else:
            command = self.bot.get_command(help_command)
            if command is None:
                embed = discord.Embed(
                    title="Help",
                    description=f"The command `r/{help_command}` doesn't exist.",
                    color=0xED001C
                )

            else:
                embed = discord.Embed(
                    title=f"r/{command.name}",
                    description=command.help or "No description available",
                    color=0xED001C
                )

                if command.aliases:
                    embed.add_field(
                        name=f"Aliases",
                        value=", ".join(command.aliases),
                        inline=False
                    )

        await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(Help(bot))