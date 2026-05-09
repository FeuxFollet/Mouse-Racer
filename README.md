# MOUSE RACER

## Project Description

- Project by: Phirawit Sommaichaiya
- Game Genre: Racing

Mouse Racer is a top-down 2D racing game built in Python using the Pygame library. The player controls a car by moving the mouse. The car will automatically steers and accelerates toward the cursor, allowing for smooth directional control. The game features multiple selectable cars with distinct stats, multiple hand-made race tracks, and a single AI opponent that races alongside the player. Tracks are rendered using Catmull-Rom splines to produce smooth curves, and a checkpoint gate system to ensure that the full lap is completed as intended.

---

## Installation

To clone this project:
```sh
git clone https://github.com/FeuxFollet/Mouse-Racer.git
cd Mouse-Racer
```

To create and run a Python virtual environment for this project:

**Windows:**
```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**Mac/Linux:**
```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Running Guide
After activate Python Environment of this project, you can process to run the game by:

Window:
```bat
python main.py
```

Mac:
```sh
python3 main.py
```

---

## Project File Structure

```
Mouse-Racer/
├── main.py                        # Game entry point, RUN THE GAME HERE
├── v2_8.py                        # Game and Race classes, master game loop
├── requirements.txt               # Python dependencies (pygame, matplotlib, etc.)
├── README.md                      
├── DESCRIPTION.md                 # Project overview and UML
├── LICENSE                        # MIT License for the project
├── game_components/               # Core game logic package
│   ├── __init__.py
│   ├── car.py                     # Car class
│   ├── track.py                   # Track class
│   ├── race.py                    # Race class
│   ├── hud.py                     # HUD
│   ├── particles.py               # ParticleSystem
│   ├── background.py              # DiagBG and SpeedLines background classes
│   ├── screens.py                 # All menu screens
│   ├── config.py                  # Config, Colors
│   ├── shared.py                  # Global screen, clock, fonts
│   ├── ui.py                      # Button, glow_text, draw_panel
│   ├── drawing.py                 # Draw car preview and track minimap
│   └── helpers.py
├── game_data/                     # Assets and Data Loaders
│   ├── car_loader.py              # Reads cars_data.csv and car sprites
│   ├── track_loader.py            # Reads tracks_data.csv and track JSONs
│   ├── cars_data.csv              # Car stats (speed, acceleration, turn rate, scale)
│   ├── tracks_data.csv            # Track data (name, file, preview)
│   ├── car_sprites/               # Car PNG sprites
│   │   ├── car_1.png
│   │   ├── car_2.png
│   │   └── ...
│   └── track_json/                # Track json waypoints and checkpoints
│       ├── track_1.json
│       ├── track_2.json
│       └── ...
├── statistics_components/         # Statistics collection and visualisation
│   ├── __init__.py
│   ├── stats_collector.py         # Records data
│   └── stats_viewer.py            # Standalone Tkinter + matplotlib stats dashboard
└── statistics/                    # Auto-generated race session data
    └── EXAMPLE STATISTICS/        # Example data containing >100 rows
        ├── lap_checkpoints.csv    # Gate crossing splits per car per lap
        ├── off_road.csv           # Off-road excursion events and durations
        └── speed_time.csv         # Speed-over-time samples
```

---

## Tutorial / Usage
- Run main.py
- Click play button
- Choose a car
- Choose a circuit
- Start the race
- Complete the race and click esc to return to main menu
- Click statistics button on the main menu or run stats_viewer.py to view your statistics

---

## Game Features 
- **Mouse-driven steering** — The car continuously steers and accelerates toward the mouse cursor, enabling smooth, analogue-style control without any keyboard input during the race.
- **Car and track selection menus** — Players can choose from multiple cars (each with unique speed, acceleration, and turning stats loaded from CSV) and multiple tracks (defined by JSON waypoint files), presented in selection screens with previews.
- **Checkpoint enforcement** — Tracks use a gate-based checkpoint system that detects direction-aware crossings, ensuring laps are completed as intended.
- **AI opponent** — A rival car which uses waypoint-following AI to provide a competition to the player.
- **Particle effects** — Skid marks, dirt spray, smoke, and exhaust particles are generated dynamically based on the car's speed and road surface.
- **Post-race statistics system** — Every race automatically saves lap checkpoint splits, off-road times, and a speed-over-time log to timestamped CSV files, viewable in a dedicated Tkinter + matplotlib statistics viewer.

---

## External sources
Acknowledge to:
1. 2D Race Cars by looneybits: https://looneybits.itch.io/2d-race-cars [Sprites]
2. 2D Sport Cars by looneybits: https://looneybits.itch.io/2d-sport-cars [Sprites]  