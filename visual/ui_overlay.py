from __future__ import annotations

import pygame

import config


class UIOverlay:
    def __init__(self) -> None:
        self.font = pygame.font.SysFont("consolas", 18)
        self.small_font = pygame.font.SysFont("consolas", 15)

    def draw(self, surface: pygame.Surface, lines: list[str]) -> None:
        y = 12
        for index, line in enumerate(lines):
            font = self.font if index < 2 else self.small_font
            color = config.TEXT_COLOR if index < 2 else config.MUTED_TEXT_COLOR
            rendered = font.render(line, True, color)
            surface.blit(rendered, (14, y))
            y += 24 if index < 2 else 20
