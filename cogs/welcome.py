import discord
import sqlite3
import os
import random
from discord.ext import commands
from utility import generate_welcome_card

# Table schema:
# CREATE TABLE welcome (server_id INTEGER, wenabled BOOL, channel_id INTEGER)

class Welcome(commands.Cog):
    """Welcome users to the server using a welcome card"""
    def __init__(self, bot):
        self.bot = bot
        self.db = sqlite3.connect('database.db')
        self.c = self.db.cursor()

    # Join listener
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """When a member joins, generate a welcome card"""
        # Query the database for the enabled status and channel
        self.c.execute('SELECT wenabled, channel_id FROM welcome WHERE server_id=?', (member.guild.id,))
        result = self.c.fetchone()
        # If the result is None, return
        if result is None:
            return
        # If the welcome is not enabled, return
        if not result[0]:
            return
        channel = member.guild.get_channel(result[1])
        # If the channel is None, return
        if channel is None:
            return
        # If the user is a bot, return
        if member.bot:
            return
        # Set the bot to typing in the channel
        async with channel.typing():
            # Attempt to make and send the welcome card, deleting it if we catch an error
            try:
                # Generate the welcome card. If the user has no avatar, use the default avatar
                path = generate_welcome_card(member.avatar.url if member.avatar else "https://cdn.discordapp.com/embed/avatars/0.png", member.name)
                # Send the welcome card to the designated channel in an embed
                embed = discord.Embed()
                embed.set_image(url=f"attachment://{path}")
                embed.title = f"Everyone be friendly and say hello!"
                embed.description = f"Welcome to Collusion, {member.name}#{member.discriminator}! We hope you never leave the best server ever!"
                await channel.send(embed=embed, file=discord.File(path))
                # Delete the welcome card
                os.remove(path)
            except Exception as e:
                # Delete the welcome card if it exists
                if os.path.exists(path):
                    os.remove(path)
                # DM the owner of the bot with the error
                await self.bot.get_user(self.bot.owner_id).send(f"Error in welcome card generation: {e}")

    # Test the listener, admin or owner only
    @commands.command()
    @commands.check_any(commands.is_owner(), commands.has_permissions(manage_guild=True))
    async def test_welcome(self, ctx: commands.Context):
        """Test the welcome listener"""
        await self.on_member_join(ctx.author)

    # Leave listener
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """When a member leaves, send a message in the welcome channel"""
        insults = [", they were a smelly potbellied prick anyway!", 
                   ". A pox on their house!",
                   ". I knew something was off about them!",
                   "! \*spits\*",
                   ". Oh well. Anyways, "]
        # Query the database for the enabled status and channel
        self.c.execute('SELECT wenabled, channel_id FROM welcome WHERE server_id=?', (member.guild.id,))
        result = self.c.fetchone()
        # If the result is None, return
        if result is None:
            return
        # If the welcome is not enabled, return
        if not result[0]:
            return
        channel = member.guild.get_channel(result[1])
        # If the channel is None, return
        if channel is None:
            return
        # Send the message in an embed with a random insult
        embed = discord.Embed(description=f"Looks like {member.name}#{member.discriminator} left" + random.choice(insults))
        await channel.send(embed=embed)

    # Test leave listener
    @commands.command()
    @commands.check_any(commands.is_owner(), commands.has_permissions(manage_guild=True))
    async def test_leave(self, ctx: commands.Context):
        """Test the leave listener"""
        await self.on_member_remove(ctx.author)
        

async def setup(bot):
    await bot.add_cog(Welcome(bot))
        
    