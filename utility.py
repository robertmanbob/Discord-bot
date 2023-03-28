import discord
import sqlite3
import requests
from PIL import Image, ImageFont, ImageDraw

# Yes or No view + buttons
class YesNoView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.value = None

    @discord.ui.button(label='Yes', style=discord.ButtonStyle.green)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        # disable the buttons
        self.clear_items()
        await interaction.response.edit_message(view=self)
        self.stop()

    @discord.ui.button(label='No', style=discord.ButtonStyle.red)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        # disable the buttons
        self.clear_items()
        await interaction.response.edit_message(view=self)
        self.stop()

def role_rank(role: int) -> int:
    """Queries the database for the rank of a role, returns 0 if not found"""
    db = sqlite3.connect('database.db')
    c = db.cursor()
    c.execute('SELECT * FROM ranks WHERE role_id=?', (role,))
    result = c.fetchone()
    db.close()
    if result is None:
        return 0
    return result[2]
    
def role_at_least(role: int, requirement: int) -> bool:
    """Returns true if a role meets the requirement, false otherwise"""
    return role_rank(role) >= requirement

def user_is_at_least(user: discord.Member, requirement: int) -> bool:
    """Returns true if a user meets the requirement, false otherwise"""
    # Get the highest role of the user
    highest_role = max([role_rank(role.id) for role in user.roles])
    return highest_role >= requirement

def get_role_of_rank(guild: discord.Guild, rank: int) -> int:
    """Returns the role of a specified rank"""
    # If the rank is 0, return "0"
    if rank == 0:
        return 0
    db = sqlite3.connect('database.db')
    c = db.cursor()
    c.execute('SELECT * FROM ranks WHERE server_id=? AND rank=?', (guild.id, rank))
    result = c.fetchone()
    db.close()
    if result is None:
        raise ValueError('Role not found')
    return guild.get_role(result[1])

def generate_welcome_card(avatar_url: str, name: str) -> str:
    """Generates a welcome card, saving it to welcome.png and returning the path"""
    # Request the avatar, convert it to RGB
    avatar = Image.open(requests.get(avatar_url, stream=True).raw).convert("RGB")

    # Create same size alpha layer with circle, and apply to avatar
    alpha = Image.new("L", avatar.size, 0)
    draw = ImageDraw.Draw(alpha)
    draw.ellipse([(0, 0), avatar.size], fill=255)
    avatar.putalpha(alpha)

    avatar = avatar.resize((120, 120))

    # create a banner image that is just a transparent image
    banner = Image.new("RGBA", (500, 120), 0)
    overlay = Image.new("RGBA", banner.size, 0)
    overlay.paste(avatar, (0, 0))
    banner.alpha_composite(overlay)
    draw = ImageDraw.Draw(banner)

    # Find the size of the text and create a text image
    text_in_image=f"Welcome to the server, {name}!"
    font = ImageFont.truetype("font.ttf", 60)
    textimg = Image.new("RGBA", (1, 1), 0)
    textdraw = ImageDraw.Draw(textimg)
    size = textdraw.textsize(text_in_image, font=font)
    width = max(size)
    textimg = Image.new("RGBA", (width, width), 0)
    textdraw = ImageDraw.Draw(textimg)
    textdraw.text((width//2, width//2), text_in_image, font=font, anchor="mm", fill="LightGrey")
    textimg = textimg.resize((375, 375), resample=Image.LANCZOS)

    # Paste the text into the banner
    banner.paste(textimg, (125, -125))
    save_path = "welcome.png"
    banner.save(save_path)
    return save_path