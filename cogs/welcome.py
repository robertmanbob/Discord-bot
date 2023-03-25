import discord
import sqlite3
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
        # If the user does not have an avatar, return
        if member.avatar is None:
            return
        # Generate the welcome card
        path = generate_welcome_card(member.avatar.url, member.name)
        # Send the welcome card to the designated channel in an embed
        await channel.send(embed=discord.Embed().set_image(url=f"attachment://{path}"), file=discord.File(path))

    # Test the listener, admin or owner only
    @commands.command()
    @commands.check_any(commands.is_owner(), commands.has_permissions(manage_guild=True))
    async def test_welcome(self, ctx: commands.Context):
        """Test the welcome listener"""
        await self.on_member_join(ctx.author)

async def setup(bot):
    await bot.add_cog(Welcome(bot))
        
    