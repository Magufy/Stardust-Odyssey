import json
import os

from player import Ship

BLUE = (0,0,255)

def save_data(credits, selected_skin, skins):
    # Sauvegarde les données du joueur dans un fichier json
    with open("save_data.json", "w") as file:
        json.dump({
            "credits": credits,
            "selected_skin": selected_skin,
            "skins": skins  # Sauvegarder l'état de déverrouillage des skins
        }, file)

# Fonction pour charger les données
def load_data():
    try:
        # Vérifier si le fichier existe
        if not os.path.exists("save_data.json"):
            # Créer le fichier avec les valeurs par défaut
            default_data = {
                "credits": 5000,
                "selected_skin": {
                    "name": "Vaisseau Basique",
                    "price": "gratuit",
                    "unlocked": True,
                    "couleur_vaisseau": BLUE
                },
                "skins": [{
                    "name": "Vaisseau Basique",
                    "price": "gratuit",
                    "unlocked": True,
                    "couleur_vaisseau": BLUE
                }]
            }
            # Écrit ces données dans un nouveau fichier
            with open("save_data.json", "w") as file:
                json.dump(default_data, file)
            return default_data["credits"], default_data["selected_skin"], default_data["skins"]

        # Lire le fichier existant
        with open("save_data.json", "r") as file:
            try:
                data = json.load(file)

                # Vérifier si selected_skin est un dictionnaire
                selected_skin = data.get("selected_skin", Ship())
                if isinstance(selected_skin, dict) and "couleur_vaisseau" in selected_skin:
                    selected_skin["couleur_vaisseau"] = tuple(selected_skin["couleur_vaisseau"])

                # Convertir les couleur_vaisseau en tuples pour tous les skins
                skins = data.get("skins", [])
                for skin in skins:
                    if isinstance(skin, dict) and "couleur_vaisseau" in skin:
                        skin["couleur_vaisseau"] = tuple(skin["couleur_vaisseau"])

                return (
                    data.get("credits", 5000),
                    selected_skin,
                    skins
                )
            except json.JSONDecodeError:
                # Si le fichier est corrompu, créer un nouveau avec les valeurs par défaut
                default_data = {
                    "credits": 5000,
                    "selected_skin": {
                        "name": "Vaisseau Basique",
                        "price": "gratuit",
                        "unlocked": True,
                        "couleur_vaisseau": BLUE
                    },
                    "skins": [{
                        "name": "Vaisseau Basique",
                        "price": "gratuit",
                        "unlocked": True,
                        "couleur_vaisseau": BLUE
                    }]
                }
                with open("save_data.json", "w") as file:
                    json.dump(default_data, file)
                return default_data["credits"], default_data["selected_skin"], default_data["skins"]

    except Exception as e:
        print(f"Erreur lors du chargement des données: {e}")
        # Retourner les valeurs par défaut en cas d'erreur
        return 5000, {
            "name": "Vaisseau Basique",
            "price": "gratuit",
            "unlocked": True,
            "couleur_vaisseau": BLUE
        }, [{
            "name": "Vaisseau Basique",
            "price": "gratuit",
            "unlocked": True,
            "couleur_vaisseau": BLUE
        }]
