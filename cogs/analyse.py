import asyncio
import datetime
import json
import logging
import random

import discord
from discord.ext import commands, tasks

from utils import karma_lock, karmic_dict, reaction_dict, REDDIT_RED, status


UPVOTE_STR = "<:reddit_upvote:1266139689136689173>"
DOWNVOTE_STR = "<:reddit_downvote:1266139651660447744>"
SILVER_STR = "<:reddit_silver:833677163739480079>"
GOLD_STR = "<:reddit_gold:833675932883484753>"
PLAT_STR = "<:reddit_platinum:833678610279563304>"
WHOLESOME_STR = "<:reddit_wholesome:833669115762835456>"
HELPFUL_STR = "<:helpful:1412197811008704694>"
TRUKE_STR = "<:truke:1359507023951298700>"

class Analyse(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.init_time = datetime.datetime.now(datetime.timezone.utc)
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self.message_count = 0

    @commands.Cog.listener()
    async def on_ready(self):
        async with karma_lock:
            # Load Karmic Deductions
            try:
                with open("deductions.json", "r", encoding="utf-8") as f:
                    deductions = json.load(f)
            except FileNotFoundError as e:
                self.logger.debug("SHIT, I LOST THE KARMIC ARCHIVES: %s", e)
                deductions = {}

            for guild in self.bot.guilds:
                guild_deductions = deductions.get(guild.id, {})

                for user, deduction in guild_deductions.items():
                    user_obj = guild.get_member_named(user)
                    if user_obj is not None:
                        karmic_dict[guild.id][user_obj.id]["Karma"] += deduction
                    else:
                        self.logger.warning("USER %s NOT IN SUBREDDIT %s", user, guild.name)

            print("Counting Karma")
            for guild in self.bot.guilds:
                for channel in guild.text_channels:
                    try:
                        async for message in channel.history(limit=None, oldest_first=True):
                            await self.analyse_message(guild, message)

                    except discord.HTTPException as e:
                        self.logger.error("HTTP ERROR: %s", e)

        self.change_status.start()

    async def analyse_message(self, guild, message):
        self.message_count += 1
        self.logger.debug("(%s) %s: %s", self.message_count, message.author, message.content)

        if self.message_count % 100 == 0:
            await self.bot.change_presence(
                activity=discord.Game(name=f"{self.message_count} MESSAGES ANALYSED"),
            )
            self.logger.info("CHANGED STATUS: \"%s MESSAGES ANALYSED\"", self.message_count)

        # Ignore Deleted Users and messages sent after bot initialisation.
        if (
                message.author.name == "Deleted User"
                or message.created_at > self.init_time
        ):
            self.logger.debug("Ignoring irrelevant message")
            return

        # Count Messages
        karmic_dict[guild.id][message.author.id]["Messages"] += 1

        for reaction in message.reactions:
            emoji_name = reaction.emoji if isinstance(reaction.emoji, str) else reaction.emoji.name

            # Ignore Non-Karmic Reactions
            if emoji_name not in reaction_dict:
                continue

            # Count multiple truke reactions as a single truke
            if emoji_name in ("truthnuke", "truke"):
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
                self.logger.error("HTTP ERROR: %s", e)

    @tasks.loop(minutes=15)
    async def change_status(self):
        activity = random.choice(status)
        self.logger.info("CHANGED STATUS: %s", activity)
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
            guild_id = payload.guild_id
            author_id = payload.author_id

            karmic_dict[guild_id][author_id][payload.emoji.name] += 1
            karmic_dict[guild_id][author_id]["Karma"] += reaction_dict[payload.emoji.name]

        self.logger.debug("ANALYSED %s'S REACTION TO %s'S POST", user.name, message.author.name)

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
            guild_id = payload.guild_id
            author_id = payload.author_id

            karmic_dict[guild_id][author_id][payload.emoji.name] -= 1
            karmic_dict[guild_id][author_id]["Karma"] -= reaction_dict[payload.emoji.name]

        self.logger.debug("ANALYSED %s'S REACTION TO %s'S POST", user.name, message.author.name)

    @commands.Cog.listener()
    async def on_message(self, message):
        self.message_count += 1

        # Update User's message count
        async with karma_lock:
            karmic_dict[message.guild.id][message.author.id]["Messages"] += 1

        self.logger.debug("ANALYSED MESSAGE: %s: %s", message.author.name, message.content)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        self.message_count -= 1

        async with karma_lock:
            karmic_dict[message.guild.id][message.author.id]["Messages"] -= 1

        self.logger.debug("UN-ANALYSED MESSAGE: %s: %s", message.author.name, message.content)

    @commands.command(aliases=['analysis'])
    async def analyse(self, ctx):
        """
        Analyse a user's karma
        - `user` (optional): Mention the user(s) to analyse.
        """
        reply = await ctx.reply("KARMA SUBROUTINE INITIALISED")

        # Load karma JSON
        if karma_lock.locked():
            await reply.edit(content="WAITING TO ACCESS KARMIC ARCHIVES, "
                                     "THIS MAY TAKE LONGER THAN USUAL")

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
                users_to_iterate.update(m.id for m in ctx.guild.members
                                        if m.status != discord.Status.offline)

            else:
                # @user
                users_to_iterate.update(m.id for m in ctx.message.mentions)

                # @role
                for role in ctx.message.role_mentions:
                    users_to_iterate.update(m.id for m in role.members)

                # No Arguments
                if not users_to_iterate:
                    users_to_iterate.add(ctx.author.id)

            self.logger.info("ANALYSING USERS: %s", users_to_iterate)

            await asyncio.sleep(random.uniform(2.5, 5))
            await reply.edit(content="KARMA ANALYSED")

            for user in users_to_iterate:
                user_data = karmic_dict[ctx.guild.id][user]
                messages = user_data["Messages"]
                karma = user_data["Karma"]

                user_obj = discord.utils.find(lambda m, u=user: m.id == user, ctx.guild.members)
                user_str = user_obj.display_name if user_obj else user

                karma_ratio = karma / messages if messages != 0 else 0
                karma_str = UPVOTE_STR if karma >= 0 else DOWNVOTE_STR

                # Create Karmic analysis embed for each user
                embed = discord.Embed(
                    title=f"{user_str}",
                    color=REDDIT_RED,
                )

                embed.add_field(
                    name="Karma",
                    value=f"{karma} {karma_str}",
                    inline=False
                )
                embed.add_field(
                    name="Messages",
                    value=f"{messages}",
                    inline=False
                )
                embed.add_field(
                    name="Karmic Ratio",
                    value=f"{round(karma_ratio, 4)}",
                    inline=False
                )
                embed.add_field(
                    name="Silver",
                    value=f"{karmic_dict[ctx.guild.id][user]['reddit_silver']} {SILVER_STR}",
                    inline=True,
                )
                embed.add_field(
                    name="Gold",
                    value=f"{karmic_dict[ctx.guild.id][user]['reddit_gold']} {GOLD_STR}",
                    inline=True,
                )
                embed.add_field(
                    name="Platinum",
                    value=f"{karmic_dict[ctx.guild.id][user]['reddit_platinum']} {PLAT_STR}",
                    inline=True,
                )
                embed.add_field(
                    name="Wholesome",
                    value=f"{karmic_dict[ctx.guild.id][user]['reddit_wholesome']} {WHOLESOME_STR}",
                    inline=True,
                )
                embed.add_field(
                    name="Helpful",
                    value=f"{karmic_dict[ctx.guild.id][user]['helpful']} {HELPFUL_STR}",
                    inline=True,
                )
                embed.add_field(
                    name="Trukes", value=f"{karmic_dict[ctx.guild.id][user]['truke']} {TRUKE_STR}",
                    inline=True,
                )

                try:
                    await ctx.channel.send(embed=embed)
                except discord.HTTPException as e:
                    self.logger.error("FAILED TO SEND EMBED: %s", e)


async def setup(bot):
    await bot.add_cog(Analyse(bot))
