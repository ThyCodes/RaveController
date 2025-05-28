import configparser
import os
import discord
import obs_controller
import asyncio
from discord.ext import commands
import re

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


# Yes I yanked this right out of the examples on discord.py's github. Sue me. (dont)
class PersistentViewBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(intents=intents, command_prefix="!")

    async def setup_hook(self) -> None:
        self.add_view(PersistentView())

    async def on_ready(self):
        print(f"Logged in as {self.user} and ready to FUCK THE HOUSE UP BAYBEEEEEEEEEE\n--------")

class PersistentView(discord.ui.View):
    """
    Class for creating persistent buttons so the discord bot will function even if a reboot needs to happen mid set
    Hopefully doesnt need to happen! But just in case.
    """


    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Swap Scene", style=discord.ButtonStyle.gray, custom_id='persistent_view:swapscene')
    async def swap_scene(self, interaction: discord.Interaction, button: discord.ui.Button):
        obs_controller.change_scene()
        await interaction.response.send_message("Scene swapped!", ephemeral=True)

    @discord.ui.button(label="Next Set", style=discord.ButtonStyle.blurple, custom_id='persistent_view:nextset')
    async def next_set(self, interaction: discord.Interaction, button: discord.ui.Button):
        obs_controller.next_set()
        await interaction.response.send_message("Next set loading now!", ephemeral=True)

    @discord.ui.button(label="Play", style=discord.ButtonStyle.green, custom_id='persistent_view:play')
    async def resume_set(self, interaction: discord.Interaction, button: discord.ui.Button):
        obs_controller.resume_set()
        await interaction.response.send_message("Set Resumed!", ephemeral=True)

    @discord.ui.button(label="Pause", style=discord.ButtonStyle.red, custom_id='persistent_view:pause')
    async def pause_set(self, interaction: discord.Interaction, button: discord.ui.Button):
        obs_controller.pause_set()
        await interaction.response.send_message("Set Paused!", ephemeral=True)


bot = PersistentViewBot()
@bot.command()
async def test(ctx:commands.Context):
    await ctx.send("BlurgleGurgleldfnmrueg", view=PersistentView())







if __name__ == "__main__":
    token = re.sub(r"\"", "", config["DEFAULT"]["token"])
    bot.run(token)
