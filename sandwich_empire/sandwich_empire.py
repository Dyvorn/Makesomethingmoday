import sys
from PyQt6.QtWidgets import QApplication, QMessageBox, QInputDialog
from game_state import GameState
from ui import SandwichUI, GovLetterDialog, KitchenDialog
from locations import LOCATIONS, UPGRADE_COSTS
from events import GOV_LETTERS, get_random_event

class GameController:
    def __init__(self):
        self.gs = GameState()
        self.ui = SandwichUI(self.gs, self)
        self.gs.add_log("Welcome to the Garden. Start selling sandwiches.")
        self.ui.refresh_ui()

    def handle_buy(self):
        if self.gs.buy_ingredients():
            self.process_turn()

    def handle_make(self):
        if self.gs.make_sandwiches():
            self.process_turn()

    def handle_sell(self):
        if self.gs.sell_sandwiches():
            self.process_turn()

    def handle_fuel(self):
        if self.gs.buy_fuel():
            self.process_turn()

    def handle_upgrade(self):
        success, up_name = self.gs.attempt_upgrade()
        if success:
            self.gs.add_log(f"UPGRADE COMPLETE: {up_name} acquired. Moving to {LOCATIONS[self.gs.chapter]['name']}.")
            new_ing = LOCATIONS[self.gs.chapter].get("new_ing")
            if new_ing:
                self.gs.unlocked_ingredients.append(new_ing)
                self.gs.add_log(f"NEW RESOURCE: {new_ing} is now available in the kitchen.")
            self.process_turn()

    def handle_kitchen(self):
        dlg = KitchenDialog(self.gs.unlocked_ingredients, self.ui)
        if dlg.exec():
            selected = [item.text() for item in dlg.selectedItems()]
            if len(selected) >= 3:
                name, ok = QInputDialog.getText(self.ui, "Naming", "Name your creation:")
                if ok and name:
                    self.gs.active_recipe = {"name": name, "ingredients": selected}
                    self.gs.sandwich_quality += 0.2
                    self.gs.add_log(f"New Recipe perfected: {name}")
                    self.gs.use_action()
                    self.process_turn()

    def handle_shop(self):
        cost = 150
        if self.gs.money >= cost:
            self.gs.money -= cost
            self.gs.production_bonus += 2
            self.gs.add_log("Hardware Upgrade: Industrial Oven. Making 3 subs at once!")
            self.gs.use_action()
            self.process_turn()

    def handle_wait(self):
        self.gs.add_log("Resting... ingredients are aging.")
        self.gs.next_day()
        self.process_turn()
    def process_turn(self):
        # Check for random events
        ev = get_random_event()
        if ev: self.gs.add_log(f"EVENT: {ev}")

        # Check for Government Ban
        current_loc = LOCATIONS.get(self.gs.chapter)
        threshold = current_loc["ban_threshold"] if current_loc else 100
        if self.gs.alert_level >= threshold:
            letter = GOV_LETTERS.get(self.gs.chapter, "The government has seized your bread.")
            GovLetterDialog(letter, self.ui).exec()
            self.gs.add_log("!!! LOCATION BANNED !!! You must move to another planet to sell.")

        # Check win/loss
        if self.gs.check_win_conditions():
            res = "Space Food Emperor" if self.gs.money > 100000 else "Black Market Legend"
            QMessageBox.information(self.ui, "GAME OVER", f"Your journey ends. Final Standing: {res}\nTotal Days: {self.gs.day}\nFinal Cash: ${self.gs.money:.2f}")
            self.gs.is_game_over = True

        self.ui.refresh_ui()

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    controller = GameController()
    controller.ui.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()