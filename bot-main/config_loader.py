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