from typing import Any

import pygame

from src.constants import GAME_AREA, WINDOW


class Camera:
    """Manages the camera's position and movement."""

    def __init__(self, width: int, height: int) -> None:
        self.rect = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity: Any) -> Any:
        """Applies the camera's offset to an entity's position."""
        if isinstance(entity, pygame.Rect):
            return entity.move(self.rect.topleft)
        return entity.rect.move(self.rect.topleft)

    def update(self, target: Any) -> None:
        """Updates the camera's position to follow the target."""
        x = -target.rect.centerx + int(WINDOW['WIDTH'] / 2)
        y = -target.rect.centery + int(WINDOW['HEIGHT'] / 2)

        x = min(0, x)
        y = min(0, y)
        x = max(-(GAME_AREA['WIDTH'] - WINDOW['WIDTH']), x)
        y = max(-(GAME_AREA['HEIGHT'] - WINDOW['HEIGHT']), y)

        self.rect.topleft = (x, y)
