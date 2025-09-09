import discord
import json
import os
import asyncio
import argparse
from discord.ext import commands

# Parse launch arguments
parser = argparse.ArgumentParser()
parser.add_argument("-c", nargs="*", default=[], help="The cogs to load")
args = parser.parse_args()

# Load settings
with open("settings.json", "r") as f:
    settings = json.load(f)
    bot_token = settings["bot_token"]

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=["r/", "R/"], intents=intents, case_insensitive=True)

@bot.event
async def on_ready():
    print(f"{bot.user} IS READY TO ANALYSE REDDIT KARMA")

# Load cogs
async def load_extensions():
    if args.c:
        for cog in args.c:
            try:
                await bot.load_extension(f"cogs.{cog}")
                print(f"LOADED COG: {cog}")
            except Exception as e:
                print(f"FAILED TO LOAD COG: {cog}: {e}")
    else:
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py") and not filename.startswith("_") and filename != "utils.py":
                try:
                    await bot.load_extension(f"cogs.{filename[:-3]}")
                    print(f"LOADED COG: {filename}")
                except Exception as e:
                    print(f"FAILED TO LOAD COG: {filename}: {e}")

async def main():
    async with bot:
        await load_extensions()
        await bot.start(bot_token)

asyncio.run(main())