import pygame


class Chest(pygame.sprite.Sprite):
    """Represents a chest that the player can open to get rewards."""

    def __init__(self, x: int, y: int, image: pygame.Surface) -> None:
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=(x, y))
        self.opened = False

    def open(self) -> None:
        """Opens the chest, unlocks a random weapon, and removes it from the game."""
        self.opened = True
        self.kill()
