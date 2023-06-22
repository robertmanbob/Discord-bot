import discord
import re
from discord.ext import commands

class Puppet(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Sends a message as the bot.
    # This works by taking in a channel and then async looping until the sender
    # sends a message. The bot then sends the message in the channel.
    # Bot owner or manage server permissions required.
    @commands.command()
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def puppet(self, ctx, channel: discord.TextChannel):
        await ctx.send("Puppeting in channel: " + channel.mention)
        while True:
            msg = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author)

            # if no message content, continue
            if not msg.content:
                continue

            if msg.content == "exit":
                await ctx.send("Exiting puppet mode.")
                break

            # If an emoji is an animated emoji, it will be in the format :emoji_name:
            # This regex will find all instances of that and replace them with the actual emoji
            # This is done in case the user wants to send an animated emoji but doesn't have nitro
            # This will also work for normal emojis, but it's not necessary
            msg.content = re.sub(r':([a-zA-Z0-9_]+):', lambda m: str(discord.utils.get(self.bot.emojis, name=m.group(1))), msg.content)


            await channel.send(msg.content)

    # Edits a message as the bot.
    # Asks for a channel and message id to edit, then asks for a message to edit to
    # Bot owner or manage server permissions required.
    @commands.command()
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def edit(self, ctx, channel: discord.TextChannel, message_id: int):
        await ctx.send("Send a message to edit the message to. Type 'exit' to cancel.")
        msg = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author)

        if msg.content == "exit":
            await ctx.send("canceled edit.")
            return
        try:
            message = await channel.fetch_message(message_id)
            await message.edit(content=msg.content)
        except discord.NotFound:
            await ctx.send("Message not found.")
        except discord.Forbidden:
            await ctx.send("I don't have permission to edit or view that message")
        
    # Deletes a message as the bot.
    # Asks for a channel and message id to delete.
    # Bot owner or manage server permissions required.
    @commands.command()
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def delete(self, ctx, channel: discord.TextChannel, message_id: int):
        try:
            await channel.delete_message(message_id)
        except discord.NotFound:
            await ctx.send("Message not found.")
        except discord.Forbidden:
            await ctx.send("I don't have permission to delete that message.")

async def setup(bot):
    await bot.add_cog(Puppet(bot))