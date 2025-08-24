import asyncio
import datetime
import random
import re
import discord
import json
from collections import defaultdict
from discord.ext import commands, tasks
from ollama import Client
from .utils import reaction_dict, status, karma_lock, askreddit_messages


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.init_time = datetime.datetime.now(datetime.timezone.utc)

    @commands.Cog.listener()
    async def on_ready(self):
        async with karma_lock:

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
                    print(f"USER {user} NOT IN SUBREDDIT.")

            print("Counting Karma")
            for channel in self.bot.guilds[0].text_channels:
                try:
                    async for message in channel.history(limit=None, oldest_first=True):
                        message_count += 1
                        print(f"({message_count}) {message.author}: {message.content}")

                        if message_count % 100 == 0:
                            await self.bot.change_presence(activity=discord.Game(name=f"{message_count} MESSAGES ANALYSED"))

                        # Ignore Bots, Deleted Users, and messages sent after bot initialisation.
                        if (
                            message.author.bot and message.author.name != "Karma Analyser"
                            or message.author.name == "Deleted User"
                            or message.created_at > self.init_time
                        ):
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

        async with karma_lock:
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

        async with karma_lock:
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

        async with karma_lock:
            with open("karma.json", "w") as f:
                json.dump(karmic_dict, f, indent=4)

    @commands.Cog.listener()
    async def on_message(self, payload):
        # Update message count
        async with karma_lock:
            with open("karma.json", "r") as f:
                karmic_dict = json.load(f)

            user_name = payload.author.name

            if user_name not in karmic_dict:
                karmic_dict[user_name] = {}

            if "Messages" not in karmic_dict[user_name]:
                karmic_dict[user_name]["Messages"] = 0

            karmic_dict[user_name]["Messages"] += 1

            with open("karma.json", "w") as f:
                json.dump(karmic_dict, f, indent=4)

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

        # r/askreddit replies
        if payload.reference and payload.reference.resolved:
            print(f"RESPONDING TO FELLOW REDDITOR {user_name}")
            replied_message = payload.reference.resolved

            ai_chat = None
            for a in askreddit_messages.values():
                if replied_message.id in a["bot_replies"]:
                    ai_chat = a
                    break

            if not ai_chat:
                return

            ai_chat["messages"].append({"role": "user", "content": payload.content})

            with open("settings.json", "r") as f:
                settings = json.load(f)

            client = Client(host=settings.get("ollama_endpoint"))
            response = await asyncio.to_thread(
                client.chat,
                model="llama3",
                messages=ai_chat["messages"]
            )
            clean_response = re.sub(r"<think>.*?</think>\\n\\n", "", response.message.content, flags=re.DOTALL)
            bot_reply = await payload.reply(clean_response[:2000])

            ai_chat["messages"].append({"role": "assistant", "content": response.message.content})
            ai_chat["bot_replies"].add(bot_reply.id)
            ai_chat["last_reply"] = datetime.datetime.now(datetime.timezone.utc)

    @commands.Cog.listener()
    async def on_message_delete(self, payload):
        async with karma_lock:
            with open("karma.json", "r") as f:
                karmic_dict = json.load(f)

            user_name = payload.author.name

            if user_name not in karmic_dict:
                karmic_dict[user_name] = {}

            if "Messages" not in karmic_dict[user_name]:
                karmic_dict[user_name]["Messages"] = 0

            karmic_dict[user_name]["Messages"] -= 1

            with open("karma.json", "w") as f:
                json.dump(karmic_dict, f, indent=4)

    @tasks.loop(minutes=30)
    async def clear_ai_chat(self):
        from .utils import askreddit_messages
        now = datetime.datetime.now()

        chats = [id for id, chat in askreddit_messages.items()
                 if now - chat["last_reply"] > datetime.timedelta(minutes=30)]

        for chat in chats:
            del askreddit_messages[chat]


async def setup(bot):
    await bot.add_cog(Events(bot))