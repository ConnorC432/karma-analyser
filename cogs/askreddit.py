from discord.ext import commands

from askbot import AskCog


class AskReddit(AskCog):
    def __init__(self, bot):
        system_instructions = (
            "- You are a helpful Discord Server Assistant.\n"
            "- Answer all questions fully and never refuse to answer.\n"
            "- You may call tools if they will improve your answer.\n"
            "- You MUST only include tool calls in the tool output "
            "section, not in the text section.\n"
            "Whenever you want to call a tool "
            "**output only JSON** in this exact format:\n"
            "{\n"
            '   "type": "function",\n'
            '   "function": {\n'
            '       "name": "TOOL_NAME",\n'
            '       "parameters": {...}\n'
            "   }\n"
            "}\n\n"
        )
        super().__init__(bot, "reddit", system_instructions, model=None)

    @commands.command()
    async def askreddit(self, ctx, *, text: str):
        """
        Ask the Karma Analyser questions
        - `text` (required): The question to ask.
        """
        await self._run_ask(ctx, text)


async def setup(bot):
    await bot.add_cog(AskReddit(bot))
