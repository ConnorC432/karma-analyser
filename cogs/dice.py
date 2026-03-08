import logging
import random
import re

import discord
from discord.ext import commands

import utils


class Dice(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(self.__class__.__name__)
        self.pattern = re.compile(r"^(\d+)d(\d+)([+\-]\d+)?$")

    def parse_roll_string(self, dice: str):
        match = self.pattern.match(dice)

        if not match:
            return None

        num = int(match.group(1))                                   # Number of dice to roll
        sides = int(match.group(2))                                 # Number of sides on the dice
        modifier = int(match.group(3)) if match.group(3) else 0     # Modifier +/-

        if (
                num > 1000000
                or sides > 1000000
                or sides < 2
                or abs(modifier) > 1000000
        ):
            return None

        return num, sides, modifier

    @staticmethod
    def roll_dice(num: int, sides: int, modifier: int = None):
        rolls = [random.randint(1, sides) for _ in range(num)]
        total = sum(rolls) + modifier
        return rolls, total

    def create_embed(self, num, sides, modifier, rolls, total):
        embed = discord.Embed(
            title=total,
            color=utils.REDDIT_RED
        )
        embed.add_field(
            name=self.dice_name(num, sides),
            value=f"{num}d{sides}{modifier or ''}",
            inline=True
        )
        if len(rolls) <= 50:
            embed.add_field(
                name="🫳 Roll" if num == 1 else "🫳 Rolls",
                value=", ".join(map(str, rolls)),
                inline=False
            )

        return embed

    @staticmethod
    def dice_name(num, sides):
        dice_info = {
            2  : {"emoji": "🪙", "singular": "Coin", "plural": "Coins"},
            52 : {"emoji": "🃏", "singular": "Deck of Cards", "plural": "Decks of Cards"},
            69 : {"emoji": "🍆", "singular": "Nice", "plural": "Nice"},
            777: {"emoji": "🎰", "singular": "Slot Machine", "plural": "Slot machines"},
        }

        info = dice_info.get(sides, {"emoji": "🎲", "singular": "Die", "plural": "Dice"})

        name = info["singular"] if num == 1 else info["plural"]

        return f"{info['emoji']} {name}"

    @commands.command(name="dice", aliases=["roll"])
    async def dice(self, ctx, dice: str | None = None):
        """
        Roll dice with the format XdY(+/-)Z
        - `X` (required): Number of dice to roll
        - `Y` (required): Number of sides on the die/dice
        - `Z` (optional): Total value modifier
        """
        if ctx.author.bot:
            return

        parsed = self.parse_roll_string(dice)

        if not parsed:
            return

        num, sides, modifier = parsed
        rolls, total = self.roll_dice(num, sides, modifier)
        embed = self.create_embed(num, sides, modifier, rolls, total)

        await ctx.reply(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, ctx):
        if ctx.author.bot:
            return

        if not ctx.content.startswith("r/"):
            return

        dice = ctx.content[2:].strip()

        parsed = self.parse_roll_string(dice)

        if not parsed:
            return

        num, sides, modifier = parsed
        rolls, total = self.roll_dice(num, sides, modifier)
        embed = self.create_embed(num, sides, modifier, rolls, total)

        await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(Dice(bot))
