import asyncio
import datetime
import random
import discord
import json
from collections import defaultdict
from discord.ext import commands, tasks
from .utils import reaction_dict, status, karma_lock


class Analyse(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.init_time = datetime.datetime.now(datetime.timezone.utc)

    @commands.Cog.listener()
    async def on_ready(self):
        async with karma_lock:

            karmic_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
            message_count = 0

            # Load Karmic Deductions
            try:
                with open("deductions.json", "r") as f:
                    deductions = json.load(f)
            except FileNotFoundError as e:
                print(f"SHIT, I LOST THE KARMIC ARCHIVES: {e}")
                deductions = {}

            for guild in self.bot.guilds:
                guild_deductions = deductions.get(guild.id, {})

                for user, deduction in guild_deductions.items():
                    user_obj = guild.get_member_named(user)
                    if user_obj is not None:
                        karmic_dict[guild.id][user_obj.name]["Karma"] += deduction
                    else:
                        print(f"USER {user} NOT IN SUBREDDIT {guild.name}")

            print("Counting Karma")
            for guild in self.bot.guilds:
                for channel in guild.text_channels:
                    try:
                        async for message in channel.history(limit=None, oldest_first=True):
                            message_count += 1
                            print(f"({message_count}) {message.author}: {message.content}")

                            if message_count % 100 == 0:
                                await self.bot.change_presence(
                                    activity=discord.Game(name=f"{message_count} MESSAGES ANALYSED"))

                            # Ignore Bots, Deleted Users, and messages sent after bot initialisation.
                            if (
                                    message.author.bot and message.author.name != "Karma Analyser"
                                    or message.author.name == "Deleted User"
                                    or message.created_at > self.init_time
                            ):
                                continue

                            # Count Messages
                            karmic_dict[guild.id][message.author.name]["Messages"] += 1

                            for reaction in message.reactions:
                                emoji_name = reaction.emoji if isinstance(reaction.emoji, str) else reaction.emoji.name

                                # Ignore Non-Karmic Reactions
                                if emoji_name not in reaction_dict:
                                    continue

                                # Count multiple truke reactions as a single truke
                                if emoji_name == "truthnuke":
                                    karmic_dict[guild.id][message.author.name]["truthnuke"] += 1
                                    continue

                                try:
                                    # Add Karma
                                    async for user in reaction.users():
                                        # Skip Self Reactions
                                        if user == message.author:
                                            continue

                                        # Add Reaction Count
                                        karmic_dict[guild.id][message.author.name][emoji_name] += 1

                                        # Add Weighted Karma Value
                                        karmic_dict[guild.id][message.author.name]["Karma"] += reaction_dict[emoji_name]

                                except discord.HTTPException as e:
                                    print(e)

                    except discord.HTTPException as e:
                        print(e)

            with open("karma.json", "w") as f:
                json.dump(karmic_dict, f, indent=4)
                print("KARMIC ANALYSIS RESULTS ARCHIVED IN THE JSON")

        self.change_status.start()

    @tasks.loop(minutes=15)
    async def change_status(self):
        activity = random.choice(status)
        print(f"CHANGED STATUS: {activity}")
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

        async with karma_lock:
            try:
                with open("karma.json", "r") as f:
                    karmic_dict = json.load(f)
            except FileNotFoundError:
                print(f"SHIT, I LOST THE KARMIC ARCHIVES: {e}")
                karmic_dict = {}

            if payload.guild_id not in karmic_dict:
                karmic_dict[payload.guild_id] = {}

            user_name = message.author.name
            if user_name not in karmic_dict[payload.guild_id]:
                karmic_dict[payload.guild_id][user_name] = {}

            if payload.emoji.name not in karmic_dict[payload.guild_id][user_name]:
                karmic_dict[payload.guild_id][user_name][payload.emoji.name] = 0

            if "Karma" not in karmic_dict[payload.guild_id][user_name]:
                karmic_dict[payload.guild_id][user_name]["Karma"] = 0

            # Count Reactions
            karmic_dict[payload.guild_id][user_name][payload.emoji.name] += 1
            karmic_dict[payload.guild_id][user_name]["Karma"] += reaction_dict[payload.emoji.name]

            with open("karma.json", "w") as f:
                json.dump(karmic_dict, f, indent=4)

            print(f"ANALYSED {user.name}'S REACTION TO {user_name}'S POST")


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

        async with karma_lock:
            try:
                with open("karma.json", "r") as f:
                    karmic_dict = json.load(f)
            except FileNotFoundError:
                print(f"SHIT, I LOST THE KARMIC ARCHIVES: {e}")
                return

            if payload.guild_id not in karmic_dict:
                karmic_dict[payload.guild_id] = {}

            user_name = message.author.name
            if user_name not in karmic_dict[payload.guild_id]:
                karmic_dict[payload.guild_id][user_name] = {}

            if payload.emoji.name not in karmic_dict[payload.guild_id][user_name]:
                karmic_dict[payload.guild_id][user_name][payload.emoji.name] = 0

            if "Karma" not in karmic_dict[payload.guild_id][user_name]:
                karmic_dict[payload.guild_id][user_name]["Karma"] = 0

            # Count Reactions
            karmic_dict[payload.guild_id][user_name][payload.emoji.name] -= 1
            karmic_dict[payload.guild_id][user_name]["Karma"] -= reaction_dict[payload.emoji.name]

            with open("karma.json", "w") as f:
                json.dump(karmic_dict, f, indent=4)

            print(f"ANALYSED {user.name}'S REACTION TO {user_name}'S POST")

    @commands.Cog.listener()
    async def on_message(self, payload):
        # Update message count
        async with karma_lock:
            try:
                with open("karma.json", "r") as f:
                    karmic_dict = json.load(f)
            except FileNotFoundError as e:
                print(f"SHIT, I LOST THE KARMIC ARCHIVES: {e}")

            user_name = payload.author.name

            if payload.guild_id not in karmic_dict:
                karmic_dict[payload.guild_id] = {}

            if user_name not in karmic_dict[payload.guild_id]:
                karmic_dict[payload.guild_id][user_name] = {}

            if "Messages" not in karmic_dict[payload.guild_id][user_name]:
                karmic_dict[payload.guild_id][user_name]["Messages"] = 0

            karmic_dict[payload.guild_id][user_name]["Messages"] += 1

            with open("karma.json", "w") as f:
                json.dump(karmic_dict, f, indent=4)

    @commands.Cog.listener()
    async def on_message_delete(self, payload):
        async with karma_lock:
            try:
                with open("karma.json", "r") as f:
                    karmic_dict = json.load(f)
            except FileNotFoundError as e:
                print(f"SHIT, I LOST THE KARMIC ARCHIVES: {e}")

            user_name = payload.author.name

            if payload.guild_id not in karmic_dict:
                karmic_dict[payload.guild_id] = {}

            if user_name not in karmic_dict[payload.guild_id]:
                karmic_dict[payload.guild_id][user_name] = {}

            if "Messages" not in karmic_dict[payload.guild_id][user_name]:
                karmic_dict[payload.guild_id][user_name]["Messages"] = 0

            karmic_dict[payload.guild_id][user_name]["Messages"] -= 1

            with open("karma.json", "w") as f:
                json.dump(karmic_dict, f, indent=4)

    @commands.command(aliases=['analysis'])
    async def analyse(self, ctx):
        reply = await ctx.reply("KARMA SUBROUTINE INITIALISED")

        # Load karma JSON
        if karma_lock.locked():
            await reply.edit(content="WAITING TO ACCESS KARMIC ARCHIVES, THIS MAY TAKE LONGER THAN USUAL")

        async with karma_lock:
            try:
                with open("karma.json", "r") as f:
                    output_dict = defaultdict(lambda: defaultdict(int))
                    for key, value in json.load(f).get(str(ctx.guild.id), {}).items():
                        output_dict[key] = defaultdict(int, value)

            except FileNotFoundError as e:
                print(f"SHIT, I LOST THE KARMIC ARCHIVES: {e}")

        # Determine which users to analyse
        users_to_iterate = set()

        # @everyone
        if "@everyone" in ctx.message.content:
            users_to_iterate.update([m.name.lower() for m in ctx.guild.members])

        # @here
        elif "@here" in ctx.message.content:
            users_to_iterate.update(m.name.lower() for m in ctx.guild.members if m.status != discord.Status.offline)

        else:
            # @user
            users_to_iterate.update(m.name.lower() for m in ctx.message.mentions)

            # @role
            for role in ctx.message.role_mentions:
                users_to_iterate.update(m.name.lower() for m in role.members)

            # No Arguments
            if not users_to_iterate:
                users_to_iterate.add(ctx.author.name.lower())

        print(f"ANALYSING THE FOLLOWING USERS: {users_to_iterate}")

        await asyncio.sleep(random.uniform(2.5, 5))
        await reply.edit(content="KARMA ANALYSED")

        for user in users_to_iterate:
            # Skip users with low message count
            messages = output_dict[user].get("Messages", 1)
            if messages < 100:
                continue

            user_obj = discord.utils.find(lambda m: m.name.lower() == user, ctx.guild.members)
            user_str = user_obj.display_name if user_obj else user

            karma = output_dict[user].get("Karma", 0)
            karma_ratio = karma / messages
            karma_str = "<:reddit_upvote:1266139689136689173>" if karma >= 0 else "<:reddit_downvote:1266139651660447744>"

            # Create Karmic analysis embed for each user
            embed = discord.Embed(
                title=f"{user_str}",
                color=0xED001C,
            )

            embed.add_field(name="Karma", value=f"{karma} {karma_str}", inline=False)
            embed.add_field(name="Messages", value=f"{messages}", inline=False)
            embed.add_field(name="Karmic Ratio", value=f"{round(karma_ratio, 4)}", inline=False)
            embed.add_field(name="Silver", value=f"{output_dict[user].get('reddit_silver', 0)} <:reddit_silver:833677163739480079>", inline=True)
            embed.add_field(name="Gold", value=f"{output_dict[user].get('reddit_gold', 0)} <:reddit_gold:833675932883484753>", inline=True)
            embed.add_field(name="Platinum", value=f"{output_dict[user].get('reddit_platinum', 0)} <:reddit_platinum:833678610279563304>", inline=True)
            embed.add_field(name="Wholesome", value=f"{output_dict[user].get('reddit_wholesome', 0)} <:reddit_wholesome:833669115762835456>", inline=True)
            embed.add_field(name="Trukes", value=f"{output_dict[user].get('truthnuke', 0)} <:truthnuke:1359507023951298700>", inline=True)

            await ctx.channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Analyse(bot))