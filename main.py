"""Lode Runner — entry point and main game loop."""

import sys

import pygame

import constants as C
from game import GamePhase, GameState
from renderer import Renderer


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Lode Runner")

    screen = pygame.display.set_mode((C.WINDOW_WIDTH, C.WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    game = GameState()
    renderer = Renderer(screen)

    running = True
    while running:
        dt = clock.tick(C.FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == C.KEY_PAUSE:
                    running = False
                else:
                    game.handle_event(event)

        game.update(dt)

        if game.phase == GamePhase.GAME_OVER:
            running = False  # Sprint 6 will add the game-over screen

        renderer.draw(game.level, game.player, game.enemies)
        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
