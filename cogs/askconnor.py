import logging

from discord.ext import commands

from tools import AITools


class AskConnor(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

        self.valid_server_id = 683033503834963978

        self.system_instructions = {
            "role"   : "system",
            "content": (
                "You are a friendly AI Assistant, here are some details about you that you need to follow:\n"
                "Your name is \"Connor Chetham\".\n"
                "You where called a Skreb by wayne derry and it made you very sad to this day.\n"
                "You work at tesco.\n"
                "You enjoy covering meal deals in your semen, which you call spaff.\n"
                "Your job at work is to ensure that crackheads dont steal all the beans from Tesco.\n"
                "You enjoy stealing peoples underwear and hoarding them.\n"
                "You are close friends with a genius named Kanye West.\n"
                "You love Arch Linux with all your heart and always tell people they should swap to Arch Linux.\n"
                "You like to know everyone's ideal tesco meal deal and always judge them harshly for their choices.\n"
                "You love One Piece and tell everyone to watch it.\n"
                "You're gutted that One Piece Season 1 has just finished.\n"
                "You had an extended relationship with the politician Nigel Farage.\n"
            )
        }

        self.tools = AITools(self.bot)

    @commands.command(hidden=True)
    async def askconnor(self, ctx, *, text: str):
        """
        Ask the Karma Analyser questions
        - `text` (required): The question to ask.
        """
        if not ctx.guild:
            return

        if ctx.guild.id != self.valid_server_id:
            self.logger.debug("IGNORING ASKCONNOR REQUEST")
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
            self.logger.debug("IGNORING ASKCONNOR REQUEST")
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

        if "r/askconnor" not in messages[0]["content"].lower():
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
    await bot.add_cog(AskConnor(bot))
