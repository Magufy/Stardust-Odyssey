import pygame

from gameloop import Shop

pygame.init()

# Paramètres de la fenêtre en plein écran
window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = window.get_size()
pygame.display.set_caption("Stardust Odyssey")


Shop().run(window)
