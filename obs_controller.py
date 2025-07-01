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
import sys
import psutil
import logging


VIDEO_DIR = os.path.join(os.getcwd(), "bin/videos")
ARCHIVE_DIR = os.path.join(VIDEO_DIR, "archive")
if not os.path.exists(ARCHIVE_DIR):
    os.makedirs(ARCHIVE_DIR)
CURR_SET = "current_set"

# Just makes editing filename easier on me

def setup():
    """
    First time setup function
    Only runs when the user has not created the required config.toml
    Will create the necessary file and advise the user on how to set up OBS.

    Default OBS setup will be processed on second boot once the websocket connection has been configured.
    """
    config["DEFAULT"] = {"swap_scene": "", "live_scene": "", "token": "YOUR_BOT_TOKEN_HERE"}
    config["connection"] = {"host": "\"localhost\"", "port": 4455, "password": "\"YOUR_WEBSOCKET_PASSWORD_HERE\"", "timeout": "None"}
    with open("config.toml", "w") as f:
        config.write(f)

    print("Default config file generated! Fill it out with whatever information you'd like, configure your OBS websocket, then run this file again to auto-generate the necessary scenes and sources!\n\nFor a more detailed explanation of what to do, check out the setup guide in the readme!")
    quit()

config = configparser.ConfigParser()
try:
    config.read("config.toml")
except FileNotFoundError:
    setup()
SWAP_SCENE = re.sub(r"[^0-9A-Za-z ]", "", config.get("DEFAULT", "swap_scene"))
LIVE_SCENE = re.sub(r"[^0-9A-Za-z ]", "", config.get("DEFAULT", "live_scene"))

def scene_setup():
    # ALL UNTESTED
    global SWAP_SCENE
    global LIVE_SCENE
    scenes = CL.get_scene_list().scenes
    if SWAP_SCENE == "" and "BRBScene" not in scenes:
        config["DEFAULT"]["swap_scene"] = "BRBScene"
        SWAP_SCENE = "BRBScene"
        with open("config.toml", "w") as f:
            config.write(f)
    if LIVE_SCENE == "" and "SetScene" not in scenes:
        config["DEFAULT"]["live_scene"] = "SetScene"
        LIVE_SCENE = "SetScene"
        with open("config.toml", "w") as f:
            config.write(f)
    
    if SWAP_SCENE not in scenes:
        CL.create_scene(SWAP_SCENE)
        logging.info(f"Scene {SWAP_SCENE} created in OBS.")
    if LIVE_SCENE not in scenes:
        CL.create_scene(LIVE_SCENE)
        logging.info(f"Scene {LIVE_SCENE} created in OBS.")
    set_media_input = CL.get_scene_item_list(LIVE_SCENE)
    if "Set" not in set_media_input:
        settings = {
            "local_file": os.path.join(VIDEO_DIR, "current_set.mp4"),
            "looping": False
        }
        try:
            CL.create_input(
                scene_name = LIVE_SCENE,
                input_name = "Set",
                input_kind = "ffmpeg_source",
                input_settings = settings,
                scene_item_enabled = True
            )
            logging.info(f"Set Media Input created in OBS scene {LIVE_SCENE}")
        except Exception as e:
            print(f"Error adding media source: {e}")




logging.basicConfig(
    filename="debug.log",
    encoding="utf-8",
    filemode="a",
    format="{asctime} - {levelname}_OBS - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M:%S"
)

try:
    CL = obs.ReqClient()
    logging.info("Connected to OBS websocket.")
except ConnectionRefusedError:
    try:
        if "OBS.exe" in (i.name() for i in psutil.process_iter()):
            logging.error("OBS websocket connection failed due to improper config.")
            sys.exit("Oops! There was an error connecting to OBS. Are you sure the config.toml has the correct info and OBS is running with the websocket option enabled?")
        else:
            logging.critical("OBS was not detected in the running process list.")
            sys.exit("Oops! OBS is not running! Please be sure to start OBS before running the bot!")
    except psutil.NoSuchProcess:
        logging.critical("OBS was not detected in the running process list.")
        sys.exit("Oops! OBS is not running! Please be sure to start OBS before running the bot!")

scene_setup()


# https://github.com/obsproject/obs-websocket/blob/master/docs/generated/protocol.md#obsmediainputactionobs_websocket_media_input_action_restart

class video_order:
    """
    Class to make handling the video order easier than loading from a json
    All that is stored is the filenames themselves, without the extension.
    Assumes the current_set.mp4 file does not need to be tracked since it's always "first"
    """
    def __init__(self):
        self.files = []
        for file in os.listdir(VIDEO_DIR):
            file_path = os.path.join(VIDEO_DIR, file)
            if os.path.isfile(file_path):
                print(file)
                if file == f"{CURR_SET}.mp4":
                    continue
                if file.endswith(".mp4"):
                    self.files.append(file)
        # Does not load from a .txt anymore
        # But kept this for debugging
        self.write()

    def remove(self, filename):
        self.files.remove(filename)
        logging.info(f"Removed {filename} from queue.")

    def __str__(self):
        file_list = ""
        if len(self.files) == 0:
            return "There are no videos in the queue!"
        for file in self.files:
            print(file)
            if self.files.index(file) != len(self.files)-1:
                file_str = file + "\n"
            else:
                file_str = file
            file_list += f"{self.files.index(file)+1}. {file_str}"
        return file_list

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
        logging.info(f"File {filename} added to queue.")
        self.write()
    
    def reorder(self, filename:str, index:int):
        """
        Pulls an item out of the list and re-inserts it at a new index.
        """
        if filename not in self.files:
            print(f"{filename} not found in the list! Double check your spelling!")
            return
        
        self.files.remove(filename)
        self.files.insert(index, filename)
        logging.info(f"File {filename} reordered in queue to index {index}.")

    def shift_up(self) -> str:
        """
        Returns the first item in the list, and removes it. Used when changing sets.
        """
        next_file = self.files.pop(0)
        self.write()
        logging.info(f"Queue moved up, file {next_file} now playing.")
        return next_file
    
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
            return f.read()

VO = video_order()

    

def set_scene_brb():
    """
    Forces the currently active scene to the "inactive" scene for video swapping
    """
    CL.set_current_program_scene(SWAP_SCENE)
    logging.info(f"Scene swapped to {SWAP_SCENE}.")
    return

def change_scene():
    """
    Flips the active scene between the active set scene and the transition scene, Mostly to allow the file to be swapped out behind the scenes.

    Defaults to swapping to the transition scene if any other scene is currently active, just in case.
    """
    # Why does it have to remove the "" from the string? Because .toml files are dumb and I cba changing over to a different library at this point.
    # Anyway dont put punctuation in your scene names. Sorry to non-english languages for this one but im lazy
    current_scene = CL.get_current_program_scene().current_program_scene_name
    print(f"Scene: {current_scene}")
    try:
        if current_scene == SWAP_SCENE:
            CL.set_current_program_scene(LIVE_SCENE)
            logging.info(f"Scene changed from {SWAP_SCENE} to {LIVE_SCENE}.")
        else:
            CL.set_current_program_scene(SWAP_SCENE)
            logging.info(f"Scene changed from {LIVE_SCENE} to {SWAP_SCENE}.")
    except obs.error.OBSSDKRequestError:
        logging.error(f"Improper scene names in config.toml: Live: {LIVE_SCENE} | Swap: {SWAP_SCENE}")
    if not video.endswith(".mp4"):
        video += ".mp4"
        print("Error processing the source names in your config.toml file. Make sure they exist and there isn't punctuation or non-english characters!")

def start_stream():
    set_scene_brb()
    CL.start_stream()
    logging.info("Stream started.")

def stop_stream():
    CL.stop_stream()
    logging.info("Stream stopped.")

def get_set_cursor():
    info = CL.get_media_input_status("Set").media_cursor
    return info

def resize_video_obj():
    """
    Resizes the video object in OBS to 1920x1080, regardless of the source resolution
    """
    # In case more than just the video item is added to the scene
    resp = CL.get_scene_item_list(scene_name=LIVE_SCENE)
    items = resp.scene_items
    item = next((i for i in items if i.source_name == "Set"), None)
    if not item:
        logging.critical(f"Live scene improperly configured: no media source with name Set found.")
        raise ValueError(f"Source 'Set' was not found in the live scene, please ensure the OBS setup function completed successfully.")

    sid = item.scene_item_id

    t_resp = CL.get_scene_item_transform(scene_name=LIVE_SCENE, scene_item_id=sid)
    info = t_resp.scene_item_transform
    video_w = info.source_width
    video_h = info.source_height

    scale_x = 1920 / video_w
    scale_y = 1080 / video_h

    CL.set_scene_item_transform(
        scene_name=LIVE_SCENE,
        scene_item_id=sid,
        scene_item_transform={
            "positionX": 0.0,
            "positionY": 0.0,
            "scaleX": scale_x,
            "scaleY": scale_y,
            "rotation": 0.0,
            "cropTop": 0,
            "cropBottom": 0,
            "cropLeft": 0,
            "cropRight": 0
        }
    )

    print("Set stretched to fit canvas.")
    logging.info(f"Set stretched to fit canvas with scale_x = {scale_x} and scale_y = {scale_y}")

def set_cursor(ms: int):
    if ms < 0:
        return
    CL.set_media_input_cursor("Set", ms)
    logging.info(f"Media cursor set to {ms} miliseconds.")

def restart_set():
    CL.set_media_input_cursor("Set", 0)
    logging.info("")

def archive_video():
    curr_video = os.path.join(f"{VIDEO_DIR}", f"{CURR_SET}.mp4")
    now = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    archived_video = os.path.join(f"{ARCHIVE_DIR}", f"{now}.mp4")
    shutil.move(curr_video, archived_video)
    logging.info(f"Current set archived under file {now}.mp4.")

async def download_video(url:str, name:str):
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
            # This is bad, it assumes the file wont have current_set anywhere else in the name. Refactor
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
        logging.error(f"Error downloading youtube video with URL {url}")
        print("Error downloading youtube video, are you sure that is a valid, visible URL?")
        #TODO: Actual error processing in case of invalid URL
        return
    logging.info(f"File {fname} successfully downloaded from url {url}.") 
    if has_first:
        VO.add_video(fname)
        VO.write()
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
    resize_video_obj()
    change_scene()
    logging.info(f"Set changed to {next_vid}.")

def pause_set():
    CL.trigger_media_input_action("Set", "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PAUSE")
    logging.info("Set paused.")

def resume_set():
    CL.trigger_media_input_action("Set", "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PLAY")
    logging.info("Set resumed.")

if __name__ == "__main__":
    # change_scene("TestBRB")
    # download_video("https://www.youtube.com/watch?v=Bjt7mDVCLtk", "testFile1")
    # download_video("https://www.youtube.com/watch?v=JP7zsdorPLI", "testFile2")
    # download_video("https://www.youtube.com/watch?v=TUzvD4XjBBo", "testFile3")
    # download_video("https://www.youtube.com/watch?v=8Bm3le9s3-A", "testFile4")
    # VO.write()
    # pause = input("Waiting...")
    # next_set()
    # VO.write()
    # pause = input("Waiting...")
    # next_set()
    # VO.write()
    # pause = input("Waiting...")
    # next_set()
    VO.write()
