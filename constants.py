"""All game constants and tuning values. Change balance here, not in entity files."""

import pygame

# ---------------------------------------------------------------------------
# Tile IDs
# ---------------------------------------------------------------------------
EMPTY = 0
DIGGABLE_BRICK = 1
SOLID_BRICK = 2
LADDER = 3
ROPE = 4
GOLD = 5
HIDDEN_LADDER = 6
FALSE_BRICK = 7
HOLE_OPEN = 8
HOLE_FILLING = 9

# Tile sets for fast membership tests
SOLID_TILES = frozenset({SOLID_BRICK, DIGGABLE_BRICK})
STANDABLE_TILES = frozenset({SOLID_BRICK, DIGGABLE_BRICK})  # entities stand on top of these
PASSABLE_TILES = frozenset({EMPTY, LADDER, ROPE, GOLD, HIDDEN_LADDER, HOLE_OPEN, FALSE_BRICK})
CLIMBABLE_TILES = frozenset({LADDER})

# ---------------------------------------------------------------------------
# Grid and window
# ---------------------------------------------------------------------------
GRID_COLS = 28
GRID_ROWS = 16
TILE_SIZE = 32  # pixels per tile
HUD_HEIGHT = 32  # pixels for HUD bar above the grid

WINDOW_WIDTH = GRID_COLS * TILE_SIZE  # 896
WINDOW_HEIGHT = GRID_ROWS * TILE_SIZE + HUD_HEIGHT  # 544
FPS = 60

# Scaling modes
SCALE_1X = 1
SCALE_2X = 2

# ---------------------------------------------------------------------------
# Colors  (hex values from design-document.md §8.2, converted to RGB tuples)
# ---------------------------------------------------------------------------
COLOR_BACKGROUND = (0, 0, 0)
COLOR_SOLID_BRICK = (42, 58, 90)
COLOR_DIGGABLE_BRICK = (139, 108, 66)
COLOR_DIGGABLE_HIGHLIGHT = (176, 138, 88)
COLOR_DIGGABLE_SHADOW = (92, 71, 40)
COLOR_LADDER = (168, 217, 64)
COLOR_ROPE = (196, 122, 42)
COLOR_GOLD = (245, 197, 66)
COLOR_GOLD_GLINT = (255, 255, 255)
COLOR_PLAYER_BODY = (168, 212, 255)
COLOR_PLAYER_OUTLINE = (232, 232, 232)
COLOR_ENEMY_BODY = (217, 64, 64)
COLOR_ENEMY_OUTLINE = (139, 26, 26)
COLOR_HUD_BG = (10, 10, 20)
COLOR_HUD_TEXT = (245, 197, 66)
COLOR_HUD_TEXT_DIM = (106, 96, 64)

# ---------------------------------------------------------------------------
# Timing (seconds)
# ---------------------------------------------------------------------------
HOLE_OPEN_DURATION = 7.0  # seconds before hole starts filling
HOLE_FILL_DURATION = 3.0  # seconds for fill animation (total life = 10s)
ENEMY_ESCAPE_TIME = 2.5  # seconds before trapped enemy climbs out
ENEMY_RESPAWN_DELAY = 3.0  # seconds after death before enemy respawns at spawn point

# ---------------------------------------------------------------------------
# Movement speeds (tiles per second)
# ---------------------------------------------------------------------------
PLAYER_RUN_SPEED = 7.0
PLAYER_CLIMB_SPEED = 5.0
PLAYER_ROPE_SPEED = 6.0
PLAYER_FALL_SPEED = 10.0

ENEMY_RUN_SPEED = 5.0
ENEMY_CLIMB_SPEED = 4.0
ENEMY_FALL_SPEED = 10.0

# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------
SCORE_GOLD = 250
SCORE_ENEMY_TRAPPED = 75
SCORE_ENEMY_KILLED = 75
SCORE_LEVEL_COMPLETE = 1500

# Championship mode scoring
SCORE_GOLD_CHAMPIONSHIP = 500
SCORE_LEVEL_COMPLETE_CHAMPIONSHIP = 2000
SCORE_ENEMY_CHAMPIONSHIP = 100

# ---------------------------------------------------------------------------
# Lives
# ---------------------------------------------------------------------------
STARTING_LIVES = 5
LIVES_PER_LEVEL = 1

# ---------------------------------------------------------------------------
# Key bindings (defaults; overridable via settings.json)
# ---------------------------------------------------------------------------
# Primary keys
KEY_LEFT = pygame.K_LEFT
KEY_RIGHT = pygame.K_RIGHT
KEY_UP = pygame.K_UP
KEY_DOWN = pygame.K_DOWN
KEY_DIG_LEFT = pygame.K_z
KEY_DIG_RIGHT = pygame.K_x
KEY_PAUSE = pygame.K_ESCAPE
KEY_MUSIC = pygame.K_m

# Alternate keys (WASD)
KEY_ALT_LEFT = pygame.K_a
KEY_ALT_RIGHT = pygame.K_d
KEY_ALT_UP = pygame.K_w
KEY_ALT_DOWN = pygame.K_s

# Dig alternates
KEY_ALT_DIG_LEFT = pygame.K_LCTRL
KEY_ALT_DIG_RIGHT = pygame.K_RCTRL

# ---------------------------------------------------------------------------
# Control mode flags (toggled via settings.json)
# ---------------------------------------------------------------------------
CONTROL_TOGGLE_MOVE = "toggle"  # Apple II authentic: press to start, press again to stop
CONTROL_HOLD_MOVE = "hold"  # Modern: hold key to move

DIG_MODE_DIRECTIONAL = "directional"  # Z/X dig relative to player facing
DIG_MODE_FIXED = "fixed"  # Z always left, X always right

# ---------------------------------------------------------------------------
# Rendering constants
# ---------------------------------------------------------------------------
HUD_FONT_SIZE = 14
HUD_PADDING = 8
LADDER_RUNG_COUNT = 4
ROPE_KNOT_SPACING = 8  # pixels between rope knots
ROPE_KNOT_OFFSET = 4  # pixels from tile edge to first knot
TILE_SNAP_TOLERANCE = 2  # pixels; max y/x offset to count as tile-aligned
PLAYER_ANIM_FPS = 8  # animation frame flips per second
PLAYER_ANIM_FRAMES = 8  # total animation frames per cycle
PLAYER_MOVE_THRESHOLD = 0.001  # min pixel delta to count as moved (sub-pixel guard)
ENEMY_ANIM_FPS = 8  # animation frame flips per second
ENEMY_ANIM_FRAMES = 8  # total animation frames per cycle
