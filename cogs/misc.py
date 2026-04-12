import asyncio
import datetime
import logging
import random

import discord
from discord.ext import commands, tasks


status = [
    "ANALYSING KARMA",
    "MASS DOWNVOTING",
    "THANKING KIND STRANGER",
    "KARMA COURT JURY SERVICE",
    "SCROLLING REELS",
    "READING REDDIQUETTE",
    "BALATRO",
    "FORTNITE",
    "FRUIT MACHINE",
    "R6 SIEGE",
    "5D CHESS WITH MULTIVERSE TIME TRAVEL",
    "MINECRAFT",
    "NOTHING (EVER HAPPENS)",
    "BLADES IN THE DARK",
    "WORDLE",
    "R/GAMBLING",
    "TOUCHING GRASS",
    "KARMA FARMING",
    "FALLOUT: NEW VEGAS",
    "BALDUR'S GATE",
    "SKYRIM",
    "FACTORIO",
    "RIMWORLD",
    "JACKBOX",
    "THE NARWHAL BACONS AT MIDNIGHT",
    "FRIENDSLOP",
    "GEOGUESSR",
    "DARK SOULS 3",
    "ELDEN RING",
    "FISH AND A RICE CAKE",
    "MEDIEVAL DYNASTY",
    "CRUSADER KINGS 3",
    "PROJECT ZOMBOID",
    "OBLIVION HORSE ARMOUR DLC",
    "BLOONS TOWER DEFENSE 6",
    "PALWORLD",
    "HAMSTER HUNTER",
    "STARDEW VALLEY",
    "INTO THE BREACH",
    "PEGGLE",
    "PORTAL 2",
    "DEATH STRANDING",
    "METAL GEAR SOLID",
    "THE LAST OF US",
    "DISHONORED",
    "THE WITCHER 3: WILD HUNT",
    "DOOM",
    "EURO TRUCK SIMULATOR 2",
    "FALLOUT SHELTER",
    "HALO: THE MASTER CHIEF COLLECTION",
    "HOUSE FLIPPER",
    "KERBAL SPACE PROGRAM",
    "LEFT 4 DEAD 2",
    "LEGO STAR WARS",
    "MASS EFFECT",
    "MIDDLE EARTH: SHADOW OF WAR",
    "MONSTER HUNTER",
    "MOUNT & BLADE",
    "OUTER WILDS",
    "PAYDAY 2",
    "RED DEAD REDEMPTION 2",
    "ROCKET LEAGUE",
    "SEA OF THIEVES",
    "SLAY THE SPIRE",
    "SOUTH PARK: THE STICK OF TRUTH",
    "THE STANLEY PARABLE",
    "STAR WARS: BATTLEFRONT II",
    "ULTRAKILL",
    "UNDERTALE",
    "XCOM",
    "ALT-TABBED",
    "SAVE SCUMMING",
    "SPEEDRUNNING",
    "CHANGING SETTINGS",
    "AFK",
    "COOKIE CLICKER",
    "RISK OF RAIN 2",
    "HADES",
    "SATISFACTORY",
    "HEARTS OF IRON IV",
    "COUNTER-STRIKE 2",
    "TEAM FORTRESS 2",
    "POWERWASH SIMULATOR",
    "HELLDIVERS 2",
    "[deleted]",
    "GIVING OUT FREE KARMA",
    "STEALING CONTENT"
]


class Misc(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.init_time = datetime.datetime.now(datetime.timezone.utc)
        self.logger = logging.getLogger(self.__class__.__name__)

    @commands.Cog.listener()
    async def on_message(self, payload):
        if not payload.guild:
            return

        if payload.type in [
            discord.MessageType.premium_guild_subscription,
            discord.MessageType.premium_guild_tier_1,
            discord.MessageType.premium_guild_tier_2,
            discord.MessageType.premium_guild_tier_3
        ]:
            await payload.reply("Thank you for boosting the server kind stranger!")

        if payload.author.bot:
            return

        if "pass it on" in payload.content.lower():
            async for message in payload.channel.history(limit=100, oldest_first=False):
                if message.author.bot and message.content == payload.content:
                    return

            await asyncio.sleep(random.uniform(0, 2.5))
            await payload.channel.send(payload.content)
            self.logger.info(f"PASSING IT ON: {payload.content}")

        if "nothing ever happens" in payload.content.lower():
            await payload.reply(
                content="https://tenor.com/view/nothing-ever-happens-chud-chudjak-soyjak-90-seconds-to-nothing-gif-9277709574191520604"
            )
            self.logger.info("NOTHING EVER HAPPENS")

    @commands.command()
    async def gild(self, ctx):
        """
        Gild the Karma Analyser
        """
        await ctx.reply("Thank you kind stranger!")

    @tasks.loop(minutes=15)
    async def change_status(self):
        activity = random.choice(status)
        self.logger.info(f"CHANGED STATUS: {activity}")
        await self.bot.change_presence(activity=discord.Game(name=activity))


async def setup(bot):
    await bot.add_cog(Misc(bot))
