import math
import random
from typing import ClassVar

import pygame

from src.constants import COLORS


class BloodParticle(pygame.sprite.Sprite):
    PARTICLES_PER_SPRAY: ClassVar = 5
    LIFETIME: ClassVar = 100000
    DECELERATION: ClassVar = 0.02
    """Factor for speed reduction per frame."""

    def __init__(self, pos: tuple[int, int], angle: float, speed: float) -> None:
        super().__init__()
        self.image = pygame.Surface((random.randint(1, 5), random.randint(1, 5)))
        self.image.fill(COLORS['RED'])
        self.rect = self.image.get_rect(center=pos)
        self.dx = speed * math.cos(angle) * -1
        self.dy = speed * math.sin(angle) * -1
        self.spawn_time = pygame.time.get_ticks()
        self.alpha = 255

    def update(self) -> None:
        self.rect.x += self.dx
        self.rect.y += self.dy
        self.dx *= 1 - self.DECELERATION
        self.dy *= 1 - self.DECELERATION

        elapsed_time = pygame.time.get_ticks() - self.spawn_time
        if elapsed_time < self.LIFETIME:
            self.alpha = int(255 * (1 - elapsed_time / self.LIFETIME))
            self.image.set_alpha(self.alpha)
        else:
            self.kill()
