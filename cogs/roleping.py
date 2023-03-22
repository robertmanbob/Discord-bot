import discord
import time
import sqlite3
import os
from discord import app_commands
from discord.ext import commands
from utility import user_is_at_least, get_role_of_rank

# Create a function that checks if a serverid is in the database, if not, add it with default values
# Server ID, ping timer, enabled, role ID, next ping time
def check_server(serverid: int, c: sqlite3.Cursor, conn: sqlite3.Connection):
    c.execute('SELECT * FROM roleping WHERE server_id=?', (serverid,))
    if c.fetchone() is None:
        c.execute('INSERT INTO roleping VALUES (?, ?, ?, ?, ?)', (serverid, 60, 0, 0, 0))
        conn.commit()

class RolePings(commands.Cog):
    """Adds commands to ping roles, used for VC pings"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
        # Confirm that the database exists, if not, throw an error
        if not os.path.isfile('database.db'):
            raise FileNotFoundError('database.db not found. Run createdb.py to create the database.')
        
        # Connect to the database
        self.conn = sqlite3.connect('database.db')
        self.c = self.conn.cursor()

    @app_commands.command(name='pingvc', description='Ping the vc role! It\'s time to chat!')
    async def pingvc(self, ctx: discord.Interaction):
        # Check if the server is in the database
        check_server(ctx.guild.id, self.c, self.conn)

        # Check if the server is enabled and get the role ID and next ping time, ping timer, and minimum rank
        self.c.execute('SELECT rpenabled, role_id, next_roleping, timer_duration, min_rank FROM roleping WHERE server_id=?', (ctx.guild.id,))
        enabled, role, next_ping_time, ping_timer, min_rank = self.c.fetchone()

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
            self.c.execute('UPDATE roleping SET next_roleping=? WHERE server_id=?', (next_time, ctx.guild.id))
            self.conn.commit()

        # If the next ping time is in the future, don't ping the role
        else:
            await ctx.response.send_message('It\'s not time to chat yet! {} can be pinged again at <t:{}:t>'.format(
                role.mention, 
                next_ping_time), ephemeral=True
                )
            return
        
        # Finally, ping the role
        await ctx.response.send_message('Hey {}! {} has decided that it\'s time to chat!'.format(role.mention, ctx.user.mention), allowed_mentions=discord.AllowedMentions(roles=True))

    @commands.command(name='listroles', description='List all roles and their IDs in the server')
    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
    async def listroles(self, ctx: commands.Context):
        # If you're not the bot owner or owner of the server, you can't use this command
        roles = ctx.guild.roles
        role_string = ''
        for role in roles:
            role_string += '{}: {}\n'.format(role.name, role.id)
        # Save the entire role list to a file and send it as a file
        with open('roles.txt', 'w', encoding="utf-8") as f:
            f.write(role_string)
        await ctx.send(file=discord.File('roles.txt'), content='Here\'s a list of all roles in this server and their IDs.')


async def setup(bot):
    await bot.add_cog(RolePings(bot))