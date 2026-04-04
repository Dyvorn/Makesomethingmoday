LOCATIONS = {
    1: {"name": "Earth Surface (Garden)", "ban_threshold": 10, "upgrade_required": None, "new_ing": None},
    2: {"name": "Moon Base", "ban_threshold": 25, "upgrade_required": "Rocket", "new_ing": "Moon Yeast"},
    3: {"name": "Mars Colony", "ban_threshold": 50, "upgrade_required": "Shuttle", "new_ing": "Martian Spice"},
    4: {"name": "Asteroid Belt Vending", "ban_threshold": 100, "upgrade_required": "Drone Fleet", "new_ing": "Void Salts"},
    5: {"name": "Jupiter Orbit Station", "ban_threshold": 200, "upgrade_required": "Orbital Station", "new_ing": "Gas Giant Mayo"}
}

UPGRADE_COSTS = {
    "Rocket": 100, "Shuttle": 500, "Drone Fleet": 2000, "Orbital Station": 10000
}