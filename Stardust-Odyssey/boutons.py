import pygame

# Couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

class Button:
    def __init__(self, x, y, width, height, text):
         # Crée un rectangle = la zone cliquable du bouton
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        # Indique si la souris "survole" le bouton
        self.is_hovered = False
        # Indique si la souris clique le boutton
        self.was_clicked = False

        self.selected_color = (255, 255, 255)
        self.unselected_color = (150, 150, 150)
        self.background_color = (10, 10, 30)
        # définition de la police du texte sur le boutton
        self.font = pygame.font.Font(None, 36)

    def draw(self, surface):
        # Changer la couleur si le bouton est survolé
        color = self.selected_color if self.is_hovered else self.unselected_color
        color2 = self.unselected_color if self.is_hovered else self.selected_color
        pygame.draw.rect(surface, color, self.rect, width=2, border_radius=10)
        text_surface = self.font.render(self.text, True, color2)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)
        if self.is_hovered:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)

    def handle_event(self, event):
        # Gère les événements liés à la souris et les boutons
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.was_clicked = True
                return True # Indique si le boutton a été cliqué
        return False # Aucun clique si en dehors du bouton
    
    def reset(self):
        # Réinitialise l'état de clic du bouton
        self.was_clicked = False 

class InputBox:
    def __init__(self, x, y, width, height, text=''):
        # Crée une zone rectangulaire pour l'entrée de texte
        self.rect = pygame.Rect(x, y, width, height)
        self.color = WHITE
        self.text = text
        self.font = pygame.font.Font(None, 36)
        self.txt_surface = self.font.render(text, True, self.color)
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Si l'utilisateur clique sur la boîte de saisie
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            # Change la couleur de la boîte de saisie
            self.color = BLUE if self.active else WHITE
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                # Re-render le texte
                self.txt_surface = self.font.render(self.text, True, self.color)
        return None

    def draw(self, screen):
        # Dessine le rectangle de fond
        pygame.draw.rect(screen, BLACK, self.rect)
        # Dessine le texte
        screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))
        # Dessine le contour
        pygame.draw.rect(screen, self.color, self.rect, 2)
