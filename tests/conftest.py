"""
Shared fixtures and configuration for all tests.
"""
import pytest
import yaml
import os
import tempfile
import shutil


# Path constants
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOT_MAIN_DIR = os.path.join(ROOT_DIR, 'bot-main')
ORIGINAL_CONFIG_PATH = os.path.join(BOT_MAIN_DIR, 'config.yaml')


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory with a valid config.yaml for testing."""
    temp_dir = tempfile.mkdtemp()
    bot_main_temp = os.path.join(temp_dir, 'bot-main')
    os.makedirs(bot_main_temp)
    
    # Create a valid config.yaml
    config_content = {
        'clanTag': '#TESTCLAN',
        'clashAPIUsername': 'test_user',
        'clashAPIPassword': 'test_pass',
        'discordBotToken': 'test_token',
        'discordChannel': '123456789',
        'discordGuildID': '987654321',
        'discordOwnerID': '111222333',
        'clanMembers': None
    }
    
    config_path = os.path.join(bot_main_temp, 'config.yaml')
    with open(config_path, 'w') as f:
        yaml.safe_dump(config_content, f)
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_config_with_members():
    """Create a temporary directory with config.yaml containing clan members."""
    temp_dir = tempfile.mkdtemp()
    bot_main_temp = os.path.join(temp_dir, 'bot-main')
    os.makedirs(bot_main_temp)
    
    config_content = {
        'clanTag': '#TESTCLAN',
        'clashAPIUsername': 'test_user',
        'clashAPIPassword': 'test_pass',
        'discordBotToken': 'test_token',
        'discordChannel': '123456789',
        'discordGuildID': '987654321',
        'discordOwnerID': '111222333',
        'clanMembers': {
            '#TAG1': 1000000001,
            '#TAG2': 1000000002
        }
    }
    
    config_path = os.path.join(bot_main_temp, 'config.yaml')
    with open(config_path, 'w') as f:
        yaml.safe_dump(config_content, f)
    
    yield temp_dir, config_content
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def original_config_backup():
    """Backup and restore the original config.yaml after tests that modify it."""
    if os.path.exists(ORIGINAL_CONFIG_PATH):
        with open(ORIGINAL_CONFIG_PATH, 'r') as f:
            backup = f.read()
    else:
        backup = None
    
    yield
    
    # Restore original config
    if backup is not None:
        with open(ORIGINAL_CONFIG_PATH, 'w') as f:
            f.write(backup)


@pytest.fixture
def sample_config_content():
    """Return a standard config content dict for testing."""
    return {
        'clanTag': '#TESTCLAN',
        'clashAPIUsername': 'test_user',
        'clashAPIPassword': 'test_pass',
        'discordBotToken': 'test_token',
        'discordChannel': '123456789',
        'discordGuildID': '987654321',
        'discordOwnerID': '111222333',
        'clanMembers': None
    }