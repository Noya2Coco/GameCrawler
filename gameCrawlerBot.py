import discord
from discord.ext import commands
import subprocess

intents = discord.Intents.default()  # Créer un objet Intents avec les intents par défaut
intents.message_content = True  # Activer l'intent message_content

command_prefix = "!"
bot = commands.Bot(command_prefix=command_prefix, intents=intents) 

channelsId = [
    1217603694758068387, # UPED
    1217990547118096448 # Dev
    ] 

token = "MTIxNzUxMzczMTg3NDA5NTEyNA.GFpCrv.4xrkgeMcxVuvjJP7RYcU7an14eI_iIyjVnZddY"

global process
process = None

@bot.event
async def on_ready():
    for channelId in channelsId:
        channel = bot.get_channel(channelId)
        await channel.send(f"{bot.user} est lancé")

"""
async def atTheEnd():
    print("Sur le point de s'éteindre...")
    for channelId in channelsId:
        channel = bot.get_channel(channelId)
        await channel.send(f"{bot.user} est éteint")
"""

@bot.command()
async def start(ctx, arg=None):
    if ctx.channel.id not in channelsId:
        return
    
    global process
    if process is None:
        try:
            process = subprocess.Popen(['python3', 'main.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            await ctx.channel.send("Le script McCrawler **s'est lancé** correctement")

        except Exception as e:
            process = None
            await ctx.channel.send(f"Le script McCrawler **n'a pas réussi à se lancer** : \n{e}")
    else:
        await ctx.channel.send(f"Le script McCrawler **est déjà lancé** : __{command_prefix}stop__")

@bot.command()
async def stop(ctx, arg=None):
    global process
    if process is not None:
        try:
            process.terminate()
            process = None
            await ctx.channel.send("Le script McCrawler **s'est éteint** correctement")
        except Exception as e:
            await ctx.channel.send(f"Le script McCrawler **n'a pas réussi à s'éteindre** : {e}")
    else:
        await ctx.channel.send(f"Le script McCrawler **n'est pas lancé** : __{command_prefix}start__")

"""
@bot.event
async def on_message(message):
    # Vérifier si le message est dans le bon canal
    if message.channel.id not in channelsId:
        return

    if message.content == "!start":
        await message.channel.send("Le message est détecté !")
"""

bot.run(token)

