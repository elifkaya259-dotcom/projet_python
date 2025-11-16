import pygame
from settings import WHITE, WIDTH, HEIGHT
from rooms_catalog import pick_random_rooms
from utils.direction import Direction

CARD_W = 250
CARD_H = 250


class RoomPicker:
    def __init__(self, inventory, entry_dir, target_row, target_col):
        self.inventory = inventory
        self.entry_dir = entry_dir
        self.target_row = target_row
        self.target_col = target_col

        # IMPORTANT : on tient compte de la direction + position
        self.rooms = pick_random_rooms(entry_dir, target_row, target_col)
        self.index = 0

        self.title_font = pygame.font.SysFont("arial", 40, bold=True)
        self.card_font = pygame.font.SysFont("arial", 28)
        self.small_font = pygame.font.SysFont("arial", 20)

    def draw_card(self, screen, room, x, y, selected):
        CARD_BG = (30, 30, 30)
        pygame.draw.rect(screen, CARD_BG, (x, y, CARD_W, CARD_H), border_radius=12)

        # Bandeau de couleur
        color_rect = pygame.Rect(x + 20, y + 20, CARD_W - 40, 70)
        pygame.draw.rect(screen, room.get_color(), color_rect, border_radius=10)

        affordable = room.cost <= self.inventory.gems

        # Nom
        name_color = WHITE if affordable else (150, 150, 150)
        name = self.card_font.render(room.name, True, name_color)
        screen.blit(name, (x + CARD_W // 2 - name.get_width() // 2, y + 110))

        # Coût
        cost_text = f"Cost: {room.cost} gem(s)"
        cost_color = WHITE if affordable else (200, 80, 80)
        cost = self.small_font.render(cost_text, True, cost_color)
        screen.blit(cost, (x + CARD_W // 2 - cost.get_width() // 2, y + 150))

        # Rareté
        rare_text = f"Rarity: {room.rarity}"
        rare = self.small_font.render(rare_text, True, (200, 200, 200))
        screen.blit(rare, (x + CARD_W // 2 - rare.get_width() // 2, y + 180))

        # Bordure
        if selected and affordable:
            border_color = (255, 255, 0)
            width = 5
        else:
            border_color = (180, 180, 180)
            width = 3

        pygame.draw.rect(
            screen, border_color, (x, y, CARD_W, CARD_H),
            width=width, border_radius=12
        )

    def run(self, screen):
        clock = pygame.time.Clock()
        running = True

        while running:
            clock.tick(30)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.index = (self.index - 1) % 3
                    if event.key == pygame.K_RIGHT:
                        self.index = (self.index + 1) % 3

                    # Relancer le tirage avec un dé
                    if event.key == pygame.K_r:
                        if self.inventory.dice > 0:
                            self.inventory.dice -= 1
                            self.rooms = pick_random_rooms(
                                self.entry_dir, self.target_row, self.target_col
                            )
                            self.index = 0
                            print("Nouveau tirage de salles (dé dépensé).")

                    if event.key == pygame.K_RETURN:
                        room = self.rooms[self.index]
                        if room.cost > self.inventory.gems:
                            print("Pas assez de gemmes pour cette salle.")
                            continue
                        if room.cost > 0:
                            self.inventory.gems -= room.cost
                            print(f"{room.cost} gemme(s) dépensée(s).")
                        return room

            # ---- DESSIN ----
            screen.fill((10, 10, 10))

            title = self.title_font.render("Choose a Room", True, WHITE)
            screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 40))

            hint = self.small_font.render(
                "← → pour choisir, ENTER pour valider, R pour relancer (si dé).",
                True, WHITE,
            )
            screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 60))

            spacing = 70
            total_width = 3 * CARD_W + 2 * spacing
            start_x = WIDTH // 2 - total_width // 2
            y = HEIGHT // 2 - CARD_H // 2

            for i, room in enumerate(self.rooms):
                x = start_x + i * (CARD_W + spacing)
                self.draw_card(screen, room, x, y, i == self.index)

            pygame.display.flip()
