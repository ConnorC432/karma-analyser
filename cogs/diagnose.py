import logging
import discord
import asyncio
import json
import re
from discord.ext import commands
from ollama import Client
from ._utils import reddiquette


class Diagnose(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

    @commands.command(aliases=["diagnosis"])
    async def diagnose(self, ctx, user: discord.Member = None):
        """
        Get a user's karmic diagnosis
        - `user` (optional): Mention the user(s) to diagnose.
        """
        if user is None:
            user = ctx.author

        self.logger.info(f"DIAGNOSING {user.name}")

        reply = await ctx.reply("DIAGNOSING...")
        message_log = []
        async for msg in ctx.channel.history(limit=200):
            if msg.author == user and "r/" not in msg.content and "http" not in msg.content:
                message_log.append(msg.content)

        ai_instructions = ("You are a reddit moderation bot...\n" + reddiquette)
        prompt = "These are the messages you need to analyse: \n" + "\n".join(message_log)

        with open("settings.json", "r") as f:
            settings = json.load(f)
        client = Client(host=settings.get("ollama_endpoint"))

        try:
            response = await asyncio.to_thread(
                client.chat,
                model="artifish/llama3.2-uncensored",
                messages=[
                    {"role": "system", "content": ai_instructions},
                    {"role": "user", "content": prompt}
                ]
            )
        except Exception as e:
            self.logger.error(e)

        clean_response = re.sub(r"<think>.*?</think>\\n\\n", "", response.message.content, flags=re.DOTALL)
        await reply.edit(content=f"{user.mention}: {clean_response[:1950]}")
        self.logger.debug(f"RESPONSE: {clean_response[:1950]}")

async def setup(bot):
    await bot.add_cog(Diagnose(bot))