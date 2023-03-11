# configparser for reading config.ini, which contains the bot token
import configparser
# import everything from discord.py
import discord

# Read the secret.ini file
config = configparser.ConfigParser()
config.read('secret.ini')

# Get the bot token from the config.ini file
token = config['DEFAULT']['token']


intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

client.run(token)