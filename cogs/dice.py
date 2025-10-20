import logging
import random
import re
import utils
import discord
from discord.ext import commands


class Dice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

    @commands.Cog.listener()
    async def on_message(self, payload):
        if payload.author.bot:
            return

        if not payload.content.startswith("r/"):
            return

        content = payload.content[2:].strip()
        pattern = r"^(\d+)d(\d+)((?:\+|\-)\d+)?$"   # Match the XdY+Z format
        match = re.match(pattern, content)
        if not match:
            return

        num = int(match.group(1))   # Number of dice to roll
        sides = int(match.group(2)) # Number of sides on the dice
        modifier = match.group(3)   # Modifier +/-

        self.logger.info(f"Rolling: {num}d{sides}{modifier or ''}")

        mod_int = int(modifier) if modifier else 0

        if num > 1000000 or sides > 1000000 or abs(mod_int) > 1000000:
            return

        rolls = [random.randint(1, sides) for _ in range(num)]
        total = sum(rolls)
        total += mod_int

        embed = discord.Embed(
            title=total,
            color=utils.reddit_red
        )
        embed.add_field(
            name="🎲 Die" if num == 1 else "🎲 Dice",
            value=f"{num}d{sides}{modifier or ''}",
            inline=True
        )
        if len(rolls) <= 50:
            embed.add_field(
                name="🫳 Roll" if num == 1 else "🫳 Rolls",
                value=", ".join(map(str, rolls)),
                inline=False
            )

        await payload.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(Dice(bot))