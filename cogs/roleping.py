import discord
import configparser
import time
import sqlite3
import os
from discord import app_commands
from discord.ext import commands

# Set of servers that are known to be in the database
known_servers = set()

# Create a function that checks if a serverid is in the database, if not, add it with default values
# Server ID, ping timer, enabled, role ID, next ping time
def check_server(serverid: int, c: sqlite3.Cursor, conn: sqlite3.Connection):
    # If the server is already in the known servers set, don't check the database
    if serverid in known_servers:
        return
    c.execute('SELECT * FROM roleping WHERE server_id=?', (serverid,))
    if c.fetchone() is None:
        c.execute('INSERT INTO roleping VALUES (?, ?, ?, ?, ?)', (serverid, 60, 1, 0, 0))
        conn.commit()
    # Add the server to the known servers set so we don't have to check the database again
    known_servers.add(serverid)

class RolePings(commands.Cog):
    """Adds commands to ping roles, used for VC pings"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
        # Confirm that the database exists, if not, throw an error
        if not os.path.isfile('roleping.db'):
            raise FileNotFoundError('roleping.db not found. Run createdb.py to create the database.')
        
        # Connect to the database
        self.conn = sqlite3.connect('roleping.db')
        self.c = self.conn.cursor()

    @app_commands.command(name='pingvc', description='Ping the vc role! It\'s time to chat!')
    async def pingvc(self, ctx: discord.Interaction):
        # Check if the server is in the database
        check_server(ctx.guild.id, self.c, self.conn)
        # Check if the server is enabled and get the role ID and next ping time, and ping timer
        self.c.execute('SELECT rpenabled, role_id, next_roleping, timer_duration FROM roleping WHERE server_id=?', (ctx.guild.id,))
        enabled, role, next_ping_time, ping_timer = self.c.fetchone()
        # If the server is disabled, don't ping the role
        if enabled == 0:
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
        await ctx.response.send_message('Hey {}! {} has decided that it\'s time to chat!'.format(role.mention, ctx.user.mention), allowed_mentions=discord.AllowedMentions(roles=True))

    @app_commands.command(name='listroles', description='List all roles and their IDs in the server')
    async def listroles(self, ctx: discord.Interaction):
        roles = ctx.guild.roles
        role_string = ''
        for role in roles:
            role_string += '{}: {}\n'.format(role.name, role.id)
        await ctx.response.send_message(role_string, ephemeral=True)

    # Commands in the admin group are only available to the bot owner and server admins
    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
    @commands.group(invoke_without_command=True)
    async def roleadmin(self, ctx: commands.Context):
        check_server(ctx.guild.id, self.c, self.conn)
        # Get the current settings from the database
        self.c.execute('SELECT timer_duration, rpenabled, role_id FROM roleping WHERE server_id=?', (ctx.guild.id,))
        time, enabled, role = self.c.fetchone()
        if ctx.invoked_subcommand is None:
            msg = """Usage: $roleadmin <subcommand> <arguments>

            Subcommands:
            roleadmin timer <time> - Set the time between role pings in minutes
            roleadmin enable/disable - Enable or disable role pings
            roleadmin setrole <role> - Set the role to ping
            
            Current Settings:
            Time: {} minutes
            Enabled: {}
            Role: {} ({})
            """.format(time, bool(enabled), role, ctx.guild.get_role(role).name if role != 0 else '')
            embed = discord.Embed(title='Role Admin', description=msg)
            embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar.url)
            await ctx.send(embed=embed)

    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
    @roleadmin.command()
    async def timer(self, ctx: commands.Context, time: int):
        # Validate time, must be a positive integer
        if time <= 0:
            await ctx.send('Invalid time')
            return
        # Get the old time and next ping time from the database
        self.c.execute('SELECT timer_duration, next_roleping FROM roleping WHERE server_id=?', (ctx.guild.id,))
        old_time, next_ping_time = self.c.fetchone()

        # Subtract the old time from the next ping time, then add the new time
        # this will update the cooldown to the new time
        next_ping_time = next_ping_time - (old_time * 60) + (time * 60)

        # Update the timer duration and next ping time in the database
        self.c.execute('UPDATE roleping SET timer_duration=?, next_roleping=? WHERE server_id=?', (time, next_ping_time, ctx.guild.id))
        self.conn.commit()

        await ctx.send('Timer set to {} minutes.'.format(time))

    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
    @roleadmin.command()
    async def enable(self, ctx: commands.Context):
        # Update the enabled status in the database
        self.c.execute('UPDATE roleping SET rpenabled=1 WHERE server_id=?', (ctx.guild.id,))
        self.conn.commit()
        await ctx.send('Role pings enabled')

    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
    @roleadmin.command()
    async def disable(self, ctx: commands.Context):
        # Update the enabled status in the database
        self.c.execute('UPDATE roleping SET rpenabled=0 WHERE server_id=?', (ctx.guild.id,))
        self.conn.commit()
        await ctx.send('Role pings disabled')
    
    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
    @roleadmin.command()
    async def setrole(self, ctx: commands.Context, role: str):
        roleid = ctx.guild.get_role(int(role))
        if roleid is None:
            await ctx.send('Role not found')
            return
        role = roleid.id
        # Update the role ID in the database
        self.c.execute('UPDATE roleping SET role_id=? WHERE server_id=?', (role, ctx.guild.id))
        self.conn.commit()
        await ctx.send('Role set to {}'.format(roleid.mention))
        


async def setup(bot):
    await bot.add_cog(RolePings(bot))