import coc
import asyncio
import discord
from discord import app_commands
import config_loader
from math import floor
import logging

# Globals
players = list()
clan_tags = list()
content = config_loader.loadYaml()

logger = logging.getLogger('logs')
logger.setLevel(logging.DEBUG)
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

# Intents and tree inits
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
managers = {}
tree = app_commands.CommandTree(bot)

# begin calling search for war
async def startWarSearch(cc):
    while True:
        await new_war(cc)
        await asyncio.sleep(600)
        logger.debug('Checking war status')

# not coc api event based search for war
async def new_war(cc):
    war = await cc.get_current_war(content['clanTag'])
    if war.state == 'inWar':
        logger.debug('adding players to list')
        players.clear()
        for member in war.members:
            if member.clan.tag == content['clanTag']:
                players.append(member)
        logger.debug('starting notifier')
        await war_notifier(war, cc)

# Event for new war start. Will start the war attack notifier
#@coc.WarEvents.new_war(tags=clan_tags)
#async def new_war(war):
#    logger.info('new war registered')
#    players.clear()
#    for member in war.members:
#        if member.clan.tag == content['clanTag']:
#            players.append(member)
#    await war_notifier(war)


# Remove users who have attacked from players list
async def removeFinishedAttackers(cc):
    logger.debug('remove users who have attacked')
    war = await cc.get_current_war(content['clanTag'])
    for p in war.members:
        if p.clan.tag == content['clanTag']:
            if len(p.attacks) == war.attacks_per_member:
                players.remove(p)

# Return time in hour/min/sec as string from sec
async def returnTime(seconds):
    minutes = floor(seconds / 60)
    seconds -= minutes * 60
    hours = floor(minutes / 60)
    minutes -= hours * 60
    remainingTime = ''
    if hours > 0:
        remainingTime += str(hours) + ' hours '
    if minutes > 0:
        remainingTime += str(minutes) + ' minutes '
    if seconds > 0:
        remainingTime += str(seconds) + ' seconds '
    remainingTime += 'remaining '
    logger.debug(f'time: {remainingTime}')
    return remainingTime

# Update the players list and notify users that haven't attacked
# wait in asyncio.sleep for amount of time passed in
async def updateAndNotify(cc, time):
    logger.debug(f'notify with time {time}')
    await removeFinishedAttackers(cc)
    remainingTime = await returnTime(time)
    notifiedPlayers = set()
    logger.debug('send notifications')
    for member in players:
        for claimedMember in content['clanMembers'].keys():
            if member.tag == claimedMember and content['clanMembers'][claimedMember] not in notifiedPlayers:
                notifyUser(content['clanMembers'][claimedMember], remainingTime)
                notifiedPlayers.add(content['clanMembers'][claimedMember])
    notifiedPlayers.clear()
    logger.debug('waiting till next notification interval')
    war = await cc.get_current_war(clan_tags[0])
    await asyncio.sleep(war.end_time.seconds_until - time)

# Sends notifications to players who haven't attacked at each interval
async def war_notifier(war, cc):
    notificationIntervals = [7200, 3600, 2400, 1200, 600]
    #if war.state != 'inWar':
    #    asyncio.sleep(war.end_time.seconds_until + 500)
    #war = await cc.get_current_war(clan_tags[0])
    logger.debug('initial countdown to 5 hours')
    await asyncio.sleep(war.end_time.seconds_until - 18000)
    for time in notificationIntervals:
        await updateAndNotify(cc, time)
    await asyncio.sleep(2400)
    await startWarSearch(cc)
    

# Command to claim clash account. With no input of username, will use discord name from command issuer
@tree.command(name='claimaccount', description='claim clash account with tag and discord name', guild=discord.Object(id=int(content['discordGuildID'])))
async def claimAccountCommand(ctx: discord.Interaction, clashtag:str):
    await ctx.response.send_message(f"Claiming account {clashtag} for {ctx.user.name}", delete_after=300)
    config_loader.addUser(ctx.user.id, clashtag)
    global content
    content = config_loader.loadYaml()

# Command to sync new slash commands
@tree.command(name='sync-commands', description='command to sync new slash commands', guild=discord.Object(id=int(content['discordGuildID'])))
async def syncCommands(ctx: discord.Interaction):
    if ctx.user.id == int(content['discordOwnerID']):
        await ctx.response.send_message('Commands synced', delete_after=30)
        await tree.sync(guild=discord.Object(id=int(content['discordGuildID'])))
    else:
        await ctx.response.send_message('This command is only for the server owner', delete_after=30)

# Send dm to user to get attack in
@bot.event
async def notifyUser(userid:int, remainingtime:str):
    user = await bot.fetch_user(userid)
    await user.send(f'{remainingtime} to get attack in')

# Bot init
@bot.event
async def on_ready():
    logger.info('bot ready')
    await startWarSearch(bot.coc_client)

# coc API init
async def main():
    async with coc.Client() as coc_client:
        try:
            await coc_client.login_with_tokens(content['clashToken'])
        except coc.InvalidCredentials as error:
            exit(error)
        #coc_client.add_clan_updates(*clan_tags)
        #coc_client.add_war_updates(*clan_tags)
        #coc_client.add_events(
        #    new_war,
        #)
        #clan_tags.append(content['clanTag'])

        # Add the client session to the bot
        bot.coc_client = coc_client
        await bot.start(content['discordBotToken'])

# Main to run main repeatedly with asyncio
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass