import pygame
import random
import math

pygame.init()

# Paramètres de la fenêtre en plein écran
window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = window.get_size()
pygame.display.set_caption("Nova Drift Prototype - Fullscreen Mode")

# Crée une classe pour les vaisseaux
class Ship: 
    def __init__(self, image_path="images/vaisseau_joueur.png", ship_size=(90, 90), damage_manager=None,ship_speed=5,ship_health=100,ship_damage=10,ship_reload_speed=1.0,ship_bullet_size=5,ship_bullet_speed=5,ship_range=300,ship_wall_bounces=0,ship_explosion_radius=0,ship_bullet_piercing=0):
        self.image = None
        self.original_image = None


        loaded_image = pygame.image.load(image_path).convert_alpha()
        self.image = pygame.transform.scale(loaded_image, ship_size)
        self.original_image = self.image

        self.rect = self.image.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.angle = 0
        self.bullets = []
        self.velocite_haut=0
        self.velocite_bas=0
        self.velocite_droite=0
        self.velocite_gauche=0

        # Stats base :
        self.speed = ship_speed
        self.health = ship_health
        self.max_health = ship_health
        self.range = ship_range
        self.bullet_speed = ship_bullet_speed
        self.reload_speed = ship_reload_speed
        self.bullet_size = ship_bullet_size 
        self.damage = ship_damage       

        self.explosion_radius = ship_explosion_radius
        self.wall_bounces = ship_wall_bounces
        self.bullet_piercing = ship_bullet_piercing
        self.body_damage = 5

        self.regen_rate = 0
        self.enemy_bounces = 0
        self.parallel_shots = 1
        self.shield = 0
        self.last_shot_time = 0
        self.invincible_time = 0
        
        # Initialise le damage manager
        self.damage_manager = damage_manager
        self.forcefield_damage = 0
        self.last_forcefield_time = pygame.time.get_ticks()
        
        # Indiquer si c'est le vaisseau local ou distant (pour le multijoueur)
        self.is_local = True  # Par défaut, c'est le vaisseau local

        
        # Disponibilitée de la vitesse de la lumière
        self.light_speed_available = False
        self.light_speed_active = False
        self.light_speed_timer = -1
        self.light_speed_cooldown = 0
        self.original_speed = self.speed

        
        # Disponibilité d'invulnérabilité
        self.invulnerability_available = False
        self.invulnerability_active = False
        self.invulnerability_timer = -1
        self.invulnerability_cooldown = 0

        
        # capacité de tirs chjargés
        self.charged_shots_available = False
        self.charged_shots_remaining = 0
        self.charged_shots_cooldown = 0
        self.crit_chance = 5  # 5% base crit chance
        self.crit_multiplier = 1.5

        self.upgrades = []
        self.stun_timer=0
    
    # Définit le déplacement avec les bouttons associés
    def move(self):
        if self.stun_timer > 0:
            return
    # fait la différence entre les vaisseaux locaux ou non dans le cas d'un  multijoueur
        if not self.is_local:
            return
    # Définition des touches associées aux mouvements
        keys = pygame.key.get_pressed()

        if keys[pygame.K_z] and self.velocite_haut < 1 :  # Avancer
            self.velocite_haut += 0.02
        if keys[pygame.K_s] and self.velocite_bas < 1 :  # Reculer
            self.velocite_bas += 0.02
        if keys[pygame.K_q] and self.velocite_gauche < 1 :  # Gauche
            self.velocite_gauche += 0.02
        if keys[pygame.K_d] and self.velocite_droite < 1 :  # Droite
            self.velocite_droite += 0.02

        # Définition de la vitesse du vaisseau
        if self.velocite_haut > 0 :
            self.rect.y -= self.velocite_haut* self.speed
        if self.velocite_bas > 0 :
            self.rect.y += self.velocite_bas* self.speed
        if self.velocite_gauche > 0 :
            self.rect.x -= self.velocite_gauche* self.speed
        if self.velocite_droite > 0 :
            self.rect.x += self.velocite_droite* self.speed

        #permet de simuler l'inertie du vaisseau en companssant les accélérations
        if self.velocite_haut > 0 and not keys[pygame.K_z]:
            self.velocite_haut -= 0.01
        if self.velocite_bas > 0 and not keys[pygame.K_s]:
            self.velocite_bas -= 0.01
        if self.velocite_gauche > 0 and not keys[pygame.K_q]:
            self.velocite_gauche -= 0.01
        if self.velocite_droite > 0 and not keys[pygame.K_d]:
            self.velocite_droite -= 0.01

        #Téléportation de bord à bord de l'écran
        #enlève de la vie si, utilisation excessive de ce mode de voyage
        if self.rect.x <= 0 :
            self.rect.x = WIDTH-5
            self.health-=5
            self.invincible_time=60
        if self.rect.x >= WIDTH :
            self.rect.x = 5
            self.health-=5
            self.invincible_time=60
        if self.rect.y <= 0 :
            self.rect.y = HEIGHT-5
            self.health-=5
            self.invincible_time=60
        if self.rect.y >= HEIGHT :
            self.rect.y = 5
            self.health-=5
            self.invincible_time=60

    def rotate_to_mouse(self):
        # Récupérer les coordonnées actuelles de la souris
        mouse_x, mouse_y = pygame.mouse.get_pos()
        # Calculer la différence en x et en y entre la position de l'objet et la souris
        dx, dy = mouse_x - self.rect.centerx, mouse_y - self.rect.centery
        # Calculer l'angle de rotation nécessaire pour que l'objet pointe vers la souris
        # atan2 retourne l'angle en radians entre l'axe x et le vecteur (dx, dy)
        # On inverse dy pour que l'angle corresponde à une orientation standard dans Pygame
        self.angle = math.degrees(math.atan2(-dy, dx))
        # Appliquer la rotation à l'image de l'objet. L'angle est augmenté de 90° pour corriger
        # la différence d'orientation entre (dx, dy) et l'orientation de l'image
        self.image = pygame.transform.rotate(self.original_image, self.angle+90)
        # Mettre à jour la position du rectangle de l'image pour que le centre reste au même endroit
        self.rect = self.image.get_rect(center=self.rect.center)

    def shoot(self):
        # Récupérer le temps actuel en millisecondes
        current_time = pygame.time.get_ticks()
        # Vérifier si le cooldown entre les tirs est respecté
        # Si le temps écoulé depuis le dernier tir est inférieur au délai entre deux tirs
        # alors on ne tire pas
        if current_time - self.last_shot_time < 1000 / self.reload_speed:  # 1000ms base cooldown
            return
        # Jouer le son de tir
        son_tir=pygame.mixer.Sound("sons/tir_joueur.mp3")
        son_tir.play()
        # Calculer l'angle du tir en radians
        angle_rad = math.radians(self.angle)
        # Si l'objet tire un seul projectile
        if self.parallel_shots == 1:
            # Calculer la position du tir en fonction de l'angle et de la distance de l'objet
            bullet_x = self.rect.centerx + 20 * math.cos(angle_rad)
            bullet_y = self.rect.centery - 20 * math.sin(angle_rad)
            # Créer une nouvelle balle et l'ajouter à la liste des balles
            bullet = Bullet(bullet_x, bullet_y, angle_rad, self)
            
            # Déterminer si ce tir est un coup critique
            is_crit = False
            if self.charged_shots_remaining > 0:
                # Si l'objet a encore des tirs chargés, appliquer un coup critique
                is_crit = True
                self.charged_shots_remaining -= 1 # Réduire les tirs chargés restants
            else:
                # déterminer aléatoirement si c'est un coup critique
                is_crit = True if random.randint(0, 100) < self.crit_chance else False # 5% de base
            # Si le tir est critique, augmenter les dégâts et marquer le tir comme critique
            if is_crit:
                bullet.damage *= self.crit_multiplier  # 50% de base # Multiplier les dégâts pour un coup critique
                bullet.is_critical = True  # Marquer ce tir comme critique, pour afficher un indicateur visuel
            # Ajouter la balle à la liste des balles
            self.bullets.append(bullet)
        else:
            # Si plusieurs projectiles sont tirés en même temps
            spread = 15  # Écart en degrés entre chaque projectile tiré simultanément
             # Créer plusieurs projectiles avec un écart angulaire
            for i in range(self.parallel_shots):
                # Calculer l'offset angulaire pour chaque balle
                offset = spread * (i - (self.parallel_shots - 1) / 2)
                bullet_angle = angle_rad + math.radians(offset)
                # Calculer la position du tir pour chaque balle
                bullet_x = self.rect.centerx + 20 * math.cos(bullet_angle)
                bullet_y = self.rect.centery - 20 * math.sin(bullet_angle)
                # Créer une nouvelle balle et l'ajouter à la liste des balle
                bullet = Bullet(bullet_x, bullet_y, bullet_angle, self)
                
                # Vérifier si le tir est critique pour chaque balle
                is_crit = False
                if self.charged_shots_remaining > 0:
                    is_crit = True
                    self.charged_shots_remaining -= 1
                else:
                    is_crit = True if random.randint(0, 100) < self.crit_chance else False # 5% de base
                
                if is_crit:
                    # Appliquer le coup critique si nécessaire
                    bullet.damage *= self.crit_multiplier  # critiques
                    bullet.is_critical = True  # Marquer ce tir comme critique
                    # Ajouter chaque balle à la liste des balles
                self.bullets.append(bullet)
    # Mettre à jour le temps du dernier tir
        self.last_shot_time = current_time

    def update(self, enemies):
        # Récupérer le temps actuel en millisecondes
        current_time = pygame.time.get_ticks()
        
        # Mise à jour des balles
        for bullet in self.bullets[:]:
            bullet.move() # Déplacer chaque balle dans la liste de balles
        # Régénération de la santé si elle est inférieure à la santé maximale
        if self.health < self.max_health:
            # Augmenter la santé du joueur en fonction de son taux de régénération
            self.health = min(self.max_health, self.health + self.regen_rate / 60)
            
    # Gestion de l'invincibilité : diminuer le temps d'invincibilité restant
        if self.invincible_time > 0:
            self.invincible_time -= 1

         # Application des dégâts du champ de force (forcefield)
        if self.forcefield_damage > 0:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_forcefield_time >= 1000:  # Appliquer les dégâts toutes les secondes
                self.last_forcefield_time = current_time # Mettre à jour le temps du dernier calcul
                for enemy in enemies[:]:
                    # Calculer la distance entre le joueur et l'ennemi
                    distance = math.hypot(self.rect.centerx - enemy.x, self.rect.centery - enemy.y)
                    # Si l'ennemi est à portée du champ de force (200 pixels), lui infliger des dégâts
                    if distance <= 200:
                        enemy.health -= self.forcefield_damage
        # Gestion du temps de stun
        if self.stun_timer>0:
            self.stun_timer-=1 # Décrémenter le timer de stun
# Mise à jour des cooldowns (délai entre l'utilisation des compétences)
        # Réduire les temps de recharge à chaque frame (16ms)
        if self.light_speed_cooldown > 0:
            self.light_speed_cooldown = max(0, self.light_speed_cooldown - 16)  # 16ms par frame
        if self.invulnerability_cooldown > 0:
            self.invulnerability_cooldown = max(0, self.invulnerability_cooldown - 16)
        if self.charged_shots_cooldown > 0:
            self.charged_shots_cooldown = max(0, self.charged_shots_cooldown - 16)

        # Vérifier si la durée de la vitesse de lumière est terminée
        if self.light_speed_active and current_time >= self.light_speed_timer:
            self.light_speed_active = False # Désactive la vitesse de lumière
            self.speed = self.original_speed # Rétablit la vitesse initiale


        # Vérifier si la durée d'invulnérabilité est terminée
        if self.invulnerability_active and current_time >= self.invulnerability_timer:
            self.invulnerability_active = False # Désactive l'invulnérabilité
            self.invincible_time = 0 # Réinitialise le temps d'invincibilité

      # Gérer les entrées des capacités
        keys = pygame.key.get_pressed()
        # Si la touche '1' est enfoncée, activer la vitesse de lumière
        if keys[pygame.K_1] and self.light_speed_available and not self.light_speed_active and self.light_speed_cooldown == 0:
            self.light_speed_active = True # Active la vitesse de lumière
            self.original_speed = self.speed # Sauvegarde la vitesse actuelle
            self.speed *= 2  # Double la vitesse pendant la vitesse de lumière
            self.light_speed_timer = current_time + 2000   # 2 secondes de durée
            self.light_speed_cooldown = 20000  # 20 secondes de recharge
    # Si la touche '2' est enfoncée, activer l'invulnérabilité
        if keys[pygame.K_2] and self.invulnerability_available and not self.invulnerability_active and self.invulnerability_cooldown == 0:
            self.invulnerability_active = True # Active l'invulnérabilité
            self.invincible_time = 10000  # 10 secondes de durée
            self.invulnerability_timer = current_time + 10000
            self.invulnerability_cooldown = 20000   # 20 secondes de recharge
        # Si la touche '3' est enfoncée, activer les tirs chargés
        if keys[pygame.K_3] and self.charged_shots_available and self.charged_shots_cooldown == 0:
            self.charged_shots_remaining = 5  # Active 5 tirs critiques
            self.charged_shots_cooldown = 20000  # 20 secondes de recharge

    def draw(self, window):
        # Dessiner le champ de force s'il est actif
        if self.forcefield_damage > 0:
            # Dessiner plusieurs cercles pour l'effet de champ de force
            alpha = 50 # Opacité initiale
            for radius in [180, 190, 200]: # Cercles concentriques avec différents rayons
                # Créer une surface temporaire avec transparence (SRCALPHA)
                s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (100, 200, 255, alpha), (radius, radius), radius, 2)
                window.blit(s, (self.rect.centerx - radius, self.rect.centery - radius))
                alpha += 20

        # Dessiner le vaisseau avec un effet de clignotement d'invincibilité
        if self.invincible_time > 0 and self.invincible_time % 4 < 2:
            temp_image = self.image.copy()
            temp_image.fill((255, 255, 255, 128), special_flags=pygame.BLEND_RGBA_MULT)
            window.blit(temp_image, self.rect)
        else:
            # Si le vaisseau n'est pas invincible ou que l'effet de flash est inactif, dessiner l'image normale
            window.blit(self.image, self.rect)


def creer_vaisseau(skin_info, damage_manager):
    # Vérifier si skin_info est une chaîne ou un dictionnaire
    if isinstance(skin_info, str):
        skin_name = skin_info
    elif isinstance(skin_info, dict):
        skin_name = skin_info.get('name', 'Basic Ship')
    else:
        # Type inconnu, utiliser le vaisseau par défaut
        return Ship(damage_manager=damage_manager)

    # Par défaut, utiliser les valeurs standard du vaisseau basique
    ship_params = {
        'image_path': 'images/vaisseau_joueur.png',
        'ship_health': 100,
        'ship_wall_bounces': 0,
        'ship_range': 300,
        'ship_speed': 5
    }

    # Modifier les paramètres selon le type de vaisseau
    if skin_name == "Cristal Ship":
        ship_params.update({
            'image_path': 'images/vaisseau_joueur_cristal.png',
            'ship_health': 200,
            'ship_damage': 15,
            'ship_reload_speed': 0.7,
            'ship_speed': 4.5,
            'ship_bullet_size': 7,
            'ship_bullet_speed': 7
        })
    elif skin_name == "Amethyst Ship":
        ship_params.update({
            'image_path': 'images/vaisseau_joueur_amethyste.png',
            'ship_health': 80,
            'ship_reload_speed': 1.75,
            'ship_speed': 6.5,
            'ship_bullet_speed': 10
        })
    elif skin_name == "Plasma Ship":
        ship_params.update({
            'image_path': 'images/vaisseau_joueur_plasma.png',
            'ship_bullet_piercing': 3,
            'ship_range': 150,
            'ship_speed': 4.5,
            'ship_damage':50,
            'ship_reload_speed': 0.5,
            'ship_bullet_speed':10
        })
    elif skin_name == "Emerald Ship":
        ship_params.update({
            'image_path': 'images/vaisseau_joueur_emeraude.png',
            'ship_health': 80,
            'ship_wall_bounces': 3,
            'ship_range': 2500,
            'ship_speed': 4.6
        })
    elif skin_name == "Diamond Ship":
        ship_params.update({
            'image_path': 'images/vaisseau_joueur_diamant.png',
            'ship_health': 200,
            'ship_speed': 6.2,
            'ship_damage': 30,
            'ship_explosion_radius': 50
        })

    # Créer le vaisseau avec les paramètres appropriés
    ship = Ship(damage_manager=damage_manager, **ship_params)
    return ship


class Bullet:
    def __init__(self, x, y, angle, ship):
        self.x = x
        self.y = y
        self.angle = angle
        self.radius = ship.bullet_size
        self.piercing = ship.bullet_piercing
        self.enemy_bounces = ship.enemy_bounces
        self.wall_bounces = ship.wall_bounces
        self.speed = ship.bullet_speed
        self.damage = ship.damage
        self.explosion_radius = ship.explosion_radius
        self.hit_enemies = set()
        self.distance_traveled = 0
        self.max_range = ship.range
        # Indicateur de coup critique
        self.is_critical = False
        # affiche le nombre de dégats
        self.damage_numbers = []  # List of {x, y, damage, time_left, color}
        # animation d'explosion
        self.is_exploding = False
        self.explosion_time = 30  # frames
        self.explosion_alpha = 255
        # Suivre le vaisseau qui a tiré cette balle (pour l'identification du réseau)
        self.fired_by_local = getattr(ship, 'is_local', True)

        size=(self.radius*10,self.radius*2)
        loaded_image = pygame.image.load('images/projectile_joueur.png').convert_alpha()
        self.image = pygame.transform.scale(loaded_image, size) # stock l'originale
        self.original_image = self.image # Garder une référence si nécessaire, mais le dessin utilise l'original

    def move(self):
        dx = self.speed * math.cos(self.angle)
        dy = self.speed * math.sin(self.angle)
        self.x += dx
        # Utilise dy négatif pour coincider avec les coordonnées de la souris
        self.y -= dy  
    
        self.distance_traveled += math.hypot(dx, dy)

    def draw(self, window):
        # Faire pivoter l'image du projectile en fonction de l'angle

        self.rotated_image= pygame.transform.rotate(self.image,math.degrees(self.angle))
        window.blit(self.rotated_image, (self.x, self.y))   # Afficher l'image du projectile à sa position (x, y)
        pygame.draw.circle(window, (255, 0, 0), (int(self.x), int(self.y)), self.radius)
        

    def explode(self, enemies, damage_manager=None):
         # Si l'explosion n'a pas encore eu lieu et que le rayon est supérieur à 0
        if not self.is_exploding and self.explosion_radius > 0:
            self.is_exploding = True
            self.explosion_time = 30

            # Appliquer des dégâts aux ennemis à proximité de l'explosion
            for enemy in enemies[:]:
                if enemy not in self.hit_enemies:
                    # Calculer la distance entre le projectile et l'ennemi
                    distance = math.hypot(self.x - enemy.x, self.y - enemy.y)
                    if distance <= self.explosion_radius:
                        enemy.health -= self.damage * 0.5  # Dégâts réduits pour l'explosion
                        if damage_manager:
                            damage_manager.add_damage_number(enemy.x, enemy.y - enemy.radius, self.damage * 0.5, getattr(self, 'is_critical', False))

            explosion_surface = pygame.Surface((self.explosion_radius * 2, self.explosion_radius * 2), pygame.SRCALPHA)

            # Calculate alpha based on remaining time
            alpha = int((self.explosion_time / 30) * self.explosion_alpha)
            pygame.draw.circle(explosion_surface, (100, 200, 255, alpha),
                            (self.explosion_radius, self.explosion_radius),
                                    self.explosion_radius, 2)
            window.blit(explosion_surface,
                       (int(self.x - self.explosion_radius),
                        int(self.y - self.explosion_radius)))
            self.explosion_time -= 1
        return


    def bounce_off_wall(self, wall_type):
        # Si la balle frappe un mur vertical
        if wall_type == "vertical":   # Mur à gauche ou à droite
            self.angle = math.pi - self.angle # Inverser l'angle horizontal
        elif wall_type == "horizontal":  # mur en bas ou en haut
            self.angle = -self.angle
        self.wall_bounces -= 1

    def bounce_off_enemy(self, enemy_x, enemy_y):
         # Calculer la direction entre la balle et l'ennemi
        dx = self.x - enemy_x
        dy = self.y - enemy_y
        new_angle = math.atan2(dy, dx)
        self.angle = new_angle
        # Définir une distance de sécurité pour éviter que la balle n'entre trop dans l'ennemi

        safe_distance = max(50, self.speed * 2)
# Calculer la nouvelle position de la balle après le rebond
        self.x = enemy_x + safe_distance * math.cos(self.angle)
        self.y = enemy_y + safe_distance * math.sin(self.angle)
# Réduire le nombre de rebonds sur les ennemis
        self.enemy_bounces -= 1
