"""Lode Runner — entry point and main game loop."""

import sys

import pygame

import constants as C
from level import Level
from player import Player
from renderer import Renderer


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Lode Runner")

    screen = pygame.display.set_mode((C.WINDOW_WIDTH, C.WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    level = Level.from_file("levels/level_01.json")
    player = Player(level.player_spawn.col, level.player_spawn.row)
    renderer = Renderer(screen)

    running = True
    while running:
        dt = clock.tick(C.FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (C.KEY_PAUSE,):
                    running = False
                else:
                    player.handle_event(event)

        if player.is_alive:
            player.update(dt, level)

        renderer.draw(level, player)
        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
