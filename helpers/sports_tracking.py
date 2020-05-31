"""
Brandon Zupan

Holds functions that deal with aquiring sports scores and generating a discord icon
"""

import asyncio
import aiohttp
import bs4
from PIL import Image, ImageFont, ImageDraw

class Score():
    def __init__(self, game_id, is_home):
        self.game_id = game_id
        self.is_home = is_home
        self.longhorn_score = None
        self.enemy_score = None
        # Scores on the icon, 1 since its an impossible score
        self.icon_longhorn_score = 1
        self.icon_enemy_score = 0
        self.game_status = None
        self.game_started = None
        self.start_trigger = None

    async def get_start_trigger(self):
        """Get the word in time class so we know when game starts"""
        async with aiohttp.ClientSession() as session:
            html = await self.fetch_score_html(session, self.game_id)

        soup = bs4.BeautifulSoup(html, features='html.parser')
        status_container = soup.findAll("div", {"class": "game-status"})

        self.start_trigger = status_container[0].getText()
        self.game_started = False

    async def start_check(self):
        """See if game has started"""
        async with aiohttp.ClientSession() as session:
            html = await self.fetch_score_html(session, self.game_id)

        soup = bs4.BeautifulSoup(html, features='html.parser')
        status_container = soup.findAll("div", {"class": "game-status"})

        #If the message changes, then the game probably started
        current_message = status_container[0].getText()
        #print("Checking if game started")
        print(f"Old: {self.start_trigger}, New: {current_message}")
        if current_message != self.start_trigger:
            self.game_started = True

    async def fetch_score_html(self, session, id):
        """Updates the score from ESPN"""
        url = f'http://www.espn.com/college-football/game/_/gameId/{id}'
        async with session.get(url) as responce:
            return await responce.text()

    async def update_score(self):
        """Updates score from ESPN"""
        async with aiohttp.ClientSession() as session:
            html = await self.fetch_score_html(session, self.game_id)

        soup = bs4.BeautifulSoup(html, features='html.parser')

        homeScoreContainer = soup.findAll("div", {"class": "score icon-font-before"})
        awayScoreContainer = soup.findAll("div", {"class": "score icon-font-after"})
        status_container = soup.findAll("div", {"class": "game-status"})

        self.game_status = status_container[0].getText()

        if self.is_home == True:
            self.longhorn_score = homeScoreContainer[0].getText()
            self.enemy_score = awayScoreContainer[0].getText()
        else:
            self.longhorn_score = awayScoreContainer[0].getText()
            self.enemy_score = homeScoreContainer[0].getText()

    def icon_generator(self):
        """
        Generates an icon for the discord server
        Inputs: 2 scores
        Output: Path to new icon
        """

        im = Image.open("gameday.png")
        draw = ImageDraw.Draw(im)

        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 150)

        #Longhorn score
        draw.text((260, 64), str(self.longhorn_score), (255,255,255), font=font)
        #Loser score
        draw.text((260, 264), str(self.enemy_score), (255,255,255), font=font)
        im.save('sample-out.png')

        self.icon_longhorn_score = self.longhorn_score
        self.icon_enemy_score = self.enemy_score

        return 'sample-out.png'

    def set_score(self, new_longhorn, new_enemy):
        self.longhorn_score = new_longhorn
        self.enemy_score = new_enemy

async def main():
    red_river = Score(401112085, True)
    red_river.set_score(10,5)
    yeet = red_river.icon_generator()
    # await red_river.get_start_trigger()
    # await red_river.update_score()
    # yeet = red_river.icon_generator()
    # print(yeet)
    #print(f"Longhorn: {red_river.longhorn_score}, OU: {red_river.enemy_score}")
    #await red_river.start_check()
    # print(red_river.game_started)
    # print(red_river.start_trigger)
    # print(red_river.game_status)

    #icon_path = red_river.icon_generator()
    #print(icon_path)

    # with open(icon_path, "rb") as image:
    #     f = image.read()
    #     b = bytearray(f)
    #     #await guild.edit(icon=b)

# loop = asyncio.get_event_loop()
# loop.run_until_complete(main())