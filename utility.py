import discord
from discord.ext import commands
import configparser
import time
from discord import app_commands

rank = {
    "":1
}

def role_rank(role: int):
    """Returns the integer rank of a role from 1-9, higher is better"""
    if str(role) in rank:
        return rank[role]
    else:
        return 0
    
def role_at_least(role: int, requirement: int):
    """Returns true if a role meets the requirement, false otherwise"""
    return role_rank(role) >= requirement