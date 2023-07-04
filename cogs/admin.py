import discord
# import sqlite3
import asyncio
import sqlalchemy
import logging
from sqlalchemy.orm import Session
from discord.ext import commands
from utility import get_role_of_rank
from models import get_setting, set_setting, check_setting, ServerSettings, Server, Rank, NameReply

class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # Admin command group
    # Check if the user has "manage server" permission or is the owner of the bot
    @commands.group(name='admin', description='Admin commands', invoke_without_command=True)
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def admin(self, ctx: commands.Context):
        embed = discord.Embed(title='Admin Commands', description='Here are the available admin commands:')
        embed.add_field(name='Subcommands', 
                        value="""$admin vcadmin - Displays VC ping admin commands and current settings
                        $admin deadchat - Displays deadchat admin commands and current settings
                        $admin suggest - Displays suggestion admin commands and current settings
                        $admin welcome - Displays welcome admin commands and current settings""", 
                        inline=False)
        embed.add_field(name='Dev Commands', 
                        value="""$addrole <role ID> <rank> - Adds a role to the database with a specified rank
                        $removerole <role ID> - Remove a role from the database
                        $listranks - List all roles and their rank in the database
                        $listroles - List all roles and their ID in the server""", 
                        inline=False)
        embed.add_field(name='Other Commands',
                        value="""$panic <*optional* message>- Logs a panic message and exits the bot""", 
                        inline=False)
        await ctx.send(embed=embed)

    # vcadmin command sub-group
    @admin.group(name='vcadmin', description='VC ping admin commands and settings', invoke_without_command=True)
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def vcadmin(self, ctx: commands.Context):
        # Check that the settings exist in the database
        # rp_timer_duration - Time between role pings in minutes
        # rp_enabled - Whether role pings are enabled
        # rp_role - The role to ping
        # rp_min_rank - The minimum rank to use the /pingvc command
        role, time, enabled, min_rank = 0, 0, 0, 0
        with self.bot.db_session.begin() as c:
            if not check_setting(ctx.guild.id, c, 'rp_timer_duration', '0'):
                await ctx.send('Could not get role ping timer duration')
                return
            if not check_setting(ctx.guild.id, c, 'rp_enabled', '0'):
                await ctx.send('Could not get role ping enabled')
                return
            if not check_setting(ctx.guild.id, c, 'rp_role', '0'):
                await ctx.send('Could not get role ping role')
                return
            if not check_setting(ctx.guild.id, c, 'rp_min_rank', '0'):
                await ctx.send('Could not get role ping minimum rank')
                return
            # Get the settings from the database
            time = get_setting(c, ctx.guild.id, 'rp_timer_duration')
            enabled = get_setting(c, ctx.guild.id, 'rp_enabled')
            role = get_setting(c, ctx.guild.id, 'rp_role')
            min_rank = get_setting(c, ctx.guild.id, 'rp_min_rank')

        if ctx.invoked_subcommand is None:
            embed = discord.Embed(title='Role Admin', description='Usage: $admin vcadmin <subcommand> <arguments>')
            embed.add_field(name='Subcommands:', value="""$admin vcadmin timer <time> - Set the time between role pings in minutes
            $admin vcadmin enable/disable - Enable or disable role pings
            $admin vcadmin setrole <role ID> - Set the role to ping
            $admin vcadmin minrank <rank> - Set the minimum rank to use the /pingvc command""", inline=False)
            embed.add_field(name='Current Settings:', value=f"""Time: {time} minutes
            Enabled: {bool(enabled)}
            Role: {role} ({ctx.guild.get_role(int(role)).name if role != 0 else ''})
            Minimum rank: {min_rank}""", inline=False)
            embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar.url)
            await ctx.send(embed=embed)

    @vcadmin.command(name='timer', aliases=['vc_timer'], description='Set the time between role pings in minutes')
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def vc_timer(self, ctx: commands.Context, time: int):
        # Validate time, must be a positive integer
        if time <= 0:
            await ctx.send('Invalid time')
            return
        # Get the old time and next ping time from the database
        # self.c.execute('SELECT timer_duration, next_roleping FROM roleping WHERE server_id=?', (ctx.guild.id,))
        # old_time, next_ping_time = self.c.fetchone()
        with self.bot.db_session.begin() as c:
            old_time = int(get_setting(c, ctx.guild.id, 'rp_timer_duration'))
            check_setting(ctx.guild.id, c, 'rp_next_ping', '0')
            next_ping_time = int(get_setting(c, ctx.guild.id, 'rp_next_ping'))

        # Subtract the old time from the next ping time, then add the new time
        # this will update the cooldown to the new time
        next_ping_time = next_ping_time - (old_time * 60) + (time * 60)

        # Update the timer duration and next ping time in the database
        with self.bot.db_session.begin() as c:
            set_setting(c, ctx.guild.id, 'rp_timer_duration', str(time))
            set_setting(c, ctx.guild.id, 'rp_next_ping', str(next_ping_time))

        await ctx.send(f'Timer set to {time} minutes.')

    @vcadmin.command(name='enable', aliases=['vc_enable'])
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def vc_enable(self, ctx: commands.Context):
        # Update the enabled status in the database
        with self.bot.db_session.begin() as c:
            set_setting(c, ctx.guild.id, 'rp_enabled', '1')
        await ctx.send('Role pings enabled')

    @vcadmin.command(name='disable', aliases=['vc_disable'])
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def vc_disable(self, ctx: commands.Context):
        # Update the enabled status in the database
        with self.bot.db_session.begin() as c:
            set_setting(c, ctx.guild.id, 'rp_enabled', '0')
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
        with self.bot.db_session.begin() as c:
            set_setting(c, ctx.guild.id, 'rp_role', str(role))
        await ctx.send(f'Role set to {roleid.name}')

    @vcadmin.command()
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def minrank(self, ctx: commands.Context, rank: int):
        # Validate rank, must be a positive integer
        if rank < 0:
            await ctx.send('Invalid rank')
            return
        # Update the minimum rank in the database
        with self.bot.db_session.begin() as c:
            set_setting(c, ctx.guild.id, 'rp_min_rank', str(rank))
        await ctx.send(f'Minimum rank set to {get_role_of_rank(ctx.guild, rank)}')

    # Dead chat ping admin command sub-group
    @admin.group(name='deadchat', description='Dead chat ping admin commands and settings', invoke_without_command=True)
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def deadchat(self, ctx: commands.Context):
        # All dead chat ping settings are prefixed with dc_rp_
        # Check whether the server is in the database or not
        with self.bot.db_session.begin() as c:
            check_setting(ctx.guild.id, c, 'dc_rp_enabled', '0')
            check_setting(ctx.guild.id, c, 'dc_rp_min_rank', '0')
            check_setting(ctx.guild.id, c, 'dc_rp_next_ping', '0')
            check_setting(ctx.guild.id, c, 'dc_rp_timer_duration', '0')
            check_setting(ctx.guild.id, c, 'dc_rp_role', '0')
            # Get the enabled status from the database
            enabled = int(get_setting(c, ctx.guild.id, 'dc_rp_enabled'))
            min_rank = int(get_setting(c, ctx.guild.id, 'dc_rp_min_rank'))
            timer_duration = int(get_setting(c, ctx.guild.id, 'dc_rp_timer_duration'))
            role = int(get_setting(c, ctx.guild.id, 'dc_rp_role'))

        # Create an embed to display the current settings
        embed = discord.Embed(title='Dead chat ping settings', color=0x00ff00)
        embed.add_field(name='Subcommands:', value="""$admin deadchat enable/disable - Enable or disable dead chat pings
        $admin deadchat timer <time> - Set the time between pings in minutes
        $admin deadchat setrole <role ID> - Set the role to ping
        $admin deadchat minrank <rank> - Set the minimum rank to use the /pingdead command""", inline=False)
        embed.add_field(name='Enabled:', value=f"""Enabled: {bool(enabled)}""", inline=False)
        embed.add_field(name='Minimum rank:', value=f"""{get_role_of_rank(ctx.guild, min_rank)}""", inline=False)
        embed.add_field(name='Timer duration:', value=f"""{timer_duration} minutes""", inline=False)
        embed.add_field(name='Role:', value=f"""{ctx.guild.get_role(role).mention}""", inline=False)
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar.url)
        await ctx.send(embed=embed)

    @deadchat.command(name='enable', aliases=['dc_enable'])
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def dc_enable(self, ctx: commands.Context):
        # Update the enabled status in the database
        with self.bot.db_session.begin() as c:
            set_setting(c, ctx.guild.id, 'dc_rp_enabled', '1')
        await ctx.send('Dead chat pings enabled')

    @deadchat.command(name='disable', aliases=['dc_disable'])
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def dc_disable(self, ctx: commands.Context):
        # Update the enabled status in the database
        with self.bot.db_session.begin() as c:
            set_setting(c, ctx.guild.id, 'dc_rp_enabled', '0')
        await ctx.send('Dead chat pings disabled')

    @deadchat.command(name='timer', aliases=['dc_timer'])
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def dc_timer(self, ctx: commands.Context, time: int):
        # Validate time, must be a positive integer
        if time < 0:
            await ctx.send('Invalid time')
            return
        # Update the timer duration in the database
        with self.bot.db_session.begin() as c:
            set_setting(c, ctx.guild.id, 'dc_rp_timer_duration', str(time))
        await ctx.send(f'Timer duration set to {time} minutes')

    @deadchat.command()
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def setrole(self, ctx: commands.Context, role: discord.Role):
        # Update the role ID in the database
        with self.bot.db_session.begin() as c:
            set_setting(c, ctx.guild.id, 'dc_rp_role', str(role.id))
        await ctx.send(f'Role set to {role.name}')

    @deadchat.command()
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def minrank(self, ctx: commands.Context, rank: int):
        # Validate rank, must be a positive integer
        if rank < 0:
            await ctx.send('Invalid rank')
            return
        # Update the minimum rank in the database
        with self.bot.db_session.begin() as c:
            set_setting(c, ctx.guild.id, 'dc_rp_min_rank', str(rank))
        await ctx.send(f'Minimum rank set to {get_role_of_rank(ctx.guild, rank)}')

    # Suggest admin command sub-group
    @admin.group(name='suggest', description='Suggest admin commands and settings', invoke_without_command=True)
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def suggest(self, ctx: commands.Context):
        # Suggest db table: (sg_enabled, sg_channel)
        # Check whether the server is in the database or not
        with self.bot.db_session.begin() as c:
            check_setting(ctx.guild.id, c, 'sg_enabled', '0')
            check_setting(ctx.guild.id, c, 'sg_channel', '0')
            # Get the channel ID and enabled status from the database
            enabled = int(get_setting(c, ctx.guild.id, 'sg_enabled'))
            channel = int(get_setting(c, ctx.guild.id, 'sg_channel'))

        # Create an embed to display the current settings
        embed = discord.Embed(title='Suggest Admin', description='Usage: $admin suggest <subcommand> <arguments>')

        embed.add_field(name='Subcommands:', value="""$admin suggest enable/disable - Enable or disable suggestions
        $admin suggest setchannel- Set the channel to send suggestions to""", inline=False)

        embed.add_field(name='Current Settings:', value=f"""Enabled: {bool(enabled)}
        Channel: {channel} ({ctx.guild.get_channel(channel).name if channel != 0 else ''})""", inline=False)

        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar.url)
        await ctx.send(embed=embed)

    @suggest.command(name='enable', aliases=['suggest_enable'])
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def suggest_enable(self, ctx: commands.Context):
        # Update the enabled status in the database
        with self.bot.db_session.begin() as c:
            set_setting(c, ctx.guild.id, 'sg_enabled', '1')
        await ctx.send('Suggestions enabled')

    @suggest.command(name='disable', aliases=['suggest_disable'])
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def suggest_disable(self, ctx: commands.Context):
        # Update the enabled status in the database
        with self.bot.db_session.begin() as c:
            set_setting(c, ctx.guild.id, 'sg_enabled', '0')
        await ctx.send('Suggestions disabled')

    @suggest.command()
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def setchannel(self, ctx: commands.Context):
        # Update the channel ID in the database to the current channel
        with self.bot.db_session.begin() as c:
            set_setting(c, ctx.guild.id, 'sg_channel', str(ctx.channel.id))
        await ctx.send(f'Suggestions channel set to {ctx.channel.name}')

    # Set event_id channel
    @suggest.command()
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def setevent(self, ctx: commands.Context):
        # Update the channel ID in the database to the current channel
        with self.bot.db_session.begin() as c:
            set_setting(c, ctx.guild.id, 'event_id', str(ctx.channel.id))
        await ctx.send(f'Event channel set to {ctx.channel.name}')

    # Group for the welcome message settings
    # Settings: wc_enabled, wc_channel
    @admin.group(name='welcome', description='Welcome message settings', invoke_without_command=True)
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def welcome(self, ctx: commands.Context):
        # Check whether the server is in the database or not
        with self.bot.db_session.begin() as c:
            if not check_setting(ctx.guild.id, c, 'wc_enabled', '0') and not check_setting(ctx.guild.id, c, 'wc_channel', '0'):
                ctx.send('Server add failed')
        
        # Get the channel ID and enabled status from the database
        enabled, channel = 0, 0
        with self.bot.db_session.begin() as c:
            enabled = int(get_setting(c, ctx.guild.id, 'wc_enabled'))
            channel = int(get_setting(c, ctx.guild.id, 'wc_channel'))
        # Create an embed to display the current settings
        embed = discord.Embed(title='Welcome Admin', description='Usage: $admin welcome <subcommand> <arguments>')

        embed.add_field(name='Subcommands:', value="""$admin welcome enable/disable - Enable or disable welcome messages
        $admin welcome setchannel - Set the channel to send welcome messages to""", inline=False)

        embed.add_field(name='Current Settings:', value=f"""Enabled: {bool(enabled)}
        Channel: {channel} ({ctx.guild.get_channel(channel).name if channel != 0 else ''})""", inline=False)

        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar.url)

        await ctx.send(embed=embed)

    @welcome.command()
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def enable(self, ctx: commands.Context):
        # Update the enabled status in the database
        with self.bot.db_session.begin() as c:
            set_setting(c, ctx.guild.id, 'wc_enabled', '1')
        await ctx.send('Welcome messages enabled')

    @welcome.command()
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def disable(self, ctx: commands.Context):
        # Update the enabled status in the database
        with self.bot.db_session.begin() as c:
            set_setting(c, ctx.guild.id, 'wc_enabled', '0')
        await ctx.send('Welcome messages disabled')

    @welcome.command()
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def setchannel(self, ctx: commands.Context):
        # Update the channel ID in the database to the current channel
        with self.bot.db_session.begin() as c:
            set_setting(c, ctx.guild.id, 'wc_channel', str(ctx.channel.id))
        await ctx.send(f'Welcome messages channel set to {ctx.channel.name}')

    # Purge a specific reaction a specific message to protect under 18s
    @admin.command()
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def purgereact(self, ctx: commands.Context, message_id: int, emoji: str):
        print(f"Purge react: {message_id}, {emoji}")
        # Make the emoji into a discord emoji object
        emoji = await commands.PartialEmojiConverter().convert(ctx, emoji)
        
        users = []
        count = 0

        # Get the message object
        message = await ctx.channel.fetch_message(message_id)

        # Get the list of users who reacted with the specified reaction
        for reaction in message.reactions:
            if reaction.emoji.id == emoji.id:
                print("Reaction found")
                users = reaction.users()
                break

        # Remove the reaction from each user
        async for user in users:
            # If the reactor is the sender of the message or a bot, skip
            if user == message.author or user.bot:
                continue
            await message.remove_reaction(emoji, user)
            count += 1
            # Sleep for 0.5 seconds to avoid rate limits
            await asyncio.sleep(0.5)

        await ctx.send(f'{count} reactions purged')

    # Add a moderator role setting per server
    @admin.command()
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def setmodrole(self, ctx: commands.Context, role: discord.Role):
        # Update the role ID in the database to the current role
        with self.bot.db_session.begin() as c:
            check_setting(ctx.guild.id, c, 'ad_mod_role', '0')
            set_setting(c, ctx.guild.id, 'ad_mod_role', str(role.id))
        await ctx.send(f'Moderator role set to {role.name}')

    # Add an admin role setting per server
    @admin.command()
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def setadminrole(self, ctx: commands.Context, role: discord.Role):
        # Update the role ID in the database to the current role
        with self.bot.db_session.begin() as c:
            check_setting(ctx.guild.id, c, 'ad_admin_role', '0')
            set_setting(c, ctx.guild.id, 'ad_admin_role', str(role.id))
        await ctx.send(f'Admin role set to {role.name}')

        

async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))