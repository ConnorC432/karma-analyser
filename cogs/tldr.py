import logging

from discord.ext import commands

from tools import AITools


class TLDR(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

        self.system_instructions = {
            "role"   : "system",
            "content": (
                "Your purpose is to summarise the user's reddit post in 50 words or less using dry-wit humour and lots of sarcasm"
            )
        }

        self.tools = AITools(self.bot)

    @commands.command(aliases=["summarise"])
    async def tldr(self, ctx, *, text: str = None):
        self.logger.debug("SUMMARISING USER'S SHIT POST")

        if ctx.message.reference:
            self.logger.debug("TLDR'ING REFERENCE MESSAGE")
            text = ctx.message.reference.resolved.content

        elif text:
            self.logger.debug("TLDR'ING TEXT MESSAGE")
            pass

        else:
            self.logger.debug("NOTHING TO TLDR")
            return

        response = await self.tools.ollama_response(
            system_instructions=self.system_instructions,
            messages=[
                {
                    "role"   : "user",
                    "content": text,
                }
            ],
            server=ctx.guild.id if ctx.guild else None,
            user=ctx.author.name
        )

        await ctx.reply(response)


async def setup(bot):
    await bot.add_cog(TLDR(bot))
