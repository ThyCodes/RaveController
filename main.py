import obs_controller
import bot_interface
import configparser
import re


config = configparser.ConfigParser()
config.read("config.toml")
if __name__ == "__main__":
    token = re.sub(r"\"", "", config["DEFAULT"]["token"])
    bot_interface.run(token)
