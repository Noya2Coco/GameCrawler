import logging
import threading
import time
import discord
from discord.ext import commands

# Configuration du bot Discord
intents = discord.Intents.default()
intents.message_content = True

command_prefix = "!"
bot = commands.Bot(command_prefix=command_prefix, intents=intents)

stop_event = threading.Event()

logging.basicConfig(filename='bot.log', level=logging.INFO)

test = 0
# Fonction pour lancer une boucle infinie avec des threads
def start_threads():
    # Liste pour stocker les threads
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
        thread = threading.Thread(target=run_thread)
        thread.start()
        threads.append(thread)
        
        global test
        test += 1
        # Vérification si l'événement d'arrêt est activé
        if stop_event.is_set():
            break

    # Arrêt de tous les threads restants
    for thread in threads:
        thread.join()

# Fonction pour la tâche de chaque thread
def run_thread():
    test_save = test
    logging.info(f"{test_save}. Thread fait")
    time.sleep(5)

# Fonction pour arrêter la boucle infinie
def stop():
    stop_event.set()

# Définir la fonction start comme une commande Discord
@bot.command()
async def start(ctx):
    # Créer un événement pour la boucle infinie
    stop_event = threading.Event()

    # Démarrer la fonction start dans un thread séparé
    threading.Thread(target=start_threads).start()

    # Envoyer un message de confirmation à l'utilisateur
    await ctx.send("Fonction start lancée avec succès !")

# Définir la fonction stop comme une commande Discord
@bot.command()
async def stop(ctx):
    stop_event.set()

    # Envoyer un message de confirmation à l'utilisateur
    await ctx.send("Fonction start arrêtée avec succès !")

# Lancer le bot Discord
bot.run("MTIxNzUxMzczMTg3NDA5NTEyNA.GFpCrv.4xrkgeMcxVuvjJP7RYcU7an14eI_iIyjVnZddY")
