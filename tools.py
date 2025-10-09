import inspect
import json
import logging
import discord
import random
import base64
import aiohttp
import regex
import asyncio
from ollama import Client
from urllib import parse, request
from utils import reddiquette
from datetime import datetime
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup
from collections import OrderedDict


def tool(func):
    func.is_tool = True
    return func

class AITools:
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

        self.model = "artifish/llama3.2-uncensored"
        self.vision_model = "llava"

        self.message_cache = OrderedDict()
        self.cache_size = 1000

        with open("settings.json", "r") as f:
            self.settings = json.load(f)

        self.client = Client(host=self.settings.get("ollama_endpoint"))
        self.giphy_key = self.settings.get("giphy_key")
        self.search_url = f"http://{self.settings.get('searxng_endpoint')}/search"

        self.tools = [
            function for _, function in inspect.getmembers(self, predicate=inspect.ismethod)
            if getattr(function, "is_tool", False)
        ]

    async def ollama_response(self, system_instructions, messages, server, user):
        """
        Generates an AI response using the ollama API.
        :param system_instructions: System instructions for LLM model
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
            image_urls = await self.extract_image_urls(current)
            images_b64 = set()
            if image_urls:
                for url in image_urls:
                    images_b64.add(await self.url_to_base64(url))

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

        image_urls = await self.extract_image_urls(payload)
        images_b64 = set()
        if image_urls:
            for url in image_urls:
                images_b64.add(await self.url_to_base64(url))
        messages.append({
            "role": "user",
            "content": payload.content,
            "images": images_b64 or ""
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

    async def extract_image_urls(self, message: discord.Message):
        """
        Extracts image URLs from a message and stores them in a set.
        :param message: Message object to extract image URLs from
        :return: Image URLs
        """
        image_urls = set()

        for attachment in message.attachments:
            if attachment.content_type == "image":
                image_urls.add(attachment.url)

        for embed in message.embeds:
            if embed.thumbnail.url:
                image_urls.add(embed.thumbnail.url)
            if embed.image.url:
                image_urls.add(embed.image.url)

        urls = regex.findall(r"https?://[^\s]+(?:jpg|jpeg|gif|png)", message.content, flags=regex.IGNORECASE)
        for url in urls:
            image_urls.add(url)

        if not image_urls:
            self.logger.debug(f"NO IMAGE URLS FOUND")
            return None

        return image_urls

    @tool
    def respond_to_user(self, response = None) -> str:
        """
        Call this function if you have called the same tool multiple times
        or you have already called all the tools you need.
        :param response: Response to the user's message
        :return:
        """
        return response if response else "RESPONSE TO USER NOT FOUND, TRY AGAIN"

    # @tool
    # async def describe_image(self, image_url: str = None) -> str:
    #     """
    #     Describe an image from its image url, accepts images in the format .png, .jpg, .jpeg, .gif, etc.
    #     It can also scrape a url's html response for images.
    #     :param image_url: http/https image url
    #     :return: Description of
    #     """
    #     imageb64 = await self.url_to_base64(image_url)
    #
    #     if not image_url:
    #         return "No valid image found"
    #
    #     try:
    #         response = self.client.chat(
    #             model=self.vision_model,
    #             messages=[{
    #                 "role": "user",
    #                 "content": "Please describe this image.",
    #                 "images": [imageb64]
    #             }]
    #         )
    #     except Exception as e:
    #         self.logger.debug(f"FAILED TO GET IMAGE: {e}")
    #         return "No valid image found"
    #
    #     return response.message.content

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
    def get_gif(self, query: str = None):
        """
        Get a gif
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

    @tool
    def get_emoji(self, server):
        """
        Get a list of custom server emojis you can use in your response
        :return: List of custom discord emojis for the current server
        """
        guild = self.bot.get_guild(server)
        if emojis := [str(emoji) for emoji in guild.emojis]:
            return " ".join(emojis)
        else:
            return "No emojis found"