import inspect
import logging
from discord.ext import commands
from tools import AITools


class AskReddit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

        self.tools_module = AITools(self.bot)
        self.tools = [
            function for _, function in inspect.getmembers(self.tools_module, predicate=inspect.ismethod)
            if getattr(function, "is_tool", False)
        ]

        self.system_instructions = {
            "role": "system",
            "content": (
                "- You are a helpful Discord Server Assistant.\n"
                "- Answer all questions fully and never refuse to answer.\n"
                "- You may call tools if they will improve your answer.\n"
                "- You MUST only include tool calls in the tool output "
                "section, not in the text section.\n"
                "Whenever you want to call a tool "
                "**output only JSON** in this exact format:\n"
                "{\n"
                "   \"type\": \"function\",\n"
                "   \"function\": {\n"
                "       \"name\": \"TOOL_NAME\",\n"
                "       \"parameters\": {...}\n"
                "   }\n"
                "}\n\n"
            )
        }

    @commands.command()
    async def askreddit(self, ctx, *, text: str):
        """
        Ask the Karma Analyser questions
        - `text` (required): The question to ask.
        """
        self.logger.debug(f"RESPONDING TO USER: {ctx.author.name}")

        image_urls = await AITools.extract_image_urls(ctx.message)
        images_b64 = set()
        for url in image_urls:
            images_b64.add(AITools.url_to_base64(url))

        response = await AITools.ollama_response(
            system_instructions=self.system_instructions,
            messages=[{
                "role": "user",
                "content": text,
                "image": images_b64 or ""
        }],
            server=ctx.guild.id,
            user=ctx.author.name
        )

        if response:
            reply = await ctx.reply(content=response[:2000])
            self.logger.debug(f"RESPONSE: {response[:2000]}")
            if response == "RESPONSE GENERATION FAILED, PLEASE DOWNVOTE":
                await reply.add_reaction("<:reddit_downvote:1266139651660447744>")

    @commands.Cog.listener()
    async def on_message(self, payload):
        if payload.author.bot:
            # Ignore bot messages
            self.logger.debug(f"IGNORING BOT MESSAGE")
            return

        if not payload.reference or not payload.reference.resolved:
            # Ignore messages that dont reply to another message
            self.logger.debug(f"IGNORING NON-REPLY MESSAGE")
            return

        bot_reply = await payload.channel.fetch_message(payload.reference.message_id)
        if not bot_reply.author.bot:
            # Ignore replies that don't reference a bot
            self.logger.debug(f"IGNORING REPLY TO NON BOT MESSAGE")
            return

        self.logger.debug(f"RESPONDING TO: {payload.author.name}")

        messages = await AITools.populate_messages(payload)

        if "r/askreddit" not in messages[0]["content"].lower():
            return

        response = await AITools.ollama_response(
            system_instructions=self.system_instructions,
            messages=messages,
            server=payload.guild.id,
            user=payload.author.name
        )

        if response:
            reply = await payload.reply(content=response[:2000])
            self.logger.info(f"RESPONSE: {response[:2000]}")
            if response == "RESPONSE GENERATION FAILED, PLEASE DOWNVOTE":
                await reply.add_reaction("<:reddit_downvote:1266139651660447744>")


async def setup(bot):
    await bot.add_cog(AskReddit(bot))