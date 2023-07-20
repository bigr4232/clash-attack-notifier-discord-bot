import yaml
from account_link import account

def loadYaml(linkedAccounts):
    with open('bot-main/config.yaml', 'r') as config:
        content = yaml.safe_load(config)
        for member in content['clanMembers'].keys():
            newAccount = account(member)
            for clashid in content['clanMembers'][member]:
                newAccount.addClashTag(clashid)
            linkedAccounts.append(newAccount)
    return content

def addUser(discordName, clashTag, linkedAccounts):
    if clashTag[0] != '#':
        clashTag = f'#{clashTag}'
    with open('bot-main/config.yaml', 'r') as config:
        content = yaml.safe_load(config)
        if content['clanMembers'] == None:
            content['clanMembers'] = dict()
        alreadyContained = False
        for tag in content['clanMembers'][discordName]:
            if tag == clashTag:
                alreadyContained = True
                break
        if not alreadyContained:
            content['clanMembers'][discordName].append(clashTag)
        for disc in linkedAccounts:
            if discordName == disc.discordID:
                disc.addClashTag(clashTag)
                break
    with open('bot-main/config.yaml', 'w') as config:
        yaml.safe_dump(content, config)