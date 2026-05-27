import yaml

def loadYaml():
    with open('bot-main/config.yaml', 'r') as config:
        content = yaml.safe_load(config)
    return content

def addUser(discordName, clashTag):
    if clashTag[0] != '#':
        clashTag = f'#{clashTag}'
    with open('bot-main/config.yaml', 'r') as config:
        content = yaml.safe_load(config)
        if content['clanMembers'] == None:
            content['clanMembers'] = dict()
        content['clanMembers'].update({clashTag: discordName})
    with open('bot-main/config.yaml', 'w') as config:
        yaml.safe_dump(content, config)

def setYaml(clantag, clashapiusername, clashapipassword, discordbottoken, discordchannel, discordguildid, discordowner, config_path='bot-main/config.yaml'):
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
    with open(config_path, 'w') as config:
        yaml.safe_dump(content, config)

def createConfig(clantag, clashapiusername, clashapipassword, discordbottoken, discordchannel, discordguildid, discordowner, config_path='bot-main/config.yaml'):
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
    with open(config_path, 'w') as config:
        yaml.safe_dump(content, config)

def loadAndUpdateAccounts(accounts):
    with open('bot-main/config.yaml', 'r') as config:
        content = yaml.safe_load(config)