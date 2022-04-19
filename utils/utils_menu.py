from enum import Enum


SCREEN_AREA = (800, 700)
GAME_AREA = (800, 500)
CHAT_AREA = (800, 200)


class State(Enum):
    START = 0
    END = 1
    LEVEL = 2
    GAME = 3
