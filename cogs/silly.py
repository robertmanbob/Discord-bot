import discord
import random
import asyncio
import codecs
import sqlalchemy
from sqlalchemy.orm import Session
from models import NameReply
from discord.ext import commands
from discord import app_commands
from utility import YesNoView, YesNoUserView

class Silly(commands.Cog):
    """Silly commands"""
    def __init__(self, bot):
        self.bot = bot

        # Import the namereply table into a dictionary
        self.namereply = {}
        with self.bot.db_session.begin() as session:
            for row in session.query(NameReply):
                self.namereply[row.user_name] = row.image_url

        # List of ongoing curses
        self.curses = set()

        # List of ongoing challenges
        self.challenges = set()

        # Losing streak dictionary, lists the number of losses in a row for each user by id
        self.streak = {}


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
        with self.bot.db_session.begin() as session:
            session.add(NameReply(user_name=name.lower(), image_url=url, server_id=ctx.guild.id))
        await ctx.send(f'Added name {name.lower()}')

    # Admin or bot owner only, not a slash command
    # Remove a name from the namereply dictionary and table
    @commands.command()
    @commands.check_any(commands.is_owner(), commands.has_permissions(manage_guild=True))
    async def removename(self, ctx: commands.Context, name: str):
        # Remove the name from the dictionary
        del self.namereply[name.lower()]
        # Remove the name from the database
        with self.bot.db_session.begin() as session:
            session.query(NameReply).filter(NameReply.user_name == name.lower()).delete()
            session.commit()
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
    # Slash command, moderator or owner only
    @app_commands.command(name='curse', description='Curse a user.')
    async def curse(self, ctx: discord.Interaction, user: discord.User, emoji: str, time: int):
        # Check if the user is the bot owner or has manage messages permission
        if ctx.user.id == self.bot.owner_id or ctx.channel.permissions_for(ctx.user).manage_messages:
            # If the target is already cursed, let them know
            if user.id in self.curses:
                await ctx.response.send_message(f'{user.mention} is already cursed!', ephemeral=True)
                return

            # 1 in 5 curses will curse the caller instead
            if random.randint(1, 5) == 1:
                user = ctx.user

            # If the time is greater than 600, set it to 600
            if time > 600:
                time = 600

            # If the curse is backfired, double the time
            if user.id == ctx.user.id:
                time *= 2

            # Send a message saying that the user has been cursed, adding a snippet if the curse backfired
            await ctx.response.send_message(f'{user.mention} has been cursed for {time} seconds!' + (' The gods are angry at their demands!' if user.id == ctx.user.id else ''))

            # Add the curse to the set of curses
            self.curses.add(user.id)
            
            # While the time is greater than 0, listen for messages from the user and react to them
            while time > 0:
                # If the curse is removed from the set, stop the loop
                if user.id not in self.curses:
                    break
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
            # (Try) to remove the curse from the set of curses
            try:
                self.curses.remove(user.id)
            except KeyError:
                # If the curse was already removed
                pass

        # If not, let them know
        else:
            await ctx.response.send_message('You don\'t have permission to use this command!', ephemeral=True)

    # Remove a curse from a user
    # Slash command, moderator or owner only
    @app_commands.command(name='uncurse', description='Remove a curse from a user early.')
    async def uncurse(self, ctx: discord.Interaction, user: discord.User):
        # If the target is the person invoking the command, reject it
        if user.id == ctx.user.id and ctx.user.id != self.bot.owner_id:
            await ctx.response.send_message('You are *far* too weak to uncurse yourself!', ephemeral=True)
            return
        # Check if the user is the bot owner or has manage messages permission
        if ctx.user.id == self.bot.owner_id or ctx.channel.permissions_for(ctx.user).manage_messages:
            # If the user is cursed, remove them from the set of curses. This will stop the curse loop.
            if user.id in self.curses:
                self.curses.remove(user.id)
                await ctx.response.send_message(f'{user.mention}\'s curse has been removed!', ephemeral=True)
            # If not, let them know
            else:
                await ctx.response.send_message(f'{user.mention} isn\'t cursed!', ephemeral=True)
        # If not, let them know
        else:
            await ctx.response.send_message('You don\'t have permission to use this command!', ephemeral=True)





async def setup(bot):
    await bot.add_cog(Silly(bot))

    