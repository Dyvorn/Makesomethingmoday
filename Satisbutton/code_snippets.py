# This file contains the code snippets for the "Copy Code" feature.
SNIPPETS = {
    'neumorphic': """# Neumorphic Button Style
# Requires a light background color (e.g., #E0E5EC)
def draw_neumorphic(surf, rect, pressed):
    light = (255, 255, 255)
    shadow = (163, 177, 198)
    base = (224, 229, 236)
    
    if pressed:
        pygame.draw.rect(surf, base, rect, border_radius=12)
        pygame.draw.rect(surf, shadow, rect, 2, border_radius=12) # Inner shadow hint
    else:
        # Outer shadows
        pygame.draw.rect(surf, shadow, rect.move(4, 4), border_radius=12)
        pygame.draw.rect(surf, light, rect.move(-4, -4), border_radius=12)
        pygame.draw.rect(surf, base, rect, border_radius=12)
""",
    'glass': """# Glassmorphism Button Style
# Best on dark/colorful backgrounds
def draw_glass(surf, rect):
    # Semi-transparent body
    s = pygame.Surface(rect.size, pygame.SRCALPHA)
    s.fill((255, 255, 255, 30))
    surf.blit(s, rect.topleft)
    
    # Border
    pygame.draw.rect(surf, (255, 255, 255, 100), rect, 1, border_radius=12)
    
    # Shine
    pygame.draw.line(surf, (255, 255, 255, 80), 
                     (rect.left+10, rect.top+10), (rect.right-10, rect.bottom-20), 20)
""",
    'outline': """# Outline Button Style
def draw_outline(surf, rect, hover):
    col = (100, 200, 255) if hover else (150, 150, 150)
    pygame.draw.rect(surf, col, rect, 2, border_radius=8)
""",
    'retro': """# Retro Windows 95 Style Button
def draw_retro(surf, rect, pressed):
    base = (192, 192, 192)
    light = (255, 255, 255)
    dark = (128, 128, 128)
    
    pygame.draw.rect(surf, base, rect)
    if not pressed:
        pygame.draw.line(surf, light, rect.topleft, rect.topright, 2)
        pygame.draw.line(surf, light, rect.topleft, rect.bottomleft, 2)
        pygame.draw.line(surf, dark, rect.bottomleft, rect.bottomright, 2)
        pygame.draw.line(surf, dark, rect.topright, rect.bottomright, 2)
    else:
        pygame.draw.rect(surf, dark, rect, 2)
""",
    'cyber': """# Cyberpunk Button Style
def draw_cyber(surf, rect, hover):
    cut = 15
    pts = [
        (rect.left + cut, rect.top), (rect.right, rect.top),
        (rect.right, rect.bottom - cut), (rect.right - cut, rect.bottom),
        (rect.left, rect.bottom), (rect.left, rect.top + cut)
    ]
    col = (255, 230, 0) if not hover else (255, 255, 100)
    pygame.draw.polygon(surf, col, pts)
    pygame.draw.polygon(surf, (0,0,0), pts, 3)
""",
    'soft': """# Soft/Cute Button Style
def draw_soft(surf, rect, pressed):
    col = (255, 180, 190)
    shadow = (200, 130, 140)
    
    if not pressed:
        pygame.draw.rect(surf, shadow, rect.move(0, 6), border_radius=20)
    pygame.draw.rect(surf, col, rect.move(0, 3 if pressed else 0), border_radius=20)
""",
    'toggle': """# UI Toggle Switch
# This requires state management for the toggle.
def draw_toggle(surf, rect, toggled_on, knob_x_anim):
    # knob_x_anim should be a class member that is smoothly interpolated
    # towards the target position in an update loop.
    
    target_knob_x = rect.right - rect.height/2 if toggled_on else rect.left + rect.height/2
    knob_x_anim += (target_knob_x - knob_x_anim) * 0.2

    # Background
    bg_col = (110, 231, 183) if toggled_on else (60, 70, 90)
    pygame.draw.rect(surf, bg_col, rect, border_radius=int(rect.height/2))
    
    # Knob
    knob_r = int(rect.height/2) - 6
    pygame.draw.circle(surf, (255,255,255), (int(knob_x_anim), rect.centery), knob_r)
""",
    'morph': """# Morphing Button
# Changes shape on hover. Requires an animation value.
def draw_morph_button(surf, rect, color, morph_progress):
    # morph_progress is a value from 0.0 (default) to 1.0 (hovered)
    # that should be animated smoothly in an update loop.
    
    eased_morph = morph_progress**2
    m_w = rect.w + 60 * eased_morph
    m_h = rect.h
    m_radius = int((m_h/2) * (1 - eased_morph) + 20 * eased_morph)
    
    morph_rect = pygame.Rect(int(rect.centerx - m_w/2), int(rect.centery - m_h/2), int(m_w), int(m_h))
    pygame.draw.rect(surf, color, morph_rect, border_radius=m_radius)
""",
    'liquid': """# Liquid Glass Button
import math, time, pygame

def draw_liquid(surf, rect, color, time_offset=0):
    liquid_surf = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(liquid_surf, (*color[:3], 60), liquid_surf.get_rect(), border_radius=25)

    # Animated waves for highlights
    for i in range(3):
        amp = rect.height / (10 + i*4)
        freq = 2 + i
        speed = 1.5 + i * 0.5
        y_off = rect.height * 0.5 + (i - 1.5) * rect.height * 0.1
        points = []
        for x in range(rect.width + 1):
            y = y_off + math.sin(x/rect.width*freq*2*math.pi + time.time()*speed + time_offset) * amp
            points.append((x, y))
        if len(points) > 1:
            pygame.draw.aalines(liquid_surf, (255, 255, 255, 55), False, points)

    surf.blit(liquid_surf, rect.topleft)
    pygame.draw.rect(surf, (255, 255, 255, 120), rect, 2, border_radius=25)
""",
    'ghost': """# Ghost Button
# Fills on hover.
def draw_ghost(surf, rect, color, hover):
    if hover:
        pygame.draw.rect(surf, color, rect, border_radius=8)
    else:
        pygame.draw.rect(surf, color, rect, 2, border_radius=8)

# Text color needs to be handled separately.
# On hover, text is typically white/black.
# Off hover, text is the button's color.
""",
    'checkbox': """# Checkbox
# Requires a `toggled_on` state and `toggle_progress` (0.0-1.0) for animation.
def draw_checkbox(surf, rect, color, progress):
    # Box
    pygame.draw.rect(surf, (80, 90, 110), rect, 2, border_radius=4)
    
    # Fill on progress
    if progress > 0:
        fill_rect = rect.inflate(-8, -8)
        fill_rect.w *= progress
        fill_rect.h *= progress
        fill_rect.center = rect.center
        pygame.draw.rect(surf, color, fill_rect, border_radius=2)

    # Checkmark (draws in based on progress)
    if progress > 0.5:
        p1 = (rect.left + 4, rect.centery)
        p2 = (rect.centerx - 2, rect.bottom - 4)
        p3 = (rect.right - 4, rect.top + 4)
        
        # Interpolate points
        t = (progress - 0.5) * 2
        if t < 0.5:
            p_mid = (p1[0] + (p2[0]-p1[0]) * t*2, p1[1] + (p2[1]-p1[1]) * t*2)
            pygame.draw.line(surf, (255,255,255), p1, p_mid, 2)
        else:
            p_mid = (p2[0] + (p3[0]-p2[0]) * (t-0.5)*2, p2[1] + (p3[1]-p2[1]) * (t-0.5)*2)
            pygame.draw.line(surf, (255,255,255), p1, p2, 2)
            pygame.draw.line(surf, (255,255,255), p2, p_mid, 2)
""",
    'radio': """# Radio Button
# Requires `toggled_on` state and `toggle_progress` (0.0-1.0) for animation.
# Note: Group logic (deselecting others) is not included here.
def draw_radio(surf, rect, color, progress):
    cx, cy = rect.centerx, rect.centery
    radius = rect.width // 2
    
    # Outer ring
    pygame.draw.circle(surf, (80, 90, 110), (cx,cy), radius, 2)
    
    # Inner dot
    if progress > 0:
        inner_radius = (radius - 4) * progress
        pygame.draw.circle(surf, color, (cx,cy), int(inner_radius))
""",
    'like': """# Like / Heart Button
# Requires a `toggled_on` state.
def draw_like_button(surf, rect, color, toggled_on):
    # A simple heart shape polygon
    r = rect.width / 2
    cx, cy = rect.centerx, rect.centery - 2 # Shift up slightly
    points = [
        (cx, cy + r*0.8), (cx - r, cy - r*0.2), (cx - r*0.6, cy - r*0.8),
        (cx, cy - r*0.4), (cx + r*0.6, cy - r*0.8), (cx + r, cy - r*0.2)
    ]
    if toggled_on:
        pygame.draw.polygon(surf, color, points)
    else:
        pygame.draw.polygon(surf, (80, 90, 110), points, 2)
""",
    'gradient': """# Gradient Button
def draw_gradient(surf, rect, color1, color2):
    # Linearly interpolates from color1 at the top to color2 at the bottom.
    
    grad_surf = pygame.Surface(rect.size)
    for i in range(rect.height):
        progress = i / rect.height
        # Linear interpolation for each color channel
        r = color1[0] * (1 - progress) + color2[0] * progress
        g = color1[1] * (1 - progress) + color2[1] * progress
        b = color1[2] * (1 - progress) + color2[2] * progress
        pygame.draw.line(grad_surf, (r, g, b), (0, i), (rect.width, i))
    
    surf.blit(grad_surf, rect.topleft)
    pygame.draw.rect(surf, (255,255,255,40), rect, 1, border_radius=10)
""",
    'link': """# Link-style Button with Underline
# This button has no body, only text and an animated underline.
def draw_link(surf, text_rect, color, underline_progress):
    # text_rect is the pygame.Rect of the rendered text.
    # underline_progress is a float from 0.0 to 1.0 for animation.
    
    if underline_progress > 0.01:
        line_width = text_rect.width * underline_progress
        line_y = text_rect.bottom + 2
        line_start = (text_rect.centerx - line_width / 2, line_y)
        line_end = (text_rect.centerx + line_width / 2, line_y)
        pygame.draw.line(surf, color, line_start, line_end, 2)
""",
    'load_spinner': """# Simple Loading Spinner
def draw_spinner(surf, center, color):
    angle = time.time() * 300
    radius = 20
    rect = pygame.Rect(center[0]-radius, center[1]-radius, radius*2, radius*2)
    pygame.draw.arc(surf, color, rect, math.radians(angle), math.radians(angle + 240), 4)
""",
    'load_bar': """# Smooth Loading Bar
def draw_loading_bar(surf, x, y, w, h, color):
    # Track
    pygame.draw.rect(surf, (50, 60, 70), (x, y, w, h), border_radius=h//2)
    
    # Oscillating Fill
    progress = (math.sin(time.time() * 2) + 1) / 2
    fill_w = w * progress
    pygame.draw.rect(surf, color, (x, y, fill_w, h), border_radius=h//2)
""",
    'load_dots': """# Bouncing Dots Loader
def draw_dots(surf, center, colors):
    for i in range(3):
        offset = math.sin(time.time() * 8 + i * 0.5) * 6
        dx = center[0] + (i - 1) * 20
        dy = center[1] + offset
        pygame.draw.circle(surf, colors[i], (int(dx), int(dy)), 6)
""",
    'load_pulse': """# Pulsing Ring Loader
def draw_pulse(surf, center, color):
    # Center dot
    pygame.draw.circle(surf, color, center, 5)
    
    # Expanding rings
    for i in range(2):
        t = (time.time() * 1.0 + i * 1.0) % 2.0
        alpha = max(0, 255 * (1 - t/2.0))
        radius = 5 + t * 20
        
        s = pygame.Surface((int(radius*2), int(radius*2)), pygame.SRCALPHA)
        pygame.draw.circle(s, (*color[:3], int(alpha)), (int(radius), int(radius)), int(radius), 2)
        surf.blit(s, (center[0] - radius, center[1] - radius))
""",
    'primary': """# Standard Primary Button
def draw_primary(surf, rect, color, hover):
    # Simple rounded rect with hover effect
    pygame.draw.rect(surf, color, rect, border_radius=8)
    if hover:
        pygame.draw.rect(surf, (255,255,255,30), rect, border_radius=8)
""",
    'download': """# Download Button with State
# Requires state: 'idle', 'downloading', 'done' and progress (0.0-1.0)
def draw_download(surf, rect, state, progress):
    if state == 'idle':
        pygame.draw.rect(surf, (110, 231, 183), rect, border_radius=12)
        # Draw text "DOWNLOAD" here
    elif state == 'downloading':
        pygame.draw.rect(surf, (40, 50, 60), rect, border_radius=12)
        fill_w = rect.width * progress
        pygame.draw.rect(surf, (110, 231, 183), (rect.x, rect.y, fill_w, rect.height), border_radius=12)
    elif state == 'done':
        pygame.draw.rect(surf, (16, 185, 129), rect, border_radius=12)
        # Draw text "DONE" here
""",
    'hold': """# Hold-to-Confirm Button
# Requires tracking how long the mouse has been held down
def draw_hold(surf, rect, hold_progress):
    # Background
    pygame.draw.rect(surf, (40, 50, 60), rect, border_radius=30)
    
    # Fill based on hold time
    if hold_progress > 0:
        fill_w = rect.width * hold_progress
        pygame.draw.rect(surf, (110, 231, 183), (rect.x, rect.y, fill_w, rect.height), border_radius=30)
        
    pygame.draw.rect(surf, (255,255,255,50), rect, 2, border_radius=30)
""",
    'fab': """# Floating Action Button (FAB)
def draw_fab(surf, cx, cy, radius, color, hover):
    # Shadow
    shadow_off = 4 if hover else 2
    pygame.draw.circle(surf, (0,0,0,60), (cx, cy + shadow_off), radius + (2 if hover else 0))
    
    # Body
    pygame.draw.circle(surf, color, (cx, cy), radius)
    
    # Icon (Plus)
    w = int(radius * 0.8)
    pygame.draw.rect(surf, (255,255,255), (cx - w/2, cy - 1, w, 2))
    pygame.draw.rect(surf, (255,255,255), (cx - 1, cy - w/2, 2, w))
""",
    'menu': """# Animated Menu Icon (Hamburger to X)
# Requires a progress value (0.0 to 1.0)
def draw_menu_icon(surf, cx, cy, size, progress):
    # Interpolate lines based on progress
    # Top line rotates 45deg, Bottom -45deg, Middle fades
    
    angle = progress * 45
    # ... rotation math ...
    
    # Draw lines
    # ...
""",
    'status': """# Status Button
def draw_status(surf, rect, text, status_color):
    pygame.draw.rect(surf, (40, 50, 60), rect, border_radius=8)
    
    # Draw Text
    # ...
    
    # Draw Status Dot
    dot_pos = (rect.right - 20, rect.centery)
    pygame.draw.circle(surf, status_color, dot_pos, 5)
""",
    'music': """# Music Visualizer Widget
# Captures system audio using 'sounddevice' and 'numpy'.
# Install with: pip install sounddevice numpy
# Note: Requires a 'loopback' or 'Stereo Mix' audio device to be enabled.

import sounddevice as sd
import numpy as np

def audio_callback(indata, frames, time, status):
    # This function is called by the audio stream in a separate thread.
    
    # 1. Apply a window function to the audio data (indata)
    windowed_data = indata[:, 0] * np.hanning(len(indata))
    
    # 2. Perform a Fast Fourier Transform (FFT)
    fft_result = np.fft.rfft(windowed_data)
    magnitudes = np.abs(fft_result)
    
    # 3. Process magnitudes into visualizer bar heights
    # (grouping into frequency bands, logarithmic scaling, etc.)
    # ... store results in a shared array for the UI thread to read.
""",
    'shatter': """# Shatter Effect
# On click, the button shatters into particles.
# This is handled by an effect function that
# creates many triangular particles from the button's area
# and temporarily hides the button via a cooldown.

def effect_shatter(app, button):
    button.shatter_cooldown = 120 # Frames to hide
    
    # Create particles
    for _ in range(80):
        # Create a triangular particle inside button bounds
        # Give it an outward velocity and gravity
        # ...
        app.particles.append(new_particle)
""",
    'paint': """# Paint Mode
# This toggles a global 'paint_mode' in the app.
# When active, clicking and dragging on the background
# creates colorful, fading trails.

class App:
    def __init__(self):
        # ...
        self.paint_mode = False
        self.paint_trails = []
        self.current_paint_trail = None

    def toggle_paint_mode(self):
        self.paint_mode = not self.paint_mode

    def handle_events(self):
        # ... in event loop ...
        if ev.type == pygame.MOUSEBUTTONDOWN and not on_a_button:
            if self.paint_mode:
                self.current_paint_trail = {'points': [], 'color': random_color()}
                self.paint_trails.append(self.current_paint_trail)
        elif ev.type == pygame.MOUSEBUTTONUP:
            self.current_paint_trail = None
        elif ev.type == pygame.MOUSEMOTION and self.current_paint_trail is not None:
            self.current_paint_trail['points'].append({'pos': ev.pos, 'life': 150})
    
    def update(self):
        # In update, iterate through trails and points, decrementing 'life'.
    def draw(self):
        # In draw, iterate through trails and draw circles for each point,
        # using 'life' to control size and alpha for a fading effect.
""",
    'bubble': """import pygame
import random
import math

# --- Basic Particle Class (Required) ---
class Particle:
    def __init__(self, x, y, vx, vy, life, size, color, gravity=0.1):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life, self.max_life, self.size, self.color, self.gravity = life, life, size, color, gravity
    def update(self):
        self.vy += self.gravity; self.x += self.vx; self.y += self.vy
        self.vx *= 0.98; self.vy *= 0.98; self.life -= 1
    def draw(self, surf):
        if self.life > 0:
            r = int(self.size * (self.life / self.max_life))
            pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), r)

# --- Bubble Effect Function ---
def effect_bubble(app, pos):
    for _ in range(18):
        vx = (random.random() * 2 - 1) * 2
        vy = -random.random() * 3 - 1
        p = Particle(pos[0] + random.uniform(-40, 40), pos[1] + random.uniform(-20, 20),
                     vx, vy, 60, random.uniform(6, 12), (200, 250, 245), gravity=-0.05)
        app.particles.append(p)

# --- Example App Usage ---
class App:
    def __init__(self):
        self.particles = []
    def on_button_click(self, button_pos):
        effect_bubble(self, button_pos)
""",
    'pixel': """import pygame
import random

# --- Basic Particle Class (Required) ---
class Particle:
    def __init__(self, x, y, vx, vy, life, size, color, gravity=0.1):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life, self.max_life, self.size, self.color, self.gravity = life, life, size, color, gravity
    def update(self):
        self.vy += self.gravity; self.x += self.vx; self.y += self.vy
        self.vx *= 0.98; self.vy *= 0.98; self.life -= 1
    def draw(self, surf):
        if self.life > 0:
            r = int(self.size * (self.life / self.max_life))
            pygame.draw.rect(surf, self.color, (int(self.x - r/2), int(self.y - r/2), r, r))

# --- Pixel Effect Function ---
def effect_pixel(app, pos):
    for _ in range(28):
        color = (random.randint(80, 255), random.randint(60, 200), random.randint(30, 160))
        p = Particle(pos[0] + random.uniform(-40, 40), pos[1] + random.uniform(-20, 20),
                     random.uniform(-8, 8), random.uniform(-8, 8),
                     random.randint(18, 40), random.randint(2, 6), color, gravity=0.2)
        app.particles.append(p)

# --- Example App Usage ---
class App:
    def __init__(self):
        self.particles = []
    def on_button_click(self, button_pos):
        effect_pixel(self, button_pos)
""",
    'search_bar': """# Search Bar with Focus State
def draw_search_bar(surf, rect, text, active):
    # Background
    col = (30, 35, 45)
    pygame.draw.rect(surf, col, rect, border_radius=8)
    
    # Border (highlight if active)
    border_col = (110, 231, 183) if active else (60, 70, 80)
    pygame.draw.rect(surf, border_col, rect, 2, border_radius=8)
    
    # Text
    if text:
        txt_surf = font.render(text, True, (200, 210, 220))
    else:
        txt_surf = font.render("Search...", True, (100, 110, 120))
    
    surf.blit(txt_surf, (rect.x + 20, rect.centery - txt_surf.get_height()//2))
""",
    'default': """# Click a button to see its code.
# The code provided will be a self-contained
# example that you can adapt for your project.

# Note: You'll need Pygame installed.
# pip install pygame"""
}