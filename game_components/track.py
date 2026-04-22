import pygame
import math

from .config import Config, Colors
from .helpers import _catmull_chain


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
