import discord
import sqlite3
from discord.ext import commands

class Silly(commands.Cog):
    """Silly commands"""
    def __init__(self, bot):
        self.bot = bot
        self.db = sqlite3.connect('database.db')
        self.c = self.db.cursor()

    # Owner only, not a slash command
    @commands.command()
    async def chance(self, ctx: commands.Context):
        """Reveals the true form of Chance"""
        # Send a specific image via an embed
        # This is a joke command, so it's not very useful
        # Check if the sender is the owner of the bot or the person with this ID 363872734532468754
        if ctx.author.id == ctx.bot.owner_id or ctx.author.id == 363872734532468754:
            await ctx.send(embed=discord.Embed().set_image(url='https://static.miraheze.org/greatcharacterswiki/thumb/0/08/1481909501350.png/290px-1481909501350.png'))

async def setup(bot):
    await bot.add_cog(Silly(bot))

    