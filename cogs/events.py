import asyncio
import random
import discord
import json
from collections import defaultdict
from discord.ext import commands, tasks
from .utils import reaction_dict, status

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        karmic_dict = defaultdict(lambda: defaultdict(int))
        message_count = 0

        # Load Karmic Deductions
        try:
            with open("deductions.json", "r") as f:
                deductions = json.load(f)
        except FileNotFoundError:
            deductions = {}

        for user, deduction in deductions.items():
            user_obj = next((member for member in self.bot.guilds[0].members if member.name == user), None)

            # Find matching user object
            if user_obj is not None:
                karmic_dict[user_obj.name]["Karma"] += deduction
            else:
                print(f"User {user} not in server.")

        print("Counting Karma")
        for channel in self.bot.guilds[0].text_channels:
            try:
                async for message in channel.history(limit=None, oldest_first=True):
                    message_count += 1
                    print(f"({message_count}) {message.author}: {message.content}")

                    if message_count % 100 == 0:
                        await self.bot.change_presence(activity=discord.Game(name=f"{message_count} MESSAGES ANALYSED"))

                    # Ignore Bot Comments
                    if message.author.bot and message.author.name != "Karma Analyser":
                        continue

                    # Ignore Deleted Users
                    if message.author.name == "Deleted User":
                        continue

                    # Count Messages
                    karmic_dict[message.author.name]["Messages"] += 1

                    for reaction in message.reactions:#
                        emoji_name = reaction.emoji if isinstance(reaction.emoji, str) else reaction.emoji.name

                        # Ignore Non-Karmic Reactions
                        if emoji_name not in reaction_dict:
                            continue

                        # Count multiple truke reactions as a single truke
                        if emoji_name == "truthnuke":
                            karmic_dict[message.author.name]["truthnuke"] += 1
                            continue

                        try:
                            # Add Karma
                            async for user in reaction.users():
                                # Skip Self Reactions
                                if user == message.author:
                                    continue

                                # Add Reaction Count
                                karmic_dict[message.author.name][emoji_name] += 1

                                # Add Weighted Karma Value
                                karmic_dict[message.author.name]["Karma"] += reaction_dict[emoji_name]

                        except discord.HTTPException as e:
                            print(e)

            except discord.HTTPException as e:
                print(e)

        with open("karma.json", "w") as f:
            json.dump(karmic_dict, f, indent=4)
            print("Karma saved to JSON")

        self.change_status.start()

    @tasks.loop(minutes=15)
    async def change_status(self):
        activity = random.choice(status)
        print(f"Status changed: {activity}")
        await self.bot.change_presence(activity=discord.Game(name=activity))

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # Ignore Non-Karmic Reactions
        if payload.emoji.name not in reaction_dict:
            return

        guild = self.bot.get_guild(payload.guild_id)
        user = guild.get_member(payload.user_id)
        message = await guild.get_channel(payload.channel_id).fetch_message(payload.message_id)

        if user == message.author:
            return

        try:
            with open("karma.json", "r") as f:
                karmic_dict = json.load(f)
        except FileNotFoundError:
            karmic_dict = {}

        user_name = message.author.name
        if user_name not in karmic_dict:
            karmic_dict[user_name] = {}

        if payload.emoji.name not in karmic_dict[user_name]:
            karmic_dict[user_name][payload.emoji.name] = 0

        if "Karma" not in karmic_dict[user_name]:
            karmic_dict[user_name]["Karma"] = 0

        # Count Reactions
        karmic_dict[user_name][payload.emoji.name] += 1
        karmic_dict[user_name]["Karma"] += reaction_dict[payload.emoji.name]

        with open("karma.json", "w") as f:
            json.dump(karmic_dict, f, indent=4)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        # Ignore Non-Karmic Reactions
        if payload.emoji.name not in reaction_dict:
            return

        guild = self.bot.get_guild(payload.guild_id)
        user = guild.get_member(payload.user_id)
        message = await guild.get_channel(payload.channel_id).fetch_message(payload.message_id)

        if user == message.author:
            return

        try:
            with open("karma.json", "r") as f:
                karmic_dict = json.load(f)
        except FileNotFoundError:
            return

        user_name = message.author.name
        if user_name not in karmic_dict:
            karmic_dict[user_name] = {}

        if payload.emoji.name not in karmic_dict[user_name]:
            karmic_dict[user_name][payload.emoji.name] = 0

        if "Karma" not in karmic_dict[user_name]:
            karmic_dict[user_name]["Karma"] = 0

        # Count Reactions
        karmic_dict[user_name][payload.emoji.name] -= 1
        karmic_dict[user_name]["Karma"] -= reaction_dict[payload.emoji.name]

        with open("karma.json", "w") as f:
            json.dump(karmic_dict, f, indent=4)

    @commands.Cog.listener()
    async def on_message(self, payload):
        if payload.author.bot:
            return

        if "pass it on" in payload.content.lower():
            async for message in payload.channel.history(limit=100, oldest_first=False):
                if message.author.bot and message.content == payload.content:
                    return

            await asyncio.sleep(random.uniform(0, 2.5))
            await payload.channel.send(payload.content)

        if "nothing ever happens" in payload.content.lower():
            await payload.reply(content="https://tenor.com/view/nothing-ever-happens-chud-chudjak-soyjak-90-seconds-to-nothing-gif-9277709574191520604")


async def setup(bot):
    await bot.add_cog(Events(bot))