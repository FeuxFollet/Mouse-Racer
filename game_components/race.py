import pygame
import sys
import os
import subprocess

import statistics_components.stats_collector as stats_collector

from .config import Config, apply_track
from .track import Track
from .particles import ParticleSystem
from .car import Car
from .hud import HUD


class Race:
    def __init__(self, selected_car):
        self.selected_car = selected_car
        self.particles = ParticleSystem()
        self._make_cars()
        self.countdown_start = pygame.time.get_ticks()
        self.started  = False
        self.finished = False
        self.pause_started = None
        self.paused_total = 0
        self._race_start_ms       = 0
        self._last_speed_sample_ms = 0

    def _make_cars(self):
        sx, sy, sa = Config.START_X, Config.START_Y, Config.START_ANG
        self.player = Car(sx - 18, sy + 22, sa, self.selected_car, "PLAYER")

        ai_data = dict(self.selected_car)
        ai_data["TURN_RATE"] = 10  # ← add this
        self.ai = Car(sx + 18, sy + 22, sa, ai_data, "RIVAL", ai=True)
        self.cars = [self.player, self.ai]

    def reset(self):
        self.particles.clear()
        self._make_cars()
        self.countdown_start = pygame.time.get_ticks()
        self.started  = False
        self.finished = False

    @property
    def countdown_n(self):
        e = (pygame.time.get_ticks() - self.countdown_start) // 1000
        return max(0, Config.COUNTDOWN - e)

    @property
    def countdown_done(self):
        return (pygame.time.get_ticks() - self.countdown_start) // 1000 >= Config.COUNTDOWN

    def update(self, track):
        if not self.countdown_done or self.finished:
            return

        if not self.started:
            self.started = True
            start_now = self.now()
            self.player.lap_start = start_now
            self.ai.lap_start = start_now
            self._race_start_ms = start_now
            stats_collector.stats.record_race_start(start_now)

        mx, my = pygame.mouse.get_pos()
        for c in self.cars:
            mp = (mx, my) if not c.ai else None
            c.update(track, self.particles, mouse_pos=mp, now=self.now())

        self.particles.update()

        now_ms = self.now()
        if now_ms - self._last_speed_sample_ms >= 1000:
            elapsed_s = (now_ms - self._race_start_ms) / 1000.0
            stats_collector.stats.record_speed(elapsed_s,
                                               round(abs(self.player.speed) * 42, 1))
            self._last_speed_sample_ms = now_ms

        if self.player.lap >= Config.TOTAL_LAPS:
            self.finished = True
            stats_collector.stats.flush()

    def now(self):
        if self.pause_started is not None:
            return self.pause_started - self.paused_total
        return pygame.time.get_ticks() - self.paused_total

    def set_paused(self, paused):
        current = pygame.time.get_ticks()
        if paused and self.pause_started is None:
            self.pause_started = current
        elif not paused and self.pause_started is not None:
            self.paused_total += current - self.pause_started
            self.pause_started = None


class Game:
    def __init__(self, selected_car, selected_track):
        # Apply track data
        apply_track(selected_track)
        stats_collector.stats.reset(
            track_name=selected_track.get("name", "track"),
            car_name=selected_car.get("name", "car"),
        )
        self.screen = pygame.display.set_mode((Config.WIDTH, Config.HEIGHT))
        pygame.display.set_caption(Config.CAPTION)
        pygame.mouse.set_visible(False)
        self.clock  = pygame.time.Clock()
        self.track  = Track()
        self.hud    = HUD()
        self.selected_car = selected_car
        self.race   = Race(selected_car)
        self._cursor = self._make_cursor()
        self.paused  = False

    @staticmethod
    def _make_cursor():
        s = pygame.Surface((22, 22), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 255, 255, 200), (11, 11), 9, 2)
        pygame.draw.line(s, (255, 80, 80), (11, 2),  (11, 8),  2)
        pygame.draw.line(s, (255, 80, 80), (11, 14), (11, 20), 2)
        pygame.draw.line(s, (255, 80, 80), (2, 11),  (8, 11),  2)
        pygame.draw.line(s, (255, 80, 80), (14, 11), (20, 11), 2)
        return s

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.race.finished:
                        return False
                    else:
                        self.paused = not self.paused   # toggle pause in-game
                        self.race.set_paused(self.paused)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if (self.race.finished
                        and self.hud.detail_btn is not None
                        and self.hud.detail_btn.collidepoint(event.pos)):
                    _sv = os.path.join(
                        os.path.dirname(os.path.abspath(__file__)),
                        "..",
                        "statistics_components",
                        "stats_viewer.py"
                    )
                    if os.path.exists(_sv):
                        subprocess.Popen([sys.executable, _sv])
        return True

    def draw_cursor(self):
        mx, my = pygame.mouse.get_pos()
        self.screen.blit(self._cursor,
                         (mx - self._cursor.get_width()//2,
                          my - self._cursor.get_height()//2))

    def _draw_paused(self):
        ov = pygame.Surface((Config.WIDTH, Config.HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 120))
        self.screen.blit(ov, (0, 0))
        txt = self.hud.f_huge.render("PAUSED", True, (240, 240, 245))
        self.screen.blit(txt, (Config.WIDTH  // 2 - txt.get_width()  // 2,
                               Config.HEIGHT // 2 - txt.get_height() // 2))

    def run(self):
        running = True
        while running:
            self.clock.tick(Config.FPS)
            running = self.handle_events()

            if not self.paused:
                self.race.update(self.track)

            self.track.draw(self.screen, self.race.player.cp_index)
            self.race.particles.draw(self.screen)
            for c in reversed(self.race.cars):
                c.draw(self.screen)
            self.hud.draw(self.screen, self.race.player, self.race.ai,
                          self.track, Config.TOTAL_LAPS, self.race.now())
            if not self.race.started:
                self.hud.draw_countdown(self.screen, self.race.countdown_n)
            if self.race.finished:
                self.hud.draw_results(self.screen, self.race.player, self.race.ai)
            if self.paused and not self.race.finished:
                self._draw_paused()

            self.draw_cursor()
            pygame.display.flip()

        stats_collector.stats.flush()   # save stats for early quit
        pygame.mouse.set_visible(True)
