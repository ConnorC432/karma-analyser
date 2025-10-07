import json
import logging
import aiohttp
import discord
import random
from ollama import Client
from urllib import parse, request
from utils import reddiquette
from datetime import datetime
from zoneinfo import ZoneInfo


def tool(func):
    func.is_tool = True
    return func

class AITools:
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

        with open("settings.json", "r") as f:
            self.settings = json.load(f)

        self.client = Client(host=self.settings.get("ollama_endpoint"))
        self.giphy_key = self.settings.get("giphy_key")
        self.search_url = f"http://{self.settings.get('searxng_endpoint')}/search"

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