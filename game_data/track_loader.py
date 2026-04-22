import csv
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_CSV_PATH = os.path.join(_HERE, "tracks_data.csv")
_JSON_DIR = os.path.join(_HERE, "track_json")


def _auto_checkpoints(waypoints: list, count: int = 8) -> list:
    """Evenly space `count` checkpoint indices around the waypoint loop."""
    n = len(waypoints)
    return [int(i * n / count) for i in range(count)]


def load_tracks() -> list:
    """
    Read tracks_data.csv and return a list of track dicts.
    Skips rows whose JSON file cannot be found (prints a warning).
    Returns an empty list if the CSV itself is missing.
    """
    if not os.path.exists(_CSV_PATH):
        print(f"[track_loader] WARNING: tracks_data.csv not found at {_CSV_PATH}")
        return []

    tracks = []

    with open(_CSV_PATH, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)

        for row in reader:
            name      = row["name"].strip()
            json_file = row["json"].strip()
            laps_raw  = row["laps"].strip()

            try:
                laps = int(laps_raw)
            except ValueError:
                print(f"[track_loader] WARNING: bad laps value '{laps_raw}' "
                      f"for track '{name}' – skipping.")
                continue

            json_path = os.path.join(_JSON_DIR, json_file)
            if not os.path.exists(json_path):
                print(f"[track_loader] WARNING: JSON not found: {json_path} – skipping.")
                continue

            with open(json_path, encoding="utf-8") as jf:
                data = json.load(jf)

            waypoints   = data.get("waypoints", [])
            track_width = data.get("track_width", 80)

            raw_cp      = data.get("checkpoints", [])
            checkpoints = raw_cp if raw_cp else _auto_checkpoints(waypoints)

            tracks.append({
                "name":        name,
                "json_file":   json_file,
                "laps":        laps,
                "waypoints":   waypoints,
                "track_width": track_width,
                "checkpoints": checkpoints,
            })

    if not tracks:
        print("[track_loader] WARNING: no valid tracks were loaded.")

    return tracks