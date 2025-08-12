import obs_controller
import bot_interface
import configparser
import re


# NOTE
# THIS BOT *TECHNICALLY* VIOLATES DISCORD TOS BECAUSE OF HOW IT INTERACTS WITH YOUTUBE VIDEOS
# ONLY USE ON YOUTUBE VIDEOS WHERE THE UPLOADER HAS GIVEN EXPRESS PERMISSION

config = configparser.ConfigParser()
config.read("config.toml")
if __name__ == "__main__":
    token = re.sub(r"\"", "", config["DEFAULT"]["token"])
    bot_interface.run(token)
