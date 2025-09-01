import aiohttp
import discord
from discord.ext import commands


class Insult(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def insult(self, ctx, user: discord.Member = None):
        """
        Insult a fellow Redditor
        - `user` (optional): The Redditor to insult
        """
        async with aiohttp.ClientSession() as session:
            async with session.get("https://evilinsult.com/generate_insult.php?lang=en&type=json") as resp:
                if resp.status != 200:
                    await ctx.reply(content="ERROR, CAN'T INSULT USER")
                    return
                data = await resp.json()
                insult = data.get("insult", "ERROR, CAN'T INSULT USER")

        if user is None:
            await ctx.reply(content=insult)
        else:
            await ctx.reply(f"{user.mention}: {insult}")


async def setup(bot):
    await bot.add_cog(Insult(bot))