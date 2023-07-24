import coc
import asyncio
import discord
from discord import app_commands
import config_loader
from math import floor
import logging

# Globals
playersMissingAttacks = set()
clan_tags = list()
content = config_loader.loadYaml()

logger = logging.getLogger('logs')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('logs.log')
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)
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
        logger.debug('Checking war status')
        await new_war_prep(cc)
        await asyncio.sleep(600)

# Runs on prep day, calls start if cwl
async def new_war_prep(cc):
    war = await cc.get_current_war(content['clanTag'])
    if war.state == 'preparation':
        logger.debug('In preparation')
        while True:
            await asyncio.sleep(war.end_time.seconds_until - 86400)
            await new_war_start(cc)
            war = await cc.get_current_war(content['clanTag'])
    elif war.state == 'inWar':
        await new_war_start(cc)

# Runs on war day
async def new_war_start(cc):
    war = await cc.get_current_war(content['clanTag'])
    if war.state == 'inWar':
        numAttacks = str(war.attacks_per_member)
        logger.debug('adding players to list')
        playersMissingAttacks.clear()
        notifiedPlayers = set()
        notifiedPlayers.clear()
        for member in war.members:
            if member.clan.tag == content['clanTag']:
                playersMissingAttacks.add(member.tag)
                for discMember in content['clanMembers'].keys():
                    if discMember == member.tag and content['clanMembers'][member.tag] not in notifiedPlayers:
                        await notifyUserStart(content['clanMembers'][discMember], numAttacks)
                        notifiedPlayers.add(content['clanMembers'][member.tag])
        logger.debug('starting notifier')
        await war_notifier(war, cc)

# Remove users who have attacked from players list
async def removeFinishedAttackers(cc):
    logger.debug('remove users who have attacked')
    war = await cc.get_current_war(content['clanTag'])
    for p in war.members:
        if p.clan.tag == content['clanTag']:
            if len(p.attacks) == war.attacks_per_member:
                playersMissingAttacks.discard(p.tag)
                logger.debug(f'Removing {p}')

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
async def updateAndNotify(cc, time, timeLeft):
    logger.debug(f'notify with time {timeLeft}')
    await removeFinishedAttackers(cc)
    remainingTime = await returnTime(timeLeft)
    notifiedPlayers = set()
    logger.debug('send notifications')
    for tag in playersMissingAttacks:
        for claimedMember in content['clanMembers'].keys():
            if tag == claimedMember and content['clanMembers'][claimedMember] not in notifiedPlayers:
                await notifyUserAttackTime(content['clanMembers'][claimedMember], remainingTime)
                notifiedPlayers.add(content['clanMembers'][claimedMember])
    notifiedPlayers.clear()
    logger.debug('waiting till next notification interval')
    war = await cc.get_current_war(content['clanTag'])
    if war.end_time.seconds_until - time >= 0:
        await asyncio.sleep(war.end_time.seconds_until - time)
    war = await cc.get_current_war(content['clanTag'])
    timeLeft = war.end_time.seconds_until
    return timeLeft

# Sends notifications to players who haven't attacked at each interval
async def war_notifier(war, cc):
    notificationIntervals = [43200, 18000, 10800, 3600, 1800, 900]
    logger.debug('initial countdown to 12 hours')
    if war.end_time.seconds_until - notificationIntervals[0] >= 0:
        await asyncio.sleep(war.end_time.seconds_until - notificationIntervals[0])
    actualTime = war.end_time.seconds_until
    for time in notificationIntervals[1:]:
        actualTime = await updateAndNotify(cc, time, actualTime)
    await asyncio.sleep(900)
    war = await cc.get_current_war(content['clanTag'])
    timeleft = war.end_time.seconds_until
    while war.state == 'inWar' and timeleft <= actualTime:
        war = await cc.get_current_war(content['clanTag'])
        timeleft = war.end_time.seconds_until
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

# Send dm to user that war has started
@bot.event
async def notifyUserStart(userid:int, numattacks:str):
    user = await bot.fetch_user(userid)
    await user.send(f'War has started in you are in it. You have 24 hours to attack')
    logger.debug(f'notified {user.name} war has started')

# Send dm to user to get attack in
@bot.event
async def notifyUserAttackTime(userid:int, remainingtime:str):
    user = await bot.fetch_user(userid)
    await user.send(f'{remainingtime} to get attack in')
    logger.debug(f'notified {user.name} to get attack in')

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

        # Add the client session to the bot
        bot.coc_client = coc_client
        await bot.start(content['discordBotToken'])

# Main to run main repeatedly with asyncio
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass