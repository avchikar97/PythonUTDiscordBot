# PythonUTDiscordBot
Discord bot for the UT Discord server, written in Python

Use `pip -r requirements.txt` to install all packages needed for this project.

## Tower Icon
Normally, the icon for the server is based on the state of the UT tower.  The tower shines burnt orange at night for various events, such as after football game wins, graduation, or to celebrate a faculty member.  Using the command `$updateicon auto` will download a picture of the tower from tower.utexas.edu then find its average color.  It will then pick the icon that matches the color of the tower and set it as the icon for the community.  The icon is also user settable with the $updateicon command, with the options such as white, orange, orangewhite, and dark.  Each corresponds to a file in the bots code, with the name of the color being the name of the file to allow expandability of icons in the future.  

## Scoreboard Icon
The bot has the ability to track football games on ESPN then turn the detected scores into a scoreboard icon.  While football mode is active, the bot will check the score every minute to see if it has changed.  To check, it uses aiohttp to prevent blocking with web requests, then parses with Beautiful Soup.  When it changes, it adds the scores to a base icon with team logos.  The bot will then animate the icon, fading between the scoreboard and tower icon.  This is done with Pillow by creating a sequence of images, then it calls an ffmpeg command through the shell to turn the images into a gif.  

## Command Database
The bot has a modifiable command database that allows administrators to add and remove simple response commands.  This is done with a SQLite database on the host machine, then it is accessed with SQLAlchemy.  

## User Assignable Roles
Users are able to add roles to themselves from a database of possible roles.  The database can be added to by administrators for when new discord roles are created.  It also supports role aliases so multiple names assign the same role for user convenience.  
