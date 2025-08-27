from discord.ext import commands


class Ben(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["talkingben"])
    async def ben(self, ctx, text: str = None):
        if text is None:
            return

        reply = None

        match text.lower():
            case "yes":
                reply = "https://tenor.com/view/yes-gif-24966277"
            case "no":
                reply = "https://tenor.com/view/no-gif-24966265"
            case "ugh":
                reply = "https://tenor.com/view/ugh-gif-24966261"
            case "hoho":
                reply = "https://tenor.com/view/hohho-ho-gif-24966256"
            case _:
                reply = "Ben only understands \"Yes\", \"No\", \"Ugh\", or \"Hoho\""

        await ctx.reply(reply)


async def setup(bot):
    await bot.add_cog(Ben(bot))