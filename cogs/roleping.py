import discord
import configparser
import time
from discord import app_commands
from discord.ext import commands

class RolePings(commands.Cog):
    """Adds commands to ping roles, used for VC pings"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
        # Open roleping.ini and read the current role ping settings, setting defaults if they don't exist
        self.config = configparser.ConfigParser()
        self.config.read('cogs/roleping.ini')
        if 'time' not in self.config['DEFAULT']:
            self.config['DEFAULT']['time'] = '60'
            self.config['DEFAULT']['enabled'] = 'True'
            self.config['DEFAULT']['role'] = '0'
            self.config['DEFAULT']['next_ping_time'] = '0'
            with open('cogs/roleping.ini', 'w') as configfile:
                self.config.write(configfile)
        
        self.time = int(self.config['DEFAULT']['time'])
        if self.config['DEFAULT']['enabled'] == 'True':
            self.enabled = True
        else:
            self.enabled = False
        self.role = int(self.config['DEFAULT']['role'])
        self.next_ping_time = int(self.config['DEFAULT']['next_ping_time'])

    # @app_commands.command(name='pingrole', description='Ping a role by name')
    # async def pingrole(self, ctx: discord.Interaction, role_name: str):
    #     role = discord.utils.get(ctx.guild.roles, name=role_name)
    #     if role is None:
    #         await ctx.send('Role not found')
    #         return
    #     await ctx.response.send_message('Pinging role {}'.format(role.mention), allowed_mentions=discord.AllowedMentions(roles=True))

    @app_commands.command(name='pingvc', description='Ping the vc role! It\'s time to chat!')
    async def pingvc(self, ctx: discord.Interaction):
        if not self.enabled:
            await ctx.response.send_message('Role pings are disabled. Cope and seethe.', ephemeral=True)
            return
        role = discord.utils.get(ctx.guild.roles, id=self.role)
        if role is None:
            await ctx.response.send_message('Role not found, let Robert#6519 know :(', ephemeral=True)
            return
        # Check if current unix time is greater than the next ping time
        if time.time() > self.next_ping_time:
            # Update the next ping time
            self.next_ping_time = int(time.time()) + self.time * 60
            self.config['DEFAULT']['next_ping_time'] = str(self.next_ping_time)
            with open('cogs/roleping.ini', 'w') as configfile:
                self.config.write(configfile)
        # If the next ping time is in the future, don't ping the role
        else:
            await ctx.response.send_message('It\'s not time to chat yet! {} can be pinged again at <t:{}:t>'.format(
                ctx.guild.get_role(self.role).mention, 
                self.next_ping_time), ephemeral=True
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
        if ctx.invoked_subcommand is None:
            msg = """Usage: $roleadmin <subcommand> <arguments>

            Subcommands:
            roleadmin timer <time> - Set the time between role pings in minutes
            roleadmin enable/disable - Enable or disable role pings
            roleadmin setrole <role> - Set the role to ping
            
            Current Settings:
            Time: {} minutes
            Enabled: {}
            Role: {}
            """.format(self.time, self.enabled, self.role)
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
        old_time = self.time
        self.time = time
        self.config['DEFAULT']['time'] = str(time)
        with open('cogs/roleping.ini', 'w') as configfile:
            self.config.write(configfile)

        # Subtract the old time from the next ping time, then add the new time
        # this will update the cooldown to the new time
        self.next_ping_time = self.next_ping_time - (old_time * 60) + (time * 60)

        await ctx.send('Timer set to {} minutes.'.format(time))

    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
    @roleadmin.command()
    async def enable(self, ctx: commands.Context):
        self.enabled = True
        self.config['DEFAULT']['enabled'] = 'True'
        with open('cogs/roleping.ini', 'w') as configfile:
            self.config.write(configfile)
        await ctx.send('Role pings enabled')

    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
    @roleadmin.command()
    async def disable(self, ctx: commands.Context):
        self.enabled = False
        self.config['DEFAULT']['enabled'] = 'False'
        with open('cogs/roleping.ini', 'w') as configfile:
            self.config.write(configfile)
        await ctx.send('Role pings disabled')
    
    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
    @roleadmin.command()
    async def setrole(self, ctx: commands.Context, role: str):
        roleid = ctx.guild.get_role(int(role))
        if roleid is None:
            await ctx.send('Role not found')
            return
        self.role = roleid.id
        self.config['DEFAULT']['role'] = str(roleid.id)
        with open('cogs/roleping.ini', 'w') as configfile:
            self.config.write(configfile)
        await ctx.send('Role set to {}'.format(ctx.guild.get_role(self.role)))


async def setup(bot):
    await bot.add_cog(RolePings(bot))