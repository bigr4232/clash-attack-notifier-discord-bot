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
commandsSynced = False

# Intents and tree inits
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
managers = {}
tree = app_commands.CommandTree(bot)

# Event for new war start. Will start the war attack notifier
@coc.WarEvents.new_war(tags=clan_tags)
async def new_war(war):
    logging.info('new war registered')
    players.clear()
    for member in war.members:
        if member.clan.tag == int(content['discordChannel']):
            players.append(member)
    await war_notifier(war)

# Remove users who have attacked from players list
async def removeFinishedAttackers(cc):
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
    return remainingTime

# Update the players list and notify users that haven't attacked
# wait in asyncio.sleep for amount of time passed in
async def updateAndNotify(cc, time):
    await removeFinishedAttackers(cc)
    remainingTime = returnTime(time)
    for member in players:
        for claimedMember in config_loader['clanMembers'].keys():
            if member.tag == claimedMember:
                notifyUser(config_loader['clanMembers'][claimedMember], remainingTime)
    war = await cc.get_current_war(clan_tags[0])
    asyncio.sleep(war.end_time.seconds_until - time)

# Sends notifications to players who haven't attacked at each interval
async def war_notifier(war):
    notificationIntervals = [7200, 3600, 2400, 1200, 600]
    async with coc.Client() as cc:
        if war.state != 'inWar':
            asyncio.sleep(war.end_time.seconds_until + 500)
        war = await cc.get_current_war(clan_tags[0])
        asyncio.sleep(war.end_time.seconds_until - 68400)
        for time in notificationIntervals:
            await updateAndNotify(cc, time)

# Command to claim clash account. With no input of username, will use discord name from command issuer
@tree.command(name='claimaccount', description='claim clash account with tag and discord name', guild=discord.Object(id=int(content['discordGuildID'])))
async def claimAccountCommand(ctx: discord.Interaction, clashtag:str):
    await ctx.response.send_message(f"Claiming account {clashtag} for {ctx.user.name}")
    config_loader.addUser(ctx.user.id, clashtag)
    global content
    content = config_loader.loadYaml()

@bot.event
async def notifyUser(ctx:discord.Interaction, userid:str, remainingtime:str):
    user = await bot.fetch_user(***REMOVED***)
    await user.send(f'{remainingtime} to get attack in')

# Bot init
@bot.event
async def on_ready():
    global commandsSynced
    if commandsSynced == False:
        await tree.sync(guild=discord.Object(id=int(content['discordGuildID'])))
        commandsSynced = True
        logging.info('commands synced')
    logging.info('ready')

# coc API init
async def main():
    async with coc.EventsClient() as coc_client:
        try:
            await coc_client.login_with_tokens(content['clashToken'])
        except coc.InvalidCredentials as error:
            exit(error)
        coc_client.add_clan_updates(*clan_tags)
        coc_client.add_war_updates(*clan_tags)
        coc_client.add_events(
            new_war,
        )
        clan_tags.append(content['clanTag'])

        # Add the client session to the bot
        bot.coc_client = coc_client
        await bot.start(content['discordBotToken'])


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass