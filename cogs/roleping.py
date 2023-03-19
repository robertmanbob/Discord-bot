import discord
from discord import app_commands
from discord.ext import commands

class RolePings(commands.Cog):
    """Adds commands to ping roles"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name='pingrole', description='Ping a role by name')
    async def pingrole(self, ctx: discord.Interaction, role_name: str):
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role is None:
            await ctx.send('Role not found')
            return
        await ctx.response.send_message('Pinging role {}'.format(role.mention), allowed_mentions=discord.AllowedMentions(roles=True))

    @app_commands.command(name='listroles', description='List all roles and their IDs in the server')
    async def listroles(self, ctx: discord.Interaction):
        roles = ctx.guild.roles
        role_string = ''
        for role in roles:
            role_string += '{}: {}\n'.format(role.name, role.id)
        await ctx.response.send_message(role_string, ephemeral=True)

async def setup(bot):
    await bot.add_cog(RolePings(bot))