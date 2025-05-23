import pygame
import math
import threading
import time
from queue import Queue
import socket
import cv2 # (pip install opencv-python)
import numpy as np

from player import Ship, creer_vaisseau, Bullet
from damage_numbers import DamageNumberManager
from upgrades import shop_upgrades, all_upgrades
from spawnwave import spawn_wave
from multijoueur import P2PCommunication
from data import load_data, save_data
from boutons import Button, InputBox
from enemies import BasicEnemy, TankEnemy, ShooterEnemy, LinkEnemy, Tank_Boss, Dash_Boss, Laser_Boss, Mothership_Boss


# Couleurs
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128)
BLACK = (0, 0, 0)

pygame.init()
#Paramètres de la fenêtre en plein écran
window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = window.get_size()
pygame.display.set_caption("Nova Drift Prototype - Fullscreen Mode")


# Game loop
def game_loop(selected_skin, shop, p2p=None, remote_skin_info=None):
    global enemies
    global shop_upgrade # Ensure shop_upgrade is accessible

    # Initialisation du gestionnaire de dégâts
    damage_manager = DamageNumberManager()

    # upgrades à 0
    for upgrade in shop_upgrade:
        upgrade['niveau'] = 1 # Reset level to 1

    # initialisation de running
    running = True

    # Initialisation du serveur/client
    is_server = p2p and p2p.est_serveur if p2p else True

    # Initialisation des vaisseau
    local_ship = None  # Vaisseau local (celui que contrôle ce joueur)
    remote_ship = None  # Vaisseau distant (celui que contrôle l'autre joueur)

    # Création du vaisseau local
    local_ship = creer_vaisseau(selected_skin, damage_manager=damage_manager)

    # Marquer le vaisseau local
    local_ship.is_local = True


    # Création du vaisseau distant si en multijoueur
    if p2p and remote_skin_info:
        remote_ship = creer_vaisseau(remote_skin_info, damage_manager=damage_manager)
        # Marquer le vaisseau distant
        remote_ship.is_local = False

    # Positions initiales des vaisseaux différentes selon serveur/client
    server_pos = (WIDTH * 2 // 3, HEIGHT // 2)  # Position du créateur
    client_pos = (WIDTH // 3, HEIGHT // 2)     # Position de celui qui rejoint

    # Placer les vaisseaux aux positions correctes
    if p2p:
        if is_server:
            # Si je suis le serveur
            local_ship.rect.center = server_pos   # Je me place à la position serveur
            remote_ship.rect.center = client_pos  # L'autre joueur est à la position client
        else:
            # Si je suis le client
            local_ship.rect.center = client_pos   # Je me place à la position client
            remote_ship.rect.center = server_pos  # L'autre joueur est à la position serveur
    else:
        # Mode solo
        local_ship.rect.center = (WIDTH // 2, HEIGHT // 2)

    # Initialisation des états de jeu
    clock = pygame.time.Clock()
    
    # Initialisation de la musique et des ennemis
    if is_server or not p2p:
        # L'hôte ou le mode solo gère la génération des ennemis et la musique
        wave_result = spawn_wave(1)
        enemies = wave_result[0]  # Get just the enemies
        cycle = wave_result[1] if len(wave_result) > 1 else 1
        
        # Déterminer le type de musique en fonction du numéro de vague
        cycle_wave = 1 % 20
        music_type = "boss_final" if cycle_wave ==0 else "boss" if cycle_wave % 5 == 0 else "vague"
        
        # Si en multijoueur, envoyer le type de musique au client
        if p2p:
            p2p.envoyer_donnees({
                'type': 'music_update',
                'music_type': music_type
            })
    else:
        # Le client ne génère pas d'ennemis, il les reçoit de l'hôte
        enemies = []
        # La musique sera jouée lorsque le client recevra l'information de l'hôte
    
    wave_in_progress = False # Initialize flag

    # Configurer les ennemis pour le multijoueur et set initial wave_in_progress for host
    if is_server or not p2p: # hôte ou mode solo
        if len(enemies) > 0:
            wave_in_progress = True # vague en cours
        if p2p: # hôte
             for enemy in enemies:
                 enemy.p2p_comm = p2p
                 if isinstance(enemy, (ShooterEnemy, LinkEnemy, Tank_Boss, Dash_Boss, Laser_Boss, Mothership_Boss)) and remote_ship:
                     enemy.second_player = remote_ship

    #variables 
    wave_number = 1
    score = 0
    font = pygame.font.Font(None, 36)
    wave_text_timer = 0

    # Variables réseau
    last_network_update = 0
    network_update_rate = 1/30  # 30FPS pour de meilleures performances
    game_over_sent = False

    # file d'attente thread-safe pour la communication réseau
    network_queue = Queue() if p2p else None

    # Fonction pour recevoir les données réseau dans un thread séparé
    def receive_data_thread(p2p_conn, queue):
        while p2p_conn and p2p_conn.running:
            try:
                messages = p2p_conn.recevoir_donnees()
                if messages:
                    for msg in messages:
                        queue.put(msg)
                time.sleep(0.01)  # Petit délai pour éviter une utilisation excessive du CPU
            except Exception as e:
                print(f"Erreur dans le thread de réception: {e}")
                if p2p_conn:
                    p2p_conn.running = False
                break

    # Démarrer le thread de réception réseau si en multijoueur
    if p2p:
        receive_thread = threading.Thread(target=receive_data_thread, args=(p2p, network_queue), daemon=True)
        receive_thread.start()

    # Boucle principale du jeu
    while running:
        current_time = time.time()
        window.fill(BLACK)

        # Traitement des événements
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                if p2p and not game_over_sent:
                    p2p.envoyer_donnees({'type': 'game_over'})
                    game_over_sent = True
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and local_ship.stun_timer==0:
                # Le joueur tire avec son propre vaisseau
                local_ship.shoot()

        # Traitement des messages réseau
        if p2p and network_queue and not network_queue.empty():
            while not network_queue.empty():
                msg = network_queue.get()
                msg_type = msg.get('type')

                if msg_type == 'state':
                    # Mise à jour de l'état du joueur distant (Player 1 pour le client, Player 2 pour le serveur)
                    remote_player_data = msg.get('player')
                    remote_bullets_data = msg.get('bullets', []) # Bullets from the other player

                    if remote_player_data and remote_ship:
                        #update l'etat de romote_ship
                        remote_ship.rect.centerx = remote_player_data.get('x', remote_ship.rect.centerx)
                        remote_ship.rect.centery = remote_player_data.get('y', remote_ship.rect.centery)
                        remote_ship.angle = (remote_player_data.get('angle', remote_ship.angle)) % 360  # Correction de la rotation pour le multijoueur
                        remote_ship.forcefield_damage = remote_player_data.get('forcefield_damage', remote_ship.forcefield_damage)
                        remote_ship.last_forcefield_time = remote_player_data.get('last_forcefield_time', remote_ship.last_forcefield_time)

                        # si serveur, update les vies de remote_ship (P2) mais que de damage_update ou collisions
                        # si client, update les vies de remote_ship (P1) mais que des messages 'state'

                        if not is_server:
                            remote_ship.health = remote_player_data.get('health', remote_ship.health)
                            remote_ship.invincible_time = remote_player_data.get('invincible_time', remote_ship.invincible_time)
                            remote_ship.regen_rate = remote_player_data.get('regen_rate', remote_ship.regen_rate)
                            remote_ship.max_health = remote_player_data.get('max_health', remote_ship.max_health)
                            remote_ship.stun_timer = remote_player_data.get('stun_timer', remote_ship.stun_timer) # Update P1 stun
                            remote_ship.forcefield_damage = remote_player_data.get('forcefield_damage', remote_ship.forcefield_damage)
                            remote_ship.last_forcefield_time = remote_player_data.get('last_forcefield_time', remote_ship.last_forcefield_time)

                        # update l'image de remote_ship
                        remote_ship.image = pygame.transform.rotate(remote_ship.original_image, remote_ship.angle)
                        remote_ship.rect = remote_ship.image.get_rect(center=remote_ship.rect.center)

                        # Mettre à jour les balles du joueur distant
                        # Au lieu de tout effacer, on garde les balles existantes et on ajoute/met à jour celles reçues
                        # Cela permet d'éviter les problèmes de synchronisation
                        
                        # Créer un dictionnaire des balles existantes pour faciliter la recherche
                        existing_bullets = {}
                        for idx, bullet in enumerate(remote_ship.bullets[:]):
                            # On utilise la position comme clé approximative
                            key = (round(bullet.x), round(bullet.y))
                            existing_bullets[key] = idx
                        
                        # Traiter les balles reçues
                        updated_bullets = []
                        for b_data in remote_bullets_data:
                            # Arrondir les coordonnées pour la recherche
                            key = (round(b_data['x']), round(b_data['y']))
                            
                            # Vérifier si cette balle existe déjà
                            if key in existing_bullets:
                                # Mettre à jour la balle existante
                                idx = existing_bullets[key]
                                if idx < len(remote_ship.bullets):
                                    bullet = remote_ship.bullets[idx]
                                    # Mettre à jour la position et l'angle
                                    bullet.x = b_data['x']
                                    bullet.y = b_data['y']
                                    bullet.angle = b_data['angle']
                                    bullet.radius = b_data.get('radius', bullet.radius)
                                    # Ajouter à la liste des balles mises à jour
                                    updated_bullets.append(bullet)
                                    # Supprimer de la liste des existantes
                                    del existing_bullets[key]
                            else:
                                # Créer une nouvelle balle
                                bullet = Bullet(b_data['x'], b_data['y'], b_data['angle'], remote_ship)
                                bullet.radius = b_data.get('radius', remote_ship.bullet_size)
                                # Définir les attributs d'explosion si présents
                                if b_data.get('is_exploding', False):
                                    bullet.is_exploding = True
                                    bullet.explosion_radius = b_data.get('explosion_radius', 0)
                                    bullet.explosion_time = b_data.get('explosion_time', 0)
                                    bullet.explosion_alpha = b_data.get('explosion_alpha', 255)
                                # Ajouter à la liste des balles mises à jour
                                updated_bullets.append(bullet)
                        
                        # Remplacer la liste des balles par les balles mises à jour
                        remote_ship.bullets = updated_bullets

                    # Le client reçoit l'état des ennemis et son propre état (santé/status) du serveur
                    if not is_server:
                        # Update Enemies
                        server_enemies_data = msg.get('enemies', [])
                        # remplace la liste d'enemis entiere
                        enemies.clear()
                        for enemy_data in server_enemies_data:
                            enemy = create_enemy_from_data(enemy_data)
                            if enemy:
                                enemy.p2p_comm = p2p
                                enemy.second_player = local_ship # vaisseau client
                                enemies.append(enemy)

                        # wave_in_progress flag pour le client
                        if not wave_in_progress and len(enemies) > 0:
                            wave_in_progress = True

                        # Update Wave Number
                        wave_number = msg.get('wave', wave_number)

                        # Update l'etat du client
                        player2_data = msg.get('player2')
                        if player2_data and local_ship:
                            local_ship.angle = (player2_data.get('angle', local_ship.angle) - 90) % 360  # Correction de la rotation pour le multijoueur
                            local_ship.invincible_time = player2_data.get('invincible_time', local_ship.invincible_time)
                            local_ship.regen_rate = player2_data.get('regen_rate', local_ship.regen_rate)
                            local_ship.max_health = player2_data.get('max_health', local_ship.max_health)
                            local_ship.stun_timer = player2_data.get('stun_timer', local_ship.stun_timer) # Update local stun timer
                            local_ship.forcefield_damage = player2_data.get('forcefield_damage', local_ship.forcefield_damage)
                            local_ship.last_forcefield_time = player2_data.get('last_forcefield_time', local_ship.last_forcefield_time)


                elif msg_type == 'damage_update':
                    # Mise à jour spécifique pour la santé du joueur 2 (côté client) ou joueur 1 (côté serveur)
                    if not is_server and local_ship: # Client updates local ship (P2)
                        local_ship.health = msg.get('player2_health', local_ship.health)
                        local_ship.invincible_time = msg.get('player2_invincible_time', local_ship.invincible_time)
                        local_ship.regen_rate = msg.get('player2_regen_rate', local_ship.regen_rate)
                        local_ship.max_health = msg.get('player2_max_health', local_ship.max_health)
                        local_ship.stun_timer = msg.get('player2_stun_timer', local_ship.stun_timer) # MAJ Stun
                        local_ship.forcefield_damage = msg.get('player2_forcefield_damage', local_ship.forcefield_damage)
                        local_ship.last_forcefield_time = msg.get('player2_last_forcefield_time', local_ship.last_forcefield_time)
                
                elif msg_type == 'music_update':
                    # Le client reçoit l'information sur la musique à jouer
                    music_type = msg.get('music_type')
                    if music_type:
                        # Arrête la musique en cours
                        pygame.mixer.stop()
                        
                        # Jouer la musique appropriée à la fenetre
                        if music_type == 'boss_final':
                            son_boss_final = pygame.mixer.Sound("sons/boss_final.mp3")
                            son_boss_final.set_volume(0.4)  # Volume à 40%
                            son_boss_final.play(loops=-1)  # -1 signifie boucle infinie
                        if music_type == 'boss':
                            son_boss = pygame.mixer.Sound("sons/boss.mp3")
                            son_boss.set_volume(0.4)  # Volume à 40%
                            son_boss.play(loops=-1)  # -1 signifie boucle infinie
                        elif music_type == 'vague':
                            son_vague = pygame.mixer.Sound("sons/vague.mp3")
                            son_vague.set_volume(0.3)  # Volume à 30%
                            son_vague.play(loops=-1)  # -1 signifie boucle infinie
                    elif is_server and remote_ship: # update du serveur de remote ship (P1 de la vue du client)
                        remote_ship.health = msg.get('player1_health', remote_ship.health)
                        remote_ship.invincible_time = msg.get('player1_invincible_time', remote_ship.invincible_time)
                        remote_ship.regen_rate = msg.get('player1_regen_rate', remote_ship.regen_rate)
                        remote_ship.max_health = msg.get('player1_max_health', remote_ship.max_health)
                        remote_ship.stun_timer = msg.get('player1_stun_timer', remote_ship.stun_timer)
                        remote_ship.forcefield_damage = msg.get('player1_forcefield_damage', remote_ship.forcefield_damage)
                        remote_ship.last_forcefield_time = msg.get('player1_last_forcefield_time', remote_ship.last_forcefield_time)

                elif msg_type == 'game_over':
                    running = False
                    show_game_over(score)
                    break # sort de la boucle des msg_type

                elif msg_type == 'start_upgrade_phase':
                    # le client recoit le signal d'entrée dans le shop
                    if not is_server:
                        enemies.clear() # Clear les enemis
                        window.fill(BLACK) # clear le fond
                        pygame.display.flip() # Update l'affichage

                        # Call shop_upgrades, qui va mettre le joueur 2 dans la boucle d'attente
                        upgrade_result = shop_upgrades(local_ship, p2p, remote_ship, network_queue)

                        if not upgrade_result: # par exemple, si l'hote quitte le jeu
                            running = False
                            # affiche le game over au 2eme joueur
                        else:
                            wave_text_timer = 120 # affichage de la vague
                            wave_in_progress = False # temps qu'il n'y a pas d'enemis


        # Vérifier si les joueurs sont morts
        if local_ship.health <= 0 or (remote_ship and remote_ship.health <= 0):
            # Si un des deux joueurs est mort, c'est game over
            if p2p and not game_over_sent:
                p2p.envoyer_donnees({'type': 'game_over'})
                game_over_sent = True
            running = False
            show_game_over(score)
            break # arrete game loop

        # Mise à jour des mouvements
        if running:
            # Mise à jour du vaisseau local (contrôlé par ce joueur)
            local_ship.update(enemies)
            local_ship.move()         # Contrôle du mouvement avec les touches
            local_ship.rotate_to_mouse() # Contrôle de la rotation avec la souris

            # Mise à jour du vaisseau distant (pas de contrôle direct)
            if remote_ship:
                remote_ship.update(enemies)

            # Empêcher la santé négative
            local_ship.health = max(0, local_ship.health)
            if remote_ship:
                remote_ship.health = max(0, remote_ship.health)

        # Envoyer l'état du joueur via le réseau
        if p2p and running and current_time - last_network_update >= network_update_rate:
            # Envoyer l'état du vaisseau local
            player_state = {
                'type': 'state',
                'player': {
                    'x': local_ship.rect.centerx,
                    'y': local_ship.rect.centery,
                    'angle': (local_ship.angle + 90) % 360,  # Correction de la rotation pour le multijoueur
                    'forcefield_damage': local_ship.forcefield_damage,
                    'last_forcefield_time': local_ship.last_forcefield_time,
                    # le serveur envoi ses info au client
                },
                # Envoyer les informations des balles pour que l'autre joueur puisse les voir
                'bullets': [{
                    'x': b.x, 'y': b.y, 'angle': b.angle, 'radius': b.radius,
                    'is_exploding': getattr(b, 'is_exploding', False),
                    'explosion_radius': getattr(b, 'explosion_radius', 0),
                    'explosion_time': getattr(b, 'explosion_time', 0),
                    'explosion_alpha': getattr(b, 'explosion_alpha', 255)
                } for b in local_ship.bullets]
            }

            # Le serveur envoie aussi l'état des ennemis et du joueur 2
            if is_server:
                # le serveur envoi les info de P1
                player_state['player']['health'] = local_ship.health
                player_state['player']['invincible_time'] = local_ship.invincible_time
                player_state['player']['regen_rate'] = local_ship.regen_rate
                player_state['player']['max_health'] = local_ship.max_health
                player_state['player']['stun_timer'] = local_ship.stun_timer # Add stun timer
                player_state['player']['forcefield_damage'] = local_ship.forcefield_damage
                player_state['player']['last_forcefield_time'] = local_ship.last_forcefield_time

                # etat des enemis
                enemies_data = []
                for e in enemies:
                    enemy_state = {
                        'id': id(e), # Client might not use this ID directly now
                        'x': e.x, 'y': e.y, 'health': e.health, 'type': e.__class__.__name__,
                        'angle': getattr(e, 'angle', 0), # *** ADD ANGLE HERE ***
                        'target_x': getattr(e, 'target_x', None),
                        'target_y': getattr(e, 'target_y', None),
                        'is_moving': getattr(e, 'is_moving', None),
                        'stationary_timer': getattr(e, 'stationary_timer', None),
                    }

                    # lasers actifs des linkenemies
                    if isinstance(e, LinkEnemy):
                        enemy_state['active_lasers'] = e.active_lasers

                    # projectiles enemis
                    if hasattr(e, 'projectiles'): #verifie si l'attribut projectiles est present chez e (enemy)
                        # rend les projectiles serialisables
                        serializable_projectiles = []
                        if isinstance(e.projectiles, list):
                           for proj in e.projectiles:
                               if isinstance(proj, dict):
                                   serializable_projectiles.append(proj)
                        enemy_state['projectiles'] = serializable_projectiles


                    # attributs de boss
                    if hasattr(e, 'maxhealth'):
                        enemy_state['maxhealth'] = e.maxhealth

                    if hasattr(e, 'healthbar'):
                        enemy_state['healthbar'] = e.healthbar

                    if hasattr(e, 'bossname'):
                        enemy_state['bossname'] = e.bossname

                    if hasattr(e, 'shoot_cooldown'):
                        enemy_state['shoot_cooldown'] = e.shoot_cooldown

                    if hasattr(e, 'action_timer'):
                        enemy_state['action_timer'] = e.action_timer

                    if hasattr(e, 'shooting'):
                        enemy_state['shooting'] = e.shooting

                    enemies_data.append(enemy_state)

                # etat du P2
                player2_state = {}
                if remote_ship:
                    player2_state = {
                        'health': remote_ship.health, # vies de P2
                        'invincible_time': remote_ship.invincible_time,
                        'regen_rate': remote_ship.regen_rate,
                        'max_health': remote_ship.max_health,
                        'stun_timer': remote_ship.stun_timer, # Add stun timer
                        'forcefield_damage': remote_ship.forcefield_damage,
                        'last_forcefield_time': remote_ship.last_forcefield_time,
                        # balles evoyées par le client, pas besoin du serveur
                    }

                player_state.update({
                    'enemies': enemies_data,
                    'wave': wave_number,
                    'player2': player2_state # etat du P2 vue du serv
                })
            # le client envoie ses infos(pos, angle, bullets)

            p2p.envoyer_donnees(player_state)
            last_network_update = current_time

        # Mettre à jour les balles et le score
        # Mettre à jour les balles du joueur local
        update_bullets(local_ship, enemies, damage_manager)
        
        # Mettre à jour les balles du joueur distant si présent
        if remote_ship:
            update_bullets(remote_ship, enemies, damage_manager)

        # Mettre à jour les ennemis (serveur uniquement en multijoueur)
        if running and (is_server or not p2p):
            for enemy in enemies[:]:
                # Déterminer la cible (joueur le plus proche en multijoueur)
                target_player = local_ship
                if remote_ship:
                    dist1 = math.hypot(enemy.x - local_ship.rect.centerx, enemy.y - local_ship.rect.centery)
                    dist2 = math.hypot(enemy.x - remote_ship.rect.centerx, enemy.y - remote_ship.rect.centery)
                    target_player = local_ship if dist1 < dist2 else remote_ship

                    # Configurer les ennemis pour qu'ils puissent accéder aux deux joueurs
                    if isinstance(enemy, (ShooterEnemy, LinkEnemy, Tank_Boss, Dash_Boss, Laser_Boss, Mothership_Boss)):
                        enemy.second_player = remote_ship if target_player == local_ship else local_ship
                    if p2p:
                        enemy.p2p_comm = p2p

                if enemy.type == [Mothership_Boss] or enemy.type == [LinkEnemy]:
                    enemy.update(target_player,enemies)
                else:
                    enemy.update(target_player)

                # Vérifier la collision avec les joueurs
                collision_p1 = enemy.check_collision(local_ship)
                if collision_p1:
                    local_ship.health = max(0, local_ship.health)

                if remote_ship:
                    collision_p2 = enemy.check_collision(remote_ship)
                    if collision_p2:
                        remote_ship.health = max(0, remote_ship.health)
                        # detection des collision par le serveur
                        if is_server and p2p:
                            p2p.envoyer_donnees({
                                'type': 'damage_update',
                                'player2_health': remote_ship.health,
                                'player2_invincible_time': remote_ship.invincible_time,
                                'player2_regen_rate': remote_ship.regen_rate, # Include these in case they change
                                'player2_max_health': remote_ship.max_health, # Include these in case they change
                                'player2_stun_timer': remote_ship.stun_timer, # Ajouter stun timer
                                'player2_forcefield_damage': remote_ship.forcefield_damage,
                                'player2_last_forcefield_time': remote_ship.last_forcefield_time
                            })

                # Supprimer les ennemis morts
                if enemy.health <= 0:
                    if enemy in enemies:
                        enemies.remove(enemy)
                        score += 10

        # Dessiner les éléments du jeu
        local_ship.draw(window)
        if remote_ship:
            remote_ship.draw(window)

        # fait les enemis seulement si la vague est en cours
        if wave_in_progress or (p2p and is_server):
             for enemy in enemies:
                 enemy.draw(window)
        elif not p2p: # mode solo fait toujours enemy.draw
             for enemy in enemies:
                 enemy.draw(window)


        # Dessiner les balles
        for bullet in local_ship.bullets:
            bullet.draw(window)
        if remote_ship:
            for bullet in remote_ship.bullets:
                bullet.draw(window)
        
        # Mettre à jour et dessiner les nombres de dégâts
        damage_manager.update()
        damage_manager.draw(window)
        
        # Dessiner les informations de jeu
        draw_game_info(window, font, score, local_ship, wave_number, wave_text_timer, remote_ship)

        # Minuteur de texte de vague
        if wave_text_timer > 0:
            wave_text_timer -= 1

        # logique de fin de vague
        # le serveur indique si la vague est finie
        if running and (is_server or not p2p) and len(enemies) == 0 and wave_in_progress:
            wave_in_progress = False # fin de la vague

            # le serveur envoie au client que la phase d'upgrade commence
            if p2p and is_server:
                p2p.envoyer_donnees({'type': 'start_upgrade_phase'})

            # le serveur ou le mode solo ouvre le shop
            upgrade_result = shop_upgrades(local_ship, p2p, remote_ship, network_queue)

            if not upgrade_result: # si le shop a ete quitté sans resultat
                running = False
                if p2p and not game_over_sent:
                    p2p.envoyer_donnees({'type': 'game_over'})
                    game_over_sent = True
                # la condition 'running' fait le game over
            else:
                # vague suivante
                wave_number += 1
                wave_text_timer = 120 # texte de vague

                print("[DEBUG] Server/SP: Spawning next wave.")
                result = spawn_wave(wave_number)
                enemies = result[0]
                if len(enemies) > 0:
                    wave_in_progress = True # flag pour l vague en cours
                
                # Déterminer le type de musique en fonction du numéro de vague
                cycle_wave = wave_number % 20
                music_type = "boss" if cycle_wave % 5 == 0 else "vague"
                
                # Si en multijoueur, envoyer le type de musique au client
                if p2p and is_server:
                    p2p.envoyer_donnees({
                        'type': 'music_update',
                        'music_type': music_type
                    })
                    print(f"[DEBUG] Server: Envoi du type de musique '{music_type}' au client.")

                # Configure new enemies for multijoueur (server only)
                if p2p and is_server: # si serveur
                    for enemy in enemies:
                        enemy.p2p_comm = p2p
                        # info du remote_ship pour les enemis
                        if isinstance(enemy, (ShooterEnemy, LinkEnemy, Tank_Boss, Dash_Boss, Laser_Boss, Mothership_Boss)) and remote_ship:
                            enemy.second_player = remote_ship

        clock.tick(60)
        pygame.display.flip()
          # Limiter à 60 FPS pour l'affichage

    # Nettoyage de fin de partie
    if p2p:
        p2p.fermer()

    # Sauvegarder les crédits gagnés
    shop.credits += score//10
    save_data(shop.credits, shop.selected_skin, shop.skins)
    print("sauvegarde",shop.credits,score//10)
    
    # Remettre la musique du menu
    pygame.mixer.stop()  # Arrêter toute musique en cours
    menu_music = pygame.mixer.Sound("sons/menu.mp3")
    menu_music.set_volume(0.4)  # Volume à 40%
    menu_music.play(loops=-1)  # Boucle infinie

def update_bullets(ship, enemies, damage_manager=None):
    for bullet in ship.bullets[:]:
        bullet.move()

        # check la portée
        if bullet.distance_traveled >= bullet.max_range:
            bullet.explode(enemies, damage_manager)
            if bullet in ship.bullets:
                ship.bullets.remove(bullet)
            continue

        # collision aux murs
        wall_collided = False
        if bullet.x - bullet.radius < 0 or bullet.x + bullet.radius > WIDTH:
            if bullet.wall_bounces > 0:
                bullet.bounce_off_wall("vertical")
                bullet.x = max(bullet.radius, min(WIDTH - bullet.radius, bullet.x))
            else:
                wall_collided = True
        elif bullet.y - bullet.radius < 0 or bullet.y + bullet.radius > HEIGHT:
            if bullet.wall_bounces > 0:
                bullet.bounce_off_wall("horizontal")
                bullet.y = max(bullet.radius, min(HEIGHT - bullet.radius, bullet.y))
            else:
                wall_collided = True

        if wall_collided:
            bullet.explode(enemies, damage_manager)
            if bullet in ship.bullets:
                ship.bullets.remove(bullet)
            continue

        # collisions aux ennemis
        enemies_hit_this_step = set()

        for enemy in enemies[:]:
            # Skip enemies already hit by this bullet (if no piercing/bounces left)
            if enemy in bullet.hit_enemies:
                if bullet.piercing <= 0 and bullet.enemy_bounces <= 0:
                    continue

            distance = math.hypot(bullet.x - enemy.x, bullet.y - enemy.y)
            if distance < bullet.radius + enemy.radius:
                if enemy not in enemies_hit_this_step:
                    # Calculate damage
                    actual_damage = bullet.damage
                    # Apply berserker bonus if applicable
                    if hasattr(ship, 'berserker_bonus') and ship.berserker_bonus:
                        missing_health_ratio = (ship.max_health - ship.health) / ship.max_health
                        bonus_damage = actual_damage * missing_health_ratio
                        actual_damage += bonus_damage

                    # Apply damage and show damage number
                    enemy.health -= actual_damage
                    if damage_manager:
                        # Ajouter le nombre de dégâts uniquement si c'est le vaisseau local
                        damage_manager.add_damage_number(enemy.x, enemy.y - enemy.radius, actual_damage, getattr(bullet, 'is_critical', False))

                    # Track hit enemies
                    bullet.hit_enemies.add(enemy)
                    enemies_hit_this_step.add(enemy)

                    # Handle piercing/bouncing AFTER damage application
                    if bullet.piercing > 0:
                        bullet.piercing -= 1
                    elif bullet.enemy_bounces > 0:
                        bullet.bounce_off_enemy(enemy.x, enemy.y)
                        # Ne pas effacer hit_enemies pour éviter les hits multiples
                    else:
                        # No piercing or bounces left, bullet should be destroyed
                        bullet.explode(enemies, damage_manager)
                        if bullet in ship.bullets:
                            ship.bullets.remove(bullet)
                        break

        # Update explosion animation
        if bullet in ship.bullets and bullet.is_exploding:
            bullet.explode(enemies) # Continue drawing/updating explosion
            if bullet.explosion_time <= 0:
                if bullet in ship.bullets:
                    ship.bullets.remove(bullet)


def show_game_over(score):
    """Affiche l'écran de fin de partie"""
    running = True
    font_large = pygame.font.Font(None, 72)
    font_medium = pygame.font.Font(None, 48)
    font_small = pygame.font.Font(None, 36)
    credits_earned = score//10

    # Textes
    game_over_text = font_large.render("GAME OVER", True, RED)
    score_text = font_medium.render(f"Score: {score}", True, WHITE)
    credits_text = font_medium.render(f"Credits earned: {credits_earned}", True, WHITE)
    continue_text = font_small.render("Press a key to continue", True, GRAY)

    # Minuteur pour rester un minimum sur l'écran de game over
    min_display_time = 180  # 3 secondes à 60 FPS
    start_time = pygame.time.get_ticks()

    while running:
        current_time = pygame.time.get_ticks()
        elapsed_time = current_time - start_time

        # Traitement des événements
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

            # Continuer après le délai minimum
            if elapsed_time >= min_display_time:
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    running = False

        # Dessin
        window.fill((20, 20, 40))  # Fond bleu foncé

        # Affichage des textes centrés
        window.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 3))
        window.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2))
        window.blit(credits_text, (WIDTH // 2 - credits_text.get_width() // 2, HEIGHT // 2 + 60))

        # Afficher le message "continuer" uniquement après le délai minimum
        if elapsed_time >= min_display_time:
            window.blit(continue_text, (WIDTH // 2 - continue_text.get_width() // 2, HEIGHT * 3 // 4))

        pygame.time.Clock().tick(60)
        pygame.display.flip()
    
    # Remettre la musique du menu quand on quitte l'écran de game over
    pygame.mixer.stop()  # Arrêter toute musique en cours
    menu_music = pygame.mixer.Sound("sons/menu.mp3")
    menu_music.set_volume(0.4)  # Volume à 40%
    menu_music.play(loops=-1)  # Boucle infinie

def create_enemy_from_data(enemy_data): #crée les enemis
    enemy_type = enemy_data.get('type', '')

    if enemy_type == 'BasicEnemy':
        enemy = BasicEnemy()
    elif enemy_type == 'TankEnemy':
        enemy = TankEnemy()
    elif enemy_type == 'ShooterEnemy':
        enemy = ShooterEnemy()
    elif enemy_type == 'LinkEnemy':
        enemy = LinkEnemy()
    elif enemy_type == 'Tank_Boss':
        enemy = Tank_Boss()
    elif enemy_type == 'Dash_Boss':
        enemy = Dash_Boss()
    elif enemy_type == 'Laser_Boss':
        enemy = Laser_Boss()
    elif enemy_type == 'Mothership_Boss':
        enemy = Mothership_Boss()
    else:
        print(f"Warning: Received unknown enemy type '{enemy_type}'")
        return None

    # Mettre à jour les propriétés de l'ennemi
    if enemy:
        enemy.x = enemy_data.get('x', enemy.x)
        enemy.y = enemy_data.get('y', enemy.y)
        enemy.health = enemy_data.get('health', enemy.health)
        enemy.angle = enemy_data.get('angle', getattr(enemy, 'angle', 0))

        # Gérer les propriétés spécifiques aux types d'ennemis (Shooter/Link)
        if isinstance(enemy, (ShooterEnemy, LinkEnemy)):
            enemy.target_x = enemy_data.get('target_x', enemy.target_x)
            enemy.target_y = enemy_data.get('target_y', enemy.target_y)
            enemy.is_moving = enemy_data.get('is_moving', enemy.is_moving)
            enemy.stationary_timer = enemy_data.get('stationary_timer', enemy.stationary_timer)

            # Traiter les lasers actifs pour LinkEnemy
            if isinstance(enemy, LinkEnemy) and 'active_lasers' in enemy_data:
                enemy.active_lasers = enemy_data.get('active_lasers', [])

        # pour tous les ennemis qui ont des projectiles
        if hasattr(enemy, 'projectiles'):
            enemy.projectiles = enemy_data.get('projectiles', [])

    return enemy

# Variable globale pour stocker les améliorations disponibles
shop_upgrade = all_upgrades

def draw_game_info(window, font, score, player, wave_number, wave_text_timer, player2=None):
    """Affiche les informations de jeu (score, santé, vague)"""
    # Score
    score_text = font.render(f"Score: {score}", True, WHITE)
    window.blit(score_text, (20, 20))

    # Numéro de vague
    wave_text = font.render(f"Wave: {wave_number}", True, WHITE)
    window.blit(wave_text, (WIDTH - wave_text.get_width() - 20, 20))

    # Affichage du texte de nouvelle vague
    if wave_text_timer > 0:
        wave_announcement = font.render(f"Wave {wave_number}", True, YELLOW)
        wave_rect = wave_announcement.get_rect(center=(WIDTH//2, HEIGHT//3))
        window.blit(wave_announcement, wave_rect)

    # Barre de vie du joueur 1
    health_width = 200
    health_height = 20
    health_x = 20
    health_y = HEIGHT - 30

    # Fond gris
    pygame.draw.rect(window, GRAY, (health_x, health_y, health_width, health_height))

    # Calcul du ratio de santé
    health_ratio = max(0, player.health / player.max_health)
    current_health_width = int(health_width * health_ratio)

    # Couleur basée sur la santé restante
    if health_ratio > 0.7:
        health_color = GREEN
    elif health_ratio > 0.3:
        health_color = YELLOW
    else:
        health_color = RED

    # Barre de vie
    pygame.draw.rect(window, health_color, (health_x, health_y, current_health_width, health_height))

    # Texte de santé
    health_text = font.render(f"{int(player.health)}/{int(player.max_health)}", True, WHITE)
    window.blit(health_text, (health_x + 10, health_y - 25))

    # Barre de vie du joueur 2 (si présent)
    if player2:
        p2_health_x = WIDTH - health_width - 20
        p2_health_y = HEIGHT - 30

        # Fond gris
        pygame.draw.rect(window, GRAY, (p2_health_x, p2_health_y, health_width, health_height))

        # Ratio de santé du joueur 2
        p2_health_ratio = max(0, player2.health / player2.max_health)
        p2_current_health_width = int(health_width * p2_health_ratio)

        # Couleur basée sur la santé restante
        if p2_health_ratio > 0.7:
            p2_health_color = GREEN
        elif p2_health_ratio > 0.3:
            p2_health_color = YELLOW
        else:
            p2_health_color = RED

        # Barre de vie
        pygame.draw.rect(window, p2_health_color, (p2_health_x, p2_health_y, p2_current_health_width, health_height))

        # Texte de santé
        p2_health_text = font.render(f"{int(player2.health)}/{int(player2.max_health)}", True, WHITE)
        window.blit(p2_health_text, (p2_health_x + 10, p2_health_y - 25))

        # Indicateurs "Joueur 1" et "Joueur 2"
        p1_label = font.render("Joueur 1", True, WHITE)
        p2_label = font.render("Joueur 2", True, WHITE)
        window.blit(p1_label, (health_x, health_y - 50))
        window.blit(p2_label, (p2_health_x, p2_health_y - 50))


class Shop:
    def __init__(self):
        self.current_screen = "menu"
        self.current_tab = "skins"
        self.credits, self.selected_skin, unlocked_skins = load_data()  # Charger les crédits, le skin sélectionné et les skins débloqués
        self.entering_ip = False
        self.connexion_reussie = False
        self.p2p = None
        self.remote_skin_info = None # stock les infos du skin du joueur 2
        self.server_ip = ""  # ip du serveur pour l'affichage
        self.font = pygame.font.Font(None, 36)

        # Initialiser les variables pour la gestion des vidéos
        self.current_video = None
        self.video_path = "images/video-menu.mp4"  # Chemin par défaut
        self.cap = None  # Sera initialisé lors du premier affichage

        # musique 
        pygame.mixer.stop()  # arrete la musique en cours
        self.menu_music = pygame.mixer.Sound("sons/menu.mp3")
        self.menu_music.set_volume(0.4)  # volume à 40%
        self.menu_music.play(loops=-1)  # -1 = boucle infinie

        self.grid_size = (3, 2)
        self.margin = 50
        self.padding = 20

        usable_width = WIDTH - (2 * self.margin)
        usable_height = HEIGHT - (2 * self.margin) - 100
        self.card_width = (usable_width - (self.grid_size[0] + 1) * self.padding) // self.grid_size[0]
        self.card_height = (usable_height - (self.grid_size[1] + 1) * self.padding) // self.grid_size[1]

        #vaisseaux du chop
        self.skins = [
            {"name": "Basic Ship", "price": "gratuit", "unlocked": True, "couleur_vaisseau": (11,11,70),"description":"clasic ship"},
            {"name": "Cristal Ship", "price": 100, "unlocked": False, "couleur_vaisseau": (20, 25, 35),"description":"tanky ship"},
            {"name": "Amethyst Ship", "price": 300, "unlocked": False, "couleur_vaisseau": (75,0,75),"description":"fast ship"},
            {"name": "Plasma Ship", "price": 250, "unlocked": False, "couleur_vaisseau": (125, 25, 125),"description":"railgun ship"},
            {"name": "Emerald Ship", "price": "325","unlocked":False,"couleur_vaisseau": (0,45,0),"description":"bullet bounces"},
            {"name": "Diamond Ship", "price": 400, "unlocked": False, "couleur_vaisseau": (0,45,45),"description":"explosions"}]
        

        # Appliquer les skins débloqués chargés depuis le json
        for skin in self.skins:
            for unlocked_skin in unlocked_skins:
                if skin["name"] == unlocked_skin["name"]:
                    skin["unlocked"] = unlocked_skin["unlocked"]

        #boutons
        self.buttons = {
            "play": Button(WIDTH // 2 - 83, HEIGHT*0.795 - 25, 162*WIDTH//1536, 49*HEIGHT//864, ""), 
            "shop": Button(WIDTH // 2 - 72, HEIGHT*0.857 - 25, 141*WIDTH//1536, 40*HEIGHT//864, ""),  
            "quit": Button(WIDTH // 2 - 83, HEIGHT*0.91 - 25, 162*WIDTH//1536, 49*HEIGHT//864, ""),
            "back": Button(self.margin, self.margin, 100, 40, "BACK"),
            "singleplayer": Button(WIDTH*0.425 - 83, HEIGHT*0.8825 - 25, 160*WIDTH//1536, 40*HEIGHT//864, ""),
            "multiplayer": Button(WIDTH*0.575 - 83, HEIGHT*0.8825 - 25, 160*WIDTH//1536, 40*HEIGHT//864, ""),
            "create_room": Button(WIDTH*0.4375 - 83, HEIGHT*0.955 - 25, 162*WIDTH//1536, 35*HEIGHT//864, ""),
            "join_room": Button(WIDTH*0.5625 - 83, HEIGHT*0.955 - 25, 162*WIDTH//1536, 35, ""),
            "enter": Button(WIDTH // 2 + 120, HEIGHT // 2 - 25, 100, 50, "Enter"),
            "jouer": Button(WIDTH // 2 - 100, HEIGHT // 2 + 100, 200, 50, "Play"),
        }

        # Champ de saisie pour l'adresse IP
        self.input_box = InputBox(WIDTH // 2 - 250, HEIGHT // 2 - 25, 200, 50)

        # Appliquer les skins débloqués chargés depuis save_data.json
        for skin in self.skins:
            for unlocked_skin in unlocked_skins:
                if skin["name"] == unlocked_skin["name"]:
                    skin["unlocked"] = unlocked_skin["unlocked"]


        self.connexion_reussie = False  # Indicateur de connexion réussie
        # Champ de saisie pour l'adresse IP
        self.input_box = InputBox(WIDTH // 2 - 250, HEIGHT // 2 - 25, 200, 50)
        self.entering_ip = False

    def draw_skin_preview(self, surface, skin, x, y):
        card_contour = pygame.Rect(x, y, self.card_width, self.card_height)
        # Utiliser couleur_vaisseau si disponible, sinon utiliser une couleur par défaut
        skin_color = skin.get("couleur_vaisseau", BLUE)  # BLUE comme couleur par défaut
        pygame.draw.rect(surface, skin_color, card_contour,15)

        card_rect = pygame.Rect(x, y, self.card_width, self.card_height)
        pygame.draw.rect(surface, GRAY, card_rect, border_radius=15)

        # vaisseaux dans le shop
        preview_area_size = min(self.card_width * 0.8, self.card_height * 0.4) # Adjust size as needed
        preview_rect_bg = pygame.Rect(x + (self.card_width - preview_area_size) // 2, y + 20, preview_area_size, preview_area_size)
        pygame.draw.rect(surface, skin_color, preview_rect_bg, border_radius=5) # Background for preview

        # creer_vaisseau pour avoir l'image
        temp_ship = creer_vaisseau(skin,damage_manager=DamageNumberManager()) 
        ship_image = temp_ship.original_image # image originale
            
        img_rect = ship_image.get_rect()
        scale = min(preview_area_size / img_rect.width, preview_area_size / img_rect.height) 
        scaled_width = int(img_rect.width * scale * 0.8)
        scaled_height = int(img_rect.height * scale * 0.8)
        scaled_image = pygame.transform.scale(ship_image, (scaled_width, scaled_height))
                
        # image centrée
        blit_rect = scaled_image.get_rect(center=preview_rect_bg.center)
        surface.blit(scaled_image, blit_rect)

        # texte de bouttons
        name_text = self.font.render(skin["name"], True, WHITE)
        name_rect = name_text.get_rect(center=(card_rect.centerx, preview_rect_bg.bottom + 30))
        surface.blit(name_text, name_rect)

        description_text = self.font.render(skin["description"], True, (200,200,200))
        description_rect = description_text.get_rect(center=(card_rect.centerx, preview_rect_bg.bottom + 60))
        surface.blit(description_text, description_rect)

        if skin["unlocked"]:
            button_text = "ÉQUIPED" if self.selected_skin == skin else "SELECT"
            button_color = GREEN if self.selected_skin == skin else BLUE
        else:
            button_text = f"{skin['price']} Credits"
            button_color = RED if self.credits < int(skin["price"]) else YELLOW

        button_rect = pygame.Rect(x + 10, y + self.card_height - 40, self.card_width - 20, 30)
        pygame.draw.rect(surface, button_color, button_rect, border_radius=5)
        text_surface = self.font.render(button_text, True, WHITE)
        text_rect = text_surface.get_rect(center=button_rect.center)
        surface.blit(text_surface, text_rect)

    def handle_skin_selection(self, skin):
        if not skin["unlocked"]:
            if isinstance(skin["price"], int) and self.credits >= skin["price"]:
                self.credits -= skin["price"]
                skin["unlocked"] = True
            else:
                return  # Ne rien faire si le joueur ne peut pas débloquer le skin

        self.selected_skin = skin
        save_data(self.credits, self.selected_skin, self.skins)  # Sauvegarder les crédits, le skin sélectionné et les skins débloqués

        global selected_ship
        selected_ship = skin

    def draw_shop_screen(self, surface):
        surface.fill(BLACK)
        self.buttons["back"].draw(surface)

        credits_text = self.font.render(f"Credits: {self.credits}", True, WHITE)
        surface.blit(credits_text, (WIDTH - 200, self.margin))

        for i, skin in enumerate(self.skins):
            row = i // self.grid_size[0]
            col = i % self.grid_size[0]
            x = self.margin + col * (self.card_width + self.padding)
            y = self.margin + 100 + row * (self.card_height + self.padding)
            self.draw_skin_preview(surface, skin, x, y)

    def run(self, screen):
        running = True
        network_status = ""
        network_color = WHITE

        while running:
            # reset le network_status
            network_status = ""
            network_color = WHITE

            if self.p2p:
                if self.p2p.running and self.p2p.connexion:
                    network_status = "Connected"
                    network_color = GREEN
                    if hasattr(self.p2p, 'remote_skin_info') and self.p2p.remote_skin_info:
                        network_status += f" (Joueur 2: {self.p2p.remote_skin_info.get('name', 'Inconnu')})"
                else:
                    # Supprimer le message d'erreur
                    network_status = ""
                    network_color = WHITE
            elif self.current_screen == "multiplayer_menu" and hasattr(self, 'entering_ip') and self.entering_ip:
                network_status = "Entering the IP..."
            elif self.current_screen == "multiplayer_menu":
                # Supprimer le message d'attente
                network_status = ""

            # envents :
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                # Gestion du menu principal
                if self.current_screen == "menu":
                    if self.buttons["shop"].handle_event(event):
                        self.current_screen = "shop"
                    elif self.buttons["play"].handle_event(event):
                        self.current_screen = "play_menu"
                    elif self.buttons["quit"].handle_event(event):
                        pygame.quit()
                        return  # sort de la fonction

                # Gestion du menu de choix de mode
                elif self.current_screen == "play_menu":
                    if self.buttons["singleplayer"].handle_event(event):
                        game_loop(self.selected_skin, self)  # Mode solo
                    elif self.buttons["multiplayer"].handle_event(event):
                        self.current_screen = "multiplayer_menu"
                        #Initialise l'attribut multijoueur
                        if not hasattr(self, 'entering_ip'):
                            self.entering_ip = False
                        if not hasattr(self, 'connexion_reussie'):
                            self.connexion_reussie = False
                        if not hasattr(self, 'remote_skin_info'):
                            self.remote_skin_info = None
                    elif self.buttons["back"].handle_event(event):
                        self.current_screen = "menu"

                # Gestion du menu multijoueur
                elif self.current_screen == "multiplayer_menu":
                    if "create_room" in self.buttons and self.buttons["create_room"].handle_event(event):
                        def get_local_ip():
                            try:
                                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                                s.connect(("8.8.8.8", 80))
                                ip = s.getsockname()[0]
                                s.close()
                                return ip
                            except Exception:
                                return "127.0.0.1"
                        self.server_ip = get_local_ip()
                        self.current_screen = "create_room_screen"
                        
                        if not self.p2p:  #pour ne pas en creer plusieurs
                            def start_server():
                                print("  Démarrage de la fonction start_server")
                                try:
                                    self.p2p = P2PCommunication(est_serveur=True, local_skin_info=self.selected_skin)
                                    if self.p2p.initialiser():
                                        if hasattr(self.p2p, 'remote_skin_info') and self.p2p.remote_skin_info:
                                            self.remote_skin_info = self.p2p.remote_skin_info  # infos du remote_skin
                                            self.connexion_reussie = True  # True quand les infos de l'autre joueur sont recues
                                        else:
                                            self.connexion_reussie = False
                                    else:
                                        self.p2p = None  # reset p2p si erreur
                                        self.connexion_reussie = False
                                except Exception as e:
                                    if hasattr(self, 'p2p') and self.p2p:
                                        self.p2p = None
                                    self.connexion_reussie = False

                            threading.Thread(target=start_server, daemon=True).start()

                    elif "join_room" in self.buttons and self.buttons["join_room"].handle_event(event):
                        if not self.p2p:  # qui si pas déjâ connecté
                            self.entering_ip = True
                            # si input_box existe bien
                            if not hasattr(self, 'input_box'):
                                self.input_box = InputBox(WIDTH // 2 - 100, HEIGHT // 2, 200, 32)
                            self.current_screen = "join_room_screen"

                    elif "enter" in self.buttons and self.buttons["enter"].handle_event(event) and self.entering_ip:
                        if not self.p2p and hasattr(self, 'input_box'):  # pour ne pas en vaoir plusieurs
                            # lance le client
                            def start_client():
                                self.p2p = P2PCommunication(est_serveur=False, ip_hote=self.input_box.text.strip(), local_skin_info=self.selected_skin)
                                if self.p2p.initialiser():
                                    if hasattr(self.p2p, 'remote_skin_info') and self.p2p.remote_skin_info:
                                        self.remote_skin_info = self.p2p.remote_skin_info  # stock le remote skin
                                        self.connexion_reussie = True  # true quand les infos sont recues
                                    else:
                                        self.connexion_reussie = False
                                else:
                                    print("Échec de la connexion client ou de l'échange de skin.")
                                    self.p2p = None
                                    self.connexion_reussie = False
                                # Reset entering_ip
                                self.entering_ip = False

                            threading.Thread(target=start_client, daemon=True).start()


                    elif "back" in self.buttons and self.buttons["back"].handle_event(event):
                        if self.p2p:  # ferme la connection si back est appuyé
                            self.p2p.fermer()
                            self.p2p = None
                        self.current_screen = "play_menu"
                        self.entering_ip = False
                        self.connexion_reussie = False
                        self.remote_skin_info = None
                        
                # Gestion de l'écran de création de room
                elif self.current_screen == "create_room_screen":
                    if "back" in self.buttons and self.buttons["back"].handle_event(event):
                        if self.p2p:  # ferme la connection si back est appuyé
                            self.p2p.fermer()
                            self.p2p = None
                        self.current_screen = "multiplayer_menu"
                        self.entering_ip = False
                        self.connexion_reussie = False
                        self.remote_skin_info = None
                    # Gestion du bouton jouer dans l'écran create_room_screen
                    elif "jouer" in self.buttons and self.buttons["jouer"].handle_event(event) and hasattr(self, 'connexion_reussie') and self.connexion_reussie and self.p2p:
                        # lance le jeu
                        current_p2p = self.p2p  # Stock p2p
                        self.p2p = None  # Reset le p2p du shop
                        self.connexion_reussie = False  # Reset le flag
                        game_loop(self.selected_skin, self, current_p2p, self.remote_skin_info)
                        # ferme p2p
                        if current_p2p and current_p2p.running:
                            current_p2p.fermer()
                        self.remote_skin_info = None  # Clear les infos du remote skin
                        self.current_screen = "menu"  # retourne au main menu
                        
                # Gestion de l'écran de rejoindre une room
                elif self.current_screen == "join_room_screen":
                    if "back" in self.buttons and self.buttons["back"].handle_event(event):
                        if self.p2p:  # ferme la connection si back est appuyé
                            self.p2p.fermer()
                            self.p2p = None
                        self.current_screen = "multiplayer_menu"
                        self.entering_ip = False
                        self.connexion_reussie = False
                        self.remote_skin_info = None
                    # Gestion du bouton enter pour se connecter au serveur
                    elif "enter" in self.buttons and self.buttons["enter"].handle_event(event) and hasattr(self, 'input_box'):
                        if not self.p2p:  # empeche les connexions multiples
                            # lance le client
                            def start_client():
                                self.p2p = P2PCommunication(est_serveur=False, ip_hote=self.input_box.text.strip(), local_skin_info=self.selected_skin)
                                if self.p2p.initialiser():
                                    if hasattr(self.p2p, 'remote_skin_info') and self.p2p.remote_skin_info:
                                        self.remote_skin_info = self.p2p.remote_skin_info  # stock les infos du skin remote
                                        self.connexion_reussie = True  # true si les infos sont recues
                                    else:
                                        self.connexion_reussie = True  # On considère quand même la connexion comme réussie
                                else:
                                    self.p2p = None
                                    self.connexion_reussie = False

                            threading.Thread(target=start_client, daemon=True).start()
                    # Gestion du bouton jouer dans l'écran join_room_screen
                    elif "jouer" in self.buttons and self.buttons["jouer"].handle_event(event) and hasattr(self, 'connexion_reussie') and self.connexion_reussie and self.p2p:
                        # lance le jeu avec les infos du remote
                        current_p2p = self.p2p  # stock l'instance de p2p
                        self.p2p = None  # Reset p2p du shop
                        self.connexion_reussie = False  # Reset le flag
                        game_loop(self.selected_skin, self, current_p2p, self.remote_skin_info)
                        if current_p2p and current_p2p.running:
                            current_p2p.fermer()
                        self.remote_skin_info = None  # Clear les infos de remote skin
                        self.current_screen = "menu"  # Retourn au main menu quand fini

                # Gestion du shop
                elif self.current_screen == "shop":
                    if self.buttons["back"].handle_event(event):
                        self.current_screen = "menu"

                    if event.type == pygame.MOUSEBUTTONDOWN:
                        mouse_pos = event.pos
                        for i, skin in enumerate(self.skins):
                            row = i // self.grid_size[0]
                            col = i % self.grid_size[0]
                            x = self.margin + col * (self.card_width + self.padding)
                            y = self.margin + 100 + row * (self.card_height + self.padding)
                            card_rect = pygame.Rect(x, y, self.card_width, self.card_height)
                            if card_rect.collidepoint(mouse_pos):
                                self.handle_skin_selection(skin)

                # Gestion du champ de saisie pour l'adresse IP
                if hasattr(self, 'entering_ip') and self.entering_ip and hasattr(self, 'input_box'):
                    self.input_box.handle_event(event)

            # ecran noir
            screen.fill(BLACK)

            if self.current_screen == "menu":
                # Vérifier si la vidéo est déjà ouverte et si c'est la bonne
                if not hasattr(self, 'current_video') or self.current_video != "menu":
                    # Fermer la vidéo précédente si elle existe
                    if hasattr(self, 'cap') and self.cap is not None:
                        self.cap.release()
                    # Charger la nouvelle vidéo
                    self.video_path = "images/video-menu.mp4"
                    self.cap = cv2.VideoCapture(self.video_path)
                    self.current_video = "menu"
                    
                    # Vérifier si la vidéo est chargée correctement
                    if not self.cap.isOpened():
                        print("Erreur lors de l'ouverture de la vidéo menu.")
                        exit()
                
                # Lire les images de la vidéo et les afficher
                ret, frame = self.cap.read()
                if not ret:
                    # Si la vidéo est terminée, revenir au début
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = self.cap.read()  # Lire la première image après réinitialisation
                    if not ret:  # Si toujours pas de frame, il y a un problème avec la vidéo
                        print("Impossible de lire la vidéo menu.")
                        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)  # Créer une image noire
                
                # Convertir l'image OpenCV (BGR) en format Pygame (RGB)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = np.transpose(frame, (1, 0, 2))  # Ajuster la forme (hauteur, largeur, canaux)
                
                # Redimensionner l'image pour qu'elle s'adapte à l'écran
                frame = cv2.resize(frame, (HEIGHT, WIDTH))
                
                # Convertir l'image en surface Pygame
                frame_surface = pygame.surfarray.make_surface(frame)
                
                # Afficher l'image sur la fenêtre Pygame
                screen.blit(frame_surface, (0, 0))
                
                stylish_font = pygame.font.Font("Stardust_Odyssey_police.ttf", 100)
                title = stylish_font.render("STARDUST ODYSSEY", True, (255, 255, 255))
                screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 80))
                self.buttons["play"].draw(screen)
                self.buttons["shop"].draw(screen)
                self.buttons["quit"].draw(screen)

            elif self.current_screen == "play_menu":
                # Vérifier si la vidéo est déjà ouverte et si c'est la bonne
                if not hasattr(self, 'current_video') or self.current_video != "play_menu":
                    # Fermer la vidéo précédente si elle existe
                    if hasattr(self, 'cap') and self.cap is not None:
                        self.cap.release()
                    # Charger la nouvelle vidéo
                    self.video_path = "images/video-menu2.mp4"
                    self.cap = cv2.VideoCapture(self.video_path)
                    self.current_video = "play_menu"
                    
                    # Vérifier si la vidéo est chargée correctement
                    if not self.cap.isOpened():
                        print("Erreur lors de l'ouverture de la vidéo play_menu.")
                        exit()
                
                # Lire les images de la vidéo et les afficher
                ret, frame = self.cap.read()
                if not ret:
                    # Si la vidéo est terminée, revenir au début
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = self.cap.read()  # Lire la première image après réinitialisation
                    if not ret:  # Si toujours pas de frame, il y a un problème avec la vidéo
                        print("Impossible de lire la vidéo play_menu.")
                        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)  # Créer une image noire
                
                # Convertir l'image OpenCV (BGR) en format Pygame (RGB)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = np.transpose(frame, (1, 0, 2))  # Ajuster la forme (hauteur, largeur, canaux)
                
                # Redimensionner l'image pour qu'elle s'adapte à l'écran
                frame = cv2.resize(frame, (HEIGHT, WIDTH))
                
                # Convertir l'image en surface Pygame
                frame_surface = pygame.surfarray.make_surface(frame)
                
                # Afficher l'image sur la fenêtre Pygame
                screen.blit(frame_surface, (0, 0))

                self.buttons["singleplayer"].draw(screen)
                self.buttons["multiplayer"].draw(screen)
                self.buttons["back"].draw(screen)

            elif self.current_screen == "multiplayer_menu":
                # Vérifier si la vidéo est déjà ouverte et si c'est la bonne
                if not hasattr(self, 'current_video') or self.current_video != "multiplayer_menu":
                    # Fermer la vidéo précédente si elle existe
                    if hasattr(self, 'cap') and self.cap is not None:
                        self.cap.release()
                    # Charger la nouvelle vidéo
                    self.video_path = "images/video-menu3.mp4"
                    self.cap = cv2.VideoCapture(self.video_path)
                    self.current_video = "multiplayer_menu"
                    
                    # Vérifier si la vidéo est chargée correctement
                    if not self.cap.isOpened():
                        exit()
                
                # Lire les images de la vidéo et les afficher
                ret, frame = self.cap.read()
                if not ret:
                    # Si la vidéo est terminée, revenir au début
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = self.cap.read()  # Lire la première image après réinitialisation
                    if not ret:  # Si toujours pas de frame, il y a un problème avec la vidéo
                        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)  # Créer une image noire
                
                # Convertir l'image OpenCV (BGR) en format Pygame (RGB)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = np.transpose(frame, (1, 0, 2))  # Ajuster la forme (hauteur, largeur, canaux)
                
                # Redimensionner l'image pour qu'elle s'adapte à l'écran
                frame = cv2.resize(frame, (HEIGHT, WIDTH))
                
                # Convertir l'image en surface Pygame
                frame_surface = pygame.surfarray.make_surface(frame)
                
                # Afficher l'image sur la fenêtre Pygame
                screen.blit(frame_surface, (0, 0))

                # Draw buttons
                if "create_room" in self.buttons: self.buttons["create_room"].draw(screen)
                if "join_room" in self.buttons: self.buttons["join_room"].draw(screen)
                if "back" in self.buttons: self.buttons["back"].draw(screen)
                
            elif self.current_screen == "create_room_screen":
                #ecran creer room
                title = self.font.render("CREATE ROOM", True, WHITE)
                screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 4))
                
                # Display l'adresse ip
                ip_text = self.font.render(f"IP: {self.server_ip}", True, WHITE)
                screen.blit(ip_text, (WIDTH // 2 - ip_text.get_width() // 2, HEIGHT // 2 - 50))
                
                # bouton back
                if "back" in self.buttons: self.buttons["back"].draw(screen)
                
                # Si la connexion est établie et que nous sommes sur l'écran create_room
                if hasattr(self, 'connexion_reussie') and self.connexion_reussie and "jouer" in self.buttons:
                    # Afficher un message de confirmation
                    connected_text = self.font.render("Player connected!", True, GREEN)
                    screen.blit(connected_text, (WIDTH // 2 - connected_text.get_width() // 2, HEIGHT // 2))
                    # Afficher le bouton jouer
                    self.buttons["jouer"].draw(screen)
                else:
                    #message 'en attente'
                    waiting_text = self.font.render("Waiting for player...", True, WHITE)
                    screen.blit(waiting_text, (WIDTH // 2 - waiting_text.get_width() // 2, HEIGHT // 2))
                
            elif self.current_screen == "join_room_screen":
                # ecran join room
                title = self.font.render("JOIN ROOM", True, WHITE)
                screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 4))
                
                # imput_box pour l'ip
                if hasattr(self, 'input_box'):
                    ip_prompt = self.font.render("Enter the server's IP:", True, WHITE)
                    screen.blit(ip_prompt, (WIDTH // 2 - ip_prompt.get_width() // 2, HEIGHT // 2 - 50))
                    self.input_box.draw(screen)
                    if "enter" in self.buttons: self.buttons["enter"].draw(screen)
                
                # bouton back
                if "back" in self.buttons: self.buttons["back"].draw(screen)
                
                # status de la connexion
                status_text_surf = self.font.render(network_status, True, network_color)
                screen.blit(status_text_surf, (WIDTH // 2 - status_text_surf.get_width() // 2, HEIGHT // 2 + 150))

                # Si la connexion est établie et que nous sommes sur l'écran join_room
                if hasattr(self, 'connexion_reussie') and self.connexion_reussie and "jouer" in self.buttons:
                    # Afficher un message de confirmation de connexion
                    connected_text = self.font.render("Connected to the server", True, GREEN)
                    screen.blit(connected_text, (WIDTH // 2 - connected_text.get_width() // 2, HEIGHT // 2 + 50))
                    # Afficher le bouton jouer avec un décalage vertical pour éviter la superposition
                    jouer_button = self.buttons["jouer"]
                    jouer_button.rect.y = HEIGHT // 2 + 100  # Repositionner le bouton plus bas
                    jouer_button.draw(screen)

            elif self.current_screen == "shop":
                self.draw_shop_screen(screen)

            pygame.display.flip()

        # si main loop existe, s'assure que p2p est fermé
        if hasattr(self, 'p2p') and self.p2p:
            self.p2p.fermer()
