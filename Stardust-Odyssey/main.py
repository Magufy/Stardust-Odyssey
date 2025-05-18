import pygame

from gameloop import Shop

pygame.init()

# Paramètres de la fenêtre en plein écran
window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("Stardust Odyssey")
icone=pygame.image.load("images/icone_stardust.png")
pygame.display.set_icon(pygame.transform.scale(icone,(32,32)))

shop = Shop()
shop.run(window)
