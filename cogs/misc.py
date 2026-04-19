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
    "STEALING CONTENT",
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
            discord.MessageType.premium_guild_tier_3,
        ]:
            await payload.reply("Thank you for boosting the server kind stranger!")

        if payload.author.bot:
            return

        try:
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
        except discord.Forbidden:
            self.logger.warning(f"Missing permissions to reply in channel {payload.channel.id} of guild {payload.guild.id}")
        except discord.HTTPException:
            self.logger.exception(f"HTTP Error replying to message {payload.id}")
        except Exception:
            self.logger.exception(f"Unexpected error in on_message in {self.__class__.__name__}")

    @commands.command()
    async def gild(self, ctx):
        """
        Gild the Karma Analyser
        """
        await ctx.reply("Thank you kind stranger!")

    @tasks.loop(minutes=15)
    async def _change_status(self):
        try:
            activity = random.choice(status)
            self.logger.info(f"CHANGED STATUS: {activity}")
            await self.bot.change_presence(activity=discord.Game(name=activity))
        except Exception:
            self.logger.exception("Unexpected error in _change_status loop")

    @_change_status.before_loop
    async def before_change_status(self):
        await self.bot.wait_until_ready()
        if not self.bot.get_cog("Analyse"):
            self.logger.debug("Analyse cog not loaded, skipping analysis wait")
            return

        self.logger.debug("Waiting for analysis to finish before starting change status loop")
        while not hasattr(self.bot, "analysis_finished"):
            self.logger.debug("Bot has no analysis_finished attribute yet, waiting")
            await asyncio.sleep(1)
        self.logger.debug("Bot has analysis_finished attribute, waiting for event to be set")
        await self.bot.analysis_finished.wait()
        self.logger.info("KARMA ANALYSIS FINISHED, CHANGE STATUS LOOP STARTED")


async def setup(bot):
    cog = Misc(bot)
    await bot.add_cog(cog)
    cog._change_status.start()
