import pytest
import config_loader



def testYamlLoad():
    config_loader.loadYaml()

def testAddUserYaml():
    config_loader.addUser('testuser1', '41932832')
    config_loader.addUser('testUser123', '#48912034')
    config_loader.addUser('testuser5', '41932832')