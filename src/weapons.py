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


class WeaponCategory:
    """Represents a category of weapons."""

    def __init__(self, name: str, weapons: list[Weapon]) -> None:
        self.name = name
        self.weapons = weapons
        self.current_index = self.find_first_unlocked_weapon()

    def find_first_unlocked_weapon(self) -> int | None:
        """Finds the index of the first unlocked weapon in the category."""
        for i, weapon in enumerate(self.weapons):
            if not weapon.locked:
                return i
        return None

    def current_weapon(self) -> Weapon | None:
        """Returns the currently selected weapon."""
        if self.current_index is not None:
            return self.weapons[self.current_index]
        return None

    def next_weapon(self) -> None:
        """Cycles to the next unlocked weapon in the category."""
        if self.current_index is None:
            return
        start_index = self.current_index
        while True:
            self.current_index = (self.current_index + 1) % len(self.weapons)
            if not self.weapons[self.current_index].locked:
                return
            if self.current_index == start_index:
                return

    def previous_weapon(self) -> None:
        """Cycles to the previous unlocked weapon in the category."""
        if self.current_index is None:
            return
        start_index = self.current_index
        while True:
            self.current_index = (self.current_index - 1) % len(self.weapons)
            if not self.weapons[self.current_index].locked:
                return
            if self.current_index == start_index:
                return

    def has_unlocked_weapon(self) -> bool:
        """Checks if the category has at least one unlocked weapon."""
        return any(not weapon.locked for weapon in self.weapons)
