import asyncio
import base64
import inspect
import json
import logging
import os
from collections import OrderedDict
from datetime import datetime
from json import JSONDecodeError
from zoneinfo import ZoneInfo

import aiohttp
import discord
import regex
from bs4 import BeautifulSoup
from ollama import Client

import utils
from utils import karmic_dict


REDDIQUETTE = (
    "Dos: \n"
    "⦁ Remember the human. When you communicate online, all you see is a computer screen. When talking to someone you might want to ask yourself Would I say it to the person's face? or Would I get jumped if I said this to a buddy? \n"
    "⦁ Adhere to the same standards of behavior online that you follow in real life. \n"
    "⦁ Read the rules of a community before making a submission. These are usually found in the sidebar. \n"
    "⦁ Read the reddiquette. Read it again every once in a while. Reddiquette is a living, breathing, working document which may change over time as the community faces new problems in its growth. \n"
    "⦁ Moderate based on quality, not opinion. Well written and interesting content can be worthwhile, even if you disagree with it. \n"
    "⦁ Use proper grammar and spelling. Intelligent discourse requires a standard system of communication. Be open for gentle corrections. \n"
    "⦁ Keep your submission titles factual and opinion free. If it is an outrageous topic, share your crazy outrage in the comment section. \n"
    "⦁ Look for the original source of content, and submit that. Often, a blog will reference another blog, which references another, and so on with everyone displaying ads along the way. Dig through those references and submit a link to the creator, who actually deserves the traffic. \n"
    "⦁ Post to the most appropriate community possible. Also, consider cross posting if the contents fits more communities. \n"
    "⦁ Vote. If you think something contributes to conversation, upvote it. If you think it does not contribute to the subreddit it is posted in or is off-topic in a particular community, downvote it. \n"
    "⦁ Search for duplicates before posting. Redundancy posts add nothing new to previous conversations. That said, sometimes bad timing, a bad title, or just plain bad luck can cause an interesting story to fail to get noticed. Feel free to post something again if you feel that the earlier posting didn't get the attention it deserved and you think you can do better.  \n"
    "⦁ Link to the direct version of a media file if the page it was found on isn't the creator's and doesn't add additional information or context. \n"
    "⦁ Link to canonical and persistent URLs where possible, not temporary pages that might disappear.In particular, use the permalink for blog entries, not the blog's index page. \n"
    "⦁ Consider posting constructive criticism / an explanation when you downvote something, and do so carefully and tactfully. \n"
    "⦁ Report any spam you find. \n"
    "⦁ Actually read an article before you vote on it ( as opposed to just basing your vote on the title). \n"
    "⦁ Feel free to post links to your own content (within reason).But if that's all you ever post, or it always seems to get voted down, take a good hard look in the mirror — you just might be a spammer. A widely used rule of thumb is the 9:1 ratio, i.e. only 1 out of every 10 of your submissions should be your own content. \n"
    "⦁ Posts containing explicit material such as nudity, horrible injury etc, add NSFW (Not Safe For Work) and tag. However, if something IS safe for work, but has a risqué title, tag as SFW (Safe for Work). Additionally, use your best judgement when adding these tags, in order for everything to go swimmingly. \n"
    "⦁ State your reason for any editing of posts. Edited submissions are marked by an asterisk (*) at the end of the timestamp after three minutes. For example: a simple Edit: spelling will help explain. This avoids confusion when a post is edited after a conversation breaks off from it. If you have another thing to add to your original comment, say Edit: And I also think... or something along those lines. \n"
    "⦁ Use an Innocent until proven guilty mentality. Unless there is obvious proof that a submission is fake, or is whoring karma, please don't say it is. It ruins the experience for not only you, but the millions of people that browse Reddit every day. \n"
    "⦁ Read over your submission for mistakes before submitting, especially the title of the submission. Comments and the content of self posts can be edited after being submitted, however, the title of a post can't be. Make sure the facts you provide are accurate to avoid any confusion down the line.  \n"
    "Don'ts: \n"
    "⦁ Engage in illegal activity. \n"
    "⦁ Post someone's personal information, or post links to personal information. This includes links to public Facebook pages and screenshots of Facebook pages with the names still legible. We all get outraged by the ignorant things people say and do online, but witch hunts and vigilantism hurt innocent people too often, and such posts or comments will be removed. Users posting personal info are subject to an immediate account deletion. If you see a user posting personal info, please contact the admins. Additionally, on pages such as Facebook, where personal information is often displayed, please mask the personal information and personal photographs using a blur function, erase function, or simply block it out with color. When personal information is relevant to the post (i.e. comment wars) please use color blocking for the personal information to indicate whose comment is whose. \n"
    "⦁ Repost deleted/removed information. Remember that comment someone just deleted because it had personal information in it or was a picture of gore? Resist the urge to repost it. It doesn't matter what the content was. If it was deleted/removed, it should stay deleted/removed. \n"
    "⦁ Be (intentionally) rude at all. By choosing not to be rude, you increase the overall civility of the community and make it better for all of us. \n"
    "⦁ Follow those who are rabble rousing against another redditor without first investigating both sides of the issue that's being presented. Those who are inciting this type of action often have malicious reasons behind their actions and are, more often than not, a troll. Remember, every time a redditor who's contributed large amounts of effort into assisting the growth of community as a whole is driven away, projects that would benefit the whole easily flounder. \n"
    "⦁ Ask people to Troll others on Reddit, in real life, or on other blogs/sites. We aren't your personal army. \n"
    "⦁ Conduct personal attacks on other commenters. Ad hominem and other distracting attacks do not add anything to the conversation. \n"
    "⦁ Start a flame war. Just report and walk away. If you really feel you have to confront them, leave a polite message with a quote or link to the rules, and no more. \n"
    "⦁ Insult others. Insults do not contribute to a rational discussion. Constructive Criticism, however, is appropriate and encouraged. \n"
    "⦁ Troll. Trolling does not contribute to the conversation. \n"
    "⦁ Take moderation positions in a community where your profession, employment, or biases could pose a direct conflict of interest to the neutral and user driven nature of Reddit. \n"
)


## Tool decorator
def tool(func):
    func.is_tool = True
    return func


class AITools:

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(self.__class__.__name__)

        self.model = "artifish/llama3.2-uncensored"
        self.vision_model = "llava"

        self.message_cache = OrderedDict()
        self.cache_size = 1000

        self.ollama_endpoint = os.getenv("OLLAMA_ENDPOINT")
        self.searxng_endpoint = os.getenv("SEARXNG_ENDPOINT")

        if not self.ollama_endpoint:
            raise ValueError("OLLAMA_ENDPOINT environment variable is not set")

        if not self.searxng_endpoint:
            raise ValueError("SEARXNG_ENDPOINT environment variable is not set")

        self.client = Client(host=self.ollama_endpoint)
        self.search_url = f"http://{self.searxng_endpoint}/search"

        self.tools = [
            function for _, function in inspect.getmembers(self, predicate=inspect.ismethod)
            if getattr(function, "is_tool", False)
        ]

    async def ollama_response(
            self, system_instructions, messages, server, user, model: str | None = None
    ) -> str | None:
        """
        Generates an AI response using the ollama API.
        :param system_instructions: System instructions for LLM model
        :param messages: Chat history messages
        :param server: Server ID the chat is taking place in
        :param user: user.name who triggered the request
        :param model: Optional - model to use for text generation
        :return: AI response string
        """
        use_tools = False
        if model is None:
            model = self.model
            use_tools = True

        original_messages = messages = [system_instructions] + list(messages)

        while True:
            try:
                response = await asyncio.to_thread(
                    self.client.chat,
                    model=model,
                    messages=messages,
                    tools=self.tools if use_tools else ""
                )
            except Exception as e:
                self.logger.error(f"Error calling Ollama API: {e}")
                return "RESPONSE GENERATION FAILED, PLEASE DOWNVOTE"

            self.logger.debug(f"RESPONSE: {response.message.content}")

            tool_calls = response.message.tool_calls or []

            json_pattern = regex.compile(
                r"""
                    (
                        \{ (?: [^{}]++ | (?R) )* \}
                      | \[ (?: [^\[\]]++ | (?R) )* \]
                    )
                """, regex.VERBOSE
            )

            for j in json_pattern.findall(response.message.content):
                try:
                    data = json.loads(j)
                    if isinstance(data, dict) and data.get("type") == "function":
                        tool_calls.append(data)
                except JSONDecodeError as e:
                    self.logger.error(e)
                    continue

            if tool_calls:
                # self.logger.debug(f"TOOL CALLS: {tool_calls}")

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

                        messages.append(
                            {
                                "role"   : "tool",
                                "name"   : function,
                                "content": str(result)
                            }
                        )

                    else:
                        messages.append(
                            {
                                "role"   : "tool",
                                "name"   : function,
                                "content": "Tool doesn't exist"
                            }
                        )

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

            messages.append(
                {
                    "role"   : "assistant" if current.author.bot else "user",
                    "content": regex.sub(
                        r"<@!?(\d+)>",
                        lambda m: (current.guild.get_member(int(m.author.id))).name
                        if payload.guild.get_member(int(m.author.id)) else m.group(0),
                        current.content
                    ),
                    "images" : images_b64 if images_b64 else "",
                }
            )

            if current.reference:
                current = await self.get_message(current.channel, current.reference.message_id)

            else:
                break

        messages.reverse()

        image_urls = await self.extract_image_urls(payload)
        images_b64 = set()
        if image_urls:
            for url in image_urls:
                images_b64.add(await self.url_to_base64(url))
        messages.append(
            {
                "role"   : "user",
                "content": payload.content,
                "images" : images_b64 if images_b64 else ""
            }
        )

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

        except aiohttp.ClientError as e:
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

        urls = regex.findall(r"https?://[^\s]+", message.content, flags=regex.IGNORECASE)
        for url in urls:
            if url.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
                image_urls.add(url)

            else:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=10) as response:
                            content_type = response.headers.get("Content-Type", "")
                            if "text/html" in content_type:
                                html = await response.text()
                                soup = BeautifulSoup(html, "html.parser")

                                # og:image
                                og_image = soup.find("meta", property="og:image")
                                if og_image and og_image.get("content"):
                                    image_urls.add(og_image["content"])

                                elif (img := soup.find("img")) and img.get("src"):
                                    image_urls.add(img["src"])

                except aiohttp.ClientError as e:
                    self.logger.debug(f"Failed to fetch HTML page {url}: {e}")

        if not image_urls:
            self.logger.debug("NO IMAGE URLS FOUND")
            return None

        return image_urls

    @tool
    def respond_to_user(self, response=None) -> str:
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
        if karmic_dict:
            return karmic_dict[server.id]

        return "No data found"

    @tool
    async def get_gif(self, query: str = None):
        """
        Get a gif
        :param query: GIF Search query - does not accept http/https format
        :return: A URL containing the gif
        """
        gif_url = await utils.gif_search(query)
        return f"INCLUDE THE FULL URL IN YOUR RESPONSE, AS LONG AS THE GIF IS RELEVANT TO THE TEXT: {gif_url}"

    @tool
    def get_reddiquette(self):
        """
        Returns the reddiquette that users must follow on the server
        :return: Reddiquette
        """
        return str(REDDIQUETTE)

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

    # noinspection PyIncorrectDocstring
    # Docstring passed through in tool list, AI isn't intended to know about the "server" variable
    @tool
    def get_server_members(self, server, online=False):
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
            "q"         : query,
            "format"    : "json",
            "categories": "general",
            "count"     : 5
        }

        results = []
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.search_url, params=params, timeout=10) as response:
                    if response.status != 200:
                        return f"Search failed with status {response.status}"
                    data = await response.json()
            except aiohttp.ClientError as e:
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
