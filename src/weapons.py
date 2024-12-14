from dataclasses import dataclass


@dataclass
class Weapon:
    name: str
    projectile_speed: int
    fire_rate: int
    damage: int
    spread_angle: float
    max_ammo: int
    reload_time: int
    penetration: int
    locked: bool = True
    blast_radius: int = 0

    def __post_init__(self) -> None:
        self.ammo = self.max_ammo
