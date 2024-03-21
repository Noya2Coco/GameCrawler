import random
import re
import subprocess
import time
import discord
from discord.ext import commands
import threading
import logging
import requests


# Configuration du bot Discord
intents = discord.Intents.default()
intents.message_content = True
command_prefix = "!"
bot = commands.Bot(command_prefix=command_prefix, intents=intents)

# Thread pour arrêter le crawler
stopEvent = threading.Event()

logger = logging.getLogger("Crawler")
logging.basicConfig(filename='bot.log', level=logging.INFO)

portToService = {
    "7777" : {
        "terraria" : "terraria",
        "terraria-server" : "terraria",
    },
    "25565" : {
        "minecraft" : "minecraft",
        "mc-server" : "minecraft",
    },
    "27015" : {
        "garrys-mod" : "gmod",
        "garrysmod" : "gmod",
        "facepunch" : "gmod",
        
        "csgo" : "csgo",
        "counter-strike" : "csgo",

        "tf2" : "tf2",
        "team-fortress-2" : "tf2",
    },
    "28015" : {
        "rust" : "rust",
        "rust-server" : "rust",
    },
}
serviceToChannel = {
    "minecraft" : "https://discord.com/api/webhooks/1217567600888778832/XBf5u_WhybDR19OldTMfTTq1Ai0TQrgUdyyjalInfWbtWf0mORuU2opiyxfp-VfJvcuQ",
    "gmod" : "https://discord.com/api/webhooks/1219426733082546258/GG0p5OjKjwErWrYpV4_fEsnSZr8zVB9-_UP8X6lHEK2fUkE4NJsa1OpUutlS9YgqbC9Y",
    "terraria" : "https://discord.com/api/webhooks/1219427083718103070/teKNJWYQ2JmGavOvJG3PNfqrmbv64w7eYa8LOdiquRsOtoScRoRTR4clE0vG1pPoP6xb",
    "rust" : "https://discord.com/api/webhooks/1219427201426919444/sm9ZepkT5n-LE_CrU5MxisRZ0DiJ6QEk81hRr7pPYrjQUTlkcyamq_Atu_AfzkmA9UDu",
    "csgo" : "https://discord.com/api/webhooks/1219426905514836078/RIRgIPjEHH4cvm_3qVgI7RK_YtT4VuAVlDqeNVJ_IgY1UdVOFB3yarv2ee6GOfHpjEM2",
    "tf2" : "https://discord.com/api/webhooks/1219426983398608956/7-0HZSG2b9MUR2_xGypL30CGEOIkmeZHlZV-BoCtXVqND7galvAOMQb52HNB_uPz-_E9",
}

index = 0



# Générer une adresse IP aléatoire
def getRandomIp():
    # Générer une adresse IP aléatoire en excluant les plages d'adresses privées et réservées
    while True:
        first_octet = random.randint(1, 223)  # Les adresses IP publiques sont généralement dans la plage 1 à 223
        second_octet = random.randint(1, 225)
        if first_octet == 10 or first_octet== 127 or (first_octet == 192 and second_octet == 168):
            # Exclure les plages privées (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
            continue

        return f"{first_octet}.{second_octet}.{random.randint(0, 255)}.{random.randint(0, 255)}"

# Envoyer une requête TCP à l'ip au port souhaité et retourne les informations        
def sendNmapRequest(ip, port):
    command = ["nmap", "-p", port, "-sV", ip]

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=60).stdout
        return result
    
    except subprocess.TimeoutExpired:
        logger.error(f" La commande a pris trop de temps sur l'ip {ip} et a été interrompue.")
    except subprocess.CalledProcessError as e:
        logger.error(f" Erreur lors de l'exécution de la commande : {e}")
        return None
    
def extractResultInfo(ip, port, result):
    pattern = r"(\d+/tcp)\s+(\w+)\s+(\w+)\s+(.*?)\n"
    match = re.search(pattern, result)

    if match:
        _, state, service, version_info = match.groups()

        message_pattern = r"Message: (.*?)(?=1\.)"
        message_match = re.search(message_pattern, version_info)
        if message_match:
            message = message_match.group(1)
        else:
            message = "?"

        version_pattern = r"1\.\d+([- .\d]*)"
        version_match = re.search(version_pattern, version_info)
        if version_match:
            version_range = version_match.group(0)
        else:
            version_range = "?"

        users_pattern = r"Users: (\d+)/(\d+)"
        users_match = re.search(users_pattern, version_info)
        if users_match:
            users_count = int(users_match.group(1))
            total_users = int(users_match.group(2))
        else:
            users_count, total_users = "?", "?"

        data = {
            'ip': ip,
            'port': port,
            'state': state,
            'service': service,
            'title': message,
            'version_range': version_range,
            'onlineUsers': users_count,
            'maxUsers': total_users,
        }
        return data
        
    else:
        return None

def sendDiscordAlert(infos):
    data = {
        "content" : "======================================\n" +
            "Un serveur ouvert a été trouvé !\n" +
            "Ip : " + infos["ip"] + "\n" +
            "Port : " + str(infos["port"]) + "\n" +
            "State : " + infos["state"] + "\n" +
            "Service : " + infos["service"] + "\n" +
            "Title : " + infos["title"] + "\n" +
            "Versions : " + infos["version_range"] + "\n" +
            "Users : " + str(infos["onlineUsers"]) + "/" + str(infos["maxUsers"]) + "\n",
        "username" : "GameCrawler Alert",
        "avatar_url" : "https://i.pinimg.com/564x/5f/39/47/5f3947a0192e4f94108325cbec86bc4f.jpg"
    }

    try:
        webhookUrl = serviceToChannel[portToService[infos['port']][infos["service"]]]
    except:
        webhookUrl = "https://discord.com/api/webhooks/1219427371791155221/RgOHfC3T0yoCvJN5xra6yr4_6dXN9pmoZftxzG5B9CuyExB5oLE_NaWQ7oB65Foqf6iq"

    
    try:
        result = requests.post(webhookUrl, json = data)
        result.raise_for_status()
        logger.info(" Message Discord envoyé avec succès, code {}.".format(result.status_code))
    except requests.exceptions.HTTPError as err:
        print(err)        

# Lancer une boucle infinie avec des threads
def startThreads():
    threads = []

    # Boucle pour créer et gérer les threads
    while True:
        # Limiter le nombre de threads à 20
        if len(threads) >= 20:
            # Attendre qu'un thread soit libre
            for thread in threads:
                thread.join()
                threads.remove(thread)
                break

        # Création d'un nouveau thread
        thread = threading.Thread(target=runThread)
        thread.start()
        threads.append(thread)
        
        global index
        index += 1

        # Vérification si l'événement d'arrêt est activé
        if stopEvent.is_set():
            break

    # Arrêt de tous les threads restants
    for thread in threads:
        thread.join()

# Fonction pour la tâche de chaque thread
def runThread():
    ip = getRandomIp()
    for port in portToService:
        result = sendNmapRequest(ip, port)
        
        if result:
            infos = extractResultInfo(ip, port, result)

            if infos != None and infos['state'] == "open" :
                #saveToDatabase(infos)
                logger.info(f" {index} - Informations pour l'ip {ip}:{port} (Timestamp : {time.time()})\n[{infos}]")
                sendDiscordAlert(infos)

            #else:
                #logger.error(f" {index} - Aucune information pour l'ip {ip}:{port} (Timestamp : {time.time()})\n[{infos}]")
                #logger.error(f"{index} - Aucune information pour l'ip {ip}:{port}\n[{infos}]\n")
        #else:
            #print(f"{i} - Erreur lors de l'exécution de la commande Nmap.")
                
                # Fonction pour arrêter la boucle infinie

def stop():
    stopEvent.set()

# Définir la fonction start comme une commande Discord
@bot.command()
async def start(ctx):
    # Créer un événement pour la boucle infinie
    #global stopEvent
    #stopEvent = threading.Event()

    # Démarrer la fonction start dans un thread séparé
    threading.Thread(target=startThreads).start()

    # Envoyer un message de confirmation à l'utilisateur
    await ctx.send("Fonction start lancée avec succès !")

# Définir la fonction stop comme une commande Discord
@bot.command()
async def stop(ctx):
    stopEvent.set()

    # Envoyer un message de confirmation à l'utilisateur
    await ctx.send("Fonction start arrêtée avec succès !")

# Lancer le bot Discord
bot.run("MTIxNzUxMzczMTg3NDA5NTEyNA.GFpCrv.4xrkgeMcxVuvjJP7RYcU7an14eI_iIyjVnZddY")

# envoyer message channel
# await message.channel.send("Le message est détecté !")