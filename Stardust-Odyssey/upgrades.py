import pygame
import random
import time
from queue import Empty

pygame.init()
# Paramètres de la fenêtre en plein écran
window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = window.get_size()
pygame.display.set_caption("Nova Drift Prototype - Fullscreen Mode")

# Couleurs
#Définition des couleurs pour les réutiliser plusn tard facilement
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128)
BLACK = (0, 0, 0)



# Stock toutes les upgrades globales ou les passes pour les réutiliser ailleurs

# Liste des niveaux, niveaux max et les IDs mise à jour
all_upgrades = [
    {"name": "Health Up", "id": "health_up", "effect": "Max Health +20","niveau":0,"niveaumax":10,"image":"images/upgrades/1_health_up.png",
     "apply": lambda p:[setattr(p, "max_health", p.max_health + 20),setattr(p, "health", p.health + 20)]},

    {"name": "Critical chance", "id": "crit_chance_up", "effect": "Critical chance +5%","niveau":0,"niveaumax":9,"image":"images/upgrades/2_crit_chance.png",
     "apply": lambda p: setattr(p, "crit_chance", p.crit_chance + 5)},

    {"name": "Critical damages", "id": "crit_damages_up", "effect": "Critical damage +25%","niveau":0,"niveaumax":6,"image":"images/upgrades/3_crit_damage.png", #max 3x dmg
     "apply": lambda p: setattr(p, "crit_multiplier", p.crit_multiplier + 0.25)},

    {"name": "Damage Up", "id": "damage_up", "effect": "Bullet Damage +5","niveau":0,"niveaumax":10,"image":"images/upgrades/4_damage_up.png",
     "apply": lambda p: setattr(p, "damage", p.damage + 5)},

    {"name": "Bullet Speed", "id": "bullet_speed_up", "effect": "Bullet Speed +2","niveau":0,"niveaumax":5,"image":"images/upgrades/5_bullet_speed.png",
     "apply": lambda p: setattr(p, "bullet_speed", p.bullet_speed + 2)},

    {"name": "Reload Speed", "id": "reload_up", "effect": "Reload Speed +20%","niveau":0,"niveaumax":5,"image":"images/upgrades/6_reload_speed.png",
     "apply": lambda p: setattr(p, "reload_speed", p.reload_speed + 0.2)},

    {"name": "Regeneration", "id": "regen_up", "effect": "Health Regen +0.5/s","niveau":0,"niveaumax":6,"image":"images/upgrades/7_regen.png",
     "apply": lambda p: setattr(p, "regen_rate", p.regen_rate + 0.5)},

    {"name": "Enemy Bounce", "id": "enemy_bounce_up", "effect": "Enemy Bounces +1","niveau":0,"niveaumax":5,"image":"images/upgrades/8_enemi_bounce.png",
     "apply": lambda p: setattr(p, "enemy_bounces", p.enemy_bounces + 1)},

    {"name": "Wall Bounce", "id": "wall_bounce_up", "effect": "Wall Bounces +1","niveau":0,"niveaumax":5,"image":"images/upgrades/9_wall_bounce.png",
     "apply": lambda p: setattr(p, "wall_bounces", p.wall_bounces + 1)},

    {"name": "Piercing", "id": "piercing_up", "effect": "Bullet Piercing +1","niveau":0,"niveaumax":5,"image":"images/upgrades/10_piercing.png",
     "apply": lambda p: setattr(p, "bullet_piercing", p.bullet_piercing + 1)},

    {"name": "Multi Shot", "id": "multishot_up", "effect": "Parallel Shots +1","niveau":0,"niveaumax":2,"image":"images/upgrades/11_multishot.png", # Limite a 3 balles
     "apply": lambda p: setattr(p, "parallel_shots", p.parallel_shots + 1)},

    {"name": "Shield", "id": "shield_up", "effect": "Damage Reduction +10%","niveau":0,"niveaumax":5,"image":"images/upgrades/12_shield.png", # 5x10 = 50% max
     "apply": lambda p: setattr(p, "shield", min(75, p.shield + 10))},

    {"name": "Bullet Size", "id": "bullet_size_up", "effect": "Bullet Size +2","niveau":0,"niveaumax":5,"image":"images/upgrades/13_bullet_size.png",
     "apply": lambda p: setattr(p, "bullet_size", p.bullet_size + 2)},

    {"name": "Explosion", "id": "explosion_up", "effect": "Explosion Radius +20","niveau":0,"niveaumax":5,"image":"images/upgrades/14_explosion.png",
     "apply": lambda p: setattr(p, "explosion_radius", p.explosion_radius + 80 if p.explosion_radius==0 else p.explosion_radius + 20) },

    {"name": "Range Up", "id": "range_up", "effect": "Bullet Range +100","niveau":0,"niveaumax":5,"image":"images/upgrades/15_range_up.png",
     "apply": lambda p: setattr(p, "range", p.range + 100)},

    {"name": "Body Damage", "id": "body_damage_up", "effect": "Body Damage +5","niveau":0,"niveaumax":10,"image":"images/upgrades/16_body_damage.png",
     "apply": lambda p: setattr(p, "body_damage", p.body_damage + 5)},

    {"name": "Forcefield", "id": "forcefield_up", "effect": "Forcefield Damage +2/s","niveau":0,"niveaumax":5,"image":"images/upgrades/17_forcefield.png",
     "apply": lambda p: setattr(p, "forcefield_damage", p.forcefield_damage + 2)},

    {"name": "Bullet Storm", "id": "decoy_up", "effect": "Double Attack Speed, -5 Damages","niveau":0,"niveaumax":3, "image":"images/upgrades/18_decoy.png",
     "apply": lambda p: [setattr(p, "reload_speed", p.reload_speed + 0.4), setattr(p, "damage", max(1,p.damage-5))]},

    {"name": "Berserker", "id": "berserker_up", "effect": "Damage scales with missing health","niveau":0,"niveaumax":1,"image":"images/upgrades/19_berserker.png", # Non-stackable
     "apply": lambda p: setattr(p, "berserker_bonus", True)}, # Use original flag logic

    {"name": "Speed", "id": "speed_up", "effect": "Speed +10%","niveau":0,"niveaumax":5,"image":"images/upgrades/20_speed.png",
     "apply": lambda p: setattr(p, "speed", p.speed * 1.1)}, # Multiplicative speed
    
    {"name": "Light speed ability", "id": "light_speed_up", "effect": "unlock lightspeed ability  [1]","niveau":0,"niveaumax":1,"image":"images/upgrades/21_light_speed.png",
     "apply": lambda p: setattr(p, "light_speed_available", True)},

    {"name": "Invulnerability ability", "id": "invulnerability_up", "effect": "unlock invulnerability  [2]","niveau":0,"niveaumax":1,"image":"images/upgrades/22_invulnerability.png",
     "apply": lambda p: setattr(p, "invulnerability_available", True)},

    {"name": "Charged_shots ability", "id": "charge_up", "effect": "charge your shots, the next 5 shots are critical  [3]","niveau":0,"niveaumax":1,"image":"images/upgrades/23_charge_shot.png",
     "apply": lambda p: setattr(p, "charged_shots_available", True)},
]
game_upgrades=all_upgrades 

def shop_upgrades(player, p2p=None, player2=None, network_queue=None):
    """Affiche les améliorations disponibles et applique celle choisie"""
   
    # Stop toute music qui est entrain d'etre jouée
    pygame.mixer.stop()
    
    
    # Joue la musique associée au shop quand le shop est ouvert
    son_shop = pygame.mixer.Sound("sons/shop.mp3")
    son_shop.set_volume(0.5)  # Set volume to 50%
    son_shop.play(loops=-1)  # -1 means loop indefinitely
    
    
    # Détermine si le serveur hébèrge ou est client
    is_server = p2p and p2p.est_serveur if p2p else True

    
    # Le client attend pour le choix du serveur
    if p2p and not is_server:
        # Afficher le message d'attente
        font = pygame.font.Font(None, 48)
        print("[DEBUG] Entrée dans la phase d'attente du choix de l'hôte (client)")
        waiting = True

        # Afficher l'écran d'attente
        while waiting:
            window.fill((20, 20, 40))  # Dark blue background
            wait_text = font.render("En attente du choix de l'hôte...", True, WHITE)
            window.blit(wait_text, (WIDTH // 2 - wait_text.get_width() // 2, HEIGHT // 2))
            pygame.display.flip()

            
            # Gère les événements pour conserver une fenetre active
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    if p2p and not game_over_sent:
                        p2p.envoyer_donnees({'type': 'game_over'})
                        window.destroy()
                        game_over_sent = True

           
            # Vérifier les messages réseau en utilisant la file d'attente non bloquante
            if network_queue:
                try:
                    while True: # Gère tous les messages dans la queue
                        msg = network_queue.get_nowait()
                        print(f"[DEBUG] Message reçu dans la phase d'attente (client) : {msg}")
                        if msg.get('type') == 'upgrade_choice':
                            upgrade_id = msg.get('upgrade_id')
                            print(f"Client: reçu amélioration '{upgrade_id}'")

                            # Trouve et applique l'upgrade
                            selected_upgrade_config = None
                            for upgrade in game_upgrades:
                                if upgrade.get('id') == upgrade_id:
                                    selected_upgrade_config = upgrade
                                    break

                            if selected_upgrade_config:
                                # Récupérer le niveau d'amélioration envoyé par le serveur
                                server_level = msg.get('upgrade_level', 1)
                                
                                # Vérifier si cette amélioration a déjà été appliquée (pour éviter les doublons)
                                current_level = selected_upgrade_config.get('niveau', 0)
                                
                                # Mettre à jour le niveau pour qu'il corresponde à celui du serveur
                                if current_level < server_level:
                                    apply_func = selected_upgrade_config.get('apply')
                                    if apply_func:
                                        # Déterminer si c'est une amélioration de santé
                                        is_health_upgrade = msg.get('is_health_upgrade', False)
                                        
                                        # Appliquer toutes les améliorations, même celles de santé
                                        # Le serveur gère déjà la synchronisation de la santé
                                        try:
                                            apply_func(player)
                                            print(f"Client: Amélioration {upgrade_id} appliquée avec succès")
                                        except Exception as e:
                                            print(f"Client: Erreur lors de l'application de l'amélioration {upgrade_id}: {e}")
                                        
                                        # Mettre à jour le niveau localement pour le client
                                        selected_upgrade_config['niveau'] = server_level
                                        print(f"Client: Applied upgrade {upgrade_id}, new level: {selected_upgrade_config['niveau']}")
                                else:
                                    print(f"Client: Skipping already applied upgrade {upgrade_id}, current level: {current_level}, server level: {server_level}")
                                
                                waiting = False
                                # Pas besoin de quitter la boucle interne, waiting=False gère la sortie de la boucle externe
                            else:
                                print(f"Erreur: Amélioration reçue inconnue ID: {upgrade_id}")
                                # Redemander éventuellement au serveur ou gérer l’erreur
                        # Gérer d’autres types de messages si nécessaire à l’avenir
                except Empty:
                    
                    pass # Pas de message dans la queue, continue d'attendre

            #Courte pause pour éviter une utilisation excessive du CPU et permettre l'affichage
            pygame.time.delay(50)

        # La musique sera restaurée par le message 'music_update' envoyé par le serveur
        return True # Return True if upgrade was received and applied

    
    # --- Serveur (hébergeur) ou mode solo ---
   
    # Filtre upgrades qui ne dépassent pas le maximum
    available_for_selection = [upgrade for upgrade in game_upgrades if upgrade.get('niveau', 0) < upgrade['niveaumax']+1]

    # gère les cas ou il n'y a pas d'upgrades
    if not available_for_selection:
        print("Toutes les améliorations sont au niveau maximum!")
        
        # Montre un message et attend pour l'action de continuer
        font = pygame.font.Font(None, 48)
        no_upgrades_running = True
        while no_upgrades_running:
            window.fill((20, 20, 40))
            msg_text = font.render("Toutes les améliorations sont au max!", True, YELLOW)
            cont_text = pygame.font.Font(None, 36).render("Appuyez sur une touche pour continuer", True, WHITE)
            window.blit(msg_text, (WIDTH // 2 - msg_text.get_width() // 2, HEIGHT // 2 - 30))
            window.blit(cont_text, (WIDTH // 2 - cont_text.get_width() // 2, HEIGHT // 2 + 30))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return False
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    no_upgrades_running = False
            pygame.time.delay(10)
        return True # Continue le jeu

    
    # Selection aléatoire de trois upgrades
    upgrades_to_show = random.sample(available_for_selection, min(3, len(available_for_selection)))
    font = pygame.font.Font(None, 36)
    shop_running = True
    selected_index = None
    upgrade_rects = [] # Store rectangles and their indices

    
    # --- Hébèrge la loupe UI 
    selection_block_time = time.time() + 2 
    while shop_running:
        window.fill((20, 20, 40))  # Fond bleu foncé
        upgrade_rects.clear()

        # Affiche le titre
        title = font.render("Choisissez une amélioration", True, WHITE)
        title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 4))
        window.blit(title, title_rect)

        # Affiche les améliorations disponibles
        mouse_pos = pygame.mouse.get_pos()
        
        
        # Calcule la position pour les 3 cases pour les upgrades cote à cote
        box_width = WIDTH // 3 - 40 # Etendue de chaque case upgrade avec des marges
        box_height = 300   #hauteur de chaque case upgrade
        margin = 20  #Marge entre les cases
        
        for i, upgrade in enumerate(upgrades_to_show):
            
            # Position de chaque cases horizontalement cote à cote
            x_pos = margin + i * (box_width + margin)
            y_pos = HEIGHT // 2 - box_height // 2
            
           
            # Création du rétangle principal pour cette upgrade
            rect = pygame.Rect(x_pos, y_pos, box_width, box_height)
            upgrade_rects.append((rect, i))
            
            is_hovered = rect.collidepoint(mouse_pos)
            color = YELLOW if is_hovered else WHITE
            border_width = 3 if is_hovered else 2
            pygame.draw.rect(window, color, rect, border_width, border_radius=5)
            
           
            # Nom et niveau en haut
            level_text = f" (Niv {int(upgrade['niveau'])}/{upgrade.get('niveaumax', 1)})"
            
            name_text = font.render(f"{i+1}. {upgrade['name']}{level_text}", True, color)
            name_rect = name_text.get_rect(center=(rect.centerx, rect.y + 30))
            window.blit(name_text, name_rect)
            
            # Image au milieu
            try:
                image_path = upgrade.get('image')
                if image_path:
                    upgrade_image = pygame.image.load(image_path).convert_alpha()
                    
                    #échelle de l'image à faire entrer dans la case
                    image_size = min(box_width - 40, 120)
                    upgrade_image = pygame.transform.scale(upgrade_image, (image_size, image_size))
                    image_rect = upgrade_image.get_rect(center=(rect.centerx, rect.centery))
                    window.blit(upgrade_image, image_rect)
            except Exception as e:
                print(f"Error loading upgrade image: {e}")
                
                # Déssine un espace réservé si l'image ne se charge pas
                placeholder = pygame.Surface((80, 80))
                placeholder.fill(GRAY)
                placeholder_rect = placeholder.get_rect(center=(rect.centerx, rect.centery))
                window.blit(placeholder, placeholder_rect)
            
            # Description en bas
            effect_font = pygame.font.Font(None, 28)
            effect_text = effect_font.render(upgrade['effect'], True, GRAY)
            effect_rect = effect_text.get_rect(center=(rect.centerx, rect.bottom - 30))
            window.blit(effect_text, effect_rect)

        pygame.display.flip()

        # Gestion des événements
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if time.time() >= selection_block_time:
                    click_pos = event.pos
                    for rect, index in upgrade_rects:
                        if rect.collidepoint(click_pos):
                            selected_index = index
                            shop_running = False
                            break

        pygame.time.delay(10)

   
    # --- Fin du la boucle UI de l'invité ---

 
    # gère les upgrades sélctionées
    if selected_index is not None and 0 <= selected_index < len(upgrades_to_show):
        selected_upgrade = upgrades_to_show[selected_index]
        apply_func = selected_upgrade.get('apply')
        upgrade_id = selected_upgrade.get('id') # Get ID for lookup and network

        if not apply_func:
            print(f"Erreur: Fonction 'apply' manquante pour l'amélioration {selected_upgrade.get('name')}")
            return False # Indique une panne/échec

        
        # Applique au vaisseau de l'invité (Player 1)
        apply_func(player)

        
        # Dans multijoueur, applique TOUTES les upgrades à player 2 localement
        if player2:  # Appliquer TOUTES les upgrades au joueur 2
            apply_func(player2)  # Apply upgrade locally to player 2
     
        
        # Trouve l'upgrade originale dans game_upgrades pour incrémenter ce niveau
        original_upgrade_config = None
        if upgrade_id:
            for upgrade in game_upgrades:
                if upgrade.get('id') == upgrade_id:
                    original_upgrade_config = upgrade
                    break

        if original_upgrade_config:
            
            # Assure que 'niveau' existe avant d'incrémenter
            if 'niveau' not in original_upgrade_config:
                original_upgrade_config['niveau'] = 1 # Initialise s'il manque
            original_upgrade_config['niveau'] += 1
            print(f"Amélioration appliquée localement: {original_upgrade_config['name']} (Niveau {original_upgrade_config['niveau']})")
        else:
             print(f"Erreur: Impossible de trouver l'amélioration originale avec ID: {upgrade_id} pour incrémenter le niveau.")
             
             # Continue dans tous les cas, mais le niveau ne suit pas correctement

        
        # dans multijoueur (serveur), envoie le choix de l'upgrade au client
        if p2p and is_server:
            if upgrade_id:
                # Utiliser original_upgrade_config au lieu de selected_upgrade_config qui n'est pas défini ici
                # Déterminer si c'est une amélioration de santé pour informer le client
                is_health_upgrade = False
                if original_upgrade_config:
                    effect_text = original_upgrade_config.get('effect', '').lower()
                    is_health_upgrade = 'health' in effect_text or 'santé' in effect_text or 'vie' in effect_text
                
                # Envoyer l'amélioration avec des informations supplémentaires
                p2p.envoyer_donnees({
                    'type': 'upgrade_choice', 
                    'upgrade_id': upgrade_id,
                    'is_health_upgrade': is_health_upgrade,
                    'upgrade_level': original_upgrade_config.get('niveau', 1) if original_upgrade_config else 1
                })
                print(f"Amélioration envoyée au client: {upgrade_id} (health: {is_health_upgrade})")
            else:
                print("Erreur: ID d'amélioration manquant pour l'envoi réseau.")

        return True # Upgrade sélectionnée at gérée
    elif selected_index is None:
        print("Aucune amélioration sélectionnée (Shop fermé?).")
        return False  # Indique qu'aucune sélection n'a été faite 
    else:
        print(f"Erreur: Index sélectionné invalide: {selected_index}")
        return False
