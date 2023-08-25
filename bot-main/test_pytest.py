import pytest
import config_loader
import clash_war_pull
import asyncio



def testYamlLoad():
    config_loader.loadYaml()

def testAddUserYaml():
    config_loader.addUser('testuser1', '41932832')
    config_loader.addUser('testUser123', '#48912034')
    config_loader.addUser('testuser5', '41932832')

@pytest.mark.asyncio
async def testNotify():
    print()
    await clash_war_pull.notifyUser(userid=186200408492867584, remainingtime="test1234")

@pytest.mark.asyncio
def testTime():
    clash_war_pull.returnTime(59*60 + 59)