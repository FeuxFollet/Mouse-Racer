import pygame
import math
import random
import sys
import os
import subprocess
import statistics_components.stats_collector as stats_collector

pygame.init()


def _catmull_chain(pts, steps=18):
    result = []
    n = len(pts)
    for i in range(n):
        p0 = pts[(i - 1) % n]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n]
        for s in range(steps):
            t  = s / steps
            t2 = t * t
            t3 = t2 * t
            x = 0.5 * (
                2 * p1[0]
                + (-p0[0] + p2[0]) * t
                + (2*p0[0] - 5*p1[0] + 4*p2[0] - p3[0]) * t2
                + (-p0[0] + 3*p1[0] - 3*p2[0] + p3[0]) * t3
            )
            y = 0.5 * (
                2 * p1[1]
                + (-p0[1] + p2[1]) * t
                + (2*p0[1] - 5*p1[1] + 4*p2[1] - p3[1]) * t2
                + (-p0[1] + 3*p1[1] - 3*p2[1] + p3[1]) * t3
            )
            result.append((x, y))
    return result


def _seg_intersect(p1, p2, p3, p4):
    def cross2d(a, b):
        return a[0] * b[1] - a[1] * b[0]

    r  = (p2[0] - p1[0], p2[1] - p1[1])
    s  = (p4[0] - p3[0], p4[1] - p3[1])
    rxs = cross2d(r, s)
    if abs(rxs) < 1e-9:
        return False
    qp = (p3[0] - p1[0], p3[1] - p1[1])
    t  = cross2d(qp, s) / rxs
    u  = cross2d(qp, r) / rxs
    return 0.0 <= t <= 1.0 and 0.0 <= u <= 1.0


# Config ───────────────────────────────────────────────────────────────

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


# Track ───────────────────────────────────────────────────────────────

class Track:
    def __init__(self):
        self.waypoints  = Config.WAYPOINTS
        self.hw         = Config.TRACK_WIDTH
        self.spline_pts = _catmull_chain(self.waypoints, steps=18)
        self.surface    = self._build()

    @staticmethod
    def _seg_normal(a, b, hw):
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy) or 1
        nx, ny = -dy / length * hw, dx / length * hw
        return ((a[0]+nx, a[1]+ny), (a[0]-nx, a[1]-ny),
                (b[0]+nx, b[1]+ny), (b[0]-nx, b[1]-ny))

    @staticmethod
    def _road_polygon(a, b, hw):
        dx, dy = b[0]-a[0], b[1]-a[1]
        length = math.hypot(dx, dy) or 1
        nx, ny = -dy/length*hw, dx/length*hw
        return [(a[0]+nx, a[1]+ny), (a[0]-nx, a[1]-ny),
                (b[0]-nx, b[1]-ny), (b[0]+nx, b[1]+ny)]

    def get_gate(self, wp_idx):
        pts = self.waypoints
        n   = len(pts)
        prv = pts[(wp_idx - 1) % n]
        nxt = pts[(wp_idx + 1) % n]
        dx, dy  = nxt[0] - prv[0], nxt[1] - prv[1]
        length  = math.hypot(dx, dy) or 1
        nx, ny  = -dy / length, dx / length
        cx, cy  = pts[wp_idx]
        hw      = self.hw + 14
        return (cx + nx*hw, cy + ny*hw), (cx - nx*hw, cy - ny*hw)

    # Surface builder ───────────────────────────────────────────────────────────────

    def _build(self):
        surf = pygame.Surface((Config.WIDTH, Config.HEIGHT))
        surf.fill(Colors.GRASS)
        for y in range(0, Config.HEIGHT, 12):
            pygame.draw.line(surf, Colors.GRASS_DARK, (0, y), (Config.WIDTH, y), 1)

        spts = self.spline_pts
        n    = len(spts)
        hw   = self.hw

        # White border
        for i in range(n):
            poly = self._road_polygon(spts[i], spts[(i+1) % n], hw + 9)
            pygame.draw.polygon(surf, Colors.KERB_WHITE, poly)
        for pt in spts:
            pygame.draw.circle(surf, Colors.KERB_WHITE, (int(pt[0]), int(pt[1])), hw + 9)

        # Border stripes
        kerb_period = 7
        for i in range(n):
            col = Colors.KERB_RED if (i // kerb_period) % 2 == 0 else Colors.KERB_WHITE
            a   = spts[i]
            b   = spts[(i + 1) % n]
            dx, dy = b[0]-a[0], b[1]-a[1]
            length = math.hypot(dx, dy) or 1
            nx, ny = -dy/length, dx/length
            r_edge = hw + 4
            # Left edge dot
            pygame.draw.circle(surf, col,
                               (int(a[0] + nx*r_edge), int(a[1] + ny*r_edge)), 5)
            # Right edge dot
            pygame.draw.circle(surf, col,
                               (int(a[0] - nx*r_edge), int(a[1] - ny*r_edge)), 5)

        # Asphalt color fill
        for i in range(n):
            poly = self._road_polygon(spts[i], spts[(i+1) % n], hw)
            pygame.draw.polygon(surf, Colors.ASPHALT, poly)
        for pt in spts:
            pygame.draw.circle(surf, Colors.ASPHALT, (int(pt[0]), int(pt[1])), hw)

        for i in range(n):
            poly = self._road_polygon(spts[i], spts[(i+1) % n], hw - 3)
            pygame.draw.polygon(surf, Colors.ASPHALT_DARK, poly)
        for pt in spts:
            pygame.draw.circle(surf, Colors.ASPHALT_DARK, (int(pt[0]), int(pt[1])), hw - 3)
        for i in range(n):
            poly = self._road_polygon(spts[i], spts[(i+1) % n], hw - 9)
            pygame.draw.polygon(surf, Colors.ASPHALT, poly)
        for pt in spts:
            pygame.draw.circle(surf, Colors.ASPHALT, (int(pt[0]), int(pt[1])), hw - 9)

        # Dashed centre line
        dash = True
        for i in range(0, n, 4):
            if dash:
                a = (int(spts[i][0]),             int(spts[i][1]))
                b = (int(spts[(i+3) % n][0]),     int(spts[(i+3) % n][1]))
                pygame.draw.line(surf, Colors.MARKING, a, b, 2)
            dash = not dash

        # Start/Finish line
        l0, r0 = self.get_gate(0)
        for k in range(10):
            t = k / 10
            t2 = (k + 1) / 10
            pa = (int(l0[0] + (r0[0] - l0[0]) * t), int(l0[1] + (r0[1] - l0[1]) * t))
            pb = (int(l0[0] + (r0[0] - l0[0]) * t2), int(l0[1] + (r0[1] - l0[1]) * t2))
            col = Colors.WHITE if k % 2 == 0 else Colors.BLACK
            pygame.draw.line(surf, col, pa, pb, 8)

        return surf

    # Collision ───────────────────────────────────────────────────────────────

    def on_track(self, x, y):
        hw2 = self.hw * self.hw
        return any((x - pt[0])**2 + (y - pt[1])**2 < hw2
                   for pt in self.spline_pts)

    def draw(self, surface, cleared_cp=0):
        surface.blit(self.surface, (0, 0))

        # Draw checkpoint gates
        if not Config.CHECKPOINTS:
            return

        # Create transparent overlay
        overlay = pygame.Surface((Config.WIDTH, Config.HEIGHT), pygame.SRCALPHA)

        n_cp = len(Config.CHECKPOINTS)
        passed = cleared_cp % n_cp    # num gates

        # Skip last checkpoint
        for i, wp_idx in enumerate(Config.CHECKPOINTS[:-1]):
            if i < passed:  # already went through
                continue
            a, b = self.get_gate(wp_idx)

            ax, ay = int(a[0]), int(a[1])
            bx, by = int(b[0]), int(b[1])

            # Gate color
            color = (*Colors.GATE_COLOR, 90)

            pygame.draw.line(overlay, color, (ax, ay), (bx, by), 6)

            pygame.draw.circle(overlay, color, (ax, ay), 4)
            pygame.draw.circle(overlay, color, (bx, by), 4)

        # Put overlay on top
        surface.blit(overlay, (0, 0))


# Particles ───────────────────────────────────────────────────────────────

class Particle:
    def __init__(self, x, y, color, size=3, life=30, vx=0, vy=0):
        self.x, self.y = x, y
        self.vx = vx + random.uniform(-0.6, 0.6)
        self.vy = vy + random.uniform(-0.6, 0.6)
        self.color   = color
        self.size    = size
        self.life    = life
        self.maxlife = life

    def update(self):
        self.x  += self.vx; self.y  += self.vy
        self.vx *= 0.96;    self.vy *= 0.96
        self.life -= 1

    def draw(self, surface):
        a = max(0, int(255 * self.life / self.maxlife))
        s = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, a), (self.size, self.size), self.size)
        surface.blit(s, (int(self.x - self.size), int(self.y - self.size)))


class SkidMark:
    def __init__(self, x, y, size=4):
        self.x, self.y = x, y
        self.size  = size
        self.alpha = 160

    def draw(self, surface):
        s = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*Colors.SKID, self.alpha),
                           (self.size, self.size), self.size)
        surface.blit(s, (int(self.x - self.size), int(self.y - self.size)))


class ParticleSystem:
    def __init__(self):
        self.particles = []
        self.skids     = []

    def smoke(self, x, y, count=2):
        for _ in range(count):
            self.particles.append(Particle(x, y, Colors.SMOKE, size=4, life=35))

    def dirt(self, x, y, count=4):
        for _ in range(count):
            self.particles.append(Particle(x, y, Colors.DIRT, size=3, life=25))

    def exhaust(self, x, y, angle):
        rad = math.radians(angle + 180)
        self.particles.append(
            Particle(x, y, Colors.SMOKE, size=2, life=20,
                     vx=math.cos(rad)*1.2, vy=math.sin(rad)*1.2))

    def skid(self, x, y):
        if random.random() < 0.4:
            self.skids.append(SkidMark(x, y))
        if len(self.skids) > 800:
            self.skids.pop(0)

    def update(self):
        for p in self.particles: p.update()
        self.particles = [p for p in self.particles if p.life > 0]

    def draw(self, surface):
        for s in self.skids:     s.draw(surface)
        for p in self.particles: p.draw(surface)

    def clear(self):
        self.particles.clear()
        self.skids.clear()


# Car ───────────────────────────────────────────────────────────────

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


# HUD ───────────────────────────────────────────────────────────────

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


# Race ───────────────────────────────────────────────────────────────

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

# Game ───────────────────────────────────────────────────────────────

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


# ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import os, json as _json
    _path = os.path.join(os.getcwd(), "track_json", "track1.json")
    with open(_path) as _f:
        _d = _json.load(_f)
    _n = len(_d.get("waypoints", []))
    _raw = _d.get("checkpoints", [])
    _fallback_track = {
        "name":        "CIRCUIT 01",
        "json_file":   "track1.json",
        "laps":        3,
        "waypoints":   _d["waypoints"],
        "track_width": _d["track_width"],
        "checkpoints": _raw if _raw else [int(i * _n / 8) for i in range(8)],
    }
    _car = {
        "name": "DEFAULT", "ACCEL": 0.18, "BRAKE_FRICTION": 0.25,
        "COAST_FRICTION": 0.05, "GRASS_FRICTION": 0.08,
        "MAX_SPEED": 7.0, "MAX_SPEED_GRASS": 3.5, "TURN_RATE": 3.8,
        "LENGTH": 36, "WIDTH": 20, "SCALE": 0.26,
        "sprite": _make_car_sprite(36, 20, (210, 30, 30), (255, 200, 0)),
    }
    Game(_car, _fallback_track).run()