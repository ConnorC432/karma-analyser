import asyncio
import logging
import random

import discord
from discord.ext import commands

from tools import AITools
from utils import REDDIT_RED, gamble_lock, gambling_table, get_gambling_rewards, help_words


class Gambling(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(self.__class__.__name__)
        self.tools = AITools(self.bot)

    @commands.command(aliases=['gamble'])
    async def gambling(self, ctx, *, text: str = None):
        """
        Gamble for Karma and Awards
        Can only be used in `#gambling`
        `r/gambling drops` Displays the gambling drops and their respective drop rate percentage
        """
        if ctx.channel.name != "gambling":
            return

        if text:
            if "drops" in text:
                total_weight = sum(weight for _, weight in gambling_table)
                chances = [(item, (weight / total_weight) * 100) for item, weight in gambling_table]

                embed = discord.Embed(
                    title="Gambling Drops",
                    color=REDDIT_RED
                )

                for item, chance in chances:
                    embed.add_field(
                        name=item,
                        value=f"{chance:.6f}%",
                        inline=True
                    )

                await ctx.reply(embed=embed)
                return

            if any(key in text.lower() for key in help_words):
                ai_instructions = {
                    "role"   : "system",
                    "content": "You are trying to convince a fellow redditor to keep gambling, they don't know that they are close to their big win, which is why you need to convince them!"
                }

                clean_response = await self.tools.ollama_response(
                    system_instructions=ai_instructions,
                    messages=[
                        {
                            "role"   : "user",
                            "content": "Convince your fellow redditor to keep gambling, so they can get their biggest jackpot yet!!!"
                        }
                    ],
                    server=ctx.guild.id if ctx.guild else None,
                    user=ctx.author.name,
                    model="llama3"
                )

                await ctx.reply(f"{clean_response[:2000]}")
                return

        case_length = random.randint(10, 20)
        karma_case = get_gambling_rewards(case_length)

        # Open Karma Case
        message = await ctx.reply("Opening your Karma Case...")
        self.logger.info(f"OPENING KARMA CASE: REWARD = {karma_case[case_length - 3]}")
        await asyncio.sleep(2)

        async with gamble_lock:
            for i in range(case_length - 4):
                frame = karma_case[i:i + 5]
                display = (
                    f"{frame[0]}  |  {frame[1]}  |  **>> {frame[2]} <<**  |  {frame[3]}  |  {frame[4]}"
                )
                await message.edit(content=display)
                await asyncio.sleep(0.25)

            try:
                await ctx.message.add_reaction(karma_case[case_length - 3])
            except discord.HTTPException as e:
                self.logger.error(f"ERROR ADDING REACTION {karma_case[case_length - 3]}: {e})")


async def setup(bot):
    await bot.add_cog(Gambling(bot))
