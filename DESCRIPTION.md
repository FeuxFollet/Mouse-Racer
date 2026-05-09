# Project Description

## 1. Project Overview
Provide a high-level understanding of the project.

- **Project Name:** 
  Mouse Racer

- **Brief Description:**  
  Mouse Racer is a top-down 2D racing game built in Python using the Pygame library. The player controls a car by moving the mouse. The car will automatically steers and accelerates toward the cursor, allowing for smooth directional control. The game features multiple selectable cars with distinct stats, multiple hand-made race tracks, and a single AI opponent that races alongside the player. Tracks are rendered using Catmull-Rom splines to produce smooth curves, and a checkpoint gate system to ensure that the full lap is completed as intended.

- **Problem Statement:**  
  Traditional top-down racing games use arrow keys or WASD for steering, which becomes confusing quickly as the car's orientation changes constantly. This also limits steering precision, since inputs are binary: fully left or fully right, with no in-between. Mouse Racer solves this by letting the player guide the car exactly where they intend to go by pointing a cursor, making control feel natural and giving the player precise steering at all times.

- **Target Users:**  
  People who are interested in top-down or arcade racing games. The mouse-based control feature makes it accessible to casual players who find keyboard steering unintuitive.

- **Key Features:**  
  - **Mouse-driven steering** — The car continuously steers and accelerates toward the mouse cursor, enabling smooth, analogue-style control without any keyboard input during the race.
  - **Car and track selection menus** — Players can choose from multiple cars (each with unique speed, acceleration, and turning stats loaded from CSV) and multiple tracks (defined by JSON waypoint files), presented in selection screens with previews.
  - **Checkpoint enforcement** — Tracks use a gate-based checkpoint system that detects direction-aware crossings, ensuring laps are completed as intended.
  - **AI opponent** — A rival car which uses waypoint-following AI to provide a competition to the player.
  - **Particle effects** — Skid marks, dirt spray, smoke, and exhaust particles are generated dynamically based on the car's speed and road surface.
  - **Post-race statistics system** — Every race automatically saves lap checkpoint splits, off-road times, and a speed-over-time log to timestamped CSV files, viewable in a dedicated Tkinter + matplotlib statistics viewer.

---

## 2. Concept

### 2.1 Background

- Why this project exists
  This project exists because I wanted to create a new and unique way to play top-down racing games while solving the problem of difficult controls.
- What inspired the project
  I have always been interested in cars, racing, and sim racing, which are some of my main hobbies. Because of this passion, I decided to create a racing game project based on something I enjoy. My interest in racing games and vehicle control mechanics inspired me to design a game that offers a different driving experience from traditional top-down racers. 
- Importance of solving this problem  
  Difficult controls is what kept most people from trying out top-down racers which is why making this game can convince that group of people to try out top-down racing games.

### 2.2 Objectives

- **Implement mouse-based car control** — Develop a steering system where the car continuously orients and accelerates toward the mouse cursor, replacing traditional binary keyboard input with smooth, analogue-precision control.

- **Build a reusable track system** — Represent tracks as JSON waypoint files rendered into smooth Catmull-Rom spline surfaces at runtime, allowing new tracks to be added without changing any game code.

- **Enforce valid lap completion** — Implement a directional checkpoint gate system that uses line-segment intersection detection to ensure the player crosses every gate in the correct order before a lap is counted.

- **Support multiple selectable cars with distinct physics** — Load car stats (speed, acceleration, turn rate) from a CSV file at startup so that each car feels meaningfully different to drive, and present them through an animated selection screen with stat previews.

- **Provide a competent AI opponent** — Create an AI driver that follows track waypoints.

- **Collect race statistics** — Automatically record per-checkpoint lap splits, off-road event durations, and speed-over-time samples to timestamped CSV files after every race.

- **Visualise statistics** — Build a separate Tkinter and matplotlib application that reads the saved CSVs and presents summary tables, a speed-over-time line chart, a time-at-speed histogram, and an on/off-road pie chart.

* **Apply Object-Oriented Programming (OOP) principles** — Structure the project using Object-Oriented Programming concepts such as classes, encapsulation, inheritance, and modular design to improve code organisation, readability, maintainability, and scalability.

---

## 3. UML Class Diagram
Provide a UML class diagram that represents the system structure.

Your diagram must include:
- Classes  
- Attributes  
- Methods (optional but recommended)  
- Relationships (e.g., association, inheritance)

**Submission Requirement:**  
- Attach the UML Class Diagram in **.pdf format**

---

## 4. Object-Oriented Programming Implementation

### Entry Points & Configuration

- **main:** Entry point of the project. Loads car and track data from CSV and JSON files, then starts the application through the menu system in `screens`.
- **Config:** Global race settings container that stores shared race data such as waypoints, checkpoints, lap count, and track information.
- **Colors:** Static collection of named colour constants used consistently throughout all rendering and UI systems.
- **shared:** Stores globally shared pygame objects including the display surface, clock, and font dictionary.

### Menus & User Interface

- **Screens:** Contains the main menu, car selection menu, track selection menu, and `launch_game()` which transfers control to the main game system.
- **Button:** Reusable interactive button component featuring hover animations and glow effects.

### Core Game Systems

- **Game:** Main controller and master game loop responsible for managing updates, rendering order, and the pygame event loop.
- **Race:** Controls the race lifecycle including countdowns, pausing, updates, and speed sampling.
- **Car:** Core gameplay class responsible for mouse steering, AI waypoint following, acceleration, checkpoint detection, lap timing, and collision handling.
- **Track:** Builds the race track surface using Catmull-Rom spline interpolation and provides collision and checkpoint functionality.

### Rendering & Visual Effects

- **HUD:** Renders all race interface elements including timers, speed bars, lap counters, checkpoint progress, leaderboards, countdown overlays, and results screens.
- **ParticleSystem:** Manages all active `Particle` and `SkidMark` objects, updating and rendering them each frame.
- **Particle:** Represents an individual smoke, dirt, or exhaust particle with position, velocity, colour, and lifetime properties.
- **SkidMark:** Represents a fading tyre mark rendered at a fixed position.
- **Background:** Abstract base class defining the `update()` and `draw()` interface used by animated backgrounds.
- **DiagBG:** Animated scrolling diagonal stripe background effect used in menus.
- **SpeedLines:** Draws drifting horizontal speed lines during races to enhance the sensation of movement and speed.

### Data Loading

- **car_loader:** Loads vehicle statistics from `cars_data.csv` and imports PNG sprites to create car data dictionaries.
- **track_loader:** Loads track definitions from `tracks_data.csv` and their corresponding JSON waypoint files.

### Statistics System

- **StatsCollector:** Singleton statistics manager that records checkpoint split times, off-road events, and speed samples before saving them into timestamped CSV files.
- **StatsViewer:** Standalone Tkinter and matplotlib application used to visualise saved race statistics through tables and charts.

### Utilities

- **helpers:** Collection of utility functions including Catmull-Rom spline interpolation and line-segment intersection detection.
- **drawing:** Stateless rendering helper functions used for car previews and minimap rendering.
- **ui:** Low-level UI helper functions used for glowing text and styled translucent panels.

## 5. Statistical Data

### 5.1 Data Recording Method

Data collection is handled by the `StatsCollector` class, which follows the singleton
pattern to ensure only one instance is active per race session. It begins recording
automatically when the race starts and requires no manual input from the player.

Three types of events are captured during a race. First, every time a car crosses a
checkpoint gate, the car name, lap number, gate index, and a timestamp are logged.
Second, when a car leaves the track surface, an off-road start time is recorded, and
when it returns, the duration of that excursion is calculated and saved. Third, the
car's speed is sampled at regular intervals throughout the race alongside an elapsed
time value, building a continuous speed-over-time record.

At the end of each race, `StatsCollector.flush_to_csv()` is called, which writes all
collected data into a dedicated folder under `statistics/` named by combining the
current timestamp with the track name (e.g. `statistics/20240508_143201_forest/`).
Inside that folder, three CSV files are created:

- `lap_checkpoints.csv` — one row per checkpoint crossing, containing car name, lap
  number, gate index, and timestamp.
- `off_road.csv` — one row per off-road event, containing car name, start time, end
  time, and total duration in seconds.
- `speed_time.csv` — one row per speed sample, containing car name, elapsed time, and
  speed in pixels per second.

This folder-per-session structure means every race produces its own isolated dataset,
and historical sessions are never overwritten.


### 5.2 Data Features

To view these features either click "Statistics" button on the main menu or run stats_viewer.py

| Feature | Visualisation | Data Represented |
|---|---|---|
| Lap time | Table (Summary tab) | Total race time, fastest lap time, and other lap time related information |
| Off-road time | Table (Summary tab) | How often and long do you go off-road |
| Speed | Table (Summary tab) | The fastest recorded lap time per car across the full race session |
| Number of off-road events | Table (Summary tab) | How many separate times each car left the track, indicating driving consistency |
| On-road vs off-road time | Pie chart (Charts tab) | The proportion of total race time spent on and off the track surface per car |
| Speed over time | Line chart (Charts tab) | A continuous trace of the car's speed in pixels per second against elapsed race time, showing acceleration, braking, and off-road slowdowns |
| Time at speed | Histogram (Charts tab) | The distribution of how long the car spent at each speed range, revealing whether the car mostly cruised, accelerated, or was frequently slowed |

---

## 6. Changed Proposed Features (Optional)

- Economy system was removed due to it not fitting the game.
- On-road vs off-road time was changed to Pie Chart instead of Bar Chart for better visualization.
- Removed Distance traveled feature since it wasn't very useful.
- Added two more table features including off-road time and speed which was more useful.

---

## 7. External Sources
Give credit for any external materials used in the project.

Car Sprites:
- 2D Race Cars by looneybits: https://looneybits.itch.io/2d-race-cars [Sprites]
- 2D Sport Cars by looneybits: https://looneybits.itch.io/2d-sport-cars [Sprites]  

License:
[License .txt file](docs/license_cc_by_4_0.txt)