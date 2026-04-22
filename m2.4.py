import pygame, math, random, sys, json, os, importlib.util
import v2_8
from game_data.car_loader import load_cars
from game_data.track_loader import load_tracks



pygame.init()

# Constants ───────────────────────────────────────────────────────────────

W, H   = 1400, 900
FPS    = 60
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("MOUSE RACER")
clock  = pygame.time.Clock()

# Fonts ───────────────────────────────────────────────────────────────

F_GIANT  = pygame.font.SysFont("consolas", 96,  bold=True)
F_BIG    = pygame.font.SysFont("consolas", 48,  bold=True)
F_MED    = pygame.font.SysFont("consolas", 26,  bold=True)
F_SM     = pygame.font.SysFont("consolas", 18)
F_XSM    = pygame.font.SysFont("consolas", 14)
F_STAT = pygame.font.SysFont("consolas", 21)

# Colors ───────────────────────────────────────────────────────────────

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

# Helpers ───────────────────────────────────────────────────────────────

def lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i]-a[i])*t) for i in range(3))

def glow_text(surf, font, text, color, cx, cy, glow_r=3):
    """Render text with a soft halo."""
    glow_col = tuple(max(0, c//4) for c in color)
    for dx in range(-glow_r, glow_r+1, glow_r):
        for dy in range(-glow_r, glow_r+1, glow_r):
            if dx == 0 and dy == 0: continue
            t = font.render(text, True, glow_col)
            surf.blit(t, (cx - t.get_width()//2 + dx, cy - t.get_height()//2 + dy))
    t = font.render(text, True, color)
    surf.blit(t, (cx - t.get_width()//2, cy - t.get_height()//2))
    return t.get_width(), t.get_height()

def draw_panel(surf, rect, border_col=None, radius=10):
    pygame.draw.rect(surf, C['panel'], rect, border_radius=radius)
    pygame.draw.rect(surf, border_col or C['border'], rect, 1, border_radius=radius)

# Background ───────────────────────────────────────────────────────────────

class SpeedLines:
    def __init__(self, count=70):
        self.lines = [self._new(random.randint(0, W)) for _ in range(count)]

    def _new(self, x=None):
        return {
            'x':  W if x is None else x,
            'y':  random.randint(0, H),
            'len': random.randint(60, 220),
            'spd': random.uniform(8, 22),
            'a':  random.randint(15, 55),
        }

    def update(self):
        for l in self.lines:
            l['x'] -= l['spd']
        self.lines = [l if l['x'] + l['len'] > 0 else self._new() for l in self.lines]

    def draw(self, surf):
        sl = pygame.Surface((W, H), pygame.SRCALPHA)
        for l in self.lines:
            col = (*C['stripe'], l['a'])
            pygame.draw.line(sl, col,
                             (int(l['x'] + l['len']), int(l['y'])),
                             (int(l['x']),            int(l['y'])), 1)
        surf.blit(sl, (0, 0))


class DiagBG:
    def __init__(self):
        self.offset = 0

    def update(self):
        self.offset = (self.offset + 0.4) % 80

    def draw(self, surf):
        surf.fill(C['bg'])
        stripe_surf = pygame.Surface((W, H), pygame.SRCALPHA)
        for x in range(-H, W + H, 80):
            pts = [
                (x + self.offset,          0),
                (x + self.offset + 36,     0),
                (x + self.offset + 36 + H, H),
                (x + self.offset      + H, H),
            ]
            pygame.draw.polygon(stripe_surf, (*C['bg2'], 255), pts)
        surf.blit(stripe_surf, (0, 0))

# Buttons ───────────────────────────────────────────────────────────────

class Button:
    def __init__(self, label, cx, cy, w=320, h=58,
                 color_key='red', disabled=False):
        self.label    = label
        self.rect     = pygame.Rect(cx - w//2, cy - h//2, w, h)
        self.ck       = color_key
        self.disabled = disabled
        self._hover_t = 0.0

    def update(self, mouse):
        target = 1.0 if (self.rect.collidepoint(mouse) and not self.disabled) else 0.0
        self._hover_t += (target - self._hover_t) * 0.18

    def clicked(self, mouse):
        return (not self.disabled) and self.rect.collidepoint(mouse)

    def draw(self, surf):
        t  = self._hover_t
        fg = C[self.ck]
        bg_col = lerp_color(C['panel'], tuple(max(0, c//5) for c in fg), t*0.4)
        br_col = lerp_color(C['border'], fg, t)
        tx_col = lerp_color(C['dim'], C['white'], t) if not self.disabled else C['dim']

        # Glow on hover
        if t > 0.05:
            glow = pygame.Surface((self.rect.w + 30, self.rect.h + 30), pygame.SRCALPHA)
            gr = pygame.Rect(0, 0, self.rect.w+30, self.rect.h+30)
            pygame.draw.rect(glow, (*fg, int(35*t)), gr, border_radius=14)
            surf.blit(glow, (self.rect.x-15, self.rect.y-15))

        pygame.draw.rect(surf, bg_col, self.rect, border_radius=8)
        pygame.draw.rect(surf, br_col, self.rect, 2, border_radius=8)

        # Left accent bar
        bar_col = lerp_color(C['border'], fg, t)
        pygame.draw.rect(surf, bar_col,
                         (self.rect.x, self.rect.y+10, 3, self.rect.h-20),
                         border_radius=2)

        txt = F_MED.render(self.label, True, tx_col)
        surf.blit(txt, (self.rect.centerx - txt.get_width()//2,
                        self.rect.centery - txt.get_height()//2))

        if self.disabled:
            ds = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
            ds.fill((0, 0, 0, 80))
            surf.blit(ds, self.rect.topleft)
            tag = F_XSM.render("COMING SOON", True, C['dim'])
            surf.blit(tag, (self.rect.right - tag.get_width() - 10,
                            self.rect.bottom - tag.get_height() - 6))

# Car Preview ───────────────────────────────────────────────────────────────

def draw_car_preview(surf, cx, cy, scale=3.0, angle=0,
                     body_col=(210,30,30), accent_col=(255,200,0)):
    L = int(26 * scale)
    Ww = int(13 * scale)
    rad = math.radians(angle)
    ca, sa = math.cos(rad), math.sin(rad)

    def rot(px, py):
        return (int(cx + px*ca - py*sa), int(cy + px*sa + py*ca))

    # Shadow
    shadow = [rot(px+int(3*scale), py+int(3*scale)) for px,py in [
        (-L//2,-Ww//2),(L//2,-Ww//2),(L//2+int(5*scale),0),(L//2,Ww//2),(-L//2,Ww//2)]]
    pygame.draw.polygon(surf, (0,0,0), shadow)

    body = [rot(-L//2,-Ww//2), rot(L//2,-Ww//2),
            rot(L//2+int(5*scale),0), rot(L//2,Ww//2), rot(-L//2,Ww//2)]
    pygame.draw.polygon(surf, body_col, body)
    pygame.draw.polygon(surf, (0,0,0), body, 2)

    roof = [rot(-L//4,-Ww//3), rot(L//4,-Ww//3), rot(L//4,Ww//3), rot(-L//4,Ww//3)]
    pygame.draw.polygon(surf, (160,210,240), roof)

    stripe = [rot(-L//2,-int(2*scale)), rot(L//2+int(5*scale),-int(2*scale)),
              rot(L//2+int(5*scale), int(2*scale)), rot(-L//2, int(2*scale))]
    pygame.draw.polygon(surf, accent_col, stripe)

    for sign in (-1,1):
        hx = cx + (L//2+int(6*scale))*ca - sign*(Ww//3)*sa
        hy = cy + (L//2+int(6*scale))*sa + sign*(Ww//3)*ca
        pygame.draw.circle(surf, (255,255,200), (int(hx), int(hy)), int(3*scale))
    for sign in (-1,1):
        rx = cx + (-L//2-int(2*scale))*ca - sign*(Ww//3)*sa
        ry = cy + (-L//2-int(2*scale))*sa + sign*(Ww//3)*ca
        pygame.draw.circle(surf, (200,40,40), (int(rx), int(ry)), int(3*scale))

# Track Preview ───────────────────────────────────────────────────────────────

def draw_track_minimap(surf, rect, waypoints, track_name="CIRCUIT 01"):
    draw_panel(surf, rect.inflate(4,4), C['cyan_dim'], radius=12)
    draw_panel(surf, rect, C['cyan'], radius=10)

    if not waypoints:
        t = F_SM.render("NO TRACK DATA", True, C['dim'])
        surf.blit(t, (rect.centerx - t.get_width()//2, rect.centery))
        return

    xs = [p[0] for p in waypoints]
    ys = [p[1] for p in waypoints]
    mn_x, mx_x = min(xs), max(xs)
    mn_y, mx_y = min(ys), max(ys)
    pad = 22
    span_x = (mx_x - mn_x) or 1
    span_y = (mx_y - mn_y) or 1

    def proj(p):
        nx = (p[0]-mn_x)/span_x * (rect.w - pad*2) + rect.x + pad
        ny = (p[1]-mn_y)/span_y * (rect.h - pad*2) + rect.y + pad
        return (int(nx), int(ny))

    pts = [proj(p) for p in waypoints]

    # Track body
    for i in range(len(pts)):
        a, b = pts[i], pts[(i+1)%len(pts)]
        pygame.draw.line(surf, C['border'], a, b, 9)
    # Centre line
    for i in range(len(pts)):
        a, b = pts[i], pts[(i+1)%len(pts)]
        pygame.draw.line(surf, C['cyan'], a, b, 2)
    # Start dot
    pygame.draw.circle(surf, C['red'], pts[0], 6)

    t = F_XSM.render(track_name, True, C['cyan'])
    surf.blit(t, (rect.x + 8, rect.y + 6))

# Screens ───────────────────────────────────────────────────────────────

def screen_main(bg, lines):
    """Returns: 'play' | 'shop' | 'quit'"""
    btn_play = Button("PLAY",      W//2, H//2 - 30,  w=300)
    btn_quit = Button("QUIT",      W//2, H//2 + 50, w=300, color_key='cyan')
    buttons  = [btn_play, btn_quit]

    title_bob = 0.0

    while True:
        mouse = pygame.mouse.get_pos()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if btn_play.clicked(mouse): return 'play'
                if btn_quit.clicked(mouse): return 'quit'

        bg.draw(screen)

        # Corner accent bars
        for col, pts in [
            (C['red'],  [(0,0),(6,0),(6,H//4),(0,H//4)]),
            (C['cyan'], [(W-6,0),(W,0),(W,H//4),(W-6,H//4)]),
            (C['red'],  [(0,H*3//4),(6,H*3//4),(6,H),(0,H)]),
            (C['cyan'], [(W-6,H*3//4),(W,H*3//4),(W,H),(W-6,H)]),
        ]:
            pygame.draw.polygon(screen, col, pts)

        # Title
        title_bob = (title_bob + 0.04) % (2*math.pi)
        bob_y = int(math.sin(title_bob) * 5)
        glow_text(screen, F_GIANT, "MOUSE", C['red'],  W//2 - 130, 160 + bob_y, glow_r=5)
        glow_text(screen, F_GIANT, "RACER", C['cyan'], W//2 + 140, 160 + bob_y, glow_r=5)

        # Subtitle line
        line_surf = pygame.Surface((400, 2))
        line_surf.fill(C['dim'])
        screen.blit(line_surf, (W//2 - 200, 225 + bob_y))


        for b in buttons: b.update(mouse); b.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)


def screen_car_select(bg, lines, cars):
    btn_select = Button("SELECT >",  W//2 + 120, H - 80, w=200)
    btn_back   = Button("< BACK",    W//2 - 120, H - 80, w=170, color_key='cyan')
    # Arrow buttons
    btn_left   = Button("<",  115, 410, w=56, h=56, color_key='cyan')
    btn_right  = Button(">",  625, 410, w=56, h=56, color_key='cyan')

    # Default preview colours
    PREVIEW_COLS = [
        ((210,  30,  30), (255, 200,   0)),
        (( 30,  60, 200), (150, 200, 255)),
        (( 30, 160,  80), (200, 255, 100)),
        ((180,  60, 200), (255, 180, 255)),
    ]

    # Build display list
    display_cars = []
    for i, c in enumerate(cars):
        body_col, accent_col = PREVIEW_COLS[i % len(PREVIEW_COLS)]
        display_cars.append(dict(
            name   = c["name"],
            body   = body_col,
            accent = accent_col,
            stats  = {
                "MAX SPEED":    f"{c['MAX_SPEED']}",
                "ACCELERATION": f"{int(c['ACCEL'] * 100)}",
                "TURNING":      f"{c['TURN_RATE']}",
            },
            data   = c,   # reference to actual car_data dict
        ))
    sel     = 0
    bob_t   = 0.0
    spark_t = 0

    while True:
        mouse = pygame.mouse.get_pos()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if btn_select.clicked(mouse):
                    return display_cars[sel]['data']
                if btn_back.clicked(mouse):   return 'back'
                if btn_left.clicked(mouse):   sel = (sel - 1) % len(display_cars)
                if btn_right.clicked(mouse):  sel = (sel + 1) % len(display_cars)
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:       return 'back'
                if ev.key == pygame.K_LEFT:         sel = (sel - 1) % len(display_cars)
                if ev.key == pygame.K_RIGHT:        sel = (sel + 1) % len(display_cars)
                if ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return display_cars[sel]['data']

        bg.draw(screen)
        bob_t  += 0.05
        spark_t += 1

        car = display_cars[sel]

        # Car Preview
        panel_r = pygame.Rect(80, 80, 580, 660)
        draw_panel(screen, panel_r, C['red_dim'], radius=12)

        # Car name at top
        glow_text(screen, F_BIG, car['name'], C['red'], panel_r.centerx, panel_r.y + 52)

        # Car render
        car_cx = panel_r.centerx
        car_cy = panel_r.centery - 20 + int(math.sin(bob_t) * 8)

        # Scale png
        raw_sprite = car['data']['sprite']
        _sw, _sh = raw_sprite.get_width(), raw_sprite.get_height()
        _sc = min(280 / max(_sw, 1), 180 / max(_sh, 1))
        _pw, _ph = max(1, int(_sw * _sc)), max(1, int(_sh * _sc))
        preview_sprite = pygame.transform.scale(raw_sprite, (_pw, _ph))
        # Subtle platform shadow
        pygame.draw.ellipse(screen, C['bg2'],
                            (car_cx - _pw // 2 - 12, car_cy + _ph // 2 + 6,
                             _pw + 24, 18))
        screen.blit(preview_sprite, (car_cx - _pw // 2, car_cy - _ph // 2))

        # Car counter
        ctr = F_SM.render(f"{sel + 1}  /  {len(display_cars)}", True, C['dim'])
        screen.blit(ctr, (panel_r.centerx - ctr.get_width() // 2,
                          panel_r.bottom - 155))


        # Stats panel
        stats_r = pygame.Rect(730, 80, 580, 660)
        draw_panel(screen, stats_r, C['border'], radius=12)

        header = F_MED.render("STATS", True, C['dim'])
        screen.blit(header, (stats_r.x + 26, stats_r.y + 22))
        pygame.draw.line(screen, C['border'],
                         (stats_r.x+20, stats_r.y+58),
                         (stats_r.right-20, stats_r.y+58), 1)

        for i, (key, val) in enumerate(car['stats'].items()):
            ky = stats_r.y + 110 + i * 100

            # Label
            lbl = F_STAT.render(key, True, C['dim'])
            screen.blit(lbl, (stats_r.x + 26, ky - 8))

            # Value
            val_s = F_BIG.render(str(val), True, C['red'])
            screen.blit(val_s, (stats_r.x + 26, ky + 20))

            pygame.draw.line(screen, C['stripe'],
                             (stats_r.x + 20, ky + 80),
                             (stats_r.right - 20, ky + 80), 1)

        # Selection indicator
        sel_r = pygame.Rect(stats_r.x+14, stats_r.y+68+sel*90,
                             stats_r.w-28, 80)

        # Heading
        glow_text(screen, F_MED, "CHOOSE  YOUR  CAR",
                  C['dim'], W//2, 42)

        btn_select.update(mouse); btn_select.draw(screen)
        btn_back.update(mouse);   btn_back.draw(screen)
        btn_left.update(mouse);   btn_left.draw(screen)
        btn_right.update(mouse);  btn_right.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)


def screen_track_select(bg, lines, tracks):
    if not tracks:
        # No tracks loaded
        while True:
            mouse = pygame.mouse.get_pos()
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if ev.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    return 'back'
            bg.draw(screen)
            glow_text(screen, F_BIG, "NO TRACKS FOUND", C['red'], W//2, H//2 - 20)
            t = F_SM.render("Add entries to tracks_data.csv and restart.", True, C['dim'])
            screen.blit(t, (W//2 - t.get_width()//2, H//2 + 30))
            pygame.display.flip()
            clock.tick(FPS)

    btn_race  = Button("START  RACE >", W//2 + 120, H - 80, w=210, color_key='neon')
    btn_back  = Button("< BACK",        W//2 - 120, H - 80, w=170, color_key='cyan')
    btn_left  = Button("<",  115, 410, w=56, h=56, color_key='cyan')
    btn_right = Button(">",  625, 410, w=56, h=56, color_key='cyan')

    sel   = 0
    bob_t = 0.0

    while True:
        mouse = pygame.mouse.get_pos()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if btn_race.clicked(mouse):  return tracks[sel]
                if btn_back.clicked(mouse):  return 'back'
                if btn_left.clicked(mouse):  sel = (sel - 1) % len(tracks)
                if btn_right.clicked(mouse): sel = (sel + 1) % len(tracks)
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:                    return 'back'
                if ev.key in (pygame.K_RETURN, pygame.K_SPACE):  return tracks[sel]
                if ev.key == pygame.K_LEFT:  sel = (sel - 1) % len(tracks)
                if ev.key == pygame.K_RIGHT: sel = (sel + 1) % len(tracks)

        bg.draw(screen)
        bob_t += 0.04

        tr = tracks[sel]

        # Minimap panel
        map_panel = pygame.Rect(80, 80, 580, 580)
        draw_panel(screen, map_panel, C['cyan_dim'], radius=12)
        map_inner = map_panel.inflate(-20, -20)
        draw_track_minimap(screen, map_inner, tr['waypoints'], tr['name'])

        # Track name below minimap
        glow_text(screen, F_BIG, tr['name'], C['cyan'],
                  map_panel.centerx, map_panel.bottom + 40)

        # Track counter
        ctr = F_SM.render(f"{sel + 1}  /  {len(tracks)}", True, C['dim'])
        screen.blit(ctr, (map_panel.centerx - ctr.get_width()//2,
                          map_panel.bottom + 80))

        # Track info panel
        info_r = pygame.Rect(730, 80, 580, 580)
        draw_panel(screen, info_r, C['border'], radius=12)

        header = F_MED.render("TRACK  INFO", True, C['dim'])
        screen.blit(header, (info_r.x+26, info_r.y+22))
        pygame.draw.line(screen, C['border'],
                         (info_r.x+20, info_r.y+58),
                         (info_r.right-20, info_r.y+58), 1)

        rows = [
            ("LAPS",       str(tr['laps'])),
            ("WAYPOINTS",  str(len(tr['waypoints']))),
            ("CHECKPOINTS", str(len(tr['checkpoints']))),
        ]
        for i, (k, v) in enumerate(rows):
            ry = info_r.y + 86 + i*90
            lbl = F_STAT.render(k, True, C['dim'])
            screen.blit(lbl, (info_r.x+26, ry))
            val = F_BIG.render(v, True, C['white'])
            screen.blit(val, (info_r.x+26, ry+28))
            pygame.draw.line(screen, C['stripe'],
                             (info_r.x+20, ry+80),
                             (info_r.right-20, ry+80), 1)

        # Heading
        glow_text(screen, F_MED, "CHOOSE  YOUR  TRACK",
                  C['dim'], W//2, 42)

        btn_race.update(mouse);  btn_race.draw(screen)
        btn_back.update(mouse);  btn_back.draw(screen)
        # Only show arrows when there is more than one track
        if len(tracks) > 1:
            btn_left.update(mouse);  btn_left.draw(screen)
            btn_right.update(mouse); btn_right.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)


# Launch Game ───────────────────────────────────────────────────────────────

def launch_game(selected_car, selected_track):
    game_path = os.path.join(os.path.dirname(__file__), "v2_8.py")
    if not os.path.exists(game_path):
            # Show error screen
            screen.fill(C['bg'])
            msg = F_MED.render("game file not found",
                               True, C['red'])
            screen.blit(msg, (W//2 - msg.get_width()//2, H//2 - 20))
            sub = F_SM.render("Press any key to return to menu.", True, C['dim'])
            screen.blit(sub, (W//2 - sub.get_width()//2, H//2 + 30))
            pygame.display.flip()
            waiting = True
            while waiting:
                for ev in pygame.event.get():
                    if ev.type in (pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                        waiting = False
            return

    spec = importlib.util.spec_from_file_location("game", game_path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.Game(selected_car, selected_track).run()


# Main ───────────────────────────────────────────────────────────────

def main():
    tracks = load_tracks()
    cars   = load_cars()

    bg    = DiagBG()
    lines = SpeedLines()

    while True:
        result = screen_main(bg, lines)
        if result == 'quit':
            pygame.quit(); sys.exit()

        if result == 'play':
            selected_car = screen_car_select(bg, lines, cars)

            if selected_car == 'back':
                continue

            selected_track = screen_track_select(bg, lines, tracks)
            if selected_track == 'back':
                continue

            pygame.mouse.set_visible(True)
            launch_game(selected_car, selected_track)
            pygame.init()
            global screen, clock
            screen = pygame.display.set_mode((W, H))
            pygame.display.set_caption("MOUSE RACER")
            clock  = pygame.time.Clock()


if __name__ == "__main__":
    main()