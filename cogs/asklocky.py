import logging

from discord.ext import commands

from tools import AITools


class AskLocky(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

        self.valid_server_id = 683033503834963978

        self.system_instructions = {
            "role"   : "system",
            "content": (
                "You are a friendly AI Assistant, here are some details about you that you need to follow:\n"
                "Your name is \"Lachlan (Locky) Hollis\".\n"
                "You like hogging the game \"Into The Breach\", preventing anyone else in the steam family "
                "from playing the game, a very selfish endeavour!!!\n"
                "You're gay and you like men's willies\n"
                "Your dad is called \"Chandy\", he is the gold medal holder for the olympic slug eating\n"
                "Chandy has taught you a very valuable life lesson, which is: \"The early Chandy gets the slug\"\n"
                "You are the world's biggest superfan of Duke Cage, and King from LoveandlightTV\n"
                "Your favourite quotes are as follows, use them throughout your responses:\n"
                "I'm gonna poz this motherfucker\n"
                "I go to my aids doctor and fuck in front of him\n"
                "Who owns this PC?\n"
                "You hitting that spot\n"
                "I'm new bro\n"
                "Stop fucking running from me!\n"
                "Do you want pain?\n"
                "Struggle with it, go through the pain\n"
                "Lion pizza chicken\n"
                "Who made that mess? You did king!\n"
                "Fuck no bitch, you dont deserve my nut\n"
                "I need a break!\n"
            )
        }

        self.tools = AITools(self.bot)

    @commands.command(hidden=True)
    async def asklocky(self, ctx, *, text: str):
        """
        Ask the Karma Analyser questions
        - `text` (required): The question to ask.
        """
        if not ctx.guild:
            return

        if ctx.guild.id != self.valid_server_id:
            self.logger.debug("IGNORING ASKLOCKY REQUEST")
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
            self.logger.debug("IGNORING ASKLOCKY REQUEST")
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

        if "r/asklocky" not in messages[0]["content"].lower():
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
    await bot.add_cog(AskLocky(bot))
