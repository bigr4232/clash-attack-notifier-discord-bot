import sys
import os
import logging
import time
import shutil
from file_exceptions import *

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bot-main'))
from config_loader import createConfig

class LocalTimeFormatter(logging.Formatter):
    converter = time.localtime

formatter = LocalTimeFormatter('%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger = logging.getLogger('logs')
logger.setLevel(logging.INFO)
logger.addHandler(stream_handler)

def updateYaml(config_path):
    clantag = input('Enter clan tag for clan to track: ')
    clashapiusername = input('Enter your clash of clans api username: ')
    clashapipassword = input('Enter your clash of clans api password: ')
    discordbottoken = input('Enter the token for the discord bot to use: ')
    discordchannel = input('Enter the id for the default war channel for the bot: ')
    discordguildid = input('Enter the id of the server/guild that the bot will be in: ')
    discordownerid = input('Enter the discord id of the bot owner for admin commands: ')
    createConfig(clantag, clashapiusername, clashapipassword, discordbottoken, discordchannel, discordguildid, discordownerid, config_path)

def updateFiles(dst):
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    dst = os.path.join(ROOT_DIR, dst)
    botPath = os.path.join(dst, 'bot-main')
    if not os.path.exists(botPath):
        os.makedirs(botPath)
    # Sources are resolved against this file, not the shell's working directory,
    # so the updater can be run from anywhere
    shutil.copy(os.path.join(ROOT_DIR, 'bot-main', 'clash_war_pull.py'), os.path.join(botPath, 'clash_war_pull.py'))
    shutil.copy(os.path.join(ROOT_DIR, 'bot-main', 'account_linker.py'), os.path.join(botPath, 'account_linker.py'))
    shutil.copy(os.path.join(ROOT_DIR, 'bot-main', 'config_loader.py'), os.path.join(botPath, 'config_loader.py'))
    shutil.copy(os.path.join(ROOT_DIR, 'docker-compose.yml'), os.path.join(dst, 'docker-compose.yml'))
    shutil.copy(os.path.join(ROOT_DIR, 'Dockerfile'), os.path.join(dst, 'Dockerfile'))
    shutil.copy(os.path.join(ROOT_DIR, 'requirements.txt'), os.path.join(dst, 'requirements.txt'))
    configPath = os.path.join(botPath, 'config.yaml')
    # Docker creates an empty directory at a bind mount target that has no file to
    # bind to. Clear it so the config is a real file the container can read and write.
    if os.path.isdir(configPath):
        logger.info('config.yaml is a directory left behind by a bind mount, replacing it with a config file')
        os.rmdir(configPath)
    if not os.path.exists(configPath):
        updateYaml(configPath)

def main():
    logger.info('Updating files to version in this folder')

    # Error checker
    directoryFlagIsPresent = False
    directoryIsPresent = False
    for i in range(len(sys.argv)):
        if sys.argv[i] == '-dir':
            directoryFlagIsPresent = True
            if len(sys.argv) > i + 1 and sys.argv[i+1][0] != '-':
                directoryIsPresent = True
    if not directoryFlagIsPresent:
        raise MissingDirArg()
    if not directoryIsPresent:
        raise NoPathException()
    
    # Run updater
    for i in range(len(sys.argv)):
        if sys.argv[i] == '-dir' and len(sys.argv) >= i+1:
            dst = sys.argv[i+1]
    updateFiles(dst)
    logger.info('Update complete')

if __name__ == "__main__":
    main()