import discord
import sqlite3
from discord.ext import commands
from utility import get_role_of_rank

def is_owner_or_admin():
    async def predicate(ctx: commands.Context):
        return ctx.author.id == ctx.bot.owner_id or ctx.author.guild_permissions.manage_guild
    return commands.check(predicate)

def check_server(serverid: int, c: sqlite3.Cursor, conn: sqlite3.Connection):
    c.execute('SELECT * FROM roleping WHERE server_id=?', (serverid,))
    if c.fetchone() is None:
        c.execute('INSERT INTO roleping VALUES (?, ?, ?, ?, ?)', (serverid, 60, 0, 0, 0))
        conn.commit()

class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.db = sqlite3.connect('database.db')
        self.c = self.db.cursor()
        self.bot = bot

    # Admin command group
    @commands.group(name='admin', description='Admin commands', invoke_without_command=True)
    @is_owner_or_admin()
    async def admin(self, ctx: commands.Context):
        embed = discord.Embed(title='Admin Commands', description='Here are the available admin commands:')
        embed.add_field(name='Subcommands', 
                        value="""$admin vcadmin - Displays VC ping admin commands and current settings""", 
                        inline=False)
        await ctx.send(embed=embed)

    # vcadmin command sub-group
    @admin.group(name='vcadmin', description='VC ping admin commands and settings', invoke_without_command=True)
    @is_owner_or_admin()
    async def vcadmin(self, ctx: commands.Context):
        check_server(ctx.guild.id, self.c, self.db)
        # Get the current settings from the database
        self.c.execute('SELECT timer_duration, rpenabled, role_id, min_rank FROM roleping WHERE server_id=?', (ctx.guild.id,))
        time, enabled, role, min_rank = self.c.fetchone()
        if ctx.invoked_subcommand is None:
            # msg = """Usage: $admin vcadmin <subcommand> <arguments>

            # Subcommands:
            # vcadmin timer <time> - Set the time between role pings in minutes
            # vcadmin enable/disable - Enable or disable role pings
            # vcadmin setrole <role> - Set the role to ping
            # vcadmin minrank <rank> - Set the minimum rank to use the pingvc command
            
            # Current Settings:
            # Time: {} minutes
            # Enabled: {}
            # Role: {} ({})
            # Minimum Level: {}
            # """.format(time, bool(enabled), role, ctx.guild.get_role(role).name if role != 0 else '', 'everyone' if min_rank == 0 else get_role_of_rank(ctx.guild, min_rank))
            embed = discord.Embed(title='Role Admin', description='Usage: $admin vcadmin <subcommand> <arguments>')
            embed.add_field(name='Subcommands:', value="""$admin vcadmin timer <time> - Set the time between role pings in minutes
            $admin vcadmin enable/disable - Enable or disable role pings
            $admin vcadmin setrole <role> - Set the role to ping according to role ID
            $admin vcadmin minrank <rank> - Set the minimum rank to use the /pingvc command""", inline=False)
            embed.add_field(name='Current Settings:', value="""Time: {} minutes
            Enabled: {}
            Role: {} ({})
            Minimum Level: {}""".format(time, 
                                        bool(enabled), 
                                        role, 
                                        ctx.guild.get_role(role).name if role != 0 else '', 
                                        'everyone' if min_rank == 0 else get_role_of_rank(ctx.guild, min_rank)), 
                                        inline=False)
            embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar.url)
            await ctx.send(embed=embed)

    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
    @vcadmin.command()
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
        self.db.commit()

        await ctx.send('Timer set to {} minutes.'.format(time))

    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
    @vcadmin.command()
    async def enable(self, ctx: commands.Context):
        # Update the enabled status in the database
        self.c.execute('UPDATE roleping SET rpenabled=1 WHERE server_id=?', (ctx.guild.id,))
        self.db.commit()
        await ctx.send('Role pings enabled')

    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
    @vcadmin.command()
    async def disable(self, ctx: commands.Context):
        # Update the enabled status in the database
        self.c.execute('UPDATE roleping SET rpenabled=0 WHERE server_id=?', (ctx.guild.id,))
        self.db.commit()
        await ctx.send('Role pings disabled')
    
    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
    @vcadmin.command()
    async def setrole(self, ctx: commands.Context, role: str):
        roleid = ctx.guild.get_role(int(role))
        if roleid is None:
            await ctx.send('Role not found')
            return
        role = roleid.id
        # Update the role ID in the database
        self.c.execute('UPDATE roleping SET role_id=? WHERE server_id=?', (role, ctx.guild.id))
        self.db.commit()
        await ctx.send('Role set to {}'.format(roleid.name))

    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
    @vcadmin.command()
    async def minrank(self, ctx: commands.Context, rank: int):
        # Validate rank, must be a positive integer
        if rank < 0:
            await ctx.send('Invalid rank')
            return
        # Update the minimum rank in the database
        self.c.execute('UPDATE roleping SET min_rank=? WHERE server_id=?', (rank, ctx.guild.id))
        self.db.commit()
        await ctx.send('Minimum rank set to {}'.format(get_role_of_rank(ctx.guild, rank)))
        

async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))