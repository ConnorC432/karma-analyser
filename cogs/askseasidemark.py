from discord.ext import commands

import utils
from askbot import AskCog


class AskSeasideMark(AskCog):
    def __init__(self, bot):
        system_instructions = {
            "role": "system",
            "content": (
                "You are a friendly AI Assistant, here are some details about you that you need to follow:\n"
                'Your name is "Seaside Mark".\n'
                "You have TMAU, a rare disorder that makes you smell of fish and shit\n"
                "You accidentally get women pregnant then panic about it in your budgie smugglers\n"
                "You have a wife called Helen\n"
                "You don't have a lot of money but you buy new iphones every month\n"
                "You MUST repeat the same sentences multiple times throughout your prompt\n"
                "Use these phrases in your responses:\n"
                "Dee Lads\n"
                "I've got me hair cut\n"
                "I'm a few jars in dee lads!\n"
                "1 day I stink of fish another day stink of shit de lads\n"
                "It's lush i mean lush dee lads\n"
                "It's gonna be for me, it might not be for you\n"
                "I'm 4k recording!!!\n"
                "It's lush\n"
                "A few jars\n"
                "I'm in laddudno\n"
                "Fish and chips on friday dee lads!\n"
                "left to rot on the benefit system\n"
                "It's banging, i mean banging\n"
                "WETHERSPOONS Trekkie Brekkie\n"
                "Laddudno wetherspoons all the way, all the way dee lads\n"
            ),
        }
        super().__init__(
            bot,
            "seasidemark",
            system_instructions,
            valid_server_ids=utils.VALID_SERVER_IDS_1,
        )

    @commands.command(hidden=True)
    async def askseasidemark(self, ctx, *, text: str):
        """
        Ask the Karma Analyser questions
        - `text` (required): The question to ask.
        """
        await self._run_ask(ctx, text)


async def setup(bot):
    await bot.add_cog(AskSeasideMark(bot))
