import random
from discord.ext import commands


class Template(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    async def purple(self, ctx, *, args=None):
        """
        Summon Purple Aki
        """
        purple_akis = [
            "https://m.media-amazon.com/images/M/MV5BMzFhY2MwOTItZjQ4ZC00MjdmLTgyYWMtOGNjNjcxOTIzYjk1XkEyXkFqcGc@._V1_.jpg",
            "https://www.bbc.co.uk/news/special/2016/newsspec_14877/media/akinwale_rex_landscape-mr.jpg",
            "https://thewillnews.com/wp-content/uploads/2025/08/Purple-Aki.jpg",
            "https://images.ctfassets.net/pjshm78m9jt4/128199_2/54638e66ab8de25ba8b04606166cbdc6/0_WA722864.jpeg?fm=jpg&fit=fill&w=400&h=225&q=80"
        ]
        if args is None:
            return
        elif args.lower() == "aki purple aki purple aki":
            await ctx.reply(random.choice(purple_akis))
        else:
            return

async def setup(bot):
    await bot.add_cog(Template(bot))