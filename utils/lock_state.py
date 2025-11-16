from enum import Enum

class LockState(Enum):
    UNLOCKED = 0
    LOCKED = 1
    DOUBLE_LOCKED = 2
