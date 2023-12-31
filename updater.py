import sys
import os
import logging
import shutil
from file_exceptions import *

sys.path.append('bot-main')
from config_loader import setYaml

logger = logging.getLogger('logs')
logger.setLevel(logging.INFO)

def updateYaml():
    clantag = input('Enter clan tag for clan to track: ')
    clashtoken = input('Enter your clash of clans api token: ')
    discordbottoken = input('Enter the token for the discord bot to use: ')
    discordchannel = input('Enter the id for the default war channel for the bot: ')
    discordguildid = input('Enter the id of the server/guild that the bot will be in: ')
    discordownerid = input('Enter the discord id of the bot owner for admin commands: ')
    setYaml(clantag, clashtoken, discordbottoken, discordchannel, discordguildid, discordownerid)

def updateFiles(dst):
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    dst = os.path.join(ROOT_DIR, dst)
    botPath = os.path.join(dst, 'bot-main')
    if not os.path.exists(botPath):
        os.makedirs(botPath)
    shutil.copy(os.path.abspath('bot-main/clash_war_pull.py'), os.path.join(botPath, 'clash_war_pull.py'))
    shutil.copy(os.path.abspath('bot-main/account_linker.py'), os.path.join(botPath, 'account_linker.py'))
    shutil.copy('bot-main/config_loader.py', os.path.join(botPath, 'config_loader.py'))
    shutil.copy('docker-compose.yml', os.path.join(dst, 'docker-compose.yml'))
    shutil.copy('Dockerfile', os.path.join(dst, 'Dockerfile'))
    shutil.copy('requirements.txt', os.path.join(dst, 'requirements.txt'))
    if not os.path.exists(dst + '/bot-main/config.yaml'):
        updateYaml()
        shutil.copy('bot-main/config.yaml', os.path.join(botPath, 'config.yaml'))

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
    if dst[:0] == '/' or dst[:0] == '\\':
        dst = dst[:-1]
    updateFiles(dst)
    logger.info('Update complete')

if __name__ == "__main__":
    main()