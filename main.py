import os
import discord
from discord.ext import commands
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging
import aiohttp
import bs4
import json

from helpers.UTBotCheckers import UTBotCheckers
from helpers.CCCommand import CCCommand
from helpers.posts import posts

from cogs.CommandDB import CommandDB
from cogs.SportsTracking import SportsTracking
from cogs.SetRank import SetRank
from cogs.NoCategory import NoCategory

#Start logging
logging.basicConfig(level=logging.INFO)

#Setup JSON config file
CONFIG_FILE = 'config.json'
CONFIG = {}
if os.path.exists(CONFIG_FILE):
    #load it
    with open(CONFIG_FILE, "r") as config_file:
        CONFIG = json.load(config_file)
else:
    #create file
    config_template = {
        "key": "put private key here",
        "prefix": "!",
        "name": "Bot",
        "database": "sqlite:///:memory:",
        "show_status": False
    }
    with open(CONFIG_FILE, "w") as config_file:
        json.dump(config_template, config_file)
    print(f"Please fill out {CONFIG_FILE}")
    exit()

#SQL Database
engine = create_engine(CONFIG['database'], echo=False)
postsEngine = create_engine("sqlite:///posts.db", echo=False)
Base = declarative_base()
UTBotChecker = UTBotCheckers()

#Create the Table   
Base.metadata.create_all(engine)    #Commands
Base.metadata.create_all(postsEngine)   #Posts

#Start the SQL session
Session = sessionmaker(bind=engine)
session = Session()

PostsSession = sessionmaker(bind=postsEngine)
postsDB = PostsSession()

#Discord client
client = commands.Bot(command_prefix=CONFIG['prefix'])

# Add cogs
client.add_cog(CommandDB(client, session))
client.add_cog(SportsTracking(client))
client.add_cog(SetRank(client, Base))
client.add_cog(NoCategory(client, postsDB))


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

    #Set activity
    if CONFIG['show_status'] == True:
        await client.change_presence(activity=discord.Game(CONFIG['name']))

@client.event
async def on_command_error(ctx: commands.Context, error):
    if isinstance(error, commands.errors.CommandNotFound):
        #await ctx.send(ctx.message.content)
        command = ctx.message.content.lower()
        command = command.split(" ", 1)

        #Look if its in the database
        for instance in session.query(CCCommand).order_by(CCCommand.name):
            if instance.name == command[0][1:]:
                await ctx.send(instance.responce)
                return
    else:
        print(error)

@client.event
async def on_message(ctx: commands.Context):
    #Add voting to suggestions channel
    if ctx.channel.id == 469191877489459220:
        #reactions = ['thumbsup', 'thumbsdown', 'shrug']
        await ctx.add_reaction('👍')
        await ctx.add_reaction('👎')
        await ctx.add_reaction('🤷')

    #Oman at oman
    message = ctx.content
    message = message.lower()

    if (' oman' in message):
        await ctx.add_reaction('🇴🇲')
    elif (message[0:5] == 'oman '):
        await ctx.add_reaction('🇴🇲')
    elif (message[0:4] == 'oman'):
        await ctx.add_reaction('🇴🇲')
        
    #rlm message
    if ctx.author.bot == False:
        if ((' rlm' in message) or (message[0:4] == 'rlm ') or (message[0:3] == 'rlm')):
            await ctx.channel.send("pma > rlm - <https://feebledribblings.wordpress.com/2017/10/10/town-hall-debrief/>")

    #Add an ickycat to anime
    if (ctx.channel.id == 565561419769315328):
        if ((ctx.attachments) or ('http://' in ctx.content) or ('https://' in ctx.content)):
            #ickycat = discord.Emoji()
            #ickycat.name='ickycat'
            #await ctx.add_reaction('<:ickycat:576983438385741836>')

            #its now an uwu instead of ickycat
            await ctx.add_reaction('🇺')
            await ctx.add_reaction('🇼')
            await ctx.add_reaction('<:anotheruforuwu:604139855802531848>')

    #Track messages and add stuff to database
    authorname = ctx.author.mention
    authorEntry = None

    #Look if its in the database
    for instance in postsDB.query(posts).order_by(posts.name):
        if instance.name == authorname:
            authorEntry = instance
            break

    if authorEntry != None:
        authorEntry.posts += 1
    else:
        authorEntry = posts(name=authorname, posts=1, animePosts=0, mentions=0, mentioned=0)

    #Check if it was posted in anime
    if ctx.channel.id == 565561419769315328:
        authorEntry.animePosts += 1

    postsDB.merge(authorEntry)
    postsDB.commit()
    #print(f"{authorEntry.name} has {str(authorEntry.posts)} posts total, and {str(authorEntry.animePosts)} posts in anime")

    await client.process_commands(ctx)


#Send a PM when someone joins
@client.event
async def on_member_join(ctx: commands.Context):
    newUserMessage = f"Welcome to the UT Austin Discord {ctx.mention}!  Please select which school/college you are in by using `$rank name of college` in the #bot-commands channel. "
    newUserMessage += "You can also select your graduating class and where you will be living.  "
    newUserMessage += "See the list of available schools/colleges, graduating classes, and communities by using `$ranks.` \n"
    newUserMessage += "If you are having problems joining a rank, please message a member with the Founder or Moderator role.  "
    newUserMessage += "Be sure to read our rules in #real-rules."
    await ctx.send(newUserMessage)
    logging.info(f"Sent join PM to {ctx.mention}")

client.run(CONFIG['key'].strip())