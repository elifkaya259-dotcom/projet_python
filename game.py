import sys
import os
import pygame

# ==== FIX PATH ====
CURRENT_FILE = os.path.abspath(__file__)
PROJECT_PATH = os.path.dirname(CURRENT_FILE)
PARENT_PATH = os.path.dirname(PROJECT_PATH)

if PROJECT_PATH not in sys.path:
    sys.path.append(PROJECT_PATH)
if PARENT_PATH not in sys.path:
    sys.path.append(PARENT_PATH)
# ===================

from settings import *
from maison import Maison
from models import Player, Inventory
from utils.direction import Direction


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Projet POO - Manoir")
        self.clock = pygame.time.Clock()

        self.maison = Maison()
        self.player = Player(MAP_ROWS - 1, MAP_COLS // 2)
        self.inventory = Inventory()

        # Direction courante choisie avec ZQSD
        self.selected_direction = None

    # ---------------------------------------------------
    def draw_direction_arrow(self):
        """Dessine une flèche dans la direction sélectionnée."""
        if self.selected_direction is None:
            return

        x = self.player.col * TILE_SIZE + TILE_SIZE // 2
        y = self.player.row * TILE_SIZE + TILE_SIZE // 2

        if self.selected_direction == Direction.TOP:
            end = (x, y - TILE_SIZE // 2)
        elif self.selected_direction == Direction.BOTTOM:
            end = (x, y + TILE_SIZE // 2)
        elif self.selected_direction == Direction.LEFT:
            end = (x - TILE_SIZE // 2, y)
        elif self.selected_direction == Direction.RIGHT:
            end = (x + TILE_SIZE // 2, y)
        else:
            return

        pygame.draw.line(self.screen, WHITE, (x, y), end, 5)

    # ---------------------------------------------------
    def try_move(self):
        """Valide le déplacement lorsqu'on appuie sur ESPACE."""
        if self.selected_direction is None:
            print("Choisis d'abord une direction avec Z, Q, S ou D.")
            return

        # Traduire la direction en (dr, dc)
        dr = dc = 0
        if self.selected_direction == Direction.TOP:
            dr = -1
        elif self.selected_direction == Direction.BOTTOM:
            dr = 1
        elif self.selected_direction == Direction.LEFT:
            dc = -1
        elif self.selected_direction == Direction.RIGHT:
            dc = 1

        result = self.maison.move(self.player, self.inventory, dr, dc)

        # ---- CAS 1 : déplacement vers une salle déjà existante ----
        if result is True:
            return

        # ---- CAS 2 : création d'une nouvelle salle ----
        if isinstance(result, tuple) and result[0] == "NEW_ROOM":
            r, c = result[1], result[2]

            from room_picker import RoomPicker
            picker = RoomPicker(self.inventory, self.selected_direction, r, c)
            choice = picker.run(self.screen)

            if choice:
                # on place la nouvelle room
                self.maison.grid[r][c] = choice
                # on se déplace dedans
                self.player.row = r
                self.player.col = c
                self.inventory.use_step()
                # effets d'entrée dans la nouvelle pièce
                choice.on_enter(self.inventory, self.maison.random)

            return

        # ---- CAS 3 : déplacement impossible ----
        print("Déplacement impossible dans cette direction (pas de porte, porte verrouillée ou bord de la carte).")
        # on force le joueur à re-choisir une direction
        self.selected_direction = None


    # ---------------------------------------------------
    def draw_inventory(self):
        font = pygame.font.SysFont("arial", 22)
        status_text = (
            f"Steps: {self.inventory.steps} | "
            f"Keys: {self.inventory.keys} | "
            f"Gems: {self.inventory.gems} | "
            f"Dice: {self.inventory.dice} | "
            f"Coins: {self.inventory.coins}"
        )
        txt = font.render(status_text, True, WHITE)
        self.screen.blit(txt, (10, HEIGHT - 40))

    # ---------------------------------------------------
    def run(self):
        running = True

        while running:
            self.clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                # Sélection de direction avec ZQSD
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

                    if event.key == pygame.K_z:
                        self.selected_direction = Direction.TOP
                    if event.key == pygame.K_s:
                        self.selected_direction = Direction.BOTTOM
                    if event.key == pygame.K_q:
                        self.selected_direction = Direction.LEFT
                    if event.key == pygame.K_d:
                        self.selected_direction = Direction.RIGHT

                    # Validation du déplacement
                    if event.key == pygame.K_SPACE:
                        self.try_move()

            # Conditions de fin
            if self.inventory.steps <= 0:
                print("PERDU - Plus de pas !")
                running = False
            # Défaite si aucune porte n'est jouable depuis la salle actuelle
            if running:  # seulement si on n'a pas déjà perdu sur les pas
                moves_possible = False
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    if self.maison.can_move(self.player, self.inventory, dr, dc):
                        moves_possible = True
                        break

                if not moves_possible:
                    print("PERDU - Vous êtes bloqué, aucune porte ne peut être ouverte.")
                    running = False

            if self.player.row == 0 and self.player.col == MAP_COLS // 2:
                print("VICTOIRE ! Vous avez atteint l'Antechamber.")
                running = False

            # Affichage
            self.screen.fill(BLACK)
            self.maison.draw(self.screen)
            self.draw_inventory()

            # Joueur
            pygame.draw.circle(
                self.screen,
                RED,
                (
                    self.player.col * TILE_SIZE + TILE_SIZE // 2,
                    self.player.row * TILE_SIZE + TILE_SIZE // 2,
                ),
                15,
            )

            # Flèche de direction
            self.draw_direction_arrow()

            pygame.display.flip()

        pygame.quit()



