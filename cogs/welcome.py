import discord
import sqlalchemy
from sqlalchemy.orm import Session
from models import ServerSettings, get_setting, set_setting, check_setting
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
        # self.db = sqlite3.connect('database.db')
        # self.c = self.db.cursor()

        # Override goodbyes, in case we want to give someone a custom goodbye
        # Dictionary with a user's ID as the key and a goodbye message as the value
        self.goodbyes = {}

    # Join listener
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """When a member joins, generate a welcome card"""
        # Query the database for the enabled status and channel
        # self.c.execute('SELECT wenabled, channel_id FROM welcome WHERE server_id=?', (member.guild.id,))
        # result = self.c.fetchone()
        result = None
        with self.bot.db_session.begin() as c:
            check_setting(member.guild.id, c, 'wc_enabled', '0')
            check_setting(member.guild.id, c, 'wc_channel', '0')
            result = int(get_setting(c, member.guild.id, 'wc_enabled')), int(get_setting(c, member.guild.id, 'wc_channel'))
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
                await channel.send(embed=embed, file=discord.File(path), allowed_mentions=discord.AllowedMentions.none())
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

    # Add a custom goodbye
    # Owner only
    @commands.command()
    @commands.is_owner()
    async def add_goodbye(self, ctx: commands.Context, user: discord.User, *, goodbye: str):
        """Add a custom goodbye message for a user"""
        # Add the goodbye to the dictionary
        self.goodbyes[user.id] = goodbye
        # Send a confirmation message
        await ctx.send(f"Added goodbye for {user.name}#{user.discriminator}")

    # Ignore a leaver
    # Owner only
    @commands.command()
    @commands.is_owner()
    async def ignore_leave(self, ctx: commands.Context, user: discord.User):
        """Ignore a user leaving"""
        # Add the user to the dictionary
        self.goodbyes[user.id] = ""
        # Send a confirmation message
        await ctx.send(f"Ignored {user.name}#{user.discriminator}")

    # Leave listener
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """When a member leaves, send a message in the welcome channel"""
        # If the user is a bot, return
        if member.bot:
            return

        insults = [", they were a smelly potbellied prick anyway!", 
                   ". A pox on their house!",
                   ". I knew something was off about them!",
                   "! \*spits\*",
                   ". Oh well. Anyways, ",
                   ". I don't know them, but fuck em'",
                   ", trash."]
        
        # If the user has a custom goodbye, use it as the goodbye message. Else, select insult.
        try:
            insult = self.goodbyes[member.id]
            # If the leave message is "", ignore the leaver
            if insult == "":
                return
        except KeyError:
            insult = random.choice(insults)

        # Query the database for the enabled status and channel
        # self.c.execute('SELECT wenabled, wc_channel FROM welcome WHERE server_id=?', (member.guild.id,))
        # result = self.c.fetchone()
        with self.bot.db_session.begin() as c:
            check_setting(member.guild.id, c, 'wc_enabled', '0')
            check_setting(member.guild.id, c, 'wc_channel', '0')
            result = int(get_setting(c, member.guild.id, 'wc_enabled')), int(get_setting(c, member.guild.id, 'wc_channel'))
            # print(f"Leave message time {result}")
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
        embed = discord.Embed(description=f"Looks like {member.name}#{member.discriminator} left" + insult)
        await channel.send(embed=embed)

    # Test leave listener
    @commands.command()
    @commands.check_any(commands.is_owner(), commands.has_permissions(manage_guild=True))
    async def test_leave(self, ctx: commands.Context):
        """Test the leave listener"""
        await self.on_member_remove(ctx.author)
        

async def setup(bot):
    await bot.add_cog(Welcome(bot))
        
    