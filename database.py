import sqlite3

class Database:
    def __init__(self, name: str, columns: dict):
        self.name = name
        self.path = "logs/" + self.name + ".db"
        self.columns = columns # columnName : arguments (type, default,...)
        
        self._create()

    def _create(self):
        dbRequest = f"CREATE TABLE IF NOT EXISTS {self.name} ("
        for columnName, columnArguments in self.columns.items():
            dbRequest = dbRequest + columnName + " " + columnArguments + ","
        
        dbRequest = dbRequest[:-1] + ")"
        self.executeAction(dbRequest)
    
    # Permet de faire une requête à la bdd
    def executeAction(self, action):
        conn = sqlite3.connect(self.path) 
        cursor = conn.cursor()
        cursor.execute(action)

        # Si la requête est un SELECT, récupérer les données
        if action.strip().upper().startswith("SELECT"):
            data = cursor.fetchall()
        else:
            data = None

        conn.commit()
        conn.close()
        return data

    # Faire un INSERT dans la db, renvoie True si ça a fonctionné sinon False
    def insert(self, data: dict):
        dbRequest = f"SELECT * FROM {self.name} LIMIT 1"

        dbRequest = f"INSERT OR REPLACE INTO {self.name} "
        dbRequestNames = "("
        dbRequestValues = "VALUES ("
        for columnName in self.columns:
            # Si la colonne n'est pas fournie -> valeur par défaut
            if columnName in data and data[columnName] != None:
                dbRequestNames += columnName
                dbRequestNames += ","

                if not isinstance(data[columnName], int):
                    dbRequestValues = dbRequestValues + "'" + str(data[columnName]) + "'"
                else:
                    dbRequestValues += str(data[columnName])
                dbRequestValues += ","
        
        dbRequest = dbRequest + dbRequestNames[:-1] + ") "+ dbRequestValues[:-1] + ")"
        try:
            self.executeAction(dbRequest)
            return True
        except:
            return False        
        


def tests():
    print("Programme lancé")

    database = Database("testDB", {
        "id" : "INTEGER PRIMARY KEY NOT NULL",
        "title" : "TEXT",
        "number" : "INTEGER",
        "date" : "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    })
    print("Database créée")

    try:
        assert database.insert({
            "id" : 1,
            "title" : "Bonjour",
            "number" : 3
        }) == True, "1. Il Doit fonctionner"

        """
        Il faudrait vérifier que le type de donnée fournie correspond
        au type attendu. Ex : int pour un nombre, et pas str
        """
        assert database.insert({
            "id" : 2,
            "title" : "Bonjour",
            "number" : "Bonjour"
        }) == False, "2. Il ne doit pas fonctionner : erreur type number"

    except Exception as e:
        print(e)

    print("Données inserrées")