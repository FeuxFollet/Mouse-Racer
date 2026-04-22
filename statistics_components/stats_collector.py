import csv
import os
from datetime import datetime


_STATS_DIR = os.path.join(os.getcwd(), "statistics")


class StatsCollector:

    def __init__(self):
        self._match_dir      = None

        # in-memory buffers
        self._checkpoints    = []   # (lap, checkpoint, race_time_ms, split_ms)
        self._off_road       = []   # (start_ms, end_ms, duration_ms)
        self._speed          = []   # (elapsed_s, speed_kmh)

        self._last_cp_time   = 0    # ms – time of last gate / race start
        self._off_road_start = None # ms – when the car left the road (None = on road)

    # public API ────────────────────────────────────────────────────────────

    def reset(self, track_name: str = "track", car_name: str = "car"):
        ts         = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_track = "".join(c if c.isalnum() or c in "-_" else "_"
                             for c in track_name).strip("_")
        self._match_dir = os.path.join(_STATS_DIR, f"{ts}_{safe_track}")
        os.makedirs(self._match_dir, exist_ok=True)

        self._checkpoints    = []
        self._off_road       = []
        self._speed          = []
        self._last_cp_time   = 0
        self._off_road_start = None

    def record_race_start(self, race_time_ms: int):
        self._last_cp_time = race_time_ms

    def record_checkpoint(self, lap: int, cp_slot: int, race_time_ms: int):
        split_ms = race_time_ms - self._last_cp_time
        self._checkpoints.append((lap, cp_slot, race_time_ms, split_ms))
        self._last_cp_time = race_time_ms

    def record_off_road_start(self, race_time_ms: int):
        # Call when player leaves track
        self._off_road_start = race_time_ms

    def record_off_road_end(self, race_time_ms: int):
        # Call when player re-enter track
        if self._off_road_start is not None:
            duration = race_time_ms - self._off_road_start
            self._off_road.append((self._off_road_start, race_time_ms, duration))
            self._off_road_start = None

    def record_speed(self, elapsed_s: float, speed_kmh: float):
        # Call once per second
        self._speed.append((round(elapsed_s, 1), round(speed_kmh, 1)))

    def flush(self):
        if self._match_dir is None:
            return

        self._write_csv(
            "lap_checkpoints.csv",
            ["lap", "checkpoint", "race_time_ms", "split_ms"],
            self._checkpoints,
        )
        self._write_csv(
            "off_road.csv",
            ["start_ms", "end_ms", "duration_ms"],
            self._off_road,
        )
        self._write_csv(
            "speed_time.csv",
            ["elapsed_s", "speed_kmh"],
            self._speed,
        )

    # private ───────────────────────────────────────────────────────────────

    def _write_csv(self, filename: str, headers: list, rows: list):
        path = os.path.join(self._match_dir, filename)
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(headers)
            w.writerows(rows)


# Singleton ─────────────────────────────────────────────────────────────────
stats = StatsCollector()