import sqlalchemy
from sqlalchemy.orm import Session
from models import ServerSettings, Rank, get_setting, set_setting, check_setting
from discord.ext import commands



class UserCommands(commands.Cog):
    """This cog handles user commands, including rank and role commands"""
    def __init__(self, bot) -> None:
        self.bot = bot

    # This command will add a role to the database with the specified rank
    # Not a slash command because it's not meant to be used by users
    # Bot owner or server admin only
    @commands.command(name='addrole', description='Add a role to the database with the specified rank')
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def addrole(self, ctx: commands.Context, role: str, rank: int):
        # Make sure the role actually exists
        if ctx.guild.get_role(int(role)) is None:
            await ctx.send('Role not found')
            return
        # If the rank is already in the database, update it
        # self.c.execute('SELECT * FROM ranks WHERE server_id=? AND rank=?', (ctx.guild.id, rank))
        # if self.c.fetchone() is not None:
        #     self.c.execute('UPDATE ranks SET role_id=? WHERE server_id=? AND rank=?', (int(role), ctx.guild.id, rank))
        with self.bot.db_session.begin() as c:
            if c.query(Rank).filter_by(server_id=ctx.guild.id, rank=rank).first() is not None:
                c.query(Rank).filter_by(server_id=ctx.guild.id, rank=rank).update({'role_id': int(role)})
            else:
                c.add(Rank(server_id=ctx.guild.id, role_id=int(role), rank=rank))
        await ctx.send(f'Added role {ctx.guild.get_role(int(role))} with rank {rank}')

    # This command will remove a role from the database
    # Not a slash command because it's not meant to be used by users
    # Bot owner or server admin only
    @commands.command(name='removerole', description='Remove a role from the database')
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def removerole(self, ctx: commands.Context, role: str):
        # Make sure the role actually exists
        if ctx.guild.get_role(int(role)) is None:
            await ctx.send('Role not found')
            return
        try:
            with self.bot.db_session.begin() as c:
                c.query(Rank).filter_by(server_id=ctx.guild.id, role_id=int(role)).delete()
        except sqlalchemy.orm.exc.NoResultFound:
            await ctx.send('Role not found')
            return
        await ctx.send(f'Removed role {ctx.guild.get_role(int(role)).name} from rank database')

    # This command will list all roles in the database
    # Not a slash command because it's not meant to be used by users
    # Bot owner or server admin only
    @commands.command(name='listranks', description='List all roles in the database')
    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    async def listranks(self, ctx: commands.Context):
        # self.c.execute('SELECT * FROM ranks WHERE server_id=?', (ctx.guild.id, ))
        # roles = self.c.fetchall()
        with self.bot.db_session.begin() as c:
            roles = c.query(Rank).filter_by(server_id=ctx.guild.id).all()
        # If no roles are found, state that
        if len(roles) == 0:
            await ctx.send('No roles found')
            return
        # Format the roles into a string, list the actual role name instead of the ID, and list the rank
        # roles = '\n'.join([f'{ctx.guild.get_role(role[1]).name}: {role[2]}' for role in roles])
        roles = '\n'.join([f'{ctx.guild.get_role(role.role_id).name}: {role.rank}' for role in roles])
        await ctx.send(f'Roles:\n{roles}')

async def setup(bot: commands.Bot):
    await bot.add_cog(UserCommands(bot))

