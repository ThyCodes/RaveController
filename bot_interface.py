import configparser
import os
import discord
import obs_controller
import asyncio
from discord.ext import commands
import re

# https://github.com/obsproject/obs-websocket/blob/master/docs/generated/protocol.md#obsmediainputactionobs_websocket_media_input_action_restart

"""
PRIMARY GOALS:
- Allow for OBS and Video to be controlled via bot
- Allow for download of YouTube videos
- Allow for redordering of downloaded videos
- SIMPLE. SIMPLE. S I M P L E.

Optional Goals:
- Allow for scene management via bot
- Allow for custom text to display on the BRB scene
- Allow for video rewinding or fast forwarding
- Partial filename recognition

Stretch Goals:
- Show video state via embed
- Allow for direct video upload
- Show screenshots of the current file structure
- Show screenshots of the current OBS setup

"""


VIDEO_DIR = os.path.join(os.getcwd(), "bin/videos")
ARCHIVE_DIR = os.path.join(VIDEO_DIR, "archive")
if not os.path.exists(ARCHIVE_DIR):
    os.makedirs(ARCHIVE_DIR)
CURR_SET = "current_set"
# Just makes editing filename easier on me
intents=discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

config = configparser.ConfigParser()
config.read("config.toml")

# If you have quotes in your role sorry
# But that's dumb :3
# Also this is causing weird issues so commented out for now
# STAFF_ROLES = re.sub(r"[\"]", "", config["DEFAULT"]["roles"]).split(",")
# STAFF_ROLES_STR = ""
# for role in STAFF_ROLES:
#     STAFF_ROLES[STAFF_ROLES.index(role)] = role.strip()
#     if STAFF_ROLES.index(role) == len(STAFF_ROLES)-1:
#         STAFF_ROLES_STR += role
#     else:
#         STAFF_ROLES_STR += f"{role},"

# Emoji List
EMOJI_stop_button = str("\U000023F9" + "\U0000FE0F")
EMOJI_start_button = str("\U000025B6" + "\U0000FE0F")
EMOJI_pause_button = str("\U000023F8" + "\U0000FE0F")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(intents=intents, command_prefix="!")

@bot.event
async def setup_hook() -> None:
    bot.add_view(OBSControls())
    bot.add_view(VideoControls())

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} and ready to FUCK THE HOUSE UP BAYBEEEEEEEEEEEE\n---------")

class OBSControls(discord.ui.View):
    """
    Class for creating persistent buttons so the discord bot will function even if a reboot needs to happen mid set
    Hopefully doesnt need to happen! But just in case.
    """


    def __init__(self):
        super().__init__(timeout=None)


    # TODO:
    # Possibly store the current cursor location in MS
    # Just in case this button is clicked accidentally
    @discord.ui.button(label="Swap Scene", style=discord.ButtonStyle.gray, custom_id='persistent_view:swapscene')
    async def swap_scene(self, interaction: discord.Interaction, button: discord.ui.Button):
        obs_controller.change_scene()
        await interaction.response.send_message("Scene swapped!", ephemeral=True)

    # TODO:
    # Maybe make this just a command that displays everything else?
    @discord.ui.button(label=f"{EMOJI_start_button} Start Stream", style=discord.ButtonStyle.green, custom_id='persistent_view:startstream')
    async def start_stream(self, interaction: discord.Interaction, button: discord.ui.Button):
        obs_controller.start_stream()
        await interaction.response.send_message("Starting stream...", ephemeral=True)

    
    @discord.ui.button(label=f"{EMOJI_stop_button} Stop Stream", style=discord.ButtonStyle.red, custom_id='persistent_view:stopstream')
    async def stop_stream(self, interaction: discord.Interaction, button: discord.ui.Button):
        obs_controller.stop_stream()
        await interaction.response.send_message("Stream stopped!", ephemeral=True)

class VideoControls(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Next Set", style=discord.ButtonStyle.blurple, custom_id='persistent_view:nextset')
    async def next_set(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            obs_controller.next_set()
        except IndexError:
            await interaction.response.send_message("This is the final video in the queue!")
            return
        await interaction.response.send_message("Next set playing now!", ephemeral=True)

    @discord.ui.button(label=f"{EMOJI_start_button} Play", style=discord.ButtonStyle.green, custom_id='persistent_view:play')
    async def resume_set(self, interaction: discord.Interaction, button: discord.ui.Button):
        obs_controller.resume_set()
        await interaction.response.send_message("Set Resumed!", ephemeral=True)

    @discord.ui.button(label=f"{EMOJI_pause_button} Pause", style=discord.ButtonStyle.red, custom_id='persistent_view:pause')
    async def pause_set(self, interaction: discord.Interaction, button: discord.ui.Button):
        obs_controller.pause_set()
        await interaction.response.send_message("Set Paused!", ephemeral=True)

@bot.command()
async def sync(interaction: discord.Interaction):
    if not interaction.author.id == 223254712944820224:
        print("Someone was a naughty sausage!")
        return
    await bot.tree.sync()

@bot.tree.command()
async def test(interaction: discord.Interaction):
    await interaction.response.send_message("BlurgleGurgleldfnmrueg", view=OBSControls())

@bot.tree.command()
async def test2(interaction: discord.Interaction):
    await interaction.response.send_message("FlingleDingle", view=VideoControls())

@bot.tree.command(name="controlpanel", description="Create the bot's control panel in this channel.")
# @bot.has_any_roles(STAFF_ROLES_STR)
async def control_panel(interaction:discord.Interaction):
    pass

@bot.tree.command(name="addvideo", description="Add a video to the player's queue")
async def add_video(interaction:discord.Interaction, url:str=None, filename:str="Change Me!"):
    if url == None:
        await interaction.response.send_message("Sorry, a URL is required to download the video! Tends to help, yknow.", ephemeral=True)
        return
    msg_id = await interaction.response.send_message(f"Attempting video download... Please be patient! This can take a while!", ephemeral=True).message_id
    try:
        place = obs_controller.download_video(url, filename)
        msg = await interaction.channel.fetch_message(msg_id)
        if place >= 0:
            await msg.edit(f"Video downloaded! It is number {place+1} in the queue!", ephemeral=True)
        else:
            await msg.edit(f"Video downloaded! It's loaded and ready to play!", ephemeral=True)
    except:
        await msg.edit(f"Something went wrong with the video download, are you sure you gave it a unique filename?", ephemeral=True)








if __name__ == "__main__":
    token = re.sub(r"\"", "", config["DEFAULT"]["token"])
    bot.run(token)
