from typing import ClassVar

import pygame

from src.constants import COLORS


class Cursor(pygame.sprite.Sprite):
    """Implements gunsight/cursor."""

    OUTER_RADIUS: ClassVar = 20
    INNER_RADIUS: ClassVar = 2

    def __init__(self) -> None:
        super().__init__()
        self.image = pygame.Surface(
            size=(2 * self.OUTER_RADIUS, 2 * self.OUTER_RADIUS),
            flags=pygame.SRCALPHA,
        )
        self.rect = self.image.get_rect()
        center = self.rect.center
        pygame.draw.circle(
            surface=self.image,
            color=COLORS['WHITE'],
            center=center,
            radius=self.OUTER_RADIUS,
            width=2,
        )
        pygame.draw.circle(
            surface=self.image,
            color=COLORS['RED'],
            center=center,
            radius=self.INNER_RADIUS,
        )

    def draw(self, *, surface: pygame.Surface, center_pos: tuple[int, int]) -> None:
        """Blit to `surface`, centered on `center_pos`."""

        surface.blit(self.image, (center_pos[0] - self.OUTER_RADIUS, center_pos[1] - self.OUTER_RADIUS))
