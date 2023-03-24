import discord
import sqlite3
from discord.ext import commands
from discord import app_commands

# Suggest table format:
# server_id, enabled, channel_id

class Suggest(commands.Cog):
    """Suggest command cog, allows users to suggest things for the bot"""
    def __init__(self, bot: commands.Bot) -> None:
        self.db = sqlite3.connect('database.db')
        self.c = self.db.cursor()
        self.bot = bot

    # Slash command for suggesting things
    # This will relay the suggestion to a designated channel
    @app_commands.command(name='suggest', description='Suggest something for the bot!')
    async def suggest(self, ctx: discord.Interaction, *, suggestion: str) -> None:
        # Check if the suggestion is too long
        if len(suggestion) > 2000:
            await ctx.response.send_message('Suggestion too long! Please keep it under 2000 characters.', ephemeral=True)
            return

        # Check if suggestions are enabled, if so, get the suggestion channel
        self.c.execute('SELECT enabled, channel_id FROM suggest WHERE server_id = ?', (ctx.guild.id,))
        enabled, suggestion_channel = self.c.fetchone()

        # If suggestions are not enabled, don't send the suggestion
        if not enabled:
            await ctx.response.send_message('Suggestions are not enabled!', ephemeral=True)
            return

        # If the suggestion channel is not set, don't send the suggestion
        if suggestion_channel == 0:
            await ctx.response.send_message('Suggestion channel not set!', ephemeral=True)
            return

        # Get the suggestion channel
        suggestion_channel = self.bot.get_channel(suggestion_channel)

        # Create an embed for the suggestion
        embed = discord.Embed(title='Suggestion', description=suggestion, color=ctx.user.color)
        embed.set_author(name=ctx.user.name, icon_url=ctx.user.avatar.url)
        embed.set_footer(text=f'User ID: {ctx.user.id}')

        # Send the suggestion
        await suggestion_channel.send(embed=embed)

        # Send a confirmation message
        await ctx.response.send_message('Suggestion sent!', ephemeral=True)
    
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Suggest(bot))