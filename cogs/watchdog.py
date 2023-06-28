import discord
from discord.ext import commands
import logging
import asyncio
import time
import json # For stringifying the watchlist for storage in the database
import sqlalchemy
from sqlalchemy.orm import Session
from models import get_setting, set_setting, check_setting, ServerSettings

class Watchdog(commands.Cog):
    """This cog is used to monitor the server for specific events and take action on them"""
    def __init__(self, bot):
        self.bot = bot

        # List to watch for specific roles
        self.watchlist = []
        # Get the stringified watchlist from the database
        with self.bot.db_session.begin() as session:
            # We use 0 as the server ID for global settings
            check_setting(0, session, 'wd_watchlist', json.dumps([]))
            watchlist = get_setting(session, 0, 'wd_watchlist')
            # Convert the stringified watchlist to a list
            self.watchlist = json.loads(watchlist)
        self.bot.logger.info('Watchdog loaded')
        self.bot.logger.info('Watching roles:')
        for role in self.watchlist:
            self.bot.logger.info(f'{role}')

    # Setup commands
    @commands.group(name='watchdog', invoke_without_command=True)
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def watchdog(self, ctx):
        """The base command for the watchdog"""
        enabled, snitch_channel = None, None
        with self.bot.db_session.begin() as session:
            # Check if watchdog is enabled
            check_setting(ctx.guild.id, session, 'wd_enabled', "0")
            enabled = get_setting(session, ctx.guild.id, 'wd_enabled')
            # Check if the watchdog snitch channel is set
            check_setting(ctx.guild.id, session, 'wd_snitch_channel', "0")
            snitch_channel = get_setting(session, ctx.guild.id, 'wd_snitch_channel')
        help_response = f'```Watchdog is currently {"enabled" if enabled == "1" else "disabled"}'
        help_response += f'\nSnitch channel: {self.bot.get_channel(int(snitch_channel)).name if snitch_channel != "0" else "Not set"}'
        help_response += '\n\nWatchlist:'
        for role in self.watchlist:
            help_response += f'\n{role}'
        help_response += '```'
        await ctx.send(help_response)

    @watchdog.command(name='enable')
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def watchdog_enable(self, ctx):
        """Enable the watchdog"""
        with self.bot.db_session.begin() as session:
            set_setting(session, ctx.guild.id, 'wd_enabled', "1")
        await ctx.send('Watchdog enabled')

    @watchdog.command(name='disable')
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def watchdog_disable(self, ctx):
        """Disable the watchdog"""
        with self.bot.db_session.begin() as session:
            set_setting(session, ctx.guild.id, 'wd_enabled', "0")
        await ctx.send('Watchdog disabled')

    @watchdog.command(name='setchannel')
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def watchdog_setchannel(self, ctx, channel: discord.TextChannel):
        """Set the watchdog snitch channel"""
        with self.bot.db_session.begin() as session:
            set_setting(session, ctx.guild.id, 'wd_snitch_channel', str(channel.id))
        await ctx.send(f'Watchdog snitch channel set to {channel.mention}')

    @watchdog.command(name='add')
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def watchdog_add(self, ctx, role: discord.Role):
        """Add a role to the watchlist"""
        # Add the role to the watchlist
        self.watchlist.append(role.id)
        # Update the watchlist in the database
        with self.bot.db_session.begin() as session:
            set_setting(session, 0, 'wd_watchlist', json.dumps(self.watchlist))
        await ctx.send(f'Role added to watchlist: {role.mention}')

    @watchdog.command(name='remove')
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def watchdog_remove(self, ctx, role: discord.Role):
        """Remove a role from the watchlist"""
        # Remove the role from the watchlist
        self.watchlist.remove(role.id)
        # Update the watchlist in the database
        with self.bot.db_session.begin() as session:
            set_setting(session, 0, 'wd_watchlist', json.dumps(self.watchlist))
        await ctx.send(f'Role removed from watchlist: {role.mention}')

    # Events
    @commands.Cog.listener()
    async def on_member_update(self, before, after: discord.Member):
        """Watch for role changes"""
        enabled = None
        # Check if the watchdog is enabled
        with self.bot.db_session.begin() as session:
            check_setting(after.guild.id, session, 'wd_enabled', "0")
            enabled = get_setting(session, after.guild.id, 'wd_enabled')
        if enabled == "1":
            # Check if the member has a role change
            if before.roles != after.roles:
                # Check if the member has a role that is being watched
                for role in after.roles:
                    if role.id in self.watchlist:
                        snitch_channel = None
                        mod_role = None
                        admin_role = None
                        # Get the snitch channel
                        with self.bot.db_session.begin() as session:
                            check_setting(after.guild.id, session, 'wd_snitch_channel', "0")
                            check_setting(after.guild.id, session, 'ad_mod_role', "0")
                            check_setting(after.guild.id, session, 'ad_admin_role', "0")
                            snitch_channel = get_setting(session, after.guild.id, 'wd_snitch_channel')
                            mod_role = get_setting(session, after.guild.id, 'ad_mod_role')
                            admin_role = get_setting(session, after.guild.id, 'ad_admin_role')
                            # Convert mod_role to a role object
                            mod_role = discord.utils.get(after.guild.roles, id=int(mod_role))
                            # Convert admin_role to a role object
                            admin_role = discord.utils.get(after.guild.roles, id=int(admin_role))
                            if snitch_channel == "0":
                                return
                        # Create the embed, pinging the mod role in the description if it exists
                        embed = discord.Embed(title='Role Watch', description=f'Watched role added by {after.name}', color=0xff0000)
                        embed.add_field(name="Role", value=role.mention)
                        embed.add_field(name="Time", value=f"<t:{round(time.time())}:t>")
                        embed.add_field(name="User", value=after.mention)
                        embed.add_field(name="User ID (long press on mobile to copy easily)", value=after.id, inline=False)
                        embed.set_thumbnail(url=after.display_avatar.url if after.display_avatar else "https://cdn.discordapp.com/embed/avatars/0.png")
                        # Send the embed, pinging the mod role in the message if it exists
                        if mod_role is not None and admin_role is not None:
                            await self.bot.get_channel(int(snitch_channel)).send(f'{mod_role.mention} {admin_role.mention}', embed=embed)
                        else:
                            await self.bot.get_channel(int(snitch_channel)).send(embed=embed)




async def setup(bot: commands.Bot):
    await bot.add_cog(Watchdog(bot))