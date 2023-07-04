import discord
import asyncio
import random
from discord.ext import commands
from utility import user_is_at_least

class Curse(commands.Cog):
    """Commands for cursing people, which reacts to every message they send."""
    def __init__(self, bot):
        self.bot = bot
        self.curses = set() # People who are cursed. This is a set of user IDs.
        self.cursers = set() # People who have already cursed someone today. This is reset every day at 12:00 AM UTC.

    # Curse slash command
    @commands.slash_command(name='curse', description='Curse a user, causing their messages to be plagued with a cursed emoji.')
    async def curse(self, ctx: discord.Interaction, user: discord.Member):
        # Check if the user is the bot owner or of sufficient rank
        if ctx.user.id == self.bot.owner_id or user_is_at_least(ctx.user, 3):
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