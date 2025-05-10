import pygame
import random
import math

WHITE = (255, 255, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)

pygame.init()

# Paramètres de la fenêtre en plein écran
window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = window.get_size()
pygame.display.set_caption("Nova Drift Prototype - Fullscreen Mode")

class Enemy:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.health = 0
        self.damage = 0
        self.radius = 0
        self.speed = 0
        self.color = WHITE
        self.image = None
        self.damage_numbers = []
        self.damage_font = pygame.font.Font(None, 120)  # Police énorme

        edge = random.choice(["top", "bottom", "left", "right"])
        margin = 50

        if edge == "top":
            self.x = random.randint(0, WIDTH)
            self.y = -margin
        elif edge == "bottom":
            self.x = random.randint(0, WIDTH)
            self.y = HEIGHT + margin
        elif edge == "left":
            self.x = -margin
            self.y = random.randint(0, HEIGHT)
        else:  # droite
            self.x = WIDTH + margin
            self.y = random.randint(0, HEIGHT)

    def is_on_screen(self):
        margin = 100
        return (-margin <= self.x <= WIDTH + margin and
                -margin <= self.y <= HEIGHT + margin)


    def draw(self, window):
        # Dessiner l'ennemi d'abord
        if self.image:
            rect = self.image.get_rect(center=(int(self.x), int(self.y)))
            window.blit(self.image, rect)
        
        # Draw health bar for bosses
        if hasattr(self, 'healthbar') and self.healthbar and hasattr(self, 'maxhealth'):
            health_ratio = 0
            if self.maxhealth > 0:
                health_ratio = self.health / self.maxhealth
            else: # Handle case where maxhealth might not be set correctly
                health_ratio = 0 if self.health <= 0 else 1

            bar_width = 600
            current_bar_width = int(bar_width * health_ratio)
            bar_x = WIDTH // 2 - bar_width // 2
            bar_y = 20
            bar_height = 20

            # Draw the background bar
            pygame.draw.rect(window, GRAY, (bar_x, bar_y, bar_width, bar_height))
            # Draw the health portion
            pygame.draw.rect(window, RED, (bar_x, bar_y, current_bar_width, bar_height))
            # Draw the border
            pygame.draw.rect(window, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)

            # Draw boss name if available
            if hasattr(self, 'bossname'):
                font = pygame.font.Font(None,36)
                self.font = pygame.font.Font(None, 36)
                bosstag = font.render(self.bossname, True, WHITE)
                # Center the boss name text above the health bar
                tag_rect = bosstag.get_rect(center=(WIDTH // 2, bar_y + bar_height // 2))
                window.blit(bosstag, tag_rect)
        
        # Dessiner les numéros de dégâts en dernier (pour être au-dessus)
        for number in self.damage_numbers[:]:
            number['y'] -= 1.5
            number['time'] -= 1
            
            if number['time'] <= 0:
                self.damage_numbers.remove(number)
                continue
            
            # Créer le texte
            damage_str = str(number['damage'])
            
            x = int(number['x'])
            y = int(number['y'])

            # Texte coloré au centre
            text = self.damage_font.render(damage_str, True, number['color'])
            window.blit(text, 
                       (x - text.get_width()//2,
                        y - text.get_height()//2))

    def show_damage(self, damage, is_critical):
        print("Création d'un nombre de dégâts")
        
        # Couleurs très contrastées
        if is_critical:
            color = RED
        else:
            color = YELLOW 
        
        # Position initiale
        x = int(self.x)
        y = int(self.y) - 80  # Juste au-dessus de l'ennemi
        
        # Créer le nombre
        number = {
            'x': x,
            'y': y,
            'damage': int(damage),
            'time': 90,
            'color': color
        }
        
        # Ajouter à la liste
        self.damage_numbers.append(number)
        print(f"Nombre ajouté: {damage} à ({x}, {y})")


        # Draw health bar for bosses
        # Ensure 'enemies' list is accessible if needed here, or pass necessary info
        # Using hasattr check is safer than assuming global 'enemies' is always up-to-date/correct
        if hasattr(self, 'healthbar') and self.healthbar and hasattr(self, 'maxhealth'): # Check for maxhealth too

            # Prevent division by zero if maxhealth is 0
            health_ratio = 0
            if self.maxhealth > 0:
                health_ratio = self.health / self.maxhealth
            else: # Handle case where maxhealth might not be set correctly
                health_ratio = 0 if self.health <= 0 else 1

            bar_width = 600
            current_bar_width = int(bar_width * health_ratio)
            bar_x = WIDTH // 2 - bar_width // 2
            bar_y = 20
            bar_height = 20

            # Draw the background bar
            pygame.draw.rect(window, GRAY, (bar_x, bar_y, bar_width, bar_height))
            # Draw the health portion
            pygame.draw.rect(window, RED, (bar_x, bar_y, current_bar_width, bar_height))
            # Draw the border
            pygame.draw.rect(window, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)

            # Draw boss name if available
            if hasattr(self, 'bossname'):
                bosstag = font.render(self.bossname, True, WHITE)
                # Center the boss name text above the health bar
                tag_rect = bosstag.get_rect(center=(WIDTH // 2, bar_y + bar_height // 2))
                window.blit(bosstag, tag_rect)

    def check_collision(self, player):
        if player.invincible_time > 0:
            return False

        distance = math.hypot(player.rect.centerx - self.x, player.rect.centery - self.y)
        if distance < self.radius + 20: # Use player radius (assuming 20)
            # degats - shield
            damage_to_player = self.damage * (1 - player.shield / 100)
            player.health -= damage_to_player
            son_degat=pygame.mixer.Sound("sons/degat_joueur.mp3")
            son_degat.play()
            player.health = max(0, player.health) # Clamp health to minimum 0
            player.invincible_time = 60

            # Body damage logic if player has it
            if hasattr(player, 'body_damage') and player.body_damage > 0:
                # Apply body damage to the enemy
                self.health -= player.body_damage
                if hasattr(player, 'damage_manager') and player.damage_manager:
                    player.damage_manager.add_damage_number(self.x, self.y - self.radius, player.body_damage, False)

            # Envoyer une mise à jour de santé si on est en multijoueur et que ce n'est pas le joueur principal
            # qui est touché (principal au sens du point de vue de cette instance de jeu)
            if hasattr(self, 'p2p_comm') and self.p2p_comm:
                # Si ce joueur est le joueur distant (donc joueur 2 depuis le serveur, ou joueur 1 depuis le client)
                is_server = getattr(self.p2p_comm, 'est_serveur', True)
                is_local_player = hasattr(player, 'is_local') and player.is_local

                if not is_local_player:
                    if is_server:
                        # Si c'est le serveur qui détecte collision avec joueur 2
                        self.p2p_comm.envoyer_donnees({
                            'type': 'damage_update',
                            'player2_health': player.health,
                            'player2_invincible_time': player.invincible_time,
                            'player2_regen_rate': player.regen_rate,
                            'player2_max_health': player.max_health
                        })
                    else:
                        # Si c'est le client qui détecte collision avec joueur 1 (cas rare)
                        self.p2p_comm.envoyer_donnees({
                            'type': 'damage_update',
                            'player1_health': player.health,
                            'player1_invincible_time': player.invincible_time,
                            'player1_regen_rate': player.regen_rate,
                            'player1_max_health': player.max_health
                        })

            return True
        return False

    def update(self, player):
        pass  # sous classe

    def move_towards(self, player):
        pass  # sous classe

class BasicEnemy(Enemy):
    def __init__(self):
        super().__init__()
        self.radius = 20
        self.speed = 2
        self.health = 20
        self.damage = 10
        self.color = RED
        self.type= [BasicEnemy]
        self.angle = 0 # Initialize angle

        # Load image
        image_path = 'images/enemi_rouge.png' # Make sure this path is correct

        loaded_image = pygame.image.load(image_path).convert_alpha()
        size = (self.radius * 2, self.radius * 2)
        self.original_image = pygame.transform.scale(loaded_image, size) # Store original
        self.image = self.original_image # Keep a reference if needed, but draw uses original


    def draw(self,window):
        # Rotate the original image for drawing
        rotated_image = pygame.transform.rotate(self.original_image, self.angle) # Adjust angle as needed
        new_rect = rotated_image.get_rect(center=(int(self.x), int(self.y)))
        window.blit(rotated_image, new_rect)
        # Do not call super().draw() as we handle drawing here

    def move_towards(self, player):
        dx = player.rect.centerx - self.x
        dy = player.rect.centery - self.y
        distance = math.hypot(dx, dy)

        if distance <= player.range or self.is_on_screen():
            if distance != 0:
                dx_norm = dx / distance
                dy_norm = dy / distance
                self.x += dx_norm * self.speed
                self.y += dy_norm * self.speed

    def update(self, player):
        self.move_towards(player)

        # Calcul l' angle 
        dx = player.rect.centerx - self.x
        dy = player.rect.centery - self.y
        # Update self.angle, used by draw method
        self.angle = math.degrees(math.atan2(-dy, dx))



class TankEnemy(Enemy):
    def __init__(self):
        super().__init__()
        self.radius = 30
        self.speed = 1
        self.health = 40
        self.damage = 20
        self.color = YELLOW
        self.type= [TankEnemy]
        self.angle = 0 # Initialize angle

        # Load image
        image_path = 'images/enemi_jaune.png' # Make sure this path is correct
        try:
            loaded_image = pygame.image.load(image_path).convert_alpha()
            size = (self.radius * 2, self.radius * 2)
            self.original_image = pygame.transform.scale(loaded_image, size) # Store original
            self.image = self.original_image # Keep reference if needed
        except pygame.error as e:
            print(f"Error loading image {image_path}: {e}")
            self.original_image = pygame.Surface((self.radius*2, self.radius*2)); self.original_image.fill(self.color)
            self.image = self.original_image # Keep reference

    def move_towards(self, player):
        dx = player.rect.centerx - self.x
        dy = player.rect.centery - self.y
        distance = math.hypot(dx, dy)

        if distance <= player.range or self.is_on_screen():
            if distance != 0:
                dx_norm = dx / distance
                dy_norm = dy / distance
                self.x += dx_norm * self.speed
                self.y += dy_norm * self.speed

    def update(self, player):
        self.move_towards(player)
        # Calculate angle in update
        dx = player.rect.centerx - self.x
        dy = player.rect.centery - self.y
        # Update self.angle, used by draw method
        self.angle = math.degrees(math.atan2(-dy, dx))

    def draw(self,window):
        # Rotate the original image for drawing
        rotated_image = pygame.transform.rotate(self.original_image, self.angle) # Adjust angle offset if needed
        new_rect = rotated_image.get_rect(center=(int(self.x), int(self.y)))
        window.blit(rotated_image, new_rect)
        # Do not call super().draw()

class ShooterEnemy(Enemy):
    def __init__(self):
        super().__init__()
        self.radius = 25
        self.speed = 3
        self.health = 30
        self.damage = 15
        self.color = GREEN
        self.type= [ShooterEnemy]
        self.angle = 0 # Initialize angle

        self.shoot_cooldown = 0
        self.shoot_delay = random.randint(60, 120)
        self.projectiles = []

        self.target_x = 0
        self.target_y = 0
        self.stationary_time = 300   # 5 secondes
        self.stationary_timer = 0
        self.is_moving = True
        self.pick_new_position()

        # Load image
        image_path = 'images/enemi_vert.png'

        loaded_image = pygame.image.load(image_path).convert_alpha()
        size = (self.radius * 2, self.radius * 2)
        self.original_image = pygame.transform.scale(loaded_image, size) # Store original
        self.image = self.original_image # Keep reference

        loaded_proj_image = pygame.image.load('images/projectile_enemi.png').convert_alpha()
        size = ( 50, 20)
        self.original_proj_image = pygame.transform.scale(loaded_proj_image, size) # Store original
        self.proj_image = self.original_proj_image # Keep reference



    def pick_new_position(self):
        margin = 100
        self.target_x = random.randint(margin, WIDTH - margin)
        self.target_y = random.randint(margin, HEIGHT - margin)

    def update(self, player):
        if self.is_moving:
            dx = self.target_x - self.x
            dy = self.target_y - self.y
            distance = math.hypot(dx, dy)

            # Calculate angle towards movement target
            if distance > 0:
                self.angle = math.degrees(math.atan2(-dy, dx))

            if distance < self.speed:  # est au point aleatoire
                self.x = self.target_x
                self.y = self.target_y
                self.is_moving = False
                self.stationary_timer = self.stationary_time
            else: #va au point aleatoire
                self.x += (dx / distance) * self.speed
                self.y += (dy / distance) * self.speed

        else:
            # Calculate angle towards player only when stationary
            dx_player = player.rect.centerx - self.x
            dy_player = player.rect.centery - self.y
            self.angle = math.degrees(math.atan2(-dy_player, dx_player))

            self.stationary_timer -= 1
            if self.stationary_timer <= 0:
                self.is_moving = True
                self.pick_new_position()
            else:
                # Only shoot when stationary
                self.shoot_cooldown = max(0, self.shoot_cooldown - 1)
                if self.shoot_cooldown == 0:
                    # Use the pre-calculated angle (towards player)
                    self.projectiles.append({
                        'x': self.x,
                        'y': self.y,
                        'angle': math.radians(self.angle), # Use the calculated angle
                        'speed': 5,
                        'radius': 5
                    })
                    self.shoot_cooldown = self.shoot_delay

        # Update projectiles
        for proj in self.projectiles[:]:
            proj['x'] += proj['speed'] * math.cos(proj['angle'])
            proj['y'] -= proj['speed'] * math.sin(proj['angle'])

            # Remove if off screen
            if (proj['x'] < -50 or proj['x'] > WIDTH + 50 or
                proj['y'] < -50 or proj['y'] > HEIGHT + 50):
                if proj in self.projectiles: self.projectiles.remove(proj) # Safe remove
                continue

            # Check collision with player
            if not player.invincible_time > 0:
                dist = math.hypot(player.rect.centerx - proj['x'],
                                player.rect.centery - proj['y'])
                if dist < proj['radius'] + 20: # Use player radius (assuming 20)
                    damage = self.damage * (1 - player.shield / 100)
                    player.health -= damage
                    son_degat=pygame.mixer.Sound("sons/degat_joueur.mp3")
                    son_degat.play()
                    player.health = max(0, player.health) # Clamp health to minimum 0
                    player.invincible_time = 60
                    if proj in self.projectiles: self.projectiles.remove(proj) # Safe remove
                    continue # Skip second player check if removed

            # Si nous sommes dans le jeu en multijoueur, on vérifie aussi une collision avec l'autre joueur
            if hasattr(self, 'second_player') and self.second_player and not self.second_player.invincible_time > 0:
                dist = math.hypot(self.second_player.rect.centerx - proj['x'],
                               self.second_player.rect.centery - proj['y'])
                if dist < proj['radius'] + 20:
                    damage = self.damage * (1 - self.second_player.shield / 100)
                    self.second_player.health -= damage
                    self.second_player.health = max(0, self.second_player.health)
                    self.second_player.invincible_time = 60
                    if proj in self.projectiles: self.projectiles.remove(proj) # Safe remove
                    # NOTE: Network update call removed here as requested by user.

    def draw(self, window):
        # Rotate the original image for drawing
        rotated_image = pygame.transform.rotate(self.original_image, self.angle) # Adjust angle offset if needed
        new_rect = rotated_image.get_rect(center=(int(self.x), int(self.y)))
        window.blit(rotated_image, new_rect)
        # Do not call super().draw()

        # Draw projectiles
        for proj in self.projectiles:
            angle = math.degrees(proj['angle'])
            rotated_proj_image = pygame.transform.rotate(self.original_proj_image, angle) # Adjust angle offset if needed
            new_rect = rotated_proj_image.get_rect(center=(int(proj['x']), int(proj['y'])))
            window.blit(rotated_proj_image, new_rect)

class LinkEnemy(Enemy):
    def __init__(self):
        super().__init__()
        self.radius = 50
        self.speed = 1
        self.health = 100
        self.damage = 20
        self.color = WHITE
        self.type = [LinkEnemy]

        # Attributs de mouvement
        self.target_x = 0
        self.target_y = 0
        self.is_moving = False
        self.stationary_timer = 0

        # Pour le stockage des lasers actifs (pour la détection de collision)
        self.active_lasers = []  # [{'start': (x1, y1), 'end': (x2, y2), 'damage': 20}, ...]

        # Load image
        image_path = 'images/enemi_blanc.png'
        try:
            loaded_image = pygame.image.load(image_path).convert_alpha()
            size = (self.radius * 2, self.radius * 2)
            self.image = pygame.transform.scale(loaded_image, size)
        except pygame.error as e:
            print(f"Error loading image {image_path}: {e}")
            self.image = pygame.Surface((self.radius*2, self.radius*2)); self.image.fill(self.color)

    def pick_new_position(self):
        margin = 100
        self.target_x = random.randint(margin, WIDTH - margin)
        self.target_y = random.randint(margin, HEIGHT - margin)

    def update(self, player):
        # Gestion du mouvement
        if self.is_moving:
            dx = self.target_x - self.x
            dy = self.target_y - self.y
            distance = math.hypot(dx, dy)

            if distance > self.speed:  # Use speed threshold
                self.x += (dx / distance) * self.speed
                self.y += (dy / distance) * self.speed
            else:
                self.x = self.target_x # Snap to target
                self.y = self.target_y
                self.is_moving = False
                self.stationary_timer = random.randint(180, 300)  # 3-5 secondes
        else:
            self.stationary_timer -= 1
            if self.stationary_timer <= 0:
                self.is_moving = True
                self.pick_new_position()

        # Calculer les lasers actifs (Optimized)
        self.active_lasers = []
        # Access the global enemies list (ensure it's accessible)
        global enemies
        for other_enemy in enemies:
            # Check only against other LinkEnemy instances, avoid self-check
            if isinstance(other_enemy, LinkEnemy) and other_enemy != self:
                distance = math.hypot(self.x - other_enemy.x, self.y - other_enemy.y)
                if distance < 900:  # Distance maximale pour les lasers
                    alpha = max(0, min(255, int(255 * (1 - distance / 900))))
                    # Store laser data for drawing and collision detection
                    self.active_lasers.append({
                        'start': (self.x, self.y),
                        'end': (other_enemy.x, other_enemy.y),
                        'damage': self.damage * (alpha / 255), # Damage proportional to intensity
                        'alpha': alpha
                    })

    def draw(self, window):
        # Draw enemy body
        super().draw(window)

        # Dessiner les lasers actifs (Optimized Drawing)
        for laser in self.active_lasers:
            # Draw line directly on the window with alpha
            # Note: pygame.draw.line doesn't directly support alpha.
            # We might need a workaround or accept non-alpha lines for performance.
            # Simple approach: Draw non-alpha line for now, adjust color intensity slightly.
            intensity_factor = laser['alpha'] / 255.0
            line_color = (
                int(self.color[0] * intensity_factor),
                int(self.color[1] * intensity_factor),
                int(self.color[2] * intensity_factor)
            )
            # Ensure color components are valid (0-255)
            line_color = tuple(max(0, min(255, c)) for c in line_color)

            if laser['alpha'] > 20: # Only draw reasonably visible lasers
                 pygame.draw.line(window, line_color, laser['start'], laser['end'], 3)

    def check_laser_collision(self, player):
        if player.invincible_time > 0:
            return False

        # active_lasers list is now populated in the update method
        for laser in self.active_lasers:
            # Algorithme de détection de collision entre une ligne et un cercle
            # Basé sur la distance du point le plus proche sur la ligne au centre du cercle
            x1, y1 = laser['start']
            x2, y2 = laser['end']

            # Vecteur de la ligne
            line_vec_x = x2 - x1
            line_vec_y = y2 - y1
            line_length = math.hypot(line_vec_x, line_vec_y)

            # Normaliser le vecteur
            if line_length > 0:
                line_vec_x /= line_length
                line_vec_y /= line_length

            # Vecteur du début de la ligne au centre du joueur
            to_player_x = player.rect.centerx - x1
            to_player_y = player.rect.centery - y1

            # Projection du vecteur joueur sur la ligne
            dot_product = to_player_x * line_vec_x + to_player_y * line_vec_y

            # Trouver le point le plus proche sur la ligne
            closest_x = x1 + dot_product * line_vec_x
            closest_y = y1 + dot_product * line_vec_y

            # S'assurer que ce point est sur le segment de ligne
            if dot_product < 0:  # Point avant le début de la ligne
                closest_x, closest_y = x1, y1
            elif dot_product > line_length:  # Point après la fin de la ligne
                closest_x, closest_y = x2, y2

            # Distance entre le point le plus proche et le centre du joueur
            distance = math.hypot(player.rect.centerx - closest_x, player.rect.centery - closest_y)

            # Collision si la distance est inférieure au rayon du joueur + épaisseur du laser/2
            player_radius = 20  # Assumant un rayon de 20 pour le joueur
            laser_width = 3     # Épaisseur du laser

            if distance < player_radius + laser_width/2:
                damage = laser['damage'] * (1 - player.shield / 100)
                # Ensure damage is at least a small amount if laser is visible
                if laser['alpha'] > 20 and damage <= 0: damage = 1 # Minimum damage for visible laser hits

                if damage > 0: # Only apply damage if it's positive
                    player.health -= damage
                    son_degat=pygame.mixer.Sound("sons/degat_joueur.mp3")
                    son_degat.play()
                    player.health = max(0, player.health)
                    player.invincible_time = 60 # Standard invincibility

                    # Si c'est un joueur distant, envoyer les mises à jour d'état via le réseau
                    # Vérifier si on est en multijoueur et qu'il existe une fonction pour envoyer des données
                    if hasattr(self, 'p2p_comm') and self.p2p_comm and hasattr(self.p2p_comm, 'envoyer_donnees'):
                        is_server = getattr(self.p2p_comm, 'est_serveur', True)

                        # Determine which player got hit based on reference comparison
                        if hasattr(self, 'second_player') and self.second_player == player:
                            # Player 2 (controlled by client) was hit
                            if is_server:
                                self.p2p_comm.envoyer_donnees({
                                    'type': 'damage_update',
                                    'player2_health': player.health,
                                    'player2_invincible_time': player.invincible_time
                                    # Include stun if laser could stun
                                })
                        else:
                            # Player 1 (controlled by server/host) was hit
                            if not is_server:
                                self.p2p_comm.envoyer_donnees({
                                    'type': 'damage_update',
                                    'player1_health': player.health,
                                    'player1_invincible_time': player.invincible_time
                                    # Include stun if laser could stun
                                })
                                return True  # Collision détectée

        return False  # Pas de collision

    def check_collision(self, player):
        # First check regular collision (from parent class)
        collision = super().check_collision(player)

        # Then check laser collisions
        laser_collision = self.check_laser_collision(player)

        return collision or laser_collision

class Tank_Boss(Enemy):
    def __init__(self):
        super().__init__()
        self.radius = 100
        self.speed = 3
        self.health = 600
        self.maxhealth=600
        self.damage = 20
        self.color = RED
        self.type= [Tank_Boss]
        self.bossname= "BEHEMOTH"

        self.shoot_cooldown = 18
        self.projectiles = []

        self.target_x = WIDTH//2
        self.target_y = HEIGHT//2

        self.healthbar=True

        # Load image
        image_path = 'images/boss_rouge.png' 
        loaded_image = pygame.image.load(image_path).convert_alpha()
        size = (self.radius * 2, self.radius * 2)
        self.image = pygame.transform.scale(loaded_image, size)
    
        loaded_proj_image = pygame.image.load('images/projectile_boss1.png').convert_alpha()
        size = ( 80, 40)
        self.original_proj_image = pygame.transform.scale(loaded_proj_image, size) # Store original
        self.proj_image = self.original_proj_image # Keep reference


    def update(self, player):
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance = math.hypot(dx, dy)

    # Déplacement vers le centre uniquement si nécessaire
        if distance > 5:
            self.x += (dx / distance) * self.speed
            self.y += (dy / distance) * self.speed
        else:
            self.shoot_cooldown = max(0, self.shoot_cooldown - 1)  # Décrémentation correcte du cooldown

            if self.shoot_cooldown == 0:  # Seulement si le cooldown est à 0

                shoot_type = random.randint(1, 100)
                if shoot_type <= 95:  # Rapidfire
                    dx = player.rect.centerx - self.x
                    dy = player.rect.centery - self.y
                    angle = math.atan2(-dy, dx)
                    self.projectiles.append({
                            'x': self.x,
                            'y': self.y,
                            'angle': angle,
                            'speed': 10,
                            'radius': 10})
                    self.shoot_cooldown = 20

                else:  # Bombe en cercle
                    for angle in range (0, 360, 20):
                        self.projectiles.append({
                            'x': self.x,
                            'y': self.y,
                            'angle': math.radians(angle),
                            'speed': 10,
                            'radius': 10}
                            )
                    self.shoot_cooldown = 180  #3sec

        # Update projectiles
        for proj in self.projectiles[:]:
            proj['x'] += proj['speed'] * math.cos(proj['angle'])
            proj['y'] -= proj['speed'] * math.sin(proj['angle'])

            # Hors de l'ecran
            if (proj['x'] < -50 or proj['x'] > WIDTH + 50 or
                proj['y'] < -50 or proj['y'] > HEIGHT + 50):
                self.projectiles.remove(proj)
                continue

            # collision au joueur
            if not player.invincible_time > 0:
                dist = math.hypot(player.rect.centerx - proj['x'],
                                player.rect.centery - proj['y'])
                if dist < proj['radius'] + 20:
                    damage = self.damage * (1 - player.shield / 100)
                    player.health -= damage
                    son_degat=pygame.mixer.Sound("sons/degat_joueur.mp3")
                    son_degat.play()
                    player.invincible_time = 60
                    self.projectiles.remove(proj)
                    continue  # Added to avoid checking second player for removed projectile

            # Vérifier la collision avec le second joueur en multijoueur
            if hasattr(self, 'second_player') and self.second_player and not self.second_player.invincible_time > 0:
                dist = math.hypot(self.second_player.rect.centerx - proj['x'],
                               self.second_player.rect.centery - proj['y'])
                if dist < proj['radius'] + 20:
                    damage = self.damage * (1 - self.second_player.shield / 100)
                    self.second_player.health -= damage
                    self.second_player.health = max(0, self.second_player.health)
                    self.second_player.invincible_time = 60
                    self.projectiles.remove(proj)
                    # Envoyer l'update au client (Server only)
                    if hasattr(self, 'p2p_comm') and self.p2p_comm and getattr(self.p2p_comm, 'est_serveur', False):
                        self.p2p_comm.envoyer_donnees({
                            'type': 'damage_update',
                            'player2_health': self.second_player.health,
                            'player2_invincible_time': self.second_player.invincible_time,
                            'player2_regen_rate': self.second_player.regen_rate,
                            'player2_max_health': self.second_player.max_health
                        })

    def draw(self, window):
        # Draw enemy
        super().draw(window)

        # Draw projectiles
        for proj in self.projectiles:
            angle = math.degrees(proj['angle'])
            rotated_proj_image = pygame.transform.rotate(self.original_proj_image, angle) # Adjust angle offset if needed
            new_rect = rotated_proj_image.get_rect(center=(int(proj['x']), int(proj['y'])))
            window.blit(rotated_proj_image, new_rect)

class Dash_Boss(Enemy):
    def __init__(self):
        super().__init__()
        self.radius = 110
        self.speed = 4
        self.health = 800
        self.maxhealth=800
        self.damage = 10
        self.color = YELLOW
        self.type= [Dash_Boss]
        self.bossname= "BERSERKER"
        self.angle = 0 # Initialize angle

        self.healthbar=True
        self.projectiles = []

        self.is_moving = False
        self.shooting = False
        self.action_timer = 0  # Timer pour l'action en cours

         # événements
        self.MOVE_EVENT = pygame.USEREVENT + 1
        self.STOP_EVENT = pygame.USEREVENT + 2
        self.SHOOT_EVENT = pygame.USEREVENT + 3

        # Load image
        image_path = 'images/boss_jaune.png'
        loaded_image = pygame.image.load(image_path).convert_alpha()
        size = (self.radius * 2, self.radius * 2)
        self.original_image = pygame.transform.scale(loaded_image, size) # Store original
        self.image = self.original_image # Keep reference

        loaded_proj_image = pygame.image.load('images/projectile_stun.png').convert_alpha()
        size = ( 80, 80)
        self.original_proj_image = pygame.transform.scale(loaded_proj_image, size) # Store original


    def move_towards_action(self, player):
        dx = player.rect.centerx - self.x
        dy = player.rect.centery - self.y
        distance = math.hypot(dx, dy)

        if distance <= player.range or self.is_on_screen():
            if distance != 0:
                dx_norm = dx / distance
                dy_norm = dy / distance
                self.x += dx_norm * self.speed
                self.y += dy_norm * self.speed

    def shoot_at_player(self, player):
        # Angle is already calculated in update
        self.projectiles.append({
                'x': self.x,
                'y': self.y,
                'angle': math.radians(self.angle), # Use pre-calculated angle
                'speed': 10,
                'radius': 50})
        son_stun = pygame.mixer.Sound("sons/stun.mp3")
        son_stun.play()

    def update(self, player):
        # Always calculate angle towards player
        dx_player = player.rect.centerx - self.x
        dy_player = player.rect.centery - self.y
        self.angle = math.degrees(math.atan2(-dy_player, dx_player))

        # Si il doit bouger
        if self.is_moving:
            self.move_towards_action(player)
        if self.shooting:
            self.shoot_at_player(player)
            self.shooting=False
    
    # Vérifier si le timer de l'action est 0
        if self.action_timer > 0:
            self.action_timer -= 1
        else:
        # Réinitialise l'action
            self.is_moving = False

        action = random.randint(0, 100)

        if action == 1:  # 1% de chances de suivre le joueur
            self.is_moving = True
            self.action_timer = 90  # 1.5 seconde

        elif action == 2:  # 1% de chances de tirer
            self.shooting = True
            self.action_timer = 120  # 2 secondes

        for proj in self.projectiles[:]:
            proj['x'] += proj['speed'] * math.cos(proj['angle'])
            proj['y'] -= proj['speed'] * math.sin(proj['angle'])

            # Hors de l'ecran
            if (proj['x'] < -50 or proj['x'] > WIDTH + 50 or
                proj['y'] < -50 or proj['y'] > HEIGHT + 50):
                if proj in self.projectiles: self.projectiles.remove(proj) # Safe remove
                continue

            # collision au joueur en ignorant sa periode d'invincibilité
            dist = math.hypot(player.rect.centerx - proj['x'],
                            player.rect.centery - proj['y'])
            if dist < proj['radius'] + 20:
                player.stun_timer=30
                player.velocite_bas=0
                player.velocite_gauche=0
                player.velocite_droite=0  
                player.velocite_haut=0 
                if proj in self.projectiles: self.projectiles.remove(proj) # Safe remove
                continue  # Added to avoid checking second player for removed projectile

            # Vérifier la collision avec le second joueur en multijoueur
            if hasattr(self, 'second_player') and self.second_player:
                dist = math.hypot(self.second_player.rect.centerx - proj['x'],
                               self.second_player.rect.centery - proj['y'])
                if dist < proj['radius'] + 20:
                    self.second_player.stun_timer = 120
                    if proj in self.projectiles: self.projectiles.remove(proj) # Safe remove
                    # Envoyer l'update au client (Server only)
                    if hasattr(self, 'p2p_comm') and self.p2p_comm and getattr(self.p2p_comm, 'est_serveur', False):
                        self.p2p_comm.envoyer_donnees({
                            'type': 'damage_update',
                            'player2_health': self.second_player.health,
                            'player2_invincible_time': 60, # Le Dash_Boss ne change pas la vie, mais on envoie l'invincibilité
                            'player2_stun_timer': self.second_player.stun_timer # Add stun timer
                        })
                    continue # Ensure we continue if projectile was removed

    def draw(self, window):
        # Rotate the original image for drawing
        rotated_image = pygame.transform.rotate(self.original_image, self.angle) # Adjust angle offset if needed
        new_rect = rotated_image.get_rect(center=(int(self.x), int(self.y)))
        window.blit(rotated_image, new_rect)
        # Draw health bar (logic copied from base class draw)
        if hasattr(self, 'healthbar') and self.healthbar and hasattr(self, 'maxhealth'):
            health_ratio = 0
            if self.maxhealth > 0: health_ratio = self.health / self.maxhealth
            else: health_ratio = 0 if self.health <= 0 else 1
            bar_width = 600; current_bar_width = int(bar_width * health_ratio)
            bar_x = WIDTH // 2 - bar_width // 2; bar_y = 20; bar_height = 20
            pygame.draw.rect(window, GRAY, (bar_x, bar_y, bar_width, bar_height))
            pygame.draw.rect(window, RED, (bar_x, bar_y, current_bar_width, bar_height))
            pygame.draw.rect(window, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)
            if hasattr(self, 'bossname'):
                bosstag = font.render(self.bossname, True, WHITE)
                tag_rect = bosstag.get_rect(center=(WIDTH // 2, bar_y + bar_height // 2))
                window.blit(bosstag, tag_rect)

        # Draw projectiles
        for proj in self.projectiles:
            new_rect = self.original_proj_image.get_rect(center=(int(proj['x']), int(proj['y'])))
            window.blit(self.original_proj_image, new_rect)

class Laser_Boss(Enemy):
    def __init__(self):
        super().__init__()
        self.radius = 140
        self.speed = 3
        self.health = 1000
        self.maxhealth=1000
        self.damage = 30
        self.color = BLUE
        self.type= [Laser_Boss]
        self.bossname= "TAZZZER"

        self.shoot_cooldown = 6
        self.projectiles = []

        self.target_x = random.randint(200,WIDTH-200)
        self.target_y = random.randint(200,HEIGHT-200)

        self.healthbar=True

        # Load image
        image_path = 'images/boss_laser.png' 

        loaded_image = pygame.image.load(image_path).convert_alpha()
        size = (self.radius * 2, self.radius * 2)
        self.image = pygame.transform.scale(loaded_image, size)

        loaded_proj_image = pygame.image.load('images/projectile_laser.png').convert_alpha()
        size = ( 50, 50)
        self.original_proj_image = pygame.transform.scale(loaded_proj_image, size) # Store original

    def update(self, player):
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance = math.hypot(dx, dy)

    # Déplacement vers le centre uniquement si nécessaire
        if distance > 5:
            self.x += (dx / distance) * self.speed
            self.y += (dy / distance) * self.speed
        else:
            self.shoot_cooldown = max(0, self.shoot_cooldown - 1)  # Décrémentation correcte du cooldown

            if self.shoot_cooldown == 0:  # Seulement si le cooldown est à 0

                shoot_type = random.randint(1, 100)
                if shoot_type <= 99:  # Rapidfire
                    dx = player.rect.centerx - self.x
                    dy = player.rect.centery - self.y
                    angle = math.atan2(-dy, dx)
                    self.projectiles.append({
                            'x': self.x,
                            'y': self.y,
                            'angle': angle,
                            'speed': 5,
                            'radius': 20,
                            'damage':5})
                    self.shoot_cooldown = 3

                else:  # Bombe en cercle
                    for i in range (10):
                        angle=random.randint(0,360)

                        self.projectiles.append({
                            'x': self.x,
                            'y': self.y,
                            'angle': math.radians(angle),
                            'speed': 4,
                            'radius': 30,
                            'damage':50}
                            )
                    self.shoot_cooldown = 240  #4sec

        # Update projectiles
        for proj in self.projectiles[:]:
            proj['x'] += proj['speed'] * math.cos(proj['angle'])
            proj['y'] -= proj['speed'] * math.sin(proj['angle'])

            # Hors de l'ecran
            if (proj['x'] < -50 or proj['x'] > WIDTH + 50 or
                proj['y'] < -50 or proj['y'] > HEIGHT + 50):
                self.projectiles.remove(proj)
                continue

            if proj['x'] <= 0 :
                proj['x'] = WIDTH-5
            if proj['x'] >= WIDTH :
                proj['x'] = 5             # Bounce off screen edges
            if proj['y'] <= 0 :
                proj['y'] = HEIGHT-5                 # Bounce off screen edges
            if proj['y'] >= HEIGHT :
                proj['y'] = 5

            # collision au joueur en ignorant sa periode d'invincibilité
            dist = math.hypot(player.rect.centerx - proj['x'],
                            player.rect.centery - proj['y'])
            if dist < proj['radius'] + 20:
                damage = proj['damage'] * (1 - player.shield / 100)
                player.health -= damage
                son_degat=pygame.mixer.Sound("sons/degat_joueur.mp3")
                son_degat.play()
                self.projectiles.remove(proj)
                continue

            # Vérifier la collision avec le second joueur en multijoueur
            if hasattr(self, 'second_player') and self.second_player:
                dist = math.hypot(self.second_player.rect.centerx - proj['x'],
                               self.second_player.rect.centery - proj['y'])
                if dist < proj['radius'] + 20:
                    damage = proj['damage'] * (1 - self.second_player.shield / 100)
                    self.second_player.health -= damage
                    self.second_player.health = max(0, self.second_player.health)
                    self.projectiles.remove(proj)
                    # Envoyer l'update au client (Server only)
                    if hasattr(self, 'p2p_comm') and self.p2p_comm and getattr(self.p2p_comm, 'est_serveur', False):
                        self.p2p_comm.envoyer_donnees({
                            'type': 'damage_update',
                            'player2_health': self.second_player.health,
                            'player2_invincible_time': 60 # Le laser boss ne stun pas, mais on envoie l'invincibilité
                        })
                    continue

            proj['radius']-=0.02
            if proj['radius']<8:
                self.projectiles.remove(proj)

    def draw(self, window):
        # Draw enemy
        super().draw(window)

        # Draw projectiles
        for proj in self.projectiles:
            new_rect = self.original_proj_image.get_rect(center=(int(proj['x']), int(proj['y'])))
            window.blit(self.original_proj_image, new_rect)

class Mothership_Boss(Enemy):

    def __init__(self):
        super().__init__()
        self.radius = 200
        self.speed = 3
        self.health = 3000 #test
        self.maxhealth=3000
        self.damage = 30
        self.color = (0,255,0)
        self.type= [Mothership_Boss]
        self.bossname= "MOTHERSHEEP"
        self.angle = 0 # Initialize angle

        self.shoot_cooldown = 180  # 3 seconds initial cooldown
        self.projectiles = []

        self.target_x = random.randint(200,WIDTH-200)
        self.target_y = random.randint(200,HEIGHT-200)

        self.healthbar=True

        # Counters for spawning minions
        self.spawn_cooldown = 600  # 10 seconds initial cooldown
        self.can_spawn_minions = True

        # Load image
        image_path = 'images/boss_final.png'

        loaded_image = pygame.image.load(image_path).convert_alpha()
        size = (self.radius * 2, self.radius * 2)
        self.original_image = pygame.transform.scale(loaded_image, size) # Store original
        self.image = self.original_image # Keep reference

        loaded_proj_image = pygame.image.load('images/projectile_boss2.png').convert_alpha()
        size = ( 80, 50)
        self.original_proj_image = pygame.transform.scale(loaded_proj_image, size) # Store original
        self.proj_image = self.original_proj_image # Keep reference

    def update(self, player):
        # Calculate angle towards player first
        dx_player = player.rect.centerx - self.x
        dy_player = player.rect.centery - self.y
        self.angle = math.degrees(math.atan2(-dy_player, dx_player))

        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance = math.hypot(dx, dy)

        # Déplacement vers le centre uniquement si nécessaire
        if distance > 5:
            self.x += (dx / distance) * self.speed
            self.y += (dy / distance) * self.speed
        else:
            # Possibly pick a new target position
            if random.random() < 0.01:  # 1% chance per frame
                self.target_x = random.randint(200, WIDTH-200)
                self.target_y = random.randint(200, HEIGHT-200)

            # Shooting logic
            self.shoot_cooldown = max(0, self.shoot_cooldown - 1)

            # Spawn minions periodically
            self.spawn_cooldown = max(0, self.spawn_cooldown - 1)

            # Shooting patterns based on health percentage
            if self.shoot_cooldown == 0:
                health_percent = self.health / self.maxhealth * 100

                # Different attack patterns based on health
                if health_percent < 30:  # Below 30% health - desperate mode
                    # Rapid fire at player (use calculated angle)
                    self.projectiles.append({
                        'x': self.x,
                        'y': self.y,
                        'angle': math.radians(self.angle), # Use calculated angle
                        'speed': 6,
                        'radius': 20,
                        'damage': 15
                    })
                    self.shoot_cooldown = 30  # Fast cooldown

                elif health_percent < 60:  # Below 60% health - aggressive mode
                    # Spiral pattern
                    for i in range(8):
                        # Spiral angle calculation needs careful review if it should target player
                        # This current logic is purely time-based spiral, not player-targeted
                        spiral_angle = math.radians(i * 45 + (pygame.time.get_ticks() % 360))
                        self.projectiles.append({
                            'x': self.x,
                            'y': self.y,
                            'angle': spiral_angle,
                            'speed': 5,
                            'radius': 20, # Increased radius
                            'damage': 10
                        })
                    self.shoot_cooldown = 120  # Medium cooldown

                else:  # Above 60% health - normal mode
                    # Target player with slower, bigger shots (use calculated angle)
                    self.projectiles.append({
                        'x': self.x,
                        'y': self.y,
                        'angle': math.radians(self.angle), # Use calculated angle
                        'speed': 4,
                        'radius': 25,
                        'damage': 20
                    })

                    # Add two spread shots
                    spread = 0.3  # ~15 degrees
                    self.projectiles.append({
                        'x': self.x,
                        'y': self.y,
                        'angle': math.radians(self.angle) + spread, # Add spread to calculated angle
                        'speed': 4,
                        'radius': 25,
                        'damage': 20
                    })
                    self.projectiles.append({
                        'x': self.x,
                        'y': self.y,
                        'angle': math.radians(self.angle) - spread, # Subtract spread from calculated angle
                        'speed': 4,
                        'radius': 25,
                        'damage': 20
                    })
                    self.shoot_cooldown = 180  # Slow cooldown

            # Spawn minions when cooldown reaches 0 and health is below 70%
            if self.spawn_cooldown == 0 and (self.health / self.maxhealth) < 0.7:
                self.spawn_minions(enemies)
                self.spawn_cooldown = 600  # Reset cooldown to 10 seconds

        # Update projectiles
        for proj in self.projectiles[:]:
            proj['x'] += proj['speed'] * math.cos(proj['angle'])
            proj['y'] -= proj['speed'] * math.sin(proj['angle'])

            # Hors de l'ecran
            if (proj['x'] < -50 or proj['x'] > WIDTH + 50 or
                proj['y'] < -50 or proj['y'] > HEIGHT + 50):
                if proj in self.projectiles: self.projectiles.remove(proj) # Safe remove
                continue

            # Bounce off screen edges
            if proj['x'] <= 0: proj['x'] = WIDTH-5
            if proj['x'] >= WIDTH: proj['x'] = 5
            if proj['y'] <= 0: proj['y'] = HEIGHT-5
            if proj['y'] >= HEIGHT: proj['y'] = 5

            # collision au joueur en ignorant sa periode d'invincibilité
            dist = math.hypot(player.rect.centerx - proj['x'],
                            player.rect.centery - proj['y'])
            if dist < proj['radius'] + 20:
                damage = proj['damage'] * (1 - player.shield / 100)
                player.health -= damage
                son_degat=pygame.mixer.Sound("sons/degat_joueur.mp3")
                son_degat.play()
                if proj in self.projectiles: self.projectiles.remove(proj) # Safe remove
                continue

            # Vérifier la collision avec le second joueur en multijoueur
            if hasattr(self, 'second_player') and self.second_player:
                dist = math.hypot(self.second_player.rect.centerx - proj['x'],
                               self.second_player.rect.centery - proj['y'])
                if dist < proj['radius'] + 20:
                    damage = proj['damage'] * (1 - self.second_player.shield / 100)
                    self.second_player.health -= damage
                    self.second_player.health = max(0, self.second_player.health)
                    if proj in self.projectiles: self.projectiles.remove(proj) # Safe remove
                    # Envoyer l'update au client (Server only)
                    if hasattr(self, 'p2p_comm') and self.p2p_comm and getattr(self.p2p_comm, 'est_serveur', False):
                        self.p2p_comm.envoyer_donnees({
                            'type': 'damage_update',
                            'player2_health': self.second_player.health,
                            'player2_invincible_time': 60 # Mothership boss does not stun
                        })
                    continue

            # Fade out projectiles over time
            proj['radius'] -= 0.015
            if proj['radius'] < 10:
                if proj in self.projectiles: self.projectiles.remove(proj) # Safe remove

    def spawn_minions(self, enemies_list):
        # Add 1-3 random enemies around the boss
        num_enemies = random.randint(1, 3)
        for _ in range(num_enemies):
            # Choose a random enemy type
            enemy_types = [BasicEnemy, ShooterEnemy, TankEnemy]
            enemy_class = random.choice(enemy_types)
            enemy = enemy_class()

            # Position the enemy near the boss with a random offset
            angle_rad = random.random() * math.pi * 2
            distance = self.radius + enemy.radius + 20  # Ensure they don't overlap
            enemy.x = self.x + math.cos(angle_rad) * distance
            enemy.y = self.y + math.sin(angle_rad) * distance

            # Add to the enemies list
            if 'enemies' in globals():
                globals()['enemies'].append(enemy)
            elif enemies_list is not None:
                enemies_list.append(enemy)

    def draw(self, window):
        # Rotate the original image for drawing
        rotated_image = pygame.transform.rotate(self.original_image, self.angle) # Adjust angle offset if needed
        new_rect = rotated_image.get_rect(center=(int(self.x), int(self.y)))
        window.blit(rotated_image, new_rect)
        # Draw health bar (logic copied from base class draw)
        if hasattr(self, 'healthbar') and self.healthbar and hasattr(self, 'maxhealth'):
            health_ratio = 0
            if self.maxhealth > 0: health_ratio = self.health / self.maxhealth
            else: health_ratio = 0 if self.health <= 0 else 1
            bar_width = 600; current_bar_width = int(bar_width * health_ratio)
            bar_x = WIDTH // 2 - bar_width // 2; bar_y = 20; bar_height = 20
            pygame.draw.rect(window, GRAY, (bar_x, bar_y, bar_width, bar_height))
            pygame.draw.rect(window, RED, (bar_x, bar_y, current_bar_width, bar_height))
            pygame.draw.rect(window, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)
            if hasattr(self, 'bossname'):
                bosstag = font.render(self.bossname, True, WHITE)
                tag_rect = bosstag.get_rect(center=(WIDTH // 2, bar_y + bar_height // 2))
                window.blit(bosstag, tag_rect)

        # Draw projectiles
        for proj in self.projectiles:
            angle = math.degrees(proj['angle'])
            rotated_proj_image = pygame.transform.rotate(self.original_proj_image, angle) # Adjust angle offset if needed
            new_rect = rotated_proj_image.get_rect(center=(int(proj['x']), int(proj['y'])))
            window.blit(rotated_proj_image, new_rect)
