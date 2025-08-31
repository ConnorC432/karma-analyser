import discord
import asyncio
import json
import random
from discord.ext import commands


class Sentence(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_role("Karma Court Judge")
    async def sentence(self, ctx, member: discord.Member):
        """
        Sentence a user for breaches against the Reddiquette
        - `user` (required): Mention the user to sentence.
        """
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

async def setup(bot):
    await bot.add_cog(Sentence(bot))