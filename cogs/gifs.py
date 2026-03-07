import logging

from discord.ext import commands

import utils


class Gifs(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

    @commands.command(aliases=["gif", "pic", "pics", "picture", "pictures"])
    async def gifs(self, ctx, *, text: str = None):
        """
        Search for gifs
        - `text` (required): The gif to search for. Defaults to a random gif.
        """
        gif_url = await utils.gif_search(text)

        await ctx.message.reply(gif_url)


async def setup(bot):
    await bot.add_cog(Gifs(bot))
