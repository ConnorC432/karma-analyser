import logging
import random
from datetime import timedelta

import discord
from discord.ext import commands

import utils


QUESTIONS = [
    "Rip your foreskin off with rusty pliers",
    "Goon to Toni Ahier",
    "Go to the job centre",
    "Polish Ben's big bald head",
    "Shave your belly with a rusty razor",
    "Spend a night in a 'Ullian Premier Inn",
    "Get in a plane when Jaden is the pilot",
    "Move to Mongoria",
    "Speak in a chinese accent for the rest of your life",
    "Wear a slug outfit near chandy",
    "Order a Cheng's garden then just get a dominoes delivered instead of picking it up",
    "Shove a pencil up your arse",
    "Clog Taz's toilet",
    "Finger your bum",
    "Bum your finger",
    "Be Indian",
    "Be Chinese",
    "Be Japanese",
    "Be Korean",
    "Brown butter",
    "Avoid paying tax",
    "Deliver an amazon parcel",
    "Be vegan",
    "Show your nob to Beth Varly",
    "Cut your left hand off",
    "Cut your right hand off",
    "Cut your left foot off",
    "Cut your right foot off",
    "Cut your nob off",
    "Lower your IQ points by 40",
    "Vote Reform UK",
    "Move to Skeggy",
    "Fight in a trial of seven",
    "Eat Indian street food",
    "Sniff Wayney's hairy toes",
    "Take a hit from Carol's electric bong",
    "Cook Crumble",
    "Recreate 9/11",
    "Go to a pub and order",
    "Have all the games",
    "Have no games",
    "Dance, walk and rearrange furniture",
    "Let the cat out of the bag",
    "Let the Tazmin out of the inside",
    "Be paralysed from the waist down",
    "Be paralysed from the neck down",
    "Get abducted by P Diddy",
    "Be chained to a radiator for 24 hours",
    "Be in a Mr Beast Video",
    "Down an entire bottle of vodka",
    "Milk Ben's teets into a bucket",
    "Watch Barnyard",
    "Watch Hotel Rwanda",
    "Watch The Office",
    "Watch The Matrix",
    "Watch The Lord of the Rings",
    "Watch all of One Piece without sleeping",
    "Pass a GCSE maths test",
    "Lick Jaden's armpits",
    "Move to 'Ull",
    "Goon to the fish in the deep aquarium in 'Ull",
    "Drink Taz's bong water",
    "Work for Amazon",
    "Work for Tesco",
    "Work for McDonalds",
    "Eat out Bonnie Blue",
    "Drive a VW Passat",
    "Own an unreliable Datsun",
    "Finger James May",
    "Play Tarkov",
    "Play Minecraft",
    "Play Fortnite",
    "Play League of Legends",
    "Play Valorant",
    "Play Overwatch",
    "Play Wordspud",
    "Play WynnCraft",
    "Play Soggy Biscuit",
    "'Lose' Soggy Biscuit",
    "'Win' Soggy Biscuit",
]


class WouldYouRather(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(self.__class__.__name__)

    @commands.command(aliases=["wyr"])
    async def wouldyourather(self, ctx):
        """
        Create a would you rather question
        """

        if ctx.guild.id in utils.VALID_SERVER_IDS_1:
            poll = discord.Poll(
                question="Would you rather:",
                duration=timedelta(hours=1),
                multiple=False,
            )

            option_a = random.choice(QUESTIONS)
            option_b = random.choice(QUESTIONS)
            while option_a == option_b:
                option_b = random.choice(QUESTIONS)

            poll.add_answer(text=option_a)
            poll.add_answer(text=option_b)

            self.logger.debug(
                f"Would you rather poll created: {option_a} or {option_b}"
            )

            await ctx.reply(poll=poll)

        self.logger.debug("WYR command ignored")
        return


async def setup(bot):
    await bot.add_cog(WouldYouRather(bot))
