class accountLink:

    def __init__(self, discordID):
        self.discordID = discordID
        self.tags = set()
        self.numAttacks = 0
        self.numAttackChances = 0

    def __hash__(self) -> int:
        return hash(self.discordID)
    
    def __eq__(self, other) -> bool:
        return self.name == other.name
    
    def addClashTag(self, tag):
        self.tags.update(tag)