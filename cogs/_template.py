import logging

from discord.ext import commands


class Template(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(f"{self.__class__.__name__}")


async def setup(bot):
    await bot.add_cog(Template(bot))
