import pygame, math, sys, os, importlib.util
import game_components.shared as _s
from game_components.ui      import Button, glow_text, draw_panel
from game_components.drawing import draw_track_minimap


# ─── Screens ─────────────────────────────────────────────────────────────────

def screen_main(bg, lines):
    """Returns: 'play' | 'shop' | 'quit'"""
    screen = _s.screen; clock = _s.clock
    W = _s.W; H = _s.H; FPS = _s.FPS; C = _s.C
    F_GIANT = _s.F_GIANT; F_MED = _s.F_MED; F_SM = _s.F_SM

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
    """Returns: 'back' | car_data_dict"""
    screen = _s.screen; clock = _s.clock
    W = _s.W; H = _s.H; FPS = _s.FPS; C = _s.C
    F_BIG = _s.F_BIG; F_MED = _s.F_MED; F_SM = _s.F_SM; F_STAT = _s.F_STAT

    btn_select = Button("SELECT >",  W//2 + 120, H - 80, w=200)
    btn_back   = Button("< BACK",    W//2 - 120, H - 80, w=170, color_key='cyan')
    # Arrow buttons sit at the left/right edges of the car preview panel (x 80–660, cy ~410)
    btn_left   = Button("<",  115, 410, w=56, h=56, color_key='cyan')
    btn_right  = Button(">",  625, 410, w=56, h=56, color_key='cyan')

    # Default preview colours per car slot (expand as needed)
    PREVIEW_COLS = [
        ((210,  30,  30), (255, 200,   0)),
        (( 30,  60, 200), (150, 200, 255)),
        (( 30, 160,  80), (200, 255, 100)),
        ((180,  60, 200), (255, 180, 255)),
    ]

    # Build display list from the loaded car data           # fix 2: no longer
    display_cars = []                                       # references undef var
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
                    return display_cars[sel]['data']  # fix 5: return real car data
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

        # ── Left panel: car preview ──────────────────────────────────────────
        panel_r = pygame.Rect(80, 80, 580, 660)
        draw_panel(screen, panel_r, C['red_dim'], radius=12)

        # Car name at top
        glow_text(screen, F_BIG, car['name'], C['red'], panel_r.centerx, panel_r.y + 52)

        # Animated car render in the centre of the panel
        car_cx = panel_r.centerx
        car_cy = panel_r.centery - 20 + int(math.sin(bob_t) * 8)

        # ── Scale PNG sprite to fit a ~280×180 preview box ──────────────────
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

        # Car counter  e.g. "1  /  2"
        ctr = F_SM.render(f"{sel + 1}  /  {len(display_cars)}", True, C['dim'])
        screen.blit(ctr, (panel_r.centerx - ctr.get_width() // 2,
                          panel_r.bottom - 155))

        # Exhaust sparks
        if spark_t % 4 == 0:
            pass  # could add particles here


        # ── Right panel: stats ───────────────────────────────────────────────
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

            # Value (bigger + cleaner)
            val_s = F_BIG.render(str(val), True, C['red'])
            screen.blit(val_s, (stats_r.x + 26, ky + 20))

            pygame.draw.line(screen, C['stripe'],
                             (stats_r.x + 20, ky + 80),
                             (stats_r.right - 20, ky + 80), 1)

        # Selection indicator (single car: just locked-in glow box)
        sel_r = pygame.Rect(stats_r.x+14, stats_r.y+68+sel*90,
                             stats_r.w-28, 80)
        # (shows selected stat block – visual only for now)

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
    """Returns: 'back' | selected track dict"""
    screen = _s.screen; clock = _s.clock
    W = _s.W; H = _s.H; FPS = _s.FPS; C = _s.C
    F_BIG = _s.F_BIG; F_MED = _s.F_MED; F_SM = _s.F_SM; F_STAT = _s.F_STAT

    if not tracks:
        # No tracks loaded – show an error and go back
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

        # ── Left panel: minimap ──────────────────────────────────────────────
        map_panel = pygame.Rect(80, 80, 580, 580)
        draw_panel(screen, map_panel, C['cyan_dim'], radius=12)
        map_inner = map_panel.inflate(-20, -20)
        draw_track_minimap(screen, map_inner, tr['waypoints'], tr['name'])

        # Track name below minimap
        glow_text(screen, F_BIG, tr['name'], C['cyan'],
                  map_panel.centerx, map_panel.bottom + 40)

        # Track counter  e.g. "1  /  3"
        ctr = F_SM.render(f"{sel + 1}  /  {len(tracks)}", True, C['dim'])
        screen.blit(ctr, (map_panel.centerx - ctr.get_width()//2,
                          map_panel.bottom + 80))

        # ── Right panel: track info ──────────────────────────────────────────
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


# ─── Launch game ─────────────────────────────────────────────────────────────
def launch_game(selected_car, selected_track):
    """Import and run Game from game.py sitting next to menu.py."""
    screen = _s.screen
    W = _s.W; H = _s.H; C = _s.C
    F_MED = _s.F_MED; F_SM = _s.F_SM

    game_path = os.path.join(os.path.dirname(__file__), "..", "v2_8.py")
    game_path = os.path.normpath(game_path)
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
