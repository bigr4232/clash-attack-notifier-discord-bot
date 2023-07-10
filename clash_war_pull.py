import coc
from coc import utils
import asyncio
import keys as k
import discord

players = list()
clan_tags = [***REMOVED***]

# Intents and tree inits
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
managers = {}

@coc.WarEvents.new_war(tags=clan_tags)
async def new_war(war):
    print('new war registered')
    for member in war.members:
        if member.clan.tag == k.nattydaddytag:
            players.append(member)
    war_notifier()

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
    
    
async def war_notifier():
    asyncio.sleep(68400)
    for member in players:
        print('5 hours left')
    asyncio.sleep(7200) #75600
    for member in players:
        print('3 hours left')
    asyncio.sleep(3600)
    for member in players:
        print('1 and a half hours left')
    asyncio.sleep(2400)
    for member in players:
        print('1 hour left')
    asyncio.sleep(1200)
    for member in players:
        print('30 minutes left')
    asyncio.sleep(600)
    for member in players:
        print('15 minutes left')

# Initialization
@bot.event
async def on_ready():
    print("connected")


async def main():
    async with coc.EventsClient() as coc_client:
        # Attempt to log into CoC API using your credentials.
        try:
            await coc_client.login_with_tokens(k.token)
        except coc.InvalidCredentials as error:
            exit(error)
        coc_client.add_clan_updates(*clan_tags)
        coc_client.add_war_updates(*clan_tags)
        coc_client.add_events(
            new_war,
            war_attack
        )

        # Add the client session to the bot
        bot.coc_client = coc_client
        await bot.start(k.RyanTestBotToken)


if __name__ == "__main__":
    asyncio.run(main())