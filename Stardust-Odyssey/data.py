import json
import os

from player import Ship

# Définition de la couleur bleue (RGB)
BLUE = (0, 0, 255)

def save_data(credits, selected_skin, skins):
    # Sauvegarde les données du joueur dans un fichier JSON
    with open("save_data.json", "w") as file:
        json.dump({
            "credits": credits,  # Montant de crédits du joueur
            "selected_skin": selected_skin,  # Skin actuellement sélectionné
            "skins": skins  # Liste des skins et leur état de déverrouillage
        }, file)

def load_data():
    # Fonction pour charger les données sauvegardées
    try:
        # Vérifier si le fichier de sauvegarde existe
        if not os.path.exists("save_data.json"):
            # Si le fichier n'existe pas, créer un fichier avec des valeurs par défaut
            default_data = {
                "credits": 5000,  # Crédit de départ
                "selected_skin": {
                    "name": "Basic Ship",
                    "price": "gratuit",
                    "unlocked": True,
                    "couleur_vaisseau": BLUE
                },
                "skins": [{
                    "name": "Basic Ship",
                    "price": "gratuit",
                    "unlocked": True,
                    "couleur_vaisseau": BLUE
                }]
            }
            # Sauvegarder les données par défaut dans le fichier
            with open("save_data.json", "w") as file:
                json.dump(default_data, file)
            # Retourner les valeurs par défaut
            return default_data["credits"], default_data["selected_skin"], default_data["skins"]

        # Si le fichier existe, lire son contenu
        with open("save_data.json", "r") as file:
            try:
                data = json.load(file)

                # Récupérer le skin sélectionné, ou une instance par défaut de Ship()
                selected_skin = data.get("selected_skin", Ship())
                
                # S'assurer que la couleur est bien un tuple (au cas où ce serait une liste après lecture JSON)
                if isinstance(selected_skin, dict) and "couleur_vaisseau" in selected_skin:
                    selected_skin["couleur_vaisseau"] = tuple(selected_skin["couleur_vaisseau"])

                # Conversion des couleurs pour tous les skins
                skins = data.get("skins", [])
                for skin in skins:
                    if isinstance(skin, dict) and "couleur_vaisseau" in skin:
                        skin["couleur_vaisseau"] = tuple(skin["couleur_vaisseau"])

                # Retourner les données chargées
                return (
                    data.get("credits", 5000),
                    selected_skin,
                    skins
                )
            except json.JSONDecodeError:
                # Si le fichier est corrompu, réinitialiser avec les données par défaut
                default_data = {
                    "credits": 5000,
                    "selected_skin": {
                        "name": "Basic Ship",
                        "price": "gratuit",
                        "unlocked": True,
                        "couleur_vaisseau": BLUE
                    },
                    "skins": [{
                        "name": "Basic Ship",
                        "price": "gratuit",
                        "unlocked": True,
                        "couleur_vaisseau": BLUE
                    }]
                }
                with open("save_data.json", "w") as file:
                    json.dump(default_data, file)
                return default_data["credits"], default_data["selected_skin"], default_data["skins"]

    except Exception as e:
        # Affiche une erreur s'il y a un problème inattendu
        print(f"Erreur lors du chargement des données: {e}")
        # Retourner les valeurs par défaut en cas d'erreur
        return 5000, {
            "name": "Basic Ship",
            "price": "gratuit",
            "unlocked": True,
            "couleur_vaisseau": BLUE
        }, [{
            "name": "Basic Ship",
            "price": "gratuit",
            "unlocked": True,
            "couleur_vaisseau": BLUE
        }]
