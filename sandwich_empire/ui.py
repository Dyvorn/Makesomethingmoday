from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QDialog,
                             QLabel, QPushButton, QTextEdit, QProgressBar, QInputDialog, QListWidget, QAbstractItemView)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from locations import LOCATIONS, UPGRADE_COSTS

class SandwichUI(QMainWindow):
    def __init__(self, game_state, controller):
        super().__init__()
        self.gs = game_state
        self.controller = controller
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Sandwich Empire: Lunar Bureaucracy")
        self.setFixedSize(750, 650)
        # Paper Aesthetic Stylesheet
        self.setStyleSheet("""
            QMainWindow { background-color: #F4F1EA; }
            QLabel { color: #2B2B2B; font-family: 'Courier New'; }
            QTextEdit { background-color: #EFECE5; border: 1px solid #D1CFC8; color: #3A3A3A; font-family: 'Courier New'; }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(30, 30, 30, 30)

        # Header Stats
        self.stats_label = QLabel()
        self.stats_label.setFont(QFont("Courier New", 13, QFont.Weight.Bold))
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.stats_label)

        # Alert Level Bar
        self.alert_container = QWidget()
        alert_layout = QHBoxLayout(self.alert_container)
        alert_layout.addWidget(QLabel("OFFICIAL SCRUTINY:"))
        self.alert_bar = QProgressBar()
        self.alert_bar.setStyleSheet("QProgressBar { border: 2px solid #2B2B2B; height: 15px; text-align: center; } QProgressBar::chunk { background-color: #8B0000; }")
        alert_layout.addWidget(self.alert_bar)
        self.main_layout.addWidget(self.alert_container)

        # Log Display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.main_layout.addWidget(self.log_display)

        # Action Buttons
        btn_grid = QVBoxLayout()
        
        row1 = QHBoxLayout()
        self.btn_buy = QPushButton("Buy Ingredients")
        self.btn_make = QPushButton("Make Sandwiches")
        self.btn_sell = QPushButton("Sell Sandwiches")
        self.btn_kitchen = QPushButton("R&D Kitchen")
        row1.addWidget(self.btn_buy)
        row1.addWidget(self.btn_make)
        row1.addWidget(self.btn_sell)
        row1.addWidget(self.btn_kitchen)
        
        row2 = QHBoxLayout()
        self.btn_fuel = QPushButton("Buy Fuel ($)")
        self.btn_upgrade = QPushButton("Upgrade Logistics")
        self.btn_day = QPushButton("Wait (Skip Day)")
        self.btn_hardware = QPushButton("Shop Hardware")
        row2.addWidget(self.btn_fuel)
        row2.addWidget(self.btn_upgrade)
        row2.addWidget(self.btn_day)


        btn_grid.addLayout(row1)
        btn_grid.addLayout(row2)
        
        all_btns = [self.btn_buy, self.btn_make, self.btn_sell, self.btn_fuel, self.btn_upgrade, self.btn_day, self.btn_kitchen, self.btn_hardware]
        for btn in all_btns:
            btn.setStyleSheet("""
                QPushButton { background-color: #E8E4D9; border: 2px solid #2B2B2B; padding: 10px; font-family: 'Courier New'; font-weight: bold; text-transform: uppercase; }
                QPushButton:hover { background-color: #D1CDC0; }
                QPushButton:pressed { background-color: #BDB9AD; margin-top: 2px; }
                QPushButton:disabled { border: 1px solid #444; color: #666; }
            """)
        
        self.main_layout.addLayout(btn_grid)
        
        # Connect signals
        self.btn_buy.clicked.connect(self.controller.handle_buy)
        self.btn_make.clicked.connect(self.controller.handle_make)
        self.btn_sell.clicked.connect(self.controller.handle_sell)
        self.btn_fuel.clicked.connect(self.controller.handle_fuel)
        self.btn_upgrade.clicked.connect(self.controller.handle_upgrade)
        self.btn_day.clicked.connect(self.controller.handle_wait)
        self.btn_kitchen.clicked.connect(self.controller.handle_kitchen)
        self.btn_hardware.clicked.connect(self.controller.handle_shop)

        self.refresh_ui()

    def refresh_ui(self):
        loc_data = LOCATIONS[self.gs.chapter]
        loc_name = loc_data["name"]
        threshold = loc_data["ban_threshold"]
        
        # Progressive UI Unlocking
        is_space_age = self.gs.chapter >= 2
        has_scrolled_eyes = self.gs.total_sold >= 2

        fuel_str = f" | Fuel: {self.gs.fuel}L" if is_space_age else ""
        
        # Hide/Show official scrutiny
        self.alert_container.setVisible(has_scrolled_eyes)
        self.btn_fuel.setVisible(is_space_age)
        self.btn_kitchen.setVisible(self.gs.total_sold >= 5)
        self.btn_hardware.setVisible(self.gs.money >= 50)
        # Hide upgrade button until we actually reach the ban or close to it
        self.btn_upgrade.setVisible(self.gs.alert_level >= threshold * 0.5 or self.gs.money >= 50)

        stats = (f"DATE: Day {self.gs.day} | REGION: {loc_name.upper()} | QUOTA: {self.gs.actions_left}\n"
                 f"ASSETS: ${self.gs.money:.2f}{fuel_str} | RECIPE: {self.gs.active_recipe['name']}\n"
                 f"B:{self.gs.bread} M:{self.gs.meat} C:{self.gs.cheese} | Subs: {self.gs.sandwiches}")
        self.stats_label.setText(stats)
        
        # Calculate percentage based on local threshold
        self.alert_bar.setValue(min(100, int((self.gs.alert_level / threshold) * 100)))
        
        formatted_log = [f"> {line}" for line in self.gs.log]
        self.log_display.setPlainText("\n".join(formatted_log))
        self.log_display.verticalScrollBar().setValue(self.log_display.verticalScrollBar().maximum())

        # Update Upgrade button text
        next_chap = self.gs.chapter + 1
        if next_chap in LOCATIONS:
            up_name = LOCATIONS[next_chap]["upgrade_required"]
            cost = UPGRADE_COSTS[up_name]
            self.btn_upgrade.setText(f"Research {up_name} (${cost})")
            self.btn_upgrade.setEnabled(self.gs.money >= cost)
        else:
            self.btn_upgrade.setText("Maximum Expansion Reached")
            self.btn_upgrade.setEnabled(False)

        # Disable sell if alert is too high (bureaucracy transition)
        if self.gs.alert_level >= threshold:
            self.btn_sell.setEnabled(False)
            self.btn_sell.setText("LOCATION BANNED")
        else:
            self.btn_sell.setEnabled(True)
            self.btn_sell.setText("Sell Sandwiches")

        if self.gs.is_game_over:
            self.setEnabled(False)

class GovLetterDialog(QDialog):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setWindowTitle("OFFICIAL CORRESPONDENCE")
        self.setFixedSize(450, 300)
        self.setStyleSheet("background-color: #F4F1EA; border: 5px double #8B0000;")
        
        layout = QVBoxLayout(self)
        
        stamp = QLabel("CONFIDENTIAL / BANNED")
        stamp.setStyleSheet("color: #8B0000; font-weight: bold; font-family: 'Courier New'; font-size: 18px;")
        stamp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(stamp)

        body = QLabel(text)
        body.setWordWrap(True)
        body.setStyleSheet("color: #2B2B2B; font-family: 'Courier New'; font-size: 14px; margin: 10px;")
        layout.addWidget(body)

        btn = QPushButton("I UNDERSTAND")
        btn.setStyleSheet("background-color: #2B2B2B; color: white; padding: 10px; font-weight: bold;")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)

class KitchenDialog(QDialog):
    def __init__(self, unlocked, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sandwich Design Studio")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select Ingredients for your Signature Sub:"))
        
        self.list = QListWidget()
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.list.addItems(unlocked)
        layout.addWidget(self.list)

        btn = QPushButton("Finalize Recipe (1 Action)")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)