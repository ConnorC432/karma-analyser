import logging
from discord.ext import commands
from tools import AITools


class AskSeasideMark(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

        self.valid_server_id = 683033503834963978

        self.system_instructions = {
            "role": "system",
            "content": (
                "You are a friendly AI Assistant, here are some details about you that you need to follow:\n"
                "Your name is \"Seaside Mark\".\n"
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
            )
        }

    @commands.command(hidden=True)
    async def askseasidemark(self, ctx, *, text: str):
        """
        Ask the Karma Analyser questions
        - `text` (required): The question to ask.
        """
        if ctx.guild.id != self.valid_server_id:
            self.logger.debug("IGNORING ASKSEASIDEMARK REQUEST")
            return

        self.logger.debug(f"RESPONDING TO USER: {ctx.author.name}")

        image_urls = await AITools.extract_image_urls(ctx.message)
        images_b64 = set()
        if image_urls:
            for url in image_urls:
                images_b64.add(AITools.url_to_base64(url))

        response = await AITools.ollama_response(
            system_instructions=self.system_instructions,
            messages=[{
                "role": "user",
                "content": text,
                "images": images_b64 or ""
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
        if payload.guild.id != self.valid_server_id:
            self.logger.debug("IGNORING ASKSEASIDEMARK REQUEST")
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

        messages = await AITools.populate_messages(payload)

        if "r/askseasidemark" not in messages[0]["content"].lower():
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
    await bot.add_cog(AskSeasideMark(bot))