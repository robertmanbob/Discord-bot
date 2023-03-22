import discord
import sqlite3
from discord.ext import commands
from discord import app_commands

def role_rank(role: int) -> int:
    """Queries the database for the rank of a role, returns 0 if not found"""
    db = sqlite3.connect('database.db')
    c = db.cursor()
    c.execute('SELECT * FROM ranks WHERE role_id=?', (role,))
    result = c.fetchone()
    db.close()
    if result is None:
        return 0
    return result[2]
    
def role_at_least(role: int, requirement: int) -> bool:
    """Returns true if a role meets the requirement, false otherwise"""
    return role_rank(role) >= requirement

def user_is_at_least(user: discord.Member, requirement: int) -> bool:
    """Returns true if a user meets the requirement, false otherwise"""
    # Get the highest role of the user
    highest_role = max([role_rank(role.id) for role in user.roles])
    return highest_role >= requirement

def get_role_of_rank(guild: discord.Guild, rank: int) -> int:
    """Returns the role of a specified rank"""
    # If the rank is 0, return "0"
    if rank == 0:
        return 0
    db = sqlite3.connect('database.db')
    c = db.cursor()
    c.execute('SELECT * FROM ranks WHERE server_id=? AND rank=?', (guild.id, rank))
    result = c.fetchone()
    db.close()
    if result is None:
        raise ValueError('Role not found')
    return guild.get_role(result[1])