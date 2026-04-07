import sys
import os
import random
import math
import json
from pathlib import Path
from PyQt6.QtCore import Qt, QRect, QPropertyAnimation, QEasingCurve, pyqtProperty, QPoint, QTimer, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QLinearGradient
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QLineEdit,
    QSlider,
)

# --- Configuration & Constants ---
BASE_DIR = Path(__file__).parent
SAVE_FILE = BASE_DIR / "save_data.json"
MUSIC_FILE = BASE_DIR / "background_music.mp3"

COLORS = {
    "primary": "#ffca28",
    "primary_hover": "#ffd54f",
    "primary_border": "#ffa000",
    "accent": "#f06292",
    "text_dark": "#5d4037",
    "sky_top": "#81d4fa",
    "sky_bottom": "#29b6f6",
    "cloud": "#ffffff",
    "cloud_outline": "#bbdefb"
}

GAME_COLORS = {
    "bread": "#d7ccc8",
    "lettuce": "#8bc34a",
    "tomato": "#ef5350",
    "cheese": "#ffeb3b"
}

class Screen:
    MAIN_MENU = 0
    SAVE_SLOTS = 1
    GAME = 2

class JuicyButton(QPushButton):
    def __init__(self, text):
        super().__init__(text)
        self._scale = 1.0
        self._selected = False
        self.setMinimumHeight(80)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_style()

        self.anim = QPropertyAnimation(self, b"scale_prop")
        self.anim.setDuration(150)
        
        self.press_anim = QPropertyAnimation(self, b"scale_prop")
        self.press_anim.setDuration(50)
        self.press_anim.setEasingCurve(QEasingCurve.Type.OutQuad)

    def refresh_style(self):
        border_col = "#ffffff" if self._selected else COLORS["primary_border"]
        bg_col = COLORS["primary_hover"] if self._selected else COLORS["primary"]
        
        self.setStyleSheet(f"""
            JuicyButton {{
                background-color: {bg_col};
                color: {COLORS["text_dark"]};
                border-radius: 30px;
                font-size: 24px;
                font-weight: bold;
                padding: 8px;
                border: 4px solid {border_col};
                margin: 5px;
            }}
            JuicyButton:hover {{
                background-color: {COLORS["primary_hover"]};
                border: 4px solid #ffffff;
            }}
            JuicyButton:pressed {{
                background-color: {COLORS["primary_border"]};
                border: 4px solid #3e2723;
            }}
        """)

    @pyqtProperty(float)
    def scale_prop(self):
        return self._scale

    @scale_prop.setter
    def scale_prop(self, value):
        self._scale = value
        self.update()

    @pyqtProperty(bool)
    def selected(self):
        return self._selected

    @selected.setter
    def selected(self, value):
        self._selected = value
        self.refresh_style()

    def enterEvent(self, event):
        self.anim.stop()
        self.anim.setEndValue(1.1)
        self.anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.anim.stop()
        self.anim.setEndValue(1.0)
        self.anim.start()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self.press_anim.setEndValue(0.95)
        self.press_anim.start()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.press_anim.setEndValue(1.1 if self.underMouse() else 1.0)
        self.press_anim.start()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(self._scale, self._scale)
        painter.translate(-self.width() / 2, -self.height() / 2)
        super().paintEvent(event)


class CloudTitle(QWidget):
    def __init__(self, text: str):
        super().__init__()
        self._text = text
        self._y_offset = 0
        self.setFixedHeight(140)

    @pyqtProperty(int)
    def y_offset(self):
        return self._y_offset

    @y_offset.setter
    def y_offset(self, value):
        self._y_offset = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        painter.translate(0, self._y_offset)
        painter.setPen(QPen(QColor(COLORS["cloud_outline"]), 4))
        painter.setBrush(QBrush(QColor(COLORS["cloud"])))
        
        # Dynamic Cloud geometry based on widget width
        w, h = self.width(), self.height()
        mid_x = w // 2
        
        # Left clusters
        painter.drawEllipse(mid_x - 420, 40, 90, 90)
        painter.drawEllipse(mid_x - 370, 10, 120, 120)
        # Right clusters
        painter.drawEllipse(mid_x + 330, 40, 90, 90)
        painter.drawEllipse(mid_x + 250, 10, 120, 120)
        # Top filler
        painter.drawEllipse(mid_x - 100, 0, 200, 100)
        # Main Body
        painter.drawRoundedRect(mid_x - 350, 40, 700, 70, 35, 35)

        # Draw the Text manually so it stays locked to the cloud movement
        font = QFont("Segoe UI", 36)
        font.setBold(True)
        painter.setFont(font)
        
        # Text Shadow for that "Loud" feel
        painter.setPen(QColor(0, 0, 0, 30))
        painter.drawText(self.rect().translated(3, 3), Qt.AlignmentFlag.AlignCenter, self._text)
        
        painter.setPen(QColor("#3949ab"))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._text)


class MainMenu(QWidget):
    def __init__(self, audio_output=None, switch_callback=None):
        super().__init__()
        self.animation = None # Animation for the cloud title
        self.audio_output = audio_output # Passed from MainWindow for volume control
        self.switch_callback = switch_callback # Callback to switch screens in QStackedWidget
        self.init_ui()
        self.start_animation()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.addStretch(2)

        cloud_container = QHBoxLayout()
        self.cloud_title = CloudTitle("🥪 OVER‑SCOPED SANDWICH SIMULATOR 🥪")
        self.cloud_title.setMinimumWidth(900)
        cloud_container.addWidget(self.cloud_title)
        main_layout.addLayout(cloud_container)
        main_layout.addSpacing(10)

        # Subtitle
        subtitle = QLabel("THE ULTIMATE OVER-ENGINEERED LUNCH EXPERIENCE")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(
            "font-size: 20px; color: #ffffff; font-weight: bold; letter-spacing: 4px;"
            "background-color: rgba(240, 98, 146, 0.8); padding: 15px; border-radius: 10px;"
        )
        main_layout.addWidget(subtitle)

        # Volume Slider Container
        vol_layout = QHBoxLayout()
        vol_container = QWidget()
        vol_container.setFixedWidth(400)
        vol_inner_layout = QHBoxLayout(vol_container)
        
        vol_label = QLabel("🎵 AUDIO")
        vol_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff; background: transparent;")
        
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 12px; background: %s; border-radius: 6px; }
            QSlider::handle:horizontal { background: %s; border: 3px solid white; width: 24px; margin: -6px 0; border-radius: 12px; }
        """ % (COLORS["primary_border"], COLORS["accent"]))
        if self.audio_output:
            self.volume_slider.valueChanged.connect(lambda v: self.audio_output.setVolume(v / 100.0))
        
        vol_inner_layout.addWidget(vol_label)
        vol_inner_layout.addWidget(self.volume_slider)
        vol_layout.addStretch()
        vol_layout.addWidget(vol_container)
        vol_layout.addStretch()
        main_layout.addLayout(vol_layout)

        main_layout.addStretch(1)

        # Buttons
        button_layout = QVBoxLayout()
        button_layout.setContentsMargins(500, 0, 500, 0) # Center the stack with wide margins
        button_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        button_layout.setSpacing(20)

        play_button = JuicyButton("▶ START GAME")
        play_button.clicked.connect(self.on_play)
        
        button_layout.addWidget(play_button)

        main_layout.addLayout(button_layout)
        main_layout.addStretch(2)

        self.setLayout(main_layout)

    def start_animation(self):
        # Smooth floating animation
        self.animation = QPropertyAnimation(self.cloud_title, b"y_offset", self)
        self.animation.setDuration(2000)
        self.animation.setStartValue(0)
        self.animation.setKeyValueAt(0.5, -20)
        self.animation.setEndValue(0)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        self.animation.setLoopCount(-1)
        self.animation.start()

    # Button slots – we’ll wire these to the game later
    def on_play(self):
        if self.switch_callback:
            self.switch_callback(Screen.SAVE_SLOTS)



class SaveSlotMenu(QWidget):
    def __init__(self, switch_callback=None):
        super().__init__()
        self.switch_callback = switch_callback
        self.selected_slot = None
        self.selected_diff = "NORMAL"
        self.save_slots = self.load_saves()
        self.slot_buttons = {} # Map slot_id -> button
        self.diff_buttons = {}
        self.init_ui()
        self.update_slot_visuals()

    def load_saves(self):
        """Loads save data from JSON file or returns empty slots."""
        if SAVE_FILE.exists():
            try:
                with open(SAVE_FILE, 'r') as f:
                    data = json.load(f)
                    return {int(k): v for k, v in data.items()}
            except Exception as e:
                print(f"Error loading save: {e}")
        return {1: None, 2: None, 3: None}

    def save_to_file(self):
        """Saves current slots to JSON file."""
        try:
            with open(SAVE_FILE, 'w') as f:
                json.dump(self.save_slots, f, indent=4)
        except Exception as e:
            print(f"Error saving to file: {e}")

    def get_slot_text(self, slot_id):
        """Generates text based on current save data."""
        data = self.save_slots.get(slot_id)
        if data:
            return f"SLOT {slot_id}\n{data['name'].upper()}\nDay {data['day']} | ${data['money']}\nRank: {data['rank']}"
        return f"SLOT {slot_id}\n(EMPTY)"

    def init_ui(self):
        layout = QVBoxLayout()
        layout.addStretch(1)

        # Title
        title = QLabel("SELECT SAVE SLOT")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 40px; font-weight: bold; color: #ffffff; letter-spacing: 2px;")
        layout.addWidget(title)
        layout.addSpacing(30)

        # Slots Row
        slot_layout = QHBoxLayout()
        slot_layout.setContentsMargins(100, 0, 100, 0)
        for i in range(1, 4):
            btn = JuicyButton("")
            btn.setFixedHeight(200)
            btn.clicked.connect(lambda _, x=i: self.on_slot_selected(x))
            self.slot_buttons[i] = btn
            slot_layout.addWidget(btn)
        layout.addLayout(slot_layout)

        layout.addSpacing(40)

        # Setup Details (Shop Name)
        details_layout = QVBoxLayout()
        details_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        name_label = QLabel("NAME YOUR SANDWICH EMPIRE:")
        name_label.setStyleSheet("font-size: 18px; color: #ffffff; font-weight: bold;")
        details_layout.addWidget(name_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Bread Zeppelin...")
        self.name_input.setFixedWidth(400)
        self.name_input.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                border: 4px solid %s;
                border-radius: 15px;
                padding: 10px;
                font-size: 20px;
                color: #3949ab;
            }
        """ % COLORS["accent"])
        details_layout.addWidget(self.name_input, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addLayout(details_layout)
        layout.addSpacing(20)

        # Difficulty Selectors
        diff_layout = QHBoxLayout()
        diff_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        diff_label = QLabel("DIFFICULTY:")
        diff_label.setStyleSheet("font-size: 18px; color: #ffffff; font-weight: bold; margin-right: 10px;")
        diff_layout.addWidget(diff_label)

        for level in ["EASY", "NORMAL", "OVER-SCOPED"]:
            btn = JuicyButton(level)
            btn.setMinimumHeight(50)
            btn.setFixedWidth(150)
            btn.clicked.connect(lambda _, l=level: self.set_difficulty(l))
            self.diff_buttons[level] = btn
            diff_layout.addWidget(btn)
        
        self.set_difficulty("NORMAL") # Initial highlight
        
        layout.addLayout(diff_layout)
        layout.addStretch(1)

        # Bottom Navigation
        nav_layout = QHBoxLayout()
        self.back_btn = JuicyButton("◀ BACK")
        self.back_btn.setFixedWidth(200)
        self.back_btn.clicked.connect(lambda: self.switch_callback(Screen.MAIN_MENU))

        self.delete_btn = JuicyButton("🗑 DELETE")
        self.delete_btn.setFixedWidth(200)
        self.delete_btn.clicked.connect(self.on_delete_clicked)
        self.delete_btn.hide()

        self.start_btn = JuicyButton("READY! ▶")
        self.start_btn.setFixedWidth(300)
        self.start_btn.clicked.connect(self.on_ready_clicked)

        nav_layout.addStretch()
        nav_layout.addWidget(self.back_btn)
        nav_layout.addWidget(self.delete_btn)
        nav_layout.addWidget(self.start_btn)
        nav_layout.addStretch()
        layout.addLayout(nav_layout)
        layout.addSpacing(50) # Add some spacing at the bottom

        self.setLayout(layout)

    def set_difficulty(self, level):
        self.selected_diff = level
        for name, btn in self.diff_buttons.items():
            is_selected = (name == level)
            bg = COLORS["accent"] if is_selected else "#bbdefb"
            txt = "white" if is_selected else COLORS["text_dark"]
            border = "4px solid white" if is_selected else "2px solid #ffffff"
            
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg};
                    color: {txt};
                    border: {border};
                    border-radius: 10px;
                    font-weight: bold;
                    padding: 5px;
                    font-size: 14px;
                }}
                QPushButton:hover {{ background-color: #e3f2fd; color: {COLORS["text_dark"]}; }}
            """)

    def update_slot_visuals(self):
        """Synchronizes slot button text and highlighting with internal state."""
        for i, btn in self.slot_buttons.items():
            btn.setText(self.get_slot_text(i))
            btn.selected = (i == self.selected_slot)

        # Update delete button visibility (only show if slot has data)
        has_data = self.selected_slot is not None and self.save_slots.get(self.selected_slot) is not None
        self.delete_btn.setVisible(has_data)

    def on_slot_selected(self, slot_id):
        self.selected_slot = slot_id
        self.update_slot_visuals()

        data = self.save_slots.get(slot_id)
        if data:
            self.name_input.setText(data['name']) # Pre-fill name if slot has data
            self.set_difficulty(data.get('difficulty', 'NORMAL'))
        else:
            self.name_input.clear() # Clear name input for new game
            self.set_difficulty('NORMAL')

    def on_delete_clicked(self):
        if self.selected_slot and self.save_slots.get(self.selected_slot):
            self.save_slots[self.selected_slot] = None
            self.save_to_file()
            # Re-trigger selection logic to clear input fields and update visuals
            self.on_slot_selected(self.selected_slot)

    def on_ready_clicked(self):
        if self.selected_slot is None:
            print("No slot selected!")
            return

        shop_name = self.name_input.text().strip()
        if not shop_name:
            shop_name = "Unnamed Sandwich Empire" # Default name if none entered
        
        # Initialize new game stats or update existing name
        if self.save_slots[self.selected_slot] is None:
            self.save_slots[self.selected_slot] = {
                "name": shop_name, "day": 1, "money": 100, "rank": "Dishwasher", "difficulty": self.selected_diff
            }
        else:
            self.save_slots[self.selected_slot]["name"] = shop_name
            self.save_slots[self.selected_slot]["difficulty"] = self.selected_diff

        self.save_to_file()
        self.update_slot_visuals() # Update UI immediately before switching
        if self.switch_callback:
            self.switch_callback(Screen.GAME, self.save_slots[self.selected_slot])


class GameScreen(QWidget):
    def __init__(self, switch_callback=None):
        super().__init__()
        self.switch_callback = switch_callback
        self.session = None
        self.init_ui()

    def update_game_data(self, data):
        """Initializes a new gameplay session with save data."""
        self.session = data 
        self.game_label.setText(f"WELCOME TO {data['name'].upper()}!")
        self.stats_label.setText(f"Day: {data['day']} | Cash: ${data['money']} | Rank: {data['rank']}")

    def init_ui(self):
        layout = QVBoxLayout()
        
        # --- Header ---
        header = QHBoxLayout()
        self.game_label = QLabel("GAME LOADED")
        self.game_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.game_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #ffffff;")
        
        exit_btn = JuicyButton("✖")
        exit_btn.setFixedSize(60, 60)
        exit_btn.clicked.connect(lambda: self.switch_callback(Screen.MAIN_MENU))
        
        header.addWidget(self.game_label, 1)
        header.addWidget(exit_btn)
        layout.addLayout(header)

        self.stats_label = QLabel("")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stats_label.setStyleSheet("font-size: 20px; color: #3e2723; background: #ffca28; padding: 10px; border-radius: 10px;")
        layout.addWidget(self.stats_label)

        # --- Gameplay Area ---
        gameplay_layout = QHBoxLayout()
        
        # Left: Orders Panel
        self.orders_panel = QVBoxLayout()
        order_placeholder = QLabel("ORDERS\n(Waiting...)")
        order_placeholder.setStyleSheet("background: rgba(0,0,0,50); color: white; border-radius: 15px; padding: 20px;")
        order_placeholder.setFixedWidth(250)
        self.orders_panel.addWidget(order_placeholder)
        
        # Middle: Prep Table
        self.prep_table = QVBoxLayout()
        table_placeholder = QLabel("PREP TABLE\n(Stack ingredients here!)")
        table_placeholder.setStyleSheet("background: #efebe9; border: 5px dashed #a1887f; border-radius: 20px;")
        table_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.prep_table.addWidget(table_placeholder)
        
        # Right: Inventory/Ingredients
        self.ingredients_panel = QVBoxLayout()
        ing_placeholder = QLabel("INGREDIENTS")
        ing_placeholder.setStyleSheet("background: rgba(255,255,255,50); border-radius: 15px; padding: 10px;")
        ing_placeholder.setFixedWidth(200)
        self.ingredients_panel.addWidget(ing_placeholder)
        
        gameplay_layout.addLayout(self.orders_panel)
        gameplay_layout.addLayout(self.prep_table, 1)
        gameplay_layout.addLayout(self.ingredients_panel)
        
        layout.addLayout(gameplay_layout, 1)

        self.setLayout(layout)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Over‑Scoped Sandwich Simulator")

        # Audio Setup
        self.audio_output = QAudioOutput()
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio_output)

        if MUSIC_FILE.exists():
            self.player.setSource(QUrl.fromLocalFile(str(MUSIC_FILE)))
            self.player.setLoops(QMediaPlayer.Loops.Infinite)
        self.audio_output.setVolume(0.5)
        self.player.play()

        # Background Animation Setup (moved from MainMenu to MainWindow)
        self.bg_clouds = []
        for _ in range(6):
            self.bg_clouds.append({'pos': QPoint(random.randint(0, 1920), random.randint(0, 1080)), 
                                   'speed': random.randint(1, 3), 'size': random.randint(100, 300)})
        self.sun_angle = 0
        self.sandwich_birds = []
        for _ in range(4):
            self.sandwich_birds.append({'pos': QPoint(random.randint(0, 1920), random.randint(50, 400)), 
                                       'speed': random.randint(4, 7), 'flap': random.random() * 6.28})
        
        self.bg_timer = QTimer(self)
        self.bg_timer.timeout.connect(self.update_bg)
        self.bg_timer.start(30)

        # Borderless Fullscreen
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.showFullScreen()

        # Light blue background and cartoony cloud style
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: %s;
            }
            """ % COLORS["sky_top"]
        )

        # Main Stack to manage different screens
        self.stack = QStackedWidget()
        
        # Custom navigation logic
        def navigate(index, data=None):
            if index == Screen.GAME and data:
                # Update the game screen with data before switching
                self.game_screen.update_game_data(data)
            self.stack.setCurrentIndex(index)

        self.main_menu = MainMenu(self.audio_output, navigate)
        self.save_menu = SaveSlotMenu(navigate)
        self.game_screen = GameScreen(navigate)
        
        self.stack.addWidget(self.main_menu)
        self.stack.addWidget(self.save_menu)
        self.stack.addWidget(self.game_screen)
        
        self.setCentralWidget(self.stack)

    def update_bg(self): # Background update logic (moved from MainMenu)
        # Drift the clouds
        for cloud in self.bg_clouds:
            cloud['pos'].setX(cloud['pos'].x() - cloud['speed'])
            if cloud['pos'].x() < -cloud['size']:
                cloud['pos'].setX(self.width() + cloud['size'])
        
        # Update Sun rotation and Bird positions/flapping
        self.sun_angle = (self.sun_angle + 1) % 360
        for bird in self.sandwich_birds:
            bird['pos'].setX(bird['pos'].x() - bird['speed'])
            bird['flap'] += 0.3
            if bird['pos'].x() < -100:
                bird['pos'].setX(self.width() + 100)
                bird['pos'].setY(random.randint(50, 400))

        self.update()

    def paintEvent(self, event): # Background drawing logic (moved from MainMenu)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw Sky Gradient
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, QColor("#81d4fa"))
        gradient.setColorAt(1.0, QColor("#29b6f6"))
        painter.fillRect(self.rect(), gradient)

        # Draw drifting background clouds
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 60))
        for cloud in self.bg_clouds:
            painter.drawEllipse(cloud['pos'].x(), cloud['pos'].y(), cloud['size'], cloud['size'] // 2)

        # Draw Sandwich Birds
        for bird in self.sandwich_birds:
            painter.save()
            painter.translate(bird['pos'])
            flap_y = math.sin(bird['flap']) * 10
            
            # Bottom Bread slice
            painter.setPen(QPen(QColor("#8d6e63"), 2))
            painter.setBrush(QBrush(QColor("#d7ccc8")))
            painter.drawRoundedRect(0, 5 + int(flap_y/2), 45, 14, 5, 5)
            # Cheese Filling
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#ffeb3b")))
            painter.drawRect(3, 2, 39, 6)
            # Top Bread slice (the 'wings')
            painter.setPen(QPen(QColor("#8d6e63"), 2))
            painter.setBrush(QBrush(QColor("#d7ccc8")))
            painter.drawRoundedRect(0, -10 - int(flap_y/2), 45, 14, 5, 5)
            painter.restore()

        # Draw Rotating Sun in Top Right
        sun_x, sun_y = self.width() - 150, 120
        painter.save()
        painter.translate(sun_x, sun_y)
        
        # Rotating Rays
        painter.setPen(QPen(QColor("#ffb300"), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.save()
        painter.rotate(self.sun_angle)
        for _ in range(12):
            painter.rotate(30)
            painter.drawLine(0, 65, 0, 95)
        painter.restore()
        
        # Sun Body
        painter.setPen(QPen(QColor("#ffa000"), 4))
        painter.setBrush(QBrush(QColor("#ffca28")))
        painter.drawEllipse(-55, -55, 110, 110)
        
        # Sun Face (Fixed orientation)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#3e2723")))
        painter.drawEllipse(-22, -18, 10, 10) # Eyes
        painter.drawEllipse(12, -18, 10, 10)
        painter.setPen(QPen(QColor("#3e2723"), 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawArc(-25, -10, 50, 45, 0, -180 * 16) # Smile
        painter.restore()

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def keyPressEvent(self, event):
        # Emergency exit with Escape key
        if event.key() == Qt.Key.Key_Escape:
            QApplication.quit()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()