import configparser
import os
import discord
import obs_controller
import asyncio
from discord.ext import commands
import re
import cv2
import math
import string
import random
import logging
from datetime import datetime

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

# Sets how long, in seconds, the bot will wait before deleting system messages besides the control panel
DELETE_AFTER = 5
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
EMOJI_restart_button = str("\U0001F501")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(intents=intents, command_prefix="!")

logging.basicConfig(
    filename="debug.log",
    encoding="utf-8",
    filemode="a",
    format="{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M:%S"
)

@bot.event
async def setup_hook() -> None:
    bot.add_view(OBSControls())
    bot.add_view(VideoControls())

@bot.event
async def on_ready():
    logging.info(f"Bot started.")
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
        logging.info(f"Scene swapped by {interaction.user.name}.")
        obs_controller.change_scene()
        embed = discord.Embed(
            title = "Scene Swapped!",
            description= "To swap back, click me again!"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=DELETE_AFTER)

    @discord.ui.button(label=f"{EMOJI_start_button} Start Stream", style=discord.ButtonStyle.green, custom_id='persistent_view:startstream')
    async def start_stream(self, interaction: discord.Interaction, button: discord.ui.Button):
        logging.info(f"Stream started by {interaction.user.name}.")
        obs_controller.start_stream()
        embed = discord.Embed(
            title = "Stream Started!",
            description="Give it a few seconds to show up in VRChat, VRCDN isn't instant!",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    @discord.ui.button(label=f"{EMOJI_stop_button} Stop Stream", style=discord.ButtonStyle.red, custom_id='persistent_view:stopstream')
    async def stop_stream(self, interaction: discord.Interaction, button: discord.ui.Button):
        logging.info(f"Stream stopped by {interaction.user.name}")
        obs_controller.stop_stream()
        embed = discord.Embed(
            title="Stream stopped!",
            description="Hope it went well!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)

    @discord.ui.button(label="Video Queue", style=discord.ButtonStyle.green, custom_id="persistent_view:vidorder")
    async def video_order(self, interaction: discord.Interaction, button: discord.ui.Button):
        logging.info("Video queue displayed.")
        queue = str(obs_controller.VO)
        embed = discord.Embed(
            title = "Current Video Queue:",
            description=queue,
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

class VideoControls(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Next Set", style=discord.ButtonStyle.blurple, custom_id='persistent_view:nextset')
    async def next_set(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            obs_controller.next_set()
            logging.info(f"Set cycled by {interaction.user.name}.")
        except IndexError:
            logging.warning(f"Set unsuccessfully cycled by {interaction.user.name}, final video in the queue.")
            await interaction.response.send_message("This is the final video in the queue! Try swapping the scene instead.", ephemeral=True, delete_after=DELETE_AFTER)
            return
        await interaction.response.send_message("Next set playing now!", ephemeral=True, delete_after=DELETE_AFTER)

    @discord.ui.button(label=f"{EMOJI_start_button} Play", style=discord.ButtonStyle.green, custom_id='persistent_view:play')
    async def resume_set(self, interaction: discord.Interaction, button: discord.ui.Button):
        logging.info(f"Set resumed by {interaction.user.name}.")
        obs_controller.resume_set()
        await interaction.response.send_message("Set Resumed!", ephemeral=True, delete_after=DELETE_AFTER)

    @discord.ui.button(label=f"{EMOJI_pause_button} Pause", style=discord.ButtonStyle.red, custom_id='persistent_view:pause')
    async def pause_set(self, interaction: discord.Interaction, button: discord.ui.Button):
        logging.info(f"Set paused by {interaction.user.name}.")
        obs_controller.pause_set()
        await interaction.response.send_message("Set Paused!", ephemeral=True, delete_after=DELETE_AFTER)

    # TODO:
    # figure out wtf is going on with wait_for and why it thinks its being used outside of an async context
    # For now this is disabled

   # @discord.ui.button(label="Set Video Time", style=discord.ButtonStyle.green, custom_id="persistent_view:ffrwd")
   # async def set_video_time(self, interaction: discord.Interaction, button:discord.ui.Button):
#
   #     def check(m):
   #         return m.author == interaction.user
#
   #     video = cv2.VideoCapture(f"{VIDEO_DIR}/{CURR_SET}.mp4")
   #     duration = video.get(cv2.CAP_PROP_POS_MSEC) # Length of video in miliseconds
   #     curr_cursor = obs_controller.get_set_cursor()
   #     if curr_cursor == None:
   #         await interaction.response.send_message("I'm sorry, the video isn't currently playing. Please start the video before modifying the time.")
   #         return
   #     else:
   #         await interaction.response.send_message("What time would you like to move the set to? You can type in a time code (HH:MM:SS), or the number of seconds.")
   #         try:
   #             reply = await client.wait_for("message", check=check, timeout=30)
   #             div = reply.content.split(":")
   #             if len(div) < 1:
   #                 try:
   #                     milliseconds = int(div[0]) * 1000
   #                 except TypeError:
   #                     await interaction.followup.send("I'm sorry, that doesn't seem to be a valid time. Please try again.")
   #                     return
   #             else:
   #                 try:
   #                     milliseconds = (int(div[0])*60*60*1000) + (int(div[1]*60*1000) + int(div[2])*1000)
   #                 except TypeError:
   #                     await interaction.followup.send("I'm sorry, that doesn't seem to be a valid timecode. Please try again.")
   #                     return
   #         
   #             if milliseconds > duration:
   #                 await interaction.followup.send("I'm sorry, that is beyond the length of the video!")
   #                 return
   #             if milliseconds < 0:
   #                 await interaction.followup.send("That's a negative value, I can't go below 0!")
   #                 return
#
   #             obs_controller.set_cursor(milliseconds)
   #         except asyncio.TimeoutError:
   #             await interaction.followup.send("I'm sorry, I timed out waiting for your response!")

    @discord.ui.button(label=f"{EMOJI_restart_button} Restart Set", style=discord.ButtonStyle.red, custom_id="persistent_view:restart")
    async def restart(self, interaction: discord.Interaction, button: discord.ui.Button):
        logging.info(f"Set restarted by {interaction.user.name}.")
        obs_controller.restart_set()
        await interaction.response.send_message("Set restarted!", delete_after=DELETE_AFTER)

def build_option_list():
    files = obs_controller.VO.files
    options = []
    if len(files) == 0:
        return None
    for file in files:
        options.append(
            discord.SelectOption(
                label=file,
                description=f"Currently number {files.index(file)+1} in the queue"
            )
        )
    return options

# TODO:
# Implement
class video_select(discord.ui.Select):
    def __init__(self):
        self.files = obs_controller.VO.files
        self.options = []
        for file in self.files:
            self.options.append(
                discord.SelectOption(
                    label=file,
                    description=f"Currently number {self.files.index(file)+1} in the queue"
                )
            )

        super().__init__(placeholder="Select a Video",max_values=1,min_values=1,options=self.options)
    async def callback(self, interaction, select):
        await interaction.response.send_message(f"{select.values[0]}")

class select_view(discord.ui.View):
    def __init__(self, *, timeout=180):
        super().__init__(timeout=timeout)
        self.add_item(video_select())

@bot.command()
async def sync(interaction: discord.Interaction):
    # TODO:
    # Change this command to look for a role rather than an ID
    # Or just do it on boot idfc
    if not interaction.author.id == 223254712944820224:
        logging.warning(f"Sync command run by {interaction.user.name}.")
        print("Someone was a naughty sausage!")
        return
    await bot.tree.sync()

@bot.command()
async def test(ctx):
    # This is purely a debug command
    # Will be gone later
    await ctx.channel.send("Choose a flavor you cunt", view=select_view())

# Currently replies application failed to respond
# TODO: Fix
@bot.tree.command(name="controlpanel", description="Create the bot's control panel in this channel.")
# @bot.has_any_roles(STAFF_ROLES_STR)
async def control_panel(interaction:discord.Interaction):
    logging.info(f"Control panel spawned by {interaction.user.name}.")
    embed_obs = discord.Embed(
        title = "Stream Controls",
        description = "Use these buttons to control OBS/The stream itself",
        colour = discord.Color.blue()
    )
    await interaction.channel.send(embed=embed_obs, view=OBSControls())

    embed_video = discord.Embed(
        title = "Video Controls",
        description = "Use these buttons to control the currently playing video",
        colour = discord.Color.green()
    )
    await interaction.channel.send(embed=embed_video, view=VideoControls())

def rand_string(len):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for i in range(len))

@bot.tree.command(name="addvideo", description="Add a video to the player's queue")
async def add_video(interaction:discord.Interaction, url:str, filename:str=None):
    # TODO:
    # Add timeouts to ephemeral messages

    if filename == "current_set":
        logging.warning(f"Invalid filename passed to addvideo command by {interaction.user.name}: 'current_set' is a reserved name.")
        await interaction.response.send_message("You picked the only name you can't have, sorry! If this is the first video being downloaded, don't worry! That'll be automatically assigned. Please pick a different name!", ephemeral=True)
    if url == None:
        logging.warning(f"No URL passed to addvideo command by {interaction.user.name}.")
        await interaction.response.send_message("Sorry, a URL is required to download the video! Ensure you entered the URL into the field as well!", ephemeral=True)
        return
    await interaction.response.send_message(f"Attempting video download... Please be patient! This can take a while!\nDuring the download, the bot may become unresponsive.", ephemeral=True)
    try:
        if filename == None:
            filename = rand_string(12)
        place = await obs_controller.download_video(url, filename)
        if place >= 0:
            await interaction.followup.send(content=f"{filename} downloaded! It is number {place+1} in the queue!", ephemeral=True)
        else:
            await interaction.followup.send(content=f"{filename} downloaded! It's loaded and ready to play!", ephemeral=True)
        logging.info(f"File with url {url} downloaded as {filename}.mp4 by {interaction.user.name}.")
    except:
        logging.error(f"Improper URL passed to addvideo command by {interaction.user.name}. URL: {url}")
        await interaction.followup.send(content=f"Something went wrong with the video download, are you sure you gave it a valid youtube URL?", ephemeral=True)

@bot.tree.command(name="removevideo", description="Remove a video from the player's queue!")
async def remove_video(interaction: discord.Interaction, video:str):
    if not video.endswith(".mp4"):
        video += ".mp4"
    if not os.path.exists(f"{VIDEO_DIR}/{video}.mp4"):
        logging.warning(f"Invalid filename passed to removevideo command by {interaction.user.name}. Filename: {video}")
        await interaction.response.send_message(f"I'm sorry, {video} is not a valid filename.", ephemeral=True, delete_after=DELETE_AFTER)
        return

    obs_controller.VO.remove(video)
    os.remove(f"{VIDEO_DIR}/{video}")
    logging.info(f"File {video} removed from queue by {interaction.user.name}.")
    embed = discord.Embed(
        title = f"{video} removed from queue!",
        description = f"Here's the queue now: \n{str(obs_controller.VO)}"
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=DELETE_AFTER)






if __name__ == "__main__":
    token = re.sub(r"\"", "", config["DEFAULT"]["token"])
    bot.run(token)
