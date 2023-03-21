import discord
import time
import sqlite3
import os
import sys
from discord import app_commands
from discord.ext import commands
from utility import role_rank, role_at_least, user_is_at_least

# Database format
# server_id, role_id, rank

class UserCommands(commands.Cog):
    """This cog handles user commands, including rank and role commands"""
    def __init__(self) -> None:
        self.db = sqlite3.connect('database.db')
        self.c = self.db.cursor()
        self.db.commit()

    # This command will add a role to the database with the specified rank
    # Not a slash command because it's not meant to be used by users
    # Bot owner or server admin only
    @commands.command(name='addrole', description='Add a role to the database with the specified rank')
    @commands.check_any(commands.is_owner(), commands.has_guild_permissions(administrator=True))
    async def addrole(self, ctx: commands.Context, role: str, rank: int):
        # Make sure the role actually exists
        if ctx.guild.get_role(int(role)) is None:
            await ctx.send('Role not found')
            return
        # If the rank is already in the database, update it
        self.c.execute('SELECT * FROM ranks WHERE server_id=? AND rank=?', (ctx.guild.id, rank))
        if self.c.fetchone() is not None:
            self.c.execute('UPDATE ranks SET role_id=? WHERE server_id=? AND rank=?', (int(role), ctx.guild.id, rank))
        # If the rank is not in the database, add it
        else:
            self.c.execute('INSERT INTO ranks VALUES (?, ?, ?)', (ctx.guild.id, int(role), rank))
        self.db.commit()
        await ctx.send(f'Added role {ctx.guild.get_role(int(role))} with rank {rank}')

    # This command will remove a role from the database
    # Not a slash command because it's not meant to be used by users
    # Bot owner or server admin only
    @commands.command(name='removerole', description='Remove a role from the database')
    @commands.check_any(commands.is_owner(), commands.has_guild_permissions(administrator=True))
    async def removerole(self, ctx: commands.Context, role: str):
        # Make sure the role actually exists
        if ctx.guild.get_role(int(role)) is None:
            await ctx.send('Role not found')
            return
        self.c.execute('DELETE FROM ranks WHERE server_id=? AND role_id=?', (ctx.guild.id, int(role)))
        self.db.commit()
        await ctx.send(f'Removed role {ctx.guild.get_role(int(role)).name} from rank database')

    # This command will list all roles in the database
    # Not a slash command because it's not meant to be used by users
    # Bot owner or server admin only
    @commands.command(name='listranks', description='List all roles in the database')
    @commands.check_any(commands.is_owner(), commands.has_guild_permissions(administrator=True))
    async def listranks(self, ctx: commands.Context):
        self.c.execute('SELECT * FROM ranks')
        roles = self.c.fetchall()
        # Format the roles into a string, list the actual role name instead of the ID, and list the rank
        roles = '\n'.join([f'{ctx.guild.get_role(role[1]).name}: {role[2]}' for role in roles])
        await ctx.send(f'Roles:\n{roles}')

async def setup(bot: commands.Bot):
    await bot.add_cog(UserCommands())

