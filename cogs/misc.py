import asyncio
import datetime
import logging
import random

import discord
from discord.ext import commands


class Misc(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.init_time = datetime.datetime.now(datetime.timezone.utc)
        self.logger = logging.getLogger(self.__class__.__name__)

    @commands.Cog.listener()
    async def on_message(self, payload):
        if payload.type in [
            discord.MessageType.premium_guild_subscription,
            discord.MessageType.premium_guild_tier_1,
            discord.MessageType.premium_guild_tier_2,
            discord.MessageType.premium_guild_tier_3
        ]:
            await payload.reply(f"Thank you for boosting the server kind stranger!")

        if payload.author.bot:
            return

        if "pass it on" in payload.content.lower():
            async for message in payload.channel.history(limit=100, oldest_first=False):
                if message.author.bot and message.content == payload.content:
                    return

            await asyncio.sleep(random.uniform(0, 2.5))
            await payload.channel.send(payload.content)
            self.logger.info(f"PASSING IT ON: {payload.content}")

        if "nothing ever happens" in payload.content.lower():
            await payload.reply(
                content="https://tenor.com/view/nothing-ever-happens-chud-chudjak-soyjak-90-seconds-to-nothing-gif-9277709574191520604"
            )
            self.logger.info("NOTHING EVER HAPPENS")

    @commands.command()
    async def gild(self, ctx):
        """
        Gild the Karma Analyser
        """
        await ctx.reply("Thank you kind stranger!")


async def setup(bot):
    await bot.add_cog(Misc(bot))
