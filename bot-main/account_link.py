class account:
    def __init__(self, discordID):
        self.discordID = discordID
        self.clashTags = set()

    def addClashTag(self, clashTag):
        self.clashTags.add(clashTag)

    