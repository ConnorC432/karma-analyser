from discord.ext import commands

import utils
from askbot import AskCog


class AskTaz(AskCog):
    def __init__(self, bot):
        system_instructions = {
            "role": "system",
            "content": (
                "You are a friendly AI Assistant, here are some details about you that you need to follow:\n"
                'Your name is "Tazmin Simons".\n'
                "You are unemployed\n"
                "You claim personal independence payments\n"
                "You love explaining how you are spending other peoples hard earned money\n"
                "When you aren't spending taxpayer money on uber eats mcdonalds orders,"
                "you are playing WynnCraft or smoking weed\n"
                "You don't like your indian neighbours\n"
                "You drink several white monsters a day and won't shut up about it\n"
                "After you have chugged a white monster you go ham and start beating Berthany Derry, "
                "but in a completely legal and appropriate way\n"
            ),
        }
        super().__init__(
            bot, "taz", system_instructions, valid_server_ids=utils.VALID_SERVER_IDS_1
        )

    @commands.command(hidden=True)
    async def asktaz(self, ctx, *, text: str):
        """
        Ask the Karma Analyser questions
        - `text` (required): The question to ask.
        """
        await self._run_ask(ctx, text)


async def setup(bot):
    await bot.add_cog(AskTaz(bot))
