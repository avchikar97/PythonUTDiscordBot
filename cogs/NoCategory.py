import os
import logging
import netifaces as NI
import subprocess
import sympy.printing.preview
from sqlalchemy.orm import Session
from datetime import datetime

from discord.ext import commands
from discord import Embed as discordEmbed
from discord import File as discordFile

from helpers import twitterColorDetection
from helpers.joinGraph import joinChartGenerator
from helpers.UTBotCheckers import UTBotCheckers
from helpers.posts import posts

class NoCategory(commands.Cog, name='No Category'):
    def __init__(self, bot: commands.Bot, postsDB_session: Session):
        self.bot = bot
        self.postsDB = postsDB_session

    @commands.command(name='hello')
    async def hello(self, ctx: commands.Context):
        message = "Hello " + str(ctx.author).split('#')[0] + '!'
        await ctx.send(message)
        self.logmessage(ctx, message)

    @commands.command(name='ip')
    #@has_any_role(UTBotChecker.admin_roles)
    async def get_ip(self, ctx: commands.Context):
        """
        Provides the local IP's of the server
        """
        try:
            EthIP = NI.ifaddresses('eno1')[NI.AF_INET][0]['addr']
            #await ctx.send(f"Ethernet Address: {str(IP)}")
        except:
            EthIP = -1
        
        try:
            VPNIP = NI.ifaddresses('tun0')[NI.AF_INET][0]['addr']
        except: 
            VPNIP = -1
        message = f"Ethernet Address: {str(EthIP)}\nUT Address (Minecraft IP on UT Network): {str(VPNIP)}"
        message += "\nNote: If VPN Address is -1, ping brandonforty2 so he can turn it on"
        await ctx.send(message)

    @commands.command(name='startvpn', hidden=True)
    @commands.check(UTBotCheckers.is_brandon)
    async def startvpn(self, ctx: commands.Context):
        await ctx.send("Attempting to start vpn, wish me luck")
        subprocess.run("/home/brandon/startvpn.sh")

    @commands.command(name='usergraph', hidden=True)
    @commands.has_any_role(UTBotCheckers.admin_roles)
    async def usergraph(self, ctx: commands.Context):
        await joinChartGenerator(ctx)

    @commands.command(name='userstats', hidden=True)
    @commands.has_any_role(UTBotCheckers.admin_roles)
    @commands.check(UTBotCheckers.in_secret_channel)
    async def userstats(self, ctx: commands.Context, *user):
        """
        Returns stats about the user, such as amount of monthly posts
        Usage: $userstats @user
        Not inputting a user will return the top posters
        """
        if len(user) == 0:
            #Put users into dictionary
            userPosts = {}

            #Iterate through database
            for instance in self.postsDB.query(posts).order_by(posts.name):
                userPosts[instance.name] = instance.posts

            #Sort by amount of posts
            userPosts = sorted(userPosts.items(), key=lambda x: x[1], reverse=True)

            output = ""
            embed = discordEmbed(title="Posts per User this Month", color=0xbf5700)
            try:
                for person in userPosts[:10]:
                    output += f"{str(person[0])} - {str(person[1])} posts\n"
            except:
                print("10 users haven't posted yet")

            embed.add_field(name="Total Posts", value=output, inline=False)
            await ctx.send(embed=embed)


        else:
            authorEntry = None
            for instance in self.postsDB.query(posts).order_by(posts.name):
                if instance.name == user:
                    authorEntry = instance
                    found = True
                    break

            if authorEntry != None:
                await ctx.send(f"{user} has {str(authorEntry.posts)} total posts and {str(authorEntry.animePosts)} posts in #anime this month")
            else:
                await ctx.send("User not found or has not posted yet this month")

    @commands.command(name='degenerates', hidden=True)
    @commands.has_any_role(UTBotCheckers.admin_roles)
    @commands.check(UTBotCheckers.in_secret_channel)
    async def degenerates(self, ctx: commands.Context):
        """
        Returns a list of the top anime posters
        """
        userPosts = {}
        for instance in self.postsDB.query(posts).order_by(posts.name):
            userPosts[instance.name] = instance.animePosts

        userPosts = sorted(userPosts.items(), key=lambda x: x[1], reverse=True)

        totalAnime = 0
        output = ""
        embed = discordEmbed(title="Degeneracy per User this Month", color=0xbf5700)
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


    @commands.command(name='updateicon', hidden=True)
    @commands.has_any_role(UTBotCheckers.admin_roles)
    async def updateicon(self, ctx: commands.Context, color):
        """
        Updates the server icon
        
        Color options are orange, orangewhite, white, dark, attackmode, or auto
        """
        if color == 'auto':
            color = await self.on_updatecolor(ctx)
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

    @commands.command(name='score')
    async def score(self, ctx: commands.Context):
        await ctx.send("Texas beat OU 48 to 45 in the Red River Rivalry with a last second field goal by Dicker the Kicker! :metal:")

    @commands.command(name='latex')
    async def latexCommand(self, ctx: commands.Context, *args):
        latex_input = " ".join(args)
        latex_input = "\\ {} \\".format(latex_input)
        
        sympy.printing.preview(latex_input, viewer='file', filename='latex_output.png')
        await ctx.send(file=discordFile(open('latex_output.png', 'rb')))
        os.remove('latex_output.png')

    @commands.command(name='time')
    async def timeCommand(self, ctx: commands.Context):
        currentDT = datetime.now()
        outTime = currentDT.strftime("%I:%M %p")
        message = "It is " + outTime + " and OU still sucks!"
        await ctx.send(message)
        self.logmessage(ctx, message)

    @commands.command(name='hellothere')
    async def hellothere(self, ctx: commands.Context):
        await ctx.author.send("General Kenobi, you are a bold one")

    #Requested by John in case he ever needs help
    @commands.command(name='john', hidden=True)
    async def john(self, ctx: commands.Context):
        """
        https://youtu.be/Ho1LgF8ys-c
        """
        return True

    # @commands.command(name='cc-csv', hidden=True)
    # async def cc_csv(ctx):
    #     with open('cc.csv', 'w', newline='') as csvfile:
    #         csv_writer = csv.writer(csvfile)
    #         for instance in session.query(ccCommand).order_by(ccCommand.name):
    #             print(instance.name)
    #             csv_writer.writerow(['', instance.name, instance.responce])

    #     await ctx.send(file=discordFile('cc.csv'))
    #     os.remove('cc.csv')

    #Used to automatically update color
    async def on_updatecolor(self, ctx: commands.Context):
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

    def logmessage(self, ctx: commands.Context, message):
        logging.info("Sent message '" + message + "' to " + ctx.channel.name)