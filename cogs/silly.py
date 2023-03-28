import discord
import sqlite3
import random
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

    # Bot owner only, not a slash command
    # Zalgo text generator
    @commands.command()
    @commands.is_owner()
    async def zalgo(self, ctx: commands.Context, *, text: str):
        """Zalgo text generator"""
        # Define the zalgo characters
        zalgo_over = [
            '\u0300', '\u0301', '\u0302', '\u0303', '\u0304',
            '\u0305', '\u0306', '\u0307', '\u0308', '\u0309',
            '\u030a', '\u030b', '\u030c', '\u030d', '\u030e',
            '\u030f', '\u0310', '\u0311', '\u0312', '\u0313',
            '\u0314', '\u0315', '\u031a', '\u031b', '\u033c',
            '\u033e', '\u033f', '\u0340', '\u0341', '\u0342',
            '\u0343', '\u0344', '\u034a', '\u0346', '\u034b',
            '\u034c', '\u0350', '\u0351', '\u0352', '\u0357',
            '\u0358', '\u035b', '\u0360', '\u035d', '\u035e',
            '\u0361'
        ]
        zalgo_under = [
            '\u0316', '\u0317', '\u0318', '\u0319', '\u031c',
            '\u031d', '\u031e', '\u031f', '\u0320', '\u0321',
            '\u0322', '\u0323', '\u0324', '\u0325', '\u0326',
            '\u0327', '\u0328', '\u0329', '\u032a', '\u032b',
            '\u032c', '\u032d', '\u032e', '\u032f', '\u0330',
            '\u0331', '\u0332', '\u0333', '\u0339', '\u033a',
            '\u033b', '\u033c', '\u0345', '\u0347', '\u0348',
            '\u0349', '\u034d', '\u034e', '\u0353', '\u0354',
            '\u0355', '\u0356', '\u0359', '\u035a', '\u035c',
            '\u035f', '\u0362'
        ]
        output = ''
        # Add zalgo characters to the text
        for char in text:
            output += char
            for i in range(random.randint(0, 4)):
                output += random.choice(zalgo_over)
            for i in range(random.randint(0, 4)):
                output += random.choice(zalgo_under)
        
        # Try to delete the original message and send the zalgo text
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        await ctx.send(output)
        

async def setup(bot):
    await bot.add_cog(Silly(bot))

    