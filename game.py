"""Game state machine — owns level, player, enemies, score, lives, and phase transitions."""

from __future__ import annotations

from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING

import constants as C
from enemy import Enemy, EnemyState
from level import Level
from player import Player

if TYPE_CHECKING:
    from sound_manager import SoundManager


class GamePhase(Enum):
    TITLE = auto()
    PLAYING = auto()
    PAUSED = auto()
    PLAYER_DEAD = auto()
    LEVEL_COMPLETE = auto()
    GAME_OVER = auto()


class GameState:
    """Central game state: drives the update loop and owns all game objects."""

    def __init__(self, level_number: int = 1) -> None:
        self.level_number: int = level_number
        self.score: int = 0
        self.lives: int = C.STARTING_LIVES
        self.phase: GamePhase = GamePhase.TITLE
        self._phase_timer: float = 0.0
        self._pending_effects: list[dict] = []
        self._load_level()

    def start_game(self) -> None:
        """Transition from TITLE to PLAYING, resetting score/lives."""
        self._load_level()
        self.score = 0
        self.lives = C.STARTING_LIVES
        self.phase = GamePhase.PLAYING
        self._phase_timer = 0.0
        self._pending_effects.clear()

    def pause(self) -> None:
        """Pause during PLAYING."""
        if self.phase == GamePhase.PLAYING:
            self.phase = GamePhase.PAUSED

    def unpause(self) -> None:
        """Resume from PAUSED."""
        if self.phase == GamePhase.PAUSED:
            self.phase = GamePhase.PLAYING

    def drain_effects(self) -> list[dict]:
        """Return and clear the pending effects list."""
        effects = self._pending_effects.copy()
        self._pending_effects.clear()
        return effects

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

    def update(self, dt: float, sound_manager: "SoundManager | None" = None) -> None:
        """Advance game state by dt seconds."""
        if self.phase == GamePhase.PLAYING:
            self._update_playing(dt, sound_manager)
        elif self.phase == GamePhase.PLAYER_DEAD:
            self._update_player_dead(dt, sound_manager)
        elif self.phase == GamePhase.LEVEL_COMPLETE:
            self._update_level_complete(dt, sound_manager)
        # TITLE, PAUSED, GAME_OVER: no per-frame updates

    def _update_playing(self, dt: float, sm: "SoundManager | None" = None) -> None:
        hole_count_before = len(self.level._holes)
        if self.player.is_alive:
            self.player.update(dt, self.level)
        self.level.update_holes(dt)
        hole_count_after = len(self.level._holes)

        if sm and hole_count_after > hole_count_before:
            sm.play_event("dig")

        for enemy in self.enemies:
            old_state = enemy.state
            enemy.update(dt, self.level, self.player)
            self._check_enemy_score(old_state, enemy, sm)
        self._check_gold_pickup(sm)
        self._check_player_collision(sm)
        self._check_level_complete(sm)

        if sm:
            sm.play_bgm("bgm_game")

    def _update_player_dead(self, dt: float, sm: "SoundManager | None" = None) -> None:
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
                if sm:
                    sm.play_event("game_over")
                    sm.play_bgm("bgm_game_over")
            else:
                self._load_level()
                self.phase = GamePhase.PLAYING
                self._phase_timer = 0.0

    def _update_level_complete(self, dt: float, sm: "SoundManager | None" = None) -> None:
        self._phase_timer += dt
        if self._phase_timer >= C.LEVEL_COMPLETE_DELAY:
            self.level_number += 1
            self._load_level()
            self.phase = GamePhase.PLAYING
            self._phase_timer = 0.0

    def _check_gold_pickup(self, sm: "SoundManager | None" = None) -> None:
        """Collect gold if player occupies a GOLD tile."""
        if not self.player.is_alive:
            return
        if self.level.get_tile(self.player.col, self.player.row) == C.GOLD:
            self.level.set_tile(self.player.col, self.player.row, C.EMPTY)
            self.score += C.SCORE_GOLD
            self.gold_remaining -= 1
            self._pending_effects.append(
                {"type": "gold_collected", "col": self.player.col, "row": self.player.row}
            )
            if sm:
                sm.play_event("gold_pickup")
            if self.gold_remaining <= 0:
                self.gold_remaining = 0
                self.level.reveal_escape_ladder()
                self._pending_effects.append({"type": "ladder_reveal"})
                if sm:
                    sm.play_event("ladder_reveal")

    def _check_player_collision(self, sm: "SoundManager | None" = None) -> None:
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
                self._pending_effects.append({"type": "player_death"})
                if sm:
                    sm.play_event("player_death")
                return

    def _check_enemy_score(
        self, old_state: EnemyState, enemy: Enemy, sm: "SoundManager | None" = None
    ) -> None:
        """Award points for enemy state transitions."""
        if old_state != EnemyState.TRAPPED and enemy.state == EnemyState.TRAPPED:
            self.score += C.SCORE_ENEMY_TRAPPED
            if sm:
                sm.play_event("enemy_trap")
        elif old_state == EnemyState.TRAPPED and enemy.state == EnemyState.DEAD:
            self.score += C.SCORE_ENEMY_KILLED
            if sm:
                sm.play_event("enemy_death")

    def _check_level_complete(self, sm: "SoundManager | None" = None) -> None:
        """Detect when player reaches the escape ladder at the top of the level."""
        if self.gold_remaining > 0:
            return
        if not self.player.is_alive:
            return
        if self.player.col in self.level.escape_ladder_cols and self.player.row == 0:
            self.score += C.SCORE_LEVEL_COMPLETE
            self.lives += C.LIVES_PER_LEVEL
            self.phase = GamePhase.LEVEL_COMPLETE
            self._phase_timer = 0.0
            self._pending_effects.append({"type": "level_complete"})
            if sm:
                sm.play_event("level_complete")
                sm.play_bgm("bgm_level_complete")
