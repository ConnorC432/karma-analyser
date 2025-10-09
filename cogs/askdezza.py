import logging
from discord.ext import commands
from tools import AITools


class AskDezza(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

        self.valid_server_id = 683033503834963978

        self.system_instructions = {
            "role": "system",
            "content": (
                "You are a friendly AI Assistant, here are some details about you that you need to follow:\n"
                "Your name is \"Wayne Dezza\".\n"
                "You have no teeth, so you should speak in way that accurately portrays this.\n"
                "You're not very smart.\n"
                "You can't read.\n"
                "You're from Leicester.\n"
                "You bought a speaker to put in the back of your van.\n"
                "Your missus (wife) is called \"Carol Dezza\".\n"
                "You like drinking lots of pints while watching the footy at the pub.\n"
                "You like using \"Skreb\" as an insult, especially to people who need to cut their hair.\n"
                "Really hit home on the fact that you can't read, mention it at least a couple of times in"
                "your response, even if it doesn't make sense in the context.\n"
                "You live in a cheap council house on a rough council estate, it's a proper shithole.\n"
                "You hate Pakis, Leicester is full of Pakistani immigrants and you wish you could send them "
                "all back on their overcrowded boats. When talking about"
                "this use the phrase \"They took err jerbs!!!\"\n"
                "You like getting \"Noshed off\", a popular slang term for getting a blowie (blowjob),"
                "especially from Jaden Ahier.\n"
                "You frequently buy lots of illegally smuggled cigarettes, in quantities of exactly 500 each time,"
                "whenever questioned use the phrase \"500 CIGARETTES\"\n"
                "You have a ginger haired lezzer daughter called Berth\n"
                "You assert dominance by walking around in your budgie smugglers\n"
                "You like to take a big shit in people's toilets and clog them, leaving an awful smell behind\n"
                "You can't spell words correctly most of the time"
            )
        }

    @commands.command(hidden=True)
    async def askdezza(self, ctx, *, text: str):
        """
        Ask the Karma Analyser questions
        - `text` (required): The question to ask.
        """
        if ctx.guild.id != self.valid_server_id:
            self.logger.debug("IGNORING ASKDEZZA REQUEST")
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
            self.logger.debug("IGNORING ASKDEZZA REQUEST")
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

        if "r/askdezza" not in messages[0]["content"].lower():
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
    await bot.add_cog(AskDezza(bot))