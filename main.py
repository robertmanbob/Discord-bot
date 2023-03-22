import os
import sys
import configparser
import datetime
import typing
import discord
import git
import sqlite3 # Crying emoji here
from discord.ext import commands

# Read the secret.ini file for bot token and config.ini for enabled cogs
secret = configparser.ConfigParser()
secret.read('secret.ini')
token = secret['DEFAULT']['token']
config = configparser.ConfigParser()
config.read('config.ini')
cogs = config['DEFAULT']['cogs'].split(',')

class MyBot(commands.Bot):
    
    def __init__(self, *args, **kwargs):
        super().__init__(
            command_prefix='$',
            intents=discord.Intents.all())
        
    async def setup_hook(self):
        # Load cogs
        for cog in cogs:
            try:
                await self.load_extension(cog)
                print('Loaded {}'.format(cog))
            except Exception as e:
                print('Failed to load extension {}\n{}: {}'.format(cog, type(e).__name__, e))
        await bot.tree.sync()
    
    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send('You do not have permission to use this command')
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Missing required argument: {}'.format(error.param.name))
        elif isinstance(error, commands.CommandNotFound):
            print('Command not found: {}'.format(ctx.message.content))
        elif isinstance(error, commands.CheckFailure):
            await ctx.send('You do not have permission to use this command')
        else:
            await ctx.send('Error: {}'.format(error))


bot = MyBot()

# Check if the user is a bot owner or has manage server permission
def is_owner_or_admin():
    async def predicate(ctx: commands.Context):
        return ctx.author.id == ctx.bot.owner_id or ctx.author.guild_permissions.manage_guild
    return commands.check(predicate)

# Test the above decorator
@bot.command()
@commands.check(is_owner_or_admin())
async def test(ctx):
    await ctx.send('Success')

# Restart the bot, bot owner only. Not a slash command. Make sure the bot is running in a screen or tmux session.
@bot.command()
@commands.is_owner()
async def restart(ctx):
    await ctx.send('Restarting...')
    await bot.close()
    os.execl(sys.executable, sys.executable, *sys.argv)


# Test ping command
@bot.tree.command(name='ping', description='Pong!')
async def ping(ctx):
    await ctx.response.send_message('Pong!', ephemeral=True)

# Manually reload a cog, bot owner only. Not a slash command.
@bot.command()
@commands.is_owner()
async def reload(ctx, cog: str):
    try:
        await bot.unload_extension(cog)
        await bot.load_extension(cog)
        await ctx.send('Reloaded {}'.format(cog))
    except Exception as e:
        await ctx.send('Failed to reload cog: {}'.format(e))

# Reload all cogs, bot owner only. Not a slash command.
@bot.command()
@commands.is_owner()
async def reloadall(ctx):
    for cog in cogs:
        try:
            await bot.unload_extension(cog)
            await bot.load_extension(cog)
            await ctx.send('Reloaded {}'.format(cog))
        except Exception as e:
            await ctx.send('Failed to reload cog: {}'.format(e))

# Resync all slash commands, bot owner only. Not a slash command.
@bot.command()
@commands.is_owner()
async def resync(ctx):
    await bot.tree.sync()
    await ctx.send('Resynced slash commands')

# Add a cog, bot owner only. Not a slash command.
@bot.command()
@commands.is_owner()
async def add(ctx, cog: str):
    try:
        await bot.load_extension(cog)

        # Add the cog to the config file, comma separated
        config['DEFAULT']['cogs'] = ','.join([config['DEFAULT']['cogs'], cog])
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        
        await ctx.send('Added {}'.format(cog))
    except Exception as e:
        await ctx.send('Failed to add cog: {}'.format(e))

# Remove a cog, bot owner only. Not a slash command.
@bot.command()
@commands.is_owner()
async def remove(ctx, cog: str):
    try:
        await bot.unload_extension(cog)

        # Remove the cog from the config file
        cogs = config['DEFAULT']['cogs'].split(',')
        cogs.remove(cog)
        config['DEFAULT']['cogs'] = ','.join(cogs)
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        
        await ctx.send('Removed {}'.format(cog))
    except Exception as e:
        await ctx.send('Failed to remove cog: {}'.format(e))

# Panic command, bot owner or server admins. Not a slash command.
# This will log the time, date, and optional message of the panic in a file, and then exit the bot.
@bot.command()
@commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
async def panic(ctx, *, message: typing.Optional[str] = None):
    with open('panic.txt', 'a') as f:
        f.write('Panic at {}:\n{}\n'.format(datetime.datetime.now(), message))
    await ctx.send('Panic logged, exiting')
    await bot.close()

# Self-update git command, bot owner only. Not a slash command.
@bot.command()
@commands.is_owner()
async def update(ctx):
    repo = git.Repo()
    repo.remotes.origin.pull()
    print('Updated to commit {}'.format(repo.head.object.hexsha))
    # Print that we updated the repo and the current commit
    await ctx.send('Updated to commit {}'.format(repo.head.object.hexsha))

# Connect to the desired database, run a query, and return the result
# Owner only, not a slash command
@bot.command()
@commands.is_owner()
async def query(ctx: discord.Interaction, *, query: str):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute(query)
    result = c.fetchall()
    conn.close()
    await ctx.send('Result: {}'.format(result))
    

bot.run(token)
