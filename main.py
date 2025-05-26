import yt_dlp
import os
import configparser
import discord
import obsws_python as obs
from datetime import datetime
import obsws_python as obs
import shutil
import re
import json


VIDEO_DIR = os.path.join(os.getcwd(), "bin/videos")
VIDEO_JSON = os.path.join(VIDEO_DIR, "order.json")
CURR_SET = "current_set"
# Just makes editing filename easier on me
intents=discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

config = configparser.ConfigParser()
config.read("config.toml")
CL = obs.ReqClient()

# client.run(config["DEFAULT"]["token"])

# https://github.com/obsproject/obs-websocket/blob/master/docs/generated/protocol.md#obsmediainputactionobs_websocket_media_input_action_restart

def add_to_json(filename):
    """
    Adds an entry to the JSON file keeping track of what order the videos are to be played in.
    Adds the file to the end of the list.
    """
    with open(VIDEO_JSON, "w") as f:
        try:
            data = json.load(f)
            next_index = str(len(data.keys()) - 1)
            data[next_index] = filename
        except:
            print("Video order JSON file not found or was empty, creating...")
            data = {"0":filename}
        json.dump(data, f, indent=4)

def set_scene_brb():
    """
    Forces the currently active scene to the "inactive" scene for video swapping
    """
    swap_scene = re.sub(r"[^0-9A-Za-z ]", "", config.get("DEFAULT", "swap_scene"))
    CL.set_current_program_scene(swap_scene)
    return

def change_scene():
    """
    Flips the active scene between the active set scene and the transition scene, Mostly to allow the file to be swapped out behind the scenes.

    Defaults to swapping to the transition scene if any other scene is currently active, just in case.
    """
    # Why does it have to remove the "" from the string? Fuck if I know, god hates me I guess.
    # Anyway dont put punctuation in your scene names. Sorry to non-english languages for this one but im lazy
    live_scene = re.sub(r"[^0-9A-Za-z ]", "", config.get("DEFAULT", "live_scene"))
    swap_scene = re.sub(r"[^0-9A-Za-z ]", "", config.get("DEFAULT", "swap_scene"))
    current_scene = CL.get_current_program_scene().current_program_scene_name
    print(f"Scene: {current_scene}")
    try:
        if current_scene == swap_scene:
            CL.set_current_program_scene(live_scene)
        else:
            CL.set_current_program_scene(swap_scene)
    except obs.error.OBSSDKRequestError:
        print("Error processing the source names in your config.toml file. Make sure they exist and there isn't punctuation or non-english characters!")

def archive_video():
    archive_dir = os.path.join(VIDEO_DIR, "archive")
    curr_video = os.path.join(f"{VIDEO_DIR}", CURR_SET)
    now = datetime.now().strftime()
    archived_video = os.path.join(f"{archive_dir}", f"{now}.mp4")
    shutil.move(curr_video, archived_video)
    # Rename File to current time and move to archive folder
    # Will get followed up by the next set vid being renamed to current_set.mp4
    # Gotta figure out that structure first
    # TODO: Come back to this

def download_video(url:str, name:str):
    """
    Downloads the youtube video passed in via URL, gives it an index and a name.
    The name wont have to be unique but yknow, it should be for ease of looking up.
    Forces first file downloaded to be named "current_set.mp4" so it will work with OBS, though this can be changed by editing global vars
    """
    cur_dir = os.getcwd()
    vid_dir = os.path.join(cur_dir, VIDEO_DIR)
    largest_index = -1
    for file in os.listdir(vid_dir):
        if file.endswith("mp4"):
            try:
                f_index = int(file.split("_")[0])
            except ValueError:
                print("WARNING: Improperly named mp4 in the video file! Please delete or rename!")
                continue
            if int(f_index) > largest_index:
                largest_index = f_index

    index = largest_index + 1
    if index == 0:
        name = CURR_SET

    fname = f"{name}.mp4"
    opts = {
        'format_sort': ["res:1080","ext:mp4:m4a"],
        "outtmpl": os.path.join(vid_dir, fname)
    }
    ydl = yt_dlp.YoutubeDL(opts)
    try:
        ydl.download(url)
    except yt_dlp.utils.DownloadError:
        print("Error downloading youtube video, are you sure that is a valid, visible URL?")
        #TODO: Actual error processing in case of invalid URL
        return
    
    return fname

def next_set():
    """
    Advances the video player to the next set.
    """
    with open(VIDEO_JSON, "r") as f:
        data = json.load(f)

    set_scene_brb()
    archive_video()
    next_vid_path = os.path.join(VIDEO_DIR, data["1"])
    current_vid_path = os.path.join(VIDEO_DIR, f"{CURR_SET}.mp4")
    shutil.move(next_vid_path, current_vid_path)
    change_scene()

if __name__ == "__main__":
    # change_scene("TestBRB")
    change_scene()
    file = download_video("https://www.youtube.com/watch?v=gXIs--FDeLA", "testFile")
    add_to_json(file)