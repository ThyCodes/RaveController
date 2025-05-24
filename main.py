import subprocess
import yt_dlp
import os

cur_dir = os.getcwd()
VIDEO_DIR = "bin/videos"
user_id="Test"
opts = {
    'format_sort': ["res:1080","ext:mp4:m4a"],
    "outtmpl": os.path.join(f"{cur_dir}/{VIDEO_DIR}", f"{user_id}.mp4")
}
ydl = yt_dlp.YoutubeDL(opts)
ydl.download("https://www.youtube.com/watch?v=pBIRk-JZoMg")