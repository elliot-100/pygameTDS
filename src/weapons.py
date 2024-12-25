from __future__ import annotations

from dataclasses import dataclass
from typing import Self


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

    @classmethod
    def setup(cls) -> list[Self]:
        """Return all `WeaponCategory`s, populated with `Weapon`s."""
        pistols = cls(
            'pistols',
            [
                Weapon('Glock(PDW)', 20, 200, 24, 0.080, 15, 1900, 1, locked=False),
            ],
        )
        smgs = cls(
            'SMG',
            [
                Weapon('Skorpian(SMG)', 20, 90, 24, 0.080, 30, 1900, 3),
            ],
        )
        # rifles = cls(
        #     'Rifles',
        #     [
        #         Weapon('SVT-40(RIFLE)', 20, 440, 59, 0.068, 10, 2250, 5),
        #     ],
        # )
        bolt_actions = cls(
            'Bolt Action',
            [
                Weapon('Mosin(BOLT)', 20, 2500, 85, 0.002, 5, 2700, 7),
            ],
        )
        assault_rifles = cls(
            'Assault Rifle',
            [
                Weapon('AK-47(AR)', 20, 100, 35, 0.090, 31, 2000, 3),
            ],
        )
        lmgs = cls(
            'LMG',
            [
                Weapon('PKM(LMG)', 20, 170, 30, 0.2, 51, 3000, 5),
            ],
        )
        shotguns = cls(
            'Shotgun',
            [
                Weapon('Mossberg 500(SG)', 20, 1200, 25, 0.6, 5, 2500, 3, locked=False),
                Weapon('Remington 870(SG)', 20, 1100, 28, 0.55, 6, 2600, 3),
            ],
        )
        launchers = cls(
            'Launchers',
            [
                Weapon(
                    'RPG-7(BLAST)',
                    20,
                    5000,
                    100,
                    0.1,
                    1,
                    5000,
                    0,
                    blast_radius=50,
                ),
            ],
        )
        return [
            pistols,
            smgs,
            bolt_actions,
            assault_rifles,
            lmgs,
            shotguns,
            launchers,
        ]

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
