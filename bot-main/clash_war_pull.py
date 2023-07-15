import coc
import asyncio
import discord
from discord import app_commands
import config_loader

players = list()
clan_tags = list()
initContent = config_loader.loadYaml()

# Intents and tree inits
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
managers = {}
tree = app_commands.CommandTree(bot)

# Event for new war start. Will start the war attack notifier
@coc.WarEvents.new_war(tags=clan_tags)
async def new_war(war):
    print('new war registered')
    for member in war.members:
        if member.clan.tag == int(initContent['discordChannel']):
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
        content = config_loader.loadYaml()
        for member in players:
            print('5 hours left')
        war = await cc.get_current_war(clan_tags[0])
        asyncio.sleep(war.end_time.seconds_until - 7200)
        content = config_loader.loadYaml()
        for member in players:
            print('3 hours left')
        war = await cc.get_current_war(clan_tags[0])
        asyncio.sleep(war.end_time.seconds_until - 3600)
        content = config_loader.loadYaml()
        for member in players:
            print('1 hour 30 minutes left')
        war = await cc.get_current_war(clan_tags[0])
        asyncio.sleep(war.end_time.seconds_until - 2400)
        content = config_loader.loadYaml()
        for member in players:
            print('1 hour left')
        war = await cc.get_current_war(clan_tags[0])
        asyncio.sleep(war.end_time.seconds_until - 1200)
        content = config_loader.loadYaml()
        for member in players:
            print('30 minutes left')
        war = await cc.get_current_war(clan_tags[0])
        asyncio.sleep(war.end_time.seconds_until - 600)
        content = config_loader.loadYaml()
        for member in players:
            print('15 minutes left')

@tree.command(name='claimaccount', description='claim clash account with tag and discord name', guild=discord.Object(id=int(initContent['discordGuildID'])))
async def claimAccountCommand(ctx: discord.Interaction, clashtag:str, discordusername:str=''):
    await ctx.response.send_message("message")
    if discordusername != '':
        config_loader.addUser(discordusername, clashtag)
    else:
        config_loader.addUser(ctx.user.name, clashtag)
    

# Bot init
@bot.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=int(initContent['discordGuildID'])))
    print("synced commands")

# coc API init
async def main():
    async with coc.EventsClient() as coc_client:
        try:
            await coc_client.login_with_tokens(initContent['clashToken'])
        except coc.InvalidCredentials as error:
            exit(error)
        coc_client.add_clan_updates(*clan_tags)
        coc_client.add_war_updates(*clan_tags)
        coc_client.add_events(
            new_war,
            war_attack
        )
        clan_tags.append(initContent['clanTag'])

        # Add the client session to the bot
        bot.coc_client = coc_client
        await bot.start(initContent['discordBotToken'])


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass