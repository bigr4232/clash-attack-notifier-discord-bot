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

def setYaml(clantag, clashtoken, discordbottoken, discordchannel, discordguildid, discordowner):
    content = loadYaml()
    if clantag[0] != '#':
        clantag = f'#{clantag}'
    content['clanTag'] = clantag
    content['clashToken'] = clashtoken
    content['discordBotToken'] = discordbottoken
    content['discordChannel'] = discordchannel
    content['discordGuildID'] = discordguildid
    content['discordOwnerID'] = discordowner
    with open('bot-main/config.yaml', 'w') as config:
        yaml.safe_dump(content, config)

def loadAndUpdateAccounts(accounts):
    with open('bot-main/config.yaml', 'r') as config:
        content = yaml.safe_load(config)