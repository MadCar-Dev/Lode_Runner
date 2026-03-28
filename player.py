"""Player entity — state machine, input handling, and physics."""
from __future__ import annotations

from enum import Enum, auto

import pygame

import constants as C
from level import Level


class PlayerState(Enum):
    IDLE = auto()
    RUNNING_LEFT = auto()
    RUNNING_RIGHT = auto()
    CLIMBING_UP = auto()
    CLIMBING_DOWN = auto()
    ROPE_LEFT = auto()
    ROPE_RIGHT = auto()
    FALLING = auto()
    DEAD = auto()


class Player:
    def __init__(self, col: int, row: int) -> None:
        self.x: float = float(col * C.TILE_SIZE)
        self.y: float = float(row * C.TILE_SIZE)
        self.state: PlayerState = PlayerState.IDLE
        self.facing: int = 1        # 1 = right, -1 = left
        self._h_dir: int = 0        # -1=left, 0=none, +1=right (toggle input)
        self._v_dir: int = 0        # -1=up, 0=none, +1=down (toggle input)
        self.anim_frame: int = 0
        self._anim_timer: float = 0.0

    @property
    def col(self) -> int:
        return int(self.x / C.TILE_SIZE)

    @property
    def row(self) -> int:
        return int(self.y / C.TILE_SIZE)

    @property
    def is_alive(self) -> bool:
        return self.state != PlayerState.DEAD

    def handle_event(self, event: pygame.event.Event) -> None:
        """Process a pygame KEYDOWN event for toggle-movement mode."""
        ...

    def update(self, dt: float, level: Level) -> None:
        """Advance player physics and state for one frame."""
        ...

    def kill(self) -> None:
        """Transition player to DEAD state immediately."""
        ...

    # --- private helpers ---

    def _is_on_floor(self, level: Level) -> bool:
        """True when y is tile-aligned and tile directly below is standable."""
        ...

    def _is_on_ladder(self, level: Level) -> bool:
        """True when x is tile-aligned and current tile is a ladder."""
        ...

    def _is_on_rope(self, level: Level) -> bool:
        """True when current tile is a rope."""
        ...

    def _snap_x(self) -> None:
        """Snap x to nearest tile boundary."""
        ...

    def _snap_y(self) -> None:
        """Snap y to nearest tile boundary."""
        ...

    def _move_horizontal(self, dx: float, level: Level) -> bool:
        """Move by dx pixels, blocked by solid tiles. Returns True if any movement occurred."""
        ...

    def _move_vertical(self, dy: float, level: Level) -> None:
        """Move by dy pixels vertically, blocked by solid tiles above."""
        ...

    def _apply_gravity(self, dt: float, level: Level) -> None:
        """Apply downward gravity; snap to floor on landing."""
        ...

    def _update_anim(self, dt: float) -> None:
        """Advance animation frame counter."""
        ...

    def _handle_rope(self, dt: float, level: Level) -> None: ...
    def _handle_climbing(self, dt: float, level: Level) -> None: ...
    def _handle_floor(self, dt: float, level: Level) -> None: ...
    def _handle_falling(self, dt: float, level: Level) -> None: ...
