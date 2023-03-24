import discord
import sqlite3
from discord.ext import commands
from utility import get_role_of_rank

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
    # Check if the user has "manage server" permission or is the owner of the bot
    @commands.group(name='admin', description='Admin commands', invoke_without_command=True)
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def admin(self, ctx: commands.Context):
        embed = discord.Embed(title='Admin Commands', description='Here are the available admin commands:')
        embed.add_field(name='Subcommands', 
                        value="""$admin vcadmin - Displays VC ping admin commands and current settings
                        $admin suggest - Displays suggestion admin commands and current settings""", 
                        inline=False)
        embed.add_field(name='Dev Commands', 
                        value="""$addrole <role ID> <rank> - Adds a role to the database with a specified rank
                        $removerole <role ID> - Remove a role from the database
                        $listranks - List all roles and their rank in the database
                        $listroles - List all roles and their ID in the server""", 
                        inline=False)
        await ctx.send(embed=embed)

    # vcadmin command sub-group
    @admin.group(name='vcadmin', description='VC ping admin commands and settings', invoke_without_command=True)
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def vcadmin(self, ctx: commands.Context):
        check_server(ctx.guild.id, self.c, self.db)
        # Get the current settings from the database
        self.c.execute('SELECT timer_duration, rpenabled, role_id, min_rank FROM roleping WHERE server_id=?', (ctx.guild.id,))
        time, enabled, role, min_rank = self.c.fetchone()
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(title='Role Admin', description='Usage: $admin vcadmin <subcommand> <arguments>')
            embed.add_field(name='Subcommands:', value="""$admin vcadmin timer <time> - Set the time between role pings in minutes
            $admin vcadmin enable/disable - Enable or disable role pings
            $admin vcadmin setrole <role ID> - Set the role to ping
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

    @vcadmin.command()
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
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

    @vcadmin.command()
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def enable(self, ctx: commands.Context):
        # Update the enabled status in the database
        self.c.execute('UPDATE roleping SET rpenabled=1 WHERE server_id=?', (ctx.guild.id,))
        self.db.commit()
        await ctx.send('Role pings enabled')

    @vcadmin.command()
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def disable(self, ctx: commands.Context):
        # Update the enabled status in the database
        self.c.execute('UPDATE roleping SET rpenabled=0 WHERE server_id=?', (ctx.guild.id,))
        self.db.commit()
        await ctx.send('Role pings disabled')
    
    @vcadmin.command()
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
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

    @vcadmin.command()
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def minrank(self, ctx: commands.Context, rank: int):
        # Validate rank, must be a positive integer
        if rank < 0:
            await ctx.send('Invalid rank')
            return
        # Update the minimum rank in the database
        self.c.execute('UPDATE roleping SET min_rank=? WHERE server_id=?', (rank, ctx.guild.id))
        self.db.commit()
        await ctx.send('Minimum rank set to {}'.format(get_role_of_rank(ctx.guild, rank)))

    # Suggest admin command sub-group
    @admin.group(name='suggest', description='Suggest admin commands and settings', invoke_without_command=True)
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def suggest(self, ctx: commands.Context):
        # Suggest db table: server_id, enabled, channel_id
        # Check whether the server is in the database or not
        self.c.execute('SELECT EXISTS(SELECT 1 FROM suggest WHERE server_id=?)', (ctx.guild.id,))
        exists = self.c.fetchone()[0]
        if not exists:
            self.c.execute('INSERT INTO suggest VALUES (?, 0, 0)', (ctx.guild.id,))
            self.db.commit()
            # Let the user know that the server was added to the database and re-run the command
            await ctx.send('Server added to database, please re-run the command')
            return
        # Get the channel ID and enabled status from the database
        self.c.execute('SELECT enabled, channel_id FROM suggest WHERE server_id=?', (ctx.guild.id,))
        enabled, channel = self.c.fetchone()
        # Create an embed to display the current settings
        embed = discord.Embed(title='Suggest Admin', description='Usage: $admin suggest <subcommand> <arguments>')
        embed.add_field(name='Subcommands:', value="""$admin suggest enable/disable - Enable or disable suggestions
        $admin suggest setchannel- Set the channel to send suggestions to""", inline=False)
        embed.add_field(name='Current Settings:', value="""Enabled: {}
        Channel: {} ({})""".format(bool(enabled),
                                    channel,
                                    ctx.guild.get_channel(channel).name if channel != 0 else ''), inline=False)
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar.url)
        await ctx.send(embed=embed)

    @suggest.command()
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def enable(self, ctx: commands.Context):
        # Update the enabled status in the database
        self.c.execute('UPDATE suggest SET enabled=1 WHERE server_id=?', (ctx.guild.id,))
        self.db.commit()
        await ctx.send('Suggestions enabled')

    @suggest.command()
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def disable(self, ctx: commands.Context):
        # Update the enabled status in the database
        self.c.execute('UPDATE suggest SET enabled=0 WHERE server_id=?', (ctx.guild.id,))
        self.db.commit()
        await ctx.send('Suggestions disabled')

    @suggest.command()
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def setchannel(self, ctx: commands.Context):
        # Update the channel ID in the database to the current channel
        self.c.execute('UPDATE suggest SET channel_id=? WHERE server_id=?', (ctx.channel.id, ctx.guild.id))
        self.db.commit()
        await ctx.send('Suggestions channel set to {}'.format(ctx.channel.name))
        

async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))