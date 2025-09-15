import base64
import asyncio
import inspect
import json
import logging
import re
import aiohttp
import discord
import random
from discord.ext import commands
from ollama import Client
from bs4 import BeautifulSoup
from collections import OrderedDict
from urllib import parse, request
from .utils import reddiquette
from datetime import datetime, timezone


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

        self.message_cache = OrderedDict()
        self.cache_size = 1000

        ## TODO Fix get_gif tool, its intended use confuses the AI
        self.tools = [
            self.describe_image,
            self.get_server_karma,
            # self.get_gif_url,
            self.get_reddiquette,
            self.get_message_user,
            self.get_message_server,
            self.get_datetime,
            self.get_server_members,
            self.get_users_roles
        ]

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
            await ctx.reply(content=response[:2000])
            self.logger.debug(f"RESPONSE: {response[:2000]}")

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
            await payload.reply(content=response[:2000])
            self.logger.info(f"RESPONSE: {response[:2000]}")

    async def url_to_base64(self, url: str) -> str:
        try:
            async with aiohttp.ClientSession() as session:
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
                            return base64.b64encode(og_image["content"]).decode("utf-8")

                    else:
                        self.logger.debug(f"NO IMAGE IN URL: {url}")
                        return None

        except Exception as e:
            self.logger.error(f"FAILED TO FETCH URL {url}: {e}")
            return None

    # async def get_images(self, payload):
    #     urls = []
    #
    #     if payload.attachments:
    #         for attachment in payload.attachments:
    #             self.logger.debug(f"Attachment: {attachment.url}")
    #             urls.append(attachment.url)
    #
    #     elif payload.embeds:
    #         for embed in payload.embeds:
    #             self.logger.debug(f"Embed: {embed.url}")
    #             urls.append(embed.url)
    #
    #     else:
    #         self.logger.debug(f"No attachments/embeds found")
    #         return []
    #
    #     images = []
    #     visited = set()
    #     queue = deque(urls)
    #
    #     while queue and len(images) < 4:
    #         url = queue.popleft()
    #         if url in visited:
    #             continue
    #         visited.add(url)
    #
    #         image_b64 = await self.url_to_base64(url)
    #         if image_b64:
    #             images.append(image_b64)
    #
    #     return images[0] if images else None

    async def ollama_response(self, messages, server, user):
        response = await asyncio.to_thread(
            self.client.chat,
            model=self.model,
            messages=messages,
            tools=self.tools
        )

        if response.message.tool_calls:
            for call in response.message.tool_calls:
                function = call.function.name
                args = call.function.arguments

                function = next((f for f in self.tools if f.__name__ == function), None)
                if function:
                    sig = inspect.signature(function)
                    kwargs = {}

                    for param in sig.parameters.values():
                        if param.name in ("server", "user"):
                            kwargs[param.name] = server if param.name == "server" else user
                        elif param.name in args:
                            kwargs[param.name] = args[param.name]

                    if inspect.iscoroutinefunction(function):
                        result = await function(**kwargs)
                    else:
                        result = function(**kwargs)

                    self.logger.debug(f"Tool {function.__name__} called with {args}, returning: {result}")

                    messages.append({
                        "role": "tool",
                        "name": function,
                        "content": f"{function.__name__}: {str(result)}"
                    })

                    response = await asyncio.to_thread(
                        self.client.chat,
                        model=self.model,
                        messages=messages,
                        tools=self.tools
                    )

                else:
                    return "Tool not found"

        # Response Post-Processing
        reply = re.sub(r"<think>.*?</think>\\n\\n", "", response.message.content, flags=re.DOTALL)
        guild = self.bot.get_guild(server)
        if guild:
            for member in guild.members:
                reply = re.sub(rf"\b{member}\b", member.mention, reply, flags=re.IGNORECASE)

        self.logger.debug(f"REPLY: {reply}")
        return reply if reply else "RESPONSE GENERATION FAILED, PLEASE DOWNVOTE"

    async def populate_messages(self, payload):
        messages = []
        current = await payload.channel.fetch_message(payload.reference.message_id)

        while current:
            messages.append({
                "role": "assistant" if current.author.bot else "user",
                "content": f"{current.author.name} | {current.content}"
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
        if message_id in self.message_cache:
            return self.message_cache[message_id]

        try:
            message = await channel.fetch_message(message_id)
            await self.cache_message(message_id, message)
            return message

        except (discord.NotFound, discord.Forbidden) as e:
            self.logger.error(f"FAILED TO GET MESSAGE: {e}")

    async def cache_message(self, message_id, message):
        self.message_cache[message_id] = message
        if len(self.message_cache) > self.cache_size:
            self.message_cache.popitem(last=False)


    ### Ollama Tools
    async def describe_image(self, image: str) -> str:
        """
        Describe an image from its image url, accepts images in the format .png, .jpg, .jpeg, .gif, etc.
        It can also scrape a url's html response for images.
        :param image: image url
        :return:
        """
        imageb64 = await self.url_to_base64(image)

        if not image:
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

    def get_server_karma(self, server):
        """
        Get the statistics for all users within the server, containing:
            - Messages
            - Karma
            - Karmic Emoji Counts

        :param server: Optional
        :param user: Optional
        :return List of all user's statistics (JSON):
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

    def get_gif_url(self, query: str = None):
        """
        Search for a gif url

        :param query: Required search query
        :return gif url:
        """
        if not self.giphy_key:
            self.logger.error("GIPHY KEY NOT FOUND")
            return "No giphy API key found"

        if not query:
            self.logger.error("SEARCH QUERY NOT FOUND")
            return "No search query found"

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
        return random.choice(gif_urls)

    def get_reddiquette(self):
        """
        Returns the reddiquette that users must follow on the server
        :return reddiquette:
        """
        return str(reddiquette)

    def get_message_user(self, user):
        """
        Gets the User's discord name
        :param user: Optional
        :return name:
        """
        return user

    def get_message_server(self, server):
        """
        Get the server that the chat is taking place in
        :param server: Optional
        :return server name:
        """
        guild = self.bot.get_guild(server)
        return guild.name

    def get_datetime(self):
        """
        Get the current UTC date & time
        :return time:
        """
        return str(datetime.now(timezone.utc))

    def get_server_members(self, server, online):
        """
        Get the members of the current server
        :param server: Optional
        :param online: bool - True to filter by online users
        :return list of members:
        """
        guild = self.bot.get_guild(server)
        if online:
            return [member.name for member in guild.members
                              if member.status != discord.Status.offline]

        return guild.members

    def get_users_roles(self, server, user):
        """
        Get the roles of the current user
        :param server: Optional
        :param user: Optional
        :return list of roles:
        """
        guild = self.bot.get_guild(server)
        member = discord.utils.find(lambda m: m.name == user or (m.nick and m.nick == user),
                                    guild.members)

        if not member:
            return "Can't find roles"

        return [role.name for role in member.roles
                if role.name != "@everyone"]

async def setup(bot):
    await bot.add_cog(AskReddit(bot))