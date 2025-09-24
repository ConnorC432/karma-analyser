import aiohttp
import random
from discord.ext import commands


class Wordle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def wordle(self, ctx):
        """
        Get a random wordle answer
        """
        async with aiohttp.ClientSession() as session:
            async with session.get("https://gist.githubusercontent.com/cfreshman/a03ef2cba789d8cf00c08f767e0fad7b/raw/c46f451920d5cf6326d550fb2d6abb1642717852/wordle-answers-alphabetical.txt") as resp:
                if resp.status != 200:
                    await ctx.reply(content="NONCE")
                    return

                text = await resp.text()
                words = [line.strip().lower() for line in text.splitlines() if line.strip()]

        await ctx.reply(content=random.choice(words).upper())


async def setup(bot):
    await bot.add_cog(Wordle(bot))