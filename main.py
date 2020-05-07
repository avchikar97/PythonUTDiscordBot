import sys
import os
import discord
import twitterColorDetection
from datetime import datetime
from discord.ext import commands, tasks
from discord.ext.commands import has_any_role
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging
import netifaces as ni
from joinGraph import joinChartGenerator
import subprocess
import aiohttp
import bs4
from PIL import Image, ImageFont, ImageDraw
import sports_tracking
import icon_animator
import json
import csv
import sympy.printing.preview

import UTBotCheckers

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


class CCCommand(Base):
    """
    Makes object that database undserstands
    """
    __tablename__ = "imageCommands"

    #Has a column for the ID, name, and responce
    #id = Column(Integer, primary_key=True)
    name = Column(String, primary_key=True)
    responce = Column(String)
    category = Column(String)   #help or fun

class posts(Base):
    __tablename__ = datetime.now().strftime("%m-%y")

    #Column for name, posts, how many mentions, how many times mentioned, how many posts in anime
    name = Column(String, primary_key=True)
    posts = Column(Integer)
    mentions = Column(Integer)
    mentioned = Column(Integer)
    animePosts = Column(Integer)


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

##################
#Command Database#
##################

class CommandDB(commands.Cog):
    """
    Handles adding commands to a database
    """

    async def add_command(self, ctx, command, _responce, _category):
        """
        Adds a command to the database
        Assumes user has permission to do it
        """
        new_command = CCCommand(
            name=command.lower(),
            responce=_responce,
            category=_category)
        session.merge(new_command)
        session.commit()
        await ctx.message.add_reaction('👌')
        logging.info(
            "%s added %s with responce %s to %s",
            ctx.author.name,
            new_command.name,
            new_command.responce,
            new_command.category)

    async def delete_command(self, ctx, victim):
        """
        Removed a command from the database
        Assumes the user has permission to do it
        """
        session.delete(victim)
        session.commit()
        await ctx.send(f"Deleted the command for {victim.name}")
        logging.info(
            "%s deleted %s from %s",
            ctx.author.name,
            victim.name,
            victim.category
        )
        return

    @commands.command(name='cc', hidden=True)
    @has_any_role(UTBotCheckers.admin_roles)
    @commands.check(UTBotCheckers.in_secret_channel)
    async def cc_command(self, ctx, command, *, _responce):
        """
        Modifies the command database

        List commands: !cc
        Modify or create a command: !cc <command_name> <responce>
        Delete a command: !cc <command_name>

        Bot will confirm with :ok_hand:
        """
        #add a command
        if ctx.message.mention_everyone == False:
            CATEGORY = 'fun'
            await self.add_command(ctx, command, _responce, CATEGORY)
            return

        else:
            await ctx.send(f"Please do not use everyone or here, {ctx.author}")


    @cc_command.error
    async def cc_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'command':
                #Output command list
                output = [""]
                i = 0
                for instance in session.query(CCCommand).order_by(CCCommand.name):
                    if (int(len(output[i])/900)) == 1:
                        i = i + 1
                        output.append("")
                    output[i] += f"{instance.name} "

                i = 1
                for message in output:
                    embed = discord.Embed(
                        title=f'CC commands, pg {i}',
                        color=0xbf5700)
                    embed.add_field(
                        name='All CC commands, times out after 2 minutes',
                        value = message,
                        inline=False)
                    i += 1
                    await ctx.send(embed=embed, delete_after=120)

            elif error.param.name == '_responce':
                #delete a command
                victim = session.query(CCCommand).filter_by(name=ctx.args[2]).one()
                await self.delete_command(ctx, victim)


    @commands.command(name='hc')
    async def hc(self, ctx, command, *, _responce):
        """
        Shows troubleshooting command list
        Usage: !hc

        Admins and Regulars can add to the database
        Modify or create a command: !hc <command_name> <responce>
        Delete a command: !hc <command_name>

        Bot will confirm with :ok_hand:
        
        """
        if await UTBotCheckers.is_regular(ctx) == True and await UTBotCheckers.in_secret_channel(ctx) == True:
            if ctx.message.mention_everyone == False:
                CATEGORY = 'help'
                await self.add_command(ctx, command, _responce, CATEGORY)
                return

            else:
                await ctx.send(f"Please do not use everyone or here, {ctx.author}")


    @hc.error
    async def hc_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'command':
                #print(UTBotCheckers.in_botspam(ctx))
                if await UTBotCheckers.in_botspam(ctx) == True:
                    #Output the command list
                    output = [""]
                    i = 0
                    for instance in session.query(CCCommand).order_by(CCCommand.name):
                        if instance.category == 'help':
                            if (int(len(output[i])/900)) == 1:
                                i = i + 1
                                output.append("")
                            output[i] += f"{instance.name} "
                    i = 1
                    for message in output:
                        #print(f"Messages: {message}")
                        embed = discord.Embed(
                            title=f'Help commands, pg {i}',
                            color=0xbf5700)
                        embed.add_field(
                            name='All help commands, times out after 2 minutes',
                            value=message,
                            inline=False)
                        i += 1
                        await ctx.send(embed=embed, delete_after=120)

                    return

                else: 
                    return

            #Responce be missing so yeet it
            elif error.param.name == '_responce':
                #Make sure they be allowed
                if await UTBotCheckers.is_regular(ctx) == True and await UTBotCheckers.in_secret_channel(ctx) == True:
                    victim = session.query(CCCommand).filter_by(name=ctx.args[2]).one()
                    if victim.category == 'help':
                        await self.delete_command(ctx, victim)
                    else:
                        await ctx.send("hc can only delete help commands")

        else:
            await ctx.send("There was an error, details in log (in function hc_error)")
            print(f"Error be different:{error}")
            


    @commands.command(name='cc-csv', hidden=True)
    @has_any_role(UTBotCheckers.admin_roles)
    @commands.check(UTBotCheckers.in_secret_channel)
    async def cc_csv(self, ctx):
        """
        Generates a csv of the command database and posts it
        """
        with open('cc.csv', 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            for instance in session.query(CCCommand).order_by(CCCommand.name):
                csv_writer.writerow([instance.category, instance.name, instance.responce])

        await ctx.send(file=discord.File('cc.csv'))
        os.remove('cc.csv')

    @commands.command(name='import-csv', hidden=True)
    @has_any_role(UTBotCheckers.admin_roles)
    @commands.check(UTBotCheckers.in_secret_channel)
    async def import_csv(self, ctx, filename):
        """
        ONLY RUN THIS IF YOU KNOW WHAT YOU ARE DOING
        SO PROBABLY DON'T USE THIS COMMAND!!!!!!!!!!

        Imports a csv file full of commands

        Usage: !import-csv filename.csv
        Note: File path is relative to server instance

        File Format:
        [category], [name], [responce]
        """
        try:
            with open(filename, 'r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                commands_added = 0
                for row in reader:
                    new_cc = CCCommand(
                        category=row[0],
                        name=row[1],
                        responce=row[2])
                    session.merge(new_cc)
                    commands_added += 1

                session.commit()
                await ctx.send(f'Added {commands_added} commands to database')

        #except FileNotFoundError:
        #    await ctx.send("Error, file not found");
        except Exception as oof:
            await ctx.send("Something went wrong with import, check log for details")
            logging.info(oof)
            

client.add_cog(CommandDB(client))

#################
#Sports Tracking#
#################


class SportsTracking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.game = None
        self.guild = None
        self.channel = None

    #Make it check every 5 minutes for score updates
    #If there's an update, change the icon
    #Send current score to a channel
    #Check if game is finished, if it is, stop the routine

    @commands.command(name='footballmode')
    @has_any_role(UTBotCheckers.admin_roles)
    async def sports_icon_updater(self, ctx, game_id, is_home):
        """
        Starts the sports tracking
        Inputs: ESPN Game ID, boolean for if home game (1 = home, 0 = away)
        Stop with stopfootball
        """
        self.game = sports_tracking.Score(int(game_id), int(is_home))
        self.guild = ctx.guild
        self.channel = ctx.channel
        await self.game.get_start_trigger()
        logging.info("Started football mode")
        await ctx.send(f"Starting football mode, will begin tracking game {game_id} when it begins\nStop with `$stopfootball`")
        await self.score_loop.start()
        #await self.score_loop()


    @commands.command(name='stopfootball')
    @has_any_role(UTBotCheckers.admin_roles)
    async def stop_loop(self, ctx):
        self.score_loop.cancel()
        logging.info("Stopping football mode")

    @tasks.loop(minutes=1)
    #@commands.command()
    #@has_any_role(UTBotCheckers.admin_roles)
    async def score_loop(self):
        """Loop used to check score"""
        #Check if game has started
        if self.game.game_started == False:
            await self.game.start_check()
            # channel = client.get_channel(617406092191858699)
            # await self.channel.send("Game has not started")
            logging.info("Game has not started")
            # await self.channel.send("Manually starting game")
            # self.game.game_started = True

        #Game started
        else:
            #Update score
            try:
                await self.game.update_score()
                logging.info("Checked scores")
                
                #print(f"new {str(self.longhorn_score)} - {str(self.enemy_score)}, old {str(self.icon_longhorn_score)} - {str(self.icon_enemy_score)}")
                if ((self.game.longhorn_score != self.game.icon_longhorn_score) or (self.game.enemy_score != self.game.icon_enemy_score)):
                    #channel = client.get_channel(617406092191858699)
                    await self.channel.send(f"Longhorns: {self.game.longhorn_score}, Losers: {self.game.enemy_score}")

                    #Generate icon
                    icon_path = self.game.icon_generator()
                    gif_icon = icon_animator.animate_icon(icon_path, "icons/white.png")
                    
                    try:
                        #Update icon on test server
                        #guild = client.get_guild(469153450953932800)
                        with open(gif_icon, 'rb') as image:
                            f = image.read()
                            b = bytearray(f)
                            await self.guild.edit(icon=b)
                            logging.info("Updated score icon")
                    except:
                        print(f"Error with updating icon: {sys.exc_info()[0]}")
                
                #print("Checking status")
                if self.game.game_status[0:5] == "Final":
                    #Game is finished, stopped updating
                    logging.info("Game over, stopping")
                    await channel.send(f"Game over, final score is {self.game.longhorn_score} - {self.game.enemy_score}")

                    #Update icon for victory
                    if self.game.longhorn_score > self.game.enemy_score:
                        score_icon_path = self.game.icon_generator()
                        icon_path = icon_animator.animate_icon(score_icon_path, "icons/orangewhite.png")

                    if self.game.longhorn_score < self.game.enemy_score:
                        icon_path = "icons/white.png"

                    try:
                        #Update icon on test server
                        #guild = client.get_guild(469153450953932800)
                        with open(icon_path, 'rb') as image:
                            f = image.read()
                            b = bytearray(f)
                            await self.guild.edit(icon=b)
                            logging.info("Updated score icon")
                    except:
                        print(f"Error with updating icon: {sys.exc_info()[0]}")

                    self.score_loop.stop()
            except:
                print("error, stopping loop")
                self.score_loop.cancel()

        

    @commands.command()
    async def cogtest(self, ctx):
        await ctx.send("Hello world!")

    

client.add_cog(SportsTracking(client))

##########
#Set Rank#
##########

class SetRank(commands.Cog):
    """Allows for the setting of ranks for users"""
    def __init__(self, bot):
        self.bot = bot
        self.rank_engine = create_engine("sqlite:///ranks.db", echo=False)
        Base.metadata.create_all(self.rank_engine)
        self.RankSession = sessionmaker(bind=self.rank_engine)
        self.rankdb = self.RankSession()
        #prohibited ranks
        self.PROHIBITED_RANKS = [
            "Founder",
            "Moderator",
            "Mod in Training",
            "Fake Nitro",
            "Time out",
            "Bots",
            "Server Mute",
            "Announcer",
            "Eyes of Texas",
            "Dyno",
            "Pokecord",
            "Rythm",
            "Muted",
            "Ping Bot",
            "Nitro Booster"
        ]


    class RankEntry(Base):
        __tablename__ = "ranks"

        name = Column(String, primary_key=True)
        category = Column(String)
        rank_id = Column(Integer)

    async def addrank(self, _category, rank_name, _rank_id):
        """
        Creates a new entry in rank database
        Inputs: Table name, name of rank, id it points to
        """

        new_rank = self.RankEntry(name=rank_name, category=_category, rank_id=_rank_id)
        self.rankdb.merge(new_rank)
        self.rankdb.commit()

    @commands.command(name='newrank')
    @has_any_role(UTBotCheckers.admin_roles)
    async def newrank(self, ctx, *args):
        """
        Adds a new rank to the list of assignable ranks. 
        Make sure to put multi word stuff, like Class of 2023 in parenthesis
        It is not case sensitive

        Creating a rank:
        $newrank Category "Name of rank"
        $newrank College "Natural Sciences"

        Creating an alias for a rank:
        $newrank College "Name of rank" "Name of alias"
        $addrole College "Natural Sciences" "Science"
        """

        #Make sure it isn't a prohibited rank
        if args[1] in self.PROHIBITED_RANKS:
            await ctx.send("Error: Tried to add a prohibited rank.  Don't do that")
            await ctx.message.add_reaction("<:uhm:582370528984301568>")
            await ctx.message.add_reaction("<:ickycat:576983438385741836>")
            return

        role = discord.utils.get(ctx.guild.roles, name=args[1])
        if role == None:
            await ctx.send("Error: Could not find the role")
            return
        
        #Parse into one of the two options
        if len(args) == 2:
            #We in option one
            #await ctx.send('Category: {}\nName: {}'.format(args[0], args[1]))
            await self.addrank(args[0].lower(), args[1].lower(), role.id)
            logging.info('{} added {} with name {} in category {}'.format(ctx.author.name, args[1], args[1], args[0]))

        elif len(args) == 3:
            #await ctx.send('Category: {}\nName: {}\nCommand: {}'.format(args[0], args[1], args[2]))
            #Add an alias
            await self.addrank(args[0].lower(), args[2].lower(), role.id)
            logging.info('{} added {} with name {} in category {}'.format(ctx.author.name, args[1], args[2], args[0]))
 

        else:
            #We in hell
            await ctx.send('Error: Cannot parse the command, make sure it be formatted good')
            return

        await ctx.message.add_reaction('👌')

    @commands.command(name="deleterank")
    @has_any_role(UTBotCheckers.admin_roles)
    async def deleterank(self, ctx, *args):
        """
        Removes a rank or alias from the rank database. 
        Include multi word ranks in " "

        Usage
        $deleterank "Name of rank"

        Example
        $deleterank "Natural Sciences"
        $deleterank Science
        """
        #Try and find the rank and yeet it, else display an error
        try:
            victim = self.rankdb.query(self.RankEntry).filter_by(name=args[0].lower()).one()
            self.rankdb.delete(victim)
            self.rankdb.commit()
            await ctx.send(f"Removed rank {args[0]}")
            logging.info(ctx.author.name + " deleted rank " + victim.name)
        except:
            await ctx.send("Error: Could not find rank")


    async def embed_list_builder(self, ctx, all_ranks):
        """
        Sends an embedded list of ranks to the output channel
        Gets around max of 1024 characters by breaking up into multiple messages
        """
        #embed = discord.Embed(title="Ranks", color=0xbf5700)
        #Make output an array of strings with each string having max of 1000 characters
        output = [""]
        i = 0
        for role in all_ranks:
            if  (int(len(output[i])/900)) == 1:
                #print(f'the calculation is {output[i]} % 900 = {len(output[i])}')
                i = i + 1
                output.append("")
            output[i] += f"`{role[0]} - {role[1]}, {role[2]} members`\n"

        #print(f'size of 1st str {len(output[i])}')
        #print(len(output[0]))
        #print(output)
        #print(int(len(output[0])/900))
        i = 1
        for rank_list in output:
            embed = discord.Embed(title=f'Ranks, pg {i}', color=0xbf5700)
            i = i + 1
            embed.add_field(name="All available ranks, times out after 2 minutes", value=rank_list, inline=False)
            await ctx.send(embed=embed, delete_after=120)


    @commands.command(name="ranks")
    #@commands.check(is_brandon)
    async def rewrite_ranks(self, ctx):
        """
        PM's a list of ranks to the user
        """
        #Generate list of tuples in format ("Category", "Rank name", "Amount of people")
        #If the rank ID's name is not in the list, then add it
        all_ranks_id = []
        is_in = False
        for instance in self.rankdb.query(self.RankEntry).order_by(self.RankEntry.name):
            #Check if its in there
            is_in = False
            #print("heloooo")
            for rank in all_ranks_id:
                #print(f"{instance.rank_id} - {rank[0]}")
                if instance.rank_id == rank[0]:
                    is_in = True
                    #print(f"is_in == {is_in}")
                    break

            #print(f"At value check, is_in == {is_in}")
            if is_in == False:
                all_ranks_id.append((instance.rank_id, instance.category))

        #print(all_ranks_id)

        #So we got a list of tuples with id and category, turn that into list of Category, Name, and amount of people
        all_ranks = []
        utdiscord = client.get_guild(469153450953932800)
        for rank in all_ranks_id:
            ut_role = discord.utils.get(utdiscord.roles, id=rank[0])
            all_ranks.append((rank[1], ut_role.name, str(len(ut_role.members))))
        #Sort it with a lambda function, first by name of role then by name of category
        all_ranks.sort(key=lambda tup: tup[1])
        all_ranks.sort(key=lambda tup: tup[0])

        #print(all_ranks)
        
        #Create function that sends list of tuples as embed
        await self.embed_list_builder(ctx, all_ranks)


    @commands.command(name='rank')
    #@commands.check(is_brandon)
    async def rewrite_rank(self, ctx, *newRank):
        """
        Adds a rank from the database to a user
        """
        if len(newRank) == 0:
            await ctx.send("Use `$rank name` to add a rank.  Use `$ranks` to list all ranks")
        else:
            newRankName = ' '.join(newRank)
            newRankName = newRankName.lower()
            #Establish guild to use
            utdiscord = client.get_guild(469153450953932800)
            utuser = discord.utils.get(utdiscord.members, id=ctx.author.id)
            try:
                victim = self.rankdb.query(self.RankEntry).filter_by(name=newRankName).one()
                newRank = discord.utils.get(utdiscord.roles, id=victim.rank_id)
            except:
                await ctx.send(f"{newRankName} not found.  Make sure it is typed the same way as in the list of ranks found in `$ranks`")
            
            #Check if they already have the role.  If so, delete it.  Else add it
            if newRank in utuser.roles:
                #If so, delete it
                await utuser.remove_roles(newRank)
                await ctx.send(f'Removed rank {newRank.name} from {ctx.author.mention}')
                logging.info(f'Removed rank {newRank.name} from {ctx.author.mention}')

            else:
                #Add it since they don't got it
                await utuser.add_roles(newRank, reason="self assigned with Eyes of Texas")
                await ctx.message.add_reaction('👌')
                logging.info(f'Added rank {newRank.name} to {ctx.author.mention}')


    #Now a college, location, and class, and group command, basically adds or deletes those from user
    #or idk maybe do this  




client.add_cog(SetRank(client))


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

    #Set activity
    if CONFIG['show_status'] == True:
        await client.change_presence(activity=discord.Game(CONFIG['name']))




##############
###Commands###
##############


@client.command(name='hello')
async def hello(ctx):
    message = "Hello " + str(ctx.author).split('#')[0] + '!'
    await ctx.send(message)
    logmessage(ctx, message)


@client.command(name='ip')
#@has_any_role(UTBotCheckers.admin_roles)
async def get_ip(ctx):
    """
    Provides the local IP's of the server
    """
    try:
        EthIP = ni.ifaddresses('eno1')[ni.AF_INET][0]['addr']
        #await ctx.send(f"Ethernet Address: {str(IP)}")
    except:
        EthIP = -1
    try:
        VPNIP = ni.ifaddresses('tun0')[ni.AF_INET][0]['addr']
    except: 
        VPNIP = -1
    message = f"Ethernet Address: {str(EthIP)}\nUT Address (Minecraft IP on UT Network): {str(VPNIP)}"
    message += "\nNote: If VPN Address is -1, ping brandonforty2 so he can turn it on"
    await ctx.send(message)


@client.command(name='startvpn', hidden=True)
@commands.check(UTBotCheckers.is_brandon)
async def startvpn(ctx):
    await ctx.send("Attempting to start vpn, wish me luck")
    subprocess.run("/home/brandon/startvpn.sh")


@client.command(name='usergraph', hidden=True)
@has_any_role(UTBotCheckers.admin_roles)
async def usergraph(ctx):
    await joinChartGenerator(ctx)


@client.command(name='userstats', hidden=True)
@has_any_role(UTBotCheckers.admin_roles)
@commands.check(UTBotCheckers.in_secret_channel)
async def userstats(ctx, *user):
    """
    Returns stats about the user, such as amount of monthly posts
    Usage: $userstats @user
    Not inputting a user will return the top posters
    """
    if len(user) == 0:
        #Put users into dictionary
        userPosts = {}

        #Iterate through database
        for instance in postsDB.query(posts).order_by(posts.name):
            userPosts[instance.name] = instance.posts

        #Sort by amount of posts
        userPosts = sorted(userPosts.items(), key=lambda x: x[1], reverse=True)

        output = ""
        embed = discord.Embed(title="Posts per User this Month", color=0xbf5700)
        try:
            for person in userPosts[:10]:
                output += f"{str(person[0])} - {str(person[1])} posts\n"
        except:
            print("10 users haven't posted yet")

        embed.add_field(name="Total Posts", value=output, inline=False)
        await ctx.send(embed=embed)


    else:
        authorEntry = None
        for instance in postsDB.query(posts).order_by(posts.name):
            if instance.name == user:
                authorEntry = instance
                found = True
                break

        if authorEntry != None:
            await ctx.send(f"{user} has {str(authorEntry.posts)} total posts and {str(authorEntry.animePosts)} posts in #anime this month")
        else:
            await ctx.send("User not found or has not posted yet this month")


@client.command(name='degenerates', hidden=True)
@has_any_role(UTBotCheckers.admin_roles)
@commands.check(UTBotCheckers.in_secret_channel)
async def degenerates(ctx):
    """
    Returns a list of the top anime posters
    """
    userPosts = {}
    for instance in postsDB.query(posts).order_by(posts.name):
        userPosts[instance.name] = instance.animePosts

    userPosts = sorted(userPosts.items(), key=lambda x: x[1], reverse=True)

    totalAnime = 0
    output = ""
    embed = discord.Embed(title="Degeneracy per User this Month", color=0xbf5700)
    try:
        for person in userPosts[:10]:
            output += f"{str(person[0])} - {str(person[1])} posts\n"
    except:
        print("10 users haven't posted yet")
    
    #Get the total anime posts
    for person in userPosts:
        totalAnime += person[1]

    embed.add_field(name="Posts in #anime", value=output, inline=False)
    totalAnimeMessage = f"{str(totalAnime)} total posts made in #anime"
    embed.add_field(name="Collective degeneracy", value=totalAnimeMessage, inline=False)
    await ctx.send(embed=embed)

    #This is getting out of hand
    if totalAnime > 100:
        ctx.send("https://tenor.com/WmUi.gif")


@client.command(name='updateicon', hidden=True)
@has_any_role(UTBotCheckers.admin_roles)
async def updateicon(ctx, color):
    """
    Updates the server icon
    
    Color options are orange, orangewhite, white, dark, attackmode, or auto
    """
    if color == 'auto':
        color = await on_updatecolor(ctx)
    try:
        with open("icons/" + color + ".png", "rb") as image:
            f = image.read()
            b = bytearray(f)
            await ctx.guild.edit(icon=b)
            await ctx.channel.send("Icon set to " + color)
            logging.info("Icon set to " + color + " by " + ctx.author.name)
    #If the file isn't found, then the tower color is probably unknown
    except FileNotFoundError:
        await ctx.send("Error: Unknown tower color.  Options are white, orange, orangewhite, and dark")


@client.command(name='score')
async def score(ctx):
    await ctx.send("Texas beat OU 48 to 45 in the Red River Rivalry with a last second field goal by Dicker the Kicker! :metal:")

@client.command(name='latex')
async def latexCommand(ctx, *args):
    latex_input = " ".join(args)
    latex_input = "\\ {} \\".format(latex_input)
    
    sympy.printing.preview(latex_input, viewer='file', filename='latex_output.png')
    await ctx.send(file=discord.File(open('latex_output.png', 'rb')))
    os.remove('latex_output.png')

@client.command(name='time')
async def timeCommand(ctx):
    currentDT = datetime.now()
    outTime = currentDT.strftime("%I:%M %p")
    message = "It is " + outTime + " and OU still sucks!"
    await ctx.send(message)
    logmessage(ctx, message)


@client.command(name='hellothere')
async def hellothere(ctx):
    await ctx.author.send("General Kenobi, you are a bold one")


#Requested by John in case he ever needs help
@client.command(name='john', hidden=True)
async def john(ctx):
    """
    https://youtu.be/Ho1LgF8ys-c
    """
    return True


# @client.command(name='cc-csv', hidden=True)
# async def cc_csv(ctx):
#     with open('cc.csv', 'w', newline='') as csvfile:
#         csv_writer = csv.writer(csvfile)
#         for instance in session.query(ccCommand).order_by(ccCommand.name):
#             print(instance.name)
#             csv_writer.writerow(['', instance.name, instance.responce])

#     await ctx.send(file=discord.File('cc.csv'))
#     os.remove('cc.csv')


@client.event
async def on_command_error(ctx, error):
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
async def on_message(ctx):
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
async def on_member_join(ctx):
    newUserMessage = f"Welcome to the UT Austin Discord {ctx.mention}!  Please select which school/college you are in by using `$rank name of college` in the #bot-commands channel. "
    newUserMessage += "You can also select your graduating class and where you will be living.  "
    newUserMessage += "See the list of available schools/colleges, graduating classes, and communities by using `$ranks.` \n"
    newUserMessage += "If you are having problems joining a rank, please message a member with the Founder or Moderator role.  "
    newUserMessage += "Be sure to read our rules in #real-rules."
    await ctx.send(newUserMessage)
    logging.info(f"Sent join PM to {ctx.mention}")


#Used to automatically update color
async def on_updatecolor(ctx):
    try:
        towerRGB = twitterColorDetection.getRGB()
        towerColor = twitterColorDetection.getColorNames(towerRGB[0], towerRGB[1])
        #Determine the correct icon
        towerColorName = towerColor[0].lower() + towerColor[1].lower()
        possibleColors = {
            "orangeorange": "orange",
            "whiteorange": "orangewhite",
            "whitewhite": "white",
            "darkdark": "dark"
        }
        towerColorName = possibleColors[towerColorName]

        return towerColorName


    except Exception as e:
        await ctx.send("Error: " + str(e))


#Logs a message that is sent
def logmessage(ctx, message):
    logging.info("Sent message '" + message + "' to " + ctx.channel.name)



client.run(CONFIG['key'].strip())