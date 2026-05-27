import os
import yaml

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yaml')

def _getConfigPath(path=None):
    return path or _CONFIG_PATH

def loadYaml():
    with open(_CONFIG_PATH, 'r') as config:
        content = yaml.safe_load(config)
    return content

def addUser(discordName, clashTag):
    if clashTag[0] != '#':
        clashTag = f'#{clashTag}'
    with open(_CONFIG_PATH, 'r') as config:
        content = yaml.safe_load(config)
        if content['clanMembers'] == None:
            content['clanMembers'] = dict()
        content['clanMembers'].update({clashTag: discordName})
    with open(_CONFIG_PATH, 'w') as config:
        yaml.safe_dump(content, config)

def setYaml(clantag, clashapiusername, clashapipassword, discordbottoken, discordchannel, discordguildid, discordowner, config_path=None):
    content = loadYaml()
    if clantag[0] != '#':
        clantag = f'#{clantag}'
    content['clanTag'] = clantag
    content['clashAPIUsername'] = clashapiusername
    content['clashAPIPassword'] = clashapipassword
    content['discordBotToken'] = discordbottoken
    content['discordChannel'] = discordchannel
    content['discordGuildID'] = discordguildid
    content['discordOwnerID'] = discordowner
    with open(_getConfigPath(config_path), 'w') as config:
        yaml.safe_dump(content, config)

def createConfig(clantag, clashapiusername, clashapipassword, discordbottoken, discordchannel, discordguildid, discordowner, config_path=None):
    if clantag[0] != '#':
        clantag = f'#{clantag}'
    content = {
        'clanTag': clantag,
        'clashAPIUsername': clashapiusername,
        'clashAPIPassword': clashapipassword,
        'discordBotToken': discordbottoken,
        'discordChannel': discordchannel,
        'discordGuildID': discordguildid,
        'discordOwnerID': discordowner,
        'clanMembers': {}
    }
    with open(_getConfigPath(config_path), 'w') as config:
        yaml.safe_dump(content, config)

def loadAndUpdateAccounts(accounts):
    with open(_CONFIG_PATH, 'r') as config:
        content = yaml.safe_load(config)