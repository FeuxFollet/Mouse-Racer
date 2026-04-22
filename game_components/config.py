class Config:
    WIDTH, HEIGHT = 1400, 900
    FPS           = 60
    TOTAL_LAPS    = 3
    COUNTDOWN     = 3
    CAPTION       = "MOUSE RACER"

    WAYPOINTS   = []
    TRACK_WIDTH = 80
    CHECKPOINTS = []
    START_X     = 700
    START_Y     = 450
    START_ANG   = -90


def apply_track(track_dict):
    Config.WAYPOINTS   = track_dict["waypoints"]
    Config.TRACK_WIDTH = track_dict["track_width"]
    Config.TOTAL_LAPS  = track_dict["laps"]
    Config.START_X     = track_dict["waypoints"][0][0]
    Config.START_Y     = track_dict["waypoints"][0][1]

    cps = list(track_dict["checkpoints"])
    if cps[-1] != 0:
        cps.append(0)
    Config.CHECKPOINTS = cps


class Colors:
    GRASS        = (45,  90,  40)
    GRASS_DARK   = (35,  72,  30)
    ASPHALT      = (58,  60,  65)
    ASPHALT_DARK = (42,  44,  48)
    KERB_WHITE   = (230, 230, 230)
    KERB_RED     = (200,  40,  40)
    MARKING      = (240, 235, 200)
    WHITE        = (255, 255, 255)
    BLACK        = (0,   0,   0)

    PLAYER_BODY  = (210,  30,  30)
    PLAYER_ACCENT= (255, 200,   0)
    AI_BODY      = (30,   60, 200)
    AI_ACCENT    = (150, 200, 255)
    WINDSCREEN   = (160, 210, 240)

    HUD_BG       = (15,  15,  18)
    HUD_LINE     = (80,  80,  90)
    TEXT_WHITE   = (240, 240, 240)
    TEXT_DIM     = (140, 140, 155)
    ACCENT_RED   = (220,  50,  50)
    ACCENT_BLUE  = (80,  140, 255)
    NEON         = (100, 220, 100)
    WARN         = (255, 160,   0)

    SMOKE        = (130, 130, 130)
    DIRT         = (110,  80,  50)
    SKID         = (30,   28,  25)
    GATE_COLOR   = (255, 210,  40)
