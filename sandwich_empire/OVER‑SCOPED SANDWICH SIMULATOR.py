import sys
import os
import random
import math
import json
from pathlib import Path
from PyQt6.QtCore import Qt, QRect, QPropertyAnimation, QEasingCurve, pyqtProperty, QPoint, QTimer, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QLinearGradient, QRadialGradient
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QStackedWidget, QLineEdit, QSlider, QTextEdit
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
    "Bread": "#d7ccc8",
    "Fresh Tomato": "#ef5350",
    "Premium Ham": "#8d6e63",
    "Cosmic Cheese": "#fff176",
    "Martian Pepper": "#ff5722",
    "Storm Pickles": "#4caf50",
    "Void Matter": "#212121",
    "Plate": "#cfd8dc"
}

LOCATIONS = {
    1: {
        "name": "Your Front Garden", "days": 7, "rank": "Beginner Chef", "req": 500, 
        "fail": "You couldn’t ketchup to demand.",
        "intro": "You begin your empire in your garden, where you craft simple tomato sandwiches for neighbors and random dogs.",
        "success_msg": "The government arrives to shut you down, but you sell your house just in time to buy a shop!",
        "profit_mult": 1,
        "sky": ["#81d4fa", "#29b6f6"],
    },
    2: {
        "name": "Small Sandwich Shop", "days": 12, "rank": "Amateur Entrepreneur", "req": 5000, 
        "fail": "You’ve been ham-handled by justice.",
        "intro": "The government arrived and seized your garden! You relocate to a small shop. Premium ham is now on the menu.",
        "success_msg": "The Global Sandwich Ban hits! You build a rocket out of stale bread and launch into the unknown.",
        "profit_mult": 10,
        "sky": ["#4fc3f7", "#0288d1"]
    },
    3: {
        "name": "The Moon Base", "days": 15, "rank": "Space Chef", "req": 100000, 
        "fail": "Moon Melt: The sandwich was too strong.",
        "intro": "The Global Sandwich Ban forced you into space. You've landed on the Moon. Cosmic Cheese awaits!",
        "success_msg": "The Lunar Authority demands a shutdown. You ignite your engines and head for the red planet.",
        "profit_mult": 100,
        "sky": ["#212121", "#000000"]
    },
    4: {
        "name": "Mars Diner", "days": 20, "rank": "Interplanetary Tycoon", "req": 10000000, 
        "fail": "Absorbed into the Martian cult of flavor.",
        "intro": "Gravity distortion laws forced you off the Moon. Welcome to Mars! Beware the heat of Martian Peppers.",
        "success_msg": "A flavor riot breaks out! You narrowly escape the Martian Senate's wrath, boosting toward Jupiter.",
        "profit_mult": 5000,
        "sky": ["#bf360c", "#3e2723"]
    },
    5: {
        "name": "Jupiter Floating Bar", "days": 25, "rank": "Gas Giant Gourmet", "req": 1000000000, 
        "fail": "You became static in the sandwich industry.",
        "intro": "Fleeing the flavor riots on Mars, you've reached Jupiter. Storm Pickles provide an electric kick.",
        "success_msg": "The gravitational pressure is crushing the bar! You warp out just as the shop implodes.",
        "profit_mult": 200000,
        "sky": ["#4a148c", "#1a237e"]
    },
    6: {
        "name": "Ton-216 (Black Hole)", "days": 999, "rank": "Galactic Master Chef", "req": 6000000000000000000, 
        "fail": "Lost to flavor singularity.",
        "intro": "The bar is imploding! You've jumped to the edge of Ton-216. Use Void Matter to reach 6 Quintillion.",
        "success_msg": "You've done it. You have the money. But the black hole beckons...",
        "profit_mult": 100000000,
        "sky": ["#000000", "#000000"]
    }
}

INGREDIENTS = {
    "Bread": {"cost": 5, "value": 10, "loc": 1},
    "Fresh Tomato": {"cost": 10, "value": 25, "loc": 1},
    "Premium Ham": {"cost": 50, "value": 120, "loc": 2},
    "Cosmic Cheese": {"cost": 500, "value": 1500, "loc": 3},
    "Martian Pepper": {"cost": 5000, "value": 20000, "loc": 4},
    "Storm Pickles": {"cost": 100000, "value": 500000, "loc": 5},
    "Void Matter": {"cost": 100000000, "value": 1000000000, "loc": 6}
}

def format_currency(amount):
    """Handles formatting for normal money up to 6 Quintillion."""
    if amount >= 1e18:
        return f"${amount/1e18:.2f}Q"
    elif amount >= 1e15:
        return f"${amount/1e15:.2f}q"
    elif amount >= 1e12:
        return f"${amount/1e12:.2f}T"
    elif amount >= 1e9:
        return f"${amount/1e9:.2f}B"
    elif amount >= 1e6:
        return f"${amount/1e6:.2f}M"
    elif amount >= 1e3:
        return f"${amount/1e3:.1f}k"
    return f"${int(amount)}"


class SandwichRenderer(QWidget): # Text-based+ Visuals
    def __init__(self):
        super().__init__()
        self.ingredients = []
        self.offsets = {} # For animation offsets
        self.wobble = 0
        self.time_val = 0
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.update_animations)
        self.anim_timer.start(16)

    def add_ingredient(self, name):
        self.ingredients.append(name)
        self.offsets[len(self.ingredients) - 1] = 100.0
        self.update()

    def clear(self):
        self.ingredients = []
        self.offsets = {}
        self.update()

    def update_animations(self):
        any_moving = False
        self.wobble = (self.wobble + 0.1) % 6.28
        self.time_val += 0.05
        
        # Physics context: Check if we are on the Moon (loc 3)
        is_moon = False
        if hasattr(self.parent(), 'session'):
            is_moon = self.parent().session.get('location_id', 1) == 3

        for idx in list(self.offsets.keys()):
            if self.offsets[idx] > 0.5:
                # Moon physics: Slower, floatier drop
                decay = 0.96 if is_moon else 0.8
                self.offsets[idx] *= decay
                any_moving = True
            else:
                # Idle "Float" effect for Moon sandwiches
                if is_moon:
                    self.offsets[idx] = math.sin(self.wobble + idx) * 3
                    any_moving = True
                else:
                    self.offsets[idx] = 0

        if any_moving:
            self.update()

    def mousePressEvent(self, event):
        # Mars Mechanic: Faster clicking to cool down
        game_screen = self.window().findChild(GameScreen)
        if game_screen and game_screen.session.get('location_id') == 4:
            game_screen.cool_down()
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Jupiter Mechanic: Gravitational distortion
        is_jupiter = False
        is_void = False
        if hasattr(self.parent(), 'session'):
            is_jupiter = self.parent().session.get('location_id') == 5
            is_void = self.parent().session.get('location_id') == 6
        
        cx, bottom_y = self.width() // 2, self.height() - 50
        
        # Draw Plate
        painter.setBrush(QColor(GAME_COLORS["Plate"]))
        painter.setPen(QPen(QColor("#90a4ae"), 3))
        painter.drawEllipse(cx - 150, bottom_y - 20, 300, 60)

        # Draw Layers
        layer_height = 25
        for i, ing in enumerate(self.ingredients):
            color = GAME_COLORS.get(ing, "#ffffff")
            offset = self.offsets.get(i, 0)
            
            rect = QRect(cx - 100, bottom_y - (i + 1) * layer_height - int(offset), 200, layer_height)
            
            painter.setBrush(QColor(color))
            painter.setPen(QPen(QColor(0, 0, 0, 50), 2))
            painter.drawRoundedRect(rect, 10, 10)
            
            # Jupiter Mechanic: Storm Pickle Crackle
            if is_jupiter and ing == "Storm Pickles":
                painter.setPen(QPen(QColor("#ffffff"), 2))
                for _ in range(3):
                    x1 = random.randint(rect.left(), rect.right())
                    y1 = random.randint(rect.top(), rect.bottom())
                    x2 = x1 + random.randint(-10, 10)
                    y2 = y1 + random.randint(-10, 10)
                    painter.drawLine(x1, y1, x2, y2)
            
            # Black Hole Mechanic: Void Matter pulsing
            if is_void and ing == "Void Matter":
                glow = abs(math.sin(self.time_val * 2)) * 15
                grad = QRadialGradient(rect.center().x(), rect.center().y(), 120 + glow)
                grad.setColorAt(0, QColor(103, 58, 183, 100))
                grad.setColorAt(1, QColor(0, 0, 0, 0))
                painter.fillRect(rect.adjusted(-20, -20, 20, 20), grad)


class StoryOverlay(QWidget):
    def __init__(self, title, text, callback):
        super().__init__()
        self.callback = callback
        self.setFixedSize(600, 400)
        self.setStyleSheet("background: rgba(13, 13, 22, 230); border: 4px solid #ffca28; border-radius: 20px;")
        
        layout = QVBoxLayout()
        t_label = QLabel(title)
        t_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #ffca28; border: none;")
        t_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        m_label = QLabel(text)
        m_label.setStyleSheet("font-size: 18px; color: white; border: none;")
        m_label.setWordWrap(True)
        m_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        btn = JuicyButton("CONTINUE")
        btn.setFixedWidth(200)
        btn.clicked.connect(self.close_and_continue)
        
        layout.addWidget(t_label)
        layout.addSpacing(20)
        layout.addWidget(m_label)
        layout.addSpacing(40)
        layout.addWidget(btn, 0, Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)

    def close_and_continue(self):
        self.setParent(None)
        if self.callback: self.callback()


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
                "name": shop_name, 
                "day": 1, 
                "money": 100, 
                "rank": "Beginner Chef", 
                "difficulty": self.selected_diff,
                "location_id": 1,
                "unlocked": ["Bread", "Fresh Tomato"]
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
        self.session = {}
        self.current_order = []
        self.current_sandwich = []
        self.init_ui()
        
        # Mars/Jupiter Mechanics
        self.spiciness = 0
        self.decay_timer = QTimer(self)
        self.decay_timer.timeout.connect(self.mechanic_update)

    def update_game_data(self, data):
        """Initializes a new gameplay session with save data."""
        self.session = data 
        self.current_location = LOCATIONS.get(data.get('location_id', 1))
        self.game_label.setText(f"{data['name'].upper()} - {self.current_location['name']}")
        self.refresh_stats()
        self.setup_ingredients()
        self.log_message(f"--- Welcome to {self.current_location['name']} ---")
        self.show_story_popup("LOCATION REACHED", self.current_location['intro'])
        self.generate_order()
        self.decay_timer.start(100) # Start background mechanics loop
        
        # Tutorial for Day 1
        if data['day'] == 1 and data['location_id'] == 1:
            self.show_story_popup("HOW TO PLAY", 
                "1. Pick ingredients on the right.\n"
                "2. Match the CUSTOMER ORDER in the log for a 3x bonus!\n"
                "3. Click SERVE to cash in.\n"
                "4. Hit END DAY to progress. Don't go broke!")

    def mechanic_update(self):
        # Spiciness Decay
        if self.spiciness > 0:
            self.spiciness = max(0, self.spiciness - 0.5)
            self.refresh_stats()
            
            # Trigger screen shake if too spicy
            if self.spiciness > 50:
                self.window().shake_intensity = int((self.spiciness - 50) / 10)
            else:
                self.window().shake_intensity = 0

    def cool_down(self):
        self.spiciness = max(0, self.spiciness - 5)
        self.log_message("<span style='color: #03a9f4;'>Clicked to cool down!</span>")

    def refresh_stats(self):
        money_str = format_currency(self.session['money'])
        spice_str = f" | 🔥 HEAT: {int(self.spiciness)}%" if self.session.get('location_id') == 4 else ""
        self.stats_label.setText(f"Day: {self.session['day']} | Cash: {money_str} | Rank: {self.session['rank']}{spice_str}")


    def show_story_popup(self, title, message, callback=None):
        self.overlay = StoryOverlay(title, message, callback)
        self.overlay.setParent(self)
        # Center the overlay
        geom = self.geometry()
        self.overlay.move((geom.width() - 600) // 2, (geom.height() - 400) // 2)
        self.overlay.show()

    def log_message(self, text):
        self.story_log.append(f"<p style='margin-bottom: 8px;'>{text}</p>")
        self.story_log.verticalScrollBar().setValue(self.story_log.verticalScrollBar().maximum())

    def generate_order(self):
        unlocked = self.session.get('unlocked', ["Bread"])
        loc_id = self.session.get('location_id', 1)
        
        # Pick 2-4 random items from unlocked ingredients
        num = random.randint(2, 4)
        if loc_id == 6:
            num = random.randint(6, 10) # BOSS TIER ORDERS
            
        self.current_order = [random.choice(unlocked) for _ in range(num)]
        
        # Text-based+ UI: Ensure bread is always hinted or included
        if "Bread" in unlocked and "Bread" not in self.current_order:
            self.current_order[0] = "Bread"
            
        order_text = ", ".join(self.current_order)
        self.log_message(f"<span style='color: #ffca28;'><b>ORDER:</b> Wants {order_text}</span>")

    def setup_ingredients(self):
        # Clear existing buttons
        for i in reversed(range(self.ingredients_panel.count())): 
            self.ingredients_panel.itemAt(i).widget().setParent(None)
            
        for ing in self.session.get('unlocked', []):
            btn = JuicyButton(ing)
            btn.setFixedHeight(50)
            btn.clicked.connect(lambda _, x=ing: self.add_ingredient(x))
            self.ingredients_panel.addWidget(btn)

    def add_ingredient(self, name):
        cost = INGREDIENTS[name]['cost']
        if self.session['money'] >= cost:
            self.session['money'] -= cost
            self.current_sandwich.append(name)
            self.sandwich_visual.add_ingredient(name)
            self.log_message(f"Added <b>{name}</b> (-${cost})")
            self.refresh_stats()
            if name == "Martian Pepper":
                self.spiciness += 20
        else:
            self.log_message(f"<span style='color: red;'>Too broke for {name}!</span>")

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
        self.log_container = QVBoxLayout()
        log_header = QLabel("NARRATIVE LOG")
        log_header.setStyleSheet("font-weight: bold; color: white;")
        self.story_log = QTextEdit()
        self.story_log.setReadOnly(True)
        self.story_log.setFixedWidth(300)
        self.story_log.setStyleSheet("background: rgba(0,0,0,120); color: #e0e0e0; border-radius: 10px; font-family: 'Consolas'; font-size: 14px;")
        
        self.log_container.addWidget(log_header)
        self.log_container.addWidget(self.story_log)
        
        # Middle: Prep Table
        self.prep_table = QVBoxLayout()
        self.sandwich_visual = SandwichRenderer()
        self.prep_table.addWidget(self.sandwich_visual)
        
        # Right: Inventory/Ingredients
        self.ingredients_panel = QVBoxLayout()
        self.ingredients_panel.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Bottom Action Bar
        actions = QHBoxLayout()
        serve_btn = JuicyButton("SERVE SANDWICH")
        serve_btn.clicked.connect(self.serve_sandwich)
        
        next_day_btn = JuicyButton("END DAY")
        next_day_btn.clicked.connect(self.next_day)
        
        actions.addWidget(serve_btn)
        actions.addWidget(next_day_btn)
        
        gameplay_layout.addLayout(self.log_container)
        gameplay_layout.addLayout(self.prep_table, 1)
        gameplay_layout.addLayout(self.ingredients_panel)
        
        layout.addLayout(gameplay_layout, 1)
        layout.addLayout(actions)

        self.setLayout(layout)

    def serve_sandwich(self):
        if not self.current_sandwich: return
        
        # Order Matching Logic
        matched = sorted(self.current_sandwich) == sorted(self.current_order)
        multiplier = 3.0 if matched else 1.1
        
        # Spiciness Bonus
        spice_bonus = 1.0 + (self.spiciness / 100.0)

        # Apply Location Inflation
        loc_mult = self.current_location.get('profit_mult', 1)
        
        total_value = sum(INGREDIENTS[i]['value'] for i in self.current_sandwich) * multiplier * loc_mult * spice_bonus
        self.session['money'] += total_value
        
        if matched:
            self.log_message(f"<span style='color: #4caf50;'>Perfect Match! Earned {format_currency(total_value)}</span>")
        else:
            self.log_message(f"Served for {format_currency(total_value)} (Order mismatch).")
            
        self.current_sandwich = []
        self.sandwich_visual.clear()
        self.spiciness = 0
        self.refresh_stats()
        self.generate_order()

    def trigger_victory(self):
        self.show_story_popup("BREAKING NEWS", 
            "Chockster Gumes goes bankrupt. ATG 6 canceled indefinitely. Your fortune is worthless in a world without the game.",
            lambda: self.show_story_popup("THE END", "You stare into Ton-216’s darkness, feeling yourself unravel. You jump into the black hole.\n\n'The Universe Tasted Well.'", 
            lambda: self.switch_callback(Screen.MAIN_MENU)))

    def next_day(self):
        self.session['day'] += 1
        self.log_message(f"<b>Day {self.session['day']} begins.</b>")
        loc_id = self.session.get('location_id', 1)
        loc_data = LOCATIONS[loc_id]
        
        # Check for location transition or failure
        if self.session['day'] > loc_data['days']:
            if self.session['money'] >= loc_data['req']:
                success_text = loc_data.get('success_story', loc_data['success_msg'])
                def transition():
                    self.session['location_id'] += 1
                    new_loc = LOCATIONS[self.session['location_id']]
                    self.session['rank'] = new_loc['rank']
                    for name, info in INGREDIENTS.items():
                        if info['loc'] == self.session['location_id']:
                            self.session['unlocked'].append(name)
                    self.update_game_data(self.session)
                
                self.show_story_popup("SUCCESS", success_text, transition)
            else:
                self.show_story_popup("GAME OVER", loc_data['fail'], lambda: self.switch_callback(Screen.MAIN_MENU))

        self.refresh_stats()


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
        self.time_counter = 0
        self.shake_intensity = 0
        for _ in range(4):
            self.sandwich_birds.append({'pos': QPoint(random.randint(0, 1920), random.randint(50, 400)), 
                                       'speed': random.randint(4, 7), 'flap': random.random() * 6.28})
        
        self.bg_timer = QTimer(self)
        self.bg_timer.timeout.connect(self.update_bg)
        self.bg_timer.start(30)

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

        # Borderless Fullscreen - Moved to end to ensure all widgets are initialized first
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.showFullScreen()

    def update_bg(self): # Background update logic (moved from MainMenu)
        # Drift the clouds
        for cloud in self.bg_clouds:
            self.time_counter += 0.01
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
        # Safety check: Default to location 1 if game session isn't loaded yet
        loc_id = 1
        if hasattr(self, 'game_screen') and self.game_screen.session:
            loc_id = self.game_screen.session.get('location_id', 1)
            
        loc_data = LOCATIONS.get(loc_id, LOCATIONS[1])
        sky_colors = loc_data.get('sky', [COLORS["sky_top"], COLORS["sky_bottom"]])

        # Screen Shake offset
        sx, sy = 0, 0
        if self.shake_intensity > 0 or loc_id == 5:
            base_shake = self.shake_intensity + (2 if loc_id == 5 else 0)
            sx = random.randint(-base_shake, base_shake)
            sy = random.randint(-base_shake, base_shake)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        


        
        # Black Hole Distortion logic
        if loc_id == 6:
            warp_x = math.sin(self.time_counter * 2) * 8
            warp_y = math.cos(self.time_counter * 1.5) * 8
            painter.translate(warp_x, warp_y)
            painter.scale(1.0 + math.sin(self.time_counter) * 0.01, 1.0 + math.cos(self.time_counter) * 0.01)

        # Draw Sky Gradient
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, QColor(sky_colors[0]))
        gradient.setColorAt(1.0, QColor(sky_colors[1]))
        painter.translate(sx, sy)
        painter.fillRect(self.rect().adjusted(-10, -10, 10, 10), gradient)

        # Draw drifting background clouds
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 60))
        for cloud in self.bg_clouds:
            painter.drawEllipse(cloud['pos'].x(), cloud['pos'].y(), cloud['size'], cloud['size'] // 2)

        # Hide sun on Moon/Void
        if loc_id in [3, 6]:
            return

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