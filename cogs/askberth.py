import logging
from discord.ext import commands
from tools import AITools


class AskBerth(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

        self.valid_server_id = 683033503834963978

        self.system_instructions = {
            "role": "system",
            "content": (
                "You are a friendly AI Assistant, here are some details about you that you need to follow:\n"
                "Your name is \"Berthany Dezza\".\n"
                "Your dad is called \"Wayne Dezza\", he has no teeth and can't read\n"
                "You get beaten by your mrs, Tazmin Simons, after she's had a few stellas\n"
                "You're a fake ginger, you dye your hair everyday, since you are ashamed to have a soul\n"
                "You use to work at a pub called \"The Aardvark\" but you quit after the new owners "
                "wouldn't pay you minimum wage, they're bunch of smelly indians anyway\n"
                "A cardboard cutout of Nigel Farage, your favourite politician, is your sleep paralysis "
                "demon, you see him staring at you from the end of your bed\n"
            )
        }

        self.tools = AITools(self.bot)

    @commands.command(hidden=True)
    async def askberth(self, ctx, *, text: str):
        """
        Ask the Karma Analyser questions
        - `text` (required): The question to ask.
        """
        if not ctx.guild:
            return

        if ctx.guild.id != self.valid_server_id:
            self.logger.debug("IGNORING ASKBERTH REQUEST")
            return

        self.logger.debug(f"RESPONDING TO USER: {ctx.author.name}")

        image_urls = await self.tools.extract_image_urls(ctx.message)
        images_b64 = set()
        if image_urls:
            for url in image_urls:
                images_b64.add(await self.tools.url_to_base64(url))

        response = await self.tools.ollama_response(
            system_instructions=self.system_instructions,
            messages=[{
                "role": "user",
                "content": text,
                "images": images_b64 or ""
        }],
            server=ctx.guild.id,
            user=ctx.author.name,
            model="dolphin-llama3"
        )

        if response:
            reply = await ctx.reply(content=response[:2000])
            self.logger.debug(f"RESPONSE: {response[:2000]}")
            if response == "RESPONSE GENERATION FAILED, PLEASE DOWNVOTE":
                await reply.add_reaction("<:reddit_downvote:1266139651660447744>")

    @commands.Cog.listener()
    async def on_message(self, payload):
        if not payload.guild:
            return

        if payload.guild.id != self.valid_server_id:
            self.logger.debug("IGNORING ASKBERTH REQUEST")
            return

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

        messages = await self.tools.populate_messages(payload)

        if "r/askberth" not in messages[0]["content"].lower():
            return

        response = await self.tools.ollama_response(
            system_instructions=self.system_instructions,
            messages=messages,
            server=payload.guild.id,
            user=payload.author.name,
            model="dolphin-llama3"
        )

        if response:
            reply = await payload.reply(content=response[:2000])
            self.logger.info(f"RESPONSE: {response[:2000]}")
            if response == "RESPONSE GENERATION FAILED, PLEASE DOWNVOTE":
                await reply.add_reaction("<:reddit_downvote:1266139651660447744>")


async def setup(bot):
    await bot.add_cog(AskBerth(bot))