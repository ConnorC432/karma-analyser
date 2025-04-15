import discord
import random
import time
import json
import os

from discord.ext import commands
from collections import defaultdict


# Get Bot Token from text file
with open("token.txt", "r") as f:
    bot_token = f.readline().strip()

# Enable the necessary intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True
intents.reactions = True
intents.guilds = True
intents.emojis = True

# Create the bot instance
bot = commands.Bot(command_prefix="r/", intents=intents)


reaction_dict = {
    "reddit_upvote": 1,
    "reddit_downvote": -1,
    "quarter_upvote": 0.5,
    "quarter_downvote": -0.5,
    "reddit_gold": 0,
    "reddit_platinum": 0,
    "reddit_silver": 0,
    "reddit_wholesome": 0,
}


@bot.command()
async def analyse(context):
    karmic_dict = defaultdict(lambda: defaultdict(int))  # User - Key - Int
    await context.send("KARMA SUBROUTINE INITIALISED")
    server = context.guild

    # Load Karmic Deductions
    with open("deductions.json", "r") as f:
        deductions = json.load(f)

    for user in deductions:
        karmic_dict[user]["Karma"] += deductions[user]

    # Count Karma
    print("Counting Karma")
    for channel in server.text_channels:
        try:
            async for message in channel.history(limit=None, oldest_first=True):
                # Ignore Bot Comments
                if message.author.bot:
                    continue

                # Count Messages
                karmic_dict[message.author]["Messages"] += 1

                for reaction in message.reactions:
                    # Ignore Bot Reactions
                    if message.author.bot:
                        continue

                    # Ignore Non-Karma Emojis
                    if reaction.emoji.name not in reaction_dict:
                        continue

                    try:
                        # Add Karma
                        async for user in reaction.users():
                            # Add Reaction Count
                            karmic_dict[user][reaction.emoji.name] += 1

                            # Add Weighted Karma Value
                            if reaction.emoji.name in reaction_dict:
                                karmic_dict[user]["Karma"] += (1 * reaction_dict[reaction.emoji.name])

                    except discord.HTTPException as e:
                        print(e)

        except discord.HTTPException as e:
            print(e)

    # Sort Dict by Karma Values
    sorted_karmic_dict = sorted(
        karmic_dict.items(),
        key=lambda item: item[1]["Karma"],
        reverse=True
    )

    # Send Karma Analysis Results
    for user, count in sorted_karmic_dict:
        karma_ratio = (karmic_dict[user]["Karma"] / karmic_dict[user]["Messages"])

        karma_str = ""
        # Karma up or downvcte?
        if karmic_dict[user]["Karma"] >= 0:
            karma_str = "<:reddit_upvote:1266139689136689173>"
        else:
            karma_str = "<:reddit_downvote: 1266139651660447744>"

        await context.send(f"{user.mention} **has:** \n"
                           f"{karmic_dict[user]["Karma"]} Karma {karma_str} \n"
                           f"{karmic_dict[user]["Messages"]} Messages. \n"
                           f"{round(karma_ratio, 4)} Karma per Message \n"
                           f"Awards: \n"
                           f"{karmic_dict[user]["reddit_silver"]} Silver <:reddit_silver:833677163739480079>\n"
                           f"{karmic_dict[user]["reddit_gold"]} Gold <:reddit_gold:833675932883484753>\n"
                           f"{karmic_dict[user]["reddit_platinum"]} Platinum <:reddit_platinum:833678610279563304>\n"
                           f"{karmic_dict[user]["reddit_wholesome"]} Wholesome <:reddit_wholesome:833669115762835456>")


@bot.command()
async def gild(context):
    await context.send("Thank you kind stranger!")

@bot.command()
#@commands.has_role("Karma Court Judge")
async def sentence(context, member: discord.Member):
    await context.send(f"ENUMERATING REDDIQUETTE VIOLATIONS FROM u/{member.name}")
    time.sleep(2)
    await context.send("CALCULATING COMMENSURATE KARMIC DEDUCTION")
    time.sleep(2)
    ded = random.randint(50,100)
    await context.send(f"FOR CRIMES AGAINST REDDIT AND XER PEOPLE, u/{member.name} IS HEREBY SENTENCED TO A KARMIC DEDUCTION TOTALLING {ded} REDDIT KARMA")

    # Read Deductions JSON
    with open("deductions.json", "r") as f:
        data = json.load(f)

    # Add User to JSON if not already there, and subtract karma
    if member.name not in data:
        data[member.name] = 0

    data[member.name] -= ded

    # Save to JSON
    with open("deductions.json", "w") as f:
        json.dump(data, f, indent=4)


bot.run(bot_token)