import pygame


class EnergyOrb(pygame.sprite.Sprite):
    """Represents an energy orb that the player can collect."""

    def __init__(self, x: int, y: int, image: pygame.Surface) -> None:
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=(x, y))
        self.lifetime = 10000000
        self.spawn_time = pygame.time.get_ticks()

    def update(self) -> None:
        """Checks if the orb's lifetime has expired and removes it if so."""
        if pygame.time.get_ticks() - self.spawn_time > self.lifetime:
            self.kill()
