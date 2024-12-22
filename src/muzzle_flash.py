import math
import random

import pygame


class MuzzleFlash(pygame.sprite.Sprite):
    """Represents a muzzle flash effect when the player fires a weapon."""

    def __init__(self, pos: tuple[int, int], angle: float) -> None:
        super().__init__()
        self.original_image = pygame.Surface((10, 10), pygame.SRCALPHA)

        base_red = random.randint(220, 255)
        base_green = random.randint(100, 180)
        base_blue = random.randint(0, 50)
        pygame.draw.circle(self.original_image, (base_red, base_green, base_blue, 230), (10, 10), 6)

        pygame.draw.circle(self.original_image, (base_red, base_green + 20, base_blue, 180), (20, 10), 9)
        pygame.draw.circle(
            self.original_image,
            (min(base_red + 20, 255), min(base_green + 40, 255), min(base_blue + 20, 255), 130),
            (30, 10),
            12,
        )

        self.image = pygame.transform.rotate(self.original_image, math.degrees(-angle))
        self.rect = self.image.get_rect(center=pos)
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = random.randint(1, 4)

    def update(self) -> None:
        """Checks if the muzzle flash's lifetime has expired and removes it if so."""
        if pygame.time.get_ticks() - self.spawn_time > self.lifetime:
            self.kill()
