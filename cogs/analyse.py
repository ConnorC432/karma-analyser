import asyncio
import datetime
import logging
import random
import discord
import json
from discord.ext import commands, tasks
from utils import reaction_dict, status, karma_lock, karmic_dict, reddit_red


class Analyse(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.init_time = datetime.datetime.now(datetime.timezone.utc)
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

    @commands.Cog.listener()
    async def on_ready(self):
        async with karma_lock:
            message_count = 0

            # Load Karmic Deductions
            try:
                with open("deductions.json", "r") as f:
                    deductions = json.load(f)
            except FileNotFoundError as e:
                self.logger.debug(f"SHIT, I LOST THE KARMIC ARCHIVES: {e}")
                deductions = {}

            for guild in self.bot.guilds:
                guild_deductions = deductions.get(guild.id, {})

                for user, deduction in guild_deductions.items():
                    user_obj = guild.get_member_named(user)
                    if user_obj is not None:
                        karmic_dict[guild.id][user_obj.id]["Karma"] += deduction
                    else:
                        self.logger.warning(f"USER {user} NOT IN SUBREDDIT {guild.name}")

            print("Counting Karma")
            for guild in self.bot.guilds:
                for channel in guild.text_channels:
                    try:
                        async for message in channel.history(limit=None, oldest_first=True):
                            message_count += 1
                            self.logger.debug(f"({message_count}) {message.author}: {message.content}")

                            if message_count % 100 == 0:
                                await self.bot.change_presence(
                                    activity=discord.Game(name=f"{message_count} MESSAGES ANALYSED"))
                                self.logger.info(f"CHANGED STATUS: \"{message_count} MESSAGES ANALYSED\"")

                            # Ignore Deleted Users and messages sent after bot initialisation.
                            if (
                                    message.author.name == "Deleted User"
                                    or message.created_at > self.init_time
                            ):
                                self.logger.debug("Ignoring irrelevant message")
                                continue

                            # Count Messages
                            karmic_dict[guild.id][message.author.id]["Messages"] += 1

                            for reaction in message.reactions:
                                emoji_name = reaction.emoji if isinstance(reaction.emoji, str) else reaction.emoji.name

                                # Ignore Non-Karmic Reactions
                                if emoji_name not in reaction_dict:
                                    continue

                                # Count multiple truke reactions as a single truke
                                if emoji_name == "truthnuke" or "truke":
                                    karmic_dict[guild.id][message.author.id]["truke"] += 1
                                    continue

                                try:
                                    # Add Karma
                                    async for user in reaction.users():
                                        # Skip Self Reactions
                                        if user == message.author:
                                            continue

                                        # Add Reaction Count
                                        karmic_dict[guild.id][message.author.id][emoji_name] += 1

                                        # Add Weighted Karma Value
                                        karmic_dict[guild.id][message.author.id]["Karma"] += reaction_dict[emoji_name]

                                except discord.HTTPException as e:
                                    self.logger.error(f"HTTP ERROR: {e}")

                    except discord.HTTPException as e:
                        self.logger.error(f"HTTP ERROR: {e}")

        self.change_status.start()

    @tasks.loop(minutes=15)
    async def change_status(self):
        activity = random.choice(status)
        self.logger.info(f"CHANGED STATUS: {activity}")
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
            # Count Reactions
            karmic_dict[payload.guild_id][message.author.id][payload.emoji.name] += 1
            karmic_dict[payload.guild_id][message.author.id]["Karma"] += reaction_dict[payload.emoji.name]

        self.logger.debug(f"ANALYSED {user.name}'S REACTION TO {message.author.name}'S POST")

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
            # Count Reactions
            karmic_dict[payload.guild_id][message.author.id][payload.emoji.name] -= 1
            karmic_dict[payload.guild_id][message.author.id]["Karma"] -= reaction_dict[payload.emoji.name]

        self.logger.debug(f"ANALYSED {user.name}'S REACTION TO {message.author.name}'S POST")

    @commands.Cog.listener()
    async def on_message(self, message):
        # Update message count
        async with karma_lock:
            karmic_dict[message.guild.id][message.author.id]["Messages"] += 1

        self.logger.debug(f"ANALYSED MESSAGE: {message.author.name}: {message.content}")

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        async with karma_lock:
            karmic_dict[message.guild.id][message.author.id]["Messages"] -= 1

            self.logger.debug(f"UN-ANALYSED MESSAGE: {message.author.name}: {message.content}")

    @commands.command(aliases=['analysis'])
    async def analyse(self, ctx):
        """
        Analyse a user's karma
        - `user` (optional): Mention the user(s) to analyse.
        """
        reply = await ctx.reply("KARMA SUBROUTINE INITIALISED")

        # Load karma JSON
        if karma_lock.locked():
            await reply.edit(content="WAITING TO ACCESS KARMIC ARCHIVES, THIS MAY TAKE LONGER THAN USUAL")

        async with karma_lock:
            # Determine which users to analyse
            users_to_iterate = set()

            # @everyone
            if "@everyone" in ctx.message.content:
                users_to_iterate.update(
                    m.id
                    for m in ctx.guild.members
                    if karmic_dict[ctx.guild.id][m.id]["Messages"] >= 100
                )

            # @here
            elif "@here" in ctx.message.content:
                users_to_iterate.update(m.id for m in ctx.guild.members if m.status != discord.Status.offline)

            else:
                # @user
                users_to_iterate.update(m.id for m in ctx.message.mentions)

                # @role
                for role in ctx.message.role_mentions:
                    users_to_iterate.update(m.id for m in role.members)

                # No Arguments
                if not users_to_iterate:
                    users_to_iterate.add(ctx.author.id)

            self.logger.info(f"ANALYSING USERS: {users_to_iterate}")

            await asyncio.sleep(random.uniform(2.5, 5))
            await reply.edit(content="KARMA ANALYSED")

            for user in users_to_iterate:
                user_data = karmic_dict[ctx.guild.id][user]
                messages = user_data["Messages"]
                karma = user_data["Karma"]

                user_obj = discord.utils.find(lambda m: m.id == user, ctx.guild.members)
                user_str = user_obj.display_name if user_obj else user

                karma_ratio = karma / messages if messages != 0 else 0
                karma_str = "<:reddit_upvote:1266139689136689173>" if karma >= 0 else "<:reddit_downvote:1266139651660447744>"

                # Create Karmic analysis embed for each user
                embed = discord.Embed(
                    title=f"{user_str}",
                    color=reddit_red
                )

                embed.add_field(name="Karma", value=f"{karma} {karma_str}", inline=False)
                embed.add_field(name="Messages", value=f"{messages}", inline=False)
                embed.add_field(name="Karmic Ratio", value=f"{round(karma_ratio, 4)}", inline=False)
                embed.add_field(name="Silver", value=f"{karmic_dict[ctx.guild.id][user]['reddit_silver']} <:reddit_silver:833677163739480079>", inline=True)
                embed.add_field(name="Gold", value=f"{karmic_dict[ctx.guild.id][user]['reddit_gold']} <:reddit_gold:833675932883484753>", inline=True)
                embed.add_field(name="Platinum", value=f"{karmic_dict[ctx.guild.id][user]['reddit_platinum']} <:reddit_platinum:833678610279563304>", inline=True)
                embed.add_field(name="Wholesome", value=f"{karmic_dict[ctx.guild.id][user]['reddit_wholesome']} <:reddit_wholesome:833669115762835456>", inline=True)
                embed.add_field(name="Helpful", value=f"{karmic_dict[ctx.guild.id][user]['helpful']} <:helpful:1412197811008704694>", inline=True)
                embed.add_field(name="Trukes", value=f"{karmic_dict[ctx.guild.id][user]['truke']} <:truke:1359507023951298700>", inline=True)

                try:
                    await ctx.channel.send(embed=embed)
                except Exception as e:
                    self.logger.error(f"FAILED TO SEND EMBED: {e}")

async def setup(bot):
    await bot.add_cog(Analyse(bot))