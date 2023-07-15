import coc
from coc import utils
import asyncio
import discord
import config_loader

players = list()
clan_tags = list()

# Intents and tree inits
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
managers = {}

# Event for new war start. Will start the war attack notifier
@coc.WarEvents.new_war(tags=clan_tags)
async def new_war(war):
    print('new war registered')
    content = config_loader.loadYaml()
    for member in war.members:
        if member.clan.tag == content['discordChannel']:
            players.append(member)
    war_notifier(war)

# Event for war attack. Updates list of players who haven't attacked
@coc.WarEvents.war_attack(tags=clan_tags)
async def war_attack(attack, war):
    print('attack registerd')
    print(f'attack by: {attack.attacker}')
    print(f'total attacks: {len(attack.attacker.attacks)}')
    print(f'war attacks total: {war.attacks_per_member}')
    for member in players:
        if member == attack.attacker:
            if len(member.attacks) == war.attacks_per_member:
                players.remove(member)
    
# Sends notifications to players who haven't attacked at each interval
async def war_notifier(war):
    async with coc.Client() as cc:
        if war.state != 'inWar':
            asyncio.sleep(86400)
        war = await cc.get_current_war(clan_tags[0])
        asyncio.sleep(war.end_time.seconds_until - 68400)
        for member in players:
            print('5 hours left')
        war = await cc.get_current_war(clan_tags[0])
        asyncio.sleep(war.end_time.seconds_until - 7200)
        for member in players:
            print('3 hours left')
        war = await cc.get_current_war(clan_tags[0])
        asyncio.sleep(war.end_time.seconds_until - 3600)
        for member in players:
            print('1 and a half hours left')
        war = await cc.get_current_war(clan_tags[0])
        asyncio.sleep(war.end_time.seconds_until - 2400)
        for member in players:
            print('1 hour left')
        war = await cc.get_current_war(clan_tags[0])
        asyncio.sleep(war.end_time.seconds_until - 1200)
        for member in players:
            print('30 minutes left')
        war = await cc.get_current_war(clan_tags[0])
        asyncio.sleep(war.end_time.seconds_until - 600)
        for member in players:
            print('15 minutes left')

# Bot init
@bot.event
async def on_ready():
    print("connected")

# coc API init
async def main():
    async with coc.EventsClient() as coc_client:
        content = config_loader.loadYaml()
        try:
            await coc_client.login_with_tokens(content['clashToken'])
        except coc.InvalidCredentials as error:
            exit(error)
        coc_client.add_clan_updates(*clan_tags)
        coc_client.add_war_updates(*clan_tags)
        coc_client.add_events(
            new_war,
            war_attack
        )
        clan_tags.append(content['clanTag'])

        # Add the client session to the bot
        bot.coc_client = coc_client
        await bot.start(content['discordBotToken'])


if __name__ == "__main__":
    asyncio.run(main())