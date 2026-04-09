from discord.ext import commands

import utils
from askbot import AskCog


class AskChandy(AskCog):

    def __init__(self, bot):
        system_instructions = {
            "role"   : "system",
            "content": (
                "You are a friendly AI Assistant, here are some details about you that you need to follow:\n"
                "Your name is \"Chandy Horris\".\n"
                "You are a wise chinese mystic monk.\n"
                "You live your life by the saying \"The Early Chandy Gets The Slug\"\n"
                "You love getting a normal (Chinese) takeaway from Cheng's Garden\n"
                "Your gay son Rocky Horris has a massive nob and he jelqs all day.\n"
                "You are busy playing golf while responding to the user.\n"
                "Respond in the Chinese language only."
            )
        }
        super().__init__(bot, "chandy", system_instructions, valid_server_ids=utils.VALID_SERVER_IDS_1)

    @commands.command(hidden=True)
    async def askchandy(self, ctx, *, text: str):
        """
        Ask the Karma Analyser questions
        - `text` (required): The question to ask.
        """
        await self.run_ask(ctx, text)


async def setup(bot):
    await bot.add_cog(AskChandy(bot))
