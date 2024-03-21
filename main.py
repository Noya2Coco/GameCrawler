import random
import re
import socket
import sqlite3
import subprocess
import concurrent.futures
import threading
import time
import keyboard
import requests

maximum_concurrent_tasks = 30

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

def initDatabase():
    # Connexion à la base de données (ou création si elle n'existe pas)
    conn = sqlite3.connect('servers_data.db')
    # Création d'une table pour stocker les informations
    conn.execute('''
        CREATE TABLE IF NOT EXISTS MCServerInfos (
            ip TEXT PRIMARY KEY NOT NULL,
            title TEXT,
            versionRange TEXT,
            onlineUsers INTEGER,
            maxUsers INTEGER,
            lastUpdate TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

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
    
def saveToDatabase(infos):
    if infos["service"] == "minecraft" and infos["state"] == 'open':
        ip = infos["ip"]

        try:
            data = {"ip": infos["ip"], "title": infos["mc"]["title"], "versionRange": infos["mc"]["version_range"],
                    "onlineUsers": infos["mc"]["users"]["online"], "maxUsers": infos["mc"]["users"]["max"]}

            conn = sqlite3.connect('MCServerInfos.db')
            conn.execute('''
                INSERT OR REPLACE INTO MCServerInfos (ip, title, versionRange, onlineUsers, maxUsers, lastUpdate)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (data["ip"], data["title"], data["versionRange"], data["onlineUsers"], data["maxUsers"]))


            # Valider les modifications et fermer la connexion
            conn.commit()
            conn.close()

            print(f"### L'ip {ip} à été sauvegardée ###")
        except:
            print(f"XXX Problème survenu lors de la sauvegarde de l'ip {ip} XXX")

# Envoyer une requête TCP à l'ip au port souhaité et retourne les informations        
def sendNmapRequest(ip, port):
    command = ["nmap", "-p", port, "-sV", ip]

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=60).stdout

        return result
    except subprocess.TimeoutExpired:
        print(f"La commande a pris trop de temps sur l'ip {ip} et a été interrompue.")
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'exécution de la commande : {e}")
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

    result = requests.post(webhookUrl, json = data)
    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)
    else:
        print("Message Discord envoyé avec succès, code {}.".format(result.status_code))

def keyDetection():
    global programEnd
    while True:
        if keyboard.is_pressed('q'):
            print("La touche 'q' a été pressée. Arrêt du programme dans moins de 1000 requêtes.")
            programEnd = True
            exit()
        time.sleep(0.1)

def main(i):
    initDatabase()
    ip = getRandomIp()
    if i % 50 == 0: 
        print(f"Requêtes effectuées : {i}")

    for port in portToService:
        result = sendNmapRequest(ip, port)
        
        if result:
            infos = extractResultInfo(ip, port, result)
            print(infos)
            if infos != None and infos['state'] == "open" :
                #saveToDatabase(infos)
                sendDiscordAlert(infos)
                print(f"{i} - Informations pour l'ip {ip}:{port}\n[{infos}]\n")

            else:
                print(f"{i} - Aucune information pour l'ip {ip}:{port}\n[{infos}]\n")
        else:
            print(f"{i} - Erreur lors de l'exécution de la commande Nmap.")
    
if __name__ == "__main__":
    # Créer un pool de threads pour exécuter les tâches en parallèle
    with concurrent.futures.ThreadPoolExecutor(max_workers=maximum_concurrent_tasks) as executor:
        # Liste des futures pour les tâches en cours
        futures = []
        i=0

        # Lancer les tâches en parallèle
        for j in range(1, 1 + 1):
            i +=1
            future = executor.submit(main, i)
            futures.append(future)
            
        # Attendre que toutes les tâches se terminent
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except socket.gaierror:
                # Gérer les erreurs de résolution DNS si nécessaire
                pass
        futures.clear()
        exit()
            
    print("Terminé")