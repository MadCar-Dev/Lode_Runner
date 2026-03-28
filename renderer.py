"""Renderer — draws game state to a pygame surface each frame."""

from __future__ import annotations

import pygame

import constants as C
from level import Level


class Renderer:
    """Draws the current game state. Sprint 1: static tiles only."""

    def __init__(self, screen: pygame.Surface) -> None:
        self._screen = screen
        # Offscreen surface at native resolution; scaled to window on flip
        self._surface = pygame.Surface((C.WINDOW_WIDTH, C.WINDOW_HEIGHT))
        pygame.font.init()
        self._font = pygame.font.SysFont("monospace", 14)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def draw(self, level: Level) -> None:
        """Draw the full frame: clear → tiles → HUD → blit to screen."""
        self._surface.fill(C.COLOR_BACKGROUND)
        self._draw_tiles(level)
        self._draw_hud()
        # Scale offscreen surface to actual screen size
        if self._screen.get_size() != (C.WINDOW_WIDTH, C.WINDOW_HEIGHT):
            scaled = pygame.transform.scale(self._surface, self._screen.get_size())
            self._screen.blit(scaled, (0, 0))
        else:
            self._screen.blit(self._surface, (0, 0))

    # ------------------------------------------------------------------
    # Tile drawing
    # ------------------------------------------------------------------

    def _draw_tiles(self, level: Level) -> None:
        for row in range(C.GRID_ROWS):
            for col in range(C.GRID_COLS):
                tile = level.get_tile(col, row)
                x = col * C.TILE_SIZE
                y = row * C.TILE_SIZE + C.HUD_HEIGHT
                self._draw_tile(tile, x, y)

    def _draw_tile(self, tile_id: int, x: int, y: int) -> None:
        ts = C.TILE_SIZE
        rect = pygame.Rect(x, y, ts, ts)

        if tile_id == C.SOLID_BRICK:
            pygame.draw.rect(self._surface, C.COLOR_SOLID_BRICK, rect)

        elif tile_id in (C.DIGGABLE_BRICK, C.FALSE_BRICK):
            # FALSE_BRICK looks identical to DIGGABLE_BRICK — that's intentional
            pygame.draw.rect(self._surface, C.COLOR_DIGGABLE_BRICK, rect)
            # Top-left highlight edge
            pygame.draw.line(self._surface, C.COLOR_DIGGABLE_HIGHLIGHT,
                             (x, y), (x + ts - 1, y))
            pygame.draw.line(self._surface, C.COLOR_DIGGABLE_HIGHLIGHT,
                             (x, y), (x, y + ts - 1))
            # Bottom-right shadow edge
            pygame.draw.line(self._surface, C.COLOR_DIGGABLE_SHADOW,
                             (x + ts - 1, y), (x + ts - 1, y + ts - 1))
            pygame.draw.line(self._surface, C.COLOR_DIGGABLE_SHADOW,
                             (x, y + ts - 1), (x + ts - 1, y + ts - 1))
            # Mortar line (horizontal, centered)
            pygame.draw.line(self._surface, C.COLOR_DIGGABLE_SHADOW,
                             (x, y + ts // 2), (x + ts - 1, y + ts // 2))

        elif tile_id == C.LADDER:
            # Two vertical rails + horizontal rungs
            rail_x1 = x + ts // 4
            rail_x2 = x + (ts * 3) // 4
            pygame.draw.line(self._surface, C.COLOR_LADDER,
                             (rail_x1, y), (rail_x1, y + ts - 1))
            pygame.draw.line(self._surface, C.COLOR_LADDER,
                             (rail_x2, y), (rail_x2, y + ts - 1))
            # Four rungs evenly spaced
            for i in range(4):
                rung_y = y + (ts * i) // 4 + ts // 8
                pygame.draw.line(self._surface, C.COLOR_LADDER,
                                 (rail_x1, rung_y), (rail_x2, rung_y))

        elif tile_id == C.ROPE:
            # Horizontal line at 1/3 height + knots every 8px
            rope_y = y + ts // 3
            pygame.draw.line(self._surface, C.COLOR_ROPE,
                             (x, rope_y), (x + ts - 1, rope_y), 2)
            for kx in range(x + 4, x + ts, 8):
                pygame.draw.circle(self._surface, C.COLOR_ROPE, (kx, rope_y), 2)

        elif tile_id == C.GOLD:
            # Diamond shape
            cx, cy = x + ts // 2, y + ts // 2
            r = ts // 5
            points = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
            pygame.draw.polygon(self._surface, C.COLOR_GOLD, points)
            # Glint
            pygame.draw.circle(self._surface, C.COLOR_GOLD_GLINT,
                                (cx - r // 2, cy - r // 2), 2)

        elif tile_id == C.HIDDEN_LADDER:
            pass  # Renders as empty space — invisible until revealed

        elif tile_id == C.HOLE_OPEN:
            pass  # Void — background shows through

        elif tile_id == C.HOLE_FILLING:
            # Partial brick closing in — drawn as two inward rectangles
            progress = 0.5  # Sprint 1: static midpoint; animated in Sprint 3
            fill_w = int(ts * progress * 0.5)
            pygame.draw.rect(self._surface, C.COLOR_DIGGABLE_BRICK,
                             pygame.Rect(x, y, fill_w, ts))
            pygame.draw.rect(self._surface, C.COLOR_DIGGABLE_BRICK,
                             pygame.Rect(x + ts - fill_w, y, fill_w, ts))

        # EMPTY: draw nothing (background color already filled)

    # ------------------------------------------------------------------
    # HUD
    # ------------------------------------------------------------------

    def _draw_hud(self) -> None:
        hud_rect = pygame.Rect(0, 0, C.WINDOW_WIDTH, C.HUD_HEIGHT)
        pygame.draw.rect(self._surface, C.COLOR_HUD_BG, hud_rect)
        label = self._font.render("LODE RUNNER  |  Sprint 1 Foundation", True,
                                  C.COLOR_HUD_TEXT)
        self._surface.blit(label, (8, 8))
