"""Lode Runner — entry point and main game loop."""

import sys

import pygame

import constants as C
from level import Level
from renderer import Renderer


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Lode Runner")

    screen = pygame.display.set_mode((C.WINDOW_WIDTH, C.WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    level = Level.from_file("levels/level_01.json")
    renderer = Renderer(screen)

    running = True
    while running:
        # Cap at 60fps; dt is elapsed seconds since last frame
        _dt = clock.tick(C.FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (C.KEY_PAUSE, pygame.K_q):
                    running = False

        renderer.draw(level)
        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
