from typing import ClassVar

import pygame


class EnergyOrb(pygame.sprite.Sprite):
    """Represents an energy orb that the player can collect."""

    LIFETIME: ClassVar = 10000 * 1000
    """Milliseconds."""

    def __init__(self, x: int, y: int, image: pygame.Surface) -> None:
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=(x, y))
        self.spawn_time = pygame.time.get_ticks()

    def update(self) -> None:
        """Checks if the orb's lifetime has expired and removes it if so."""
        age = pygame.time.get_ticks() - self.spawn_time
        if age > self.LIFETIME:
            self.kill()
