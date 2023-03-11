import configparser
import sqlite3
import discord
import datetime
from updatedb import update_db


# Read the secret.ini file for bot token
config = configparser.ConfigParser()
config.read('secret.ini')
token = config['DEFAULT']['token']
config.read('config.ini')
db_file = config['DEFAULT']['db_file']
schema_file = config['DEFAULT']['schema_file']

# Update the database
update_db(db_file, schema_file)

# Our intents are the things we want to listen for from the Discord API
intents = discord.Intents.default()
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