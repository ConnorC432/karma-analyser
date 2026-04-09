#!/usr/bin/env python

import argparse
import asyncio
import logging
import os
from pathlib import Path

import discord
from discord.ext import commands
from discord.ext.commands import ExtensionError


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
bot_token = os.environ.get("BOT_TOKEN")
if not bot_token:
    raise ValueError("BOT_TOKEN environment variable is not set")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=["r/", "R/"], intents=intents, case_insensitive=True)


@bot.event
async def on_ready():
    logger.info(f"{bot.user} IS READY TO ANALYSE REDDIT KARMA")


@bot.check
async def globally_block_dms(ctx):
    if ctx.guild is None:
        logger.debug(f"Ignoring command '{ctx.command}' from user {ctx.author} in DM")
        return False
    return True


@bot.event
async def on_command_error(ctx, error):
    # bot.check filtered command calls fail cleanly
    if isinstance(error, commands.CheckFailure):
        if ctx.guild is None:
            return
    
    # Handle other errors
    if not isinstance(error, (commands.CommandNotFound, commands.CheckFailure)):
        logger.error(f"Ignoring exception in command {ctx.command}: {error}")


# Load cogs
async def load_extensions():
    logger.info("Loading cogs...")

    if args.c:
        cogs_to_load = [f"cogs.{cog}" for cog in args.c]
    else:
        cogs_to_load = [
            f"cogs.{path.stem}"
            for path in Path("./cogs").iterdir()
            if path.suffix == ".py" and not path.name.startswith("_")
        ]

    loaded_count = 0
    failed_count = 0

    for extension in cogs_to_load:
        logger.info(f"Loading {extension}...")
        try:
            await bot.load_extension(extension)
            logger.info(f"Loaded {extension}")
            loaded_count += 1
        except ExtensionError as e:
            logger.exception(f"Failed to load {extension}: {e}")
            failed_count += 1

    logger.info(
        "Cogs loaded %s/%s",
        loaded_count,
        loaded_count + failed_count
    )


async def main():
    async with bot:
        await load_extensions()
        await bot.start(bot_token)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except discord.LoginFailure:
        logger.critical("Invalid bot token")
    except discord.PrivilegedIntentsRequired:
        logger.critical("Privileged intents are required to run this bot")
    except discord.HTTPException as e:
        logger.critical(f"Discord API Error: {e}")
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
