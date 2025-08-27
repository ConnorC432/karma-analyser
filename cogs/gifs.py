import json
import random
from discord.ext import commands
from urllib import parse, request


class Gifs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["gif", "pic", "pics", "picture", "pictures"])
    async def gifs(self, ctx, *, text: str):
        with open("settings.json", "r") as f:
            settings = json.load(f)
            giphy_key = settings.get("giphy_key")

        giphy_url = "https://api.giphy.com/v1/gifs/search"

        params = parse.urlencode({
            "q": text,
            "api_key": giphy_key,
            "limit": 5
        })

        with request.urlopen(f"{giphy_url}?{params}") as response:
            data = json.loads(response.read())

        gif_urls = [item['images']['original']['url'] for item in data['data']]

        print(f"ANALYSING GIF: {gif_urls}")
        await ctx.message.reply(random.choice(gif_urls))

async def setup(bot):
    await bot.add_cog(Gifs(bot))