import re

# Exemple de chaîne
exemple_chaine = "Minecraft 1.8 - 1.20.3 est une version populaire."

# Expression régulière
regex = r"(^.*?1\.)\d+(?:[- ,.\d]*)"

# Recherche de la correspondance
correspondance = re.search(regex, exemple_chaine)

# Vérification de la correspondance
if correspondance:
    resultat = correspondance.group()
    print("Résultat de la correspondance :", resultat)
else:
    print("Aucune correspondance trouvée.")

# Expression régulière
regex = r"1\.\d+([- ,.\d]*)"

# Recherche de la correspondance
correspondance = re.search(regex, exemple_chaine)

# Vérification de la correspondance
if correspondance:
    resultat = correspondance.group()
    print("Résultat de la correspondance :", resultat)
else:
    print("Aucune correspondance trouvée.")