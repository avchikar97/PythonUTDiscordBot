import discord
import matplotlib.pyplot as plt


async def joinChartGenerator(ctx):
    totalUsers = 0
    dates = []
    #df = pd.DataFrame(columns=['number', 'joindate'])
    print("Gathering Users")
    allUsers = ctx.guild.members
    for i in allUsers:
        totalUsers += 1
        dates.append(i.joined_at)
        #df[totalUsers] = i.joined_at
        #print(f"User {i.name} joined at {i.joined_at}")
    print(f"Total Users: {str(totalUsers)}")
    dates.sort()
    #print(dates)

    #Plot with matplotlib
    #y axis will be members
    y = range(totalUsers)
    plt.suptitle(ctx.guild.name)
    plt.ylabel("Number of Users")
    plt.xlabel("Join Date")
    plt.plot_date(dates, y)    
    plt.locator_params(axis='x', nbins=8)
    ax = plt.axes()
    ax.xaxis.set_major_locator(plt.MaxNLocator(4))
    plt.savefig("plot.png")

    #Upload to discord
    await ctx.send(file=discord.File('plot.png'))

