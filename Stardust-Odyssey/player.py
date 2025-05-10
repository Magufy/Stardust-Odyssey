import pygame
import random
import math

pygame.init()

# Paramètres de la fenêtre en plein écran
window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = window.get_size()
pygame.display.set_caption("Nova Drift Prototype - Fullscreen Mode")

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
        self. velocite_haut=0
        self. velocite_bas=0
        self. velocite_droite=0
        self. velocite_gauche=0

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
        
        # Initialize le damage manager
        self.damage_manager = damage_manager
        self.forcefield_damage = 0
        self.last_forcefield_time = pygame.time.get_ticks()
        
        # Indiquer si c'est le vaisseau local ou distant (pour le multijoueur)
        self.is_local = True  # Par défaut, c'est le vaisseau local

        # Light Speed ability
        self.light_speed_available = False
        self.light_speed_active = False
        self.light_speed_timer = -1
        self.light_speed_cooldown = 0
        self.original_speed = self.speed

        # Invulnerability ability
        self.invulnerability_available = False
        self.invulnerability_active = False
        self.invulnerability_timer = -1
        self.invulnerability_cooldown = 0

        # Charged Shots ability
        self.charged_shots_available = False
        self.charged_shots_remaining = 0
        self.charged_shots_cooldown = 0
        self.crit_chance = 5  # 5% base crit chance
        self.crit_multiplier = 1.5

        self.upgrades = []
        self.stun_timer=0

    def move(self):
        if self.stun_timer > 0:
            return

        if not self.is_local:
            return

        keys = pygame.key.get_pressed()

        if keys[pygame.K_z] and self. velocite_haut < 1 :  # Avancer
            self. velocite_haut += 0.02
        if keys[pygame.K_s] and self. velocite_bas < 1 :  # Reculer
            self. velocite_bas += 0.02
        if keys[pygame.K_q] and self. velocite_gauche < 1 :  # Gauche
            self. velocite_gauche += 0.02
        if keys[pygame.K_d] and self. velocite_droite < 1 :  # Droite
            self. velocite_droite += 0.02

        if self. velocite_haut > 0 :
            self.rect.y -= self. velocite_haut* self.speed
        if self. velocite_bas > 0 :
            self.rect.y += self. velocite_bas* self.speed
        if self. velocite_gauche > 0 :
            self.rect.x -= self. velocite_gauche* self.speed
        if self. velocite_droite > 0 :
            self.rect.x += self. velocite_droite* self.speed

        if self. velocite_haut > 0 and not keys[pygame.K_z]:
            self. velocite_haut -= 0.01
        if self. velocite_bas > 0 and not keys[pygame.K_s]:
            self. velocite_bas -= 0.01
        if self. velocite_gauche > 0 and not keys[pygame.K_q]:
            self. velocite_gauche -= 0.01
        if self. velocite_droite > 0 and not keys[pygame.K_d]:
            self. velocite_droite -= 0.01

        #TP de bord à bord de l'écran
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
        mouse_x, mouse_y = pygame.mouse.get_pos()
        dx, dy = mouse_x - self.rect.centerx, mouse_y - self.rect.centery
        self.angle = math.degrees(math.atan2(-dy, dx))
        self.image = pygame.transform.rotate(self.original_image, self.angle+90)
        self.rect = self.image.get_rect(center=self.rect.center)

    def shoot(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot_time < 1000 / self.reload_speed:  # 1000ms base cooldown
            return

        son_tir=pygame.mixer.Sound("sons/tir_joueur.mp3")
        son_tir.play()

        angle_rad = math.radians(self.angle)
        if self.parallel_shots == 1:
            bullet_x = self.rect.centerx + 20 * math.cos(angle_rad)
            bullet_y = self.rect.centery - 20 * math.sin(angle_rad)
            bullet = Bullet(bullet_x, bullet_y, angle_rad, self)
            
            # Check for critical hit - either from charged shots or random chance
            is_crit = False
            if self.charged_shots_remaining > 0:
                is_crit = True
                self.charged_shots_remaining -= 1
            else:
                is_crit = True if random.randint(0, 100) < self.crit_chance else False # 5% de base
            
            if is_crit:
                bullet.damage *= self.crit_multiplier  # 50% de base
                bullet.is_critical = True  # Set critical hit visual indicator
            self.bullets.append(bullet)
        else:
            spread = 15  # degrees between bullets
            for i in range(self.parallel_shots):
                offset = spread * (i - (self.parallel_shots - 1) / 2)
                bullet_angle = angle_rad + math.radians(offset)
                bullet_x = self.rect.centerx + 20 * math.cos(bullet_angle)
                bullet_y = self.rect.centery - 20 * math.sin(bullet_angle)
                bullet = Bullet(bullet_x, bullet_y, bullet_angle, self)
                
                # Check for critical hit - either from charged shots or random chance
                is_crit = False
                if self.charged_shots_remaining > 0:
                    is_crit = True
                    self.charged_shots_remaining -= 1
                else:
                    is_crit = True if random.randint(0, 100) < self.crit_chance else False # 5% de base
                
                if is_crit:
                    bullet.damage *= self.crit_multiplier  # critiques
                    bullet.is_critical = True  # Set critical hit visual indicator
                self.bullets.append(bullet)

        self.last_shot_time = current_time

    def update(self, enemies):
        current_time = pygame.time.get_ticks()
        
        # Update bullets
        for bullet in self.bullets[:]:
            bullet.move()

        if self.health < self.max_health:
            self.health = min(self.max_health, self.health + self.regen_rate / 60)
        if self.invincible_time > 0:
            self.invincible_time -= 1

        # Apply forcefield damage
        if self.forcefield_damage > 0:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_forcefield_time >= 1000:  # Apply damage every second (1000ms)
                self.last_forcefield_time = current_time
                for enemy in enemies[:]:
                    distance = math.hypot(self.rect.centerx - enemy.x, self.rect.centery - enemy.y)
                    if distance <= 200:
                        enemy.health -= self.forcefield_damage
                        if enemy.health <= 0:
                            enemies.remove(enemy)

        if self.stun_timer>0:
            self.stun_timer-=1
# Update cooldowns
        if self.light_speed_cooldown > 0:
            self.light_speed_cooldown = max(0, self.light_speed_cooldown - 16)  # 16ms per frame
        if self.invulnerability_cooldown > 0:
            self.invulnerability_cooldown = max(0, self.invulnerability_cooldown - 16)
        if self.charged_shots_cooldown > 0:
            self.charged_shots_cooldown = max(0, self.charged_shots_cooldown - 16)

        # Check Light Speed duration
        if self.light_speed_active and current_time >= self.light_speed_timer:
            self.light_speed_active = False
            self.speed = self.original_speed

        # Check Invulnerability duration
        if self.invulnerability_active and current_time >= self.invulnerability_timer:
            self.invulnerability_active = False
            self.invincible_time = 0

        # Handle ability inputs
        keys = pygame.key.get_pressed()
        if keys[pygame.K_1] and self.light_speed_available and not self.light_speed_active and self.light_speed_cooldown == 0:
            self.light_speed_active = True
            self.original_speed = self.speed
            self.speed *= 2  # Double speed during Light Speed
            self.light_speed_timer = current_time + 2000  # 2 seconds duration
            self.light_speed_cooldown = 20000  # 20 seconds cooldown

        if keys[pygame.K_2] and self.invulnerability_available and not self.invulnerability_active and self.invulnerability_cooldown == 0:
            self.invulnerability_active = True
            self.invincible_time = 2000  # 2 seconds duration
            self.invulnerability_timer = current_time + 2000
            self.invulnerability_cooldown = 20000  # 20 seconds cooldown

        if keys[pygame.K_3] and self.charged_shots_available and self.charged_shots_cooldown == 0:
            self.charged_shots_remaining = 5  # Activate 5 critical shots
            self.charged_shots_cooldown = 20000  # 20 seconds cooldown

    def draw(self, window):
        # Draw forcefield if active
        if self.forcefield_damage > 0:
            # Draw multiple circles for forcefield effect
            alpha = 50
            for radius in [180, 190, 200]:
                s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (100, 200, 255, alpha), (radius, radius), radius, 2)
                window.blit(s, (self.rect.centerx - radius, self.rect.centery - radius))
                alpha += 20

        # Draw ship with invincibility flash
        if self.invincible_time > 0 and self.invincible_time % 4 < 2:
            temp_image = self.image.copy()
            temp_image.fill((255, 255, 255, 128), special_flags=pygame.BLEND_RGBA_MULT)
            window.blit(temp_image, self.rect)
        else:
            window.blit(self.image, self.rect)


def creer_vaisseau(skin_info, damage_manager):
    # Vérifier si skin_info est une chaîne ou un dictionnaire
    if isinstance(skin_info, str):
        skin_name = skin_info
    elif isinstance(skin_info, dict):
        skin_name = skin_info.get('name', 'Vaisseau Basique')
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
    if skin_name == "Vaisseau Cristal":
        ship_params.update({
            'image_path': 'images/vaisseau_joueur_cristal.png',
            'ship_health': 200,
            'ship_damage': 15,
            'ship_reload_speed': 0.7,
            'ship_speed': 4.5,
            'ship_bullet_size': 7,
            'ship_bullet_speed': 7
        })
    elif skin_name == "Vaisseau Améthyste":
        ship_params.update({
            'image_path': 'images/vaisseau_joueur_amethyste.png',
            'ship_health': 80,
            'ship_reload_speed': 1.75,
            'ship_speed': 6.5,
            'ship_bullet_speed': 10
        })
    elif skin_name == "Vaisseau Plasma":
        ship_params.update({
            'image_path': 'images/vaisseau_joueur_plasma.png',
            'ship_bullet_piercing': 3,
            'ship_range': 150,
            'ship_speed': 4.5,
            'ship_damage':20,
            'ship_reload_speed': 0.5,
            'ship_bullet_speed':10
        })
    elif skin_name == "Vaisseau Emeraude":
        ship_params.update({
            'image_path': 'images/vaisseau_joueur_emeraude.png',
            'ship_health': 80,
            'ship_wall_bounces': 3,
            'ship_range': 2500,
            'ship_speed': 4.6
        })
    elif skin_name == "Vaisseau Diamant":
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
        # Critical hit indicator
        self.is_critical = False
        # Damage number display
        self.damage_numbers = []  # List of {x, y, damage, time_left, color}
        # Explosion animation
        self.is_exploding = False
        self.explosion_time = 30  # frames
        self.explosion_alpha = 255
        # Track the ship that fired this bullet (for network identification)
        self.fired_by_local = getattr(ship, 'is_local', True)

        size=(self.radius*10,self.radius*2)
        loaded_image = pygame.image.load('images/projectile_joueur.png').convert_alpha()
        self.image = pygame.transform.scale(loaded_image, size) # Store original
        self.original_image = self.image # Keep a reference if needed, but draw uses original

    def move(self):
        dx = self.speed * math.cos(self.angle)
        dy = self.speed * math.sin(self.angle)
        self.x += dx
        self.y -= dy  # Use negative dy to match mouse coordinates
        self.distance_traveled += math.hypot(dx, dy)

    def draw(self, window):

        self.rotated_image= pygame.transform.rotate(self.image,math.degrees(self.angle))
        window.blit(self.rotated_image, (self.x, self.y))
        
        if self.is_exploding and self.explosion_radius > 0:
            current_radius = self.explosion_radius * (self.explosion_time / 60)
            
            if self.fired_by_local:
                color = (255, 100, 50, min(200, 255 * (self.explosion_time / 30)))
            else: 
                color = (150, 50, 255, min(200, 255 * (self.explosion_time / 30)))
            
            pygame.draw.circle(
                window, 
                color,
                (int(self.x), int(self.y)),
                int(current_radius),
                3
            )
         
            pygame.draw.circle(
                window,
                (255, 255, 255, min(255, 300 * (self.explosion_time / 60))),
                (int(self.x), int(self.y)),
                int(current_radius * 0.4)
            )
            
            self.explosion_time -= 1

    def explode(self, enemies, damage_manager=None):
        if not self.is_exploding and self.explosion_radius > 0:
            self.is_exploding = True
            self.explosion_time = 30

            # Damage nearby enemies
            for enemy in enemies[:]:
                if enemy not in self.hit_enemies:
                    distance = math.hypot(self.x - enemy.x, self.y - enemy.y)
                    if distance <= self.explosion_radius:
                        enemy.health -= self.damage * 0.5  # Half damage for explosion
                        if enemy.health <= 0:
                            enemies.remove(enemy)

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
        if wall_type == "vertical":   # Left or right wall
            self.angle = math.pi - self.angle
        elif wall_type == "horizontal":  # Top or bottom wall
            self.angle = -self.angle
        self.wall_bounces -= 1

    def bounce_off_enemy(self, enemy_x, enemy_y):
        dx = self.x - enemy_x
        dy = self.y - enemy_y
        new_angle = math.atan2(dy, dx)
        self.angle = new_angle

        safe_distance = max(50, self.speed * 2)
        self.x = enemy_x + safe_distance * math.cos(self.angle)
        self.y = enemy_y + safe_distance * math.sin(self.angle)
        self.enemy_bounces -= 1
