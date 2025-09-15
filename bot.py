import discord
import json
import os
import asyncio
import argparse
import logging
from discord.ext import commands

# Parse launch arguments
parser = argparse.ArgumentParser()
parser.add_argument("-c", nargs="*", default=[], help="The cogs to load")
parser.add_argument("-d", help="debug mode", action="store_true")
args = parser.parse_args()

# Logger
logging.basicConfig(
    level=logging.DEBUG if args.d else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s | %(message)s"
)

logger = logging.getLogger("Bot")

# Load settings
with open("settings.json", "r") as f:
    settings = json.load(f)
    bot_token = settings["bot_token"]

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=["r/", "R/"], intents=intents, case_insensitive=True)

@bot.event
async def on_ready():
    logger.info(f"{bot.user} IS READY TO ANALYSE REDDIT KARMA")

# Load cogs
async def load_extensions():
    if args.c:
        for cog in args.c:
            try:
                await bot.load_extension(f"cogs.{cog}")
                logger.debug(f"LOADED COG: {cog}")
            except Exception as e:
                logger.critical(f"FAILED TO LOAD COG: {cog}: {e}")
    else:
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py") and not filename.startswith("_") and filename != "utils.py":
                try:
                    await bot.load_extension(f"cogs.{filename[:-3]}")
                    logger.debug(f"LOADED COG: {filename}")
                except Exception as e:
                    logger.critical(f"FAILED TO LOAD COG: {filename}: {e}")

async def main():
    async with bot:
        await load_extensions()
        await bot.start(bot_token)

asyncio.run(main())