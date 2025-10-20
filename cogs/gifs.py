import json
import logging
import random
from urllib import parse, request

from discord.ext import commands


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
        with open("settings.json", "r", encoding="utf-8") as f:
            settings = json.load(f)
            giphy_key = settings.get("giphy_key")

        if not text:
            giphy_url = "https://api.giphy.com/v1/gifs/random"
            params = parse.urlencode(
                {
                    "api_key": giphy_key
                }
            )
            self.logger.debug("GETTING RANDOM GIF")
        else:
            giphy_url = "https://api.giphy.com/v1/gifs/search"
            params = parse.urlencode(
                {
                    "q"      : text,
                    "api_key": giphy_key,
                    "limit"  : 5
                }
            )
            self.logger.debug("GETTING 5 GIFS")

        with request.urlopen(f"{giphy_url}?{params}") as response:
            data = json.loads(response.read())
            self.logger.debug(f"RESPONSE: {data}")

        if not text:
            gif_url = data["data"]["images"]["original"]["url"]
        else:
            if not data["data"]:
                await ctx.message.reply("No GIFs found")
                self.logger.info("No GIFs found")
                return
            gif_urls = [item["images"]["original"]["url"] for item in data["data"]]
            gif_url = random.choice(gif_urls)

        self.logger.info(f"SENDING GIF: {gif_url}")
        await ctx.message.reply(gif_url)


async def setup(bot):
    await bot.add_cog(Gifs(bot))
