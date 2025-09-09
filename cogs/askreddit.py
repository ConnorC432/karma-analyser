import base64
import asyncio
import json
import logging
import re
import aiohttp
import discord
from discord.ext import commands
from ollama import Client
from bs4 import BeautifulSoup
from collections import deque


class AskReddit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

        with open("settings.json", "r") as f:
            self.settings = json.load(f)

        self.client = Client(host=self.settings.get("ollama_endpoint"))

    @commands.command()
    async def askreddit(self, ctx, *, text: str):
        """
        Ask the Karma Analyser questions
        - `text` (required): The question to ask.
        """
        response = await self.ollama_response(image=False, messages=[{
            "role": "user",
            "content": text
        }])
        await ctx.reply(response[:2000])
        self.logger.info(f"RESPONSE: {response[:2000]}")

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

        images = await self.get_images(payload)
        messages = await self.populate_messages(payload)

        if "r/askreddit" not in messages[0]["content"].lower():
            return

        response = await self.ollama_response(image=(True if images else False), messages=messages)

        await payload.reply(response[:2000])
        self.logger.info(f"RESPONSE: {response[:2000]}")

    async def get_images(self, payload):
        urls = []

        if payload.attachments:
            for attachment in payload.attachments:
                self.logger.debug(f"Attachment: {attachment.url}")
                urls.append(attachment.url)

        elif payload.embeds:
            for embed in payload.embeds:
                self.logger.debug(f"Embed: {embed.url}")
                urls.append(embed.url)

        else:
            self.logger.debug(f"No attachments/embeds found")
            return []

        images = []
        visited = set()
        queue = deque(urls)

        async with aiohttp.ClientSession() as session:
            while queue and len(images) < 4:
                url = queue.popleft()
                if url in visited:
                    continue

                try:
                    async with session.get(url, timeout=10) as response:
                        content_type = response.headers["Content-Type"]

                        if "image" in content_type:
                            self.logger.debug(f"Image found: {url}")
                            data = await response.content.read()
                            images.append(base64.b64encode(data).decode("utf-8"))
                            break

                        elif "text/html" in content_type:
                            self.logger.debug(f"HTML found: {url}")
                            html = await response.content.read()
                            soup = BeautifulSoup(html, "html.parser")

                            og_image = soup.find("meta", property="og:image")
                            if og_image and og_image.get("content"):
                                queue.append(og_image["content"])

                except Exception as e:
                    self.logger.error(f"FAILED TO GET IMAGE: {e}")

        return images

    async def ollama_response(self, image, messages):
        response = await asyncio.to_thread(
            self.client.chat,
            model="llava" if image else "artifish/llama3.2-uncensored",
            messages=messages
        )

        return re.sub(r"<think>.*?</think>\\n\\n", "", response.message.content, flags=re.DOTALL)

    async def populate_messages(self, payload):
        messages = []
        current = await payload.channel.fetch_message(payload.reference.message_id)

        while current:
            messages.append({
                "role": "assistant" if current.author.bot else "user",
                "content": current.content
            })

            if current.reference:
                try:
                    current = await current.channel.fetch_message(current.reference.message_id)
                except (discord.NotFound, discord.Forbidden) as e:
                    self.logger.error(f"FAILED TO GET MESSAGE: {e}")
                    break

            else: break

        messages.reverse()

        images = await self.get_images(payload)
        messages.append({
            "role": "user",
            "content": payload.content,
            "images": images if images else ""
        })

        return list(messages)


async def setup(bot):
    await bot.add_cog(AskReddit(bot))