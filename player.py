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
        self.facing: int = 1
        self._h_dir: int = 0
        self._v_dir: int = 0
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

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        """Process KEYDOWN for toggle-movement mode. KEYUP is ignored."""
        if event.type != pygame.KEYDOWN:
            return
        key = event.key
        if key in (C.KEY_LEFT, C.KEY_ALT_LEFT):
            self._h_dir = -1 if self._h_dir != -1 else 0
        elif key in (C.KEY_RIGHT, C.KEY_ALT_RIGHT):
            self._h_dir = 1 if self._h_dir != 1 else 0
        elif key in (C.KEY_UP, C.KEY_ALT_UP):
            self._v_dir = -1 if self._v_dir != -1 else 0
        elif key in (C.KEY_DOWN, C.KEY_ALT_DOWN):
            self._v_dir = 1 if self._v_dir != 1 else 0

    def update(self, dt: float, level: Level) -> None:
        """Advance player physics and state for one frame."""
        if self.state == PlayerState.DEAD:
            return
        on_rope = self._is_on_rope(level)
        on_ladder = self._is_on_ladder(level)
        on_floor = self._is_on_floor(level)

        if on_rope:
            self._handle_rope(dt, level)
        elif on_ladder and self._v_dir != 0:
            self._handle_climbing(dt, level)
        elif on_floor:
            self._handle_floor(dt, level)
        else:
            self._handle_falling(dt, level)

        self._update_anim(dt)

    def kill(self) -> None:
        self.state = PlayerState.DEAD

    # ------------------------------------------------------------------
    # State handlers
    # ------------------------------------------------------------------

    def _handle_rope(self, dt: float, level: Level) -> None:
        self._snap_y()
        if self._h_dir == -1:
            self._move_horizontal(-C.PLAYER_ROPE_SPEED * C.TILE_SIZE * dt, level)
            self.state = PlayerState.ROPE_LEFT
            self.facing = -1
        elif self._h_dir == 1:
            self._move_horizontal(C.PLAYER_ROPE_SPEED * C.TILE_SIZE * dt, level)
            self.state = PlayerState.ROPE_RIGHT
            self.facing = 1
        else:
            self.state = PlayerState.IDLE
        if not self._is_on_rope(level):
            self.state = PlayerState.FALLING

    def _handle_climbing(self, dt: float, level: Level) -> None:
        self._snap_x()
        if self._v_dir == -1:
            self._move_vertical(-C.PLAYER_CLIMB_SPEED * C.TILE_SIZE * dt, level)
            self.state = PlayerState.CLIMBING_UP
        else:
            self._move_vertical(C.PLAYER_CLIMB_SPEED * C.TILE_SIZE * dt, level)
            self.state = PlayerState.CLIMBING_DOWN
        if not self._is_on_ladder(level):
            self.state = PlayerState.IDLE

    def _handle_floor(self, dt: float, level: Level) -> None:
        self._snap_y()
        if self._h_dir == -1:
            moved = self._move_horizontal(-C.PLAYER_RUN_SPEED * C.TILE_SIZE * dt, level)
            self.state = PlayerState.RUNNING_LEFT if moved else PlayerState.IDLE
            if moved:
                self.facing = -1
        elif self._h_dir == 1:
            moved = self._move_horizontal(C.PLAYER_RUN_SPEED * C.TILE_SIZE * dt, level)
            self.state = PlayerState.RUNNING_RIGHT if moved else PlayerState.IDLE
            if moved:
                self.facing = 1
        else:
            self.state = PlayerState.IDLE
        if self.state in (PlayerState.RUNNING_LEFT, PlayerState.RUNNING_RIGHT):
            if not self._is_on_floor(level) and not self._is_on_rope(level):
                self.state = PlayerState.FALLING

    def _handle_falling(self, dt: float, level: Level) -> None:
        self.state = PlayerState.FALLING
        self._apply_gravity(dt, level)
        if self._is_on_rope(level):
            self.state = PlayerState.IDLE
            self._snap_y()
        elif self._is_on_ladder(level) and self.state == PlayerState.FALLING:
            self.state = PlayerState.IDLE

    # ------------------------------------------------------------------
    # Support detection
    # ------------------------------------------------------------------

    def _is_on_floor(self, level: Level) -> bool:
        if self.y % C.TILE_SIZE > C.TILE_SNAP_TOLERANCE:
            return False
        return level.is_standable(self.col, self.row + 1)

    def _is_on_ladder(self, level: Level) -> bool:
        if self.x % C.TILE_SIZE > C.TILE_SNAP_TOLERANCE:
            return False
        return level.is_ladder(self.col, self.row)

    def _is_on_rope(self, level: Level) -> bool:
        return level.is_rope(self.col, self.row)

    # ------------------------------------------------------------------
    # Movement primitives
    # ------------------------------------------------------------------

    def _snap_x(self) -> None:
        self.x = float(round(self.x / C.TILE_SIZE) * C.TILE_SIZE)

    def _snap_y(self) -> None:
        self.y = float(round(self.y / C.TILE_SIZE) * C.TILE_SIZE)

    def _move_horizontal(self, dx: float, level: Level) -> bool:
        target_x = self.x + dx
        if dx > 0:
            cur_right = int(self.x) + C.TILE_SIZE - 1
            new_right = int(target_x) + C.TILE_SIZE - 1
            cur_right_col = cur_right // C.TILE_SIZE
            new_right_col = new_right // C.TILE_SIZE
            if new_right_col > cur_right_col and level.is_solid(new_right_col, self.row):
                target_x = float(new_right_col * C.TILE_SIZE - C.TILE_SIZE)
        elif dx < 0:
            cur_left_col = int(self.x) // C.TILE_SIZE
            new_left_col = int(target_x) // C.TILE_SIZE
            if new_left_col < cur_left_col and level.is_solid(new_left_col, self.row):
                target_x = float((new_left_col + 1) * C.TILE_SIZE)
        target_x = max(0.0, min(target_x, float((C.GRID_COLS - 1) * C.TILE_SIZE)))
        moved = abs(target_x - self.x) > 0.001
        self.x = target_x
        return moved

    def _move_vertical(self, dy: float, level: Level) -> None:
        target_y = self.y + dy
        if dy < 0:
            cur_top_row = int(self.y) // C.TILE_SIZE
            new_top_row = int(target_y) // C.TILE_SIZE
            if new_top_row < cur_top_row and level.is_solid(self.col, new_top_row):
                target_y = float((new_top_row + 1) * C.TILE_SIZE)
        target_y = max(0.0, min(target_y, float((C.GRID_ROWS - 1) * C.TILE_SIZE)))
        self.y = target_y

    def _apply_gravity(self, dt: float, level: Level) -> None:
        dy = C.PLAYER_FALL_SPEED * C.TILE_SIZE * dt
        target_y = self.y + dy
        old_bottom_row = (int(self.y) + C.TILE_SIZE) // C.TILE_SIZE
        new_bottom_row = (int(target_y) + C.TILE_SIZE) // C.TILE_SIZE
        if new_bottom_row > old_bottom_row and level.is_standable(self.col, new_bottom_row):
            target_y = float((new_bottom_row - 1) * C.TILE_SIZE)
            self.state = PlayerState.IDLE
            self._v_dir = 0
        self.y = min(target_y, float((C.GRID_ROWS - 1) * C.TILE_SIZE))

    def _update_anim(self, dt: float) -> None:
        self._anim_timer += dt
        if self._anim_timer >= 1.0 / C.PLAYER_ANIM_FPS:
            self._anim_timer -= 1.0 / C.PLAYER_ANIM_FPS
            self.anim_frame = (self.anim_frame + 1) % 8
