import csv
import os
import pygame

_HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(_HERE, "cars_data.csv")
CAR_FOLDER = os.path.join(_HERE, "car_sprites")

def load_cars():
    cars = []

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            sprite_path = os.path.join(CAR_FOLDER, row["sprite"])

            car = {
                "name": row["name"],
                "sprite": pygame.image.load(sprite_path).convert_alpha(),
                "ACCEL": float(row["accel"]),
                "BRAKE_FRICTION": float(row["brake_friction"]),
                "COAST_FRICTION": float(row["coast_friction"]),
                "GRASS_FRICTION": float(row["grass_friction"]),
                "MAX_SPEED": float(row["max_speed"]),
                "MAX_SPEED_GRASS": float(row["max_speed_grass"]),
                "TURN_RATE": float(row["turn_rate"]),
                "LENGTH": int(row["length"]),
                "WIDTH": int(row["width"]),
                "SCALE": float(row["scale"]),
            }
            cars.append(car)

    return cars