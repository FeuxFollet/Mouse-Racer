import pygame

# Shared constants ────────────────────────────────────────────────────────
W, H   = 1400, 900
FPS    = 60

# Palette ─────────────────────────────────────────────────────────────────
C = dict(
    bg        = (12,  13,  16),
    bg2       = (18,  20,  26),
    panel     = (22,  25,  33),
    border    = (45,  50,  65),
    red       = (220,  40,  40),
    red_dim   = (130,  20,  20),
    cyan      = ( 60, 200, 230),
    cyan_dim  = ( 25,  80,  95),
    neon      = (100, 230,  80),
    neon_dim  = ( 35,  90,  30),
    white     = (240, 240, 245),
    dim       = (100, 105, 120),
    gold      = (255, 195,  40),
    gold_dim  = ( 90,  65,   5),
    stripe    = ( 30,  32,  42),
)

# Pygame display globals ───────────────────────────────────────────────────
screen  = None
clock   = None
F_GIANT = None
F_BIG   = None
F_MED   = None
F_SM    = None
F_XSM   = None
F_STAT  = None


def init():
    """Create / recreate the display, clock, and fonts.  Call after pygame.init()."""
    global screen, clock, F_GIANT, F_BIG, F_MED, F_SM, F_XSM, F_STAT
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("MOUSE RACER")
    clock   = pygame.time.Clock()
    F_GIANT = pygame.font.SysFont("consolas", 96,  bold=True)
    F_BIG   = pygame.font.SysFont("consolas", 48,  bold=True)
    F_MED   = pygame.font.SysFont("consolas", 26,  bold=True)
    F_SM    = pygame.font.SysFont("consolas", 18)
    F_XSM   = pygame.font.SysFont("consolas", 14)
    F_STAT  = pygame.font.SysFont("consolas", 21)
