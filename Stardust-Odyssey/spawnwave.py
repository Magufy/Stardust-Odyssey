import pygame
import random
import math
import json
import socket
import threading
import time
import os
import cv2
import numpy as np
from queue import Queue, Empty

from enemies import BasicEnemy, TankEnemy, ShooterEnemy, LinkEnemy, Tank_Boss, Dash_Boss, Laser_Boss, Mothership_Boss

def spawn_wave(wave_number, play_music=True):
    enemies = []
    cycle=1 + wave_number//20
    cycle_wave=wave_number%20
    num_enemies = cycle_wave + 3*cycle**2
    
    # Déterminer le type de musique à jouer
    music_type = "boss" if cycle_wave % 5 == 0 else "vague"
    
    # Jouer la musique seulement si demandé
    if play_music:
        # Stop any currently playing music
        pygame.mixer.stop()
        
        # Play sound effect based on wave type
        if music_type == "boss":
            # Boss wave
            son_boss = pygame.mixer.Sound("sons/boss.mp3")
            son_boss.set_volume(0.4)  # Set volume to 40%
            son_boss.play(loops=-1)  # -1 means loop indefinitely
        else:
            # Regular wave
            son_vague = pygame.mixer.Sound("sons/vague.mp3")
            son_vague.set_volume(0.3)  # Set volume to 30%
            son_vague.play(loops=-1)  # -1 means loop indefinitely

    if cycle_wave < 5 :
        types = [BasicEnemy] * 70 + [TankEnemy] * 30
    elif cycle_wave < 10:
        types = [BasicEnemy] * 50 + [TankEnemy] * 25 + [ShooterEnemy] * 25
    elif cycle_wave < 15 :
        types = [BasicEnemy] * 30 + [TankEnemy] * 25 + [ShooterEnemy] * 25 + [LinkEnemy] * 20
    else :
        types = [TankEnemy] * 40 + [ShooterEnemy] * 45 + [LinkEnemy] * 15

    if cycle_wave == 5 :
        enemies.append(Tank_Boss())
        return enemies,cycle
    elif cycle_wave == 10 :
        enemies.append(Dash_Boss())
        return enemies,cycle
    elif cycle_wave == 15:
        enemies.append(Laser_Boss())
        return enemies,cycle
    elif cycle_wave == 0 : # donc 20 car changement de cycle
        enemies.append(Mothership_Boss())
        return enemies,cycle
    else:
        for i in range(num_enemies):
            enemy_class = random.choice(types)
            enemies.append(enemy_class())
        return enemies,cycle
