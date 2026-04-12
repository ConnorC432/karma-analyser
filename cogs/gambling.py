import asyncio
import logging
import random

import discord
from discord.ext import commands

from tools import AITools
from utils import REDDIT_RED


gamble_lock = asyncio.Lock()

help_words = [
    "help",
    "helpline",
    "addiction",
    "support",
    "assistance",
    "advice",
    "tips",
    "problem",
    "recovery",
    "struggling",
    "stop",
    "lost",
    "losses",
    "lose",
    "urge",
    "temptation",
    "compulsive",
    "control"
]

gambling_table = [
    ("<:quarter_downvote:1266139626276388875>", 275),
    ("<:quarter_upvote:1266139599814529034>", 250),
    ("<:reddit_downvote:1266139651660447744>", 125),
    ("<:reddit_upvote:1266139689136689173>", 100),
    ("<:middlevote:1152474066331123823>", 50),
    ("<:absolutelynothing:1379228455580729435>", 35),
    ("<:fellforitagainaward:1361028185709346976>", 35),
    ("<:reddit_wholesome:833669115762835456>", 30),
    ("<:reddit_silver:833677163739480079>", 25),
    ("<:reddit_gold:833675932883484753>", 10),
    ("<:Hullnarna:1406697829883314280>", 10),
    ("<:fruity:1399459414716715078>", 10),
    ("<:reddit_platinum:833678610279563304>", 1),
    ("<:kayspag:1398048349579378849>", 1),
    ("<:budgiesmugglers:1399456204215947315>", 1),
    ("<:colin_nobinson:1412205389285691403>", 1),
    ("<:horseinsuit2:1363514876265365514>", 1),
    ("<:nissan:1351514275855863871>", 1),
    ("<:imjakingit:1361028727206711488>", 1),
    ("<:Last_in_PE:1371888191858016266>", 1),
    ("<:bovril:1401110047500668958>", 1),
    ("<:pepperjak:1189327796724580493>", 1),
    ("<:sadmark:1398048884332298260>", 1),
    ("<:duke:1414946579302842388>", 0.001)
]


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
        karma_case = self._get_gambling_rewards(case_length)

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

    def _get_gambling_rewards(self, length=10):
        rewards, weights = zip(*gambling_table)
        return random.choices(rewards, weights=weights, k=length)


async def setup(bot):
    await bot.add_cog(Gambling(bot))
