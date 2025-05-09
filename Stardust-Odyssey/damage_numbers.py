import pygame

class DamageNumber:
    def __init__(self, x, y, damage, is_critical=False):
        self.x = x
        self.y = y
        self.damage = damage
        self.time_left = 45  # Durée d'affichage en frames
        self.color = (255, 165, 0) if is_critical else (255, 255, 255)  # Orange pour critique, blanc sinon
        self.speed = 2  # Vitesse de déplacement vers le haut
        self.font = pygame.font.Font(None, 36)
        
    def update(self):
        self.y -= self.speed  # Monte
        self.time_left -= 1
        return self.time_left > 0  # Retourne True si le nombre doit rester affiché
        
    def draw(self, window):
        # Rendre le texte avec une taille plus grande pour les critiques
        text = self.font.render(str(int(self.damage)), True, self.color)
        window.blit(text, (self.x - text.get_width() // 2, self.y))

class DamageNumberManager:
    def __init__(self):
        self.damage_numbers = []
        
    def add_damage_number(self, x, y, damage, is_critical=False):
        self.damage_numbers.append(DamageNumber(x, y, damage, is_critical))
        
    def update(self):
        # Mettre à jour les nombres et supprimer ceux qui ont expiré
        self.damage_numbers = [num for num in self.damage_numbers if num.update()]
        
    def draw(self, window):
        for number in self.damage_numbers:
            number.draw(window)
