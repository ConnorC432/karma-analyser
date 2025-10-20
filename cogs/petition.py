import discord
from discord.ext import commands


class Petition(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def petition(self, ctx, *, text: str):
        """
        Create a petition
        - `text` (required): The petition text
        """
        reply = await ctx.message.reply(content=f"# {text}", file=discord.File("./petition.gif"))

        await reply.add_reaction("🖊️")


async def setup(bot):
    await bot.add_cog(Petition(bot))
