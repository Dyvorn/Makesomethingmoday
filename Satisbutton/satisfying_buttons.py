import math
import random
import sys
import struct
import time
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
except Exception as e:
    print("Missing dependency: pygame is required. Install with: pip install pygame")
    raise

# --- Config ---
FPS = 60
BG = (10, 16, 28)
TEXT = (230, 240, 255)
ACCENT = (110, 231, 183)
SECOND = (96, 165, 250)
TERTIARY = (236, 72, 153)
NEUMORPHIC_BASE = (224, 229, 236)
DARK_PANEL = (20, 25, 35)

# --- Sound helper (generate simple tone) ---
SAMPLE_RATE = 44100
DEFAULT_VOL = 0.12

def make_tone(freq=440.0, duration=0.18, volume=0.12):
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
        self.angle = random.random() * 360

    def update(self):
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
            s = pygame.Surface((r, r), pygame.SRCALPHA); s.fill(col)
            surf.blit(s, (int(self.x - r/2), int(self.y - r/2)))
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
        else:
            r = int(current_size)
            if r > 0:
                pygame.gfxdraw.filled_circle(surf, int(self.x), int(self.y), r, col)

class TextParticle(Particle):
    def __init__(self, x, y, text, color, life):
        super().__init__(x, y, 0, -1.5, life, 0, color, kind='text', gravity=0.05)
        self.font = pygame.font.SysFont('Segoe UI', 18, bold=True)
        self.text = text

    def draw(self, surf):
        if self.life <= 0: return
        alpha = max(0, min(255, int(255 * (self.life / self.max_life)**2)))
        
        text_surf = self.font.render(self.text, True, self.color)
        text_surf.set_alpha(alpha)
        
        surf.blit(text_surf, text_surf.get_rect(center=(self.x, self.y)))

class Slider:
    def __init__(self, x, y, w, min_val, max_val, value, label):
        self.rect = pygame.Rect(x, y, w, 6)
        self.knob_rect = pygame.Rect(x, y-7, 14, 20)
        self.min_val = min_val
        self.max_val = max_val
        self.value = value
        self.label = label
        self.dragging = False
        self.update_knob()

    def update_knob(self):
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        self.knob_rect.centerx = self.rect.x + self.rect.w * ratio

    def update(self, mx, my, down):
        if down:
            if self.knob_rect.collidepoint(mx, my) or self.rect.collidepoint(mx, my):
                self.dragging = True
        else:
            self.dragging = False
        
        if self.dragging:
            ratio = (mx - self.rect.x) / self.rect.w
            ratio = max(0, min(1, ratio))
            self.value = self.min_val + ratio * (self.max_val - self.min_val)
            self.update_knob()
            return True
        return False

    def draw(self, surf, font):
        lbl = font.render(f"{self.label}: {self.value:.2f}", True, (200, 200, 200))
        surf.blit(lbl, (self.rect.x, self.rect.y - 25))
        pygame.draw.rect(surf, (60, 60, 70), self.rect, border_radius=3)
        
        is_hovered = self.knob_rect.collidepoint(pygame.mouse.get_pos())
        active_color = ACCENT if self.dragging or is_hovered else (180, 180, 200)
        pygame.draw.rect(surf, active_color, (self.rect.x, self.rect.y, self.knob_rect.centerx - self.rect.x, 6), border_radius=3)
        knob_color = (255, 255, 255) if self.dragging or is_hovered else (220, 220, 240)
        pygame.draw.rect(surf, knob_color, self.knob_rect, border_radius=5)

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
        
        # Set specific colors for variants
        if self.variant in ['bubble', 'candy', 'ripple', 'pixel', 'firefly', 'glitch']:
             self.color = random.choice([ACCENT, SECOND, TERTIARY, (245,158,11), (16,185,129)])
             self.current_color = list(self.color)
        if self.variant == 'retro': self.color = (192, 192, 192)
        if self.variant == 'cyber': self.color = (255, 230, 0)
        if self.variant == 'soft': self.color = (255, 180, 190)
        if self.variant == 'intro_orb': self.color = (255, 255, 255)
        self.scale = 1.0
        self.orb_angle = 0.0
        self.orb_velocity = 2.0
        self.val_pull = 0.0
        self.time_offset = random.random() * 100

    def contains(self, px, py):
        if not self.visible: return False
        return (self.x - self.w/2 <= px <= self.x + self.w/2) and (self.y - self.h/2 <= py <= self.y + self.h/2)

    def update(self, mx, my):
        # Spring physics for scale
        stiffness = 0.22
        damping = 0.70
        
        # Proximity / Magnetic Effect
        dist = math.hypot(mx - self.x, my - self.y)
        # Increased range and sensitivity for better feel
        range_limit = 200
        pull = max(0.0, (range_limit - dist) / range_limit)
        pull = pull * pull # Quadratic ease-in for smoother onset
        self.val_pull = pull

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
        if not self.hover and not self.pressed:
             self.target_scale = 1.0 + pull * 0.15

        # Intro Orb Physics (Smooth Rotation)
        if self.variant == 'intro_orb':
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

        # Animation state machine
        if self.anim_state in ['entering', 'exiting']:
            self.anim_progress += 0.05
            if self.anim_progress >= 1.0:
                self.anim_progress = 1.0
                if self.anim_state == 'exiting': self.visible = False
                self.anim_state = 'active'

        # Intro Orb Suction Effect
        if self.variant == 'intro_orb' and self.hover:
             if random.random() < 0.6:
                 angle = random.uniform(0, 6.28)
                 dist = 110 # Start further out
                 px = self.x + math.cos(angle) * dist
                 py = self.y + math.sin(angle) * dist
                 
                 # Spiral velocity
                 speed = random.uniform(5, 9)
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
        if not self.visible: return
        
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
            eased_prog = 1 - (1 - self.anim_progress)**3
            cy = self.vis_y - self.app.H * (1 - eased_prog)
        elif self.anim_state == 'exiting':
            eased_prog = self.anim_progress**3
            cy = self.vis_y + self.app.H * eased_prog

        if self.variant == 'header':
            font = self.app.font_small
            txt = font.render(self.text, True, (100, 110, 130))
            surf.blit(txt, txt.get_rect(center=(cx, cy + 10)))
            pygame.draw.line(surf, (40, 50, 60), (cx - 120, cy + 25), (cx + 120, cy + 25), 1)
            return

        # --- SHAPE RENDERING ---
        if self.variant in ['bubble', 'candy', 'coin', 'blackhole', 'firefly', 'slime', 'grow']:
            # CIRCULAR SHAPE
            r = int(min(w, h) / 2.2) # Slightly smaller for padding
            # Shadow
            pygame.gfxdraw.filled_circle(surf, int(cx), int(cy)+4, r, (0,0,0,60))
            
            # Body
            if self.variant == 'firefly':
                # Dark body with glowing rim
                pygame.gfxdraw.filled_circle(surf, int(cx), int(cy), r, (20, 25, 35))
                pygame.gfxdraw.aacircle(surf, int(cx), int(cy), r, (60, 70, 80))
                # Inner glow pulse
                glow_r = int(r * (0.6 + 0.1 * math.sin(time.time() * 3) + self.val_pull * 0.2))
                pygame.gfxdraw.filled_circle(surf, int(cx), int(cy), glow_r, (*self.color[:3], 100))
            elif self.variant == 'bubble':
                # Gradient-like fill
                pygame.gfxdraw.filled_circle(surf, int(cx), int(cy), r, draw_color)
                pygame.gfxdraw.filled_circle(surf, int(cx - r*0.2), int(cy - r*0.2), int(r*0.6), (255,255,255,40))
                pygame.gfxdraw.aacircle(surf, int(cx), int(cy), r, (255,255,255,100))
            else:
                pygame.gfxdraw.filled_circle(surf, int(cx), int(cy), r, draw_color)
                pygame.gfxdraw.aacircle(surf, int(cx), int(cy), r, (255,255,255,50))
            
            # Details
            if self.variant == 'coin':
                pygame.gfxdraw.aacircle(surf, int(cx), int(cy), int(r*0.8), (255,255,200))
            elif self.variant == 'candy':
                # Swirl pattern
                for i in range(0, 360, 45): # Spin faster with proximity
                    rad = math.radians(i + time.time() * 50)
                    ex, ey = cx + math.cos(rad) * r * 0.8, cy + math.sin(rad) * r * 0.8
                    pygame.draw.line(surf, (255,255,255,80), (cx, cy), (ex, ey), 3)
            # Gloss
            pygame.gfxdraw.filled_circle(surf, int(cx - r*0.3), int(cy - r*0.3), int(r*0.25), (255,255,255,80))
            
            # Text offset for circle
            rect = pygame.Rect(cx-w/2, cy-h/2, w, h)

        elif self.variant == 'pixel' or self.variant == 'glitch':
            # PIXEL ART SHAPE (Sharp Rect)
            rect = pygame.Rect(int(cx - w/2), int(cy - h/2), int(w), int(h))
            # Hard Shadow
            shadow_off = 4 + int(self.val_pull * 4)
            pygame.draw.rect(surf, (0,0,0,80), rect.move(shadow_off, shadow_off))
            # Body
            pygame.draw.rect(surf, draw_color, rect)
            # Thick Border
            pygame.draw.rect(surf, (255,255,255), rect, 3)
            pygame.draw.rect(surf, (0,0,0), rect.inflate(2,2), 2)
            if self.variant == 'glitch':
                # Random glitch bars - intensity based on proximity
                glitch_chance = 0.1 + self.val_pull * 0.5
                if random.random() < glitch_chance:
                    gx = rect.x + random.randint(0, int(w))
                    gy = rect.y + random.randint(0, int(h))
                    gr = pygame.Rect(gx, gy, random.randint(10, 40), random.randint(2, 6))
                    pygame.draw.rect(surf, random.choice([(255,50,50), (50,255,255), (20,20,20)]), gr)

        elif self.variant == 'laser':
            # NEON RECT SHAPE
            rect = pygame.Rect(int(cx - w/2), int(cy - h/2), int(w), int(h))
            # Glow
            for i in range(1, 4):
                pygame.draw.rect(surf, (*self.color[:3], 50//i), rect.inflate(i*6, i*6), 1, border_radius=4)
            pygame.draw.rect(surf, (10,10,10), rect, border_radius=4)
            pygame.draw.rect(surf, draw_color, rect, 2, border_radius=4)

        elif self.variant == 'ui':
            rect = pygame.Rect(int(cx - w/2), int(cy - h/2), int(w), int(h))
            # Clean, sharp look for UI
            shadow_color = (*self.app.accent_color[:3], 40) if self.hover else (0,0,0,60)
            shadow_offset = 2 if self.hover else 4
            pygame.draw.rect(surf, shadow_color, rect.move(0, shadow_offset), border_radius=8)
            
            pygame.draw.rect(surf, draw_color, rect, border_radius=8)
            
            if self.hover:
                pygame.draw.rect(surf, self.app.accent_color, rect, 2, border_radius=8)

        elif self.variant == 'neumorphic':
            rect = pygame.Rect(int(cx - w/2), int(cy - h/2), int(w), int(h))
            # Light source top-left
            light_color = (255, 255, 255)
            shadow_color = (163, 177, 198)
            base_color = NEUMORPHIC_BASE
            
            if self.pressed:
                # Inner shadow look
                pygame.draw.rect(surf, base_color, rect, border_radius=12)
                pygame.draw.rect(surf, shadow_color, rect, 2, border_radius=12) # Simple inset simulation
            else:
                # Outer shadow
                # Dark shadow bottom-right
                pygame.draw.rect(surf, shadow_color, rect.move(4, 4), border_radius=12)
                # Light shadow top-left
                pygame.draw.rect(surf, light_color, rect.move(-4, -4), border_radius=12)
                pygame.draw.rect(surf, base_color, rect, border_radius=12)

        elif self.variant == 'glass':
            rect = pygame.Rect(int(cx - w/2), int(cy - h/2), int(w), int(h))
            # Semi-transparent white body
            s = pygame.Surface((int(w), int(h)), pygame.SRCALPHA)
            s.fill((255, 255, 255, 30))
            surf.blit(s, rect.topleft)
            # Border
            pygame.draw.rect(surf, (255, 255, 255, 100), rect, 1, border_radius=12)
            # Shine
            pygame.draw.line(surf, (255, 255, 255, 80), (rect.left + 10, rect.top + 10), (rect.right - 10, rect.bottom - 20), 20)

        elif self.variant == 'outline':
            rect = pygame.Rect(int(cx - w/2), int(cy - h/2), int(w), int(h))
            col = ACCENT if self.hover else (150, 150, 150)
            pygame.draw.rect(surf, col, rect, 2, border_radius=8)
            if self.pressed:
                s = pygame.Surface((int(w), int(h)), pygame.SRCALPHA)
                s.fill((*col[:3], 50))
                surf.blit(s, rect.topleft)

        elif self.variant == 'retro':
            rect = pygame.Rect(int(cx - w/2), int(cy - h/2), int(w), int(h))
            base = (192, 192, 192)
            light = (255, 255, 255)
            dark = (128, 128, 128)
            black = (0, 0, 0)
            
            pygame.draw.rect(surf, base, rect)
            if not self.pressed:
                pygame.draw.line(surf, light, rect.topleft, rect.topright, 2)
                pygame.draw.line(surf, light, rect.topleft, rect.bottomleft, 2)
                pygame.draw.line(surf, dark, rect.bottomleft, rect.bottomright, 2)
                pygame.draw.line(surf, dark, rect.topright, rect.bottomright, 2)
                pygame.draw.line(surf, black, (rect.right-1, rect.top), (rect.right-1, rect.bottom), 1)
                pygame.draw.line(surf, black, (rect.left, rect.bottom-1), (rect.right, rect.bottom-1), 1)
            else:
                pygame.draw.rect(surf, dark, rect, 2)

        elif self.variant == 'cyber':
            rect = pygame.Rect(int(cx - w/2), int(cy - h/2), int(w), int(h))
            cut = 15
            pts = [
                (rect.left + cut, rect.top), (rect.right, rect.top),
                (rect.right, rect.bottom - cut), (rect.right - cut, rect.bottom),
                (rect.left, rect.bottom), (rect.left, rect.top + cut)
            ]
            col = draw_color if not self.hover else (255, 255, 150)
            pygame.draw.polygon(surf, col, pts)
            pygame.draw.polygon(surf, (0,0,0), pts, 3)
            # Tech lines
            # Scanline effect
            scan_speed = 50 + self.val_pull * 100
            scan_y = int(rect.top + (time.time() * scan_speed) % h)
            if rect.top < scan_y < rect.bottom:
                pygame.draw.line(surf, (255, 255, 255, 150), (rect.left, scan_y), (rect.right, scan_y), 1)
            pygame.draw.line(surf, (0,0,0), (rect.left + cut + 5, rect.top + 8), (rect.right - 5, rect.top + 8), 2)
            pygame.draw.line(surf, (0,0,0), (rect.left + 5, rect.bottom - 8), (rect.right - cut - 5, rect.bottom - 8), 2)

        elif self.variant == 'soft':
            rect = pygame.Rect(int(cx - w/2), int(cy - h/2), int(w), int(h))
            col = draw_color
            shadow_col = (200, 130, 140)
            if not self.pressed:
                pygame.draw.rect(surf, shadow_col, rect.move(0, 6), border_radius=20)
            pygame.draw.rect(surf, col, rect.move(0, 3 if self.pressed else 0), border_radius=20)

        elif self.variant == 'intro_orb':
            r = int(w/2)
            cx, cy = int(cx), int(cy)
            mx, my = self.app.mouse_pos
            
            # Dynamic variables based on hover/press
            rot_speed = self.orb_angle
            pulse_speed = 15 if self.hover else 2
            energy_level = 1.0 + (0.5 if self.hover else 0) + (1.0 if self.pressed else 0)
            
            # Parallax Core Offset
            core_off_x = (mx - cx) * 0.1
            core_off_y = (my - cy) * 0.1
            
            # 1. Ambient Particles (Orbiting) - Increased count and complexity
            for i in range(8): 
                orb_angle = rot_speed * 0.3 + i * (360/8)
                dist = r + 15 + 5 * math.sin(time.time() * 5 + i) * energy_level
                ox = cx + math.cos(math.radians(orb_angle)) * dist
                oy = cy + math.sin(math.radians(orb_angle)) * dist
                # Trail
                for j in range(4):
                    trail_alpha = 150 - j*35
                    tx = cx + math.cos(math.radians(orb_angle - j*5)) * dist
                    ty = cy + math.sin(math.radians(orb_angle - j*5)) * dist
                    pygame.gfxdraw.filled_circle(surf, int(tx), int(ty), max(1, 4-j), (100, 220, 255, trail_alpha))
                pygame.gfxdraw.filled_circle(surf, int(ox), int(oy), 4, (200, 255, 255))

            # Outer Glow / Pulse
            pulse = (math.sin(time.time() * pulse_speed) + 1) * 0.5 
            glow_size = int(r + 30 + 20 * pulse * energy_level)
            if self.pressed: glow_size = int(glow_size * 0.9)
            
            # Draw glow (using blit for better alpha blending with ADD)
            s = pygame.Surface((glow_size*2, glow_size*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (20, 60, 150, 50), (glow_size, glow_size), glow_size)
            pygame.draw.circle(s, (60, 120, 255, 80), (glow_size, glow_size), int(glow_size*0.7))
            if self.pressed: pygame.draw.circle(s, (200, 230, 255, 100), (glow_size, glow_size), int(glow_size*0.4))
            
            # Extra energy streaks
            if self.hover:
                pygame.draw.circle(s, (100, 200, 255, 30), (glow_size, glow_size), int(glow_size * 1.2), 2)
            surf.blit(s, (cx - glow_size, cy - glow_size), special_flags=pygame.BLEND_RGBA_ADD)
            
            # Rotating Rings
            rect_ring = pygame.Rect(cx - r - 12, cy - r - 12, r*2 + 24, r*2 + 24)
            pygame.draw.arc(surf, (100, 200, 255), rect_ring, math.radians(rot_speed), math.radians(rot_speed + 240), 3)
            
            rect_ring2 = pygame.Rect(cx - r - 6, cy - r - 6, r*2 + 12, r*2 + 12)
            pygame.draw.arc(surf, (200, 230, 255), rect_ring2, math.radians(-rot_speed*1.5), math.radians(-rot_speed*1.5 + 120), 2)
            
            # Horizontal energy streak on hover
            if self.hover:
                 streak_w = r * 4 * energy_level
                 streak_h = 2
                 streak_surf = pygame.Surface((int(streak_w), streak_h), pygame.SRCALPHA)
                 streak_surf.fill((200, 250, 255, 150))
                 surf.blit(streak_surf, (cx - streak_w/2, cy - streak_h/2))

            # Main Body
            core_x, core_y = int(cx + core_off_x), int(cy + core_off_y)
            
            # Core jitter
            if self.hover:
                core_x += random.randint(-1, 1)
                core_y += random.randint(-1, 1)

            pygame.gfxdraw.filled_circle(surf, cx, cy, r, (230, 240, 255)) # Base
            pygame.gfxdraw.filled_circle(surf, core_x, core_y, int(r*0.85), (180, 220, 255)) # Inner
            pygame.gfxdraw.aacircle(surf, cx, cy, r, (255, 255, 255)) # Rim White
            
            # Play Icon
            icon_col = (10, 20, 40)
            if self.pressed:
                pygame.gfxdraw.filled_circle(surf, core_x, core_y, r, (255, 255, 255))
                icon_col = (100, 150, 255)
            
            # Centered Play Triangle
            pts = [(core_x - 8, core_y - 14), (core_x - 8, core_y + 14), (core_x + 16, core_y)]
            pygame.draw.polygon(surf, icon_col, pts)
            
            # Shine
            pygame.gfxdraw.filled_circle(surf, int(core_x - r*0.3), int(core_y - r*0.3), int(r*0.3), (255,255,255,180))

        elif self.variant == 'load_spinner':
            rect = pygame.Rect(int(cx - w/2), int(cy - h/2), int(w), int(h))
            # Card BG
            pygame.draw.rect(surf, (30, 35, 45), rect, border_radius=12)
            if self.hover: pygame.draw.rect(surf, (50, 60, 70), rect, 2, border_radius=12)
            
            # Spinner
            angle = time.time() * 300
            radius = 20
            rect_s = pygame.Rect(cx-radius, cy-radius-10, radius*2, radius*2)
            pygame.draw.arc(surf, ACCENT, rect_s, math.radians(angle), math.radians(angle + 240), 4)
            
            # Label
            font = self.app.font_small
            txt = font.render("SPINNER", True, (150, 160, 180))
            surf.blit(txt, txt.get_rect(center=(cx, cy + 25)))
            return

        elif self.variant == 'load_bar':
            rect = pygame.Rect(int(cx - w/2), int(cy - h/2), int(w), int(h))
            pygame.draw.rect(surf, (30, 35, 45), rect, border_radius=12)
            if self.hover: pygame.draw.rect(surf, (50, 60, 70), rect, 2, border_radius=12)
            
            bar_w = 140
            bar_h = 6
            bx = cx - bar_w / 2
            by = cy - 10
            
            # Track
            pygame.draw.rect(surf, (50, 60, 70), (bx, by, bar_w, bar_h), border_radius=3)
            # Fill
            progress = (math.sin(time.time() * 2) + 1) / 2
            fill_w = bar_w * progress
            pygame.draw.rect(surf, SECOND, (bx, by, fill_w, bar_h), border_radius=3)
            
            # Label
            font = self.app.font_small
            txt = font.render("PROGRESS", True, (150, 160, 180))
            surf.blit(txt, txt.get_rect(center=(cx, cy + 25)))
            return

        elif self.variant == 'load_dots':
            rect = pygame.Rect(int(cx - w/2), int(cy - h/2), int(w), int(h))
            pygame.draw.rect(surf, (30, 35, 45), rect, border_radius=12)
            if self.hover: pygame.draw.rect(surf, (50, 60, 70), rect, 2, border_radius=12)
            
            for i in range(3):
                offset = math.sin(time.time() * 8 + i * 0.5) * 6
                dx = cx + (i - 1) * 20
                dy = cy - 10 + offset
                color = [ACCENT, SECOND, TERTIARY][i]
                pygame.draw.circle(surf, color, (int(dx), int(dy)), 6)
                
            # Label
            font = self.app.font_small
            txt = font.render("BOUNCE", True, (150, 160, 180))
            surf.blit(txt, txt.get_rect(center=(cx, cy + 25)))
            return

        elif self.variant == 'load_pulse':
            rect = pygame.Rect(int(cx - w/2), int(cy - h/2), int(w), int(h))
            pygame.draw.rect(surf, (30, 35, 45), rect, border_radius=12)
            if self.hover: pygame.draw.rect(surf, (50, 60, 70), rect, 2, border_radius=12)
            
            for i in range(2):
                t = (time.time() * 1.0 + i * 1.0) % 2.0
                alpha = max(0, 255 * (1 - t/2.0))
                radius = 5 + t * 20
                s = pygame.Surface((int(radius*2), int(radius*2)), pygame.SRCALPHA)
                pygame.draw.circle(s, (*TERTIARY[:3], int(alpha)), (int(radius), int(radius)), int(radius), 2)
                surf.blit(s, (cx - radius, cy - 10 - radius))
            
            pygame.draw.circle(surf, TERTIARY, (int(cx), int(cy-10)), 5)

            # Label
            font = self.app.font_small
            txt = font.render("PULSE", True, (150, 160, 180))
            surf.blit(txt, txt.get_rect(center=(cx, cy + 25)))
            return

        else:
            # STANDARD ROUNDED RECT (Pill/Box)
            rect = pygame.Rect(int(cx - w/2), int(cy - h/2), int(w), int(h))

            # Firefly hover glow
            if self.variant == 'firefly' and self.hover:
                pygame.gfxdraw.filled_circle(surf, int(cx), int(cy), int(w/2 * 1.3), (*self.color[:3], 40))

            # Shadow
            shadow_surf = pygame.Surface((int(w)+20, int(h)+20), pygame.SRCALPHA)
            pygame.gfxdraw.filled_ellipse(shadow_surf, int(w/2+10), int(h/2+10+4), int(w/2), int(h/2), (0,0,0,50))
            surf.blit(shadow_surf, (rect.x-10, rect.y-10 + (2 if self.pressed else 0)))
            # Body
            pygame.draw.rect(surf, draw_color, rect, border_radius=16)
            # Gloss
            pygame.draw.rect(surf, (255,255,255,20), rect.inflate(-4, -h/2).move(0, -h/4 + 2), border_radius=16)

        # text
        font = self.app.font_large if self.w > 160 else self.app.font_small
        txt_col = TEXT
        if self.variant == 'neumorphic': txt_col = (100, 100, 110)
        if self.variant in ['retro', 'cyber']: txt_col = (20, 20, 20)
        if self.variant == 'soft': txt_col = (255, 255, 255)
        if self.variant == 'intro_orb': return # No text for intro orb
        
        txt_shadow = font.render(self.text, True, (0,0,0, 50))
        surf.blit(txt_shadow, txt_shadow.get_rect(center=(self.x, self.y + 2)))

        # Glitch text offset
        tx_off = 0
        if self.variant == 'glitch' and random.random() < self.val_pull * 0.3:
            tx_off = random.randint(-2, 2)
        txt = font.render(self.text, True, txt_col)
        surf.blit(txt, txt.get_rect(center=(self.x, self.y)))

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
            self.target_scale = 1.08
            if self.variant in ['bubble', 'candy', 'jelly', 'slime']:
                self.wobble = 0.1
            if self.app.sound_on:
                self.app.play_hover()

    def on_exit(self):
        self.hover = False
        self.target_scale = 1.0

    def on_down(self, mx, my):
        if self.anim_state != 'active': return
        self.pressed = True
        self.target_scale = 0.95
        if self.variant in ['bubble', 'candy', 'slime']:
            self.wobble = 0.2
        if self.app.sound_on:
            self.app.play_click(self.variant)

    def on_up(self):
        if self.anim_state != 'active': return
        if self.pressed and self.hover:
            if self.command:
                self.command()
            else:
                self.activate()
        self.pressed = False
        self.target_scale = 1.08 if self.hover else 1.0

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
        pygame.mixer.pre_init(SAMPLE_RATE, -16, 1, 512)
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
        self.W, self.H = pygame.display.get_surface().get_size()
        pygame.display.set_caption("Satisfying Buttons")
        self.clock = pygame.time.Clock()
        self.running = True
        self.particles = []
        self.shake = 0
        self.flash = 0
        self.sound_on = True
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

        # fonts
        self.font_large = pygame.font.SysFont('Segoe UI', 28, bold=True)
        self.font_small = pygame.font.SysFont('Segoe UI', 14, bold=True)

        # UI state
        self.state = 'INTRO'
        self.sidebar_buttons = []
        self.showcase_elements = []
        self.active_element = None
        self.sidebar_initialized = False
        
        self.copy_code_button = Button(self, self.W - 200, 50, 160, 40, "COPY CODE", variant='ui', command=self.copy_code)
        if not PYPERCLIP_AVAILABLE:
            self.copy_code_button.text = "pyperclip missing"
            self.copy_code_button.command = None
            
        self.intro_btn = Button(self, self.W//2, self.H//2, 120, 120, "", variant='intro_orb', command=self.trigger_intro)

        # preload tones
        self.hover_tone = make_tone(980, 0.10, 0.02)
        self.click_tone = make_tone(660, 0.18, 0.12)
        self.crit_tone = make_tone(1200, 0.1, 0.15)
        self.fever_tone = make_tone(220, 0.4, 0.2)
        self.ui_click_tone = make_tone(1500, 0.1, 0.05)
        self.intro_hit = make_tone(100, 0.5, 0.4)
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
            'intro_orb': self._effect_intro
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
        
    def trigger_intro(self):
        self.next_state = 'BUTTONS'
        self._effect_intro(self.intro_btn, 1.0)

    def play_hover(self):
        try:
            self.hover_tone.play()
        except: pass

    def play_click(self, variant):
        try:
            freqs = {'bubble':700,'candy':880,'ripple':520,'pixel':220,'firefly':980,'glitch':100, 'neumorphic': 400, 'glass': 1200, 'retro': 300, 'cyber': 1000, 'soft': 200}
            f = freqs.get(variant, 520)
            s = make_tone(f, 0.16, 0.11)
            s.play()
        except: pass

    def make_sidebar(self):
        self.sidebar_buttons = []
        cats = ['BUTTONS', 'LOADING', 'TRANSITIONS', 'PARTICLES']
        for i, cat in enumerate(cats):
            btn = Button(self, 100, 100 + i*70, 160, 50, cat, variant='ui', command=lambda c=cat: self.set_category(c))
            btn.color = (40, 50, 70)
            self.sidebar_buttons.append(btn)

    def set_category(self, category):
        self.state = category
        self.showcase_elements = []
        self.active_element = None
        self.current_code_snippet = ""
        self.scroll_y = 0.0
        self.scroll_target = 0.0
        
        cx = (self.W - 260 - 400) // 2 + 260 # Center between sidebar and code panel
        
        if category == 'BUTTONS':
            groups = [
                ("MODERN UI", ['neumorphic', 'glass', 'outline', 'soft']),
                ("RETRO & TECH", ['retro', 'cyber', 'pixel', 'glitch']),
                ("JUICY EFFECTS", ['bubble', 'candy', 'ripple', 'firefly']),
            ]
            for title, variants in groups:
                self.showcase_elements.append(Button(self, cx, 0, 300, 50, title, variant='header'))
                for v in variants:
                    btn = Button(self, cx, 0, 280, 80, v.upper(), variant=v, command=lambda v=v: self.show_code(v))
                    self.showcase_elements.append(btn)
        
        elif category == 'LOADING':
            variants = ['load_spinner', 'load_bar', 'load_dots', 'load_pulse']
            for i, v in enumerate(variants):
                btn = Button(self, cx, 0, 280, 100, "", variant=v, command=lambda v=v: self.show_code(v))
                self.showcase_elements.append(btn)
            
        elif category == 'TRANSITIONS':
            self.current_code_snippet = "# Transition effects coming soon..."
            
        elif category == 'PARTICLES':
            self.current_code_snippet = "# Particle systems coming soon..."

    def show_code(self, variant):
        # Example code snippets
        snippets = {
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
            'default': """# Click a button to see its code.
# The code provided will be a self-contained
# example that you can adapt for your project.

# Note: You'll need Pygame installed.
# pip install pygame"""
        }
        self.current_code_snippet = snippets.get(variant, snippets['default'])

    def copy_code(self):
        if PYPERCLIP_AVAILABLE and self.current_code_snippet:
            pyperclip.copy(self.current_code_snippet)
            # Optional: Add visual feedback
            self.flash_screen((100, 255, 100))

    def flash_screen(self, color):
        self.flash = 12

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS)
            self.handle_events()
            self.update()
            self.draw()
            pygame.display.flip()
        pygame.quit(); sys.exit()

    def trigger_button_effect(self, btn):
        # Update code view
        self.show_code(btn.variant)
        
        if btn.variant.startswith('custom_') or btn.variant == 'custom_preview':
            self._effect_custom(btn, 1.0)
            return

        # --- Call variant-specific handler ---
        handler = self.effect_handlers.get(btn.variant)
        if handler:
            handler(btn, 1.0)

    # --- Effect Handlers ---
    def _effect_bubble(self, btn, mult):
        for i in range(int(18 * mult)):
            vx = (random.random()*2-1)*2; vy = -random.random()*3-1 - 1
            self.particles.append(Particle(btn.x+random.uniform(-40,40), btn.y+random.uniform(-20,20), vx, vy, 60, random.uniform(6,12), (200,250,245), gravity=-0.05))
    
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
        self.shake = 60
        self.flash = 60
        self.intro_hit.play()
        
        cx, cy = btn.x, btn.y
        
        # Shockwave
        self.particles.append(Particle(cx, cy, 0, 0, 120, 50, (200, 240, 255), 'ripple', gravity=0))
        self.particles.append(Particle(cx, cy, 0, 0, 100, 100, (255, 255, 255), 'ripple', gravity=0))
        
        # High speed rays
        for i in range(36):
            angle = math.radians(i * 10)
            vx = math.cos(angle) * 40
            vy = math.sin(angle) * 40
            self.particles.append(Particle(cx, cy, vx, vy, 40, 6, (200, 255, 255), 'line', gravity=0))

        # Massive Explosion
        for i in range(250):
            speed = random.uniform(5, 30)
            angle = random.uniform(0, 6.28)
            p_type = random.choice(['sparkle', 'confetti', 'circle'])
            col = random.choice([(200, 230, 255), (255, 255, 255), (100, 200, 255)])
            self.particles.append(Particle(cx, cy, math.cos(angle)*speed, math.sin(angle)*speed, random.randint(60, 150), random.uniform(4, 12), col, p_type))
            
        # Slow heavy debris
        for i in range(20):
             speed = random.uniform(2, 8)
             angle = random.uniform(0, 6.28)
             self.particles.append(Particle(cx, cy, math.cos(angle)*speed, math.sin(angle)*speed, 100, random.uniform(10, 20), (255,255,255), 'circle', gravity=0.1))

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
                self.scroll_target -= ev.y * 120

    def on_pointer_down(self, mx, my):
        current_buttons = self.get_current_buttons()
        is_on_button = any(btn.contains(mx, my) for btn in current_buttons)

        for btn in current_buttons:
            if btn.contains(mx, my):
                btn.on_down(mx, my)
        
        if not is_on_button and self.transition_alpha == 0:
            # Create a ripple effect for clicks on empty space
            self.particles.append(Particle(mx, my, 0, 0, 40, 5, (200,220,255), 'ripple', gravity=0))
            self.ui_click_tone.play()

    def on_pointer_up(self, mx, my):
        current_buttons = self.get_current_buttons()
        for btn in current_buttons:
            btn.on_up()

    def get_current_buttons(self):
        # Always show sidebar
        if self.state == 'INTRO':
            return [self.intro_btn]
            
        btns = self.sidebar_buttons[:] + [self.copy_code_button] 
        btns.extend(self.showcase_elements)
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
        if self.showcase_elements:
            # Smooth scroll
            self.scroll_y += (self.scroll_target - self.scroll_y) * 0.1
            
            # Snap to nearest button
            if abs(self.scroll_target - self.scroll_y) < 1:
                spacing = 110
                snap_index = round(self.scroll_y / spacing)
                snap_target = snap_index * spacing
                # Only snap if we aren't actively scrolling
                # For simplicity in this loop, we just drift towards snap
                self.scroll_target += (snap_target - self.scroll_target) * 0.05

            # Update button positions
            center_y = self.H / 2
            for i, btn in enumerate(self.showcase_elements):
                target_y = center_y + (i * 110) - self.scroll_y
                btn.y = target_y

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

        # update particles
        for p in self.particles[:]:
            p.update()
            if p.life <= 0:
                try: self.particles.remove(p)
                except: pass

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

        if self.state == 'INTRO':
            # Intro Title
            t = self.font_large.render("SATISFYING UI", True, TEXT)
            self.canvas.blit(t, t.get_rect(center=(self.W//2, self.H//2 - 120)))
            t2 = self.font_small.render("CLICK TO START", True, (100, 120, 150))
            self.canvas.blit(t2, t2.get_rect(center=(self.W//2, self.H//2 + 100)))
        else:
            # Calculate transition offsets for panels
            t_norm = self.transition_alpha / 255.0
            if self.transition_fade_in:
                 ease = 1 - (1 - t_norm)**3
            else:
                 ease = t_norm**3
            
            sidebar_x = -260 * ease
            code_x_offset = 400 * ease
            
            # Draw Sidebar
            # Sidebar slides from left
            pygame.draw.rect(self.canvas, DARK_PANEL, (sidebar_x, 0, 260, self.H))
            pygame.draw.line(self.canvas, (40, 50, 70), (sidebar_x + 260, 0), (sidebar_x + 260, self.H), 1)
            
            # Draw Code Panel
            # Code panel slides from right
            code_x = self.W - 400 + code_x_offset
            pygame.draw.rect(self.canvas, (15, 18, 25), (int(code_x), 0, 400, self.H))
            pygame.draw.line(self.canvas, (40, 50, 70), (int(code_x), 0), (int(code_x), self.H), 1)
            
            # Render Code Snippet
            if self.current_code_snippet:
                lines = self.current_code_snippet.split('\n')
                y_off = 100
                for line in lines:
                    color = (150, 200, 255) if line.strip().startswith('def') else (200, 200, 200)
                    if line.strip().startswith('#'): color = (100, 150, 100)
                    t = self.font_small.render(line, True, color)
                    self.canvas.blit(t, (int(code_x) + 20, y_off))
                    y_off += 24
            else:
                # Default message if no code is shown
                t = self.font_small.render("Click a button to see its code snippet.", True, (150, 160, 180))
                rect = t.get_rect(center=(int(code_x) + 200, 150))
                self.canvas.blit(t, rect)
        
        # Draw all buttons for the current state
        # Sort by size to ensure smaller buttons (nav) draw on top of larger ones if they overlap
        # This is a simple hack for z-ordering
        for btn in sorted(current_buttons, key=lambda b: b.w * b.h * (b.wheel_scale if hasattr(b, 'wheel_scale') else 1), reverse=False):
            # Only draw if visible on screen (plus some margin)
            if -100 < btn.y < self.H + 100:
                btn.draw(self.canvas)


        # draw particles on top
        for p in self.particles:
            p.draw(self.canvas)

        # flash
        if self.flash > 0:
            f = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
            f.fill((255,255,255, min(180, int(self.flash*12))))
            self.canvas.blit(f, (0,0), special_flags=pygame.BLEND_RGBA_ADD)

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
        if self.transition_alpha > 0:
            transition_surf = pygame.Surface((self.W, self.H))
            transition_surf.fill((0,0,0))
            transition_surf.set_alpha(self.transition_alpha)
            self.screen.blit(transition_surf, (0,0))


if __name__ == '__main__':

    app = App()
    try:
        app.run()
    except KeyboardInterrupt:
        pygame.quit()
