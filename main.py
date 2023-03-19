import configparser
import datetime
import typing
import discord
from discord.ext import commands

# List of cogs to load
cogs = ['cogs.roleping']

# Read the secret.ini file for bot token and owner ID
config = configparser.ConfigParser()
config.read('secret.ini')
token = config['DEFAULT']['token']
owner = config['DEFAULT']['owner']

class MyBot(commands.Bot):
    
    def __init__(self, *args, **kwargs):
        super().__init__(
            command_prefix='$',
            intents=discord.Intents.all())
        
    async def setup_hook(self):
        # Load cogs
        for cog in cogs:
            await self.load_extension(cog)
            print('Loaded {}'.format(cog))
        await bot.tree.sync()
    
    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')


bot = MyBot()

# Test ping command
@bot.tree.command(name='ping', description='Pong!')
async def ping(ctx):
    await ctx.response.send_message('Pong!', ephemeral=True)

# Manually reload a cog, owner only. Not a slash command.
@bot.command()
@commands.is_owner()
async def reload(ctx, cog: str):
    try:
        await bot.unload_extension(cog)
        await bot.load_extension(cog)
        await ctx.send('Reloaded {}'.format(cog))
    except Exception as e:
        await ctx.send('Failed to reload cog: {}'.format(e))

# Resync all slash commands, owner only. Not a slash command.
@bot.command()
@commands.is_owner()
async def resync(ctx):
    await bot.tree.sync()
    await ctx.send('Resynced slash commands')


bot.run(token)