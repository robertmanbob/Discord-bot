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
    avatar = Image.open(requests.get(avatar_url, stream=True).raw).convert("RGBA")
    welcome_gif = Image.open("welcome.gif")

    # Create same size alpha layer with circle, gaussian blur, and apply to avatar
    alpha = Image.new("L", avatar.size, 0)
    draw = ImageDraw.Draw(alpha)
    draw.ellipse([(0, 0), avatar.size], fill=255)
    avatar.putalpha(alpha)

    avatar = avatar.resize((120, 120))

    # create a banner image that is just a transparent image
    banner = Image.new("RGBA", (500, 140), 0)
    overlay = Image.new("RGBA", banner.size, 0)
    overlay.paste(avatar, (10, 10))
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
    banner.paste(textimg, (135, -115))
    
    gen_welcome = []
    # Open each frame of the welcome gif, paste the banner, save to a new frame
    for frame in range(welcome_gif.n_frames):
        welcome_gif.seek(frame)
        new_frame = Image.new("RGBA", welcome_gif.size, 0)
        new_frame.paste(welcome_gif)
        new_frame.paste(banner, (0, 0), banner)
        new_frame = new_frame.convert(mode='P', palette=Image.ADAPTIVE)
        cropped_frame = new_frame.crop((0, 0, 500+20, 140))
        gen_welcome.append(cropped_frame)



    # Save the frames to a new gif
    gen_welcome[0].save(f"welcome_{name}.gif", save_all=True, append_images=gen_welcome[1:], loop=0, duration=welcome_gif.info['duration'], disposal=1, optimize=True)

    # Return the path to the first frame
    print(f"Welcome card generated for {name}")
    return f"welcome_{name}.gif"

    
