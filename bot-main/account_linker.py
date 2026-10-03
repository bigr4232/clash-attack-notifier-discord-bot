import logging
import coc
import config_loader

logger = logging.getLogger('logs')

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
    
    # Highest role across this user's accounts in the bot's clan: 4 leader, 3 co-leader, 2 elder, 1 member, 0 not in clan
    async def updateRole(self, cc):
        roleRanks = {'leader': 4, 'co_leader': 3, 'elder': 2, 'member': 1}
        highestRole = 0
        for tag in list(self.tags):
            try:
                player = await cc.get_player(player_tag=tag)
            except coc.NotFound:
                logger.warning(f'Clash account {tag} claimed by {self.discordID} was not found, skipping it')
                continue
            # Accounts outside the bot's clan don't count
            if player.clan is None or player.role is None or player.clan.tag != content['clanTag']:
                continue
            highestRole = max(highestRole, roleRanks.get(player.role.name, 1))
        return highestRole

def updateAccounts():
    # Reload from disk so accounts claimed after startup are picked up
    global content
    content = config_loader.loadYaml()
    clanMembers = content.get('clanMembers') or {}
    for clashid in clanMembers.keys():
        discord_id = clanMembers[clashid]
        existing = discordTagMapping.get(discord_id)
        if existing:
            existing.addClashTagTarget(clashid, [])
            clashTagMapping[clashid] = existing
        else:
            acc = accountLink(discordID=discord_id)
            acc.addClashTagTarget(clashid, [])
            discordAccounts.add(acc)
            clashTagMapping[clashid] = acc
            discordTagMapping[discord_id] = acc

updateAccounts()