import logging

from discord.ext import commands

from tools import AITools


class AskCog(commands.Cog):
    def __init__(
        self,
        bot,
        askbot_name,
        system_instructions,
        valid_server_ids=None,
        model="dolphin-llama3",
    ):
        """
        :param bot: Discord bot object
        :param askbot_name: Name of the askbot instance
        :param system_instructions: System instructions for the askbot
        :param valid_server_ids: Optional server ID(s) for which the askbot will be limited to
        :param model: Optional model name for the askbot
        """
        self.bot = bot
        self.logger = logging.getLogger(self.__class__.__name__)
        self.askbot_name = askbot_name.lower()
        self.system_instructions = system_instructions
        self.valid_server_ids = valid_server_ids
        if isinstance(self.valid_server_ids, int):
            self.valid_server_ids = [self.valid_server_ids]
        self.model = model
        self.tools = AITools(self.bot)

    async def _get_images(self, message):
        image_urls = await self.tools._extract_image_urls(message)
        images_b64 = set()
        if image_urls:
            for url in image_urls:
                images_b64.add(await self.tools._url_to_base64(url))
        return images_b64

    async def _handle_response(self, response, target):
        if response:
            reply = await target.reply(content=response[:2000])
            self.logger.debug(f"RESPONSE: {response[:2000]}")
            if response == "RESPONSE GENERATION FAILED, PLEASE DOWNVOTE":
                await reply.add_reaction("<:reddit_downvote:1266139651660447744>")

    async def _run_ask(self, ctx, text: str):
        if not ctx.guild:
            return

        if self.valid_server_ids and (ctx.guild.id not in self.valid_server_ids):
            self.logger.debug(f"IGNORING {self.askbot_name.upper()} REQUEST")
            return

        self.logger.debug(f"RESPONDING TO USER: {ctx.author.name}")

        images_b64 = await self._get_images(ctx.message)

        response = await self.tools.ollama_response(
            system_instructions=self.system_instructions,
            messages=[
                {
                    "role": "user",
                    "content": text,
                    "images": images_b64 or "",
                    "image": images_b64 or "",  # Support both for compatibility
                }
            ],
            server=ctx.guild.id if ctx.guild else None,
            user=ctx.author.name,
            model=self.model,
        )

        await self._handle_response(response, ctx)

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild:
            return

        if self.valid_server_ids and (message.guild.id not in self.valid_server_ids):
            return

        if message.author.bot:
            return

        if not message.reference or not message.reference.resolved:
            return

        bot_reply = await message.channel.fetch_message(message.reference.message_id)
        if not bot_reply.author.bot:
            return

        self.logger.debug(f"RESPONDING TO: {message.author.name}")

        messages = await self.tools._populate_messages(message)

        if f"r/ask{self.askbot_name}" not in messages[0]["content"].lower():
            return

        response = await self.tools.ollama_response(
            system_instructions=self.system_instructions,
            messages=messages,
            server=message.guild.id if message.guild else None,
            user=message.author.name,
            model=self.model,
        )

        await self._handle_response(response, message)
