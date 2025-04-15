import asyncio
import discord
import random
import time
import json

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


# Karma Reaction Values
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


# Gambling Rewards Tables
def get_gambling_rewards(length=10,mode="good"):
    # Rewards table for Reddiquette followers
    good_table = [
        ("<:reddit_upvote:1266139689136689173>", 30),
        ("<:quarter_upvote:1266139599814529034>", 60),
        ("<:reddit_downvote:1266139651660447744>", 25),
        ("<:quarter_downvote:1266139626276388875>", 50),
        ("<:reddit_silver:833677163739480079>", 5),
        ("<:reddit_gold:833675932883484753>", 2),
        ("<:reddit_platinum:833678610279563304>", 1),
        ("<:reddit_wholesome:833669115762835456>", 10)
    ]

    # Rewards table for those in Karmic Debt
    bad_table = [
        ("<:reddit_upvote:1266139689136689173>", 25),
        ("<:quarter_upvote:1266139599814529034>", 50),
        ("<:reddit_downvote:1266139651660447744>", 40),
        ("<:quarter_downvote:1266139626276388875>", 70),
        ("<:reddit_silver:833677163739480079>", 5),
        ("<:reddit_gold:833675932883484753>", 2),
        ("<:reddit_platinum:833678610279563304>", 1),
        ("<:reddit_wholesome:833669115762835456>", 5)
    ]

    table = good_table if mode == "good" else bad_table
    rewards, weights = zip(*table)

    array = random.choices(rewards, weights=weights, k=length)

    return array



@bot.command()
async def analyse(context):
    karmic_dict = defaultdict(lambda: defaultdict(int))  # User - Key - Int
    await context.send("KARMA SUBROUTINE INITIALISED")
    server = context.guild

    # Load Karmic Deductions
    with open("deductions.json", "r") as f:
        deductions = json.load(f)

    for user, deduction in deductions.items():
        user_obj = next((member for member in server.members if member.name == user), None)
        # Find matching user object
        if user_obj is not None:
            karmic_dict[user_obj]["Karma"] += deduction
        else:
            print(f"User {user} not in server.")

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

                    # Ignore Non-Karma Emojis
                    if reaction.emoji.name not in reaction_dict:
                        continue

                    try:
                        # Add Karma
                        async for user in reaction.users():
                            # Skip Self Reactions
                            if user == message.author:
                                continue

                            # Add Reaction Count
                            karmic_dict[message.author][reaction.emoji.name] += 1

                            # Add Weighted Karma Value
                            if reaction.emoji.name in reaction_dict:
                                karmic_dict[message.author]["Karma"] += (1 * reaction_dict[reaction.emoji.name])

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
    for user, count in karmic_dict.items():
        if user is None:
            continue

        karma_ratio = (karmic_dict[user]["Karma"] / karmic_dict[user]["Messages"])

        karma_str = ""
        # Karma up or downvcte?
        if karmic_dict[user]["Karma"] >= 0:
            karma_str = "<:reddit_upvote:1266139689136689173>"
        else:
            karma_str = "<:reddit_downvote:1266139651660447744>"

        await context.reply(f"{user.mention} **has:** \n"
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
    await asyncio.sleep(2)
    await context.send("CALCULATING COMMENSURATE KARMIC DEDUCTION")
    await asyncio.sleep(2)
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

@bot.command()
async def gambling(context):
    # Determine Karma Case Length
    case_length = random.randint(10, 20)

    # Good or bad odds?
    user = context.author
    with open("deductions.json", "r") as f:
        data = json.load(f)

    if user not in data:
        karma_case = get_gambling_rewards(case_length, "good")
        print("rolling case with good odds")
    else:
        user_karma = data[user]
        if user_karma < 0:
            karma_case = get_gambling_rewards(case_length, "bad")
            print("rolling case with bad odds")
        else:
            karma_case = get_gambling_rewards(case_length, "good")
            print("rolling case with good odds")

    # Open Karma Case
    karma_case = get_gambling_rewards(case_length)
    message = await context.reply("Opening your Karma Case...")
    await asyncio.sleep(2)

    for i in range(case_length - 4):
        frame = karma_case[i:i + 5]
        display = (
            f"{frame[0]}  |  "
            f"{frame[1]}  |  "
            f"**>> {frame[2]} <<**  |  "
            f"{frame[3]}  |  "
            f"{frame[4]}"
        )
        await message.edit(content=display)
        await asyncio.sleep(0.5)

    print(karma_case[case_length - 2])
    await message.add_reaction(karma_case[case_length - 2])


bot.run(bot_token)