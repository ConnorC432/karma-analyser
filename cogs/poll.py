import logging

import discord
from discord.ext import commands

from cogs._utils import emoji_numbers


class Poll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

    @commands.command()
    async def poll(self, ctx, question: str, *options: str) -> None:
        """
        Create a poll with between 2 and 10 questions.
        - `text` (required): Poll question
        - `text` (required): Option 1
        - `text` (required): Option 2
        - `text` (optional): Option 3...
        """

        if len(options) < 2:
            await ctx.message.reply("A poll must have at least 2 options")
            self.logger.warning("A poll must have at least 2 options")
            return
        if len(options) > 10:
            await ctx.message.reply("A poll can't have more than 10 options")
            self.logger.warning("A poll can't have more than 10 options")
            return

        embed = discord.Embed(
            title=question,
            description="\n".join(f"### {emoji_numbers[i]} {opt} \n" for i, opt in enumerate(options)),
            color=0xED001C
        )

        poll_message = await ctx.message.reply(embed=embed)

        for i in range(len(options)):
            await poll_message.add_reaction(emoji_numbers[i])


async def setup(bot):
    await bot.add_cog(Poll(bot))