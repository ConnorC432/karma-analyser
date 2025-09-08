import base64
import datetime
import asyncio
import json
import re

import aiohttp
from discord.ext import commands, tasks
from ollama import Client
from .utils import askreddit_messages


class AskReddit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.clear_ai_chat.start()

    @commands.command()
    async def askreddit(self, ctx, *, text: str):
        """
        Ask the Karma Analyser questions
        - `text` (required): The question to ask.
        """
        with open("settings.json", "r") as f:
            settings = json.load(f)

        client = Client(host=settings.get("ollama_endpoint"))
        ai_instructions = "You are replying to a post on the subreddit r/askreddit..."

        message_history = [
            {"role": "system", "content": ai_instructions},
            {"role": "user", "content": text}
        ]

        response = await asyncio.to_thread(
            client.chat,
            model="artifish/llama3.2-uncensored",
            messages=message_history
        )
        clean_response = re.sub(r"<think>.*?</think>\\n\\n", "", response.message.content, flags=re.DOTALL)
        bot_reply = await ctx.reply(clean_response[:2000])

        # Store r/askreddit chats
        askreddit_messages[bot_reply.id] = {
            "messages": message_history + [{"role": "assistant", "content": response.message.content}],
            "bot_replies": {bot_reply.id},
            "last_reply": datetime.datetime.now(datetime.timezone.utc)
        }

    @commands.Cog.listener()
    async def on_message(self, payload):
        # r/askreddit replies
        if payload.reference and payload.reference.resolved:
            print(f"RESPONDING TO FELLOW REDDITOR {payload.author.name}")
            replied_message = payload.reference.resolved

            ai_chat = None
            for a in askreddit_messages.values():
                if replied_message.id in a["bot_replies"]:
                    ai_chat = a
                    break

            if not ai_chat:
                return

            images = []

            if payload.attachments:
                for attachment in payload.attachments:
                    is_image = False
                    if attachment.content_type:
                        is_image = attachment.content_type.startswith("image/")
                    else:
                        is_image = any(
                            attachment.filename.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".gif"])

                    if is_image:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(attachment.url) as response:
                                if response.status == 200:
                                    image_bytes = await response.read()
                                    base64_image = base64.b64encode(image_bytes)
                                    images.append(base64_image.decode("utf-8"))

            if payload.embeds:
                for embed in payload.embeds:
                    urls = []

                    if getattr(embed, "image", None) and getattr(embed.image, "url", None):
                        urls.append(embed.image.url)

                    if getattr(embed, "thumbnail", None) and getattr(embed.thumbnail, "url", None):
                        urls.append(embed.thumbnail.url)

                    if getattr(embed, "url", None):
                        urls.append(embed.url)

                    if getattr(embed, "video", None) and getattr(embed.video, "url", None):
                        urls.append(embed.video.url)

                    async with aiohttp.ClientSession() as session:
                        async with session.get(urls[0]) as response:
                            if response.status == 200:
                                image_bytes = await response.read()
                                base64_image = base64.b64encode(image_bytes)
                                images.append(base64_image.decode("utf-8"))

            ai_chat["messages"].append({
                "role": "user",
                "content": payload.content or "",
                "images": images
            })

            print("ANALYSING REDDITOR'S IMAGE" if len(images) > 0 else "REPLYING TO REDDITOR")

            with open("settings.json", "r") as f:
                settings = json.load(f)

            client = Client(host=settings.get("ollama_endpoint"))
            try:
                response = await asyncio.to_thread(
                    client.chat,
                    model="llava" if len(images) > 0 else "artifish/llama3.2-uncensored",
                    messages=ai_chat["messages"]
                )
            except Exception as e:
                print(e)

            clean_response = re.sub(r"<think>.*?</think>\\n\\n", "", response.message.content, flags=re.DOTALL)
            bot_reply = await payload.reply(clean_response[:2000])

            ai_chat["messages"].append({"role": "assistant", "content": response.message.content})
            ai_chat["bot_replies"].add(bot_reply.id)
            ai_chat["last_reply"] = datetime.datetime.now(datetime.timezone.utc)

    @tasks.loop(minutes=60)
    async def clear_ai_chat(self):
        from .utils import askreddit_messages
        now = datetime.datetime.now()

        chats = [id for id, chat in askreddit_messages.items()
                 if now - chat["last_reply"] > datetime.timedelta(minutes=60)]

        for chat in chats:
            del askreddit_messages[chat]


async def setup(bot):
    await bot.add_cog(AskReddit(bot))