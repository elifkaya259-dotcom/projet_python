import sys
import os
import random

# ==== FIX DES IMPORTS ====
CURRENT_FILE = os.path.abspath(__file__)
PROJECT_PATH = os.path.dirname(CURRENT_FILE)
PARENT_PATH = os.path.dirname(PROJECT_PATH)

if PROJECT_PATH not in sys.path:
    sys.path.append(PROJECT_PATH)

if PARENT_PATH not in sys.path:
    sys.path.append(PARENT_PATH)
# ==========================

from models import Room, Door
from utils.direction import Direction
from utils.lock_state import LockState
from settings import MAP_ROWS, MAP_COLS


class Maison:
    def __init__(self):
        # Création de la grille vide
        self.grid = [[None for _ in range(MAP_COLS)] for _ in range(MAP_ROWS)]
        self.random = random.Random()

        # Position du Start (ligne du bas, colonne centrale)
        start_row = MAP_ROWS - 1
        start_col = MAP_COLS // 2

        # ----- Salle de départ -----
        entrance = Room(
            "Start",
            color="blue",
            doors=[Door(Direction.TOP, LockState.UNLOCKED)]
        )
        self.grid[start_row][start_col] = entrance

        # ----- Salle d'arrivée -----
        antechamber = Room(
            "Goal",
            color="purple",
            doors=[Door(Direction.BOTTOM, LockState.DOUBLE_LOCKED)]
        )
        self.grid[0][MAP_COLS // 2] = antechamber


    # ======================================================
    # Vérifie si on peut se déplacer
    # ======================================================
    def can_move(self, player, inventory, dr, dc):
        r2 = player.row + dr
        c2 = player.col + dc

        # Limites du manoir
        if not (0 <= r2 < MAP_ROWS and 0 <= c2 < MAP_COLS):
            return False

        current = self.grid[player.row][player.col]
        target = self.grid[r2][c2]

        # Trouver direction
        if dr == -1:
            direction = Direction.TOP
        elif dr == 1:
            direction = Direction.BOTTOM
        elif dc == -1:
            direction = Direction.LEFT
        else:
            direction = Direction.RIGHT

        # Vérifier la porte
        door = current.get_door(direction)
        if door:
            return door.can_open(inventory)

        return False


    # ======================================================
    # Déplacement effectif
    # ======================================================
    def move(self, player, inventory, dr, dc):
        r2 = player.row + dr
        c2 = player.col + dc

        # Limites : hors map
        if not (0 <= r2 < MAP_ROWS and 0 <= c2 < MAP_COLS):
            return False

        current = self.grid[player.row][player.col]

        # Trouver direction
        if dr == -1:
            direction = Direction.TOP
        elif dr == 1:
            direction = Direction.BOTTOM
        elif dc == -1:
            direction = Direction.LEFT
        else:
            direction = Direction.RIGHT

        door = current.get_door(direction)
        if door is None:
            return False

        # ---- CAS 1 : La salle existe déjà → mouvement normal ----
        if self.grid[r2][c2] is not None:
            if door.open(inventory):
                player.move(dr, dc)
                inventory.use_step()
                return True
            return False

        # ---- CAS 2 : La salle n'existe pas encore → tirage ----
        if not door.can_open(inventory):
            return False

        # Ouverture de la porte
        door.open(inventory)

        # On renvoie un code spécial pour dire "nouvelle salle"
        return ("NEW_ROOM", r2, c2)


    # ======================================================
    # Affichage de la grille
    # ======================================================
    def draw(self, screen):
        import pygame
        from settings import TILE_SIZE, GREY

        for r in range(MAP_ROWS):
            for c in range(MAP_COLS):
                x = c * TILE_SIZE
                y = r * TILE_SIZE
                room = self.grid[r][c]

                if room is None:
                    pygame.draw.rect(screen, GREY, (x, y, TILE_SIZE, TILE_SIZE), 1)
                else:
                    room.draw(screen, x, y)



