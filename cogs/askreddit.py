import asyncio
import inspect
import json
import logging
import regex
import discord
from discord.ext import commands
from ollama import Client
from collections import OrderedDict
from tools import AITools


class AskReddit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

        self.model="artifish/llama3.2-uncensored"
        self.vision_model="llava"

        with open("settings.json", "r") as f:
            self.settings = json.load(f)

        self.client = Client(host=self.settings.get("ollama_endpoint"))

        self.message_cache = OrderedDict()
        self.cache_size = 1000

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

        response = await self.ollama_response(
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

        messages = await self.populate_messages(payload)

        if "r/askreddit" not in messages[0]["content"].lower():
            return

        response = await self.ollama_response(
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

    async def ollama_response(self, system_instructions, messages, server, user):
        """
        Generates an AI response using the ollama API.
        :param messages: Chat history messages
        :param server: Server ID the chat is taking place in
        :param user: user.name who triggered the request
        :return: AI response string
        """
        original_messages = messages = [system_instructions] + list(messages)

        while True:
            response = await asyncio.to_thread(
                self.client.chat,
                model=self.model,
                messages=messages,
                tools=self.tools
            )
            self.logger.debug(f"RESPONSE: {response.message.content}")

            tool_calls = response.message.tool_calls or []

            json_pattern = regex.compile(r"""
                (
                    \{ (?: [^{}]++ | (?R) )* \}
                  | \[ (?: [^\[\]]++ | (?R) )* \]
                )
            """, regex.VERBOSE)

            for j in json_pattern.findall(response.message.content):
                try:
                    data = json.loads(j)
                    if isinstance(data, dict) and data.get("type") == "function":
                        tool_calls.append(data)
                except:
                    continue

            if tool_calls:
                self.logger.debug(f"TOOL CALLS: {tool_calls}")

                for call in tool_calls:
                    if isinstance(call, dict):
                        function = call["function"]["name"]
                        args = call.get("parameters") or {}
                    else:
                        function = call.function.name
                        args = call.function.arguments or {}
                        if isinstance(args, dict) and "parameters" in args:
                            args = args["parameters"]

                    function = next((f for f in self.tools if f.__name__ == function), None)
                    if function:
                        sig = inspect.signature(function)
                        kwargs = {}

                        for param in sig.parameters.values():
                            if param.name == "server":
                                kwargs[param.name] = server
                            elif param.name == "user":
                                kwargs[param.name] = args.get("user") or user
                            elif param.name in args:
                                kwargs[param.name] = args[param.name]
                            elif param.default is not inspect.Parameter.empty:
                                kwargs[param.name] = param.default

                        self.logger.debug(f"Tool {function.__name__} called with {kwargs}")

                        if inspect.iscoroutinefunction(function):
                            result = await function(**kwargs)
                        else:
                            result = function(**kwargs)

                        self.logger.debug(f"TOOL RESULT: {result}")

                        messages.append({
                            "role": "tool",
                            "name": function,
                            "content": str(result)
                        })

                    else:
                        messages.append({
                            "role": "tool",
                            "name": function,
                            "content": "Tool doesn't exist"
                        })

                continue

            # Response Post-Processing
            reply = json_pattern.sub("", response.message.content).strip()

            # Fall back to response generation without tools if response is empty
            if reply == "":
                response = await asyncio.to_thread(
                    self.client.chat,
                    model=self.model,
                    messages=original_messages
                )
                self.logger.warning("FALLING BACK TO NON-TOOL RESPONSE")
                reply = response.message.content

            guild = self.bot.get_guild(server)
            if guild:
                for member in guild.members:
                    reply = regex.sub(
                        rf"\b{regex.escape(member.name)}\b",
                        member.mention,
                        reply,
                        flags=regex.IGNORECASE
                    )

            reply = regex.sub(
                r"(<think>.*?</think>|<json>.*?</json>)\n\n",
                "",
                reply,
                flags=regex.DOTALL
            )

            reply = regex.sub(
                r'\{"type"\s*:\s*"function"\s*,\s*"function"\s*:\s*',
                '',
                reply
            )

            self.logger.debug(f"FINAL REPLY: {reply}")
            return reply if reply.strip() else "RESPONSE GENERATION FAILED, PLEASE DOWNVOTE"

    async def populate_messages(self, payload):
        """
        Creates a message history from a single message,
        looking through all of it's replies
        :param payload: Message to start search from
        :return: Message history
        """
        messages = []
        current = await payload.channel.fetch_message(payload.reference.message_id)

        while current:
            image_urls = await AITools.extract_image_urls(current.message)
            images_b64 = set()
            for url in image_urls:
                images_b64.add(AITools.url_to_base64(url))

            messages.append({
                "role": "assistant" if current.author.bot else "user",
                "content": regex.sub(
                    r"<@!?(\d+)>",
                    lambda m: (current.guild.get_member(int(m.author.id))).name
                        if payload.guild.get_member(int(m.author.id)) else m.group(0),
                    current.content
                ),
                "images": images_b64 or ""
            })

            if current.reference:
                current = await self.get_message(current.channel, current.reference.message_id)

            else: break

        messages.reverse()

        # images = await self.get_images(payload)
        messages.append({
            "role": "user",
            "content": payload.content
        })

        return list(messages)

    async def get_message(self, channel: discord.TextChannel, message_id: int):
        """
        Helper function to find a message object, looks for a cached message
        first, falling back to the discord API if not found.
        :param channel: Channel to look in
        :param message_id: Message ID to look for
        :return: Message object
        """
        if message_id in self.message_cache:
            return self.message_cache[message_id]

        try:
            message = await channel.fetch_message(message_id)
            await self.cache_message(message_id, message)
            return message

        except (discord.NotFound, discord.Forbidden) as e:
            self.logger.error(f"FAILED TO GET MESSAGE: {e}")

    async def cache_message(self, message_id, message):
        """
        Cache a message object
        :param message_id: message ID to cache
        :param message: message object to cache
        :return:
        """
        self.message_cache[message_id] = message
        if len(self.message_cache) > self.cache_size:
            self.message_cache.popitem(last=False)


async def setup(bot):
    await bot.add_cog(AskReddit(bot))