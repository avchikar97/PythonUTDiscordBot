import asyncio
from discord.ext import commands
from discord.utils import get as discord_get

class UTBotCheckers():
    ##############  Founder              Moderator           UT Discord Admin
    admin_roles =   [469158572417089546, 490250496028704768, 667104998714245122]

    async def in_secret_channel(self, ctx: commands.Context):
        """Checks if a command was used in a secret channel"""
        secretChannels = {
            'ece-torture-dungeon': 508350921403662338,
            'nitro-commands': 591363307487625227,
            'eyes-of-texas': 532781500471443477
        }
        usedChannel = ctx.channel.id
        for channel in secretChannels:
            if secretChannels[channel] == usedChannel:
                return True

        #It dont exist
        return False

    async def in_botspam(self, ctx: commands.Context):
        """Checks if a command was done in a botspam channel"""
        botspam = {
            'eyes-of-texas': 532781500471443477,
            'bot-commands': 469197513593847812,
            'ece-torture-dungeon': 508350921403662338
        }
        used_channel = ctx.channel.id
        for channel in botspam:
            if botspam[channel] == used_channel:
                return True

        await ctx.send("Error: View the command list in a bot command channel like #voice-pastebin")
        return False

    async def is_regular(self, ctx: commands.Context):
        """Checks if they can be trusted to add help commands"""
        regular_roles = {
            'Founder': 469158572417089546,
            'Moderator': 490250496028704768,
            'UT Discord Admin': 667104998714245122
        }

        for role_id in regular_roles:
            test_role = discord_get(ctx.guild.roles, id=regular_roles[role_id])
            if test_role in ctx.author.roles:
                return True

        await ctx.send("You do not have permission to do that")
        return False

    async def is_nitro(self, ctx: commands.Context):
        """Checks if a user has Discord Nitro"""
        
        guild = ctx.guild()
        if guild != None:
            user = guild.get_member(ctx.author)
            user_prof = await user.profile()
            return user_prof.premium

    async def is_brandon(self, ctx: commands.Context):
        """Checks if I ran this"""
        brandon = discord_get(ctx.guild.members, id=158062741112881152)
        return brandon == ctx.author
