"""Game state machine — owns level, player, enemies, score, lives, and phase transitions."""

from __future__ import annotations

from enum import Enum, auto
from pathlib import Path

import constants as C
from enemy import Enemy, EnemyState
from level import Level
from player import Player


class GamePhase(Enum):
    PLAYING = auto()
    PLAYER_DEAD = auto()
    LEVEL_COMPLETE = auto()
    GAME_OVER = auto()


class GameState:
    """Central game state: drives the update loop and owns all game objects."""

    def __init__(self, level_number: int = 1) -> None:
        self.level_number: int = level_number
        self.score: int = 0
        self.lives: int = C.STARTING_LIVES
        self.phase: GamePhase = GamePhase.PLAYING
        self._phase_timer: float = 0.0
        self._load_level()

    def _load_level(self) -> None:
        """Load the current level_number. Falls back to level 1 if file missing."""
        path = f"levels/level_{self.level_number:02d}.json"
        if not Path(path).exists():
            self.level_number = 1
            path = "levels/level_01.json"
        self.level = Level.from_file(path)
        self.gold_remaining: int = len(self.level.gold_positions())
        self.player = Player(self.level.player_spawn.col, self.level.player_spawn.row)
        self.enemies: list[Enemy] = [Enemy(sp.col, sp.row) for sp in self.level.enemy_spawns]

    def handle_event(self, event: object) -> None:
        """Route input events to the player (only during PLAYING phase)."""
        if self.phase == GamePhase.PLAYING:
            self.player.handle_event(event)  # type: ignore[arg-type]

    def update(self, dt: float) -> None:
        """Advance game state by dt seconds."""
        if self.phase == GamePhase.PLAYING:
            self._update_playing(dt)
        elif self.phase == GamePhase.PLAYER_DEAD:
            self._update_player_dead(dt)
        elif self.phase == GamePhase.LEVEL_COMPLETE:
            self._update_level_complete(dt)
        # GAME_OVER: no per-frame updates

    def _update_playing(self, dt: float) -> None:
        if self.player.is_alive:
            self.player.update(dt, self.level)
        self.level.update_holes(dt)
        for enemy in self.enemies:
            old_state = enemy.state
            enemy.update(dt, self.level, self.player)
            self._check_enemy_score(old_state, enemy)
        self._check_gold_pickup()
        self._check_player_collision()
        # Note: _check_level_complete is added in Task 5

    def _update_player_dead(self, dt: float) -> None:
        self.level.update_holes(dt)
        for enemy in self.enemies:
            enemy.update(dt, self.level, self.player)
        self._phase_timer += dt
        if self._phase_timer >= C.DEATH_DISPLAY_TIME:
            self.lives -= 1
            if self.lives <= 0:
                self.lives = 0
                self.phase = GamePhase.GAME_OVER
                self._phase_timer = 0.0
            else:
                self._load_level()
                self.phase = GamePhase.PLAYING
                self._phase_timer = 0.0

    def _update_level_complete(self, dt: float) -> None:
        self._phase_timer += dt
        if self._phase_timer >= C.LEVEL_COMPLETE_DELAY:
            self.level_number += 1
            self._load_level()
            self.phase = GamePhase.PLAYING
            self._phase_timer = 0.0

    def _check_gold_pickup(self) -> None:
        """Collect gold if player occupies a GOLD tile."""
        if not self.player.is_alive:
            return
        if self.level.get_tile(self.player.col, self.player.row) == C.GOLD:
            self.level.set_tile(self.player.col, self.player.row, C.EMPTY)
            self.score += C.SCORE_GOLD
            self.gold_remaining -= 1
            if self.gold_remaining <= 0:
                self.gold_remaining = 0
                self.level.reveal_escape_ladder()

    def _check_player_collision(self) -> None:
        """Kill player if any live enemy occupies the same tile."""
        if not self.player.is_alive:
            return
        for enemy in self.enemies:
            if enemy.state in (EnemyState.DEAD, EnemyState.TRAPPED):
                continue
            if enemy.col == self.player.col and enemy.row == self.player.row:
                self.player.kill()
                self.phase = GamePhase.PLAYER_DEAD
                self._phase_timer = 0.0
                return

    def _check_enemy_score(self, old_state: EnemyState, enemy: Enemy) -> None:
        """Award points for enemy state transitions."""
        if old_state != EnemyState.TRAPPED and enemy.state == EnemyState.TRAPPED:
            self.score += C.SCORE_ENEMY_TRAPPED
        elif old_state == EnemyState.TRAPPED and enemy.state == EnemyState.DEAD:
            self.score += C.SCORE_ENEMY_KILLED
