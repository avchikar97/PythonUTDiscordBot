import logging
import sys

from discord.ext import commands, tasks

from helpers import sports_tracking, icon_animator
from helpers.UTBotCheckers import UTBotCheckers

class SportsTracking(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.game = None
        self.guild = None
        self.channel = None
        self.UTBotChecker = UTBotCheckers()

    #Make it check every 5 minutes for score updates
    #If there's an update, change the icon
    #Send current score to a channel
    #Check if game is finished, if it is, stop the routine

    @commands.command(name='footballmode')
    @commands.has_any_role(UTBotChecker.admin_roles)
    async def sports_icon_updater(self, ctx: commands.Context, game_id, is_home):
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
    @commands.has_any_role(UTBotChecker.admin_roles)
    async def stop_loop(self, ctx: commands.Context):
        self.score_loop.cancel()
        logging.info("Stopping football mode")

    @tasks.loop(minutes=1)
    #@commands.command()
    #@has_any_role(UTBotChecker.admin_roles)
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
                    if(self.channel != None):
                        await self.channel.send(f"Game over, final score is {self.game.longhorn_score} - {self.game.enemy_score}")

                    icon_path = None
                    #Update icon for victory
                    if self.game.longhorn_score >= self.game.enemy_score:
                        score_icon_path = self.game.icon_generator()
                        icon_path = icon_animator.animate_icon(score_icon_path, "icons/orangewhite.png")
                    else:
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
    async def cogtest(self, ctx: commands.Context):
        await ctx.send("Hello world!")
