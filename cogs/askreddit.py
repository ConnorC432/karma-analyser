import base64
import asyncio
import inspect
import json
import logging
import regex
import aiohttp
import discord
import random
from discord.ext import commands
from ollama import Client
from bs4 import BeautifulSoup
from collections import OrderedDict
from urllib import parse, request
from utils import reddiquette
from datetime import datetime
from zoneinfo import ZoneInfo


def tool(func):
    func.is_tool = True
    return func

class AskReddit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

        self.model="artifish/llama3.2-uncensored"
        self.vision_model="llava"

        with open("settings.json", "r") as f:
            self.settings = json.load(f)

        self.client = Client(host=self.settings.get("ollama_endpoint"))

        self.giphy_key = self.settings.get("giphy_key")
        self.search_url = f"http://{self.settings.get('searxng_endpoint')}/search"

        self.message_cache = OrderedDict()
        self.cache_size = 1000

        self.tools = [
            function for _, function in inspect.getmembers(self, predicate=inspect.ismethod)
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

        response = await self.ollama_response(messages=[{
            "role": "user",
            "content": text
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
            messages=messages,
            server=payload.guild.id,
            user=payload.author.name
        )

        if response:
            reply = await payload.reply(content=response[:2000])
            self.logger.info(f"RESPONSE: {response[:2000]}")
            if response == "RESPONSE GENERATION FAILED, PLEASE DOWNVOTE":
                await reply.add_reaction("<:reddit_downvote:1266139651660447744>")

    async def url_to_base64(self, url: str) -> str:
        """
        Converts an image URL to a base64 encoded string.
        :param url: Image URL
        :return: Base64 encoded string
        """
        try:
            async with aiohttp.ClientSession() as session:
                tries = 0

                while url and tries < 5:
                    async with session.get(url, timeout=10) as response:
                        content_type = response.headers.get("Content-Type", "")
                        if "image" in content_type:
                            data = await response.read()
                            return base64.b64encode(data).decode("utf-8")

                        elif "text/html" in content_type:
                            self.logger.debug(f"HTML found: {url}")
                            html = await response.content.read()
                            soup = BeautifulSoup(html, "html.parser")

                            og_image = soup.find("meta", property="og:image")
                            if og_image and og_image.get("content"):
                                url = og_image["content"]
                                tries += 1
                                continue

                        else:
                            self.logger.debug(f"NO IMAGE IN URL: {url}")
                            return None

        except Exception as e:
            self.logger.error(f"FAILED TO FETCH URL {url}: {e}")
            return None

    async def ollama_response(self, messages, server, user):
        """
        Generates an AI response using the ollama API.
        :param messages: Chat history messages
        :param server: Server ID the chat is taking place in
        :param user: user.name who triggered the request
        :return: AI response string
        """
        original_messages = messages = [self.system_instructions] + list(messages)

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

            ## TODO rearrange post processing to after fallback response and remove <json> tags aswell
            ## TODO increase model context size to 8k plus
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
                        rf"\b{regex.escape(member)}\b",
                        member.mention,
                        reply,
                        flags=regex.IGNORECASE
                    )

            reply = regex.sub(
                r"<think>.*?</think>\n\n",
                "",
                reply,
                flags=regex.DOTALL
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
            messages.append({
                "role": "assistant" if current.author.bot else "user",
                "content": current.content
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


    ### Ollama Tools
    @tool
    def respond_to_user(response = None) -> str:
        """
        This function does nothing.
        Call this function if you have called the same tool multiple times
        or you have already called all the tools you need.
        :param response: Response to the user's message
        :return:
        """
        return response if response else "RESPONSE TO USER NOT FOUND, TRY AGAIN"

    @tool
    async def describe_image(self, image_url: str = None) -> str:
        """
        Describe an image from its image url, accepts images in the format .png, .jpg, .jpeg, .gif, etc.
        It can also scrape a url's html response for images.
        :param image_url: http/https image url
        :return: Description of
        """
        imageb64 = await self.url_to_base64(image_url)

        if not image_url:
            return "No valid image found"

        try:
            response = self.client.chat(
                model=self.vision_model,
                messages=[{
                    "role": "user",
                    "content": "Please describe this image.",
                    "images": [imageb64]
                }]
            )
        except Exception as e:
            self.logger.debug(f"FAILED TO GET IMAGE: {e}")
            return "No valid image found"

        return response.message.content

    @tool
    def get_server_karma(self, server):
        """
        Get the statistics for all users within the server, containing:
            - Messages
            - Karma
            - Karmic Emoji Counts
        :return: A JSON formatted list of the stats for all members in the server
        """
        try:
            with open("karma.json", "r") as f:
                data = json.load(f)
        except FileNotFoundError as e:
            self.logger.error(f"karma.json NOT FOUND: {e}")
            return "No data found"
        except json.decoder.JSONDecodeError as e:
            self.logger.error(f"INVALID karma.json: {e}")
            return "No data found"

        try:
            karma = data[str(server)]
        except KeyError as e:
            self.logger.error(f"USER'S KARMA NOT FOUND: {e}")
            return "No data found"

        if karma:
            return str(karma)

        return "No data found"

    @tool
    def search_for_gif(self, query: str = None):
        """
        Search for a gif
        :param query: GIF Search query - does not accept http/https format
        :return: A URL containing the gif
        """
        if not self.giphy_key:
            self.logger.error("GIPHY KEY NOT FOUND")
            return "No giphy API key found"

        if not query:
            self.logger.error("SEARCH QUERY NOT FOUND")
            return ("No search query found. "
                    "Please call this tool with a meaningful query, "
                    "such as \"cat\", \"reaction\" or \"yes\".")

        else:
            giphy_url = "https://api.giphy.com/v1/gifs/search"
            params = parse.urlencode({
                "q": query,
                "api_key": self.giphy_key,
                "limit": 5
            })
            self.logger.debug(f"GETTING 5 GIFS: {query}")

        try:
            with request.urlopen(f"{giphy_url}?{params}") as response:
                data = json.loads(response.read())

        except Exception as e:
            self.logger.error(f"FAILED TO GET GIF: {e}")
            return "Failed to get gif."

        items = data.get("data", [])
        if not items:
            self.logger.error("GIFS NOT FOUND")
            return "No data found"

        gif_urls = [item["images"]["original"]["url"] for item in items]
        return f"INCLUDE THE FULL URL IN YOUR RESPONSE, AS LONG AS THE GIF IS RELEVANT TO THE TEXT: {random.choice(gif_urls)}"

    @tool
    def get_reddiquette(self):
        """
        Returns the reddiquette that users must follow on the server
        :return: Reddiquette
        """
        return str(reddiquette)

    @tool
    def get_server_name(self, server):
        """
        Get the name of the server that the chat is taking place in
        :return: Server name
        """
        guild = self.bot.get_guild(server)
        return guild.name

    @tool
    def get_datetime(self):
        """
        Get the current date & time for Europe/London
        :return: Current date & time for Europe/London
        """
        return str(datetime.now(ZoneInfo("Europe/London")))

    @tool
    def get_server_members(self, server, online = False):
        """
        Get the members of the current server
        :param online: bool - True to filter by online users, False to get all users
        :return:
        """
        guild = self.bot.get_guild(server)
        if online:
            return [member.name for member in guild.members
                              if member.status != discord.Status.offline]

        return guild.members

    @tool
    def get_users_roles(self, server, user = None):
        """
        Get the roles of the current user
        :param user: User to get the roles for
        :return: Users roles
        """
        if not user:
            return "No user argument given"

        guild = self.bot.get_guild(server)
        member = discord.utils.find(lambda m: m.name == user or (m.nick and m.nick == user),
                                    guild.members)

        if not member:
            return "Can't find roles"

        return [role.name for role in member.roles
                if role.name != "@everyone"]

    @tool
    async def google_search(self, query: str = None):
        """
        Perform a google search and return the top 5 results.
        :param query: Search query
        :return: Formatted string of the top 5 results
        """
        if not query:
            return "No search query found"

        params = {
            "q": query,
            "format": "json",
            "categories": "general",
            "count": 5
        }

        results = []
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.search_url, params=params, timeout=10) as response:
                    if response.status != 200:
                        return f"Search failed with status {response.status}"
                    data = await response.json()
            except Exception as e:
                self.logger.error(f"SEARCH FAILED: {e}")
                return "Failed to get search results."

        for item in data.get("results", [])[:5]:
            title = item.get("title")
            url = item.get("url")
            if title and url:
                results.append(f"{title}: {url}")

        if not results:
            return "No results found"

        return " | ".join(results)

async def setup(bot):
    await bot.add_cog(AskReddit(bot))