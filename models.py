import sys
import os
import pygame

# ==== FIX DES IMPORTS ====
CURRENT_FILE = os.path.abspath(__file__)
PROJECT_PATH = os.path.dirname(CURRENT_FILE)
PARENT_PATH = os.path.dirname(PROJECT_PATH)

if PROJECT_PATH not in sys.path:
    sys.path.append(PROJECT_PATH)
if PARENT_PATH not in sys.path:
    sys.path.append(PARENT_PATH)
# ==========================

from utils.direction import Direction
from utils.lock_state import LockState
from settings import ROOM_COLORS, TILE_SIZE, BLACK, WHITE


# ------------------------------------------------------
# DOOR (porte)
# ------------------------------------------------------
class Door:
    def __init__(self, direction: Direction, lock_state: LockState):
        self.direction = direction
        self.lock_state = lock_state

    def can_open(self, inventory):
        """Vérifie si la porte peut être ouverte."""
        if self.lock_state == LockState.UNLOCKED:
            return True

        if self.lock_state == LockState.LOCKED:
            # soit une clé, soit un kit de crochetage
            return inventory.keys > 0 or inventory.has_lockpick

        if self.lock_state == LockState.DOUBLE_LOCKED:
            # toujours besoin d'une clé
            return inventory.keys > 0

        return False

    def open(self, inventory):
        """Ouvre la porte et consomme les ressources si besoin."""
        if not self.can_open(inventory):
            return False

        # Niveau 1 : si pas de kit de crochetage, consomme une clé
        if self.lock_state == LockState.LOCKED:
            if not inventory.has_lockpick:
                inventory.keys -= 1

        # Niveau 2 : consomme toujours une clé
        if self.lock_state == LockState.DOUBLE_LOCKED:
            inventory.keys -= 1

        return True


# ------------------------------------------------------
# ROOM (salle)
# ------------------------------------------------------
class Room:
    def __init__(self, name, color="blue", cost=0, rarity=0, doors=None):
        self.name = name
        self.color = color          # blue / green / yellow / purple / orange / red
        self.cost = cost            # coût en gemmes
        self.rarity = rarity        # entier 0..3
        self.doors = doors if doors else []

    def get_color(self):
        """Retourne la couleur RGB de la salle."""
        return ROOM_COLORS[self.color]

    def draw(self, screen, x, y):
        # Fond
        pygame.draw.rect(screen, self.get_color(), (x, y, TILE_SIZE, TILE_SIZE))
        # Bordure
        pygame.draw.rect(screen, BLACK, (x, y, TILE_SIZE, TILE_SIZE), 2)
        # Nom
        font = pygame.font.SysFont("arial", 16)
        txt = font.render(self.name, True, WHITE)
        screen.blit(txt, (x + 5, y + 5))

    def get_door(self, direction: Direction):
        """Retourne la porte correspondant à la direction demandée."""
        for d in self.doors:
            if d.direction == direction:
                return d
        return None

    # --------------------------------------------------
    # Effets / loot quand on entre dans la salle
    # --------------------------------------------------
    def on_enter(self, inventory, rng):
        """
        Quand le joueur entre dans la salle, il y a une certaine probabilité
        de trouver quelque chose : nourriture, gemmes, clés, dés, objets permanents.
        On fait un truc simple mais conforme à l'énoncé.
        """

        # chance de base de trouver quelque chose
        base = 0.15
        if self.color == "green":
            base = 0.40   # jardins -> riches en loot
        elif self.color == "purple":
            base = 0.35   # chambres -> souvent de la nourriture
        elif self.color == "blue":
            base = 0.20
        elif self.color == "yellow":
            base = 0.25
        elif self.color == "red":
            base = 0.25

        # Patte de lapin => plus de chances globales
        if inventory.has_rabbit_foot:
            base *= 1.5

        if rng.random() > base:
            return  # rien trouvé

        # Petit tirage : permanent ou consommable
        roll = rng.random()

        # Une petite chance de tomber sur un objet permanent
        if roll > 0.85:
            item = rng.choice(["lockpick", "metal", "rabbit"])
            if item == "lockpick":
                inventory.has_lockpick = True
                print(f"Vous trouvez un kit de crochetage dans {self.name} !")
            elif item == "metal":
                inventory.has_metal_detector = True
                print(f"Vous trouvez un détecteur de métaux dans {self.name} !")
            else:
                inventory.has_rabbit_foot = True
                print(f"Vous trouvez une patte de lapin dans {self.name} !")
            return

        # Sinon : objet consommable
        options = ["gem", "key", "dice", "food"]
        weights = [3, 3, 2, 4]

        # Détecteur de métaux : plus de clés et de gemmes
        if inventory.has_metal_detector:
            weights[0] += 2  # gemmes
            weights[1] += 2  # clés

        # Jardins : plus de gemmes / nourriture
        if self.color == "green":
            weights[0] += 1
            weights[3] += 1

        loot = rng.choices(options, weights=weights, k=1)[0]

        if loot == "gem":
            inventory.gems += 1
            print(f"Vous trouvez une gemme dans {self.name}.")
        elif loot == "key":
            inventory.keys += 1
            print(f"Vous trouvez une clé dans {self.name}.")
        elif loot == "dice":
            inventory.dice += 1
            print(f"Vous trouvez un dé dans {self.name}.")
        else:  # nourriture -> on choisit un type
            food_roll = rng.random()
            if food_roll < 0.2:
                inventory.add_steps(2)   # pomme
                print("Vous mangez une pomme (+2 pas).")
            elif food_roll < 0.4:
                inventory.add_steps(3)   # banane
                print("Vous mangez une banane (+3 pas).")
            elif food_roll < 0.7:
                inventory.add_steps(10)  # gâteau
                print("Vous mangez un gâteau (+10 pas).")
            elif food_roll < 0.9:
                inventory.add_steps(15)  # sandwich
                print("Vous mangez un sandwich (+15 pas).")
            else:
                inventory.add_steps(25)  # repas
                print("Vous mangez un repas complet (+25 pas).")


# ------------------------------------------------------
# INVENTORY (inventaire du joueur)
# ------------------------------------------------------
class Inventory:
    def __init__(self):
        # consommables
        self.steps = 70
        self.keys = 0
        self.gems = 2
        self.dice = 0

        # permanents
        self.has_lockpick = False
        self.has_metal_detector = False
        self.has_rabbit_foot = False

    def use_step(self):
        self.steps -= 1

    def add_steps(self, n):
        self.steps += n


# ------------------------------------------------------
# PLAYER (joueur)
# ------------------------------------------------------
class Player:
    def __init__(self, start_row, start_col):
        self.row = start_row
        self.col = start_col

    def move(self, dr, dc):
        self.row += dr
        self.col += dc

