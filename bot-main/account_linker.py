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
    
    async def updateRole(self, cc):
        highestRole = 0
        for tag in self.tags:
            player = await cc.get_player(player_tag=tag)
            if player.role.name == 'leader':
                return 4
            elif player.role.name == 'co_leader':
                highestRole = 3
            elif player.role.name == 'elder' and highestRole < 2:
                highestRole = 2
            else:
                highestRole = 1
        return highestRole

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