import coc
import asyncio
import discord
from discord import app_commands
import config_loader
from math import floor
import logging
import aiohttp.client_exceptions
import sys
from account_linker import discordTagMapping, clashTagMapping, updateAccounts
import time

# Globals
__version__ = '1.1.22'
playersMissingAttacks = set()
clan_tags = list()
content = config_loader.loadYaml()
updateAccounts()
availableRoles = {'leader', 'co-leader', 'elder', 'member', 'not-in-clan'}
roles = {'leader':0, 'co-leader':0, 'elder':0, 'member':0, 'not-in-clan':0}
# Wars that already had their "war has started" DMs handled, and reminders already sent, keyed by warKey()
startNotifiedWars = set()
sentReminders = set()

# Background task handles, kept so the tasks aren't garbage-collected and can be restarted
background_tasks = {}

debugMode = False
silentMode = False
syncCommandsOnStart = False
# Logging
class LocalTimeFormatter(logging.Formatter):
    converter = time.localtime

formatter = LocalTimeFormatter('%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger = logging.getLogger('logs')
for arg in sys.argv:
    if arg == '-d':
        logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler('logs.log')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        debugMode = True
    if arg == '--silent':
        silentMode = True
    if arg == '--sync':
        syncCommandsOnStart = True
if not debugMode:
    logger.setLevel(logging.INFO)
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(stream_handler)
logger.addHandler(stream_handler)
logger.propagate = False

# Intents and tree inits
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.moderation = True
bot = discord.Client(intents=intents)
managers = {}
tree = app_commands.CommandTree(bot)

# Begin calling search for war
async def startWarSearch(cc):
    logger.info('Starting war notifier')
    firstRun = True
    while True:
        try:
            logger.debug('Checking war status')
            await new_war_prep(cc, firstRun)
            firstRun = False
            logger.debug('Checking again in 10 minutes')
            await asyncio.sleep(600)
        except Exception as e:
            logger.error(f'War search task crashed unexpectedly: {e}. Restarting in 30s.', exc_info=True)
            await asyncio.sleep(30)

# Identifies a war across API fetches
def warKey(war):
    return (content['clanTag'], war.start_time.raw_time)

# Fetch the current war, retrying transient API/network errors before giving up
async def fetchWarWithRetry(cc, attempts=10, delay=30):
    for attempt in range(1, attempts + 1):
        try:
            return await cc.get_current_war(content['clanTag'])
        except Exception as e:
            if attempt == attempts:
                raise
            logger.warning(f'Failed to fetch current war (attempt {attempt}/{attempts}): {e}. Retrying in {delay}s.')
            await asyncio.sleep(delay)

# Runs on prep day, calls start if cwl
async def new_war_prep(cc, firstRun):
    try:
        war = await cc.get_current_war(content['clanTag'])
        if war == None:
            return
        if war.state == 'preparation':
            logger.debug('In preparation')
            # Wait for battle day. Sleep at least 30s per pass so short wars or clock skew can't busy-loop the API
            while war is not None and war.state == 'preparation':
                await asyncio.sleep(max(30, war.start_time.seconds_until))
                war = await cc.get_current_war(content['clanTag'])
            if war is not None and war.state == 'inWar':
                # The bot was running before battle day began, so start DMs should go out
                await new_war_start(cc, war, False)
        elif war.state == 'inWar':
            await new_war_start(cc, war, firstRun)
    except coc.Maintenance:
        logger.warning('CoC API under maintenance - waiting for recovery')
        await asyncio.sleep(300)
        return
    except coc.GatewayError:
        logger.warning('Gateway error - waiting for recovery')
        await asyncio.sleep(300)
        return
    except aiohttp.client_exceptions.ClientConnectorDNSError as e:
        logger.warning(f'DNS resolution failed: {e}. Waiting 60s before retry.')
        await asyncio.sleep(60)
        return
    except aiohttp.client_exceptions.ClientConnectorError as e:
        logger.warning(f'Connection error: {e}. Waiting 30s before retry.')
        await asyncio.sleep(30)
        return

# Runs on war day
async def new_war_start(cc, war, firstRun):
    key = warKey(war)
    numAttacks = str(war.attacks_per_member)
    # DM "war has started" once per war, only in the first hour, and not if the bot came up mid-war
    sendStartDMs = key not in startNotifiedWars and not firstRun and war.end_time.seconds_until > 82800
    startNotifiedWars.add(key)
    timeleft = returnTime(war.end_time.seconds_until)
    logger.debug('adding players to list')
    playersMissingAttacks.clear()
    notifiedPlayers = set()
    for member in war.members:
        if member.clan.tag == content['clanTag']:
            playersMissingAttacks.add(member.tag)
            acc = clashTagMapping.get(member.tag)  # O(1) lookup instead of O(M) inner loop
            if acc and acc not in notifiedPlayers:
                if sendStartDMs:
                    await notifyUserStart(acc.discordID, numAttacks, timeleft)
                notifiedPlayers.add(acc)
    logger.debug('starting notifier')
    await war_notifier(war, cc)

# Remove users who have attacked from players list
async def removeFinishedAttackers(cc, war=None):
    logger.debug('remove users who have attacked')
    if war is None:
        war = await cc.get_current_war(content['clanTag'])
    for p in war.members:
        if p.clan.tag == content['clanTag']:
            if len(p.attacks) == war.attacks_per_member:
                playersMissingAttacks.discard(p.tag)
                logger.debug(f'Removing {p}')

# Return time in hour/min/sec as string from sec, round time to minutes
def returnTime(seconds):
    minutes = floor(seconds / 60)
    seconds -= minutes * 60
    hours = floor(minutes / 60)
    minutes -= hours * 60
    if seconds >= 50:
        minutes += 1
        if minutes == 60:
            minutes = 0
            hours += 1
    remainingTime = ''
    if hours > 0:
        remainingTime += str(hours) + ' hours '
    if minutes > 0:
        remainingTime += str(minutes) + ' minutes '
    remainingTime += 'remaining '
    logger.debug(f'time: {remainingTime}')
    return remainingTime

# Sleep until `interval` seconds before the war ends, then remind everyone who still has attacks left
async def updateAndNotify(cc, war, interval):
    logger.debug('waiting till next notification interval')
    await asyncio.sleep(max(0, war.end_time.seconds_until - interval))
    # Retry transient API errors so a blip at reminder time doesn't drop the reminder
    war = await fetchWarWithRetry(cc)
    if war is None or war.state != 'inWar':
        logger.debug('War is no longer in battle day, skipping reminder')
        return
    timeLeft = war.end_time.seconds_until
    logger.debug(f'notify with time {timeLeft}')
    await removeFinishedAttackers(cc, war)
    remainingTime = returnTime(timeLeft)
    notifiedPlayers = set()
    logger.debug('send notifications')
    for tag in list(playersMissingAttacks):
        acc = clashTagMapping.get(tag)  # O(1) lookup instead of O(M) inner loop
        if acc and acc not in notifiedPlayers:
            await notifyUserAttackTime(acc.discordID, remainingTime)
            notifiedPlayers.add(acc)

# Sends notifications to players who haven't attacked at each interval
async def war_notifier(war, cc):
    try:
        key = warKey(war)
        notificationIntervals = [43200, 18000, 10800, 7200, 3600, 1800, 900]
        for interval in notificationIntervals:
            # Skip reminders whose time already passed or that were already sent for this war
            if war.end_time.seconds_until > interval and (key, interval) not in sentReminders:
                await updateAndNotify(cc, war, interval)
                sentReminders.add((key, interval))
        # Wait out the rest of the war so the search loop doesn't pick this war up again
        await asyncio.sleep(max(0, war.end_time.seconds_until) + 60)
    except Exception as e:
        logger.error(f'War notifier crashed unexpectedly: {e}. War notifications may be incomplete.', exc_info=True)
    
# True if userId is the configured bot owner. A blank or invalid discordOwnerID matches nobody.
def isOwner(userId):
    try:
        return userId == int(content['discordOwnerID'])
    except (KeyError, TypeError, ValueError):
        return False

# Command to claim clash account. With no input of username, will use discord name from command issuer
@tree.command(name='claimaccount', description='claim clash account with tag and discord name')
async def claimAccountCommand(ctx: discord.Interaction, clashtag:str):
    logger.info(f'{ctx.user.name} ({ctx.user.id}) is claiming account {clashtag}')
    try:
        config_loader.addUser(ctx.user.id, clashtag)
        updateAccounts()
    except Exception as e:
        logger.error(f'Failed to claim account {clashtag} for {ctx.user.name}: {e}')
        await ctx.response.send_message(f'Failed to claim account {clashtag}, please try again later', delete_after=30)
        return
    logger.info(f'Claimed account {clashtag} for {ctx.user.name}, tracking {len(clashTagMapping)} clash accounts')
    await ctx.response.send_message(f"Claiming account {clashtag} for {ctx.user.name}", delete_after=300)

# Command to sync new slash commands
@tree.command(name='sync-commands', description='command to sync new slash commands')
async def syncCommands(ctx: discord.Interaction):
    if isOwner(ctx.user.id):
        await tree.sync()
        await ctx.response.send_message('Commands synced', delete_after=30)
    else:
        await ctx.response.send_message('This command is only for the server owner', delete_after=30)

# Command to send intro message to someone manually
@tree.command(name='send-welcome-message', description='send welcome message to specified user')
async def sendWelcomeCommand(ctx:discord.Interaction, username:str):
    if isOwner(ctx.user.id):
        for member in tree.client.users:
            if member.name == username:
                newMemberMessage = (f'Hello {member.name}, Welcome to the Natty Daddy discord Server\n\nPlease claim your account in clash by using the command /claimaccount [clashtag]. This can be messaged to me here or placed in the server in any channel. Multiple accounts can be added one at a time\n\nExample: /claimaccount #859404klj')
                await member.send(newMemberMessage)
                await ctx.response.send_message(f'Sent welcome message to {username}', delete_after=30)
                return
        await ctx.response.send_message(f'Unable to find user {username}', delete_after=30)
    else:
        await ctx.response.send_message('This command is only for the server owner', delete_after=30)

# Send dm to user that war has started
@bot.event
async def notifyUserStart(userid:int, numattacks:str, remainingtime:str):
    # Never raise: one bad user must not stop notifications for the rest
    try:
        user = await bot.fetch_user(userid)
        logger.debug(f'Notifying {user.name} war has started')
        if not silentMode:
            await user.send(f'War has started and you are in it. You have {remainingtime}to attack {numattacks} times')
    except discord.Forbidden:
        logger.info(f'User {userid} has DMs disabled, cannot send notification')
    except Exception as e:
        logger.error(f'Failed to notify user {userid} that war started: {e!r}')

# Send dm to user to get attack in
@bot.event
async def notifyUserAttackTime(userid:int, remainingtime:str):
    # Never raise: one bad user must not stop notifications for the rest
    try:
        user = await bot.fetch_user(userid)
        logger.debug(f'notifying {user.name} to get attack in')
        if not silentMode:
            await user.send(f'{remainingtime}to get attack in')
    except discord.Forbidden:
        logger.info(f'User {userid} has DMs disabled, cannot send notification')
    except Exception as e:
        logger.error(f'Failed to send attack reminder to user {userid}: {e!r}')

# Send message to new member
@bot.event
async def on_member_join(member):
    newMemberMessage = (f'Hello {member.name}, Welcome to the Natty Daddy discord Server\n\nPlease claim your account in clash by using the command /claimaccount [clashtag]. This can be messaged to me here or placed in the server in any channel. Multiple accounts can be added one at a time\n\nExample: /claimaccount #859404klj')
    logger.debug(f'Sending welcome message to {member.name}')
    try:
        if not silentMode:
            await member.send(newMemberMessage)
    except discord.Forbidden:
        logger.info(f'{member.name} has DMs disabled, cannot send welcome message')
    except discord.HTTPException as e:
        logger.error(f'Failed to send welcome message to {member.name}: {e}')

# Update role if there is a change and remove old role
async def userRoleUpdate(updatedRole, member):
    for role in member.roles:
        if role.name in availableRoles:
            if role.name == updatedRole:
                return
            else:
                logger.debug(f'Updating role for {member.name} to {updatedRole}')
                await member.remove_roles(role)
                await member.add_roles(discord.Object(id=roles[updatedRole]))
                return
    logger.debug(f'Setting initial role for {member.name} to {updatedRole}')
    await member.add_roles(discord.Object(id=roles[updatedRole]))

# Updates roles of each member in clan every 5 minutes
async def updateRoles(cc):
    clashRoleNames = {4: 'leader', 3: 'co-leader', 2: 'elder', 1: 'member', 0: 'not-in-clan'}
    while True:
        logger.debug('Updating discord roles')
        try:
            guild = bot.get_guild(int(content['discordGuildID']))
            if not guild:
                logger.warning('Guild not found, skipping role update')
            else:
                # Snapshot the mapping, /claimaccount can add to it while this loop awaits
                for member_id, acc in list(discordTagMapping.items()):
                    member = guild.get_member(member_id)  # get_member is on Guild, not Client in discord.py 2.x
                    if not member:
                        continue
                    try:
                        clashRole = await acc.updateRole(cc)
                        await userRoleUpdate(clashRoleNames[clashRole], member)
                    except (coc.Maintenance, coc.GatewayError, aiohttp.client_exceptions.ClientConnectorError):
                        raise  # API is unreachable, give up on this pass
                    except Exception as e:
                        logger.warning(f'Failed to update role for {member.name} ({member_id}): {e!r}')
        except coc.Maintenance:
            logger.warning('CoC API under maintenance. Trying again in 5 minutes.')
        except coc.GatewayError:
            logger.warning('Gateway error, retrying in 5 minutes.')
        except aiohttp.client_exceptions.ClientConnectorDNSError as e:
            logger.warning(f'DNS resolution failed during role update: {e}. Retrying in 5 minutes.')
        except aiohttp.client_exceptions.ClientConnectorError as e:
            logger.warning(f'Connection error during role update: {e}. Retrying in 5 minutes.')
        except Exception as e:
            logger.error(f'Role update failed: {e}. Retrying in 5 minutes.', exc_info=True)
        await asyncio.sleep(300)

# Assign roles to user
@bot.event
async def assignRoles():
    logger.debug('Checking available roles in server')
    rolesInServer = set()
    guild = bot.get_guild(int(content['discordGuildID']))
    if not guild:
        logger.warning('Guild not found in cache, skipping role assignment')
        return
    for role in guild.roles:
        if role.name in roles.keys():
            rolesInServer.add(role.name)
            roles[role.name] = role.id
    if len(rolesInServer) != len(roles.keys()):
        for role in roles.keys():
            if role not in rolesInServer:
                logger.debug(f'Adding role {role} to server')
                r = await guild.create_role(name=role)
                roles[role] = r.id
    
# Add ! commands for hidden commands
@bot.event
async def on_message(ctx):
    if isOwner(ctx.author.id):
        if ctx.content.startswith('!coc-bot'):
            if ctx.content[9:] == 'version':
                await ctx.channel.send(f'Version: {__version__}')

# Start a background task unless it's already running. If it ever ends, log it and start it again.
def startBackgroundTask(name, coro_factory):
    task = background_tasks.get(name)
    if task and not task.done():
        logger.debug(f'{name} task already running')
        return
    task = asyncio.get_running_loop().create_task(coro_factory(), name=name)
    task.add_done_callback(lambda t: onBackgroundTaskDone(name, coro_factory, t))
    background_tasks[name] = task

def onBackgroundTaskDone(name, coro_factory, task):
    if task.cancelled():
        return
    exc = task.exception()
    if exc:
        logger.error(f'{name} task crashed: {exc!r}. Restarting it.', exc_info=exc)
    else:
        logger.error(f'{name} task exited unexpectedly. Restarting it.')
    startBackgroundTask(name, coro_factory)

# Bot init
@bot.event
async def on_ready():
    logger.info('bot ready')
    # Start the war notifier first so role setup problems can never block it
    startBackgroundTask('war search', lambda: startWarSearch(bot.coc_client))
    startBackgroundTask('update roles', lambda: updateRoles(bot.coc_client))
    try:
        await assignRoles()
    except Exception as e:
        logger.error(f'Role setup failed, role sync will not work until this is fixed: {e}', exc_info=True)
    if syncCommandsOnStart:
        try:
            await tree.sync()
        except Exception as e:
            logger.error(f'Failed to sync slash commands: {e}', exc_info=True)

# Event to restart bot on maintenance
@coc.ClientEvents.maintenance_completion()
async def on_maintenance_completion(time_started):
    logger.debug('maint complete')


# Coc API init
async def main():
    async with coc.EventsClient() as coc_client:
        await coc_client.login(content['clashAPIUsername'], content['clashAPIPassword'])
        # Add the client session to the bot, uncomment if needed
        # coc_client.add_events(on_maintenance_completion)
        bot.coc_client = coc_client
        await bot.start(content['discordBotToken'])

# Run once. On a fatal error exit non-zero so Docker's restart policy starts a clean process;
# the discord.Client can't be reused after its event loop closes.
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.critical(f'Main crashed with error: {e}. Exiting so the container restarts.', exc_info=True)
        sys.exit(1)