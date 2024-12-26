"""Contains `BloodParticle` class."""

import math
import random
from typing import ClassVar, Self

import pygame

from src.constants import COLORS


class BloodParticle(pygame.sprite.Sprite):
    """Represents a blood particle."""

    PARTICLES_PER_SPRAY: ClassVar = 5
    LIFETIME: ClassVar = 100 * 1000
    """Milliseconds."""
    INITIAL_SPEED_MIN: ClassVar = 0.7
    """Minimum initial speed, pixels per frame."""
    INITIAL_SPEED_MAX: ClassVar = 1.5
    """Maximum initial speed, pixels per frame."""
    DECELERATION: ClassVar = 0.02
    """Factor for speed reduction per frame."""

    def __init__(self, *, pos: tuple[int, int]) -> None:
        super().__init__()
        self.image = pygame.Surface((random.randint(1, 5), random.randint(1, 5)))
        self.image.fill(COLORS['RED'])
        self.rect = self.image.get_rect(center=pos)
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(self.INITIAL_SPEED_MIN, self.INITIAL_SPEED_MAX)
        self.dx = speed * math.cos(angle) * -1
        self.dy = speed * math.sin(angle) * -1
        self.spawn_time = pygame.time.get_ticks()
        self.alpha = 255

    @classmethod
    def spawn_spray(cls, *, pos: tuple[int, int]) -> set[Self]:
        """Return a set of `BloodParticle`s representing a spray."""
        return {cls(pos=pos) for _ in range(cls.PARTICLES_PER_SPRAY)}

    def update(self) -> None:
        """Update the entity."""
        self.rect.x += int(self.dx)
        self.rect.y += int(self.dy)
        self.dx *= 1 - self.DECELERATION
        self.dy *= 1 - self.DECELERATION

        elapsed_time = pygame.time.get_ticks() - self.spawn_time
        if elapsed_time < self.LIFETIME:
            self.alpha = int(255 * (1 - elapsed_time / self.LIFETIME))
            self.image.set_alpha(self.alpha)
        else:
            self.kill()
