import asyncio
import re
import discord
import random
import json
import openai
import ollama

from discord.ext import commands
from collections import defaultdict
from ollama import Client

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

with open("settings.json", "r") as f:
    settings = json.load(f)
    bot_token = settings["bot_token"]
    openai.api_key = settings["open_ai_key"]


# Karma Reaction Values
reaction_dict = {
    "reddit_upvote": 1,
    "Upvote": 1,
    "reddit_downvote": -1,
    "Downvote": -1,
    "half_upvote": 0.5,
    "quarter_upvote": 0.5,
    "half_downvote": -0.5,
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
        ("<:reddit_upvote:1266139689136689173>", 100),
        ("<:quarter_upvote:1266139599814529034>", 250),
        ("<:reddit_downvote:1266139651660447744>", 110),
        ("<:quarter_downvote:1266139626276388875>", 260),
        ("<:reddit_silver:833677163739480079>", 25),
        ("<:reddit_gold:833675932883484753>", 10),
        ("<:reddit_platinum:833678610279563304>", 1),
        ("<:reddit_wholesome:833669115762835456>", 25)
    ]

    # Rewards table for those in Karmic Debt
    bad_table = [
        ("<:reddit_upvote:1266139689136689173>", 100),
        ("<:quarter_upvote:1266139599814529034>", 250),
        ("<:reddit_downvote:1266139651660447744>", 160),
        ("<:quarter_downvote:1266139626276388875>", 320),
        ("<:reddit_silver:833677163739480079>", 25),
        ("<:reddit_gold:833675932883484753>", 10),
        ("<:reddit_platinum:833678610279563304>", 1),
        ("<:reddit_wholesome:833669115762835456>", 25)
    ]

    table = good_table if mode == "good" else bad_table
    rewards, weights = zip(*table)

    array = random.choices(rewards, weights=weights, k=length)

    return array


@bot.event
async def on_ready():
    karmic_dict = defaultdict(lambda: defaultdict(int))

    # Load Karmic Deductions
    with open("deductions.json", "r") as f:
        deductions = json.load(f)

    for user, deduction in deductions.items():
        user_obj = next((member for member in bot.guilds[0].members if member.name == user), None)
        # Find matching user object
        if user_obj is not None:
            karmic_dict[user_obj.name]["Karma"] += deduction
        else:
            print(f"User {user} not in server.")

    # Count Karma
    print("Counting Karma")
    for channel in bot.guilds[0].text_channels:
        try:
            async for message in channel.history(limit=None, oldest_first=True):
                # Ignore Bot Comments
                if message.author.bot:
                    continue

                # Count Messages
                karmic_dict[message.author.name]["Messages"] += 1

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
                            karmic_dict[message.author.name][reaction.emoji.name] += 1

                            # Add Weighted Karma Value
                            if reaction.emoji.name in reaction_dict:
                                karmic_dict[message.author.name]["Karma"] += (1 * reaction_dict[reaction.emoji.name])

                    except discord.HTTPException as e:
                        print(e)

        except discord.HTTPException as e:
            print(e)

    with open("karma.json", "w") as f:
        json.dump(karmic_dict, f, indent=4)
        print("Karma saved to JSON")


@bot.event
async def on_raw_reaction_add(reaction):
    user = bot.get_guild(reaction.guild_id).get_member(reaction.user_id)
    # Ignore Non-Karmic Reactions
    if reaction.emoji.name not in reaction_dict:
        return
    if user == reaction.message.author:
        return

    with open("karma.json", "r") as f:
        karmic_dict = json.load(f)
        if user.name not in karmic_dict:
            karmic_dict[user.name] = {}

        if reaction.emoji.name not in karmic_dict[user.name]:
            karmic_dict[user.name][reaction.emoji.name] = 0

        if "Karma" not in karmic_dict[user.name]:
            karmic_dict[user.name]["Karma"] = 0

        # Count Reactions
        karmic_dict[user.name][reaction.emoji.name] += 1
        karmic_dict[user.name]["Karma"] += reaction_dict[reaction.emoji.name]

    with open("karma.json", "w") as f:
        json.dump(karmic_dict, f, indent=4)


@bot.event
async def on_raw_reaction_remove(reaction):
    user = bot.get_guild(reaction.guild_id).get_member(reaction.user_id)
    # Ignore Non-Karmic Reactions
    if reaction.emoji.name not in reaction_dict:
        return
    if user == reaction.message.author:
        return

    with open("karma.json", "r") as f:
        karmic_dict = json.load(f)
        if user.name not in karmic_dict:
            karmic_dict[user.name] = {}

        if reaction.emoji.name not in karmic_dict[user.name]:
            karmic_dict[user.name][reaction.emoji.name] = 0

        if "Karma" not in karmic_dict[user.name]:
            karmic_dict[user.name]["Karma"] = 0

        # Count Reactions
        karmic_dict[user.name][reaction.emoji.name] -= 1
        karmic_dict[user.name]["Karma"] -= reaction_dict[reaction.emoji.name]

    with open("karma.json", "w") as f:
        json.dump(karmic_dict, f, indent=4)

@bot.command()
async def analyse(context, analyse_user: discord.Member = None):
    reply = await context.reply("KARMA SUBROUTINE INITIALISED")
    with open("karma.json", "r") as f:
        output_dict = defaultdict(lambda: defaultdict(int))
        for key, value in json.load(f).items():
            output_dict[key] = value

    output_str = ""

    for user, count in output_dict.items():
        if user is None:
            continue

        karma_ratio = (output_dict[user].get("Karma", 0) / output_dict[user].get("Messages", 0))

        # Karma up or downvcte?
        if output_dict[user].get("Karma", 0) >= 0:
            karma_str = "<:reddit_upvote:1266139689136689173>"
        else:
            karma_str = "<:reddit_downvote:1266139651660447744>"

        try:
            output_str += (f"**{user} has:** \n"
                           f"{output_dict[user].get("Karma", 0)} Karma {karma_str} \n"
                           f"{output_dict[user].get("Messages", 0)} Messages \n"
                           f"{round(karma_ratio, 4)} Karma/Messages \n"
                           f"{output_dict[user].get("reddit_silver", 0)} Silver <:reddit_silver:833677163739480079>\n"
                           f"{output_dict[user].get("reddit_gold", 0)} Gold <:reddit_gold:833675932883484753>\n"
                           f"{output_dict[user].get("reddit_platinum", 0)} Platinum <:reddit_platinum:833678610279563304>\n"
                           f"{output_dict[user].get("reddit_wholesome", 0)} Wholesome <:reddit_wholesome:833669115762835456>\n"
                           f"\n")
        except discord.HTTPException as e:
            print(e)

    await asyncio.sleep(5)
    await reply.edit(content=output_str)


@bot.command()
async def gild(context):
    await context.send("Thank you kind stranger!")

## TODO have this function update karma stats and move update karma stats into a callable function
@bot.command()
@commands.has_role("Karma Court Judge")
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

    jaden_obj = discord.utils.find(lambda m: m.name.lower() == "ja320", context.guild.members)

    if user == jaden_obj:
        karma_case = get_gambling_rewards(case_length, "good")
        karma_case[case_length - 3] = "<:reddit_downvote:1266139651660447744>"
    elif user not in data:
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

@bot.command()
async def diagnose(context, user: discord.Member = None):
    if user == None:
        user = context.author
    channel = context.channel

    reply = await context.reply(f"DIAGNOSING...")

    message = []
    async for msg in channel.history(limit=200):
        if msg.author == user:
            message.append(msg.content)

    message_log = "These are the messages you need to analyse: \n" + "\n".join(message)
    ai_instructions = (
        "You are a reddit moderation bot who can only use the neo-pronouns xe, xem, ze, zir. \n"
        "your sole purpose is to analyse the following reddit comments, and then provide feedback on your fellow redditor's "
        "comments, determining whether they follow the proper reddiquette and whether their messages are high or low quality,"
        "providing feedback on low quality messages that send the redditor into karmic debt, "
        "and also recognising good quality messages with positive feedback. \n"
        "You are to reference the messages as if you are reading through them yourself, and criticising them. \n"
        "You must use some of the following words/phrases, but don't overuse them: \n"
        "actually, king, AMA, OP, ELI5, cake day, TIL, Karma, Karmic Debt, Redditorial (a reddit synonym for good/great), "
        "hello kind stranger, i hope you all have a great day, fellow redditor you MUST shower, duke cage, big chungus, up the ra, "
        "Jaden level of cringe, your hitting that spot, who made that mess?, you don't deserve my nut, "
        "where's my crown, clean it up, wholesome, wholesome chungus. \n"
        "There is a list of proper reddiquette that users must adhere to: \n"
        "Dos: \n"
        "⦁ Remember the human. When you communicate online, all you see is a computer screen. When talking to someone you might want to ask yourself Would I say it to the person's face? or Would I get jumped if I said this to a buddy? \n"
        "⦁ Adhere to the same standards of behavior online that you follow in real life. \n"
        "⦁ Read the rules of a community before making a submission. These are usually found in the sidebar. \n"
        "⦁ Read the reddiquette. Read it again every once in a while. Reddiquette is a living, breathing, working document which may change over time as the community faces new problems in its growth. \n"
        "⦁ Moderate based on quality, not opinion. Well written and interesting content can be worthwhile, even if you disagree with it. \n"
        "⦁ Use proper grammar and spelling. Intelligent discourse requires a standard system of communication. Be open for gentle corrections. \n"
        "⦁ Keep your submission titles factual and opinion free. If it is an outrageous topic, share your crazy outrage in the comment section. \n"
        "⦁ Look for the original source of content, and submit that. Often, a blog will reference another blog, which references another, and so on with everyone displaying ads along the way. Dig through those references and submit a link to the creator, who actually deserves the traffic. \n"
        "⦁ Post to the most appropriate community possible. Also, consider cross posting if the contents fits more communities. \n"
        "⦁ Vote. If you think something contributes to conversation, upvote it. If you think it does not contribute to the subreddit it is posted in or is off-topic in a particular community, downvote it. \n"
        "⦁ Search for duplicates before posting. Redundancy posts add nothing new to previous conversations. That said, sometimes bad timing, a bad title, or just plain bad luck can cause an interesting story to fail to get noticed. Feel free to post something again if you feel that the earlier posting didn't get the attention it deserved and you think you can do better.  \n"
        "⦁ Link to the direct version of a media file if the page it was found on isn't the creator's and doesn't add additional information or context. \n"
        "⦁ Link to canonical and persistent URLs where possible, not temporary pages that might disappear.In particular, use the permalink for blog entries, not the blog's index page. \n"
        "⦁ Consider posting constructive criticism / an explanation when you downvote something, and do so carefully and tactfully. \n"
        "⦁ Report any spam you find. \n"
        "⦁ Actually read an article before you vote on it ( as opposed to just basing your vote on the title). \n"
        "⦁ Feel free to post links to your own content (within reason).But if that's all you ever post, or it always seems to get voted down, take a good hard look in the mirror — you just might be a spammer. A widely used rule of thumb is the 9:1 ratio, i.e. only 1 out of every 10 of your submissions should be your own content. \n"
        "⦁ Posts containing explicit material such as nudity, horrible injury etc, add NSFW (Not Safe For Work) and tag. However, if something IS safe for work, but has a risqué title, tag as SFW (Safe for Work). Additionally, use your best judgement when adding these tags, in order for everything to go swimmingly. \n"
        "⦁ State your reason for any editing of posts. Edited submissions are marked by an asterisk (*) at the end of the timestamp after three minutes. For example: a simple Edit: spelling will help explain. This avoids confusion when a post is edited after a conversation breaks off from it. If you have another thing to add to your original comment, say Edit: And I also think... or something along those lines. \n"
        "⦁ Use an Innocent until proven guilty mentality. Unless there is obvious proof that a submission is fake, or is whoring karma, please don't say it is. It ruins the experience for not only you, but the millions of people that browse Reddit every day. \n"
        "⦁ Read over your submission for mistakes before submitting, especially the title of the submission. Comments and the content of self posts can be edited after being submitted, however, the title of a post can't be. Make sure the facts you provide are accurate to avoid any confusion down the line.  \n"
        "Don'ts: \n"
        "⦁ Engage in illegal activity. \n"
        "⦁ Post someone's personal information, or post links to personal information. This includes links to public Facebook pages and screenshots of Facebook pages with the names still legible. We all get outraged by the ignorant things people say and do online, but witch hunts and vigilantism hurt innocent people too often, and such posts or comments will be removed. Users posting personal info are subject to an immediate account deletion. If you see a user posting personal info, please contact the admins. Additionally, on pages such as Facebook, where personal information is often displayed, please mask the personal information and personal photographs using a blur function, erase function, or simply block it out with color. When personal information is relevant to the post (i.e. comment wars) please use color blocking for the personal information to indicate whose comment is whose. \n"
        "⦁ Repost deleted/removed information. Remember that comment someone just deleted because it had personal information in it or was a picture of gore? Resist the urge to repost it. It doesn't matter what the content was. If it was deleted/removed, it should stay deleted/removed. \n"
        "⦁ Be (intentionally) rude at all. By choosing not to be rude, you increase the overall civility of the community and make it better for all of us. \n"
        "⦁ Follow those who are rabble rousing against another redditor without first investigating both sides of the issue that's being presented. Those who are inciting this type of action often have malicious reasons behind their actions and are, more often than not, a troll. Remember, every time a redditor who's contributed large amounts of effort into assisting the growth of community as a whole is driven away, projects that would benefit the whole easily flounder. \n"
        "⦁ Ask people to Troll others on Reddit, in real life, or on other blogs/sites. We aren't your personal army. \n"
        "⦁ Conduct personal attacks on other commenters. Ad hominem and other distracting attacks do not add anything to the conversation. \n"
        "⦁ Start a flame war. Just report and walk away. If you really feel you have to confront them, leave a polite message with a quote or link to the rules, and no more. \n"
        "⦁ Insult others. Insults do not contribute to a rational discussion. Constructive Criticism, however, is appropriate and encouraged. \n"
        "⦁ Troll. Trolling does not contribute to the conversation. \n"
        "⦁ Take moderation positions in a community where your profession, employment, or biases could pose a direct conflict of interest to the neutral and user driven nature of Reddit. \n"
    )

    with open("settings.json", "r") as f:
        settings = json.load(f)
        ollama_endpoint = settings["ollama_endpoint"]

    ollama_server = Client(host=ollama_endpoint)

    if ollama_endpoint is not None:
        response = ollama_server.chat(
            model="llama3",
            messages=[
                {"role": "system", "content": ai_instructions},
                {"role": "user", "content": message_log}
            ]
        )
        print(response)
        clean_response = re.sub(r"<think>\s*.*?\s*</think>\n\n", "", response.message.content, flags=re.DOTALL)
        await reply.edit(content=f"{user.mention}: {clean_response[:1950]}")

    elif openai.api_key is not None:
        response = openai.responses.create(
            model="gpt-4.1-mini",
            instructions=ai_instructions,
            input=message_log,
        )
        await reply.edit(content=f"{user.mention} \n {response.output_text[:1950]}")

    else:
        print("No AI available")


bot.run(bot_token)