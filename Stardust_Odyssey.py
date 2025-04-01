import pygame
import random
import math
import json

pygame.init()

# Paramètres de la fenêtre en plein écran
window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = window.get_size()
pygame.display.set_caption("Nova Drift Prototype - Fullscreen Mode")

# Couleurs
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
GOLD = (212,174,55)
GRAY = (128, 128, 128)
BLACK = (0, 0, 0)

selected_ship = "Vaisseau Basique"

# Police
font = pygame.font.Font(None, 36)

# Fonction pour sauvegarder les données
def save_data(credits, selected_skin, skins):
    with open("save_data.json", "w") as file:
        json.dump({
            "credits": credits,
            "selected_skin": selected_skin,
            "skins": skins  # Sauvegarder l'état de déverrouillage des skins
        }, file)

# Fonction pour charger les données
def load_data():

    try:
        with open("save_data.json", "r") as file:
            data = json.load(file)

             # Vérifier si selected_skin est bien un dictionnaire
            selected_skin = data.get("selected_skin", None)
            if isinstance(selected_skin, dict) and "preview_color" in selected_skin:
                selected_skin["preview_color"] = tuple(selected_skin["preview_color"])

            return (
                data.get("credits", 5000),  # Crédits par défaut           
                selected_skin,  # Skin sélectionné par défaut
                data.get("skins", [])  # Skins débloqués par défaut
                )
            
    except FileNotFoundError:
        return 5000, None, []  # Valeurs par défaut si le fichier n'existe pas           

class Button:
    def __init__(self, x, y, width, height, text, color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.is_hovered = False

    def draw(self, surface):
        color = tuple(max(0, min(255, c - 40)) for c in self.color) if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect)
        text_surface = font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered:
                return True
        return False

class Shop:
    def __init__(self):
        self.current_screen = "menu"
        self.current_tab = "skins"
        self.credits, self.selected_skin, unlocked_skins = load_data()  # Charger les crédits, le skin sélectionné et les skins débloqués
        self.pub_used = False

        self.grid_size = (4, 2)
        self.margin = 50
        self.padding = 20

        usable_width = WIDTH - (2 * self.margin)
        usable_height = HEIGHT - (2 * self.margin) - 100
        self.card_width = (usable_width - (self.grid_size[0] + 1) * self.padding) // self.grid_size[0]
        self.card_height = (usable_height - (self.grid_size[1] + 1) * self.padding) // self.grid_size[1]

        self.skins = [
            {"name": "Vaisseau Basique", "price": "gratuit", "unlocked": True, "preview_color": BLUE},
            {"name": "Vaisseau Doré", "price": 1000, "unlocked": False, "preview_color": GOLD},
            {"name": "Vaisseau Cristal", "price": 2000, "unlocked": False, "preview_color": (150, 200, 255)},
            {"name": "Vaisseau Pierre", "price": 30, "unlocked" : False, "preview_color": GRAY},
            {"name": "Vaisseau Plasma", "price": 50, "unlocked": False, "preview_color": (255, 100, 255)}, #unlock test x100prix
            {"name": "Vaisseau Emeraude", "price": 100,"unlocked":False,"preview_color": (0,255,50)},  #unlock test
            {"name": "Vaisseau Améthyste", "price": 120, "unlocked": False, "preview_color": (200,0,200)},
            {"name": "Vaisseau Diamant", "price": "PUB", "unlocked": False, "preview_color": (0,255,255)}
        ]

        # Appliquer les skins débloqués chargés depuis save_data.json
        for skin in self.skins:
            for unlocked_skin in unlocked_skins:
                if skin["name"] == unlocked_skin["name"]:
                    skin["unlocked"] = unlocked_skin["unlocked"]

        self.buttons = {
            "shop": Button(WIDTH // 2 - 100, HEIGHT // 2 - 25, 200, 50, "BOUTIQUE", BLUE),
            "play": Button(WIDTH // 2 - 100, HEIGHT // 2 + 50, 200, 50, "JOUER", GREEN),
            "back": Button(self.margin, self.margin, 100, 40, "RETOUR", GRAY),
            "quit": Button(WIDTH // 2 - 100, HEIGHT // 2 + 125, 200, 50,"QUITTER", RED ),
        }

    def draw_skin_preview(self, surface, skin, x, y):
        card_rect = pygame.Rect(x, y, self.card_width, self.card_height)
        pygame.draw.rect(surface, GRAY, card_rect, border_radius=10)

        preview_size = min(self.card_width, self.card_height) // 3
        preview_rect = pygame.Rect(x + (self.card_width - preview_size) // 2, y + 20, preview_size, preview_size)
        pygame.draw.rect(surface, (40, 40, 40), preview_rect)

        ship_surface = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.polygon(ship_surface, skin["preview_color"], [(15, 0), (0, 30), (30, 30)])
        ship_rect = ship_surface.get_rect(center=preview_rect.center)
        surface.blit(ship_surface, ship_rect)

        name_text = font.render(skin["name"], True, WHITE)
        surface.blit(name_text, (x + 10, y + preview_rect.bottom + 10))

        if skin["unlocked"]:
            button_text = "ÉQUIPÉ" if self.selected_skin == skin else "SÉLECTIONNER"
            button_color = GREEN if self.selected_skin == skin else BLUE
        else:
            button_text = "REGARDER PUB" if skin["price"] == "PUB" else f"{skin['price']} Crédits"
            button_color = RED if self.credits < (skin["price"] if isinstance(skin["price"], int) else 0) else YELLOW

        button_rect = pygame.Rect(x + 10, y + self.card_height - 40, self.card_width - 20, 30)
        pygame.draw.rect(surface, button_color, button_rect, border_radius=5)
        text_surface = font.render(button_text, True, WHITE)
        text_rect = text_surface.get_rect(center=button_rect.center)
        surface.blit(text_surface, text_rect)

    def handle_skin_selection(self, skin):
        if not skin["unlocked"]:
            if skin["price"] == "PUB" and not self.pub_used:
                self.pub_used = True
                skin["unlocked"] = True
            elif isinstance(skin["price"], int) and self.credits >= skin["price"]:
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

        credits_text = font.render(f"Crédits: {self.credits}", True, WHITE)
        surface.blit(credits_text, (WIDTH - 200, self.margin))

        for i, skin in enumerate(self.skins):
            row = i // self.grid_size[0]
            col = i % self.grid_size[0]
            x = self.margin + col * (self.card_width + self.padding)
            y = self.margin + 100 + row * (self.card_height + self.padding)
            self.draw_skin_preview(surface, skin, x, y)

    def run(self, screen):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if self.current_screen == "menu":
                    if self.buttons["shop"].handle_event(event):
                        self.current_screen = "shop"
                    elif self.buttons["play"].handle_event(event):
                        game_loop(self.selected_skin)
                    elif self.buttons["quit"].handle_event(event):
                        pygame.quit()

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

            if self.current_screen == "menu":
                screen.fill(BLACK)
                title = font.render("MENU PRINCIPAL", True, WHITE)
                screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 100))
                self.buttons["shop"].draw(screen)
                self.buttons["play"].draw(screen)
                self.buttons["quit"].draw(screen)

            elif self.current_screen == "shop":
                self.draw_shop_screen(screen)

            pygame.display.flip()


class Ship:
    def __init__(self, selected_skin="Vaisseau Basique"):
        self.image = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, BLUE, [(20, 0), (0, 40), (40, 40)])
        self.original_image = self.image
        self.rect = self.image.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.angle = 0
        self.bullets = []
        self.volicite_haut=0
        self.volicite_bas=0
        self.volicite_droite=0
        self.volicite_gauche=0
        

        # Stats base :
        self.speed = 5
        self.health = 100
        self.max_health = 100
        self.damage = 10
        self.range = 300

        self.bullet_speed = 10
        self.reload_speed = 1.0
        self.regen_rate = 0
        self.enemy_bounces = 0
        self.wall_bounces = 0
        self.bullet_piercing = 0
        self.parallel_shots = 1
        self.shield = 0
        self.bullet_size = 5
        self.explosion_radius = 0
        self.body_damage = 5
        self.last_shot_time = 0
        self.invincible_time = 0
        self.stun_timer=0

        self.forcefield_damage = 0
        self.forcefield_radius = 0
        self.last_forcefield_time = pygame.time.get_ticks()

        self.upgrades = []

    def move(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_z] and self.volicite_haut < 1 and self.stun_timer==0:  # Avancer
            self.volicite_haut += 0.02
        if keys[pygame.K_s] and self.volicite_bas < 1 and self.stun_timer==0:  # Reculer
            self.volicite_bas += 0.02     
        if keys[pygame.K_q] and self.volicite_gauche < 1 and self.stun_timer==0:  # Gauche
            self.volicite_gauche += 0.02           
        if keys[pygame.K_d] and self.volicite_droite < 1 and self.stun_timer==0:  # Droite
            self.volicite_droite += 0.02

        if self.volicite_haut > 0 :
                self.rect.y -= self.volicite_haut* self.speed
        if self.volicite_bas > 0 :
                self.rect.y += self.volicite_bas* self.speed
        if self.volicite_gauche > 0 :
                self.rect.x -= self.volicite_gauche* self.speed
        if self.volicite_droite > 0 :
                self.rect.x += self.volicite_droite* self.speed

        if self.volicite_haut > 0 and not keys[pygame.K_z]:
            self.volicite_haut -= 0.01
        if self.volicite_bas > 0 and not keys[pygame.K_s]:
            self.volicite_bas -= 0.01
        if self.volicite_gauche > 0 and not keys[pygame.K_q]:
            self.volicite_gauche -= 0.01
        if self.volicite_droite > 0 and not keys[pygame.K_d]:
            self.volicite_droite -= 0.01

        #TP de bord à bord de l'écran
        if self.rect.x <= 0 :
            self.rect.x = WIDTH-5
            self.health-=5
        if self.rect.x >= WIDTH :
            self.rect.x = 5
            self.health-=5
        if self.rect.y <= 0 :
            self.rect.y = HEIGHT-5
            self.health-=5
        if self.rect.y >= HEIGHT :
            self.rect.y = 5
            self.health-=5

    def rotate_to_mouse(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        dx, dy = mouse_x - self.rect.centerx, mouse_y - self.rect.centery
        self.angle = math.degrees(math.atan2(-dy, dx))
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)

    def shoot(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot_time < 500 / self.reload_speed:  # 500ms base cooldown
            return

        angle_rad = math.radians(self.angle)
        if self.parallel_shots == 1:
            bullet_x = self.rect.centerx + 20 * math.cos(angle_rad)
            bullet_y = self.rect.centery - 20 * math.sin(angle_rad)
            self.bullets.append(Bullet(bullet_x, bullet_y, angle_rad, self))
        else:
            spread = 15  # degrees between bullets
            for i in range(self.parallel_shots):
                offset = spread * (i - (self.parallel_shots - 1) / 2)
                bullet_angle = angle_rad + math.radians(offset)
                bullet_x = self.rect.centerx + 20 * math.cos(bullet_angle)
                bullet_y = self.rect.centery - 20 * math.sin(bullet_angle)
                self.bullets.append(Bullet(bullet_x, bullet_y, bullet_angle, self))

        self.last_shot_time = current_time

    def update(self, enemies):
        if self.health < self.max_health:
            self.health = min(self.max_health, self.health + self.regen_rate / 60)
        if self.invincible_time > 0:
            self.invincible_time -= 1

        # Update forcefield radius based on range
        self.forcefield_radius = 500-(400-self.range*0.2)

        # Apply forcefield damage
        if self.forcefield_damage > 0:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_forcefield_time >= 1000:  # Apply damage every second
                self.last_forcefield_time = current_time
                for enemy in enemies[:]:
                    distance = math.hypot(self.rect.centerx - enemy.x, self.rect.centery - enemy.y)
                    if distance <= self.forcefield_radius:
                        enemy.health -= self.forcefield_damage
                        if enemy.health <= 0:
                            enemies.remove(enemy)
        if self.stun_timer>0:
            self.stun_timer-=1
    def draw(self, window):
        # Draw forcefield if active
        if self.forcefield_damage > 0:
            # Draw multiple circles for forcefield effect
            alpha = 50
            for radius in [self.forcefield_radius - 20, self.forcefield_radius - 10, self.forcefield_radius]:
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

class VaisseauDore(Ship):
    def __init__(self):
        super().__init__()
        self.speed += 0.5
        self.health -= 50
        self.max_health -= 50
        self.range -+ 100
        pygame.draw.polygon(self.image, GOLD, [(20, 0), (0, 40), (40, 40)])

class VaisseauCristal(Ship):
    def __init__(self):
        super().__init__()
        self.speed -= 0.2
        self.health += 100
        self.max_health += 100
        self.damage += 5
        self.reload_speed -+ 0.4
        self.bullet_size += 2
        self.bullet_speed -= 5
        pygame.draw.polygon(self.image, (150, 200, 255), [(20, 0), (0, 40), (40, 40)])

class VaisseauPierre(Ship):
    def __init__(self):
        super().__init__()
        self.speed+=0.5
        self.health+=250
        self.max_health+=250
        self.regen_rate+=5
        self.body_damage=20
        self.damage=1    
        pygame.draw.polygon(self.image, (50, 20, 55), [(20, 0), (0, 40), (40, 40)])

class VaisseauPlasma(Ship):
    def __init__(self):
        super().__init__()
        self.speed -= 0.1
        self.bullet_piercing += 3
        self.damage += 10
        self.bullet_speed +=10
        self.reload_speed -= 0.8
        pygame.draw.polygon(self.image, (255, 100, 255), [(20, 0), (0, 40), (40, 40)])

class VaisseauEmeraude(Ship) :
    def __init__(self):
        super().__init__()
        self.health-=30
        self.max_health-+30
        self.wall_bounces+=3
        self.range+=2700
        self.speed-=0.4
        pygame.draw.polygon(self.image, (15, 250, 30), [(20, 0), (0, 40), (40, 40)])

class VaisseauAmethyste(Ship):
    def __init__(self):
        super().__init__()
        self.health-=50
        self.max_health-=50
        self.speed+=1
        self.bullet_speed+=5
        self.reload_speed+=0.5
        self.damage-=2
        pygame.draw.polygon(self.image, (250, 15, 255), [(20, 0), (0, 40), (40, 40)])

class VaisseauDiamant(Ship):
    def __init__(self):
        super().__init__()
        self.health += 50
        self.max_health += 50
        self.speed += 1.2
        self.damage += 80
        self.explosion_radius += 300
        pygame.draw.polygon(self.image, (0, 255, 255), [(20, 0), (0, 40), (40, 40)])


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
        # Explosion animation
        self.is_exploding = False
        self.explosion_time = 30  # frames
        self.explosion_alpha = 255

    def move(self):
        dx = self.speed * math.cos(self.angle)
        dy = self.speed * math.sin(self.angle)
        self.x += dx
        self.y -= dy  # Use negative dy to match mouse coordinates
        self.distance_traveled += math.hypot(dx, dy)

    def draw(self, window):
        # Draw bullet
        color = WHITE
        pygame.draw.circle(window, color, (int(self.x), int(self.y)), self.radius)

    def explode(self, enemies):
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

class Enemy:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.health = 0
        self.damage = 0
        self.radius = 0
        self.speed = 0
        self.color = WHITE

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
        pygame.draw.circle(window, self.color, (int(self.x), int(self.y)), self.radius)

    def check_collision(self, player):
        if player.invincible_time > 0:
            return False

        distance = math.hypot(player.rect.centerx - self.x, player.rect.centery - self.y)
        if distance < self.radius + 20:
            # degats - shield
            damage_to_player = self.damage * (1 - player.shield / 100)
            player.health -= damage_to_player
            player.invincible_time = 60
        
             # degats autour de lui
            for enemy in enemies[:]:
                distance = math.hypot(self.x - enemy.x, self.y - enemy.y)
                if distance <= 100:
                    enemy.health -= player.body_damage  # Half damage for explosion
                    if enemy.health <= 0:
                        enemies.remove(enemy)

            explosion_surface = pygame.Surface((200,200), pygame.SRCALPHA)

            pygame.draw.circle(explosion_surface, (100, 200, 255,30),
                            (player.explosion_radius, player.explosion_radius),
                                    player.explosion_radius, 2)
            window.blit(explosion_surface,
                       (int(self.x - player.explosion_radius),
                        int(self.y - player.explosion_radius)))



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

        self.healthbar=False

    def move_towards(self, player):
        dx = player.rect.centerx - self.x
        dy = player.rect.centery - self.y
        distance = math.hypot(dx, dy)

        if distance <= player.range or self.is_on_screen():
            if distance != 0:
                dx = dx / distance * self.speed
                dy = dy / distance * self.speed
                self.x += dx
                self.y += dy

    def update(self, player):
        self.move_towards(player)

class TankEnemy(Enemy):
    def __init__(self):
        super().__init__()
        self.radius = 30
        self.speed = 1
        self.health = 40
        self.damage = 20
        self.color = YELLOW
        self.type= [TankEnemy]

        self.healthbar=False

    def move_towards(self, player):
        dx = player.rect.centerx - self.x
        dy = player.rect.centery - self.y
        distance = math.hypot(dx, dy)

        if distance <= player.range or self.is_on_screen():
            if distance != 0:
                dx = dx / distance * self.speed
                dy = dy / distance * self.speed
                self.x += dx
                self.y += dy

    def update(self, player):
        self.move_towards(player)

class ShooterEnemy(Enemy):
    def __init__(self):
        super().__init__()
        self.radius = 25
        self.speed = 3
        self.health = 30
        self.damage = 15
        self.color = GREEN
        self.type= [ShooterEnemy]

        self.shoot_cooldown = 0
        self.shoot_delay = random.randint(60, 120)
        self.projectiles = []
    
        self.target_x = 0
        self.target_y = 0
        self.stationary_time = 300  
        self.stationary_timer = 0
        self.is_moving = True
        self.pick_new_position()

        self.healthbar=False

    def pick_new_position(self):
        margin = 100
        self.target_x = random.randint(margin, WIDTH - margin)
        self.target_y = random.randint(margin, HEIGHT - margin)

    def update(self, player):
        if self.is_moving:
            dx = self.target_x - self.x
            dy = self.target_y - self.y
            distance = math.hypot(dx, dy)

            if distance < self.speed:  # est au point aleatoire
                self.x = self.target_x
                self.y = self.target_y
                self.is_moving = False
                self.stationary_timer = self.stationary_time
            else: #va au point aleatoire

                self.x += (dx / distance) * self.speed
                self.y += (dy / distance) * self.speed
        else:

            self.stationary_timer -= 1
            if self.stationary_timer <= 0:
                self.is_moving = True
                self.pick_new_position()
            else:
                # Only shoot when stationary
                self.shoot_cooldown = max(0, self.shoot_cooldown - 1)
                if self.shoot_cooldown == 0:
                    dx = player.rect.centerx - self.x
                    dy = player.rect.centery - self.y
                    angle = math.atan2(-dy, dx)

                    self.projectiles.append({
                        'x': self.x,
                        'y': self.y,
                        'angle': angle,
                        'speed': 5,
                        'radius': 5
                    })
                    self.shoot_cooldown = self.shoot_delay

        # Update projectiles
        for proj in self.projectiles[:]:
            proj['x'] += proj['speed'] * math.cos(proj['angle'])
            proj['y'] -= proj['speed'] * math.sin(proj['angle'])

            # hors de l'ecran
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
                    player.invincible_time = 60
                    self.projectiles.remove(proj)

    def draw(self, window):
        # Draw enemy
        super().draw(window)

        # Draw projectiles
        for proj in self.projectiles:
            pygame.draw.circle(window, RED,
                             (int(proj['x']), int(proj['y'])),
                             proj['radius'])

class LinkEnemy(Enemy):
    def __init__(self):
        super().__init__()
        self.radius = 50
        self.speed=1
        self.health=100
        self.damage=20
        self.color = WHITE
        self.type= [LinkEnemy]

        self.projectiles = []

        # Movement attributes
        self.target_x = 0
        self.target_y = 0
        self.stationary_time = 150 
        self.stationary_timer = 0
        self.is_moving = True
        self.pick_new_position()

        self.healthbar=False

    def pick_new_position(self):
        margin = 100
        self.target_x = random.randint(margin, WIDTH - margin)
        self.target_y = random.randint(margin, HEIGHT - margin)

    def update(self, player):
        if self.is_moving:
            dx = self.target_x - self.x
            dy = self.target_y - self.y
            distance = math.hypot(dx, dy)

            if distance < self.speed:  # est au point aleatoire
                self.x = self.target_x
                self.y = self.target_y
                self.is_moving = False
                self.stationary_timer = self.stationary_time
            else:
                # Va au point aleatoire
                self.x += (dx / distance) * self.speed
                self.y += (dy / distance) * self.speed
                
        else:
            self.stationary_timer -= 1
            if self.stationary_timer <= 0:
                self.is_moving = True
                self.pick_new_position()

                           

    def draw(self, window):
        super().draw(window)

        # laser                  
        for other in enemies :
            if other.type == [LinkEnemy] :
                pygame.draw.line(window, (230,200,200),(self.x ,self.y ),(other.x,other.y),width=20)

class Tank_Boss(Enemy):
    def __init__(self):
        super().__init__()
        self.radius = 100
        self.speed = 3
        self.health = 600
        self.maxhealth=600
        self.damage = 5
        self.color = RED
        self.type= [Tank_Boss]
        self.bossname= "BEHEMOTH"

        self.shoot_cooldown = 18
        self.projectiles = []
    
        self.target_x = WIDTH//2
        self.target_y = HEIGHT//2
        
        self.healthbar=True

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
                    player.invincible_time = 60
                    self.projectiles.remove(proj)
        

    
    def draw(self, window):
        # Draw enemy
        super().draw(window)

        # Draw projectiles
        for proj in self.projectiles:
            pygame.draw.circle(window, RED, (int(proj['x']), int(proj['y'])), proj['radius'])
            print(f"Projectile dessiné à ({proj['x']}, {proj['y']})")  # DEBUG


class Dash_Boss(Enemy):
    def __init__(self):
        super().__init__()
        self.radius = 110
        self.speed = 4
        self.health = 800
        self.maxhealth=800
        self.damage = 50
        self.color = YELLOW
        self.type= [Dash_Boss]
        self.bossname= "BERSERKER"

        self.healthbar=True
        self.projectiles = []

        self.is_moving = False
        self.shooting = False
        self.action_timer = 0  # Timer pour l'action en cours

         # événements
        self.MOVE_EVENT = pygame.USEREVENT + 1
        self.STOP_EVENT = pygame.USEREVENT + 2
        self.SHOOT_EVENT = pygame.USEREVENT + 3

    def move_towards_action(self, player):
        dx = player.rect.centerx - self.x
        dy = player.rect.centery - self.y
        distance = math.hypot(dx, dy)

        if distance <= player.range or self.is_on_screen():
            if distance != 0:
                dx = dx / distance * self.speed
                dy = dy / distance * self.speed
                self.x += dx
                self.y += dy

    def shoot_at_player(self, player):
        dx = player.rect.centerx - self.x
        dy = player.rect.centery - self.y
        angle = math.atan2(-dy, dx)
        self.projectiles.append({
                'x': self.x,
                'y': self.y,
                'angle': angle,
                'speed': 10,
                'radius': 50})

    def update(self, player):
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
                self.projectiles.remove(proj)
                continue

            # collision au joueur en ignorant sa periode d'invincibilité
            dist = math.hypot(player.rect.centerx - proj['x'],
                            player.rect.centery - proj['y'])
            if dist < proj['radius'] + 20:
                player.stun_timer=120
                self.projectiles.remove(proj)


    def draw(self, window):
        # Draw enemy
        super().draw(window)

        # Draw projectiles
        for proj in self.projectiles:
            pygame.draw.circle(window, RED, (int(proj['x']), int(proj['y'])), proj['radius'])
        

    

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
                proj['x'] = 5            
            if proj['y'] <= 0 :
                proj['y'] = HEIGHT-5                
            if proj['y'] >= HEIGHT :
                proj['y'] = 5
                

            # collision au joueur en ignorant sa periode d'invincibilité
            dist = math.hypot(player.rect.centerx - proj['x'],
                            player.rect.centery - proj['y'])
            if dist < proj['radius'] + 20:
                damage = proj['damage'] * (1 - player.shield / 100)
                player.health -= damage
                self.projectiles.remove(proj)
        

    
    def draw(self, window):
        # Draw enemy
        super().draw(window)

        # Draw projectiles
        for proj in self.projectiles:
            pygame.draw.circle(window, RED, (int(proj['x']), int(proj['y'])), proj['radius'])

class Mothership_Boss(Enemy) :
    pass


def spawn_wave(wave_number):
    enemies = []
    cycle=1 + wave_number//20
    cycle_wave=wave_number%20
    num_enemies = cycle_wave + 3*cycle



    if cycle_wave < 5 :
        types = [BasicEnemy] * 70 + [TankEnemy] * 30
    elif cycle_wave < 10:
        types = [BasicEnemy] * 50 + [TankEnemy] * 25 + [ShooterEnemy] * 25
    elif cycle_wave < 15 :
        types = [BasicEnemy] * 30 + [TankEnemy] * 25 + [ShooterEnemy] * 25 + [LinkEnemy] * 20

    if cycle_wave == 5 :
        enemies.append(Tank_Boss())
        return enemies,cycle
    elif cycle_wave == 10 :
        enemies.append(Laser_Boss())
        return enemies,cycle
    elif cycle_wave == 15:
        enemies.append(Dash_Boss())
        return enemies,cycle
    elif cycle_wave == 20 :
        enemies.append(Mothership_Boss())
        return enemies,cycle
        #else wave 20 donc boss final
    else:
        for i in range(num_enemies):
            enemy_class = random.choice(types)
            enemies.append(enemy_class())
        return enemies,cycle




def shop_upgrades(player):
    all_upgrades = [
        {"name": "Health Up", "effect": "Max Health +20","niveau":1,
         "apply": lambda p: setattr(p, "max_health", p.max_health + 20)},
        {"name": "Health Up", "effect": "Max Health +20","niveau":2,
         "apply": lambda p: setattr(p, "max_health", p.max_health + 20)}, 
        {"name": "Health Up", "effect": "Max Health +20","niveau":3,
         "apply": lambda p: setattr(p, "max_health", p.max_health + 20)},
        {"name": "Health Up", "effect": "Max Health +20","niveau":4,
         "apply": lambda p: setattr(p, "max_health", p.max_health + 20)},
        {"name": "Health Up", "effect": "Max Health +20","niveau":5,
         "apply": lambda p: setattr(p, "max_health", p.max_health + 20)},

        {"name": "Damage Up", "effect": "Bullet Damage +5","niveau":1,
         "apply": lambda p: setattr(p, "damage", p.damage + 5)},
        {"name": "Damage Up", "effect": "Bullet Damage +5","niveau":2,
         "apply": lambda p: setattr(p, "damage", p.damage + 5)},
        {"name": "Damage Up", "effect": "Bullet Damage +5","niveau":3,
         "apply": lambda p: setattr(p, "damage", p.damage + 5)},
        {"name": "Damage Up", "effect": "Bullet Damage +5","niveau":4,
         "apply": lambda p: setattr(p, "damage", p.damage + 5)},
        {"name": "Damage Up", "effect": "Bullet Damage +5","niveau":5,
         "apply": lambda p: setattr(p, "damage", p.damage + 5)},

        {"name": "Bullet Speed", "effect": "Bullet Speed +2","niveau":1,
         "apply": lambda p: setattr(p, "bullet_speed", p.bullet_speed + 2)},         
        {"name": "Bullet Speed", "effect": "Bullet Speed +2","niveau":2,
         "apply": lambda p: setattr(p, "bullet_speed", p.bullet_speed + 2)},
        {"name": "Bullet Speed", "effect": "Bullet Speed +2","niveau":3,
         "apply": lambda p: setattr(p, "bullet_speed", p.bullet_speed + 2)},
        {"name": "Bullet Speed", "effect": "Bullet Speed +2","niveau":4,
         "apply": lambda p: setattr(p, "bullet_speed", p.bullet_speed + 2)},
        {"name": "Bullet Speed", "effect": "Bullet Speed +2","niveau":5,
         "apply": lambda p: setattr(p, "bullet_speed", p.bullet_speed + 2)},

        {"name": "Reload Speed", "effect": "Reload Speed +20%","niveau":1,
         "apply": lambda p: setattr(p, "reload_speed", p.reload_speed + 0.2)},
        {"name": "Reload Speed", "effect": "Reload Speed +20%","niveau":2,
         "apply": lambda p: setattr(p, "reload_speed", p.reload_speed + 0.2)},
        {"name": "Reload Speed", "effect": "Reload Speed +20%","niveau":3,
         "apply": lambda p: setattr(p, "reload_speed", p.reload_speed + 0.2)},
        {"name": "Reload Speed", "effect": "Reload Speed +20%","niveau":4,
         "apply": lambda p: setattr(p, "reload_speed", p.reload_speed + 0.2)},
        {"name": "Reload Speed", "effect": "Reload Speed +20%","niveau":5,
         "apply": lambda p: setattr(p, "reload_speed", p.reload_speed + 0.2)},


        {"name": "Regeneration", "effect": "Health Regen +0.5/s","niveau":1,
         "apply": lambda p: setattr(p, "regen_rate", p.regen_rate + 0.5)},
        {"name": "Regeneration", "effect": "Health Regen +0.5/s","niveau":2,
         "apply": lambda p: setattr(p, "regen_rate", p.regen_rate + 0.5)},
        {"name": "Regeneration", "effect": "Health Regen +0.5/s","niveau":3,
         "apply": lambda p: setattr(p, "regen_rate", p.regen_rate + 0.5)},
        {"name": "Regeneration", "effect": "Health Regen +0.5/s","niveau":4,
         "apply": lambda p: setattr(p, "regen_rate", p.regen_rate + 0.5)},
        {"name": "Regeneration", "effect": "Health Regen +0.5/s","niveau":5,
         "apply": lambda p: setattr(p, "regen_rate", p.regen_rate + 0.5)},


        {"name": "Enemy Bounce", "effect": "Enemy Bounces +1","niveau":1,
         "apply": lambda p: setattr(p, "enemy_bounces", p.enemy_bounces + 1)},
        {"name": "Enemy Bounce", "effect": "Enemy Bounces +1","niveau":2,
         "apply": lambda p: setattr(p, "enemy_bounces", p.enemy_bounces + 1)},
        {"name": "Enemy Bounce", "effect": "Enemy Bounces +1","niveau":3,
         "apply": lambda p: setattr(p, "enemy_bounces", p.enemy_bounces + 1)},
        {"name": "Enemy Bounce", "effect": "Enemy Bounces +1","niveau":4,
         "apply": lambda p: setattr(p, "enemy_bounces", p.enemy_bounces + 1)},
        {"name": "Enemy Bounce", "effect": "Enemy Bounces +1","niveau":5,
         "apply": lambda p: setattr(p, "enemy_bounces", p.enemy_bounces + 1)},


        {"name": "Wall Bounce", "effect": "Wall Bounces +1","niveau":1,
         "apply": lambda p: setattr(p, "wall_bounces", p.wall_bounces + 1)},
        {"name": "Wall Bounce", "effect": "Wall Bounces +1","niveau":2,
         "apply": lambda p: setattr(p, "wall_bounces", p.wall_bounces + 1)},
        {"name": "Wall Bounce", "effect": "Wall Bounces +1","niveau":3,
         "apply": lambda p: setattr(p, "wall_bounces", p.wall_bounces + 1)},
        {"name": "Wall Bounce", "effect": "Wall Bounces +1","niveau":4,
         "apply": lambda p: setattr(p, "wall_bounces", p.wall_bounces + 1)},
        {"name": "Wall Bounce", "effect": "Wall Bounces +1","niveau":5,
         "apply": lambda p: setattr(p, "wall_bounces", p.wall_bounces + 1)},


        {"name": "Piercing", "effect": "Bullet Piercing +1","niveau":1,
         "apply": lambda p: setattr(p, "bullet_piercing", p.bullet_piercing + 1)},
        {"name": "Piercing", "effect": "Bullet Piercing +1","niveau":2,
         "apply": lambda p: setattr(p, "bullet_piercing", p.bullet_piercing + 1)},
        {"name": "Piercing", "effect": "Bullet Piercing +1","niveau":3,
         "apply": lambda p: setattr(p, "bullet_piercing", p.bullet_piercing + 1)},
        {"name": "Piercing", "effect": "Bullet Piercing +1","niveau":4,
         "apply": lambda p: setattr(p, "bullet_piercing", p.bullet_piercing + 1)},
        {"name": "Piercing", "effect": "Bullet Piercing +1","niveau":5,
         "apply": lambda p: setattr(p, "bullet_piercing", p.bullet_piercing + 1)},


        {"name": "Multi Shot", "effect": "Parallel Shots +1","niveau":1,
         "apply": lambda p: setattr(p, "parallel_shots", p.parallel_shots + 1)},
        {"name": "Multi Shot", "effect": "Parallel Shots +1","niveau":2,
         "apply": lambda p: setattr(p, "parallel_shots", p.parallel_shots + 1)},
        {"name": "Multi Shot", "effect": "Parallel Shots +1","niveau":3,
         "apply": lambda p: setattr(p, "parallel_shots", p.parallel_shots + 1)},
        {"name": "Multi Shot", "effect": "Parallel Shots +1","niveau":4,
         "apply": lambda p: setattr(p, "parallel_shots", p.parallel_shots + 1)},
        {"name": "Multi Shot", "effect": "Parallel Shots +1","niveau":5,
         "apply": lambda p: setattr(p, "parallel_shots", p.parallel_shots + 1)},


        {"name": "Shield", "effect": "Damage Reduction +5%","niveau":1,
         "apply": lambda p: setattr(p, "shield", min(75, p.shield + 5))},
        {"name": "Shield", "effect": "Damage Reduction +5%","niveau":2,
         "apply": lambda p: setattr(p, "shield", min(75, p.shield + 5))},
        {"name": "Shield", "effect": "Damage Reduction +5%","niveau":3,
         "apply": lambda p: setattr(p, "shield", min(75, p.shield + 5))},
        {"name": "Shield", "effect": "Damage Reduction +5%","niveau":4,
         "apply": lambda p: setattr(p, "shield", min(75, p.shield + 5))},
        {"name": "Shield", "effect": "Damage Reduction +5%","niveau":5,
         "apply": lambda p: setattr(p, "shield", min(75, p.shield + 5))},


        {"name": "Bullet Size", "effect": "Bullet Size +2","niveau":1,
         "apply": lambda p: setattr(p, "bullet_size", p.bullet_size + 2)},
        {"name": "Bullet Size", "effect": "Bullet Size +2","niveau":2,
         "apply": lambda p: setattr(p, "bullet_size", p.bullet_size + 2)},
        {"name": "Bullet Size", "effect": "Bullet Size +2","niveau":3,
         "apply": lambda p: setattr(p, "bullet_size", p.bullet_size + 2)},
        {"name": "Bullet Size", "effect": "Bullet Size +2","niveau":4,
         "apply": lambda p: setattr(p, "bullet_size", p.bullet_size + 2)},
        {"name": "Bullet Size", "effect": "Bullet Size +2","niveau":5,
         "apply": lambda p: setattr(p, "bullet_size", p.bullet_size + 2)},


        {"name": "Explosion", "effect": "Explosion Radius +10","niveau":1,
         "apply": lambda p: setattr(p, "explosion_radius", p.explosion_radius + 80 if p.explosion_radius==0 else p.explosion_radius + 20) },
        {"name": "Explosion", "effect": "Explosion Radius +10","niveau":2,
         "apply": lambda p: setattr(p, "explosion_radius", p.explosion_radius + 80 if p.explosion_radius==0 else p.explosion_radius + 20) },
        {"name": "Explosion", "effect": "Explosion Radius +10","niveau":3,
         "apply": lambda p: setattr(p, "explosion_radius", p.explosion_radius + 80 if p.explosion_radius==0 else p.explosion_radius + 20) },
        {"name": "Explosion", "effect": "Explosion Radius +10","niveau":4,
         "apply": lambda p: setattr(p, "explosion_radius", p.explosion_radius + 80 if p.explosion_radius==0 else p.explosion_radius + 20) },
        {"name": "Explosion", "effect": "Explosion Radius +10","niveau":5,
         "apply": lambda p: setattr(p, "explosion_radius", p.explosion_radius + 80 if p.explosion_radius==0 else p.explosion_radius + 20) },


        {"name": "Range Up", "effect": "Bullet Range +100","niveau":1,
         "apply": lambda p: setattr(p, "range", p.range + 100)},
        {"name": "Range Up", "effect": "Bullet Range +100","niveau":2,
         "apply": lambda p: setattr(p, "range", p.range + 100)},
        {"name": "Range Up", "effect": "Bullet Range +100","niveau":3,
         "apply": lambda p: setattr(p, "range", p.range + 100)},
        {"name": "Range Up", "effect": "Bullet Range +100","niveau":4,
         "apply": lambda p: setattr(p, "range", p.range + 100)},
        {"name": "Range Up", "effect": "Bullet Range +100","niveau":5,
         "apply": lambda p: setattr(p, "range", p.range + 100)},


        {"name": "Body Damage", "effect": "Body Damage +5","niveau":1,
         "apply": lambda p: setattr(p, "body_damage", p.body_damage + 5)},         
        {"name": "Body Damage", "effect": "Body Damage +5","niveau":2,
         "apply": lambda p: setattr(p, "body_damage", p.body_damage + 5)},         
        {"name": "Body Damage", "effect": "Body Damage +5","niveau":3,
         "apply": lambda p: setattr(p, "body_damage", p.body_damage + 5)},
        {"name": "Body Damage", "effect": "Body Damage +5","niveau":4,
         "apply": lambda p: setattr(p, "body_damage", p.body_damage + 5)},
        {"name": "Body Damage", "effect": "Body Damage +5","niveau":5,
         "apply": lambda p: setattr(p, "body_damage", p.body_damage + 5)},


        {"name": "Forcefield", "effect": "Forcefield Damage +2/s","niveau":1,
         "apply": lambda p: setattr(p, "forcefield_damage", p.forcefield_damage + 2)},
        {"name": "Forcefield", "effect": "Forcefield Damage +2/s","niveau":2,
         "apply": lambda p: setattr(p, "forcefield_damage", p.forcefield_damage + 2)},
        {"name": "Forcefield", "effect": "Forcefield Damage +2/s","niveau":3,
         "apply": lambda p: setattr(p, "forcefield_damage", p.forcefield_damage + 2)},
        {"name": "Forcefield", "effect": "Forcefield Damage +2/s","niveau":4,
         "apply": lambda p: setattr(p, "forcefield_damage", p.forcefield_damage + 2)},
        {"name": "Forcefield", "effect": "Forcefield Damage +2/s","niveau":5,
         "apply": lambda p: setattr(p, "forcefield_damage", p.forcefield_damage + 2)},


        {"name": "Decoy", "effect": "Double Attack Speed, Half Damage","niveau":1,
         "apply": lambda p: [setattr(p, "reload_speed", p.reload_speed * 2), setattr(p, "damage", p.damage / 2)]},
        {"name": "Decoy", "effect": "Double Attack Speed, Half Damage","niveau":2,
         "apply": lambda p: [setattr(p, "reload_speed", p.reload_speed * 2), setattr(p, "damage", p.damage / 2)]},
        {"name": "Decoy", "effect": "Double Attack Speed, Half Damage","niveau":3,
         "apply": lambda p: [setattr(p, "reload_speed", p.reload_speed * 2), setattr(p, "damage", p.damage / 2)]},
        {"name": "Decoy", "effect": "Double Attack Speed, Half Damage","niveau":4,
         "apply": lambda p: [setattr(p, "reload_speed", p.reload_speed * 2), setattr(p, "damage", p.damage / 2)]},
        {"name": "Decoy", "effect": "Double Attack Speed, Half Damage","niveau":5,
         "apply": lambda p: [setattr(p, "reload_speed", p.reload_speed * 2), setattr(p, "damage", p.damage / 2)]},


        {"name": "Berserker", "effect": "Damage scales with missing health","niveau":1,
         "apply": lambda p: setattr(p, "damage", p.damage + (p.max_health - p.health) / 10)},         
        {"name": "Berserker", "effect": "Damage scales with missing health","niveau":2,
         "apply": lambda p: setattr(p, "damage", p.damage + (p.max_health - p.health) / 10)},         
        {"name": "Berserker", "effect": "Damage scales with missing health","niveau":3,
         "apply": lambda p: setattr(p, "damage", p.damage + (p.max_health - p.health) / 10)},
        {"name": "Berserker", "effect": "Damage scales with missing health","niveau":4,
         "apply": lambda p: setattr(p, "damage", p.damage + (p.max_health - p.health) / 10)},
        {"name": "Berserker", "effect": "Damage scales with missing health","niveau":5,
         "apply": lambda p: setattr(p, "damage", p.damage + (p.max_health - p.health) / 10)},
         

        {"name": "Speed", "effect": "FASTER","niveau":1,
         "apply": lambda p: setattr(p, "speed", p.speed + p.speed*0.1)},         
        {"name": "Speed", "effect": "FASTER","niveau":2,
         "apply": lambda p: setattr(p, "speed", p.speed + p.speed*0.1)},     
        {"name": "Speed", "effect": "FASTER","niveau":3,
         "apply": lambda p: setattr(p, "speed", p.speed + p.speed*0.1)},
        {"name": "Speed", "effect": "FASTER","niveau":4,
         "apply": lambda p: setattr(p, "speed", p.speed + p.speed*0.1)},
        {"name": "Speed", "effect": "FASTER","niveau":5,
         "apply": lambda p: setattr(p, "speed", p.speed + p.speed*0.1)}


    ]

    shop_upgrades = random.sample(all_upgrades, 3)

    font = pygame.font.Font(None, 36)
    running = True
    selected = None

    while running:
        window.fill((0, 0, 0))

        title = font.render("Choose an Upgrade", True, WHITE)
        window.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 4))

        for i, upgrade in enumerate(shop_upgrades):

            rect = pygame.Rect(i * 500 + WIDTH//19, HEIGHT//5,WIDTH//4, HEIGHT//1.5)
            color = YELLOW if selected == i else WHITE
            pygame.draw.rect(window, color, rect, 2)

            text = font.render(f"{i+1}. {upgrade['name']} - {upgrade['effect']}", True, color)
            window.blit(text, (rect.x + 10, rect.y + 10))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_1, pygame.K_2, pygame.K_3]:
                    selected = event.key - pygame.K_1
                    if 0 <= selected < len(shop_upgrades):
                        upgrade = shop_upgrades[selected]
                        upgrade["apply"](player)
                        running = False
                        return True

    return True

def game_loop(selected_skin):
    global enemies
    player_ship = Ship(selected_skin)
    enemies,cycle = spawn_wave(1)  # lance la vague 1
    wave_number = 1
    score = 0
    credits_earned = 0  # Crédits gagnés pendant cette partie
    running = True
    font = pygame.font.Font(None, 36)
    wave_text_timer = 0

    for enemy in enemies :
        enemy.health = int(enemy.health * cycle ** 1.5)
        enemy.damage = enemy.damage * cycle

    if selected_skin["name"] == "Vaisseau Doré":
        player_ship = VaisseauDore()
    elif selected_skin["name"] == "Vaisseau Cristal":
        player_ship = VaisseauCristal()
    elif selected_skin["name"] == "Vaisseau Pierre" :
        player_ship= VaisseauPierre()
    elif selected_skin["name"] == "Vaisseau Plasma":
        player_ship = VaisseauPlasma()
    elif selected_skin["name"] == "Vaisseau Emeraude":
        player_ship = VaisseauEmeraude()
    elif selected_skin["name"] == "Vaisseau Améthyste":
        player_ship = VaisseauAmethyste()
    elif selected_skin["name"] == "Vaisseau Diamant":
        player_ship = VaisseauDiamant()
    else:
        player_ship = Ship()  # Par défaut, Vaisseau Basique


    while running:
        window.fill((0, 0, 0))

        for event in pygame.event.get():
            
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                player_ship.shoot()

        player_ship.update(enemies)
        player_ship.move()
        player_ship.rotate_to_mouse()
        player_ship.draw(window)

        # Update les balles
        for bullet in player_ship.bullets[:]:
            bullet.move()
            bullet.draw(window)

            # portée de la balle
            if bullet.distance_traveled >= bullet.max_range:
                player_ship.bullets.remove(bullet)
                continue

            # colision au mur
            if bullet.x < 0:
                if bullet.wall_bounces > 0:
                    bullet.x = 0
                    bullet.bounce_off_wall("vertical")
                else:
                    player_ship.bullets.remove(bullet)
                    continue
            elif bullet.x > WIDTH:
                if bullet.wall_bounces > 0:
                    bullet.x = WIDTH
                    bullet.bounce_off_wall("vertical")
                else:
                    player_ship.bullets.remove(bullet)
                    continue

            if bullet.y < 0:
                if bullet.wall_bounces > 0:
                    bullet.y = 0
                    bullet.bounce_off_wall("horizontal")
                else:
                    player_ship.bullets.remove(bullet)
                    continue
            elif bullet.y > HEIGHT:
                if bullet.wall_bounces > 0:
                    bullet.y = HEIGHT
                    bullet.bounce_off_wall("horizontal")
                else:
                    player_ship.bullets.remove(bullet)
                    continue


            # colision à l'ennemi
            for enemy in enemies[:]:
                if enemy not in bullet.hit_enemies:
                    distance = math.hypot(bullet.x - enemy.x, bullet.y - enemy.y)
                    if distance < bullet.radius + enemy.radius:
                        # Degats à l'ennemi
                        enemy.health -= bullet.damage
                        bullet.hit_enemies.add(enemy)

                        # explosion s'il meur
                        if enemy.health <= 0:
                            enemies.remove(enemy)
                            score += 1
                            if score % 2 == 0:  # Gagner 1 crédit tous les 2 points
                                credits_earned += 1
                            if bullet.explosion_radius > 0:
                                bullet.explode(enemies)
                        # effets de balles
                        if bullet.piercing > 0:

                            bullet.piercing -= 1
                            if bullet.piercing < 0: 
                                player_ship.bullets.remove(bullet)
                            break
                        elif bullet.enemy_bounces > 0:
                            bullet.bounce_off_enemy(enemy.x, enemy.y)
                            if bullet.enemy_bounces < 0:
                                player_ship.bullets.remove(bullet)
                            break
                        else:
                            player_ship.bullets.remove(bullet)
                            break

        # Update ennemis
        for enemy in enemies[:]:
            enemy.update(player_ship)  # Add player parameter for shooter enemies
            enemy.move_towards(player_ship)
            enemy.draw(window)

            enemy.check_collision(player_ship)
            if player_ship.health <= 0:
                running = False
                show_game_over(score, credits_earned)
                break

        # nouvelle vague
        if len(enemies) == 0:
            wave_number += 1
            if not shop_upgrades(player_ship):
                running = False
                break
            enemies,cycle = spawn_wave(wave_number)
            wave_text_timer = 120

        if wave_text_timer > 0:
            wave_text = font.render(f"Cycle {cycle}      Wave {wave_number}", True, WHITE)
            window.blit(wave_text, (WIDTH // 2 - wave_text.get_width() // 2, HEIGHT // 2))
            wave_text_timer -= 1

        if enemies[0].healthbar==True :
            pygame.draw.line(window,RED,(int(WIDTH//2 - (enemies[0].health/enemies[0].maxhealth)*300),20),(int(WIDTH//2 + (enemies[0].health/enemies[0].maxhealth)*300),20),width=20)

            rect= WIDTH//2-300 , 10 , 600 , 20
            pygame.draw.rect(window,WHITE,rect,2)

            bosstag = font.render(enemies[0].bossname,True,WHITE)
            window.blit(bosstag, (WIDTH//2-50, 15))


        # statistiques à gauche
        score_text = font.render(f"Score: {score}", True, WHITE)
        health_text = font.render(f"Health: {int(player_ship.health)}/{player_ship.max_health}", True, GREEN)
        credits_text = font.render(f"Crédits: {credits_earned}", True, YELLOW)
        window.blit(score_text, (10, 10))
        window.blit(health_text, (10, 50))
        window.blit(credits_text, (10, 90))

        # dernieres 3 upgrades
        upgrade_y = 130
        for upgrade in player_ship.upgrades[-3:]:
            upgrade_text = font.render(upgrade, True, YELLOW)
            window.blit(upgrade_text, (10, upgrade_y))
            upgrade_y += 30

        # Stats  ( a modifier )
        stats = [
            f"Damage: {player_ship.damage}",
            f"Speed: {player_ship.speed}",
            f"Range: {player_ship.range}",
            f"Bullet Speed: {player_ship.bullet_speed}",
            f"Reload Speed: {player_ship.reload_speed:.1f}x",
            f"Regeneration: {player_ship.regen_rate:.1f}/s",
            f"Enemy Bounces: {player_ship.enemy_bounces}",
            f"Wall Bounces: {player_ship.wall_bounces}",
            f"Bullet Piercing: {player_ship.bullet_piercing}",
            f"Parallel Shots: {player_ship.parallel_shots}",
            f"Shield: {player_ship.shield}%",
            f"Bullet Size: {player_ship.bullet_size}",
            f"Explosion Radius: {player_ship.explosion_radius}",
            f"Bullet Range: {player_ship.range}",
            f"Body Damage: {player_ship.body_damage}",
            f"Forcefield Damage: {player_ship.forcefield_damage}/s"
        ]

        stat_y = 200
        for stat in stats:
            stat_text = font.render(stat, True, WHITE)
            window.blit(stat_text, (10, stat_y))
            stat_y += 25

        pygame.display.flip()
        pygame.time.Clock().tick(60)

    # Après la fin de la partie, ajouter les crédits gagnés à la boutique
    shop.credits += credits_earned
    save_data(shop.credits, shop.selected_skin, shop.skins)  # Sauvegarder les crédits, le skin sélectionné et les skins débloqués
    show_game_over(score, credits_earned)

def show_game_over(score, credits_earned):
    font = pygame.font.Font(None, 48)
    game_over_text = font.render("Game Over", True, RED)
    score_text = font.render(f"Score: {score}", True, WHITE)
    credits_text = font.render(f"Crédits gagnés: {credits_earned}", True, YELLOW)
    restart_text = font.render("Press SPACE to Restart", True, GREEN)
    menu_text = font.render("Press M for Main Menu", True, BLUE)

    window.fill((0, 0, 0))
    window.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 100))
    window.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2 - 50))
    window.blit(credits_text, (WIDTH // 2 - credits_text.get_width() // 2, HEIGHT // 2))
    window.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 50))
    window.blit(menu_text, (WIDTH // 2 - menu_text.get_width() // 2, HEIGHT // 2 + 100))
    pygame.display.flip()


# Crée le Shop et exécute la boucle principale
shop = Shop()
shop.run(window)
