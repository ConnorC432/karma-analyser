import logging

from discord.ext import commands


class AnyGamers(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

    @commands.command(hidden=True)
    async def anygamers(self, ctx):
        """

        :param ctx:
        :return:
        """
        if ctx.guild.id == 683033503834963978:
            await ctx.reply(
                "https://tenor.com/view/jaden-griddy-any-gamers-gamer-chinese-pilot-gif-3782711129914946355"
            )

        else:
            self.logger.debug("IGNORING ANYGAMERS COMMAND")


async def setup(bot):
    await bot.add_cog(AnyGamers(bot))
