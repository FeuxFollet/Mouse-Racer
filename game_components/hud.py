import pygame

from .config import Config, Colors


class HUD:
    def __init__(self):
        self.f_big   = pygame.font.SysFont("consolas", 32, bold=True)
        self.f_med   = pygame.font.SysFont("consolas", 20, bold=True)
        self.f_sm    = pygame.font.SysFont("consolas", 15)
        self.f_huge  = pygame.font.SysFont("consolas", 110, bold=True)
        self.f_title = pygame.font.SysFont("consolas", 56, bold=True)
        self.detail_btn = None

    @staticmethod
    def ms(ms):
        if ms is None: return "--:--.--"
        m  = ms // 60000
        s  = (ms % 60000) // 1000
        cs = (ms % 1000)  // 10
        return f"{m}:{s:02d}.{cs:02d}"

    def _bar(self, surf, x, y, w, h, pct, fg, bg=Colors.HUD_LINE):
        pygame.draw.rect(surf, bg, (x, y, w, h), border_radius=3)
        pygame.draw.rect(surf, fg, (x, y, int(w*pct), h), border_radius=3)
        pygame.draw.rect(surf, Colors.TEXT_DIM, (x, y, w, h), 1, border_radius=3)

    def draw(self, surface, player, ai, track, total_laps, now):
        W, H = Config.WIDTH, Config.HEIGHT

        pygame.draw.rect(surface, Colors.HUD_BG, (0, 0, W, 60))
        pygame.draw.line(surface, Colors.HUD_LINE, (0, 60), (W, 60), 1)

        lap_s = self.f_big.render(
            f"LAP  {min(player.lap+1, total_laps)} / {total_laps}",
            True, Colors.TEXT_WHITE)
        surface.blit(lap_s, (W//2 - lap_s.get_width()//2, 14))

        kmh   = int(abs(player.speed) * 42)
        spd_s = self.f_big.render(f"{kmh:3d} km/h", True, Colors.ACCENT_RED)
        surface.blit(spd_s, (20, 14))
        self._bar(surface, 20, 44, 160, 8,
                  abs(player.speed)/player.MAX_SPEED, Colors.ACCENT_RED)

        surface.blit(
            self.f_med.render(self.ms(now - player.lap_start), True, Colors.TEXT_WHITE),
            (W - 200, 14))
        if player.best_lap:
            surface.blit(
                self.f_sm.render(f"BEST  {self.ms(player.best_lap)}", True, Colors.NEON),
                (W - 200, 40))

        # Checkpoint progress bar
        n_cp  = len(Config.CHECKPOINTS)
        cp_pct = (player.cp_index % n_cp) / n_cp if n_cp else 0
        self._bar(surface, W//2 - 80, 44, 160, 8, cp_pct, Colors.GATE_COLOR)

        # Mini leaderboard
        ranked = sorted([player, ai], key=lambda c: c.rank_key(), reverse=True)
        bx, by = 14, H - 14 - len(ranked)*26
        pygame.draw.rect(surface, Colors.HUD_BG,
                         (bx-6, by-6, 210, len(ranked)*26+12), border_radius=4)
        for i, c in enumerate(ranked):
            col = Colors.ACCENT_RED if c is player else Colors.ACCENT_BLUE
            surface.blit(
                self.f_sm.render(f"{'P' if c is player else 'AI'}  {i+1}  {c.name}",
                                 True, col),
                (bx, by + i*26))

        # Off-road warning
        if not track.on_track(player.x, player.y):
            warn = self.f_big.render("OFF  ROAD", True, Colors.WARN)
            surface.blit(warn, (W//2 - warn.get_width()//2, H//2 - 20))

    def draw_countdown(self, surface, n):
        ov = pygame.Surface((Config.WIDTH, Config.HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 110))
        surface.blit(ov, (0, 0))
        txt = "GO!" if n == 0 else str(n)
        col = Colors.NEON if n == 0 else Colors.TEXT_WHITE
        t   = self.f_huge.render(txt, True, col)
        surface.blit(t, (Config.WIDTH//2  - t.get_width()//2,
                         Config.HEIGHT//2 - t.get_height()//2))

    def draw_results(self, surface, player, ai):
        ov = pygame.Surface((Config.WIDTH, Config.HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 210))
        surface.blit(ov, (0, 0))

        t = self.f_title.render("RACE  FINISHED", True, Colors.TEXT_WHITE)
        surface.blit(t, (Config.WIDTH//2 - t.get_width()//2, 80))

        ranked = sorted([player, ai], key=lambda c: c.rank_key(), reverse=True)
        for i, c in enumerate(ranked):
            col  = Colors.NEON if c is player else Colors.ACCENT_BLUE
            line = f"{i+1}.  {c.name:<14}  BEST: {self.ms(c.best_lap)}"
            surface.blit(self.f_med.render(line, True, col),
                         (Config.WIDTH//2 - 220, 180 + i*52))

        sx, sy = Config.WIDTH//2 - 220, 310
        pygame.draw.rect(surface, Colors.HUD_BG, (sx, sy, 440, 150), border_radius=8)
        pygame.draw.rect(surface, Colors.HUD_LINE, (sx, sy, 440, 150), 1, border_radius=8)
        stats = [
            ("Top Speed",     f"{int(player.top_speed * 42)} km/h"),
            ("Distance",      f"{int(player.distance / 100):.0f} m"),
            ("Off-road hits", str(player.off_road_count)),
        ]
        for j, (label, val) in enumerate(stats):
            surface.blit(self.f_sm.render(label,  True, Colors.TEXT_DIM),
                         (sx + 16, sy + 14 + j*44))
            surface.blit(self.f_med.render(val,   True, Colors.TEXT_WHITE),
                         (sx + 16, sy + 30 + j*44))

        # View Detailed Stats
        detail_btn = pygame.Rect(sx + 72, sy + 230, 296, 34)
        self.detail_btn = detail_btn
        pygame.draw.rect(surface, Colors.HUD_BG, detail_btn, border_radius=6)
        pygame.draw.rect(surface, Colors.TEXT_WHITE, detail_btn, 1, border_radius=6)
        pygame.draw.rect(surface, Colors.TEXT_WHITE,
                         (detail_btn.x, detail_btn.y + 6, 3, detail_btn.h - 12),
                         border_radius=2)

        detail_txt = self.f_sm.render("View Detailed Stats", True, Colors.TEXT_WHITE)
        surface.blit(
            detail_txt,
            (detail_btn.centerx - detail_txt.get_width() // 2,
             detail_btn.centery - detail_txt.get_height() // 2)
        )

        menu = self.f_med.render("ESC  RETURN TO MENU", True, Colors.ACCENT_RED)
        surface.blit(menu, (Config.WIDTH//2 - menu.get_width()//2,
                                Config.HEIGHT - 70))
