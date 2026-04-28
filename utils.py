import asyncio
import logging
import os
import random
from collections import defaultdict

import aiohttp
import discord


logger = logging.getLogger("UTILS")

INTENTS = discord.Intents.none()
INTENTS.guilds = True
INTENTS.members = True
INTENTS.expressions = True
INTENTS.invites = True
INTENTS.voice_states = True
INTENTS.presences = True
INTENTS.guild_messages = True
INTENTS.guild_reactions = True
INTENTS.message_content = True
INTENTS.guild_polls = True

REDDIT_RED = 0xED001C
REDDIT_ORANGE = 0xFF8700
REDDIT_GREEN = 0x3BCB56
REDDIT_BLUE = 0x149EF0
REDDIT_GRAY = 0xA5A4A4

VALID_SERVER_IDS_1 = [683033503834963978, 1361336155169226792]

karmic_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
karma_lock = asyncio.Lock()


async def gif_search(query: str):
    api_key = os.getenv("KLIPY_KEY")
    if not api_key:
        logger.warning("KLIPY_KEY environment variable is not set")
        return None

    url = f"https://api.klipy.com/api/v1/{api_key}/gifs/search"
    params = {
        "q": query or "reddit",
        "page": 1,
        "per_page": 8,
        "customer_id": 0,
        "locale": "GB",
        "content_filter": "off",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as resp:
                resp.raise_for_status()
                data = await resp.json()
    except Exception:
        logger.exception(f"Failed to fetch GIF for query: {query}")
        return None

    gifs = data.get("data", {}).get("data", [])
    if not gifs:
        return None

    gif = random.choice(gifs)
    return gif.get("file", {}).get("md", {}).get("gif", {}).get("url")
