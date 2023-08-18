import config_loader

clashTagMapping = dict()
discordTagMapping = dict()
discordAccounts = set()
content = config_loader.loadYaml()
class accountLink:
    def __init__(self, discordID):
        self.discordID = discordID
        self.tags = dict()
        self.numAttacks = 0
        self.numAttackChances = 0
        self.finishedAttacks = False
        self.clashRole = 'member'

    def __hash__(self):
        return hash(self.discordID)
    
    def __eq__(self, other):
        return self.discordID == other.discordID
    
    def addClashTagTarget(self, tag, target):
        if tag not in self.tags:
            self.tags.update({tag:target})


def updateAccounts():
    for clashid in content['clanMembers'].keys():
        acc = accountLink(discordID=content['clanMembers'][clashid])
        if acc in discordAccounts:
            discordTagMapping[content['clanMembers'][clashid]].addClashTagTarget(clashid, [])
            discordAccounts.add(acc)
            clashTagMapping.update({clashid:acc})
        else:
            acc.addClashTagTarget(clashid, [])
            discordAccounts.add(acc)
            clashTagMapping.update({clashid:acc})
            discordTagMapping.update({content['clanMembers'][clashid]:acc})

updateAccounts()