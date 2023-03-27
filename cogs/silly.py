import discord
import sqlite3
from discord.ext import commands

class Silly(commands.Cog):
    """Silly commands"""
    def __init__(self, bot):
        self.bot = bot
        self.db = sqlite3.connect('database.db')
        self.c = self.db.cursor()

        # Import the namereply table into a dictionary
        # namereply schema: (user_name, reply_url)
        self.namereply = {}
        for row in self.c.execute('SELECT * FROM namereply'):
            self.namereply[row[0]] = row[1]


    # Owner only, not a slash command
    @commands.command()
    async def chance(self, ctx: commands.Context):
        """Reveals the true form of Chance"""
        # Send a specific image via an embed
        # This is a joke command, so it's not very useful
        # Check if the sender is the owner of the bot or the person with this ID 363872734532468754
        if ctx.author.id == ctx.bot.owner_id or ctx.author.id == 363872734532468754:
            await ctx.send(embed=discord.Embed().set_image(url='https://static.miraheze.org/greatcharacterswiki/thumb/0/08/1481909501350.png/290px-1481909501350.png'))

    # Listener for on_message, handling name invoking
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignore messages from bots
        if message.author.bot:
            return

        # Check if the entirety of the message is a name in the namereply dictionary
        if message.content.lower() in self.namereply:
            # Send the reply url via an embed
            await message.channel.send(embed=discord.Embed().set_image(url=self.namereply[message.content.lower()]))

    # Admin or bot owner only, not a slash command
    # Add a name to the namereply dictionary and table
    @commands.command()
    @commands.check_any(commands.is_owner(), commands.has_permissions(manage_guild=True))
    async def addname(self, ctx: commands.Context, name: str, url: str):
        # Add the name and url to the dictionary
        self.namereply[name.lower()] = url
        # Add the name and url to the database
        self.c.execute('INSERT INTO namereply VALUES (?, ?)', (name.lower(), url))
        self.db.commit()
        await ctx.send('Added name {}'.format(name.lower()))

    # Admin or bot owner only, not a slash command
    # Remove a name from the namereply dictionary and table
    @commands.command()
    @commands.check_any(commands.is_owner(), commands.has_permissions(manage_guild=True))
    async def removename(self, ctx: commands.Context, name: str):
        # Remove the name from the dictionary
        del self.namereply[name.lower()]
        # Remove the name from the database
        self.c.execute('DELETE FROM namereply WHERE user_name = ?', (name.lower(),))
        self.db.commit()
        await ctx.send('Removed name {}'.format(name.lower()))
        

async def setup(bot):
    await bot.add_cog(Silly(bot))

    