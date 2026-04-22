import pygame, sys
import v2_8
from game_data.car_loader   import load_cars
from game_data.track_loader import load_tracks

import game_components.shared as _s
from game_components.background import DiagBG, SpeedLines
from game_components.screens    import (screen_main, screen_car_select,
                                        screen_track_select, launch_game)


pygame.init()
_s.init()   # creates screen, clock, and all fonts


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    tracks = load_tracks()
    cars   = load_cars()

    bg    = DiagBG()
    lines = SpeedLines()

    while True:
        result = screen_main(bg, lines)
        if result == 'quit':
            pygame.quit(); sys.exit()

        if result == 'play':
            selected_car = screen_car_select(bg, lines, cars)

            if selected_car == 'back':
                continue

            selected_track = screen_track_select(bg, lines, tracks)
            if selected_track == 'back':
                continue

            pygame.mouse.set_visible(True)
            launch_game(selected_car, selected_track)
            # Re-init display after game closes pygame
            pygame.init()
            _s.init()


if __name__ == "__main__":
    main()
