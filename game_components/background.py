"""
game_components/background.py  –  MOUSE RACER
───────────────────────────────────────────────
Animated background effects used on all menu screens.
    SpeedLines  –  horizontal speed-line particles
    DiagBG      –  scrolling diagonal stripe pattern
"""

import pygame, random
import game_components.shared as _s


# ─── Speed-line background ────────────────────────────────────────────────────
class SpeedLines:
    def __init__(self, count=70):
        self.lines = [self._new(random.randint(0, _s.W)) for _ in range(count)]

    def _new(self, x=None):
        return {
            'x':  _s.W if x is None else x,
            'y':  random.randint(0, _s.H),
            'len': random.randint(60, 220),
            'spd': random.uniform(8, 22),
            'a':  random.randint(15, 55),
        }

    def update(self):
        for l in self.lines:
            l['x'] -= l['spd']
        self.lines = [l if l['x'] + l['len'] > 0 else self._new() for l in self.lines]

    def draw(self, surf):
        sl = pygame.Surface((_s.W, _s.H), pygame.SRCALPHA)
        for l in self.lines:
            col = (*_s.C['stripe'], l['a'])
            pygame.draw.line(sl, col,
                             (int(l['x'] + l['len']), int(l['y'])),
                             (int(l['x']),            int(l['y'])), 1)
        surf.blit(sl, (0, 0))


# ─── Animated diagonal stripe background ─────────────────────────────────────
class DiagBG:
    def __init__(self):
        self.offset = 0

    def update(self):
        self.offset = (self.offset + 0.4) % 80

    def draw(self, surf):
        surf.fill(_s.C['bg'])
        stripe_surf = pygame.Surface((_s.W, _s.H), pygame.SRCALPHA)
        for x in range(-_s.H, _s.W + _s.H, 80):
            pts = [
                (x + self.offset,              0),
                (x + self.offset + 36,         0),
                (x + self.offset + 36 + _s.H, _s.H),
                (x + self.offset      + _s.H, _s.H),
            ]
            pygame.draw.polygon(stripe_surf, (*_s.C['bg2'], 255), pts)
        surf.blit(stripe_surf, (0, 0))
