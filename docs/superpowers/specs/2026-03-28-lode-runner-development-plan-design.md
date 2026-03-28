# Lode Runner — Development Plan Design

**Date:** 2026-03-28
**Author:** orchestrator_pm_george
**Status:** Approved — ready for implementation planning
**Scope:** v1.0 full feature set (Must + Should)

---

## 1. Scope

All items in the v1.0 Must and Should categories from `docs/design-document.md §6`:

| # | Feature | Priority |
|---|---------|----------|
| 1 | All 150 original levels | Must |
| 2 | Full mechanics fidelity (all Apple II original behaviors) | Must |
| 3 | Level editor with immediate playtest | Must |
| 4 | HUD: score, lives, level number, gold remaining | Must |
| 5 | High score table (top 5 with initials, persisted) | Must |
| 6 | Background music + all sound effects (procedural synthesis) | Must |
| 7 | Direction-independent dig control option | Should |
| 8 | Hold-to-move control option | Should |
| 9 | Championship mode (50 Championship levels, alt scoring) | Should |

v1.5 and v2.0 features are explicitly out of scope.

---

## 2. Module Architecture

### File Responsibilities

```
constants.py        — All numeric tuning values, tile IDs, color hex values,
                      key bindings, timing constants. Nothing hardcoded elsewhere.

level.py            — Level class: load/save JSON tile grid (28×16), query tile
                      type by (col, row), mutate tiles (digging, hole lifecycle),
                      gold tracking, escape ladder state.

player.py           — Player class: full state machine (IDLE, RUNNING_LEFT/RIGHT,
                      CLIMBING_UP/DOWN, ROPE_LEFT/RIGHT, FALLING, DIGGING_LEFT/RIGHT,
                      DEAD), keyboard input processing, collision resolution
                      against Level.

enemy.py            — Enemy class: greedy heuristic AI state machine (SPAWNING,
                      CHASING, CARRYING, TRAPPED, CLIMBING_OUT, DEAD), all known
                      AI quirks (ladder loop, wall-ladder freeze, horizontal-first
                      priority), gold carrying/dropping behavior.

game.py             — GameState: owns Level + Player + list[Enemy] + score/lives
                      counter + hole timers. Drives the per-frame update loop.
                      Single source of truth — renderer, sound, and tests all
                      read from GameState rather than entity internals.

renderer.py         — Renderer: reads GameState each frame, draws tiles (with
                      animations), player sprite, enemy sprites, HUD, all menus
                      (title, pause, game over, level complete, high score).
                      Renders to 896×544 offscreen surface, scales to window.

sound_manager.py    — SoundManager: generates all waveforms at init using numpy +
                      pygame. Exposes play_event(name: str) API. No audio files —
                      all sounds synthesized procedurally.

main.py             — Entry point: pygame init, window setup, create GameState +
                      Renderer + SoundManager, run game loop.
```

### Interface Contract

`game.py` is the hub. All modules depend on `GameState` for read access. No module reaches into another module's internals. This contract enables safe parallel development — a module's internal implementation can change freely as long as its public interface to `GameState` is stable.

### Level Data Format

JSON files in `levels/` directory:

```json
{
  "level": 1,
  "grid": [[0,0,1,...], ...],
  "player_spawn": {"col": 3, "row": 12},
  "enemy_spawns": [{"col": 10, "row": 0}, ...],
  "escape_ladder_cols": [13, 14, 15]
}
```

Tile IDs match `constants.py`:
- 0 = EMPTY
- 1 = DIGGABLE_BRICK
- 2 = SOLID_BRICK
- 3 = LADDER
- 4 = ROPE
- 5 = GOLD
- 6 = HIDDEN_LADDER
- 7 = FALSE_BRICK
- 8 = HOLE_OPEN (runtime only)
- 9 = HOLE_FILLING (runtime only)

---

## 3. Sprint Plan

### Sprint 1 — Foundation
**Goal:** Blank pygame window displaying a static level. All subsequent sprints depend on this.

**Deliverables:**
- `constants.py` — complete with all tile IDs, colors, timing values, key bindings
- `level.py` — load/save JSON, tile query, tile mutation API
- `renderer.py` — static tile rendering only (no animation, no sprites)
- `main.py` — pygame init, window, game loop skeleton
- `levels/level_01.json` — level 1 hand-crafted as reference
- Level JSON schema documented
- Full unit tests for `level.py`

**Agents:** `python_developer` + `testing_expert` (parallel within sprint)
**Sequential:** Yes — all other sprints depend on this foundation.

---

### Sprint 2 — Player Movement & Physics
**Goal:** Player moves around level 1 correctly — running, climbing, rope traverse, falling, no jump.

**Deliverables:**
- `player.py` — full state machine, keyboard input, collision against Level
- Toggle-movement mode (Apple II authentic) as default
- Gravity and fall-safety implemented
- Renderer updated: player sprite (stick figure, 8 animation frames total)

**Agents:** `python_developer` (implementation) ‖ `testing_expert` (tests)
**Parallel:** Within sprint — testing_expert writes tests against the state machine spec while developer implements.

---

### Sprint 3 — Enemy AI + Digging System
**Goal:** Enemies chase the player. Player can dig holes. Enemies fall in and respawn.

**Deliverables (parallel tracks):**

**Track A — Enemy AI** (`python_developer_A`):
- `enemy.py` — full state machine + greedy heuristic pathfinding
- All AI quirks: ladder loop, wall-ladder freeze, horizontal-first priority
- Gold carrying/dropping behavior
- Enemy respawn at top row

**Track B — Digging System** (`python_developer_B`):
- Hole lifecycle in `level.py`: HOLE_OPEN → HOLE_FILLING → DIGGABLE_BRICK
- Dig constraints (no dig from rope, falling, or non-brick)
- Independent hole timers (no limit on simultaneous holes)
- Hole fill animation frames

**Agents:** 2× `python_developer` fully parallel + `testing_expert`

---

### Sprint 4 — Game Logic Complete
**Goal:** A full level is playable end-to-end — collect gold, escape, die, progress.

**Deliverables:**
- Gold pickup → `gold_remaining` counter → escape ladder reveal + fanfare
- Enemy gold-carry → drop in hole → player can collect
- Lives system: 5 start, +1 per level, -1 per death, game over at 0
- Scoring: 250/gold, 75/enemy trapped, 75/enemy killed, 1500/level
- Level progression: load next JSON, loop 1→150, game complete screen
- Level restart on death
- High score table: top 5 with initials, persisted to `highscores.json`

**Agents:** `python_developer` + `testing_expert` (parallel within sprint)

---

### Sprint 5 — Sound System
**Goal:** All game sounds and background music playing correctly.

**Deliverables** (`sound_manager.py`):
- All SFX: footstep, dig, gold pickup, enemy trap, enemy death, player death,
  escape ladder reveal, level complete, game over
- BGM: title theme, in-game loop, level complete jingle, game over sting
- `play_event(name)` API wired into `game.py` events
- Player-toggleable BGM (M key)
- All sounds procedurally synthesized (numpy + pygame, no audio files)

**Agents:** `sound_designer`
**Parallel:** SoundManager waveform generation and API can start in parallel with Sprint 4. The final wiring step (`game.py` calling `play_event()`) requires Sprint 4's `game.py` to exist — complete that step at the end of Sprint 5 after Sprint 4 merges.

---

### Sprint 6 — Full Renderer & UI
**Goal:** Game looks complete — animated tiles, character sprites, all screens.

**Deliverables** (`renderer.py` expansion):
- Animated tiles: diggable brick highlight/shadow, hole fill animation, gold shimmer
- Full player sprite set: all 8 animation states × frame counts per design doc
- Full enemy sprite set: CHASING, TRAPPED, CLIMBING_OUT, gold-carrying variant
- HUD: score, lives (as icons), level number, gold remaining count
- Title screen with controls display
- Pause screen
- Game over screen
- Level complete screen
- High score entry screen (initials input)
- Window scaling: 1×/2×/fullscreen with letterboxing
- Color palette exactly as specified in `docs/design-document.md §8.2`

**Agents:** `gui_expert`
**Parallel:** Fully parallel with Sprints 4 and 5.

---

### Sprint 7 — Level Editor
**Goal:** Built-in level editor — paint tiles, place spawns, playtest immediately.

**Deliverables:**

**Track A — Editor Logic** (`python_developer`):
- Editor mode in `game.py` / new `editor.py` module
- Tile palette state, cursor movement, tile placement
- Player/enemy spawn placement tools
- Save to JSON, load existing levels for editing
- Playtest: launch normal game from current editor state

**Track B — Editor UI** (`gui_expert`):
- Tile palette toolbar (left sidebar)
- Grid cursor highlight
- Spawn marker rendering
- Toolbar: New / Load / Save / Playtest buttons
- Level metadata panel (level number, title)

**Agents:** `python_developer` ‖ `gui_expert` (parallel within sprint)

---

### Sprint 8 — Level Content + Championship Mode
**Goal:** All 150 original levels exist as JSON. Championship mode selectable.

**Deliverables:**

**Track A — Level Data** (`technical_writer`):
- All 150 original level grids transcribed to JSON format
- All 50 Championship levels as JSON
- Validation: every level passes a completability check script

**Track B — Championship Mode** (`python_developer`):
- Game mode flag: CLASSIC (150 levels) vs CHAMPIONSHIP (50 levels)
- Championship scoring: 500/gold, 2000/escape, 100/enemy
- No level-skip in Championship mode
- Mode selection on title screen

**Agents:** `technical_writer` ‖ `python_developer` (parallel)

---

### Sprint 9 — Control Options + Polish + Performance
**Goal:** Game is fully polished and all control options work.

**Deliverables:**

**Track A — Control Options** (`python_developer`):
- Hold-to-move as alternative to toggle-movement (settings toggle)
- Direction-independent dig: Z always digs left, X always digs right (settings toggle)
- Settings persisted to `settings.json`

**Track B — Integration Testing** (`testing_expert`):
- Full end-to-end playthrough tests for levels 1, 9, 25, 42 (milestone levels)
- Regression suite covering all known AI quirks
- Performance: 60 fps confirmed on target hardware

**Track C — Performance** (`optimization_engineer`):
- Profile game loop for bottlenecks
- Optimize renderer surface caching
- Ensure hole timer logic scales to maximum simultaneous holes

**Agents:** `python_developer` ‖ `testing_expert` ‖ `optimization_engineer` (all parallel)

---

## 4. Code Review Gate

This process runs after **every sprint** before the next sprint begins.

### Process

```
Sprint Complete
     │
     ▼
code_reviewer agent
  • Reviews all files changed in the sprint
  • Posts findings as deliverable message to orchestrator_pm
  • Categorises each finding: MUST FIX / SHOULD FIX / NOTE
     │
     ▼
orchestrator_pm reviews findings
  • MUST FIX items → re-engage relevant specialist agent(s)
  • SHOULD FIX → orchestrator_pm decides: fix now or defer to backlog
  • NOTE → logged, no action required
     │
     ▼
Specialist(s) address findings
     │
     ▼
code_reviewer re-reviews changed files only (not full re-scan)
     │
     ▼ (repeat until no MUST FIX items remain)
     │
orchestrator_pm posts sprint approval → next sprint begins
```

### What code_reviewer Checks Per Sprint

| Check | Description |
|-------|-------------|
| Spec fidelity | Implementation matches `docs/game-spec.md` and `docs/design-document.md` |
| Interface contract | Module exposes what `game.py` hub pattern requires; no internal reach-through |
| Test coverage | New behaviors have tests; no obvious gaps |
| Constants discipline | No magic numbers inline — all in `constants.py` |
| Style | `ruff check` passes, 100-char line length, type hints on public functions |
| Integration risk | Anything that could break a downstream sprint flagged explicitly |

### Rules

- `code_reviewer` findings always go to `orchestrator_pm` — reviewer never blocks directly
- MUST FIX items block sprint advancement without exception
- SHOULD FIX and NOTE items are at orchestrator_pm's discretion
- Re-review is scoped to changed files only

---

## 5. AgentOps Protocol

All agents follow the standard lifecycle from `CLAUDE.md`:

1. **Register** under their own role slot (e.g. `PUT /agents/python_developer`) — never `orchestrator_pm`
2. **Announce** online with assigned name
3. **Heartbeat** at 0% / 33% / 66% / 100%
4. **Messages:** `task_assignment` on dispatch, `deliverable` on completion
5. **Idle** when done

Orchestrator checks for active agents before spawning to avoid duplicates. Usage metrics posted after every agent completion.

---

## 6. Definition of Done (Full Project)

- [ ] `uv run python main.py` launches the game with title screen
- [ ] All 150 classic levels playable in sequence
- [ ] All 50 Championship levels playable in Championship mode
- [ ] Level editor launches, allows tile painting, saves to JSON, playtests immediately
- [ ] All sounds and BGM play correctly (procedurally generated, no audio files)
- [ ] HUD displays score/lives/level/gold at all times
- [ ] High score table persists between sessions
- [ ] Hold-to-move and direction-independent dig toggleable in settings
- [ ] `uv run pytest tests/ -v` passes with no failures
- [ ] `uv run ruff check .` passes clean
- [ ] Runs at stable 60 fps on modern hardware
