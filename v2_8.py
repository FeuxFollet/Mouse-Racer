import pygame
import sys
import os
import subprocess
import statistics_components.stats_collector as stats_collector

from game_components.config import Config, Colors, apply_track
from game_components.helpers import _catmull_chain, _seg_intersect
from game_components.track import Track
from game_components.particles import Particle, SkidMark, ParticleSystem
from game_components.car import Car, _make_car_sprite
from game_components.hud import HUD
from game_components.race import Race, Game

pygame.init()


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
