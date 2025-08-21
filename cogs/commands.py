import discord
import asyncio
import json
import random
import re
from collections import defaultdict
from discord.ext import commands
from ollama import Client
from .utils import get_gambling_rewards, reddiquette, help_words


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['analysis'])
    async def analyse(self, ctx, analyse_user: discord.Member = None):
        reply = await ctx.reply("KARMA SUBROUTINE INITIALISED")

        # Load karma JSON
        if karma_lock.locked(): print("WAITING TO ACCESS KARMIC ARCHIVES, THIS MAY TAKE LONGER THAN USUAL")
        async with karma_lock:
            with open("karma.json", "r") as f:
                output_dict = defaultdict(lambda: defaultdict(int))
                for key, value in json.load(f).items():
                    output_dict[key] = defaultdict(int, value)

        # Determine which users to analyse
        users_to_iterate = [str(analyse_user.name)] if analyse_user else output_dict.keys()

        await asyncio.sleep(random.uniform(2.5, 5))

        await reply.edit(content="KARMA ANALYSED")

        for user in users_to_iterate:
            user_obj = discord.utils.find(lambda m: m.name.lower() == user, ctx.guild.members)
            user_str = user_obj.display_name if user_obj else user
            messages = output_dict[user].get("Messages", 1)
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

    @commands.command()
    async def gild(self, ctx):
        await ctx.reply("Thank you kind stranger!")

    @commands.command()
    @commands.has_role("Karma Court Judge")
    async def sentence(self, ctx, member: discord.Member):
        await ctx.reply(f"ENUMERATING REDDIQUETTE VIOLATIONS FROM u/{member.name}")
        await asyncio.sleep(2)
        await ctx.send("CALCULATING COMMENSURATE KARMIC DEDUCTION")
        await asyncio.sleep(2)
        ded = random.randint(50, 100)
        await ctx.send(f"FOR CRIMES AGAINST REDDIT AND XER PEOPLE, u/{member.name} IS HEREBY SENTENCED TO A KARMIC DEDUCTION TOTALLING {ded} REDDIT KARMA")

        try:
            with open("deductions.json", "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}

        if member.name not in data:
            data[member.name] = 0

        data[member.name] -= ded

        with open("deductions.json", "w") as f:
            json.dump(data, f, indent=4)

    @commands.command(aliases=['gamble'])
    async def gambling(self, ctx, *, option: str = None):
        if ctx.channel.name != "gambling":
            return

        if option:
            if any(key in option.lower() for key in help_words):
                with open("settings.json", "r") as f:
                    settings = json.load(f)

                client = Client(host=settings.get("ollama_endpoint"))
                ai_instructions = "You are trying to convince a fellow redditor to keep gambling, they don't know that they are close to their big win, which is why you need to convince them!"

                response = await asyncio.to_thread(
                    client.chat,
                    model="llama3",
                    messages=[
                        {"role": "system", "content": ai_instructions},
                        {"role": "user", "content": "Convince your fellow redditor to keep gambling, so they can get their biggest jackpot yet!!!"}
                    ]
                )

                clean_response = re.sub(r"<think>.*?</think>\\n\\n", "", response.message.content, flags=re.DOTALL)
                await ctx.reply(f"{clean_response[:2000]}")
                return

        user = ctx.author
        case_length = random.randint(10, 20)
        with open("deductions.json", "r") as f:
            data = json.load(f)

        jaden_obj = discord.utils.find(lambda m: m.name.lower() == "ja320", ctx.guild.members)
        hull_obj = discord.utils.find(lambda m: m.name.lower() == "emnelwt3x7" or "jopj", ctx.guild.members)

        # Determine if Jaden's odds are used
        if user == jaden_obj:
            karma_case = get_gambling_rewards(case_length, "good")
            karma_case[case_length - 3] = "<:reddit_downvote:1266139651660447744>"
        elif user == hull_obj:
            karma_case = get_gambling_rewards(case_length, "good")
            karma_case[case_length - 3] = "<:Hullnarna:1406697829883314280>"
        elif user.name not in data:
            karma_case = get_gambling_rewards(case_length, "good")
        else:
            user_karma = data[user.name]
            karma_case = get_gambling_rewards(case_length, "bad" if user_karma < 0 else "good")

        # Open Karma Case
        message = await ctx.reply("Opening your Karma Case...")
        await asyncio.sleep(2)

        for i in range(case_length - 4):
            frame = karma_case[i:i + 5]
            display = (
                f"{frame[0]}  |  {frame[1]}  |  **>> {frame[2]} <<**  |  {frame[3]}  |  {frame[4]}"
            )
            await message.edit(content=display)
            await asyncio.sleep(0.25)

        await ctx.message.add_reaction(karma_case[case_length - 3])

    @commands.command(aliases=["diagnosis"])
    async def diagnose(self, ctx, user: discord.Member = None):
        if user is None:
            user = ctx.author
        reply = await ctx.reply("DIAGNOSING...")
        message_log = []
        async for msg in ctx.channel.history(limit=200):
            if msg.author == user and "r/" not in msg.content:
                message_log.append(msg.content)

        ai_instructions = ("You are a reddit moderation bot...\n" + reddiquette)
        prompt = "These are the messages you need to analyse: \n" + "\n".join(message_log)

        with open("settings.json", "r") as f:
            settings = json.load(f)
        client = Client(host=settings.get("ollama_endpoint"))

        response = await asyncio.to_thread(
            client.chat,
            model="llama3",
            messages=[
                {"role": "system", "content": ai_instructions},
                {"role": "user", "content": prompt}
            ]
        )
        clean_response = re.sub(r"<think>.*?</think>\\n\\n", "", response.message.content, flags=re.DOTALL)
        await reply.edit(content=f"{user.mention}: {clean_response[:1950]}")

    @commands.command()
    async def askreddit(self, ctx, *, text: str):
        with open("settings.json", "r") as f:
            settings = json.load(f)

        client = Client(host=settings.get("ollama_endpoint"))
        ai_instructions = "You are replying to a post on the subreddit r/askreddit...\n" + reddiquette

        response = await asyncio.to_thread(
            client.chat,
            model="llama3",
            messages=[
                {"role": "system", "content": ai_instructions},
                {"role": "user", "content": text}
            ]
        )
        clean_response = re.sub(r"<think>.*?</think>\\n\\n", "", response.message.content, flags=re.DOTALL)
        await ctx.reply(clean_response[:2000])


async def setup(bot):
    await bot.add_cog(Commands(bot))