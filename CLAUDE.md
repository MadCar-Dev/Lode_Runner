# Lode Runner

Recreation and modernization of the classic 1983 Lode Runner arcade game in Python/Pygame. Also serves as a test bed for mcc-agentops multi-agent orchestration.

## Game Overview

Lode Runner is a 2D platformer where the player collects all gold on a level while avoiding enemies, then escapes via a ladder that appears at the top. The player can dig holes in brick floors to trap enemies temporarily. The original featured 150 hand-crafted levels and a built-in level editor.

## Development Commands

**Package manager: uv -- NEVER pip**

```bash
# First-time setup
uv venv && uv sync

# Run the game
uv run python main.py

# Run all tests
uv run pytest tests/

# Run a single test file
uv run pytest tests/test_player.py

# Run with verbose output
uv run pytest tests/ -v

# Lint and format
uv run ruff check .
uv run ruff format .

# Add a dependency
uv add <package>
```

## Architecture

### Core Game Elements

- **Player** — Runs left/right, climbs ladders, traverses hand-over-hand on bars, digs holes left/right in brick floors
- **Enemies** — Chase the player using pathfinding AI, fall into dug holes, regenerate after being trapped
- **Gold** — Collectibles scattered across each level; all must be collected to complete the level
- **Terrain** — Brick (diggable), solid (indestructible), ladders, bars (monkey bars), empty space
- **Escape ladder** — Appears at the top of the screen when all gold is collected

### Key Mechanics

- **Gravity** — Player and enemies fall when unsupported (no floor, ladder, or bar beneath)
- **Digging** — Player digs holes in brick one tile left or right; holes fill back in after a timer
- **Enemy AI** — Enemies path toward the player, can climb ladders, and fall into holes
- **Trapped enemies** — When an enemy falls in a hole, it's stuck until the hole fills; if still in the hole when it fills, the enemy dies and respawns
- **Level progression** — 150 levels with increasing difficulty

### Project Structure

```
main.py              # Entry point and game loop
game.py              # Game state machine
player.py            # Player entity and controls
enemy.py             # Enemy entity and AI
level.py             # Level loading, terrain, tile map
constants.py         # All game constants and tuning values
renderer.py          # Drawing and display
sound_manager.py     # Procedural audio (no audio files)
tests/               # pytest test suite
levels/              # Level data files
```

### Conventions

- **Coordinates:** Tile-based grid, origin top-left
- **Rendering:** Retro pixel art style using Pygame surfaces, no external sprite assets
- **Audio:** All sounds procedurally generated — no audio files
- **Constants:** All numeric values in `constants.py` — change balance there, not in entity files
- **Python:** 3.12+, type hints, 100 char line length, ruff for linting

## AgentOps Integration

- **URL:** `http://vampire:8600/api/v1`
- **API Key:** `BaileyDog`
- **Project ID:** `ada23f3c-cc81-4f2c-b88d-f742cc030ee0`
- **Auth header:** `Authorization: Bearer BaileyDog`

### Assigned Agents

| Role Slot | Definition | When to Use |
|-----------|------------|-------------|
| `orchestrator_pm` | Lead Orchestrator / PM | SDLC pipeline manager — dispatches, validates, routes. Never produces artifacts. |
| `sprint_planner` | Sprint Planner | Produces dependency-classified task waves from design docs. Dispatch BEFORE implementation. |
| `solutions_architect` | Solutions Architect | Defines module interfaces, data flow, technical decisions. Dispatch BEFORE sprint planning. |
| `game_designer` | Game Designer | Mechanics design, balance tuning, feature specs. Research + design phases. |
| `ux_designer` | UX Designer | Controls tuning, game feel, feedback systems, UI flow. Design + post-sprint review. |
| `python_developer` | Python Developer | All implementation code. TDD: tests first, then implementation. |
| `gui_expert` | GUI Expert | Rendering, visual design, Pygame surfaces, HUD layout. |
| `testing_expert` | Testing Expert | Unit tests and TDD test suites. NOT spec compliance (that's qa_engineer). |
| `qa_engineer` | QA Engineer | Integration testing, spec compliance, acceptance testing. Post-implementation. |
| `code_reviewer` | Code Reviewer | Code quality gate. Reviews git diffs, not entire files. One review per sprint. |
| `level_designer` | Level Designer | Tile layouts, enemy placement, gold distribution, difficulty curves. |
| `sound_designer` | Sound Designer | Procedural audio — all sounds synthesized via numpy, no audio files. |
| `code_optimizer` | Code Optimizer | Refactoring for readability/DRY/simplicity without changing behavior. |
| `devops_engineer` | DevOps Engineer | CI/CD, deployment, builds, release management. |
| `technical_writer` | Technical Writer | READMEs, specs, design docs, architecture decision records. |

### Agent Lifecycle

1. **Register** -- PUT to `.../agents/<role-slot>` with `{"status": "active", "phase": "..."}`. API returns `agent_name` with human suffix (e.g. `python_developer_alice`). **Use that name for all subsequent calls.** Write the name to the per-worktree state file: `echo "<agent_name>" > .claude/agentops-agent-name` (creates `.claude/` dir if needed). The automatic heartbeat hook reads this file.
2. **Announce** -- Output: `> Agent online: **python_developer_alice** (role: python_developer, phase: planning)`
3. **Progress heartbeats** -- POST to `.../agents/<assigned-name>/heartbeat` with `progress_pct` at these mandatory milestones. The automatic hook handles alive-pings between milestones, but does NOT set progress — you must call these explicitly:
   - `0%` -- immediately after registering (started)
   - `33%` -- reading spec / planning approach
   - `66%` -- core implementation done, running tests
   - `100%` -- verified and done, about to idle
4. **Messages** -- Mandatory at two points:
   - **Orchestrator -> worker** (type `task_assignment`) when dispatching a subagent
   - **Worker -> orchestrator** (type `deliverable`) when task is complete
5. **Idle** -- PUT with `{"status": "idle"}` when done.

```bash
# Register (returns assigned name with suffix)
curl -s -X PUT http://vampire:8600/api/v1/projects/ada23f3c-cc81-4f2c-b88d-f742cc030ee0/agents/<role-slot> \
  -H "Authorization: Bearer BaileyDog" -H "Content-Type: application/json" \
  -d '{"status": "active", "phase": "planning", "model": "<your-model-short-name>"}'
# -> save returned agent_name, then:
mkdir -p .claude && echo "<agent_name>" > .claude/agentops-agent-name

# Progress heartbeat (use assigned name, not role-slot)
curl -s -X POST http://vampire:8600/api/v1/projects/ada23f3c-cc81-4f2c-b88d-f742cc030ee0/agents/<assigned-name>/heartbeat \
  -H "Authorization: Bearer BaileyDog" -H "Content-Type: application/json" \
  -d '{"progress_pct": 33, "current_task": "Reading spec and planning approach"}'

# Post message
curl -s -X POST http://vampire:8600/api/v1/projects/ada23f3c-cc81-4f2c-b88d-f742cc030ee0/messages \
  -H "Authorization: Bearer BaileyDog" -H "Content-Type: application/json" \
  -d '{"from_agent": "<assigned-name>", "to_agents": ["<target-role>"], "message_type": "deliverable", "subject": "...", "body": "...", "priority": "normal"}'
```

### Init Commands

**`/io`** -- Bootstrap orchestrator_pm mode. Registers, loads team, checks active agents and recent messages, asks for direction.

**`/init <role-slot>`** -- Register with given role, check for pending assignments, report in, heartbeat after every task.

### Spawning Parallel Worker Agents

When the orchestrator spawns subagents via the Agent tool:

1. **Check existing agents first** -- GET `.../agents` and confirm no active/idle agents of that role already exist before registering new ones
2. **Register each separately** before dispatching -- each PUT returns a unique name
3. **Post a `task_assignment` message** to the worker's role slot immediately after registering
4. **Pass the assigned name and worktree path** into the subagent prompt
5. **Each subagent writes its name** to `.claude/agentops-agent-name` in its worktree root

### Maximizing Parallelism (IMPORTANT)

The orchestrator MUST dispatch independent tasks simultaneously, not sequentially. This is
the single biggest efficiency lever — sequential dispatch wastes wall-clock time.

**Before dispatching a sprint's tasks, classify dependencies:**
- Tasks touching different files with no imports between them → **parallel**
- TDD tests + implementation of the same module → **sequential** (tests first)
- Integration task that imports from other sprint tasks → **sequential** (after dependencies)

**Example sprint plan:**
```
Sprint 2: Player Movement
  Wave 1 (parallel): constants.py additions + player.py tests (TDD)
  Wave 2 (parallel): player.py implementation + renderer.py player drawing
  Wave 3 (sequential): main.py integration (depends on wave 1+2)
  Wave 4: code review gate
```

**Dispatch all tasks in a wave as a single message with multiple Agent tool calls.**
Use `isolation: "worktree"` for each to avoid file conflicts. Never dispatch one task,
wait for it to complete, then dispatch the next independent task.

### Sprint Transition Efficiency

To minimize dead time between sprints:

1. **Pre-plan the next sprint** while the gate review is running — analyze what the next
   sprint needs, identify task dependencies, and have the dispatch ready
2. **Pipeline the review** — if the gate review returns `needs-work`, dispatch the fix
   agent AND start planning the next sprint in parallel
3. **Never re-register as orchestrator** between sprints — maintain your identity and
   heartbeat throughout the entire session

### Code Review Efficiency

When dispatching code reviewers:
- Tell them which files changed and how many commits to diff: `git diff HEAD~N`
- Scope the review to the sprint's changes, not the entire codebase
- This keeps review cost proportional to change size, not project size
