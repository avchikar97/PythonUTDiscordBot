import logging
import os
import csv
from sqlalchemy.orm import Session

from discord import Embed as discordEmbed
from discord import File as discordFile
from discord.ext import commands

from helpers.CCCommand import CCCommand
from helpers.UTBotCheckers import UTBotCheckers

class CommandDB(commands.Cog):
    """
    Handles adding commands to a database
    """

    def __init__(self, bot: commands.Bot, my_session: Session):
        self.bot = bot
        self.session = my_session
        self.UTBotChecker = UTBotCheckers()

    async def add_command(self, ctx: commands.Context, command, _responce, _category):
        """
        Adds a command to the database
        Assumes user has permission to do it
        """
        new_command = CCCommand(
            name=command.lower(),
            responce=_responce,
            category=_category)
        self.session.merge(new_command)
        self.session.commit()
        await ctx.message.add_reaction('👌')
        logging.info(
            "%s added %s with responce %s to %s",
            ctx.author.name,
            new_command.name,
            new_command.responce,
            new_command.category)

    async def delete_command(self, ctx: commands.Context, victim):
        """
        Removed a command from the database
        Assumes the user has permission to do it
        """
        self.session.delete(victim)
        self.session.commit()
        await ctx.send(f"Deleted the command for {victim.name}")
        logging.info(
            "%s deleted %s from %s",
            ctx.author.name,
            victim.name,
            victim.category
        )
        return

    @commands.command(name='cc', hidden=True)
    @commands.has_any_role(UTBotChecker.admin_roles)
    @commands.check(UTBotChecker.in_secret_channel)
    async def cc_command(self, ctx: commands.Context, command, *, _responce):
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
    async def cc_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'command':
                #Output command list
                output = [""]
                i = 0
                for instance in self.sessionquery(CCCommand).order_by(CCCommand.name):
                    if (int(len(output[i])/900)) == 1:
                        i = i + 1
                        output.append("")
                    output[i] += f"{instance.name} "

                i = 1
                for message in output:
                    embed = discordEmbed(
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
                victim = self.sessionquery(CCCommand).filter_by(name=ctx.args[2]).one()
                await self.delete_command(ctx, victim)


    @commands.command(name='hc')
    async def hc(self, ctx: commands.Context, command, *, _responce):
        """
        Shows troubleshooting command list
        Usage: !hc

        Admins and Regulars can add to the database
        Modify or create a command: !hc <command_name> <responce>
        Delete a command: !hc <command_name>

        Bot will confirm with :ok_hand:
        
        """
        if await self.UTBotChecker.is_regular(ctx) == True and await self.UTBotChecker.in_secret_channel(ctx) == True:
            if ctx.message.mention_everyone == False:
                CATEGORY = 'help'
                await self.add_command(ctx, command, _responce, CATEGORY)
                return

            else:
                await ctx.send(f"Please do not use everyone or here, {ctx.author}")


    @hc.error
    async def hc_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'command':
                #print(self.UTBotChecker.in_botspam(ctx))
                if await self.UTBotChecker.in_botspam(ctx) == True:
                    #Output the command list
                    output = [""]
                    i = 0
                    for instance in self.sessionquery(CCCommand).order_by(CCCommand.name):
                        if instance.category == 'help':
                            if (int(len(output[i])/900)) == 1:
                                i = i + 1
                                output.append("")
                            output[i] += f"{instance.name} "
                    i = 1
                    for message in output:
                        #print(f"Messages: {message}")
                        embed = discordEmbed(
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
                if await self.UTBotChecker.is_regular(ctx) == True and await self.UTBotChecker.in_secret_channel(ctx) == True:
                    victim = self.sessionquery(CCCommand).filter_by(name=ctx.args[2]).one()
                    if victim.category == 'help':
                        await self.delete_command(ctx, victim)
                    else:
                        await ctx.send("hc can only delete help commands")

        else:
            await ctx.send("There was an error, details in log (in function hc_error)")
            print(f"Error be different:{error}")
            


    @commands.command(name='cc-csv', hidden=True)
    @commands.has_any_role(UTBotChecker.admin_roles)
    @commands.check(UTBotChecker.in_secret_channel)
    async def cc_csv(self, ctx: commands.Context):
        """
        Generates a csv of the command database and posts it
        """
        with open('cc.csv', 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            for instance in self.sessionquery(CCCommand).order_by(CCCommand.name):
                csv_writer.writerow([instance.category, instance.name, instance.responce])

        await ctx.send(file=discordFile('cc.csv'))
        os.remove('cc.csv')

    @commands.command(name='import-csv', hidden=True)
    @commands.has_any_role(UTBotChecker.admin_roles)
    @commands.check(UTBotChecker.in_secret_channel)
    async def import_csv(self, ctx: commands.Context, filename):
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
                    self.sessionmerge(new_cc)
                    commands_added += 1

                self.sessioncommit()
                await ctx.send(f'Added {commands_added} commands to database')

        #except FileNotFoundError:
        #    await ctx.send("Error, file not found");
        except Exception as oof:
            await ctx.send("Something went wrong with import, check log for details")
            logging.info(oof)
