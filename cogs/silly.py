import discord
import sqlite3
import random
import asyncio
import codecs
from discord.ext import commands
from discord import app_commands
from utility import YesNoView

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
            # await ctx.send(embed=discord.Embed().set_image(url='https://static.miraheze.org/greatcharacterswiki/thumb/0/08/1481909501350.png/290px-1481909501350.png'))
            await ctx.send(embed=discord.Embed().set_image(url='https://static.wikia.nocookie.net/howtotrainyourdragon/images/7/78/Character_Hiccup_02.png/revision/latest?cb=20180702130930'))

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
        await ctx.send(f'Added name {name.lower()}')

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
        await ctx.send(f'Removed name {name.lower()}')

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

    # # Anyone can use this command
    # # Nickname game. First reply to the message wins and sets the nickname of the author
    # # to the content of the message
    # # Slash command
    @app_commands.command(name='nickgame', description='Start a nickname game, the first person to reply gets to set YOUR nickname!')
    async def nickgame(self, ctx: discord.Interaction):
        # Ask if the user is sure they want to start a nickname game. Yes or no buttons
        view = YesNoView(ctx)
        await ctx.response.send_message('Are you sure you want to start a nickname game? This will send a message that allows the first person to respond to set YOUR nickname!', view=view, ephemeral=True)
        
        # Wait for a response
        no_response = await view.wait()
        
        # If the user said no or has not responded, return
        if no_response or not view.value:
            return
        
        # If the user said yes, let them know and start the game
        game = await ctx.channel.send(f'{ctx.user.mention} has started a nickname game! The first person to reply to this message gets to set their nickname!')
        
        # Wait for a reply
        try:
            # Message must be in the same channel, not from the game target, and must be a reply to the game message
            reply = await self.bot.wait_for('message', check=lambda m: m.channel == ctx.channel and m.reference.message_id == game.id and m.author.id != ctx.user.id, timeout=15)
        except asyncio.TimeoutError:
            # If a user didn't reply in time, let them know
            await ctx.channel.send('No one replied in time, so I\'m not going to set your nickname.')
            return
        
        # If the user replied, try to set their nickname to the content of the message
        try:
            await ctx.user.edit(nick=reply.content)
            await ctx.channel.send(f'{ctx.user.mention}\'s nickname has been set to {reply.content}!')
        except discord.Forbidden:
            # If the bot doesn't have permission to change the nickname, let them know
            await ctx.channel.send(f'I don\'t have permission to change {ctx.user.mention}\'s nickname, so we\'re going to get with the honor system and pretend I did. Their nickname is now {reply.content}!')

    # Bot owner or specified person, not a slash command
    # Sends a lemon man image
    @commands.command()
    async def nona(self, ctx: commands.Context):
        if ctx.author.id == ctx.bot.owner_id or ctx.author.id == 686724506164658221:
            await ctx.send(embed=discord.Embed().set_image(url='https://i.imgur.com/ycbiaBS.png'))

    # Bot owner, slash command
    @app_commands.command(name='asay', description='Make the bot say something. Requires perms.')
    async def asay(self, ctx: discord.Interaction, *, text: str):
        # Check if the user is the bot owner
        if ctx.user.id == self.bot.owner_id:
            await ctx.response.send_message('Sending...', ephemeral=True)
            await ctx.channel.send(text)
        # If not, let them know
        else:
            await ctx.response.send_message('You don\'t have permission to use this command!', ephemeral=True)

    # Secret command. Guess the cryptology with your own input, win a prize
    @commands.command()
    async def secret(self, ctx: commands.Context, *, text: str = None):
        # If you're from the server and you're reading this, don't cheat :(

        def rot_alpha(n):
            from string import ascii_lowercase as lc, ascii_uppercase as uc
            lookup = str.maketrans(lc + uc, lc[n:] + lc[:n] + uc[n:] + uc[:n])
            return lambda s: s.translate(lookup)

        # Display an instruction message
        if not text:
            await ctx.send("You've found a secret!" +
                           " Input some text and try to figure out what it's doing!" +
                           "\nIf you get it right, you'll get a prize by DMing Robbit the answer!")
            return
        
        # If the input is "hint", give a hint
        if text == 'hint':
            await ctx.send('The input is being partially reversed,' +
                            'and then encoded with random variation of a common cipher.')
            return

        # Strip all non-alphabetical characters from the input
        text = ''.join([char for char in text if char.isalpha() or char == ' '])

        # Make it all lowercase
        text = text.lower()

        # Split the input into a list of words
        text = text.split()   

        # reverse every other word in the input
        for i in range(len(text)):
            if i % 2 == 0:
                text[i] = text[i][::-1]

        # Join the input back into a string
        text = ' '.join(text)

        # Choose a random rot cipher from 2 to 13, encode the input with it
        rot = random.randint(2, 13)
        text = rot_alpha(rot)(text)

        # Return the result
        await ctx.send(text)

    # Reply with bot permissions, owner only
    # Slash command
    @app_commands.command(name='perms', description='Get the bot\'s permissions in this channel.')
    async def perms(self, ctx: discord.Interaction):
        # Check if the user is the bot owner
        if ctx.user.id == self.bot.owner_id:
            # Get the bot's permissions in the channel
            perms = ctx.channel.permissions_for(ctx.guild.me)
            # For each permission, if it's True, add it to the output
            output = ''
            for perm in perms:
                if perm[1]:
                    output += f'{perm[0]}\n'
            # Send a message with the permissions
            await ctx.response.send_message(f'```{output}```', ephemeral=True)
        # If not, let them know
        else:
            await ctx.response.send_message('You don\'t have permission to use this command!', ephemeral=True)

    # Curse the designated user, reacting to their messages with a specific emoji for a designated amount of time
    # Slash command, owner only
    @app_commands.command(name='curse', description='Curse a user.')
    async def curse(self, ctx: discord.Interaction, user: discord.User, emoji: str, time: int):
        # Check if the user is the bot owner
        if ctx.user.id == self.bot.owner_id:
            # Send a message saying that the user has been cursed
            await ctx.response.send_message(f'{user.mention} has been cursed for {time} seconds!')
            
            # While the time is greater than 0, listen for messages from the user and react to them
            while time > 0:
                try:
                    # Wait for a message from the user
                    message = await self.bot.wait_for('message', check=lambda m: m.author.id == user.id, timeout=1)
                except asyncio.TimeoutError:
                    # If the user didn't send a message in time, subtract 1 from the time
                    time -= 1
                else:
                    # If the user did send a message, react to it
                    await message.add_reaction(emoji)

            # Send a message saying that the curse has been lifted
            await ctx.channel.send(f'{user.mention}\'s curse has been lifted!')
        # If not, let them know
        else:
            await ctx.response.send_message('You don\'t have permission to use this command!', ephemeral=True)
    

async def setup(bot):
    await bot.add_cog(Silly(bot))

    