import yt_dlp
import os
import configparser
import discord
import obsws_python as obs
from datetime import datetime
import obsws_python as obs
import shutil
import re
import time


VIDEO_DIR = os.path.join(os.getcwd(), "bin/videos")
ARCHIVE_DIR = os.path.join(VIDEO_DIR, "archive")
if not os.path.exists(ARCHIVE_DIR):
    os.makedirs(ARCHIVE_DIR)
CURR_SET = "current_set"
# Just makes editing filename easier on me

config = configparser.ConfigParser()
config.read("config.toml")
CL = obs.ReqClient()

# https://github.com/obsproject/obs-websocket/blob/master/docs/generated/protocol.md#obsmediainputactionobs_websocket_media_input_action_restart

class video_order:
    """
    Class to make handling the video order easier than loading from a json
    All that is stored is the filenames themselves, without the extension.
    Assumes the current_set.mp4 file does not need to be tracked since it's always "first"
    """
    def __init__(self, from_file=False):
        self.files = []
        if from_file:
            try:
                self.files = self.read().split(",")
            except FileNotFoundError:
                print("Video order not found! Using empty list!")

    def index_of(self, key:str) -> int:
        try:
            return self.files.index(key)
        except ValueError:
            print(f"Video file {key} not found in the order!")
            return None
        
    def add_video(self, filename:str, index:int=-1):
        """
        Adds a filename to the list at specified index, defaults to just appending it.
        """
        if index == -1:
            self.files.append(filename)
        else:
            self.files.insert(index, filename)
    
    def reorder(self, filename:str, index:int):
        """
        Pulls an item out of the list and re-inserts it at a new index.
        """
        if filename not in self.files:
            print(f"{filename} not found in the list! Double check your spelling!")
            return
        
        self.files.remove(filename)
        self.files.insert(index, filename)

    def shift_up(self) -> str:
        """
        Returns the first item in the list, and removes it. Used when changing sets.
        """
        return self.files.pop(0)
    
    def write(self):
        """
        Write list to a file inside the video directory
        """
        vid_order = ""
        for item in self.files:
            if self.index_of(item) != len(self.files) -1:
                vid_order += f"{item},"
            else:
                vid_order += item
        file = os.path.join(VIDEO_DIR, "list.txt")
        with open(file, "w") as f:
            f.write(vid_order)

    def read(self):
        """
        Read list from file inside video directory as plain text
        """
        file = os.path.join(VIDEO_DIR, "list.txt")
        with open(file, "r") as f:
            return f.read(f)

VO = video_order()


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

def start_stream():
    set_scene_brb()
    CL.start_stream()

def stop_stream():
    CL.stop_stream()

def get_set_info():
    info = CL.get_media_input_status("Set").media_cursor

def archive_video():
    curr_video = os.path.join(f"{VIDEO_DIR}", f"{CURR_SET}.mp4")
    now = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    archived_video = os.path.join(f"{ARCHIVE_DIR}", f"{now}.mp4")
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
    
    if has_first:
        VO.add_video(fname)
    else:
        return -1

    return VO.index_of(fname)

def next_set():
    """
    Advances the video player to the next set.
    """

    set_scene_brb()
    time.sleep(1)
    archive_video()
    next_vid = VO.shift_up()
    next_vid_path = os.path.join(VIDEO_DIR, next_vid)
    current_vid_path = os.path.join(VIDEO_DIR, f"{CURR_SET}.mp4")
    shutil.move(next_vid_path, current_vid_path)
    change_scene()

def pause_set():
    CL.trigger_media_input_action("Set", "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PAUSE")

def resume_set():
    CL.trigger_media_input_action("Set", "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PLAY")

if __name__ == "__main__":
    # change_scene("TestBRB")
    download_video("https://www.youtube.com/watch?v=Bjt7mDVCLtk", "testFile1")
    download_video("https://www.youtube.com/watch?v=JP7zsdorPLI", "testFile2")
    download_video("https://www.youtube.com/watch?v=TUzvD4XjBBo", "testFile3")
    download_video("https://www.youtube.com/watch?v=8Bm3le9s3-A", "testFile4")
    VO.write()
    pause = input("Waiting...")
    next_set()
    VO.write()
    pause = input("Waiting...")
    next_set()
    VO.write()
    pause = input("Waiting...")
    next_set()
    VO.write()