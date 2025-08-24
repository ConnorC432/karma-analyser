import datetime
import discord
import asyncio
import json
import random
import re
from collections import defaultdict
from discord.ext import commands
from ollama import Client
from urllib import parse, request
from .utils import get_gambling_rewards, reddiquette, help_words, karma_lock, askreddit_messages


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot



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

        print (f"SENTENCING {member.name} BY A DEDUCTION TOTALLING {ded} REDDIT KARMA")

        try:
            with open("deductions.json", "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}

        if str(ctx.guild.id) not in data:
            data[str(ctx.guild.id)] = {}

        if member.name not in data[str(ctx.guild.id)]:
            data[str(ctx.guild.id)][member.name] = 0

        data[str(ctx.guild.id)][member.name] -= ded

        with open("deductions.json", "w") as f:
            json.dump(data, f, indent=4)

    @commands.command(aliases=['gamble'])
    async def gambling(self, ctx, *, text: str = None):
        if ctx.channel.name != "gambling":
            return

        if text:
            if any(key in text.lower() for key in help_words):
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

        case_length = random.randint(10, 20)
        karma_case = get_gambling_rewards(case_length)

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

        print(f"DIAGNOSING {user.name}")

        reply = await ctx.reply("DIAGNOSING...")
        message_log = []
        async for msg in ctx.channel.history(limit=200):
            if msg.author == user and "r/" not in msg.content and "http" not in msg.content:
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

        message_history = [
            {"role": "system", "content": ai_instructions},
            {"role": "user", "content": text}
        ]

        response = await asyncio.to_thread(
            client.chat,
            model="llama3",
            messages=message_history
        )
        clean_response = re.sub(r"<think>.*?</think>\\n\\n", "", response.message.content, flags=re.DOTALL)
        bot_reply = await ctx.reply(clean_response[:2000])

        # Store r/askreddit chats
        askreddit_messages[bot_reply.id] = {
            "messages": message_history + [{"role": "assistant", "content": response.message.content}],
            "bot_replies": {bot_reply.id},
            "last_reply": datetime.datetime.now(datetime.timezone.utc)
        }

    @commands.command(aliases=["gif", "pic", "pics", "picture", "pictures"])
    async def gifs(self, ctx, *, text: str):
        with open("settings.json", "r") as f:
            settings = json.load(f)
            giphy_key = settings.get("giphy_key")

        giphy_url = "https://api.giphy.com/v1/gifs/search"

        params = parse.urlencode({
            "q": text,
            "api_key": giphy_key,
            "limit": 5
        })

        with request.urlopen(f"{giphy_url}?{params}") as response:
            data = json.loads(response.read())

        gif_urls = [item['images']['original']['url'] for item in data['data']]

        print(f"ANALYSING GIF: {gif_urls}")
        await ctx.message.reply(random.choice(gif_urls))


async def setup(bot):
    await bot.add_cog(Commands(bot))