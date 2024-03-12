import random
import re
import sqlite3
import subprocess


def initDatabase():
    # Connexion à la base de données (ou création si elle n'existe pas)
    conn = sqlite3.connect('MCServerInfos.db')
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

def extractResultInfo(ip, result):
    # Utilisez une expression régulière pour extraire les informations souhaitées
    pattern = r"(\d+/tcp)\s+(\w+)\s+(\w+)\s+(.*?)\n"
    match = re.search(pattern, result)

    if match:
        port, state, service, version_info = match.groups()

        # Utilisez une autre expression régulière pour extraire les informations spécifiques de la version
        message_pattern = r"Message: (.*?)(?=1\.)"
        message_match = re.search(message_pattern, version_info)
        if message_match:
            message = message_match.group(1)
        else:
            message = None

        version_pattern = r"(1\..*?1\..*)(?=,)"
        version_match = re.search(version_pattern, version_info)
        if version_match:
            version_range = version_match.group(1)
        else:
            version_range = None

        users_pattern = r"Users: (\d+)/(\d+)"
        users_match = re.search(users_pattern, version_info)
        if users_match:
            users_count = int(users_match.group(1))
            total_users = int(users_match.group(2))
        else:
            users_count, total_users = None, None

        return {
            'IP': ip,
            'PORT': port,
            'STATE': state,
            'SERVICE': service,
            'INFOS': {
                'TITLE': message,
                'VERSION_RANGE': version_range,
                'USERS': {
                    'ONLINE': users_count,
                    'MAX': total_users,
                },
            }
        }
        
    else:
        return None
    
def saveToDatabase(infos):
    data = {"ip": infos["IP"], "title": infos["INFOS"]["TITLE"], "versionRange": infos["INFOS"]["VERSION_RANGE"],
            "onlineUsers": infos["INFOS"]["USERS"]["ONLINE"], "maxUsers": infos["INFOS"]["USERS"]["MAX"]}

    conn = sqlite3.connect('MCServerInfos.db')
    conn.execute('''
        INSERT OR REPLACE INTO MCServerInfos (ip, title, versionRange, onlineUsers, maxUsers, lastUpdate)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (data["ip"], data["title"], data["versionRange"], data["onlineUsers"], data["maxUsers"]))


    # Valider les modifications et fermer la connexion
    conn.commit()
    conn.close()

# Envoyer une requête TCP à l'ip au port souhaité et retourne les informations        
def sendNmapRequest(ip, port):
    command = ["nmap", "-p", port, "-sV", ip]

    try:
        # Exécutez la commande et capturez la sortie
        result = subprocess.run(command, capture_output=True, text=True, check=True).stdout

        return result
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'exécution de la commande : {e}")
        return None

def main():
    initDatabase()
    ip = getRandomIp()
    port = "25565"
    result = sendNmapRequest(ip, port)

    if result:
        # Extrayez les informations du service
        infos = extractResultInfo(ip, result)
        saveToDatabase(infos)
        print("Informations du service :\n", infos)
    else:
        print("Erreur lors de l'exécution de la commande Nmap.")
    
if __name__ == "__main__":
    nbCrawl = int(input("Combien de crawl ?"))
    for i in range(nbCrawl):
        main()