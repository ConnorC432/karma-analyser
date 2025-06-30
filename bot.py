import discord
import json
import os
import asyncio
from discord.ext import commands

# Load settings
with open("settings.json", "r") as f:
    settings = json.load(f)
    bot_token = settings["bot_token"]

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="r/", intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user} is online and ready.")

# Load cogs
async def load_extensions():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and not filename.startswith("_") and filename != "utils.py":
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"Loaded extension: {filename}")
            except Exception as e:
                print(f"Failed to load {filename}: {e}")

async def main():
    async with bot:
        await load_extensions()
        await bot.start(bot_token)

asyncio.run(main())