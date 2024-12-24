import pygame

from src.constants import COLORS


class FloatingText(pygame.sprite.Sprite):
    def __init__(
        self,
        x: int,
        y: int,
        text: str,
        color: tuple[int, int, int],
        font: pygame.font.Font,
    ) -> None:
        super().__init__()
        self.font = font
        self.text = str(text)
        self.color = color
        self.outline_color = COLORS['BLACK']
        self.outline_width = 0.1
        self.create_image()
        self.rect = self.image.get_rect(center=(x, y))
        self.creation_time = pygame.time.get_ticks()
        self.duration = 1750
        self.fade_duration = 500
        self.y_speed = -2
        self.alpha = 255

    def create_image(self) -> None:
        outline_surface = self.font.render(self.text, True, self.outline_color)
        outline_rect = outline_surface.get_rect()
        self.image = pygame.Surface(
            (
                outline_rect.width + self.outline_width * 2,
                outline_rect.height + self.outline_width * 2,
            ),
            pygame.SRCALPHA,
        )

        for dx, dy in [
            (-1, -1),
            (-1, 1),
            (1, -1),
            (1, 1),
            (-1, 0),
            (1, 0),
            (0, -1),
            (0, 1),
        ]:
            self.image.blit(
                outline_surface, (self.outline_width + dx, self.outline_width + dy)
            )

        text_surface = self.font.render(self.text, True, self.color)
        self.image.blit(text_surface, (self.outline_width, self.outline_width))

    def update(self) -> None:
        self.rect.y += self.y_speed

        current_time = pygame.time.get_ticks()
        elapsed_time = current_time - self.creation_time

        if elapsed_time > self.duration:
            fade_progress = min(1, (elapsed_time - self.duration) / self.fade_duration)
            self.alpha = int(255 * (1 - fade_progress))
            self.image.set_alpha(self.alpha)

            if fade_progress >= 1:
                self.kill()
