import pygame

from gameloop import Shop

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
GRAY = (128, 128, 128)
BLACK = (0, 0, 0)

selected_ship = "Vaisseau Basique"

# Police
font = pygame.font.Font(None, 36)


Shop().run(window)