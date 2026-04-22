import pygame
import math
import random

import statistics_components.stats_collector as stats_collector

from .config import Config, Colors
from .helpers import _seg_intersect


class Car:
    def __init__(self, x, y, angle, car_data, name, ai=False):
        self.x, self.y = float(x), float(y)
        self.angle = float(angle)
        self.speed = 0.0
        self.ai = ai
        self.name = name

        # Load stats from data
        self.ACCEL = car_data["ACCEL"]
        self.BRAKE_FRICTION = car_data["BRAKE_FRICTION"]
        self.COAST_FRICTION = car_data["COAST_FRICTION"]
        self.GRASS_FRICTION = car_data["GRASS_FRICTION"]
        self.MAX_SPEED = car_data["MAX_SPEED"]
        self.MAX_SPEED_GRASS = car_data["MAX_SPEED_GRASS"]
        self.TURN_RATE = car_data["TURN_RATE"]

        self.LENGTH = car_data["LENGTH"]
        self.WIDTH = car_data["WIDTH"]

        # Sprite scale
        scale = car_data.get("SCALE", 0.26)    # Default 0.26
        orig = car_data["sprite"]
        w, h = orig.get_size()
        self.sprite = pygame.transform.smoothscale(orig, (int(w * scale), int(h * scale)))

        # Checkpoint lap tracking
        self.cp_index  = 0
        self.lap       = 0
        self.lap_times = []
        self.lap_start = 0
        self.best_lap  = None

        # Stats
        self.top_speed       = 0.0
        self.distance        = 0.0
        self.off_road_frames = 0
        self.off_road_count  = 0
        self._was_on_road    = True

        # AI navigation use all waypoints
        self.wp_index = 1
        self._noise   = 0.0

        # Previous position
        self.prev_x = float(x)
        self.prev_y = float(y)

    # ── update ────────────────────────────────────────────────────────────────
    def update(self, track, particles, mouse_pos=None, now=None):
        # Save previous position before moving
        self.prev_x, self.prev_y = self.x, self.y

        on_road  = track.on_track(self.x, self.y)
        friction = self.COAST_FRICTION if on_road else self.GRASS_FRICTION
        max_spd  = self.MAX_SPEED      if on_road else self.MAX_SPEED_GRASS

        if self.ai and self.lap >= Config.TOTAL_LAPS:
            self.speed *= 0.99  # gradual slow down
            if abs(self.speed) < 0.05:
                self.speed = 0
            return

        if not on_road:
            self.off_road_frames += 1
            if self._was_on_road:
                self.off_road_count += 1
                if not self.ai:    # stats
                    stats_collector.stats.record_off_road_start(now or 0)
        elif not self._was_on_road and not self.ai:    # stats
            stats_collector.stats.record_off_road_end(now or 0)
        self._was_on_road = on_road

        if self.ai:
            self._ai_steer(on_road)
            self._ai_throttle(max_spd, friction)
            self._update_ai_nav()
        else:
            self._mouse_steer(mouse_pos, max_spd)
            self._auto_throttle(max_spd, friction)

        rad     = math.radians(self.angle)
        self.x += math.cos(rad) * self.speed
        self.y += math.sin(rad) * self.speed
        self.x  = max(10, min(Config.WIDTH  - 10, self.x))
        self.y  = max(10, min(Config.HEIGHT - 10, self.y))

        self.distance += abs(self.speed)
        if abs(self.speed) > self.top_speed:
            self.top_speed = abs(self.speed)

        # Checkpoint check
        self._check_checkpoints(track, now)

        if not on_road and abs(self.speed) > 0.3:
            particles.dirt(self.x, self.y, count=3)
            particles.skid(self.x, self.y)
        elif abs(self.speed) > 0.5 and not on_road:
            particles.smoke(self.x, self.y)
        if abs(self.speed) > 1.0 and random.random() < 0.25:
            particles.exhaust(self.x, self.y, self.angle)

    # Checkpoint ───────────────────────────────────────────────────────────────

    def _check_checkpoints(self, track, now=None):
        if now is None:
            now = pygame.time.get_ticks()

        if not Config.CHECKPOINTS:
            return

        n_cp = len(Config.CHECKPOINTS)
        cp_wp = Config.CHECKPOINTS[self.cp_index % n_cp]
        gate_a, gate_b = track.get_gate(cp_wp)

        if _seg_intersect((self.prev_x, self.prev_y), (self.x, self.y), gate_a, gate_b):
            pts = Config.WAYPOINTS
            n = len(pts)
            fwd_x = pts[(cp_wp + 1) % n][0] - pts[(cp_wp - 1) % n][0]
            fwd_y = pts[(cp_wp + 1) % n][1] - pts[(cp_wp - 1) % n][1]
            move_x = self.x - self.prev_x
            move_y = self.y - self.prev_y

            if fwd_x * move_x + fwd_y * move_y > 0:
                self.cp_index += 1
                cp_slot_in_lap = (self.cp_index - 1) % n_cp    # stats
                if self.cp_index % n_cp == 0:
                    lt = now - self.lap_start
                    self.lap_times.append(lt)
                    if self.best_lap is None or lt < self.best_lap:
                        self.best_lap = lt
                    self.lap_start = now
                    self.lap += 1
                    if not self.ai:    # stats
                        stats_collector.stats.record_checkpoint(
                            self.lap, cp_slot_in_lap, now)
                else:
                    if not self.ai:    # stats
                        stats_collector.stats.record_checkpoint(
                            self.lap + 1, cp_slot_in_lap, now)

    # AI Navigation ───────────────────────────────────────────────────────────────
    
    def _update_ai_nav(self):
        ti     = self.wp_index % len(Config.WAYPOINTS)
        tx, ty = Config.WAYPOINTS[ti]
        if math.hypot(self.x - tx, self.y - ty) < 45:
            self.wp_index += 1

    # Mouse Steering ───────────────────────────────────────────────────────────────

    def _mouse_steer(self, mouse_pos, max_spd):
        mx, my = mouse_pos
        dx, dy = mx - self.x, my - self.y
        dist   = math.hypot(dx, dy)
        if dist < 5:
            return
        target = math.degrees(math.atan2(dy, dx))
        diff   = (target - self.angle + 180) % 360 - 180
        turn   = self.TURN_RATE * min(1.0, abs(self.speed) / 2.0 + 0.3)
        self.angle += math.copysign(min(abs(diff), turn), diff)

    def _auto_throttle(self, max_spd, friction):
        mx, my  = pygame.mouse.get_pos()
        dx, dy  = mx - self.x, my - self.y
        dist    = math.hypot(dx, dy)
        target  = math.degrees(math.atan2(dy, dx))
        diff    = abs((target - self.angle + 180) % 360 - 180)
        desired = max_spd * max(0.3, 1.0 - diff / 180.0)
        if dist < 30:
            self.speed -= math.copysign(self.BRAKE_FRICTION * 2, self.speed)
            if abs(self.speed) < 0.05:
                self.speed = 0
        elif self.speed < desired:
            self.speed = min(self.speed + self.ACCEL, desired)
        else:
            self.speed = max(self.speed - friction, desired)

    # AI Steering ───────────────────────────────────────────────────────────────

    def _ai_steer(self, on_road):
        n_wp = len(Config.WAYPOINTS)
        ti = self.wp_index % n_wp
        tx, ty = Config.WAYPOINTS[ti]
        target = math.degrees(math.atan2(ty - self.y, tx - self.x))
        diff = (target - self.angle + 180) % 360 - 180
        noise_scale = 0.0 if not on_road else (0.35 if abs(diff) > 25 else 1.0)
        self._noise = self._noise * 0.88 + random.uniform(-0.8, 0.8) * noise_scale
        diff += self._noise
        self.angle += math.copysign(min(abs(diff), self.TURN_RATE), diff)

    def _ai_throttle(self, max_spd, friction):
        ti     = self.wp_index % len(Config.WAYPOINTS)
        tx, ty = Config.WAYPOINTS[ti]
        diff   = abs((math.degrees(math.atan2(ty-self.y, tx-self.x))
                      - self.angle + 180) % 360 - 180)
        corner_factor = max(0.08, 1.0 - diff / 90.0)
        desired = max_spd * corner_factor * random.uniform(0.92, 1.0)
        if self.speed > desired:
            f = self.BRAKE_FRICTION if self.speed > desired + 0.5 else friction
            self.speed = max(self.speed - f, desired)
        else:
            self.speed = min(self.speed + self.ACCEL, desired)

    def rank_key(self):
        return self.lap * len(Config.CHECKPOINTS) + self.cp_index

    def draw(self, surface):
        rotated = pygame.transform.rotate(self.sprite, -self.angle)

        # Make AI semi-transparent
        if self.ai:
            rotated.set_alpha(140)
        rect = rotated.get_rect(center=(self.x, self.y))
        surface.blit(rotated, rect)


# AI Sprite generator ───────────────────────────────────────────────────────────────

def _make_car_sprite(length, width, body_col, accent_col):
    """Generate a simple polygon car sprite Surface from colours."""
    pad  = 12
    w    = length + pad * 2
    h    = width  + pad * 2
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cx, cy = w // 2, h // 2
    L2, W2 = length // 2, width // 2
    nose   = max(6, length // 6)
    body = [
        (cx - L2,        cy - W2),
        (cx + L2,        cy - W2),
        (cx + L2 + nose, cy),
        (cx + L2,        cy + W2),
        (cx - L2,        cy + W2),
    ]
    pygame.draw.polygon(surf, body_col, body)
    pygame.draw.polygon(surf, (0, 0, 0), body, 2)
    roof = [
        (cx - L2 // 3, cy - W2 // 2 + 2),
        (cx + L2 // 4, cy - W2 // 2 + 2),
        (cx + L2 // 4, cy + W2 // 2 - 2),
        (cx - L2 // 3, cy + W2 // 2 - 2),
    ]
    pygame.draw.polygon(surf, (160, 210, 240), roof)
    pygame.draw.rect(surf, accent_col, (cx - L2, cy - 3, length + nose, 6))
    return surf
