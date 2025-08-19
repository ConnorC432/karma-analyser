import discord
import json
from collections import defaultdict
from discord.ext import commands
from .utils import reaction_dict

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        karmic_dict = defaultdict(lambda: defaultdict(int))

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
                    # Ignore Bot Comments
                    if message.author.bot:
                        continue

                    # Count Messages
                    karmic_dict[message.author.name]["Messages"] += 1

                    for reaction in message.reactions:#
                        # Ignore Non-Karmic Reactions
                        if reaction.emoji.name not in reaction_dict:
                            continue

                        # Count multiple truke reactions as a single truke
                        if reaction.emoji.name == "truthnuke":
                            karmic_dict[message.author.name]["truthnuke"] += 1
                            continue

                        try:
                            # Add Karma
                            async for user in reaction.users():
                                # Skip Self Reactions
                                if user == message.author:
                                    continue

                                # Add Reaction Count
                                karmic_dict[message.author.name][reaction.emoji.name] += 1

                                # Add Weighted Karma Value
                                karmic_dict[message.author.name]["Karma"] += reaction_dict[reaction.emoji.name]

                        except discord.HTTPException as e:
                            print(e)

            except discord.HTTPException as e:
                print(e)

        with open("karma.json", "w") as f:
            json.dump(karmic_dict, f, indent=4)
            print("Karma saved to JSON")

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

async def setup(bot):
    await bot.add_cog(Events(bot))