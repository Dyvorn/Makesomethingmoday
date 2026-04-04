import random
import json
from locations import LOCATIONS, UPGRADE_COSTS

class GameState:
    def __init__(self):
        self.day = 1
        self.actions_left = 3
        self.money = 20.0
        self.bread = 0
        self.meat = 0
        self.cheese = 0
        self.sandwiches = 0
        self.fuel = 0
        
        self.chapter = 1
        self.total_sold = 0
        self.chapter_sold = 0
        self.alert_level = 0
        self.is_game_over = False
        self.log = []
        
        # New: Sandwich Customization & Shop
        self.unlocked_ingredients = ["Basic Bread", "Mystery Meat", "Processed Cheese"]
        self.active_recipe = {"name": "The Default", "ingredients": ["Basic Bread", "Mystery Meat", "Processed Cheese"]}
        self.sandwich_quality = 1.0
        self.production_bonus = 1 # Number of sandwiches made per action
        self.hardware = {"Kitchen": "Old Toaster"}

        # Market Prices
        self.prices = {"bread": 2, "meat": 3, "cheese": 2, "fuel": 5}
        
        self.upgrades = {
            "Rocket": False,
            "Shuttle": False,
            "Drone Fleet": False,
            "Orbital Station": False
        }

    def add_log(self, text):
        self.log.append(text)
        if len(self.log) > 50:
            self.log.pop(0)

    def use_action(self):
        self.actions_left -= 1
        if self.actions_left <= 0:
            self.next_day()

    def next_day(self):
        self.day += 1
        self.actions_left = 3
        # Market fluctuation
        for item in self.prices:
            change = random.uniform(0.9, 1.2)
            self.prices[item] = round(self.prices[item] * change, 2)
        self.add_log(f"--- Day {self.day} Begins ---")

    def buy_ingredients(self):
        cost = self.prices["bread"] + self.prices["meat"] + self.prices["cheese"]
        if self.money >= cost:
            self.money -= cost
            self.bread += 1
            self.meat += 1
            self.cheese += 1
            self.add_log("Bought 1 set of ingredients.")
            self.use_action()
            return True
        return False

    def make_sandwiches(self):
        batch = min(self.bread, self.meat, self.cheese, self.production_bonus)
        if batch > 0:
            self.bread -= batch
            self.meat -= batch
            self.cheese -= batch
            self.sandwiches += batch
            self.add_log(f"Assembled {batch}x '{self.active_recipe['name']}'.")
            self.use_action()
            return True
        return False

    def sell_sandwiches(self):
        if self.sandwiches <= 0:
            return False

        # Logic for space logistics
        fuel_cost = 0
        if self.chapter == 2: fuel_cost = 50
        elif self.chapter == 3: fuel_cost = 150
        elif self.chapter >= 4: fuel_cost = 300

        if self.fuel < fuel_cost:
            self.add_log("Not enough fuel for delivery!")
            return False

        sold = min(self.sandwiches, random.randint(3, 8))
        base_price = 15 if self.chapter > 1 else 5
        # Quality and ingredient complexity drive price up
        revenue = round(sold * base_price * self.sandwich_quality * (len(self.active_recipe["ingredients"]) / 3), 2)

        self.money += revenue
        self.fuel = max(0, self.fuel - fuel_cost)
        self.sandwiches -= sold
        self.total_sold += sold
        self.chapter_sold += sold
        
        # Increase alert level
        self.alert_level += sold * 2
        self.add_log(f"Sold {sold} sandwiches for ${revenue}.")
        self.use_action()
        return True

    def buy_fuel(self):
        if self.money >= self.prices["fuel"] * 10:
            self.money -= self.prices["fuel"] * 10
            self.fuel += 200
            self.add_log("Refueled 200L.")
            if self.chapter == 1: # Safety for early game
                self.fuel = 1000
            self.use_action()
            return True
        return False

    def attempt_upgrade(self):
        """Handles the logic for upgrading to the next chapter."""
        next_chap = self.chapter + 1
        if next_chap in LOCATIONS:
            up_name = LOCATIONS[next_chap]["upgrade_required"]
            cost = UPGRADE_COSTS[up_name]
            if self.money >= cost:
                self.money -= cost
                self.chapter = next_chap
                if self.chapter == 2 and self.fuel == 0:
                    self.fuel = 500 # Initial fuel for the first flight
                self.alert_level = 0
                self.chapter_sold = 0
                self.use_action()
                return True, up_name
        return False, None

    def check_win_conditions(self):
        if self.money >= 500000 or self.day >= 50 or self.chapter > 5:
            self.is_game_over = True
            return True
        return False