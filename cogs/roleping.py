import discord
import time
# import sqlite3 # Migrating to sqlalchemy
import sqlalchemy
from sqlalchemy.orm import Session
from models import Server, ServerSettings, check_setting, get_setting, set_setting
import os
from discord import app_commands
from discord.ext import commands
from utility import user_is_at_least, get_role_of_rank

class RolePings(commands.Cog):
    """Adds commands to ping roles, used for VC pings"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
        # Confirm that the database exists, if not, throw an error
        if not os.path.isfile('database.db'):
            raise FileNotFoundError('database.db not found. Run createdb.py to create the database.')

    @app_commands.command(name='pingvc', description='Ping the vc role! It\'s time to chat!')
    async def pingvc(self, ctx: discord.Interaction):
        enabled, role, next_ping_time, ping_timer, min_rank = None, None, None, None, None
        # Check if the server is in the database
        
        with self.bot.db_session.begin() as c:
            # Check if the server is enabled and get the role ID and next ping time, ping timer, and minimum rank
            enabled = int(get_setting(c, ctx.guild.id, 'rp_enabled'))
            role = int(get_setting(c, ctx.guild.id, 'rp_role'))
            next_ping_time = int(get_setting(c, ctx.guild.id, 'rp_next_role_ping'))
            ping_timer = int(get_setting(c, ctx.guild.id, 'rp_timer_duration'))
            min_rank = int(get_setting(c, ctx.guild.id, 'rp_min_rank'))

            # Check if the user is at least rank min_rank
            if not user_is_at_least(ctx.user, min_rank):
                await ctx.response.send_message('You are not high enough level to use this command!', ephemeral=True)
                return
            
            # If the server is disabled or not in the database, don't ping the role
            if enabled == 0 or enabled is None:
                await ctx.response.send_message('VC pings are disabled for this server.', ephemeral=True)
                return
            role = discord.utils.get(ctx.guild.roles, id=role)

            # If the role is not found, don't ping the role (duh)
            if role is None:
                await ctx.response.send_message('Role not found, tell an admin to check `$roleadmin`', ephemeral=True)
                return
            
            # Check if current unix time is greater than the next ping time
            if time.time() > next_ping_time:
                # Update the next ping time in the database
                next_time = int(time.time() + ping_timer * 60)
                set_setting(c, ctx.guild.id, 'rp_next_role_ping', str(next_time))

            # If the next ping time is in the future, don't ping the role
            else:
                await ctx.response.send_message(f'It\'s not time to chat yet! {role.mention} can be pinged again at <t:{next_ping_time}:t>',
                                                 ephemeral=True)
                return
            
            # Finally, ping the role
            await ctx.response.send_message(f'Hey {role.mention}! {ctx.user.mention} has decided that it\'s time to chat!',
                                             allowed_mentions=discord.AllowedMentions(roles=True))

    @commands.command(name='listroles', description='List all roles and their IDs in the server')
    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
    async def listroles(self, ctx: commands.Context):
        # If you're not the bot owner or owner of the server, you can't use this command
        roles = ctx.guild.roles
        role_string = ''
        for role in roles:
            role_string += f'{role.name}: {role.id}\n'
        # Save the entire role list to a file and send it as a file
        with open('roles.txt', 'w', encoding="utf-8") as f:
            f.write(role_string)
        await ctx.send(file=discord.File('roles.txt'), content='Here\'s a list of all roles in this server and their IDs.')


async def setup(bot):
    await bot.add_cog(RolePings(bot))