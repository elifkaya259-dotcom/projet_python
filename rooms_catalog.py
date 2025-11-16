import random
from models import Room, Door
from utils.direction import Direction
from utils.lock_state import LockState
from settings import MAP_ROWS, MAP_COLS


def opposite(dir_):
    if dir_ == Direction.TOP:
        return Direction.BOTTOM
    if dir_ == Direction.BOTTOM:
        return Direction.TOP
    if dir_ == Direction.LEFT:
        return Direction.RIGHT
    if dir_ == Direction.RIGHT:
        return Direction.LEFT
    return dir_


# Chaque définition décrit une "famille" de pièces
# Les directions sont ABSOLUES (haut/bas/gauche/droite dans la grille)
ROOM_DEFS = [
    # Très communes : pièces bleues
    {
        "name": "Blue",
        "color": "blue",
        "cost": 0,
        "rarity": 0,
        "doors": [Direction.TOP, Direction.BOTTOM],  # couloir vertical simple
    },
    {
        "name": "Cross",
        "color": "blue",
        "cost": 0,
        "rarity": 0,
        "doors": [Direction.TOP, Direction.BOTTOM, Direction.LEFT, Direction.RIGHT],
    },

    # Jardins verts : chemins latéraux
    {
        "name": "Left Garden",
        "color": "green",
        "cost": 1,
        "rarity": 1,
        "doors": [Direction.BOTTOM, Direction.LEFT],
    },
    {
        "name": "Right Garden",
        "color": "green",
        "cost": 1,
        "rarity": 1,
        "doors": [Direction.BOTTOM, Direction.RIGHT],
    },

    # Couloirs jaunes : tournants
    {
        "name": "Turn Left",
        "color": "yellow",
        "cost": 1,
        "rarity": 1,
        "doors": [Direction.TOP, Direction.LEFT],
    },
    {
        "name": "Turn Right",
        "color": "yellow",
        "cost": 1,
        "rarity": 1,
        "doors": [Direction.TOP, Direction.RIGHT],
    },
    
    {
        "name": "Shop",
        "color": "yellow",
        "cost": 1,
        "rarity": 2,
        "doors": [Direction.TOP, Direction.BOTTOM, Direction.LEFT, Direction.RIGHT],
    },
    # Pièces violettes : chambres (un peu rares)
    {
        "name": "Bedroom",
        "color": "purple",
        "cost": 2,
        "rarity": 2,
        "doors": [Direction.BOTTOM],
    },

    # Pièce rouge : un peu "dangereuse"
    {
        "name": "Trap",
        "color": "red",
        "cost": 0,
        "rarity": 2,
        "doors": [Direction.BOTTOM],
    },
]

def random_lock_state_for_row(row):
    """
    Choisit aléatoirement un niveau de verrouillage pour une porte
    située sur la ligne `row` de la grille.

    - Rangée de départ (MAP_ROWS - 1) : toujours UNLOCKED (niveau 0)
    - Rangée de l'antichambre (0)    : toujours DOUBLE_LOCKED (niveau 2)
    - Entre les deux : mélange, avec plus de portes difficiles en remontant.
    """
    # Sécurité au cas où
    if row is None:
        return LockState.UNLOCKED

    # Rangée de départ : que des portes ouvertes
    if row == MAP_ROWS - 1:
        return LockState.UNLOCKED

    # Rangée de l'antichambre : que des portes double-tour
    if row == 0:
        return LockState.DOUBLE_LOCKED

    # Progression verticale : 0 tout en bas, 1 tout en haut
    progress = (MAP_ROWS - 1 - row) / (MAP_ROWS - 1)

    # On définit des probabilités simples selon la progression
    if progress < 0.33:
        # proche de l'entrée : surtout des portes ouvertes
        p_unlocked = 0.7
        p_locked = 0.25
        p_double = 0.05
    elif progress < 0.66:
        # milieu du manoir : mix équilibré
        p_unlocked = 0.5
        p_locked = 0.35
        p_double = 0.15
    else:
        # proche de l'antichambre (mais pas tout en haut) : portes plus dures
        p_unlocked = 0.3
        p_locked = 0.4
        p_double = 0.3

    r = random.random()
    if r < p_unlocked:
        return LockState.UNLOCKED
    elif r < p_unlocked + p_locked:
        return LockState.LOCKED
    else:
        return LockState.DOUBLE_LOCKED


def _make_room(defn, target_row=None):
    """
    Crée une Room à partir de sa définition, en donnant à chacune
    de ses portes un niveau de verrouillage adapté à la ligne.
    """
    doors = [
        Door(d, random_lock_state_for_row(target_row))
        for d in defn["doors"]
    ]
    return Room(defn["name"], defn["color"], defn["cost"], defn["rarity"], doors)



def _weighted_choice(candidates):
    """Choisit une définition de pièce en fonction de la rareté."""
    weights = []
    for d in candidates:
        r = d["rarity"]
        w = 1 / (3 ** r)   # rareté 1 → prob divisée par 3, etc.
        weights.append(w)

    idx = random.choices(range(len(candidates)), weights=weights, k=1)[0]
    return candidates[idx]


def pick_random_rooms(entry_dir, target_row=None, target_col=None):
    """
    Tire 3 pièces compatibles avec la direction d'entrée.

    entry_dir = direction choisie par le joueur (haut/bas/gauche/droite)
    target_row / target_col = case où la pièce sera posée (pour éviter de
    mettre des portes qui sortent du manoir).
    """
    entry_side = opposite(entry_dir)

    # 1) Candidats dont les portes contiennent au moins la face d'entrée
    candidates = [d for d in ROOM_DEFS if entry_side in d["doors"]]

    # 2) Optionnel : filtrer les pièces dont une porte donnerait hors du manoir
    if target_row is not None and target_col is not None:
        filtered = []
        for d in candidates:
            ok = True
            for door_dir in d["doors"]:
                dr = dc = 0
                if door_dir == Direction.TOP:
                    dr = -1
                elif door_dir == Direction.BOTTOM:
                    dr = 1
                elif door_dir == Direction.LEFT:
                    dc = -1
                elif door_dir == Direction.RIGHT:
                    dc = 1

                r2 = target_row + dr
                c2 = target_col + dc

                if not (0 <= r2 < MAP_ROWS and 0 <= c2 < MAP_COLS):
                    # cette porte mènerait dehors → pièce illégale
                    ok = False
                    break
            if ok:
                filtered.append(d)

        if filtered:
            candidates = filtered

    # Si jamais on a plus aucun candidat (très rare), on retombe sur tous
    if not candidates:
        candidates = ROOM_DEFS

    # 3) Tirage de 3 pièces, avec rareté
        # 3) Tirage de 3 pièces, avec rareté
    while True:
        defs = [_weighted_choice(candidates) for _ in range(3)]
        # On passe target_row pour choisir les niveaux de verrouillage
        rooms = [_make_room(d, target_row) for d in defs]

        # 4) On s'assure qu'au moins une coûte 0, comme demandé dans l'énoncé
        if any(r.cost == 0 for r in rooms):
            return rooms



