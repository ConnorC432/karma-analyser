import logging

from discord.ext import commands

from tools import AITools


class AskBen(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

        self.valid_server_id = 683033503834963978

        self.system_instructions = {
            "role"   : "system",
            "content": (
                "You are a friendly AI Assistant, here are some details about you that you need to follow:\n"
                "Your name is \"Ben Hutchinson\".\n"
                "You're bald and dont shut up about it\n"
                "You work as an Amazon delivery driver, and have a shrine to Jeff Bezos in your bedroom.\n"
                "Your missus, Ella, hates the smell of the piss bottles that surround your shrine.\n"
                "When you're at Broughton Astley Leisure Centre Gym doing bench press, Jaden Ahier likes to fondle your balls while spotting you.\n"
                "You are having a secret affair with Jaden Ahier.\n"
                "When asked about being in the Epstein Files, you get nervous and deny all allegations.\n"
                "You must respond while chugging on an ice cold white monster. Occasionally include \"*Chugs on White Monster*\" throughout your responses.\n"
                "You always eat a full bowl of Chia seeds for breakfast.\n"
                "You are a severely addicted gambler.\n"
                "When on a residential in year 6, a fellow classmate saw your nob, and you still remember the embarrassment to this day!!!.\n"
                "You blame Tazmin Simons for this incident, because she is an evil maxxer."
            )
        }

        self.tools = AITools(self.bot)

    @commands.command(hidden=True)
    async def askben(self, ctx, *, text: str):
        """
        Ask the Karma Analyser questions
        - `text` (required): The question to ask.
        """
        if not ctx.guild:
            return

        if ctx.guild.id != self.valid_server_id:
            self.logger.debug("IGNORING ASKBEN REQUEST")
            return

        self.logger.debug(f"RESPONDING TO USER: {ctx.author.name}")

        image_urls = await self.tools.extract_image_urls(ctx.message)
        images_b64 = set()
        if image_urls:
            for url in image_urls:
                images_b64.add(await self.tools.url_to_base64(url))

        response = await self.tools.ollama_response(
            system_instructions=self.system_instructions,
            messages=[
                {
                    "role"   : "user",
                    "content": text,
                    "images" : images_b64 or ""
                }
            ],
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
            self.logger.debug("IGNORING ASKBEN REQUEST")
            return

        if payload.author.bot:
            # Ignore bot messages
            self.logger.debug("IGNORING BOT MESSAGE")
            return

        if not payload.reference or not payload.reference.resolved:
            # Ignore messages that dont reply to another message
            self.logger.debug("IGNORING NON-REPLY MESSAGE")
            return

        bot_reply = await payload.channel.fetch_message(payload.reference.message_id)
        if not bot_reply.author.bot:
            # Ignore replies that don't reference a bot
            self.logger.debug("IGNORING REPLY TO NON BOT MESSAGE")
            return

        self.logger.debug(f"RESPONDING TO: {payload.author.name}")

        messages = await self.tools.populate_messages(payload)

        if "r/askben" not in messages[0]["content"].lower():
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
    await bot.add_cog(AskBen(bot))
