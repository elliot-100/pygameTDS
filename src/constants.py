"""Constants for the game."""

GAME_WINDOW = {
    'WIDTH': 1920,
    'HEIGHT': 1080,
    'FPS': 60,
}
PLAY_AREA = {
    'WIDTH': 2020,
    'HEIGHT': 1180,
}
COLORS: dict[str, tuple[int, int, int]] = {
    'WHITE': (255, 255, 255),
    'RED': (255, 0, 0),
    'BLACK': (0, 0, 0),
    'NEON': (57, 255, 20),
    'YELLOW': (255, 255, 0),
    'GAMMA': (74, 254, 2),
}
PENETRATION_COLORS: list[tuple[int, int, int]] = [
    (255, 0, 0),
    (255, 128, 0),
    (255, 255, 0),
    (0, 255, 0),
]
LEVEL_THRESHOLDS = {
    1: 0,
    2: 90,
    3: 180,
    4: 280,
    5: 390,
    6: 515,
    7: 655,
    8: 810,
    9: 980,
    10: 1170,
    11: 1380,
    12: 1615,
    13: 1875,
    14: 2155,
    15: 2465,
    16: 2805,
    17: 3175,
    18: 3580,
    19: 4020,
    20: 4500,
    21: 5025,
    22: 5600,
    23: 6225,
    24: 6905,
    25: 7645,
    26: 8450,
    27: 9325,
    28: 10275,
    29: 11305,
    30: 12425,
}
UPGRADE_OPTIONS = [
    'HP +20%',
    'Bullet SPD 10%',
    'Bullet DMG 5%',
    'Reload SPD +5%',
    'Mag Ammo +5%',
    'Fire Rate +5%',
    'Precision +5%',
    'Increase XP Gain',
    'a Random Weapon',
]
