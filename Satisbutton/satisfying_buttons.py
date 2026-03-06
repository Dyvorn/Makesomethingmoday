import math
import random
import sys
import struct
import time
import threading
import warnings

warnings.filterwarnings("ignore", category=UserWarning, message=".*pkg_resources.*")

try:
    import pygame
    from pygame import gfxdraw
    try:
        import pyperclip
        PYPERCLIP_AVAILABLE = True
    except ImportError:
        PYPERCLIP_AVAILABLE = False
        print("Warning: pyperclip not found. 'Copy Code' will not work. Install with: pip install pyperclip")
    try:
        import numpy as np
        NUMPY_AVAILABLE = True
    except ImportError:
        NUMPY_AVAILABLE = False
    try:
        import sounddevice as sd
        SOUNDDEVICE_AVAILABLE = True
    except ImportError:
        SOUNDDEVICE_AVAILABLE = False
except Exception as e:
    print("Missing dependency: pygame is required. Install with: pip install pygame")
    raise

from code_snippets import SNIPPETS

# --- Config ---
FPS = 60
BG = (10, 16, 28)
TEXT = (230, 240, 255)
ACCENT = (110, 231, 183)
SECOND = (96, 165, 250)
TERTIARY = (236, 72, 153)
NEUMORPHIC_BASE = (224, 229, 236)
DARK_PANEL = (20, 25, 35) 
RANDOM_COLORS = [ACCENT, SECOND, TERTIARY, (245,158,11), (16,185,129)]

# --- Sound helper (generate simple tone) ---
SAMPLE_RATE = 44100
DEFAULT_VOL = 0.12

def get_text_color_for_bg(bg_color):
    """Chooses black or white text based on background luminance."""
    if not bg_color: return (240, 240, 255)
    r, g, b = bg_color[:3]
    # Formula for luminance
    luminance = (0.299 * r + 0.587 * g + 0.114 * b)
    return (30, 30, 35) if luminance > 140 else (240, 240, 255)

def make_tone(freq=440.0, duration=0.18, volume=0.12):
    if pygame.mixer.get_init() is None:
        return None
    n_samples = int(SAMPLE_RATE * duration)
    buf = bytearray()
    amp = int(32767 * volume)
    for i in range(n_samples):
        t = i / SAMPLE_RATE
        # simple decaying sine
        v = math.sin(2.0 * math.pi * freq * t) * (1 - t / duration)
        s = int(v * amp)
        buf += struct.pack('<h', s)
    return pygame.mixer.Sound(buffer=bytes(buf))


class Particle:
    def __init__(self, x, y, vx, vy, life, size, color, kind='circle', gravity=0.18):
        self.x = x; self.y = y
        self.vx = vx; self.vy = vy
        self.life = life; self.max_life = life
        self.size = size; self.color = color
        self.kind = kind
        self.gravity = gravity
        self.stick_timer = 0
        self.angle = random.random() * 360

    def update(self, app):
        # Special logic for sticky liquid
        if self.kind == 'sticky_liquid' and app:
            mouse_pos = app.mouse_pos
            if self.stick_timer > 0:
                self.x, self.y = mouse_pos
                self.stick_timer -= 1
                self.life -= 0.5 # Die slower while stuck
                if self.stick_timer <= 0: # Fell off
                    self.gravity = 0.4 # Start falling
                return # Skip normal physics
            else:
                dist_to_mouse = math.hypot(self.x - mouse_pos[0], self.y - mouse_pos[1])
                if dist_to_mouse < 20:
                    self.stick_timer = random.randint(40, 80) # Stick for a bit
                    self.vx, self.vy = 0, 0
                else: # Move towards mouse
                    self.vx += (mouse_pos[0] - self.x) * 0.01
                    self.vy += (mouse_pos[1] - self.y) * 0.01

        self.vy += self.gravity
        self.x += self.vx; self.y += self.vy
        self.vx *= 0.96 # Air resistance
        self.vy *= 0.96
        self.life -= 1
        self.angle += self.vx * 2

    def draw(self, surf):
        if self.life <= 0: return
        alpha = max(0, min(255, int(255 * (self.life / self.max_life))))
        col = (*self.color[:3], alpha) if len(self.color) == 4 else (*self.color, alpha)
        
        # Particles now shrink as they die
        current_size = self.size * (self.life / self.max_life)
        
        if self.kind == 'pixel':
            r = max(1, int(current_size))
            pygame.gfxdraw.box(surf, pygame.Rect(int(self.x - r/2), int(self.y - r/2), r, r), col)
        elif self.kind == 'ripple':
            prog = 1 - self.life / self.max_life
            r = int(self.size + prog * 150)
            s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color[:3], int(180*(1-prog))), (r, r), r, width=max(1,int(8*(1-prog))))
            surf.blit(s, (int(self.x-r), int(self.y-r)))
        elif self.kind == 'line':
            end_x = self.x - self.vx * 4
            end_y = self.y - self.vy * 4
            pygame.draw.line(surf, col, (self.x, self.y), (end_x, end_y), int(current_size))
        elif self.kind == 'confetti':
            s = pygame.Surface((int(current_size), int(current_size/2)), pygame.SRCALPHA)
            s.fill(col)
            s = pygame.transform.rotate(s, self.angle)
            surf.blit(s, s.get_rect(center=(int(self.x), int(self.y))))
        elif self.kind == 'sparkle':
            # Cross shape
            r = int(current_size)
            pygame.draw.line(surf, col, (self.x - r, self.y), (self.x + r, self.y), 2)
            pygame.draw.line(surf, col, (self.x, self.y - r), (self.x, self.y + r), 2)
        elif self.kind == 'triangle':
            size = int(current_size)
            points = [(-size, -size//2), (size, -size//2), (0, size//2)]
            rad = math.radians(self.angle)
            cos_a, sin_a = math.cos(rad), math.sin(rad)
            rotated_points = [(self.x + x*cos_a - y*sin_a, self.y + x*sin_a + y*cos_a) for x, y in points]
            try:
                pygame.gfxdraw.filled_polygon(surf, rotated_points, col)
            except: pass # Can fail if points are off-screen
        else:
            r = int(current_size)
            if r > 0:
                pygame.gfxdraw.filled_circle(surf, int(self.x), int(self.y), r, col)

class TextParticle(Particle):
    def __init__(self, x, y, text, color, life):
        super().__init__(x, y, 0, -1.5, life, 0, color, kind='text', gravity=0.05)
        self.font = pygame.font.SysFont('arial', 20, bold=True)
        self.text = text

    def draw(self, surf):
        if self.life <= 0: return
        alpha = max(0, min(255, int(255 * (self.life / self.max_life)**2)))
        
        text_surf = self.font.render(self.text, True, self.color)
        text_surf.set_alpha(alpha)
        
        surf.blit(text_surf, text_surf.get_rect(center=(self.x, self.y)))

# --- BUTTON RENDERER FUNCTIONS ---
# These functions are decoupled from the Button class for modularity.
# Each function is responsible for drawing a specific button variant.

def draw_header(btn, surf, rect, color):
    font = btn.app.font_small
    txt = font.render(btn.text, True, (100, 110, 130))
    surf.blit(txt, txt.get_rect(center=(rect.centerx, rect.centery + 10)))
    pygame.draw.line(surf, (40, 50, 60), (rect.centerx - 120, rect.centery + 25), (rect.centerx + 120, rect.centery + 25), 1)
    return rect

def draw_circular(btn, surf, rect, color):
    r = int(min(rect.w, rect.h) / 2.2)
    cx, cy = int(rect.centerx), int(rect.centery)
    pygame.gfxdraw.filled_circle(surf, cx, cy+4, r, (0,0,0,60))
    if btn.variant == 'firefly':
        pygame.gfxdraw.filled_circle(surf, cx, cy, r, (20, 25, 35))
        pygame.gfxdraw.aacircle(surf, cx, cy, r, (60, 70, 80))
        glow_r = int(r * (0.6 + 0.1 * math.sin(time.time() * 3) + btn.val_pull * 0.2))
        pygame.gfxdraw.filled_circle(surf, cx, cy, glow_r, (*btn.color[:3], 100))
    elif btn.variant == 'bubble':
        pygame.gfxdraw.filled_circle(surf, cx, cy, r, color)
        pygame.gfxdraw.filled_circle(surf, int(cx - r*0.2), int(cy - r*0.2), int(r*0.6), (255,255,255,40))
        pygame.gfxdraw.aacircle(surf, cx, cy, r, (255,255,255,100))
    else:
        pygame.gfxdraw.filled_circle(surf, cx, cy, r, color)
        pygame.gfxdraw.aacircle(surf, cx, cy, r, (255,255,255,50))
    if btn.variant == 'coin':
        pygame.gfxdraw.aacircle(surf, cx, cy, int(r*0.8), (255,255,200))
    elif btn.variant == 'candy':
        for i in range(0, 360, 45):
            rad = math.radians(i + time.time() * 50)
            ex, ey = cx + math.cos(rad) * r * 0.8, cy + math.sin(rad) * r * 0.8
            pygame.draw.line(surf, (255,255,255,80), (cx, cy), (ex, ey), 3)
    pygame.gfxdraw.filled_circle(surf, int(cx - r*0.3), int(cy - r*0.3), int(r*0.25), (255,255,255,80))
    return rect

def draw_pixel(btn, surf, rect, color):
    shadow_off = 4 + int(btn.val_pull * 4)
    pygame.draw.rect(surf, (0,0,0,80), rect.move(shadow_off, shadow_off))
    pygame.draw.rect(surf, color, rect)
    pygame.draw.rect(surf, (255,255,255), rect, 3)
    pygame.draw.rect(surf, (0,0,0), rect.inflate(2,2), 2)
    if btn.variant == 'glitch':
        glitch_chance = 0.1 + btn.val_pull * 0.5
        if random.random() < glitch_chance:
            gx = rect.x + random.randint(0, int(rect.w))
            gy = rect.y + random.randint(0, int(rect.h))
            gr = pygame.Rect(gx, gy, random.randint(10, 40), random.randint(2, 6))
            pygame.draw.rect(surf, random.choice([(255,50,50), (50,255,255), (20,20,20)]), gr)
    return rect

def draw_laser(btn, surf, rect, color):
    if btn.laser_glow_cache is None:
        base_w, base_h = btn.w + 20, btn.h + 20
        glow_surf = pygame.Surface((base_w, base_h), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (*btn.color[:3], 80), glow_surf.get_rect(), border_radius=10)
        if base_w > 4 and base_h > 4:
            small = pygame.transform.smoothscale(glow_surf, (int(base_w/4), int(base_h/4)))
            btn.laser_glow_cache = pygame.transform.smoothscale(small, (base_w, base_h))
        else:
            btn.laser_glow_cache = glow_surf
    if rect.w > 0 and rect.h > 0:
        scaled_glow = pygame.transform.smoothscale(btn.laser_glow_cache, (int(rect.w+20), int(rect.h+20)))
        surf.blit(scaled_glow, (rect.x - 10, rect.y - 10), special_flags=pygame.BLEND_RGBA_ADD)
    pygame.draw.rect(surf, (10,10,10), rect, border_radius=4)
    pygame.draw.rect(surf, color, rect, 2, border_radius=4)
    return rect

def draw_ui(btn, surf, rect, color):
    shadow_color = (*btn.app.accent_color[:3], 40) if btn.hover else (0,0,0,60)
    shadow_offset = 2 if btn.hover else 4
    pygame.draw.rect(surf, shadow_color, rect.move(0, shadow_offset), border_radius=8)
    if btn.hover:
        top_color = tuple(min(255, c+15) for c in color); bottom_color = tuple(max(0, c-15) for c in color)
        pygame.draw.rect(surf, top_color, (rect.x, rect.y, rect.w, rect.h/2), border_top_left_radius=8, border_top_right_radius=8)
        pygame.draw.rect(surf, bottom_color, (rect.x, rect.centery, rect.w, rect.h/2), border_bottom_left_radius=8, border_bottom_right_radius=8)
    else:
        pygame.draw.rect(surf, color, rect, border_radius=8)
    if btn.hover:
        pygame.draw.rect(surf, btn.app.accent_color, rect, 2, border_radius=8)
    return rect

def draw_standard(btn, surf, rect, color):
    # Shadow
    shadow_surf = pygame.Surface((rect.w+20, rect.h+20), pygame.SRCALPHA)
    pygame.gfxdraw.filled_ellipse(shadow_surf, int(rect.w/2+10), int(rect.h/2+10+4), int(rect.w/2), int(rect.h/2), (0,0,0,50))
    surf.blit(shadow_surf, (rect.x-10, rect.y-10 + (2 if btn.pressed else 0)))
    # Body
    pygame.draw.rect(surf, color, rect, border_radius=16)
    # Gloss
    pygame.draw.rect(surf, (255,255,255,20), rect.inflate(-4, -rect.h/2).move(0, -rect.h/4 + 2), border_radius=16)
    return rect

def draw_neumorphic(btn, surf, rect, color):
    # Light source top-left
    light_color = (255, 255, 255, 90)
    shadow_color = (163, 177, 198, 180)
    base_color = NEUMORPHIC_BASE
    
    if btn.pressed:
        # Inner shadow look
        inset_rect = rect.inflate(-4, -4)
        pygame.draw.rect(surf, (208, 215, 224), rect, border_radius=12)
        pygame.gfxdraw.box(surf, inset_rect, (*shadow_color[:3], 30))
        s = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        pygame.draw.rect(s, light_color, s.get_rect().move(2,2), border_radius=12)
        surf.blit(s, rect.topleft, special_flags=pygame.BLEND_RGBA_SUB)
    else:
        # Outer shadow
        pygame.draw.rect(surf, shadow_color, rect.move(4, 4), border_radius=12)
        pygame.draw.rect(surf, light_color, rect.move(-4, -4), border_radius=12)
        pygame.draw.rect(surf, base_color, rect, border_radius=12)
    return rect

def draw_glass(btn, surf, rect, color):
    glass_surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    glass_surf.fill((255, 255, 255, 25))
    shine_poly = [ (0,0), (rect.w*0.6, 0), (rect.w*0.3, rect.h), (0,rect.h) ]
    pygame.draw.polygon(glass_surf, (255,255,255,30), shine_poly)
    surf.blit(glass_surf, rect.topleft)
    pygame.draw.rect(surf, (255, 255, 255, 100), rect, 1, border_radius=12)
    return rect

def draw_outline(btn, surf, rect, color):
    col = ACCENT if btn.hover else (150, 150, 150)
    pygame.draw.rect(surf, col, rect, 2, border_radius=8)
    if btn.pressed:
        s = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        s.fill((*col[:3], 50))
        surf.blit(s, rect.topleft)
    return rect

def draw_retro(btn, surf, rect, color):
    base, light, dark, black = (192, 192, 192), (255, 255, 255), (128, 128, 128), (0, 0, 0)
    pygame.draw.rect(surf, base, rect)
    if not btn.pressed:
        pygame.draw.line(surf, light, rect.topleft, rect.topright, 2)
        pygame.draw.line(surf, light, rect.topleft, rect.bottomleft, 2)
        pygame.draw.line(surf, dark, rect.bottomleft, rect.bottomright, 2)
        pygame.draw.line(surf, dark, rect.topright, rect.bottomright, 2)
        pygame.draw.line(surf, black, (rect.right-1, rect.top), (rect.right-1, rect.bottom), 1)
        pygame.draw.line(surf, black, (rect.left, rect.bottom-1), (rect.right, rect.bottom-1), 1)
    else:
        pygame.draw.rect(surf, dark, rect, 2)
    return rect

def draw_cyber(btn, surf, rect, color):
    cut = 15
    pts = [(rect.left + cut, rect.top), (rect.right, rect.top), (rect.right, rect.bottom - cut), (rect.right - cut, rect.bottom), (rect.left, rect.bottom), (rect.left, rect.top + cut)]
    col = color if not btn.hover else (255, 255, 150)
    grad_surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    pygame.draw.polygon(grad_surf, col, [(p[0]-rect.left, p[1]-rect.top) for p in pts])
    surf.blit(grad_surf, rect.topleft)
    pygame.draw.polygon(surf, (0,0,0), pts, 3)
    return rect

def draw_soft(btn, surf, rect, color):
    shadow_col = (200, 130, 140)
    if not btn.pressed:
        pygame.draw.rect(surf, shadow_col, rect.move(0, 6), border_radius=20)
    pygame.draw.rect(surf, color, rect.move(0, 3 if btn.pressed else 0), border_radius=20)
    return rect

def draw_toggle(btn, surf, rect, color):
    target_knob_x = rect.right - rect.height/2 if btn.toggled_on else rect.left + rect.height/2
    if btn.knob_x == 0: btn.knob_x = target_knob_x
    btn.knob_x += (target_knob_x - btn.knob_x) * 0.2
    bg_col = ACCENT if btn.toggled_on else (60, 70, 90)
    pygame.draw.rect(surf, bg_col, rect, border_radius=int(rect.h/2))
    knob_r = int(rect.h/2) - 6
    pygame.gfxdraw.filled_circle(surf, int(btn.knob_x), int(rect.centery), knob_r, (255,255,255))
    return rect

def draw_morph(btn, surf, rect, color):
    eased_morph = btn.morph_progress**2
    m_w = btn.w + 60 * eased_morph
    m_h = btn.h
    m_radius = int((m_h/2) * (1 - eased_morph) + 20 * eased_morph)
    rect = pygame.Rect(int(rect.centerx - m_w/2), int(rect.centery - m_h/2), int(m_w), int(m_h))
    pygame.draw.rect(surf, color, rect, border_radius=m_radius)
    return rect

def draw_liquid(btn, surf, rect, color):
    # --- Bulge towards mouse ---
    cx, cy = rect.centerx, rect.centery
    w, h = rect.w, rect.h
    mx, my = btn.app.mouse_pos
    angle_to_mouse = math.atan2(my - cy, mx - cx)
    pull = btn.val_pull
    
    segments = 40
    points = []
    for i in range(segments):
        ang = (i / segments) * math.pi * 2
        
        # Calculate how much this point should bulge
        diff = abs((ang - angle_to_mouse + math.pi) % (2 * math.pi) - math.pi)
        bulge_factor = max(0, 1 - diff / (math.pi / 1.5))**3 # Concentrated bulge
        bulge_amount = pull * 25 * bulge_factor
        
        # Base ellipse shape
        base_rx = w / 2
        base_ry = h / 2
        
        px = cx + math.cos(ang) * (base_rx + bulge_amount)
        py = cy + math.sin(ang) * (base_ry + bulge_amount)
        points.append((px, py))

    # Draw the bulging shape
    if len(points) > 2:
        pygame.gfxdraw.filled_polygon(surf, points, (*color[:3], 60))

    # Animated waves for distortion/highlight (drawn inside the shape)
    for i in range(3):
        amplitude = (h / (10 + i*4)) * (1 + btn.val_pull * 1.5) # Agitate with proximity
        frequency = 2 + i
        speed = 1.5 + i * 0.5
        y_offset = rect.top + h * 0.5 + (i - 1.5) * h * 0.1
        
        wave_points = []
        for x_p in range(int(rect.left), int(rect.right) + 1):
            y_p = y_offset + math.sin((x_p - rect.left) / w * frequency * 2 * math.pi + time.time() * speed + btn.time_offset) * amplitude
            wave_points.append((x_p, y_p))
        
        if len(wave_points) > 1:
            pygame.draw.aalines(surf, (255, 255, 255, 40 + i*15), False, wave_points)

    # Draw the border
    if len(points) > 2:
        pygame.gfxdraw.aapolygon(surf, points, (255, 255, 255, 120))
    return rect

def draw_intro_orb(btn, surf, rect, color):
    cx, cy = rect.centerx, rect.centery
    r = rect.w / 2
    
    # Liquid distortion calculation
    points = []
    segments = 50
    base_r = r
    
    # Dynamic wobble based on state
    if btn.app.intro_sequence:
        wobble_amp = 10.0 + btn.app.intro_timer * 2 # Wildly unstable as it expands
    elif btn.pressed:
        wobble_amp = 1.5 # Less wobble when squashed down
    elif btn.hover:
        wobble_amp = 6.0
    else: # Idle breathing wobble
        wobble_amp = 2.0 + math.sin(time.time() * 2.5) * 1.5

    for i in range(segments):
        ang = (i / segments) * math.pi * 2
        # Superposition of sines for liquid feel
        offset = math.sin(ang * 3 + time.time() * 4) * wobble_amp * 0.5
        offset += math.cos(ang * 5 - time.time() * 2) * wobble_amp * 0.3
        
        rad = base_r + offset
        px = cx + math.cos(ang) * rad
        py = cy + math.sin(ang) * rad
        points.append((px, py))
    
    # Draw
    if len(points) > 2:
        # Shadow
        if not btn.app.intro_sequence:
            pygame.draw.polygon(surf, (0,0,0,30), [(p[0], p[1]+10) for p in points])
        
        # Main Body (Gradient-ish via layering)
        pygame.draw.polygon(surf, (200, 230, 255), points)
        
        # Inner darker liquid
        inner_points = [(cx + (p[0]-cx)*0.8, cy + (p[1]-cy)*0.8) for p in points]
        pygame.draw.polygon(surf, (180, 210, 250), inner_points)
        
        # Highlight (Gloss)
        gloss_points = []
        for i in range(10): # Top left arc
            idx = (i + int(segments*0.6)) % segments
            p = inner_points[idx]
            gloss_points.append(((p[0]+cx)/2, (p[1]+cy)/2))
        if len(gloss_points) > 2:
             pygame.draw.lines(surf, (255, 255, 255, 200), False, gloss_points, 4)

    # Icon
    if not btn.app.intro_sequence:
        # Simple Play Triangle
        pygame.draw.polygon(surf, (255, 255, 255), [(cx-5, cy-8), (cx-5, cy+8), (cx+10, cy)])
    return rect

def draw_shiny(btn, surf, rect, color):
    pygame.draw.rect(surf, (40,40,45), rect, border_radius=12)
    pygame.draw.rect(surf, (255,255,255,100), rect, 2, border_radius=12)
    return rect

def draw_holographic(btn, surf, rect, color):
    base_surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    base_surf.fill((80, 150, 255, 20))
    surf.blit(base_surf, rect.topleft)
    hue = (pygame.time.get_ticks() * 0.1) % 360
    c = pygame.Color(0); c.hsva = (hue, 80, 100, 100)
    pygame.draw.rect(surf, c, rect, 2, border_radius=8)
    return rect

def draw_jelly(btn, surf, rect, color):
    r = int(min(rect.w, rect.h) / 2.2)
    pygame.gfxdraw.filled_circle(surf, int(rect.centerx), int(rect.centery), r, (*color[:3], 100))
    pygame.gfxdraw.aacircle(surf, int(rect.centerx), int(rect.centery), r, (255,255,255,120))
    return rect

def draw_ghost(btn, surf, rect, color):
    if btn.hover or btn.pressed:
        pygame.draw.rect(surf, color, rect, border_radius=8)
    else:
        pygame.draw.rect(surf, color, rect, 2, border_radius=8)
    return rect

def draw_gradient(btn, surf, rect, color):
    c1 = color
    c2 = tuple(min(255, c + 40) for c in btn.color[:3])
    if rect.h > 0:
        grad_strip = pygame.Surface((1, int(rect.h)))
        for i in range(int(rect.h)):
            p = i / rect.h
            r, g, b = [c1[j] * (1 - p) + c2[j] * p for j in range(3)]
            grad_strip.set_at((0, i), (int(r), int(g), int(b)))
        surf.blit(pygame.transform.smoothscale(grad_strip, (int(rect.w), int(rect.h))), rect.topleft)
    pygame.draw.rect(surf, (255,255,255,40), rect, 1, border_radius=10)
    return rect

def draw_link(btn, surf, rect, color):
    font = btn.app.font_large if btn.w > 160 else btn.app.font_small
    text_surf = font.render(btn.text, True, color)
    text_rect = text_surf.get_rect(center=rect.center)
    surf.blit(text_surf, text_rect)
    if btn.underline_progress > 0.01:
        lw = text_rect.width * btn.underline_progress
        ly = text_rect.bottom + 2
        pygame.draw.line(surf, color, (text_rect.centerx - lw/2, ly), (text_rect.centerx + lw/2, ly), 2)
    return text_rect

def draw_flat(btn, surf, rect, color):
    if btn.variant == 'secondary':
        pygame.draw.rect(surf, color, rect, 2, border_radius=8)
    else:
        pygame.draw.rect(surf, color, rect, border_radius=8)
    if btn.hover and btn.variant != 'secondary':
        pygame.draw.rect(surf, (255,255,255,30), rect, border_radius=8)
    return rect

def draw_download(btn, surf, rect, color):
    if btn.download_state == 'idle':
        pygame.draw.rect(surf, color, rect, border_radius=12)
    elif btn.download_state == 'downloading':
        pygame.draw.rect(surf, (40, 50, 60), rect, border_radius=12)
        if btn.download_progress > 0:
            pygame.draw.rect(surf, color, (rect.x, rect.y, rect.w * btn.download_progress, rect.h), border_radius=12)
    elif btn.download_state == 'done':
        pygame.draw.rect(surf, (16, 185, 129), rect, border_radius=12)
    return rect

def draw_hold(btn, surf, rect, color):
    pygame.draw.rect(surf, (40, 50, 60), rect, border_radius=30)
    if btn.hold_progress > 0:
        pygame.draw.rect(surf, btn.app.accent_color, (rect.x, rect.y, rect.w * btn.hold_progress, rect.h), border_radius=30)
    pygame.draw.rect(surf, (255,255,255,50), rect, 2, border_radius=30)
    return rect

def draw_slider(btn, surf, rect, color):
    track_rect = pygame.Rect(rect.centerx - rect.w/2, rect.centery - 4, rect.w, 8)
    pygame.draw.rect(surf, (40, 50, 60), track_rect, border_radius=4)
    fill_w = rect.w * btn.slider_val
    pygame.draw.rect(surf, ACCENT, (track_rect.x, track_rect.y, fill_w, 8), border_radius=4)
    pygame.draw.circle(surf, (255, 255, 255), (int(track_rect.x + fill_w), int(rect.centery)), 10)
    return track_rect

def draw_fab(btn, surf, rect, color):
    r = int(min(rect.w, rect.h) / 2)
    pygame.gfxdraw.filled_circle(surf, int(rect.centerx), int(rect.centery) + (4 if btn.hover else 2), r + (2 if btn.hover else 0), (0,0,0,60))
    pygame.gfxdraw.filled_circle(surf, int(rect.centerx), int(rect.centery), r, color)
    icon_w = int(r * 0.8)
    pygame.draw.rect(surf, (255,255,255), (rect.centerx - icon_w/2, rect.centery - 1.5, icon_w, 3), border_radius=1)
    pygame.draw.rect(surf, (255,255,255), (rect.centerx - 1.5, rect.centery - icon_w/2, 3, icon_w), border_radius=1)
    return pygame.Rect(rect.centerx-r, rect.centery-r, r*2, r*2)

def draw_menu(btn, surf, rect, color):
    if btn.hover: pygame.draw.rect(surf, (255,255,255,20), rect, border_radius=8)
    t = btn.toggle_progress
    spacing = 9
    y_top = (rect.centery - spacing) * (1-t) + rect.centery * t
    y_bot = (rect.centery + spacing) * (1-t) + rect.centery * t
    pygame.draw.line(surf, (220, 230, 240), (rect.centerx - 15, y_top), (rect.centerx + 15, y_top), 3)
    if t < 0.5: pygame.draw.line(surf, (220, 230, 240), (rect.centerx - 15, rect.centery), (rect.centerx + 15, rect.centery), 3)
    pygame.draw.line(surf, (220, 230, 240), (rect.centerx - 15, y_bot), (rect.centerx + 15, y_bot), 3)
    return rect

def draw_social(btn, surf, rect, color):
    r = int(min(rect.w, rect.h) / 2)
    pygame.gfxdraw.filled_circle(surf, int(rect.centerx), int(rect.centery), r, color)
    font = btn.app.font_large
    txt = font.render(btn.text[:1], True, (255,255,255))
    surf.blit(txt, txt.get_rect(center=rect.center))
    return pygame.Rect(rect.centerx-r, rect.centery-r, r*2, r*2)

def draw_status(btn, surf, rect, color):
    pygame.draw.rect(surf, (40, 50, 60), rect, border_radius=8)
    pygame.draw.circle(surf, (16, 185, 129), (int(rect.right - 20), int(rect.centery)), 5)
    return rect

def draw_music(btn, surf, rect, color):
    pygame.draw.rect(surf, (30, 35, 45), rect, border_radius=16)
    bar_count = 16
    bar_w = (rect.w - 40 - (4 * (bar_count - 1))) / bar_count
    for i in range(bar_count):
        h_factor = btn.music_bar_heights[i]
        if btn.music_playing:
             target = btn.app.audio_levels[i] if btn.app.audio_levels is not None else (math.sin(time.time()*8+i)*0.5+0.5)
             btn.music_bar_heights[i] += (target - h_factor) * 0.4
        else:
             btn.music_bar_heights[i] += (0.1 - h_factor) * 0.1
        bar_h = (rect.h - 40) * btn.music_bar_heights[i]
        pygame.draw.rect(surf, color, (rect.left + 20 + i*(bar_w+4), rect.bottom - 20 - bar_h, bar_w, bar_h), border_radius=2)
    return rect

def draw_search_bar(btn, surf, rect, color):
    pygame.draw.rect(surf, (30, 35, 45), rect, border_radius=8)
    border_col = ACCENT if btn.app.search_active else (60, 70, 80)
    pygame.draw.rect(surf, border_col, rect, 2, border_radius=8)
    font = btn.app.font_small
    display_text = btn.app.search_text if btn.app.search_text else "Search buttons..."
    text_color = (200, 210, 220) if btn.app.search_text else (100, 110, 120)
    txt_surf = font.render(display_text, True, text_color)
    surf.blit(txt_surf, txt_surf.get_rect(midleft=(rect.left + 20, rect.centery)))
    return rect

def draw_load_card(btn, surf, rect, color):
    pygame.draw.rect(surf, (30, 35, 45), rect, border_radius=12)
    if btn.variant == 'load_spinner':
        angle = time.time() * 300
        rect_s = pygame.Rect(rect.centerx-20, rect.centery-30, 40, 40)
        pygame.draw.arc(surf, ACCENT, rect_s, math.radians(angle), math.radians(angle + 240), 4)
    elif btn.variant == 'load_bar':
        pygame.draw.rect(surf, (50, 60, 70), (rect.centerx-60, rect.centery-10, 120, 8), border_radius=3)
        pygame.draw.rect(surf, SECOND, (rect.centerx-60, rect.centery-10, 120 * ((math.sin(time.time()*2)+1)/2), 8), border_radius=3)
    elif btn.variant == 'load_dots':
        for i in range(3):
            dy = rect.centery - 10 + math.sin(time.time()*8+i*0.5)*6
            pygame.draw.circle(surf, [ACCENT, SECOND, TERTIARY][i], (int(rect.centerx + (i-1)*20), int(dy)), 6)
    return rect

DRAW_HANDLERS = {
    'bubble': draw_circular, 'candy': draw_circular, 'coin': draw_circular,
    'blackhole': draw_circular, 'firefly': draw_circular, 'slime': draw_circular,
    'grow': draw_circular,
    'pixel': draw_pixel, 'glitch': draw_pixel,
    'laser': draw_laser,
    'ui': draw_ui,
    'neumorphic': draw_neumorphic,
    'glass': draw_glass,
    'outline': draw_outline,
    'retro': draw_retro,
    'cyber': draw_cyber,
    'soft': draw_soft,
    'toggle': draw_toggle,
    'morph': draw_morph,
    'liquid': draw_liquid,
    'intro_orb': draw_intro_orb,
    'load_spinner': draw_load_card,
    'load_bar': draw_load_card,
    'load_dots': draw_load_card,
    'load_pulse': draw_load_card,
    'header': draw_header,
    'shiny': draw_shiny,
    'holographic': draw_holographic,
    'jelly': draw_jelly,
    'ghost': draw_ghost,
    'gradient': draw_gradient,
    'link': draw_link,
    'primary': draw_flat, 'secondary': draw_flat, 'danger': draw_flat,
    'download': draw_download,
    'hold': draw_hold,
    'slider': draw_slider,
    'fab': draw_fab,
    'menu': draw_menu,
    'social': draw_social,
    'status': draw_status,
    'music': draw_music,
    'search_bar': draw_search_bar,
}

BUTTON_COLOR_MAP = {
    'liquid': (180, 220, 255),
    'toggle': (150, 160, 180),
    'morph': (147, 112, 219),
    'retro': (192, 192, 192),
    'cyber': (255, 230, 0),
    'soft': (255, 180, 190),
    'intro_orb': (200, 230, 255),
    'link': ACCENT,
    'primary': ACCENT,
    'secondary': (150, 160, 170),
    'danger': (239, 68, 68),
    'download': SECOND,
    'fab': ACCENT,
    'social': (59, 130, 246), # Blue
    'menu': (40, 50, 70), # Dark background for menu button usually
    'status': (40, 50, 70),
    'music': (236, 72, 153),
}
RANDOM_COLOR_VARIANTS = [
    'bubble', 'candy', 'ripple', 'pixel', 'firefly', 
    'glitch', 'ghost', 'gradient', 'shatter', 'jelly'
]

class Button:
    def __init__(self, app, x, y, w, h, text, variant='standard', command=None):
        self.app = app
        self.x = x; self.y = y; self.w = w; self.h = h
        self.text = text
        # Visual position for physics/magnetic effects
        self.vis_x = x
        self.vis_y = y
        self.vis_x_vel = 0; self.vis_y_vel = 0
        self.variant = variant
        self.hover = False
        self.pressed = False
        self.count = 0
        self.color = (40, 50, 70) # Default color
        self.current_color = list(self.color) # For smooth transition
        self.scale = 1.0
        self.scale_vel = 0.0
        self.target_scale = 1.0
        self.visible = True
        self.wobble = 0.0
        self.anim_state = 'active' # active, entering, exiting
        self.anim_progress = 0.0
        self.command = command
        self.toggled_on = False
        self.morph_progress = 0.0
        self.knob_x = 0
        self.liquid_distortion = 0.0
        self.underline_progress = 0.0
        self.text_cycle_index = 0
        self.hold_progress = 0.0
        self.download_progress = 0.0
        self.download_state = 'idle' # idle, downloading, done
        self.slider_val = 0.5
        self.shatter_cooldown = 0
        self.toggle_progress = 0.0
        self.music_playing = False
        self.music_bar_heights = [0.1] * 16 # For smooth animation
        
        # Refactored color initialization
        self.color = BUTTON_COLOR_MAP.get(self.variant)
        if self.color is None:
            if self.variant in RANDOM_COLOR_VARIANTS:
                self.color = random.choice(RANDOM_COLORS)
            else:
                self.color = (40, 50, 70) # Default

        self.current_color = list(self.color)
        self.scale = 1.0
        self.orb_angle = 0.0
        self.orb_velocity = 2.0
        self.val_pull = 0.0
        self.time_offset = random.random() * 100
        
        # Caches for expensive rendering operations
        self.laser_glow_cache = None
        # Drawing handlers are now globally defined

    def contains(self, px, py):
        if not self.visible: return False
        return (self.x - self.w/2 <= px <= self.x + self.w/2) and (self.y - self.h/2 <= py <= self.y + self.h/2)

    def update(self, mx, my):
        # Spring physics for scale
        stiffness = 0.35
        damping = 0.65
        
        # Proximity / Magnetic Effect
        dist = math.hypot(mx - self.x, my - self.y)
        # Increased range and sensitivity for better feel
        range_limit = 200
        pull = max(0.0, (range_limit - dist) / range_limit)
        pull = pull * pull # Quadratic ease-in for smoother onset
        self.val_pull = pull

        # Liquid button "sucks in" the mouse cursor with particles
        if self.variant == 'liquid':
            if pull > 0.1 and random.random() < pull * 0.4: # Spawn more particles the closer the mouse is
                    # Spawn particle at mouse position
                    px, py = mx, my
                    
                    # Calculate velocity vector towards the button's center
                    dist_x = self.x - px
                    dist_y = self.y - py
                    dist_total = math.hypot(dist_x, dist_y)
                    
                    if dist_total > 1:
                        # Normalize vector and add speed
                        speed = random.uniform(4, 9)
                        vx = (dist_x / dist_total) * speed + random.uniform(-1, 1)
                        vy = (dist_y / dist_total) * speed + random.uniform(-1, 1)
                        self.app.particles.append(Particle(px, py, vx, vy, 25, random.uniform(1, 4), (200, 230, 255), 'pixel', gravity=0))
            
            # Lose liquid that sticks to mouse
            if pull > 0.7 and random.random() < 0.08:
                angle_to_mouse = math.atan2(my - self.y, mx - self.x)
                # Spawn from the edge of the button
                spawn_x = self.x + math.cos(angle_to_mouse) * self.w / 2.2
                spawn_y = self.y + math.sin(angle_to_mouse) * self.h / 2.2
                
                p = Particle(spawn_x, spawn_y, 0, 0, 150, random.uniform(5, 10), 
                             (200, 230, 255, 150), 'sticky_liquid', gravity=0)
                self.app.particles.append(p)

        # Target visual position (Magnetic pull)
        target_vis_x = self.x + (mx - self.x) * pull * 0.2
        target_vis_y = self.y + (my - self.y) * pull * 0.2
        
        # Spring physics for position
        self.vis_x_vel += (target_vis_x - self.vis_x) * 0.15
        self.vis_x_vel *= 0.6
        self.vis_x += self.vis_x_vel
        self.vis_y_vel += (target_vis_y - self.vis_y) * 0.15
        self.vis_y_vel *= 0.6
        self.vis_y += self.vis_y_vel

        # Scale physics
        if self.variant == 'intro_orb' and not self.app.intro_sequence and not self.hover and not self.pressed:
            # Gentle breathing effect for the orb
            self.target_scale = 1.0 + math.sin(time.time() * 2.5) * 0.03
        elif not self.hover and not self.pressed:
            self.target_scale = 1.0 + pull * 0.15

        # Morphing logic
        if self.variant == 'morph':
            target_morph = 1.0 if self.hover else 0.0
            self.morph_progress += (target_morph - self.morph_progress) * 0.1
            
        # Toggle progress smoothing
        target_toggle = 1.0 if self.toggled_on else 0.0
        self.toggle_progress += (target_toggle - self.toggle_progress) * 0.15

        if self.shatter_cooldown > 0:
            self.shatter_cooldown -= 1

        # Hold button logic
        if self.variant == 'hold':
            if self.pressed:
                self.hold_progress += 0.015
                if self.hold_progress >= 1.0:
                    self.hold_progress = 0.0
                    self.activate()
                    self.pressed = False # Reset
            else:
                self.hold_progress = max(0, self.hold_progress - 0.05)

        # Download button logic
        if self.variant == 'download':
            if self.download_state == 'downloading':
                self.download_progress += 0.005
                if self.download_progress >= 1.0:
                    self.download_progress = 1.0
                    self.download_state = 'done'
                    self.text = "DONE"
                    self.app.play_click('success')

        # Slider logic
        if self.variant == 'slider' and self.pressed:
            self.slider_val = max(0.0, min(1.0, (mx - (self.x - self.w/2)) / self.w))

        # Intro Orb Physics (Smooth Rotation)
        if self.variant == 'intro_orb' and not self.app.intro_sequence:
            # Base speed 2, adds up to 10 from proximity, jumps to 25 on hover. Smoother lerp.
            target_vel = 2.0 + pull * 10.0
            if self.hover: target_vel = 25.0
            self.orb_velocity += (target_vel - self.orb_velocity) * 0.08
            self.orb_angle += self.orb_velocity

        # Smooth Color Transition
        target_col = self.color
        if self.variant == 'ui' and self.hover: target_col = (50, 60, 80)
        if self.variant == 'ui' and self.pressed: target_col = (30, 40, 60)
        
        for i in range(3):
            self.current_color[i] += (target_col[i] - self.current_color[i]) * 0.15

        force = (self.target_scale - self.scale) * stiffness
        self.scale_vel += force
        self.scale_vel *= damping
        self.scale += self.scale_vel
        self.wobble *= 0.92

        if self.variant == 'link':
            target_underline = 1.0 if self.hover else 0.0
            self.underline_progress += (target_underline - self.underline_progress) * 0.15
 
        # Animation state machine
        if self.anim_state in ['entering', 'exiting']:
            if self.anim_progress < 0:
                self.anim_progress += 0.05 # Delay timer
                return

            self.anim_progress += 0.05
            if self.anim_progress >= 1.0:
                self.anim_progress = 1.0
                if self.anim_state == 'exiting': self.visible = False
                self.anim_state = 'active'

        # Intro Orb Suction Effect
        if self.variant == 'intro_orb' and self.hover and not self.app.intro_sequence:
             if random.random() < 0.8: # Increased spawn rate
                 angle = random.uniform(0, 6.28)
                 dist = 130 # Start further out
                 px = self.x + math.cos(angle) * dist
                 py = self.y + math.sin(angle) * dist
                 
                 # Spiral velocity
                 speed = random.uniform(8, 14) # Increased speed
                 vx = -math.cos(angle) * speed
                 vy = -math.sin(angle) * speed
                 # Using 'pixel' kind for small energy bits
                 self.app.particles.append(Particle(px, py, vx, vy, 20, 2, (180, 230, 255), 'line', gravity=0))

        # Global Hover Effect (Subtle particles for all buttons)
        if self.hover and self.variant != 'intro_orb' and self.variant != 'header':
             if random.random() < 0.15:
                 # Spawn a small rising particle
                 p_col = tuple(min(255, c+40) for c in self.color[:3])
                 self.app.particles.append(Particle(self.x + random.uniform(-self.w/2, self.w/2), self.y + self.h/2, 0, random.uniform(-1, -2), 25, 2, p_col, 'pixel', gravity=0))

    def draw(self, surf):
        if not self.visible or self.shatter_cooldown > 0: return
        
        # Apply wobble to scale
        s = self.scale + math.sin(time.time() * 20) * self.wobble
        w, h = self.w * s, self.h * s
        cx, cy = self.vis_x, self.vis_y

        # --- Global Transition Animation ---
        if self.app.state != 'INTRO':
            t_norm = self.app.transition_alpha / 255.0
            # Smooth easing
            if self.app.transition_fade_in:
                 ease = 1 - (1 - t_norm)**3 # Ease Out
            else:
                 ease = t_norm**3 # Ease In
            
            if self.variant == 'ui':
                if self.x < 300: # Sidebar buttons
                    cx -= 260 * ease
                elif self.x > self.app.W - 300: # Copy code button
                    cx += 400 * ease
            elif self.variant == 'intro_orb':
                # Zoom out on exit
                if not self.app.transition_fade_in:
                    s *= (1 + ease * 5)
                    self.app.transition_alpha = min(255, self.app.transition_alpha + 5) # Speed up fade
            else:
                # Content buttons: Staggered slide down
                # Calculate a delay based on index or Y position to make them cascade
                stagger = (self.y / self.app.H) * 0.2
                slide_amount = 150 * max(0, ease - stagger)
                cy += slide_amount

        draw_color = tuple(map(int, self.current_color))

        # Entry/Exit animation
        if self.anim_state == 'entering':
            if self.anim_progress < 0: return # In delay, don't draw

            eased_prog = 1 - (1 - self.anim_progress)**3
            cy = self.vis_y - self.app.H * (1 - eased_prog)
        elif self.anim_state == 'exiting':
            eased_prog = self.anim_progress**3
            cy = self.vis_y + self.app.H * eased_prog

        # --- SHAPE RENDERING ---
        rect = pygame.Rect(int(cx - w/2), int(cy - h/2), int(w), int(h))
        handler = DRAW_HANDLERS.get(self.variant, draw_standard)
        text_rect = handler(self, surf, rect, draw_color)

        # --- TEXT & COUNTER RENDERING ---
        text_variants_to_exclude = [
            'header', 'toggle', 'intro_orb', 'load_spinner', 'load_bar', 
            'load_dots', 'load_pulse', 'link', 'slider', 'fab', 'menu', 
            'social', 'music'
        ]
        if self.variant not in text_variants_to_exclude:
            self._draw_text(surf, text_rect if text_rect else rect)

    def _get_text_color(self):
        # Default
        text_color = TEXT

        # Variant-specific overrides
        if self.variant == 'ghost' and not self.hover:
            return self.color
        elif self.variant == 'neumorphic':
            return (100, 100, 110)
        elif self.variant in ['retro', 'cyber']:
            return (20, 20, 20)
        elif self.variant == 'soft':
            return (255, 255, 255)
        
        # Adaptive color for solid backgrounds
        adaptive_variants = [
            'primary', 'danger', 'download', 'gradient', 'shatter', 
            'bubble', 'candy', 'ripple', 'pixel', 'firefly', 
            'glitch', 'jelly', 'status'
        ]
        if self.variant in adaptive_variants or (self.variant == 'ghost' and self.hover):
            return get_text_color_for_bg(self.current_color)

        return text_color

    def _draw_text(self, surf, rect):
        font = self.app.font_large if self.w > 160 else self.app.font_small
        txt_col = self._get_text_color()
        
        txt_shadow = font.render(self.text, True, (0,0,0, 50))
        surf.blit(txt_shadow, txt_shadow.get_rect(center=(rect.centerx, rect.centery + 2)))

        # Glitch text offset
        tx_off = 0
        if self.variant == 'glitch' and random.random() < self.val_pull * 0.3:
            tx_off = random.randint(-2, 2)
        txt = font.render(self.text, True, txt_col)
        surf.blit(txt, txt.get_rect(center=(rect.centerx + tx_off, rect.centery + tx_off)))

        # counter
        if self.count > 0:
            c_font = self.app.font_small
            c_text_str = str(self.count)
            c_shadow = c_font.render(c_text_str, True, (6,10,16))
            c_pos = (rect.right - c_shadow.get_width() - 12, rect.bottom - c_shadow.get_height() - 8)
            surf.blit(c_shadow, (c_pos[0], c_pos[1] + 1))
            c_text = c_font.render(c_text_str, True, TEXT)
            surf.blit(c_text, c_pos)

    def on_hover(self):
        if not self.hover:
            self.hover = True
            self.target_scale = 1.05
            if self.variant in ['bubble', 'candy', 'slime']:
                self.wobble = 0.1
            if self.variant == 'jelly':
                self.wobble = 0.25
            if self.app.sound_on:
                self.app.play_hover()

    def on_exit(self):
        self.hover = False
        self.target_scale = 1.0

    def on_down(self, mx, my):
        if self.anim_state != 'active': return
        
        # Special press-down effect for the intro orb
        if self.variant == 'intro_orb':
            self.pressed = True
            self.target_scale = 0.9 # Squash down
            self.app.particles.append(Particle(self.x, self.y, 0, 0, 40, 10, (220, 230, 255), 'ripple', gravity=0))
            if self.app.sound_on and self.app.intro_orb_press_tone:
                self.app.intro_orb_press_tone.play()
            return # Skip generic press logic

        # Only trigger press effects if not a slider (sliders handle their own logic)
        if self.variant != 'slider':
            self.pressed = True
            self.target_scale = 0.92
            if self.variant == 'soft':
                self.target_scale = 0.9
            if self.variant in ['bubble', 'candy', 'slime', 'jelly']:
                self.wobble = 0.2
            if self.app.sound_on:
                self.app.play_click(self.variant)

    def on_up(self):
        if self.anim_state != 'active': return
        if self.pressed and self.hover:
            if self.variant == 'toggle':
                self.toggled_on = not self.toggled_on
            if self.variant == 'menu':
                self.toggled_on = not self.toggled_on
            if self.command:
                self.command()
            else:
                self.activate()
        self.pressed = False
        self.target_scale = 1.05 if self.hover else 1.0

    def activate(self):
        # spawn particles / effects based on variant
        self.count += 1
        
        # Delegate to the App's effect handler
        self.app.trigger_button_effect(self)

class Star:
    def __init__(self, app):
        self.app = app
        self.x = random.uniform(0, app.W)
        self.y = random.uniform(0, app.H)
        self.depth = random.uniform(0.1, 0.9)
        self.size = self.depth * 2
        self.color = (int(self.depth * 100), int(self.depth * 100), int(self.depth * 150))

    def update(self, mouse_pos):
        parallax_x = (mouse_pos[0] - self.app.W/2) * self.depth * 0.05
        parallax_y = (mouse_pos[1] - self.app.H/2) * self.depth * 0.05
        return (self.x + parallax_x, self.y + parallax_y)


class App:
    def __init__(self):
        pygame.init()
        self.sound_on = True
        try:
            pygame.mixer.pre_init(SAMPLE_RATE, -16, 1, 512)
            pygame.mixer.init()
        except pygame.error as e:
            print(f"Warning: Audio initialization failed ({e}). Sound disabled.")
            self.sound_on = False
        self.screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
        self.W, self.H = pygame.display.get_surface().get_size()
        pygame.display.set_caption("Satisfying Buttons")
        self.clock = pygame.time.Clock()
        self.running = True
        self.particles = []
        self.shake = 0
        self.flash = 0
        self.mouse_pos = (0,0)
        self.glitch_frames = 0
        self.stars = [Star(self) for _ in range(100)]
        self.transition_alpha = 0
        self.transition_fade_in = False
        self.next_state = None
        self.rainbow_cycle_timer = 0
        self.current_code_snippet = ""
        self.scroll_y = 0.0
        self.scroll_target = 0.0
        self.scroll_vel = 0.0
        self.intro_sequence = False
        self.intro_timer = 0
        self.intro_solidify = False
        self.solidify_progress = 0.0
        self.code_scroll_y = 0.0
        self.code_scroll_target = 0.0
        self.audio_levels = None
        self.audio_stream = None
        self.audio_thread = None
        self.sound_cache = {}
        self.flash_surf = pygame.Surface((self.W, self.H), pygame.SRCALPHA)

        # Audio device settings
        self.audio_devices = []
        if SOUNDDEVICE_AVAILABLE:
            try:
                self.audio_devices = sd.query_devices()
            except Exception as e:
                print(f"Warning: Could not query audio devices: {e}")
        self.selected_audio_device_index = -1 # -1 for auto-detect

        # fonts
        self.font_large = pygame.font.SysFont('sans', 28, bold=True)
        self.font_small = pygame.font.SysFont('sans', 14, bold=True)

        # UI state
        self.state = 'INTRO'
        self.sidebar_buttons = []
        self.showcase_elements = []
        self.active_element = None
        self.visible_showcase_elements = []
        self.search_text = ""
        self.search_active = False
        self.active_input = None
        self.sidebar_initialized = False
        
        self.copy_code_button = Button(self, self.W - 200, 50, 160, 40, "COPY CODE", variant='ui', command=self.copy_code)
        if not PYPERCLIP_AVAILABLE:
            self.copy_code_button.text = "pyperclip missing"
            self.copy_code_button.command = None
        self.search_bar = Button(self, self.W//2, 50, 300, 40, "", variant='search_bar', command=lambda: None)

        self.intro_btn = Button(self, self.W//2, self.H//2, 120, 120, "", variant='intro_orb', command=self.trigger_intro)

        # preload tones
        self.hover_tone = make_tone(980, 0.10, 0.02)
        self.click_tone = make_tone(660, 0.18, 0.12)
        self.crit_tone = make_tone(1200, 0.1, 0.15)
        self.fever_tone = make_tone(220, 0.4, 0.2)
        self.ui_click_tone = make_tone(1500, 0.1, 0.05)
        self.intro_hit = make_tone(100, 0.5, 0.4)
        self.intro_orb_press_tone = make_tone(80, 0.15, 0.3)
        self.whoosh_tone = make_tone(300, 0.3, 0.05) # Transition sound
        

        # Palettes for candy button
        self.candy_palettes = { 'pastel': [(255, 182, 193), (173, 216, 230), (144, 238, 144)], 'neon': [ACCENT, SECOND, TERTIARY], 'mono': [(200,200,200), (150,150,150), (100,100,100)] }
        self.current_candy_palette = 'pastel'

        # Effect dispatcher
        self.effect_handlers = {
            'bubble': self._effect_bubble,
            'candy': self._effect_candy, 'ripple': self._effect_ripple,
            'pixel': self._effect_pixel,
            'firefly': self._effect_firefly,
            'glitch': self._effect_glitch,
            'neumorphic': self._effect_ripple, 'glass': self._effect_ripple, 'outline': self._effect_ripple,
            'retro': self._effect_ripple, 'cyber': self._effect_glitch, 'soft': self._effect_bubble,
            'intro_orb': self._effect_intro,
            'liquid': self._effect_liquid,
            'toggle': self._effect_toggle,
            'morph': self._effect_morph,
            'shiny': self._effect_shiny,
            'holographic': self._effect_holographic,
            'jelly': self._effect_jelly,
            'ghost': self._effect_ripple,
            'gradient': self._effect_gradient,
            'link': self._effect_link,
            'shatter': self._effect_shatter,
            'music': self._effect_music,
        }

        # Dynamic UI Colors
        self.accent_color = ACCENT
        self.default_accent = ACCENT

        # Pre-render background to improve performance
        self.bg_surf = pygame.Surface((self.W, self.H))
        self.bg_surf.fill(BG)
        for i in range(6):
            r = int(max(self.W, self.H) * (0.2 + i*0.12))
            s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.gfxdraw.filled_circle(s, r, r, r, (30,40,60, int(12/(i+1))))
            self.bg_surf.blit(s, (self.W//2 - r, self.H//2 - r), special_flags=pygame.BLEND_RGBA_ADD)
        self.canvas = pygame.Surface((self.W, self.H))
        
        # Start audio capture if possible
        self.start_audio_capture()

    def trigger_intro(self):
        self.intro_sequence = True
        self.intro_timer = 0
        if self.intro_hit:
            self.intro_hit.play()

    def play_hover(self):
        if self.hover_tone:
            self.hover_tone.play()

    def play_click(self, variant):
        try:
            freqs = {'bubble':700,'candy':880,'ripple':520,'pixel':220,'firefly':980,'glitch':100, 'neumorphic': 400, 'glass': 1200, 'retro': 300, 'cyber': 1000, 'soft': 200, 'shiny': 1400, 'holographic': 1100, 'jelly': 300, 'ghost': 600, 'gradient': 800, 'link': 1200}
            f = freqs.get(variant, 520)
            if f not in self.sound_cache:
                self.sound_cache[f] = make_tone(f, 0.16, 0.11)
            self.sound_cache[f].play()
        except: pass

    def start_audio_capture(self):
        if not SOUNDDEVICE_AVAILABLE or not NUMPY_AVAILABLE:
            print("Info: sounddevice or numpy not found. Audio visualization will be simulated.")
            if not NUMPY_AVAILABLE: print("Install with: pip install numpy")
            if not SOUNDDEVICE_AVAILABLE: print("Install with: pip install sounddevice")
            self.audio_levels = np.zeros(16) if NUMPY_AVAILABLE else [0]*16
            self.audio_stream = None
            return

        self.audio_levels = np.zeros(16)
        try:
            device_index = None
            devices = sd.query_devices()

            if self.selected_audio_device_index == -1:
                # Auto-detect logic
                loopback_device_index = None
                for i, device in enumerate(devices):
                    if 'loopback' in device['name'].lower() or 'stereo mix' in device['name'].lower():
                        loopback_device_index = i
                        break
                device_index = loopback_device_index
            else:
                # Use selected device if valid
                if 0 <= self.selected_audio_device_index < len(devices):
                    device_index = self.selected_audio_device_index
                else:
                    print(f"Warning: Selected audio device index {self.selected_audio_device_index} is invalid.")
                    self.audio_stream = None
                    return

            if device_index is None:
                print("Warning: No suitable audio device found or selected. Visualizer will not show system audio.")
                if self.selected_audio_device_index == -1:
                     print("You may need to enable 'Stereo Mix' on Windows or install a virtual audio device.")
                self.audio_stream = None
                return

            self.audio_stream = sd.InputStream(
                device=device_index,
                channels=1,
                samplerate=SAMPLE_RATE,
                blocksize=2048,
                callback=self._audio_callback
            )
            self.audio_stream.start()
            print(f"Success: Audio stream started on device: {devices[device_index]['name']}")

        except Exception as e:
            print(f"Error starting audio stream: {e}")
            self.audio_stream = None

    def _audio_callback(self, indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        
        # Use a window function for better FFT results
        window = np.hanning(len(indata))
        magnitude = np.abs(np.fft.rfft(indata[:, 0] * window))
        
        # Define frequency bands on a logarithmic scale
        freq_bins = np.fft.rfftfreq(len(indata), 1./SAMPLE_RATE)
        log_min, log_max = np.log10(20), np.log10(20000)
        log_freq_cutoffs = np.logspace(log_min, log_max, len(self.audio_levels) + 1)

        new_levels = []
        for i in range(len(self.audio_levels)):
            # Find which frequency bins fall into this visualizer bar
            in_band = (freq_bins >= log_freq_cutoffs[i]) & (freq_bins < log_freq_cutoffs[i+1])
            if np.any(in_band):
                avg_mag = np.mean(magnitude[in_band])
                # Scale logarithmically for better visual perception
                level = np.log10(1 + avg_mag * 10) * 0.3
                new_levels.append(min(1.0, level))
            else:
                new_levels.append(0)
        self.audio_levels = new_levels

    def make_sidebar(self):
        self.sidebar_buttons = []
        cats = ['ESSENTIALS', 'STYLES', 'COMPLEX', 'LOADING', 'SETTINGS']
        for i, cat in enumerate(cats):
            btn = Button(self, 100, 100 + i*70, 160, 50, cat, variant='ui', command=lambda c=cat: self.set_category(c))
            btn.color = (40, 50, 70)
            self.sidebar_buttons.append(btn)

    def set_category(self, category):
        self.state = category
        self.showcase_elements = []
        self.active_element = None
        self.current_code_snippet = ""
        self.search_text = ""
        self.search_active = False
        self.active_input = None

        self.scroll_y = 0.0
        self.scroll_target = 0.0
        
        cx = (self.W - 260 - 400) // 2 + 260 # Center between sidebar and code panel
        self.search_bar.x = cx
        
        if category == 'ESSENTIALS':
            self.showcase_elements.append(Button(self, cx, 0, 300, 50, "STANDARD UI", variant='header'))
            
            self.showcase_elements.append(Button(self, cx, 0, 200, 50, "PRIMARY", variant='primary', command=lambda: self.show_code('primary')))
            self.showcase_elements.append(Button(self, cx, 0, 200, 50, "SECONDARY", variant='secondary', command=lambda: self.show_code('secondary')))
            self.showcase_elements.append(Button(self, cx, 0, 200, 50, "DANGER", variant='danger', command=lambda: self.show_code('danger')))
            
            self.showcase_elements.append(Button(self, cx, 0, 300, 50, "GHOST / LINK", variant='header'))
            self.showcase_elements.append(Button(self, cx, 0, 180, 50, "TEXT LINK", variant='link', command=lambda: self.show_code('link')))

            self.showcase_elements.append(Button(self, cx, 0, 300, 50, "ICONS & FAB", variant='header'))
            self.showcase_elements.append(Button(self, cx, 0, 60, 60, "+", variant='fab', command=lambda: self.show_code('fab')))
            self.showcase_elements.append(Button(self, cx, 0, 60, 60, "f", variant='social', command=lambda: self.show_code('social')))
            self.showcase_elements.append(Button(self, cx, 0, 60, 60, "", variant='menu', command=lambda: self.show_code('menu')))

        elif category == 'STYLES':
            groups = [
                ("MODERN UI", ['neumorphic', 'glass', 'outline', 'soft', 'liquid', 'toggle', 'shiny', 'ghost', 'gradient']),
                ("RETRO & TECH", ['retro', 'cyber', 'pixel', 'glitch', 'holographic']),
                ("JUICY EFFECTS", ['bubble', 'candy', 'ripple', 'firefly', 'morph', 'jelly', 'shatter']),
            ]
            for title, variants in groups:
                self.showcase_elements.append(Button(self, cx, 0, 300, 50, title, variant='header'))
                for v in variants:
                    if v == 'toggle':
                        btn = Button(self, cx, 0, 100, 50, "", variant=v, command=lambda v=v: self.show_code(v))
                    elif v == 'link':
                        btn = Button(self, cx, 0, 180, 50, v.upper(), variant=v, command=lambda v=v: self.show_code(v))
                    else:
                        btn = Button(self, cx, 0, 280, 80, v.upper(), variant=v, command=lambda v=v: self.show_code(v))
                    self.showcase_elements.append(btn)
        
        elif category == 'COMPLEX':
            self.showcase_elements.append(Button(self, cx, 0, 300, 50, "INTERACTIVE", variant='header'))
            self.showcase_elements.append(Button(self, cx, 0, 240, 60, "DOWNLOAD", variant='download', command=lambda: self.show_code('download')))
            self.showcase_elements.append(Button(self, cx, 0, 240, 50, "STATUS CHECK", variant='status', command=lambda: self.show_code('status')))
            self.showcase_elements.append(Button(self, cx, 0, 240, 60, "HOLD ME", variant='hold', command=lambda: self.show_code('hold')))
            self.showcase_elements.append(Button(self, cx, 0, 280, 100, "MUSIC PLAYER", variant='music', command=lambda: self.show_code('music')))
            self.showcase_elements.append(Button(self, cx, 0, 240, 50, "SLIDER", variant='slider', command=lambda: self.show_code('slider')))

        elif category == 'LOADING':
            variants = ['load_spinner', 'load_bar', 'load_dots', 'load_pulse']
            for i, v in enumerate(variants):
                btn = Button(self, cx, 0, 280, 100, "", variant=v, command=lambda v=v: self.show_code(v))
                self.showcase_elements.append(btn)
        
        elif category == 'SETTINGS':
            self.showcase_elements.append(Button(self, cx, 0, 300, 50, "AUDIO INPUT DEVICE", variant='header'))
            
            # Auto-selection button
            auto_btn_text = "Auto (Stereo Mix/Loopback)"
            auto_btn = Button(self, cx, 0, 280, 50, auto_btn_text, variant='secondary', command=lambda: self.select_audio_device(-1))
            if self.selected_audio_device_index == -1: auto_btn.variant = 'primary' # Highlight active
            self.showcase_elements.append(auto_btn)

            # Device list
            if not self.audio_devices:
                self.showcase_elements.append(Button(self, cx, 0, 280, 50, "No input devices found", variant='header'))
            else:
                for i, device in enumerate(self.audio_devices):
                    if device['max_input_channels'] > 0:
                        # Truncate long device names
                        device_name = f"{i}: {device['name']}"
                        if len(device_name) > 35: device_name = device_name[:32] + "..."
                        
                        btn = Button(self, cx, 0, 280, 50, device_name, variant='secondary', command=lambda i=i: self.select_audio_device(i))
                        if i == self.selected_audio_device_index:
                            btn.variant = 'primary' # Highlight active selection
                        self.showcase_elements.append(btn)
            
        else:
            self.current_code_snippet = "# Coming soon..."

    def show_code(self, variant):
        # Example code snippets
        self.current_code_snippet = SNIPPETS.get(variant, SNIPPETS['default'])
        self.code_scroll_y = 0.0
        self.code_scroll_target = 0.0

    def copy_code(self):
        if PYPERCLIP_AVAILABLE and self.current_code_snippet:
            pyperclip.copy(self.current_code_snippet)
            # Optional: Add visual feedback
            self.flash_screen((100, 255, 100))

    def draw_code_snippet(self, x_pos, alpha):
        if not self.current_code_snippet:
            return
            
        # Clip to code area to handle scrolling
        code_rect = pygame.Rect(x_pos, 100, 400, self.H - 100)
        old_clip = self.canvas.get_clip()
        self.canvas.set_clip(code_rect)

        start_y = 100 - self.code_scroll_y
        line_height = 22
        
        try:
            # Use a generic monospace font for better portability
            code_font = pygame.font.SysFont('monospace', 14)
        except:
            code_font = self.font_small

        lines = self.current_code_snippet.split('\n')
        
        # Calculate content height for scrolling limits
        total_h = len(lines) * line_height + 40
        max_scroll = max(0, total_h - code_rect.height)
        if self.code_scroll_target > max_scroll: self.code_scroll_target = max_scroll

        for i, line in enumerate(lines):
            y_pos = start_y + i * line_height
            
            # Optimization: Skip off-screen lines
            if y_pos < 100 - line_height or y_pos > self.H:
                continue

            # Line numbers
            line_num = str(i + 1)
            num_surf = code_font.render(line_num, True, (60, 70, 80))
            if alpha < 255: num_surf.set_alpha(alpha)
            self.canvas.blit(num_surf, (x_pos + 10, y_pos))

            # Simple syntax highlighting
            text_color = (210, 220, 230) # Default
            if line.strip().startswith('#'):
                text_color = (100, 160, 120) # Comment
            elif line.strip().startswith(('def ', 'class ')):
                text_color = SECOND # Keyword
            elif 'import ' in line or 'from ' in line:
                text_color = TERTIARY # Import
            elif line.strip().startswith(('return', 'if ', 'else:', 'for ')):
                text_color = (200, 150, 100) # Control flow

            try:
                txt_surf = code_font.render(line, True, text_color)
                if alpha < 255:
                    txt_surf.set_alpha(alpha)
                self.canvas.blit(txt_surf, (x_pos + 45, y_pos))
            except pygame.error:
                pass

        # Restore clip
        self.canvas.set_clip(old_clip)
        
        # Scrollbar
        if max_scroll > 0:
            sb_h = max(30, (code_rect.height / total_h) * code_rect.height)
            sb_y = 100 + (self.code_scroll_y / max_scroll) * (code_rect.height - sb_h - 10)
            pygame.draw.rect(self.canvas, (60, 70, 80), (x_pos + 390, sb_y, 4, sb_h), border_radius=2)

    def flash_screen(self, color):
        self.flash = 12

    def select_audio_device(self, index):
        if self.selected_audio_device_index == index:
            return

        self.selected_audio_device_index = index
        
        # Stop existing stream if it's running
        if self.audio_stream:
            self.audio_stream.stop()
            self.audio_stream.close()
            self.audio_stream = None
        
        # Restart audio capture with new device
        self.start_audio_capture()
        
        # Provide feedback and refresh the settings view to show the new selection
        self.flash_screen((100, 100, 255))
        self.set_category('SETTINGS') # This will rebuild the button list with the correct one highlighted
        
        if index == -1:
            print("Audio device set to auto-detect.")
        elif self.audio_devices:
            print(f"Audio device set to index {index}: {self.audio_devices[index]['name']}")

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS)
            self.handle_events()
            self.update()
            self.draw()
            pygame.display.flip()
        
        if self.audio_stream:
            self.audio_stream.stop()
            self.audio_stream.close()
        
        pygame.quit()

    def trigger_button_effect(self, btn):
        # Update code view
        self.show_code(btn.variant)
        
        if btn.variant.startswith('custom_') or btn.variant == 'custom_preview':
            self._effect_custom(btn, 1.0)
            return
            
        if btn.variant == 'download' and btn.download_state == 'idle':
            btn.download_state = 'downloading'
            btn.download_progress = 0.0
            btn.text = "LOADING..."

        # --- Call variant-specific handler ---
        handler = self.effect_handlers.get(btn.variant)
        if handler:
            handler(btn, 1.0)

    # --- Effect Handlers ---
    def _effect_bubble(self, btn, mult):
        for i in range(int(18 * mult)):
            vx = (random.random()*2-1)*2; vy = -random.random()*3-1 - 1
            self.particles.append(Particle(btn.x+random.uniform(-40,40), btn.y+random.uniform(-20,20), vx, vy, 60, random.uniform(6,12), (200,250,245), gravity=-0.05))
    
    def _effect_toggle(self, btn, mult):
        # Small poof of particles
        side = 1 if btn.toggled_on else -1
        for i in range(int(8 * mult)):
            vx = side * random.uniform(1, 3)
            vy = random.uniform(-2, 2)
            x_start = btn.x + side * btn.w/2
            self.particles.append(Particle(x_start, btn.y, vx, vy, 20, random.uniform(1, 4), (200,200,220), 'pixel', gravity=0.05))

    def _effect_morph(self, btn, mult):
        # Particles burst from corners
        w, h = btn.w + 60, btn.h
        for i in range(int(20 * mult)):
            # Top-left, top-right, bottom-left, bottom-right
            px = btn.x + (w/2 * random.choice([-1, 1]))
            py = btn.y + (h/2 * random.choice([-1, 1]))
            
            vx = (px - btn.x) * 0.1 * random.uniform(0.5, 1.2)
            vy = (py - btn.y) * 0.1 * random.uniform(0.5, 1.2)
            
            self.particles.append(Particle(px, py, vx, vy, 40, random.uniform(2, 6), btn.color, 'circle', gravity=0))
    
    def _effect_liquid(self, btn, mult):
        for i in range(int(25 * mult)):
            vx = random.uniform(-2, 2)
            vy = random.uniform(-2, 2)
            start_y = btn.y + random.uniform(-btn.h/4, btn.h/4)
            p = Particle(btn.x, start_y, vx, vy, 
                         random.randint(40, 70), # life
                         random.uniform(4, 10), # size
                         (200, 230, 255), 'circle', gravity=0.25)
            self.particles.append(p)

    def _effect_shiny(self, btn, mult):
        for i in range(int(25 * mult)):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 6)
            vx = math.cos(angle) * speed; vy = math.sin(angle) * speed
            self.particles.append(Particle(btn.x, btn.y, vx, vy, random.randint(30, 60), random.uniform(1, 4), (220,220,255), 'sparkle', gravity=0.05))

    def _effect_holographic(self, btn, mult):
        self.glitch_frames = 4
        for i in range(int(15 * mult)):
            hue = (pygame.time.get_ticks() * 0.1 + random.randint(0, 50)) % 360
            c = pygame.Color(0); c.hsva = (hue, 80, 100, 100)
            self.particles.append(Particle(btn.x + random.uniform(-btn.w/2, btn.w/2), btn.y + random.uniform(-btn.h/2, btn.h/2), 
                                 random.uniform(-4,4), random.uniform(-4,4), random.randint(20, 40), random.randint(4, 8), c, 'pixel'))

    def _effect_jelly(self, btn, mult):
        for i in range(int(15 * mult)):
            vx = (random.random()*2-1)*3; vy = (random.random()*2-1)*3 - 1
            color = (*btn.color[:3], 150)
            self.particles.append(Particle(btn.x+random.uniform(-30,30), btn.y+random.uniform(-30,30), vx, vy, 50, random.uniform(8,15), color, 'circle', gravity=0.02))
    
    def _effect_gradient(self, btn, mult):
        c1 = btn.color
        c2 = tuple(min(255, c + 40) for c in btn.color[:3])
        for i in range(int(20 * mult)):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 7)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            color = c1 if random.random() > 0.5 else c2
            self.particles.append(Particle(btn.x, btn.y, vx, vy, random.randint(30, 50), random.uniform(2, 5), color, 'pixel'))

    def _effect_link(self, btn, mult):
        pass
    
    def _effect_music(self, btn, mult):
        btn.music_playing = not btn.music_playing
        if btn.music_playing:
            # Spawn music notes
            for i in range(5):
                note = random.choice(["♪", "♫", "♬"])
                self.particles.append(TextParticle(btn.x + random.uniform(-40, 40), btn.y, note, (255, 100, 150), 60))

    def _effect_shatter(self, btn, mult):
        btn.shatter_cooldown = 120 # 2 seconds
        
        num_w, num_h = 10, 6
        part_w, part_h = btn.w / num_w, btn.h / num_h
        
        for i in range(num_w):
            for j in range(num_h):
                px = (btn.x - btn.w/2) + (i + 0.5) * part_w
                py = (btn.y - btn.h/2) + (j + 0.5) * part_h
                
                vx = (px - btn.x) * 0.05 + random.uniform(-1, 1)
                vy = (py - btn.y) * 0.05 + random.uniform(-4, 2)
                self.particles.append(Particle(px, py, vx, vy, random.randint(80, 120), part_w * random.uniform(0.8, 1.2), btn.color, 'triangle', gravity=0.2))

    def _effect_candy(self, btn, mult):
        # This effect is more complex, so the snippet is simplified.
        palette = self.candy_palettes[self.current_candy_palette]
        btn.text_cycle_index = (btn.text_cycle_index + 1) % len(palette)
        btn.color = palette[btn.text_cycle_index]

        # If a full cycle is complete, switch to the next palette
        if btn.text_cycle_index == 0:
            palettes = list(self.candy_palettes.keys())
            current_idx = palettes.index(self.current_candy_palette)
            self.current_candy_palette = palettes[(current_idx + 1) % len(palettes)]

        for i in range(int(20 * mult)):
            self.particles.append(Particle(btn.x, btn.y, random.uniform(-8,8), random.uniform(-8,-2), 50, random.uniform(5,10), btn.color, 'confetti'))

    def _effect_ripple(self, btn, mult):
        self.particles.append(Particle(btn.x, btn.y, 0,0,60,6,(120,200,255),'ripple', gravity=0))

    def _effect_pixel(self, btn, mult):
        for i in range(int(28 * mult)):
            self.particles.append(Particle(btn.x+random.uniform(-40,40), btn.y+random.uniform(-20,20), random.randint(-8,8), random.randint(-8,8), random.randint(18,40), random.randint(2,6), (random.randint(80,255), random.randint(60,200), random.randint(30,160)), 'pixel'))

    def _effect_firefly(self, btn, mult):
        for i in range(int(18 * mult)): self.particles.append(Particle(btn.x+random.uniform(-40,40), btn.y+random.uniform(-20,20), random.uniform(-1,1), random.uniform(-1,1), random.randint(40,80), random.uniform(2,5), (200,255,190), gravity=-0.02))

    def _effect_glitch(self, btn, mult):
        self.glitch_frames = 6
        for i in range(int(8 * mult)): self.particles.append(Particle(btn.x, btn.y, random.uniform(-10,10), random.uniform(-10,10), 20, 8, random.choice([(255,0,0),(0,255,255),(255,255,255)]), 'pixel'))

    def _effect_intro(self, btn, mult):
        # Replaced by intro_sequence logic in update
        pass

    def _effect_custom(self, btn, mult):
        cfg = btn.custom_config
        if not cfg: return

        # New particle customization
        particle_kinds = ['circle', 'pixel', 'confetti', 'sparkle']
        kind_index = int(cfg.get('particle_kind', 0))
        kind = particle_kinds[min(len(particle_kinds)-1, kind_index)]
        
        count = int(cfg.get('particle_count', 15))
        life = int(cfg.get('particle_life', 40))
        size = cfg.get('particle_size', 6)
        speed = cfg.get('particle_speed', 5)

        if count > 0:
            for i in range(int(count * mult)):
                angle = random.uniform(0, 2 * math.pi)
                vx = math.cos(angle) * random.uniform(0.5, 1) * speed
                vy = math.sin(angle) * random.uniform(0.5, 1) * speed
                self.particles.append(Particle(btn.x, btn.y, vx, vy, life, size, btn.color, kind))


    def handle_events(self):
        self.mouse_pos = pygame.mouse.get_pos()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    self.running = False
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button == 1:
                    self.on_pointer_down(self.mouse_pos[0], self.mouse_pos[1])
            elif ev.type == pygame.MOUSEBUTTONUP:
                if ev.button == 1:
                    self.on_pointer_up(self.mouse_pos[0], self.mouse_pos[1])
                    self.drag_start = None
            elif ev.type == pygame.MOUSEWHEEL:
                if self.search_active:
                    # Don't scroll page while typing in search
                    pass
                elif self.mouse_pos[0] > self.W - 400:
                    self.code_scroll_target -= ev.y * 40
                    self.code_scroll_target = max(0, self.code_scroll_target)
                else:
                    self.scroll_vel -= ev.y * 15
            elif ev.type == pygame.KEYDOWN and self.search_active:
                if ev.key == pygame.K_RETURN or ev.key == pygame.K_KP_ENTER:
                    self.search_active = False
                    self.active_input = None
                elif ev.key == pygame.K_BACKSPACE:
                    self.search_text = self.search_text[:-1]
                else:
                    self.search_text += ev.unicode

    def on_pointer_down(self, mx, my):
        current_buttons = self.get_current_buttons()
        is_on_button = False
        clicked_search_bar = False

        for btn in current_buttons:
            if btn.contains(mx, my):
                is_on_button = True
                if btn is self.search_bar: # Direct object comparison
                    clicked_search_bar = True
                btn.on_down(mx, my)

        self.search_active = clicked_search_bar
        self.active_input = self.search_bar if clicked_search_bar else None

        if not is_on_button and self.transition_alpha == 0:
            # Create a ripple effect for clicks on empty space
            self.particles.append(Particle(mx, my, 0, 0, 40, 5, (200,220,255), 'ripple', gravity=0))
            if self.ui_click_tone:
                self.ui_click_tone.play()

    def on_pointer_up(self, mx, my):
        current_buttons = self.get_current_buttons()
        for btn in current_buttons:
            btn.on_up()

    def get_current_buttons(self):
        # Always show sidebar
        if self.state == 'INTRO':
            return [self.intro_btn]
            
        btns = self.sidebar_buttons[:] + [self.copy_code_button, self.search_bar]
        btns.extend(self.visible_showcase_elements)
        return btns

    def update(self):
        # Handle screen transitions
        if self.next_state is not None: # Fading out
            self.transition_alpha = min(255, self.transition_alpha + 15)
            if self.transition_alpha >= 255:                
                new_state = self.next_state
                self.state = new_state
                self.next_state = None
                self.transition_fade_in = True
                
                if not self.sidebar_initialized and new_state != 'INTRO':
                     self.make_sidebar()
                     self.sidebar_initialized = True
                if new_state in ['BUTTONS', 'LOADING', 'TRANSITIONS', 'PARTICLES']:
                    self.set_category(new_state)
        elif self.transition_fade_in: # Fading in
            self.transition_alpha = max(0, self.transition_alpha - 15)
            if self.transition_alpha <= 0:
                self.transition_fade_in = False

        # Code scroll logic
        self.code_scroll_y += (self.code_scroll_target - self.code_scroll_y) * 0.1

        # Intro Sequence Logic
        if self.intro_sequence:
            self.intro_timer += 1
            # Wobble and expand
            self.intro_btn.liquid_distortion = self.intro_timer
            
            if self.intro_timer < 30:
                # Anticipation (shrink slightly)
                self.intro_btn.target_scale = 0.8
            else:
                # Expansion
                self.intro_btn.target_scale = 1.0 + (self.intro_timer - 30) ** 3 * 0.001
            
            if self.intro_btn.scale > 25: # Covered screen
                self.intro_sequence = False
                self.intro_btn.scale = 1.0

                # Start the solidification process
                self.intro_solidify = True
                self.solidify_progress = 0.0
                
                # Prepare the UI for drawing
                self.state = 'BUTTONS'
                if not self.sidebar_initialized:
                     self.make_sidebar()
                     self.set_category('STYLES')
                     self.sidebar_initialized = True
                
                # Make all buttons invisible initially. They will be animated in.
                for elem in self.sidebar_buttons + self.showcase_elements + [self.copy_code_button, self.search_bar]:
                    if elem: elem.visible = False

        # Solidification sequence
        if self.intro_solidify:
            self.solidify_progress += 0.02 # Controls speed of solidification
            if self.solidify_progress >= 1.0:
                self.solidify_progress = 1.0
                self.intro_solidify = False
                
                # Make UI buttons visible immediately
                for btn in self.sidebar_buttons: btn.visible = True
                self.copy_code_button.visible = True
                self.search_bar.visible = True
                # Animate in the showcase buttons
                for i, elem in enumerate(self.showcase_elements):
                    elem.visible = True
                    elem.anim_state = 'entering'
                    elem.anim_progress = -i * 0.1 # Staggered start

        # Update UI accent color
        if self.rainbow_cycle_timer > 0:
            self.rainbow_cycle_timer -= 1
            hue = (pygame.time.get_ticks() * 0.2) % 360
            c = pygame.Color(0); c.hsva = (hue, 100, 100, 100)
            self.accent_color = (c.r, c.g, c.b)
        else: # Lerp back to default
            r1,g1,b1 = self.accent_color
            r2,g2,b2 = self.default_accent
            if abs(r1-r2) > 1 or abs(g1-g2) > 1 or abs(b1-b2) > 1:
                self.accent_color = (r1 + (r2 - r1) * 0.1, g1 + (g2 - g1) * 0.1, b1 + (b2 - b1) * 0.1)
            else:
                self.accent_color = self.default_accent

        # Scroll logic
        # Filter showcase elements based on search
        if self.search_text:
            search_term = self.search_text.lower()
            self.visible_showcase_elements = []
            for btn in self.showcase_elements:
                # Always show headers and the search bar itself
                if btn.variant in ['header', 'search_bar'] or \
                   search_term in btn.variant.lower() or \
                   search_term in btn.text.lower():
                    self.visible_showcase_elements.append(btn)
        else:
            self.visible_showcase_elements = self.showcase_elements

        if self.visible_showcase_elements:
            # Inertial scroll physics
            self.scroll_target += self.scroll_vel
            self.scroll_vel *= 0.85 # Damping
            if abs(self.scroll_vel) < 0.1: self.scroll_vel = 0

            # Calculate content height for clamping
            content_h = sum(btn.h + 20 for btn in self.visible_showcase_elements) - 20
            max_scroll = max(0, content_h - (self.H - 200)) # Visible area H - 100px top/bottom padding
            self.scroll_target = max(0, min(self.scroll_target, max_scroll))

            # Smoothly move scroll_y towards scroll_target
            self.scroll_y += (self.scroll_target - self.scroll_y) * 0.1

            # Dynamic Layout Calculation (Vertical Stack)
            current_y = 100 - self.scroll_y
            for btn in self.visible_showcase_elements:
                btn.y = current_y + btn.h / 2
                current_y += btn.h + 20 # Advance Y-cursor by button height + padding

        current_buttons = self.get_current_buttons()
        for btn in current_buttons:
            # Don't check for hover if transitioning
            if self.transition_alpha == 0:
                if btn.contains(self.mouse_pos[0], self.mouse_pos[1]):
                    btn.on_hover()
                else:
                    btn.on_exit()
            btn.update(self.mouse_pos[0], self.mouse_pos[1])
            
                
        # Update cursor trail
        self.particles.append(Particle(self.mouse_pos[0], self.mouse_pos[1], 0, 0, 10, 3, self.accent_color, gravity=0))

        # update and filter particles
        for p in self.particles:
            p.update(self)
        self.particles = [p for p in self.particles if p.life > 0]

        if self.shake > 0:
            self.shake *= 0.88
            if self.shake < 0.5: self.shake = 0

        if self.flash > 0:
                       self.flash -= 1
        if self.glitch_frames > 0:
            self.glitch_frames -= 1
        
    def draw(self):
        # Use pre-rendered background on persistent canvas
        self.canvas.blit(self.bg_surf, (0, 0))

        # Draw parallax stars
        for star in self.stars:
            pos = star.update(self.mouse_pos)
            pygame.draw.rect(self.canvas, star.color, (pos[0], pos[1], star.size, star.size))

        current_buttons = self.get_current_buttons()

        # --- Panel and Background Drawing ---
        if self.intro_solidify:
            # 1. Draw solidifying background
            prog = self.solidify_progress**2 # Ease-in
            liquid_color = (200, 230, 255)
            solid_color = tuple(int(l * (1 - prog) + b * prog) for l, b in zip(liquid_color, BG))
            self.canvas.fill(solid_color)

            # 2. Draw UI panels fading in
            panel_alpha = int(255 * prog)
            
            # Sidebar
            sidebar_surf = pygame.Surface((260, self.H), pygame.SRCALPHA)
            sidebar_surf.fill((*DARK_PANEL, panel_alpha))
            pygame.draw.line(sidebar_surf, (*(40, 50, 70), panel_alpha), (259, 0), (259, self.H), 1)
            self.canvas.blit(sidebar_surf, (0, 0))

            # Code Panel
            code_x = self.W - 400
            code_panel_surf = pygame.Surface((400, self.H), pygame.SRCALPHA)
            code_panel_surf.fill((*(15, 18, 25), panel_alpha))
            pygame.draw.line(code_panel_surf, (*(40, 50, 70), panel_alpha), (0, 0), (0, self.H), 1)
            self.canvas.blit(code_panel_surf, (code_x, 0))
            
            # Code Snippet Text
            self.draw_code_snippet(code_x, panel_alpha)

        elif self.state == 'INTRO':
            # Intro Title with parallax
            mx, my = self.mouse_pos
            parallax_x = (mx - self.W/2) * 0.02
            parallax_y = (my - self.H/2) * 0.02

            t = self.font_large.render("SATISFYING UI", True, TEXT)
            self.canvas.blit(t, t.get_rect(center=(self.W//2 + parallax_x, self.H//2 - 120 + parallax_y)))
            t2 = self.font_small.render("CLICK TO START", True, (100, 120, 150))
            self.canvas.blit(t2, t2.get_rect(center=(self.W//2 + parallax_x*0.5, self.H//2 + 100 + parallax_y*0.5)))
        
        elif self.state != 'INTRO': # Normal UI state with sliding transitions
            t_norm = self.transition_alpha / 255.0
            ease = (1 - (1 - t_norm)**3) if self.transition_fade_in else t_norm**3
            
            sidebar_x = -260 * ease
            code_x_offset = 400 * ease
            
            pygame.draw.rect(self.canvas, DARK_PANEL, (sidebar_x, 0, 260, self.H))
            pygame.draw.line(self.canvas, (40, 50, 70), (sidebar_x + 260, 0), (sidebar_x + 260, self.H), 1)
            
            code_x = self.W - 400 + code_x_offset
            pygame.draw.rect(self.canvas, (15, 18, 25), (int(code_x), 0, 400, self.H))
            pygame.draw.line(self.canvas, (40, 50, 70), (int(code_x), 0), (int(code_x), self.H), 1)
            
            self.draw_code_snippet(int(code_x), 255)

        # Draw all buttons for the current state
        # Sort by size to ensure smaller buttons (nav) draw on top of larger ones if they overlap
        # This is a simple hack for z-ordering
        for btn in sorted(current_buttons, key=lambda b: b.w * b.h, reverse=False):
            # Only draw if visible on screen (plus some margin)
            if -100 < btn.y < self.H + 100:
                btn.draw(self.canvas)


        # draw particles on top
        for p in self.particles:
            p.draw(self.canvas)

        # Draw blinking cursor for search bar
        if self.search_active and self.search_bar.visible:
            if int(time.time() * 2) % 2 == 0: # Blink
                font = self.font_small
                text_surf = font.render(self.search_text, True, TEXT)
                # Calculate cursor position
                text_width = text_surf.get_width()
                start_x = self.search_bar.x - self.search_bar.w / 2 + 20 # same as text start
                cursor_x = start_x + text_width + 2
                cursor_y = self.search_bar.y
                pygame.draw.line(self.canvas, ACCENT, (cursor_x, cursor_y - 8), (cursor_x, cursor_y + 8), 2)

        # flash
        if self.flash > 0:
            self.flash_surf.fill((255,255,255, min(180, int(self.flash*12))))
            self.canvas.blit(self.flash_surf, (0,0), special_flags=pygame.BLEND_RGBA_ADD)

        # Glitch effect
        if self.glitch_frames > 0:
            for _ in range(10):
                h = random.randint(10, 50)
                y = random.randint(0, self.H - h)
                off = random.randint(-20, 20)
                chunk = self.canvas.subsurface(0, y, self.W, h).copy()
                self.canvas.blit(chunk, (off, y))

        # apply shake
        if self.shake:
            ox = int((random.random()*2-1)*self.shake)
            oy = int((random.random()*2-1)*self.shake)
            self.screen.fill(BG) # Clear edges if shaking
        else:
            ox = oy = 0

        self.screen.blit(self.canvas, (ox, oy))

        # Draw screen transition overlay
        if self.transition_alpha > 0 and not self.intro_solidify:
            transition_surf = pygame.Surface((self.W, self.H))
            transition_color = (0,0,0)
            # This is now only for category transitions, so it's always black
            transition_surf.fill(transition_color)
            transition_surf.set_alpha(self.transition_alpha)
            self.screen.blit(transition_surf, (0,0))


if __name__ == '__main__':

    app = App()
    try:
        app.run()
    except KeyboardInterrupt:
        pygame.quit()
