import pygame
import math
import random

from .config import Colors


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
