import logging
from sqlalchemy import Column, String, Integer, DeclarativeMeta
import sqlalchemy.engine
from sqlalchemy.orm import session

import discord
from discord.ext import commands

from helpers.UTBotCheckers import UTBotCheckers

class SetRank(commands.Cog):
    """Allows for the setting of ranks for users"""
    def __init__(self, bot: commands.Bot, my_base: DeclarativeMeta):
        self.bot = bot
        self.rank_engine = sqlalchemy.engine.create_engine("sqlite:///ranks.db", echo=False)
        self.myBase = my_base
        self.myBase.metadata.create_all(self.rank_engine)
        self.RankSession = session.sessionmaker(bind=self.rank_engine)
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


    class RankEntry(DeclarativeMeta):
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
    @commands.has_any_role(UTBotCheckers.admin_roles)
    async def newrank(self, ctx: commands.Context, *args):
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

        role = ctx.guild().roles
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
    @commands.has_any_role(UTBotCheckers.admin_roles)
    async def deleterank(self, ctx: commands.Context, *args):
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


    async def embed_list_builder(self, ctx: commands.Context, all_ranks):
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
    async def rewrite_ranks(self, ctx: commands.Context):
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
        utdiscord = self.bot.get_guild(469153450953932800)
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
    async def rewrite_rank(self, ctx: commands.Context, *newRank):
        """
        Adds a rank from the database to a user
        """
        if len(newRank) == 0:
            await ctx.send("Use `$rank name` to add a rank.  Use `$ranks` to list all ranks")
        else:
            newRankName = ' '.join(newRank)
            newRankName = newRankName.lower()
            #Establish guild to use
            utdiscord = self.bot.get_guild(469153450953932800)
            utuser = discord.utils.get(utdiscord.members, id=ctx.author.id)
            try:
                victim = self.rankdb.query(self.RankEntry).filter_by(name=newRankName).one()
                rank_attempt = discord.utils.get(utdiscord.roles, id=victim.rank_id)
            except:
                await ctx.send(f"{newRankName} not found.  Make sure it is typed the same way as in the list of ranks found in `$ranks`")
                return
            
            #Check if they already have the role.  If so, delete it.  Else add it
            if rank_attempt in utuser.roles:
                #If so, delete it
                await utuser.remove_roles(newRank)
                await ctx.send(f'Removed rank {rank_attempt.name} from {ctx.author.mention}')
                logging.info(f'Removed rank {rank_attempt.name} from {ctx.author.mention}')
            else:
                #Add it since they don't got it
                await utuser.add_roles(newRank, reason="self assigned with Eyes of Texas")
                await ctx.message.add_reaction('👌')
                logging.info(f'Added rank {rank_attempt.name} to {ctx.author.mention}')


    #Now a college, location, and class, and group command, basically adds or deletes those from user
    #or idk maybe do this  

