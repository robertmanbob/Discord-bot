import os
import sys
import configparser
import datetime
import typing
import discord
import git
import sqlalchemy
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
import asyncio
from discord.ext import commands

# Logger
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)

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
            intents=discord.Intents.all(),
            owner_id=168392772506746880)
        self.db_engine = create_engine('sqlite:///db/alchemy.db')
        self.db_session = sessionmaker(bind=self.db_engine)
        self.logger = logger
        
    async def setup_hook(self):
        # Load cogs
        for cog in cogs:
            try:
                await self.load_extension(cog)
                print(f'Loaded {cog}')
            except Exception as e:
                print(f'Failed to load extension {cog}\n{type(e).__name__}: {e}')
        await bot.tree.sync()
    
    async def on_ready(self):
        self.remove_command('help')
        self.logger.info(f'Logged in as {self.user.name} ({self.user.id})')
        self.logger.info(f'Using discord.py version {discord.__version__}')
        self.logger.info(f'Using Python version {sys.version}')
        self.logger.info(f'Using SQLAlchemy version {sqlalchemy.__version__}')

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send('You do not have permission to use this command')
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f'Missing required argument: {error.param.name}')
        elif isinstance(error, commands.CommandNotFound):
            print(f'Command not found: {ctx.message.content}')
        elif isinstance(error, commands.CheckFailure):
            await ctx.send('You do not have permission to use this command')
        else:
            await ctx.send(f'Error: {error}')


bot = MyBot()

# Restart the bot, bot owner only. Not a slash command.
@bot.command()
@commands.is_owner()
async def restart(ctx: commands.Context):
    # Verify that the bot should restart
    await ctx.send('Are you sure you want to restart?')
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
    try:
        msg = await bot.wait_for('message', check=check, timeout=30)
    except asyncio.TimeoutError:
        await ctx.send('Restart cancelled')
        return
    if msg.content.lower() != 'yes':
        await ctx.send('Restart cancelled')
        return
    await ctx.send('Restarting...')
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
        await ctx.send(f'Reloaded {cog}')
    except Exception as e:
        await ctx.send(f'Failed to reload cog: {e}')

# Reload all cogs, bot owner only. Not a slash command.
@bot.command()
@commands.is_owner()
async def reloadall(ctx):
    for cog in cogs:
        try:
            await bot.unload_extension(cog)
            await bot.load_extension(cog)
            await ctx.send(f'Reloaded {cog}')
        except Exception as e:
            await ctx.send(f'Failed to reload cog: {e}')

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
        
        await ctx.send(f'Added {cog}')
    except Exception as e:
        await ctx.send(f'Failed to add cog: {e}')

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
        
        await ctx.send(f'Removed {cog}')
    except Exception as e:
        await ctx.send(f'Failed to remove cog: {e}')

# Panic command, bot owner or server admins. Not a slash command.
# This will log the time, date, and optional message of the panic in a file, and then exit the bot.
@bot.command()
@commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
async def panic(ctx, *, message: typing.Optional[str] = None):
    with open('panic.txt', 'a') as f:
        f.write(f'Panic at {datetime.datetime.now()}:\n{message}\n')
    await ctx.send('Panic logged, exiting')
    await bot.close()

# Self-update git command, bot owner only. Not a slash command.
@bot.command()
@commands.is_owner()
async def update(ctx):
    repo = git.Repo()
    repo.remotes.origin.pull()
    print(f'Updated to commit {repo.head.object.hexsha}')
    # Print that we updated the repo and the current commit
    await ctx.send(f'Updated to commit {repo.head.object.hexsha}, commit message: {repo.head.object.message}')

# Connect to the SQLAlchemy db, run a query, and return the result
# Owner only, not a slash command
@bot.command()
@commands.is_owner()
async def query(ctx: commands.Context, *, query: str):
    # Get the engine from the bot, type hint it as an engine
    engine: sqlalchemy.engine.Engine = ctx.bot.db_engine
    query = text(query)
    with engine.connect() as conn:
        results = conn.execute(query)
        output = ''
        for row in results:
            output += str(row) + '\n'
        await ctx.send(f'```{output}```')
        

# Disable a command, bot owner only. Not a slash command.
@bot.command()
@commands.is_owner()
async def disable(ctx, command: str):
    # You can't disable the disable command
    if command == 'disable':
        await ctx.send('You can\'t disable the disable command')
        return
    # Remove_command returns None if the command doesn't exist
    if bot.remove_command(command) is None:
        await ctx.send(f'Command {command} not found')
    else:
        await ctx.send(f'Disabled {command}')
    

bot.run(token)
