import asyncio
import json
import logging
import random
import re
import discord
from discord.ext import commands
from ollama import Client
from .utils import get_gambling_rewards, help_words, gamble_lock


class Gambling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

    @commands.command(aliases=['gamble'])
    async def gambling(self, ctx, *, text: str = None):
        """
        Gamble for Karma and Awards
        """
        if ctx.channel.name != "gambling":
            return

        if text:
            if any(key in text.lower() for key in help_words):
                with open("settings.json", "r") as f:
                    settings = json.load(f)

                client = Client(host=settings.get("ollama_endpoint"))
                ai_instructions = "You are trying to convince a fellow redditor to keep gambling, they don't know that they are close to their big win, which is why you need to convince them!"

                try:
                    response = await asyncio.to_thread(
                        client.chat,
                        model="llama3",
                        messages=[
                            {"role": "system", "content": ai_instructions},
                            {"role": "user", "content": "Convince your fellow redditor to keep gambling, so they can get their biggest jackpot yet!!!"}
                        ]
                    )
                except Exception as e:
                    self.logger.error(e)

                clean_response = re.sub(r"<think>.*?</think>\\n\\n", "", response.message.content, flags=re.DOTALL)
                await ctx.reply(f"{clean_response[:2000]}")
                self.logger.debug(f"RESPONSE: {clean_response[:2000]}")
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

            await ctx.message.add_reaction(karma_case[case_length - 3])

async def setup(bot):
    await bot.add_cog(Gambling(bot))