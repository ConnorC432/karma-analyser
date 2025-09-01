from discord.ext import commands


class Sounding(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def sounding(self, ctx):
        """
        Listen to r/sounding
        """
        await ctx.reply(content="https://open.spotify.com/playlist/6FeuMOuHqcedxUis0NQbch")


async def setup(bot):
    await bot.add_cog(Sounding(bot))