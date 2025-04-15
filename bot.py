import discord
from discord.ext import commands
import random
import time

# Enable the necessary intents
intents = discord.Intents.default()
intents.messages = True  # Allow the bot to read messages
intents.message_content = True  # Allow the bot to access the content of the messages
intents.members = True

# Create the bot instance
bot = commands.Bot(command_prefix="r/", intents=intents)

blacklist = {"Karma Analyser", "cicropia"}
karmaMods = {
    "heinzdeez" : -88
}

class Stats:
    def __init__(self, name):
        self.name = name
        self.totalMessages = 0
        self.karma = 0.0
        self.wholesome = 0
        self.silver = 0
        self.gold = 0
        self.platinum = 0

    def __str__(self):
        out = f"{self.name} has earned {self.karma} karma over {self.totalMessages} messages\n"
        out += f"karma per message = {round(self.karma/self.totalMessages,5)}\n"
        out += "awards: "
        out += f"wholesome = {self.wholesome}, "
        out += f"silver = {self.silver}, "
        out += f"gold = {self.gold}, "
        out += f"platinum = {self.platinum}\n"
        return out

def enumReactions(message, dic):
    print(" (",end='')
    for reaction in message.reactions:
        emoji = reaction.emoji if isinstance(reaction.emoji, str) else reaction.emoji.name
        count = reaction.count
        print(f"{count}*{emoji}, ",end='')
        for _ in range(count):
            update(dic[message.author.name], emoji)
    print("\b\b)")

def update(obj, emoji):
    emoji = emoji.lower()
    match emoji:
        case "reddit_upvote":
            obj.karma += 1
        case "upvote":
            obj.karma += 1
        case "quarter_upvote":
            obj.karma += 0.5
        case "half_upvote":
            obj.karma += 0.5
        case "downvote":
            obj.karma -= 1
        case "reddit_downvote":
            obj.karma -= 1
        case "quarter_downvote":
            obj.karma -= 0.5
        case "half_downvote":
            obj.karma -= 0.5
        case "reddit_wholesome":
            obj.wholesome += 1
        case "reddit_silver":
            obj.silver += 1
        case "reddit_gold":
            obj.gold += 1
        case "reddit_platinum":
            obj.platinum += 1
        case "Squidup":
            obj.karma += 1
        case "Squiddown":
            obj.karma += 1

@bot.command()
async def analyse(context):
    await context.send("KARMA SUBROUTINE INITIALISED")
    server = context.guild
    members = server.members
    nameToStats = {member.name : Stats(member.name) for member in members}
    count = 0
    for channel in server.text_channels:
        async for message in channel.history(limit=None, oldest_first=True):
            if message.author.name not in nameToStats: continue
            count += 1
            nameToStats[message.author.name].totalMessages += 1
            if message.reactions:
                print(f"({count}) {message.author.name}: {message.content}", end='') 
                enumReactions(message, nameToStats)

    analysis = [nameToStats[name] for name in nameToStats]
    place = 1
    for stat in sorted(analysis, key = lambda s : s.karma, reverse=True)[:10]:
        if stat.name in karmaMods: stat.karma += karmaMods[stat.name]
        await context.send(f"#{place} - {stat}")
        place += 1
    await context.send("KARMA == ANALYSED")

@bot.command()
async def gild(context):
    await context.send("Thank you kind stranger!")

@bot.command()
@commands.has_role("Karma Court Judge")
async def sentence(context, member: discord.Member):
    await context.send(f"ENUMERATING REDDIQUETTE VIOLATIONS FROM u/{member.name}")
    time.sleep(2)
    await context.send("CALCULATING COMMENSURATE KARMIC DEDUCTION")
    time.sleep(2)
    ded = random.randint(50,100)
    await context.send(f"FOR CRIMES AGAINST REDDIT AND XER PEOPLE, u/{member.name} IS HEREBY SENTENCED TO A KARMIC DEDUCTION TOTALLING {ded} REDDIT KARMA")
    if member.name in karmaMods:
        karmaMods[member.name] -= ded
    else:
        karmaMods[member.name] = -ded

bot.run('put token here')