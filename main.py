import configparser
import datetime
import typing
import discord
from discord.ext import commands
from cogs import roleping


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
        await bot.load_extension('cogs.roleping')
        print('Loaded roleping extension')
        await bot.tree.sync()
    
    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')


bot = MyBot()

@bot.tree.command(name='ping', description='Pong!')
async def ping(ctx):
    await ctx.response.send_message('Pong!', ephemeral=True)

bot.run(token)