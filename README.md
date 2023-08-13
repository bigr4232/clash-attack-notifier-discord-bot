# Clash Attack Notifier

Discord Bot that will notify members in clan when war starts and if they haven't attacked.

Notification intervals are set in the bot-main file.

## Installation

Use updater.py to install or update. It will not overwrite your config file if one is already present.

You are required to specify an install directory using the -dir arg.

python updater.py -dir [directory]

Follow prompts to fill in inital config.

## Usage

Start up using python on bot-main.py or provided docker-compose. -d arg availabled for additional console logs
as well as logs to a file.

Users will need to add themselves to the bot and connect their clash tag.

/claimaccount [clashtag]
