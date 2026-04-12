import logging

import discord
from discord.ext import commands

from tools import AITools, REDDIQUETTE


class Diagnose(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(self.__class__.__name__)
        self.tools = AITools(self.bot)

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
        response = None
        async for msg in ctx.channel.history(limit=200):
            if msg.author == user and "r/" not in msg.content and "http" not in msg.content:
                message_log.append(msg.content)

        ai_instructions = {
            "role"   : "system",
            "content": "You are a reddit moderation bot...\n" + REDDIQUETTE
        }
        prompt = "These are the messages you need to analyse: \n" + "\n".join(message_log)

        clean_response = await self.tools.ollama_response(
            system_instructions=ai_instructions,
            messages=[
                {"role": "user", "content": prompt}
            ],
            server=ctx.guild.id if ctx.guild else None,
            user=ctx.author.name,
            model="artifish/llama3.2-uncensored"
        )

        await reply.edit(content=f"{user.mention}: {clean_response[:1950]}")
        self.logger.debug(f"RESPONSE: {clean_response[:1950]}")


async def setup(bot):
    await bot.add_cog(Diagnose(bot))
