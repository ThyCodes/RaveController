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
import copy
import time


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

if not os.path.isfile(VIDEO_JSON):
    with open(VIDEO_JSON, "w") as f:
        f.write("")

# client.run(config["DEFAULT"]["token"])

# https://github.com/obsproject/obs-websocket/blob/master/docs/generated/protocol.md#obsmediainputactionobs_websocket_media_input_action_restart

def add_to_json(filename):
    """
    Adds an entry to the JSON file keeping track of what order the videos are to be played in.
    Adds the file to the end of the list.
    """
    try:
        with open(VIDEO_JSON, "r") as f:
            data = json.load(f)
            next_index = str(len(data.keys()))
            data[next_index] = filename
    except Exception as e:
            print(e)
            print("Video order JSON file not found or was empty, creating...")
            data = {"0":filename}
    with open(VIDEO_JSON, "w") as f:
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
    curr_video = os.path.join(f"{VIDEO_DIR}", f"{CURR_SET}.mp4")
    now = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
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
    has_first = False
    for file in os.listdir(vid_dir):
        if file.endswith("mp4"):
            if CURR_SET in file:
                has_first = True

    
    if not has_first:
        fname = f"{CURR_SET}.mp4"
    else:
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
    with open(VIDEO_JSON, "r") as f:
        if not fname in f.read():
            add_to_json(fname)

def next_set():
    """
    Advances the video player to the next set.
    """
    with open(VIDEO_JSON, "r") as f:
        data = json.load(f)

    set_scene_brb()
    time.sleep(1)
    archive_video()
    next_vid_path = os.path.join(VIDEO_DIR, data["1"])
    current_vid_path = os.path.join(VIDEO_DIR, f"{CURR_SET}.mp4")
    shutil.move(next_vid_path, current_vid_path)
    change_scene()
    # New video is loaded, now we rebuild the JSON with the new info
    data_new = copy.deepcopy(data)
    data_new["0"] = f"{CURR_SET}.mp4"
    del data_new["1"]
    final_entry = len(data_new.keys())
    for key in list(data_new.keys())[1:]:
        index_int = int(key)
        data_new[str(index_int-1)] = data_new[key]
        print(f"Index {index_int} moved up")
    if final_entry != 1:
        del data_new[str(final_entry)]
    
    with open(VIDEO_JSON, "w") as f:
        json.dump(data_new, f, indent=4)

if __name__ == "__main__":
    # change_scene("TestBRB")
    download_video("https://www.youtube.com/watch?v=Bjt7mDVCLtk", "testFile1")
    download_video("https://www.youtube.com/watch?v=JP7zsdorPLI", "testFile2")
    download_video("https://www.youtube.com/watch?v=TUzvD4XjBBo", "testFile3")
    download_video("https://www.youtube.com/watch?v=8Bm3le9s3-A", "testFile4")
    pause = input("Waiting...")
    next_set()
    pause = input("Waiting...")
    next_set()
    pause = input("Waiting...")
    next_set()