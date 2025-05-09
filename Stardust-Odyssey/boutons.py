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
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.is_hovered = False

        self.selected_color = (255, 255, 255)
        self.unselected_color = (150, 150, 150)
        self.background_color = (10, 10, 30)

        self.font = pygame.font.Font(None, 36)

    def draw(self, surface):
        # Changer la couleur si le bouton est survolé
        color = self.selected_color if self.is_hovered else self.unselected_color
        color2 = self.unselected_color if self.is_hovered else self.selected_color
        pygame.draw.rect(surface, color, self.rect, width=2, border_radius=10)
        text_surface = self.font.render(self.text, True, color2)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered:
                return True
        return False

class InputBox:
    def __init__(self, x, y, width, height, text=''):
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
