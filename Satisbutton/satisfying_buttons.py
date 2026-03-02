import math
import random
import sys
import webbrowser
import struct
import time
import warnings
import json
import os

warnings.filterwarnings("ignore", category=UserWarning, message=".*pkg_resources.*")

try:
    import pygame
    from pygame import gfxdraw
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
ALL_VARIANTS = ['bubble','laser','candy','ripple','pixel','magnetic','rainbow','origami','slam','firefly','rocket','blackhole','shatter','coin','slime','glitch','grow', 'atomic']

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

class RocketEntity:
    def __init__(self, app, x, y):
        self.app = app
        self.start_pos = (x, y)
        self.x, self.y = x, y
        self.vx, self.vy = 0, -5
        self.state = 0 # 0: Launch, 1: Roam, 2: Return
        self.timer = 0
        self.angle = 0
        self.life = 1000

    def update(self):
        self.timer += 1
        if self.state == 0: # Launch
            self.vy -= 0.5
            if self.y < -50: self.state = 1; self.timer = 0
        elif self.state == 1: # Roam
            target_x = self.app.W/2 + math.sin(self.timer * 0.05) * (self.app.W/2 - 50)
            target_y = self.app.H/2 + math.cos(self.timer * 0.07) * (self.app.H/2 - 50)
            dx, dy = target_x - self.x, target_y - self.y
            dist = math.hypot(dx, dy)
            self.vx += (dx/dist) * 0.5; self.vy += (dy/dist) * 0.5
            self.vx *= 0.95; self.vy *= 0.95
            if self.timer > 180: self.state = 2
        elif self.state == 2: # Return
            dx, dy = self.start_pos[0] - self.x, self.start_pos[1] - self.y
            dist = math.hypot(dx, dy)
            if dist < 20:
                self.life = 0 # Landed
                self.app.shake = 20
                for _ in range(30): self.app.particles.append(Particle(self.x, self.y, random.uniform(-5,5), random.uniform(-2,-8), 60, 4, (255,100,50)))
            else:
                self.vx = (dx/dist) * 15; self.vy = (dy/dist) * 15
        self.x += self.vx; self.y += self.vy
        self.angle = math.degrees(math.atan2(-self.vy, self.vx)) - 90
        if self.timer % 3 == 0: self.app.particles.append(Particle(self.x, self.y, random.uniform(-1,1), random.uniform(1,3), 30, 4, random.choice([(255,180,80), (255,100,50)]), gravity=0))

    def draw(self, surf):
        # Draw trail/engine glow
        pygame.gfxdraw.filled_circle(surf, int(self.x), int(self.y + 10), 8, (255, 100, 50, 100))
        
        pts = [(0, -20), (-8, 10), (0, 5), (8, 10)]
        rad = math.radians(self.angle)
        cos_a, sin_a = math.cos(rad), math.sin(rad)
        new_pts = [(p[0]*cos_a - p[1]*sin_a + self.x, p[0]*sin_a + p[1]*cos_a + self.y) for p in pts]
        pygame.draw.polygon(surf, (240, 240, 250), new_pts)
        pygame.draw.polygon(surf, (255, 50, 50), new_pts, 2)

class Button:
    def __init__(self, app, x, y, w, h, text, variant='standard', command=None):
        self.app = app
        self.x = x; self.y = y; self.w = w; self.h = h
        self.text = text
        self.variant = variant
        self.hover = False
        self.pressed = False
        self.count = 0
        self.color = random.choice([ACCENT, SECOND, TERTIARY, (245,158,11), (16,185,129)])
        self.scale = 1.0
        self.scale_vel = 0.0
        self.target_scale = 1.0
        self.visible = True
        self.wobble = 0.0
        self.growth_stage = 0
        self.wheel_scale = 1.0
        self.show_panel = False
        self.anim_state = 'active' # active, entering, exiting
        self.anim_progress = 0.0
        self.fold_state = 0 # 0: unfolded, 1: folding, 2: unfolding
        self.fold_progress = 0.0
        self.mag_sep = 5
        self.magnetic_labels = ["Off", "On", "Super On", "Ultra On"]
        self.is_slamming = False
        self.slam_progress = 0.0
        self.original_y = y
        self.text_cycle_index = 0
        self.custom_config = None
        self.command = command
        self.color = (40, 50, 70)
        self.scale = 1.0

        if self.variant.startswith('custom_'):
            self.custom_config = self.app.custom_configs.get(self.variant, {})
            self.color = tuple(self.custom_config.get('color', ACCENT))
            self.text = self.custom_config.get('text', 'CUSTOM')
            self.w = self.custom_config.get('width', 200)
            self.h = self.custom_config.get('height', 80)

    def contains(self, px, py):
        if not self.visible: return False
        return (self.x - self.w/2 <= px <= self.x + self.w/2) and (self.y - self.h/2 <= py <= self.y + self.h/2)

    def update(self):
        # Spring physics for scale
        stiffness = 0.22
        damping = 0.70
        
        if self.custom_config:
            stiffness = self.custom_config.get('stiffness', 0.22)
            damping = self.custom_config.get('damping', 0.70)

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
        
        # Origami folding state machine
        if self.fold_state == 1: # Folding
            self.fold_progress += 0.08
            if self.fold_progress >= 1.0:
                self.fold_progress = 1.0
                self.fold_state = 2 # Start unfolding
        elif self.fold_state == 2: # Unfolding
            self.fold_progress -= 0.08
            if self.fold_progress <= 0.0:
                self.fold_progress = 0.0
                self.fold_state = 0 # Done
        
        # Slamming physics
        if self.is_slamming:
            self.slam_progress += 0.05
            if self.slam_progress < 1.0: # Falling
                eased_t = self.slam_progress**2
                self.y = self.original_y + (self.app.H - self.original_y - self.h/2) * eased_t
                self.app.shake = max(self.app.shake, 15 * (1 - self.slam_progress))
            elif self.slam_progress < 2.0: # Returning
                eased_t = 1 - (2.0 - self.slam_progress)**3
                self.y = self.original_y + (self.app.H - self.original_y - self.h/2) * (1 - eased_t)
            else:
                self.is_slamming = False
                self.y = self.original_y
                self.slam_progress = 0.0


    def draw(self, surf):
        if not self.visible: return
        
        # Calculate effective scale including wheel effect
        eff_scale = self.scale * self.wheel_scale
        
        # Apply wobble to scale
        s = eff_scale + math.sin(time.time() * 20) * self.wobble * self.wheel_scale
        w, h = self.w * s, self.h * s
        cx, cy = self.x, self.y

        # Entry/Exit animation
        if self.anim_state == 'entering':
            eased_prog = 1 - (1 - self.anim_progress)**3
            cy = self.y - self.app.H * (1 - eased_prog)
        elif self.anim_state == 'exiting':
            eased_prog = self.anim_progress**3
            cy = self.y + self.app.H * eased_prog

        # UI button animations for scene transitions
        if self.variant == 'ui':
            if self.app.next_state is not None: # Fading out
                eased_prog = self.app.transition_alpha / 255
                cy += eased_prog * 100 # Slide down and out
            elif self.app.transition_fade_in: # Fading in
                eased_prog = 1 - (self.app.transition_alpha / 255)
                cy += (1 - eased_prog) * 100 # Slide in from below

        # --- PANEL RENDERING (For Collection) ---
        if self.show_panel:
            pw, ph = 300 * self.wheel_scale, 160 * self.wheel_scale
            pr = pygame.Rect(0, 0, int(pw), int(ph))
            pr.center = (int(cx), int(cy))
            pygame.draw.rect(surf, (25, 30, 40), pr, border_radius=int(16*self.wheel_scale))
            pygame.draw.rect(surf, (45, 50, 65), pr, 2, border_radius=int(16*self.wheel_scale))

        # --- SHAPE RENDERING ---
        if self.variant in ['bubble', 'candy', 'coin', 'blackhole', 'firefly', 'slime', 'grow']:
            # CIRCULAR SHAPE
            r = int(min(w, h) / 2)
            # Shadow
            pygame.gfxdraw.filled_circle(surf, int(cx), int(cy)+6, r, (0,0,0,50))
            # Body
            if self.variant == 'firefly':
                pygame.gfxdraw.filled_circle(surf, int(cx), int(cy), r, (20, 30, 40))
                pygame.gfxdraw.aacircle(surf, int(cx), int(cy), r, self.color)
            elif self.variant == 'blackhole':
                pygame.gfxdraw.filled_circle(surf, int(cx), int(cy), r, (0, 0, 0))
                pygame.gfxdraw.aacircle(surf, int(cx), int(cy), r, (50, 50, 50))
            elif self.variant == 'slime':
                # Blobby
                pygame.gfxdraw.filled_circle(surf, int(cx), int(cy), r, (100, 255, 100))
                pygame.gfxdraw.aacircle(surf, int(cx), int(cy), r, (50, 200, 50))
                # Eyes
                pygame.gfxdraw.filled_circle(surf, int(cx-r*0.3), int(cy-r*0.2), int(r*0.2), (255,255,255))
                pygame.gfxdraw.filled_circle(surf, int(cx+r*0.3), int(cy-r*0.2), int(r*0.2), (255,255,255))
                pygame.gfxdraw.filled_circle(surf, int(cx-r*0.3), int(cy-r*0.2), int(r*0.08), (0,0,0))
                pygame.gfxdraw.filled_circle(surf, int(cx+r*0.3), int(cy-r*0.2), int(r*0.08), (0,0,0))
            else:
                pygame.gfxdraw.filled_circle(surf, int(cx), int(cy), r, self.color)
                pygame.gfxdraw.aacircle(surf, int(cx), int(cy), r, self.color)
            
            # Details
            if self.variant == 'coin':
                pygame.gfxdraw.aacircle(surf, int(cx), int(cy), int(r*0.8), (255,255,200))
            elif self.variant == 'candy':
                # Simple stripes
                for i in range(-r, r, 20):
                    pygame.draw.line(surf, (255,255,255,100), (cx+i, cy-r/2), (cx+i-10, cy+r/2), 5)
            elif self.variant == 'grow':
                # Pulse ring
                pygame.gfxdraw.aacircle(surf, int(cx), int(cy), int(r * (0.5 + 0.1 * (self.count % 5))), (255, 255, 255))

            # Gloss
            pygame.gfxdraw.filled_circle(surf, int(cx - r*0.3), int(cy - r*0.3), int(r*0.25), (255,255,255,80))
            
            # Text offset for circle
            rect = pygame.Rect(cx-w/2, cy-h/2, w, h)

        elif self.variant == 'pixel' or self.variant == 'glitch':
            # PIXEL ART SHAPE (Sharp Rect)
            rect = pygame.Rect(int(cx - w/2), int(cy - h/2), int(w), int(h))
            # Hard Shadow
            pygame.draw.rect(surf, (0,0,0,100), rect.move(6, 6))
            # Body
            pygame.draw.rect(surf, self.color, rect)
            # Thick Border
            pygame.draw.rect(surf, (255,255,255), rect, 4)
            pygame.draw.rect(surf, (0,0,0), rect, 2)
            if self.variant == 'glitch':
                # Random glitch bars
                for _ in range(3):
                    gr = pygame.Rect(rect.x + random.randint(0, int(w)), rect.y + random.randint(0, int(h)), random.randint(5, 20), 2)
                    pygame.draw.rect(surf, random.choice([(255,0,0), (0,255,255), (0,0,0)]), gr)

        elif self.variant == 'laser':
            # NEON RECT SHAPE
            rect = pygame.Rect(int(cx - w/2), int(cy - h/2), int(w), int(h))
            # Glow
            for i in range(1, 4):
                pygame.draw.rect(surf, (*self.color[:3], 50//i), rect.inflate(i*6, i*6), 1, border_radius=4)
            pygame.draw.rect(surf, (10,10,10), rect, border_radius=4)
            pygame.draw.rect(surf, self.color, rect, 2, border_radius=4)

        elif self.variant == 'magnetic':
            rect = pygame.Rect(int(cx - w/2), int(cy - h/2), int(w), int(h))
            half_w = w / 2
            sep = self.mag_sep * s
            
            left_rect = pygame.Rect(rect.x, rect.y, half_w - sep/2, h)
            right_rect = pygame.Rect(rect.x + half_w + sep/2, rect.y, half_w - sep/2, h)
            
            pygame.draw.rect(surf, self.color, left_rect, border_radius=int(min(w,h)*0.4))
            pygame.draw.rect(surf, self.color, right_rect, border_radius=int(min(w,h)*0.4))

            # Draw cycling text
            label = self.magnetic_labels[self.text_cycle_index]
            font = self.app.font_small
            txt_shadow = font.render(label, True, (6,10,16))
            surf.blit(txt_shadow, txt_shadow.get_rect(center=(cx, cy + 1)))
            txt = font.render(label, True, TEXT)
            surf.blit(txt, txt.get_rect(center=(cx, cy)))
            return # Return early to skip default text rendering
            
        elif self.variant == 'slam':
            # Draw hanging lines
            if self.anim_state == 'active' and not self.is_slamming:
                line_start_y = 0
                line_end_y = cy - h/2
                pygame.draw.line(surf, (80,90,110), (cx - w/4, line_start_y), (cx - w/4, line_end_y), 2)
                pygame.draw.line(surf, (80,90,110), (cx + w/4, line_start_y), (cx + w/4, line_end_y), 2)
            
            # Standard Rect Drawing for Slam
            rect = pygame.Rect(int(cx - w/2), int(cy - h/2), int(w), int(h))
            # Shadow
            shadow_surf = pygame.Surface((int(w)+20, int(h)+20), pygame.SRCALPHA)
            pygame.gfxdraw.filled_ellipse(shadow_surf, int(w/2+10), int(h/2+10+4), int(w/2), int(h/2), (0,0,0,50))
            surf.blit(shadow_surf, (rect.x-10, rect.y-10))
            # Body
            pygame.draw.rect(surf, self.color, rect, border_radius=int(min(w,h)*0.4))
            # Gloss
            pygame.draw.rect(surf, (255,255,255,30), rect.inflate(-4, -h/2).move(0, -h/4 + 2), border_radius=int(min(w,h)*0.4))

        elif self.variant == 'origami':
            rect = pygame.Rect(int(cx - w/2), int(cy - h/2), int(w), int(h))
            
            # Simple fold to a line
            y_offset = h/2 * self.fold_progress
            p1, p2 = (rect.left, rect.top + y_offset), (rect.right, rect.top + y_offset)
            p3, p4 = (rect.right, rect.bottom - y_offset), (rect.left, rect.bottom - y_offset)
            pygame.draw.polygon(surf, self.color, [p1, p2, p3, p4])

        elif self.variant == 'ui':
            rect = pygame.Rect(int(cx - w/2), int(cy - h/2), int(w), int(h))
            # Clean, sharp look for UI
            shadow_color = (*self.app.accent_color[:3], 20) if self.hover else (0,0,0,50)
            shadow_offset = 2 if self.hover else 6
            pygame.draw.rect(surf, shadow_color, rect.move(0, shadow_offset), border_radius=12)
            
            body_color = tuple(min(255, c+15) for c in self.color) if self.pressed else self.color
            pygame.draw.rect(surf, body_color, rect, border_radius=12)
            
            if self.hover:
                pygame.draw.rect(surf, self.app.accent_color, rect, 2, border_radius=12)

        elif self.variant.startswith('custom_'):
            rect = pygame.Rect(int(cx - w/2), int(cy - h/2), int(w), int(h))
            # Custom button rendering
            shadow_surf = pygame.Surface((int(w)+20, int(h)+20), pygame.SRCALPHA)
            pygame.gfxdraw.filled_ellipse(shadow_surf, int(w/2+10), int(h/2+10+4), int(w/2), int(h/2), (0,0,0,50))
            surf.blit(shadow_surf, (rect.x-10, rect.y-10))
            
            pygame.draw.rect(surf, self.color, rect, border_radius=12)
            # Inner border
            pygame.draw.rect(surf, (255,255,255), rect.inflate(-4, -4), 2, border_radius=10)
            

        else:
            # STANDARD ROUNDED RECT (Pill/Box)
            rect = pygame.Rect(int(cx - w/2), int(cy - h/2), int(w), int(h))

            # Firefly hover glow
            if self.variant == 'firefly' and self.hover:
                pygame.gfxdraw.filled_circle(surf, int(cx), int(cy), int(w/2 * 1.2), (*self.color[:3], 30))

            # Shadow
            shadow_surf = pygame.Surface((int(w)+20, int(h)+20), pygame.SRCALPHA)
            pygame.gfxdraw.filled_ellipse(shadow_surf, int(w/2+10), int(h/2+10+4), int(w/2), int(h/2), (0,0,0,50))
            surf.blit(shadow_surf, (rect.x-10, rect.y-10))
            # Body
            pygame.draw.rect(surf, self.color, rect, border_radius=int(min(w,h)*0.4))
            # Gloss
            pygame.draw.rect(surf, (255,255,255,30), rect.inflate(-4, -h/2).move(0, -h/4 + 2), border_radius=int(min(w,h)*0.4))

        # text
        font = self.app.font_large if (self.w > 200 and self.wheel_scale > 0.6) else self.app.font_small
        
        if self.text == 'LOCKED':
            lr = int(12 * s)
            pygame.draw.rect(surf, (80, 90, 100), (cx - lr, cy, lr*2, lr*1.5))
            pygame.draw.arc(surf, (80, 90, 100), (cx - lr*0.8, cy - lr*1.2, lr*1.6, lr*2), math.pi, 0, 3)
        else:
            # Use smaller font for collection panel text
            if self.show_panel:
                font = self.app.font_small
            
            text_to_render = self.text
            
            txt_shadow = font.render(text_to_render, True, (6,10,16))
            surf.blit(txt_shadow, txt_shadow.get_rect(center=(self.x, self.y + 2)))
            txt = font.render(self.text, True, TEXT)
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
            self.target_scale = 1.1
            if self.variant in ['bubble', 'candy', 'jelly', 'slime']:
                self.wobble = 0.1
            if self.app.sound_on:
                self.app.play_hover()

    def on_exit(self):
        self.hover = False
        self.target_scale = 1.0

    def on_down(self, mx, my):
        if self.anim_state != 'active': return
        if self.variant == 'magnetic':
            self.mag_sep = 0

        self.pressed = True
        self.target_scale = 0.9
        if self.variant in ['bubble', 'candy', 'slime']:
            self.wobble = 0.2
        if self.app.sound_on:
            self.app.play_click(self.variant)

    def on_up(self):
        if self.anim_state != 'active': return
        if self.variant == 'magnetic':
            self.mag_sep = 5

        if self.pressed and self.hover:
            if self.command:
                self.command()
            else:
                self.activate()
        self.pressed = False
        self.target_scale = 1.1 if self.hover else 1.0

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
        self.available_variants = []
        self.main_btn = None
        self.mouse_pos = (0,0)
        self.total_clicks = 0
        self.unlocked_variants = set()
        self.glitch_frames = 0
        self.scroll_y = 0.0
        self.scroll_target = 0.0
        self.drag_start = None
        self.scroll_vel = 0.0
        self.juice_meter = 0
        self.juice_max = 100
        self.fever_timer = 0
        self.stars = [Star(self) for _ in range(100)]
        self.transition_alpha = 0
        self.transition_fade_in = False
        self.next_state = None
        self.rainbow_cycle_timer = 0
        self.custom_configs = {}
        self.save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "save_data.json")

        # fonts
        self.font_large = pygame.font.SysFont('Segoe UI', 28, bold=True)
        self.font_small = pygame.font.SysFont('Segoe UI', 14, bold=True)

        # UI state
        self.state = 'MENU'
        self.menu_buttons = []
        self.show_buttons = []
        self.back_btn = None
        self.collection_buttons = []
        self.current_variant = None
        self.make_menu()
        self.make_showcase_nav()

        # preload tones
        self.hover_tone = make_tone(980, 0.10, 0.02)
        self.click_tone = make_tone(660, 0.18, 0.12)
        self.crit_tone = make_tone(1200, 0.1, 0.15)
        self.fever_tone = make_tone(220, 0.4, 0.2)
        self.ui_click_tone = make_tone(1500, 0.1, 0.05)
        self.whoosh_tone = make_tone(300, 0.3, 0.05) # Transition sound
        

        # Palettes for candy button
        self.candy_palettes = { 'pastel': [(255, 182, 193), (173, 216, 230), (144, 238, 144)], 'neon': [ACCENT, SECOND, TERTIARY], 'mono': [(200,200,200), (150,150,150), (100,100,100)] }
        self.current_candy_palette = 'pastel'

        # Effect dispatcher
        self.effect_handlers = {
            'bubble': self._effect_bubble, 'laser': self._effect_laser,
            'candy': self._effect_candy, 'ripple': self._effect_ripple,
            'pixel': self._effect_pixel, 'magnetic': self._effect_magnetic,
            'rainbow': self._effect_rainbow, 'origami': self._effect_origami,
            'slam': self._effect_slam, 'firefly': self._effect_firefly,
            'rocket': self._effect_rocket, 'blackhole': self._effect_blackhole,
            'shatter': self._effect_shatter, 'coin': self._effect_coin,
            'slime': self._effect_slime, 'glitch': self._effect_glitch,
            'grow': self._effect_grow, 'atomic': self._effect_atomic,
            'custom': self._effect_custom
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
        
        # Editor State
        self.editor_sliders = []
        self.editor_btn_preview = None
        self.editor_text_input = ""
        self.load_data()

    def load_data(self):
        if os.path.exists(self.save_path):
            try:
                with open(self.save_path, "r") as f:
                    data = json.load(f)
                    clicks = data.get("clicks", 0)
                    # Fix for absurdly large numbers from previous bug
                    if clicks > 1_000_000_000: clicks = 0
                    self.total_clicks = clicks
                    self.unlocked_variants = set(data.get("variants", []))
                    self.custom_configs = data.get("custom_configs", {})
            except Exception:
                print("Failed to load save data")

    def save_data(self):
        data = {
            "clicks": self.total_clicks,
            "variants": list(self.unlocked_variants),
            "custom_configs": self.custom_configs
        }
        try:
            with open(self.save_path, "w") as f:
                json.dump(data, f)
        except Exception:
            print("Failed to save data")

    def play_hover(self):
        try:
            self.hover_tone.play()
        except: pass

    def play_click(self, variant):
        try:
            is_crit = random.random() < 0.05 or self.fever_timer > 0
            freqs = {'bubble':700,'laser':130,'candy':880,'ripple':520,'pixel':220,'magnetic':320,'rainbow':760,'origami':520,'slam':120,'firefly':980,'rocket':200,'blackhole':50,'shatter':1000,'coin':1500,'slime':400,'glitch':100,'grow':600, 'atomic': 40}
            f = freqs.get(variant, 520)
            s = make_tone(f, 0.16, 0.11)
            s.play()
            if is_crit:
                self.crit_tone.play()
        except: pass

    def make_menu(self):
        self.menu_buttons = []
        cx, cy = self.W//2, self.H//2
        start_btn = Button(self, cx, cy-120, 320, 70, 'START', variant='ui', command=self.start_showcase)
        create_btn = Button(self, cx, cy-40, 320, 70, 'CREATE', variant='ui', command=self.open_editor)
        collection_btn = Button(self, cx, cy+40, 320, 70, 'COLLECTION', variant='ui', command=self.open_collection)
        coffee_btn = Button(self, cx, cy+120, 320, 70, 'BUY ME A COFFEE', variant='ui', command=lambda: webbrowser.open('https://www.buymeacoffee.com/'))
        self.menu_buttons.extend([start_btn, create_btn, collection_btn, coffee_btn])

    def start_showcase(self):
        self.next_state = 'SHOWCASE'
        if not self.current_variant:
            self.next_variant()
        self.whoosh_tone.play()

    def open_collection(self):
        self.next_state = 'COLLECTION'

    def open_editor(self):
        self.next_state = 'EDITOR'
        # Initialize default custom config
        self.current_edit_config = {
            'color': [100, 200, 255],
            'width': 200, 'height': 80,
            'text': 'MY BUTTON',
            'stiffness': 0.2, 'damping': 0.7,
            # New animation properties
            'particle_kind': 0, # 0:circle, 1:pixel, 2:confetti, 3:sparkle
            'particle_count': 15,
            'particle_life': 40,
            'particle_size': 6,
            'particle_speed': 5,
        }
        self.editor_text_input = "MY BUTTON"
        
        # Create sliders
        col1_x, col2_x, col3_x = 50, self.W/2 - 100, self.W - 300
        sy = 120
        self.editor_sliders = [
            # Appearance
            Slider(col1_x, sy, 200, 0, 255, 100, "Red"),
            Slider(col1_x, sy+60, 200, 0, 255, 200, "Green"),
            Slider(col1_x, sy+120, 200, 0, 255, 255, "Blue"),
            Slider(col1_x, sy+180, 200, 50, 400, 200, "Width"),
            Slider(col1_x, sy+240, 200, 30, 200, 80, "Height"),
            
            # Physics
            Slider(col2_x, sy, 200, 0.05, 0.5, 0.2, "Spring Stiffness"),
            Slider(col2_x, sy+60, 200, 0.5, 0.95, 0.7, "Spring Damping"),
            
            # Click Effect
            Slider(col3_x, sy, 200, 0, 3, 0, "Particle Kind"),
            Slider(col3_x, sy+60, 200, 0, 50, 15, "Particle Count"),
            Slider(col3_x, sy+120, 200, 10, 120, 40, "Particle Life"),
            Slider(col3_x, sy+180, 200, 2, 20, 6, "Particle Size"),
            Slider(col3_x, sy+240, 200, 1, 15, 5, "Particle Speed"),
        ]
        
        # Preview button
        self.editor_btn_preview = Button(self, col2_x + 100, self.H - 150, 200, 80, "MY BUTTON", variant='custom_preview')
        self.editor_btn_preview.custom_config = self.current_edit_config
        
        self.editor_ui_buttons = [Button(self, self.W - 140, self.H - 60, 100, 40, "SAVE", variant='ui', command=self.save_custom_button), Button(self, 80, 60, 100, 40, "EXIT", variant='ui', command=self.go_to_menu)]
        self.whoosh_tone.play()

    def make_collection_buttons(self):
        self.collection_buttons = []
        # Back button
        self.back_btn = Button(self, 80, 60, 120, 40, 'BACK', variant='ui', command=self.go_to_menu)
        
        # Grid of collected buttons
        cols = 5
        start_x = self.W // 2 - (cols * 70) // 2 + 35
        start_y = 180
        
        for i, variant in enumerate(ALL_VARIANTS):
            # Positions are set in update loop for wheel
            if variant in self.unlocked_variants:
                btn = Button(self, 0, 0, 100, 100, variant.upper(), variant=variant)
            else:
                btn = Button(self, 0, 0, 100, 100, 'LOCKED', variant='standard') # Text used for logic, drawing handled in draw()
                btn.color = (50, 50, 60) # Locked color
            
            btn.show_panel = True
            self.collection_buttons.append(btn)
            
        # Add custom buttons to collection
        for cid, cfg in self.custom_configs.items():
            btn = Button(self, 0, 0, 100, 100, cfg.get('text', 'CUSTOM'), variant=cid)
            btn.show_panel = True; self.collection_buttons.append(btn)

    def unlock_variant(self, variant):
        if variant not in self.unlocked_variants:
            self.unlocked_variants.add(variant)
            self.save_data()

    def go_to_menu(self):
        self.next_state = 'MENU'
        self.whoosh_tone.play()

    def save_custom_button(self):
        # Generate ID
        cid = f"custom_{len(self.custom_configs)}"
        self.custom_configs[cid] = self.current_edit_config.copy()
        self.save_data()
        self.flash_screen((100, 255, 100))
        self.go_to_menu()

    def make_showcase_nav(self):
        self.show_buttons = []
        self.show_buttons.append(Button(self, 80, 60, 140, 48, 'MENU', variant='ui', command=self.go_to_menu))
        self.show_buttons.append(Button(self, self.W//2, self.H-80, 220, 56, 'NEXT', variant='ui', command=self.next_variant))

    def next_variant(self):
        if self.main_btn and self.main_btn.anim_state == 'active':
            self.main_btn.anim_state = 'exiting'
            self.main_btn.anim_progress = 0.0
            return

        # 3% chance for a surprise atomic bomb, if not already in the upcoming list
        if random.random() < 0.03 and 'atomic' not in self.available_variants:
            self.current_variant = 'atomic'
        else:
            if not self.available_variants:
                self.available_variants = ALL_VARIANTS[:] + list(self.custom_configs.keys())
                random.shuffle(self.available_variants)
            
            self.current_variant = self.available_variants.pop()

        self.main_btn = Button(self, self.W//2, self.H//2, 360, 120, 'Click Me', self.current_variant)
        self.main_btn.anim_state = 'entering'
        self.unlock_variant(self.current_variant)

    def flash_screen(self, color):
        self.flash = 12

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS)
            self.handle_events()
            self.update()
            self.draw()
            pygame.display.flip()
        self.save_data()
        pygame.quit(); sys.exit()

    def add_juice(self, amount):
        if self.fever_timer <= 0:
            self.juice_meter = min(self.juice_max, self.juice_meter + amount)

    def trigger_button_effect(self, btn):
        if btn.variant != 'atomic': # Atomic bomb doesn't count as a normal click for stats
            self.total_clicks += 1
            self.unlock_variant(btn.variant)
            if self.total_clicks % 10 == 0:
                self.save_data()

        # --- Universal Click Effects (Crits, Juice) ---
        is_crit = random.random() < 0.05 or self.fever_timer > 0
        particle_multiplier = 1.5 if is_crit else 1.0
        if self.fever_timer > 0: particle_multiplier *= 1.5 # Extra juicy during fever

        if is_crit and self.fever_timer <= 0 and btn.variant != 'atomic':
            self.particles.append(TextParticle(btn.x, btn.y - 40, "CRIT!", (255, 220, 100), 60))
            for _ in range(5): # Add sparkles
                self.particles.append(Particle(btn.x, btn.y, random.uniform(-10, 10), random.uniform(-10, 10), 40, 8, (255, 255, 200), 'sparkle', gravity=0.1))
            self.add_juice(40)
        elif btn.variant != 'atomic':
            self.add_juice(15)
        
        if btn.variant.startswith('custom_') or btn.variant == 'custom_preview':
            self._effect_custom(btn, particle_multiplier)
            return

        # --- Call variant-specific handler ---
        handler = self.effect_handlers.get(btn.variant)
        if handler:
            handler(btn, particle_multiplier)

    # --- Effect Handlers ---
    def _effect_bubble(self, btn, mult):
        for i in range(int(18 * mult)):
            vx = (random.random()*2-1)*2; vy = -random.random()*3-1 - 1
            self.particles.append(Particle(btn.x+random.uniform(-40,40), btn.y+random.uniform(-20,20), vx, vy, 60, random.uniform(6,12), (200,250,245), gravity=-0.05))
    
    def _effect_laser(self, btn, mult):
        for _ in range(random.randint(1, 2) if mult > 1 else 1):
            angle = random.random()*math.pi*2
            self.particles.append(Particle(btn.x, btn.y, math.cos(angle)*30, math.sin(angle)*30, 20, 5, (255,50,50), 'line', gravity=0))
        self.flash_screen((255,220,200))

    def _effect_candy(self, btn, mult):
        # Cycle through colors in the current palette
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

    def _effect_magnetic(self, btn, mult):
        # Cycle through text labels
        btn.text_cycle_index = (btn.text_cycle_index + 1) % len(btn.magnetic_labels)
        for i in range(int(12 * mult)): self.particles.append(Particle(btn.x, btn.y, random.uniform(-6,6), random.uniform(-6,0), 40, random.uniform(3,6), (250,180,120), 'line'))

    def _effect_rainbow(self, btn, mult):
        # Instead of spawning particles, start the dash
        btn.is_dashing = True

    def _effect_rainbow_pulse(self):
        self.rainbow_cycle_timer = 240 # 4 seconds
        for h in range(0,360,20):
            self.particles.append(Particle(self.W/2, self.H/2, math.cos(math.radians(h))*8, math.sin(math.radians(h))*8, 60, 6, (int(128+127*math.cos(math.radians(h))), int(128+127*math.cos(math.radians(h-120))), int(128+127*math.cos(math.radians(h-240)) )), gravity=0))

    def _effect_origami(self, btn, mult):
        if btn.fold_state == 0: btn.fold_state = 1

    def _effect_slam(self, btn, mult):
        if not btn.is_slamming:
            btn.is_slamming = True
            btn.slam_progress = 0.0

    def _effect_firefly(self, btn, mult):
        for i in range(int(18 * mult)): self.particles.append(Particle(btn.x+random.uniform(-40,40), btn.y+random.uniform(-20,20), random.uniform(-1,1), random.uniform(-1,1), random.randint(40,80), random.uniform(2,5), (200,255,190), gravity=-0.02))

    def _effect_rocket(self, btn, mult):
        self.particles.append(RocketEntity(self, btn.x, btn.y))

    def _effect_blackhole(self, btn, mult):
        for p in self.particles:
            if isinstance(p, Particle):
                dx, dy = btn.x - p.x, btn.y - p.y
                p.vx += dx * 0.05; p.vy += dy * 0.05
        self.particles.append(Particle(btn.x, btn.y, 0, 0, 30, 100, (0,0,0), 'ripple', gravity=0))

    def _effect_shatter(self, btn, mult):
        btn.visible = False
        for i in range(int(20 * mult)): self.particles.append(Particle(btn.x, btn.y, random.uniform(-10,10), random.uniform(-10,10), 60, 15, btn.color, 'confetti'))

    def _effect_coin(self, btn, mult):
        for i in range(int(10 * mult)): self.particles.append(Particle(btn.x, btn.y, random.uniform(-5,5), random.uniform(-15,-5), 60, 8, (255, 215, 0), 'circle'))

    def _effect_slime(self, btn, mult):
        for i in range(int(12 * mult)): self.particles.append(Particle(btn.x, btn.y, random.uniform(-3,3), random.uniform(-5,0), 40, random.uniform(4,10), (100,255,100), gravity=0.3))

    def _effect_glitch(self, btn, mult):
        self.glitch_frames = 6
        for i in range(int(8 * mult)): self.particles.append(Particle(btn.x, btn.y, random.uniform(-10,10), random.uniform(-10,10), 20, 8, random.choice([(255,0,0),(0,255,255),(255,255,255)]), 'pixel'))

    def _effect_grow(self, btn, mult):
        btn.growth_stage += 1
        btn.target_scale = 1.0 + btn.growth_stage * 0.2
        if btn.growth_stage > 5:
            btn.growth_stage = 0
            btn.target_scale = 1.0
            for i in range(int(20 * mult)): self.particles.append(Particle(btn.x, btn.y, random.uniform(-5,5), random.uniform(-5,5), 40, 6, btn.color))

    def _effect_atomic(self, btn, mult):
        btn.visible = False
        self.shake = 60
        self.flash = 25
        # Push existing particles
        for p in self.particles:
            if isinstance(p, Particle):
                dx, dy = p.x - btn.x, p.y - btn.y
                dist = math.hypot(dx, dy)
                if dist > 0:
                    p.vx += (dx / dist) * 40; p.vy += (dy / dist) * 40
        # Shockwave & Fireball
        self.particles.append(Particle(btn.x, btn.y, 0, 0, 80, 10, (255,255,220), 'ripple', gravity=0))
        for i in range(150): self.particles.append(Particle(btn.x, btn.y, random.uniform(-18,18), random.uniform(-18,18), random.randint(50,80), random.uniform(5,15), random.choice([(255,100,0),(255,200,0),(200,50,0)])))

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
                if self.state == 'EDITOR':
                    if ev.key == pygame.K_BACKSPACE:
                        self.editor_text_input = self.editor_text_input[:-1]
                    elif len(self.editor_text_input) < 12 and ev.unicode.isprintable():
                        self.editor_text_input += ev.unicode
                    self.current_edit_config['text'] = self.editor_text_input
                    self.editor_btn_preview.text = self.editor_text_input

            elif ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button == 1:
                    self.on_pointer_down(self.mouse_pos[0], self.mouse_pos[1])
            elif ev.type == pygame.MOUSEBUTTONUP:
                if ev.button == 1:
                    self.on_pointer_up(self.mouse_pos[0], self.mouse_pos[1])
                    self.drag_start = None
            elif ev.type == pygame.MOUSEWHEEL:
                if self.state == 'COLLECTION':
                    self.scroll_vel += ev.y * 10
            elif ev.type == pygame.MOUSEMOTION:
                if self.state == 'COLLECTION' and pygame.mouse.get_pressed()[0]:
                    if self.drag_start is None:
                        self.drag_start = ev.pos[1]
                        self.scroll_vel = 0 # Stop inertia on new drag
                    else:
                        dy = ev.pos[1] - self.drag_start
                        self.scroll_vel = dy * 0.8 # Track velocity
                        self.scroll_y += dy # Immediate feel
                        self.drag_start = ev.pos[1]

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
        if self.state == 'MENU':
            return self.menu_buttons
        elif self.state == 'SHOWCASE':
            return self.show_buttons + ([self.main_btn] if self.main_btn else [])
        elif self.state == 'COLLECTION':
            return self.collection_buttons + ([self.back_btn] if self.back_btn else [])
        return []
    
    def get_editor_buttons(self):
        if self.state == 'EDITOR':
            return self.editor_ui_buttons + [self.editor_btn_preview]

    def update(self):
        # Handle screen transitions
        if self.next_state is not None: # Fading out
            self.transition_alpha = min(255, self.transition_alpha + 15)
            if self.transition_alpha >= 255:
                self.state = self.next_state
                self.next_state = None
                self.transition_fade_in = True
                if self.state == 'COLLECTION':
                    self.make_collection_buttons()
                elif self.state == 'EDITOR':
                    self.open_editor() # Re-init editor state
                if self.state == 'EDITOR':
                    self.editor_btn_preview.visible = True
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

        if self.state == 'EDITOR':
            # Update sliders
            mx, my = self.mouse_pos
            down = pygame.mouse.get_pressed()[0]
            for s in self.editor_sliders:
                if s.update(mx, my, down):
                    # Update config live
                    c = self.current_edit_config
                    if "Red" in s.label: c['color'][0] = int(s.value)
                    if "Green" in s.label: c['color'][1] = int(s.value)
                    if "Blue" in s.label: c['color'][2] = int(s.value)
                    if "Width" in s.label: c['width'] = int(s.value)
                    if "Height" in s.label: c['height'] = int(s.value)
                    if "Stiffness" in s.label: c['stiffness'] = s.value
                    if "Damping" in s.label: c['damping'] = s.value
                    if "Kind" in s.label: c['particle_kind'] = s.value
                    if "Count" in s.label: c['particle_count'] = s.value
                    if "Life" in s.label: c['particle_life'] = s.value
                    if "Size" in s.label: c['particle_size'] = s.value
                    if "Speed" in s.label: c['particle_speed'] = s.value
                    
            self.editor_btn_preview.color = tuple(self.current_edit_config['color'])
            self.editor_btn_preview.w = self.current_edit_config['width']
            self.editor_btn_preview.h = self.current_edit_config['height']
            self.editor_btn_preview.update()
            for b in self.editor_ui_buttons: b.update()
            
            # Don't run normal button update loop for editor
            return

        current_buttons = self.get_current_buttons()
        for btn in current_buttons:
            # Don't check for hover if transitioning
            if self.transition_alpha == 0:
                if btn.contains(self.mouse_pos[0], self.mouse_pos[1]):
                    btn.on_hover()
                else:
                    btn.on_exit()
            btn.update()
            
        # Handle next button creation after exit animation
        if self.main_btn and self.main_btn.anim_state == 'active' and not self.main_btn.visible:
            self.next_variant()


        if self.state == 'COLLECTION':
            # Smooth scroll
            if self.drag_start is None: # Not dragging
                self.scroll_y += self.scroll_vel
                self.scroll_vel *= 0.94 # Friction
                
                # Snap to center when slow
                if abs(self.scroll_vel) < 0.1:
                    spacing = 180
                    snap_target = round(self.scroll_y / spacing) * spacing
                    self.scroll_y += (snap_target - self.scroll_y) * 0.1
                    self.scroll_vel = 0

            spacing = 180
            total_h = len(self.collection_buttons) * spacing
            cy = self.H / 2
            
            for i, btn in enumerate(self.collection_buttons):
                # Infinite scroll math
                base_y = i * spacing
                offset = (base_y + self.scroll_y) % total_h
                if offset > total_h / 2: offset -= total_h
                
                btn.x = self.W / 2
                btn.y = cy + offset
                
                # Wheel effect (Scale based on distance from center)
                dist = abs(offset)
                max_dist = self.H * 0.6
                if dist > max_dist:
                    btn.visible = False
                else:
                    btn.visible = True
                    btn.wheel_scale = max(0.0, 1.0 - (dist / max_dist)**2)

        # Float animation for main button in showcase
        if self.state == 'SHOWCASE' and self.main_btn:
            if self.main_btn.variant == 'rainbow' and self.main_btn.anim_state == 'active':
                if not getattr(self.main_btn, 'is_dashing', False):
                    mx, my = self.mouse_pos
                    self.main_btn.x += (mx - self.main_btn.x) * 0.1
                    self.main_btn.y += (my - self.main_btn.y) * 0.1
                else: # Dashing to center
                    self.main_btn.x += (self.W/2 - self.main_btn.x) * 0.15
                    self.main_btn.y += (self.H/2 - self.main_btn.y) * 0.15
                    if math.hypot(self.W/2 - self.main_btn.x, self.H/2 - self.main_btn.y) < 5:
                        self.main_btn.is_dashing = False
                        self._effect_rainbow_pulse()
            else: # Default float
                self.main_btn.y = self.H//2 + math.sin(pygame.time.get_ticks() * 0.002) * 8
                
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
        
        # Juice & Fever
        if self.fever_timer > 0:
            self.fever_timer -= 1
            self.juice_meter = (self.fever_timer / 300) * self.juice_max
        elif self.juice_meter >= self.juice_max:
            self.fever_timer = 300 # 5 seconds at 60fps
            self.fever_tone.play()
            self.shake = 10
        else:
            self.juice_meter = max(0, self.juice_meter - 0.1)

    def draw(self):
        # Use pre-rendered background on persistent canvas
        if self.fever_timer > 0:
            # Pulsing red background during fever
            fever_pulse = (1 - (self.fever_timer / 300))
            fever_alpha = abs(math.sin(fever_pulse * math.pi * 4)) * 40
            fever_surf = pygame.Surface((self.W, self.H)); fever_surf.fill(TERTIARY)
            fever_surf.set_alpha(fever_alpha)
            self.canvas.blit(self.bg_surf, (0,0)); self.canvas.blit(fever_surf, (0,0))
        else:
            self.canvas.blit(self.bg_surf, (0, 0))

        # Draw parallax stars
        for star in self.stars:
            pos = star.update(self.mouse_pos)
            pygame.draw.rect(self.canvas, star.color, (pos[0], pos[1], star.size, star.size))

        current_buttons = self.get_current_buttons()

        if self.state == 'MENU':
            title = self.font_large.render('Satisfying Buttons', True, TEXT)
            self.canvas.blit(title, title.get_rect(center=(self.W//2, self.H//2 - 160)))
            stats = self.font_small.render(f"TOTAL CLICKS: {self.total_clicks}", True, (100, 110, 130))
            self.canvas.blit(stats, (20, 20))
        
        elif self.state == 'COLLECTION':
            # Title and Hint
            title = self.font_large.render('COLLECTION', True, TEXT)
            self.canvas.blit(title, title.get_rect(center=(self.W//2, 80)))
            
            # Hint
            hint = self.font_small.render(f"Found: {len(self.unlocked_variants)} / {len(ALL_VARIANTS)}", True, (150, 160, 180))
            self.canvas.blit(hint, hint.get_rect(center=(self.W//2, 140)))

        elif self.state == 'SHOWCASE':
            stats = self.font_small.render(f"TOTAL CLICKS: {self.total_clicks}", True, (100, 110, 130))
            self.canvas.blit(stats, (20, 20))

        elif self.state == 'EDITOR':
            title = self.font_large.render('BUTTON ENGINE', True, TEXT)
            self.canvas.blit(title, (50, 40))
            
            # Column Titles
            col1_x, col2_x, col3_x = 50, self.W/2 - 100, self.W - 300
            self.canvas.blit(self.font_small.render("APPEARANCE", True, TEXT), (col1_x, 90))
            self.canvas.blit(self.font_small.render("PHYSICS", True, TEXT), (col2_x, 90))
            self.canvas.blit(self.font_small.render("CLICK EFFECT", True, TEXT), (col3_x, 90))

            # Particle Kind Label
            particle_kinds = ['Circle', 'Pixel', 'Confetti', 'Sparkle']
            kind_slider = self.editor_sliders[7]
            kind_label = self.font_small.render(f"({particle_kinds[int(kind_slider.value)]})", True, (150,150,160))
            self.canvas.blit(kind_label, (col3_x + 120, 120 - 25))

            # Draw Sliders
            for s in self.editor_sliders:
                s.draw(self.canvas, self.font_small)
            
            # Draw Spline Graph (Physics Visualization)
            gx, gy, gw, gh = self.W - 250, 120, 200, 100
            pygame.draw.rect(self.canvas, (20, 25, 35), (gx, gy, gw, gh), border_radius=8)
            # Grid lines
            pygame.draw.line(self.canvas, (30, 35, 45), (gx, gy + gh/2), (gx + gw, gy + gh/2), 1)
            pygame.draw.line(self.canvas, (30, 35, 45), (gx + gw/2, gy), (gx + gw/2, gy + gh), 1)

            points = []
            val = 0; vel = 0; target = gh/2
            stiff = self.current_edit_config['stiffness']
            damp = self.current_edit_config['damping']
            for i in range(gw):
                force = (target - val) * stiff
                vel += force; vel *= damp; val += vel
                points.append((gx + i, gy + gh - (val + gh/4)))
            if len(points) > 1: pygame.draw.lines(self.canvas, ACCENT, False, points, 2)
            
            for b in self.editor_ui_buttons: b.draw(self.canvas)
            self.editor_btn_preview.draw(self.canvas)

        # Draw Juice Meter
        juice_h = (self.juice_meter / self.juice_max) * (self.H - 40)
        juice_color = self.accent_color if self.fever_timer <= 0 else (255, 255, 255)
        if self.fever_timer > 0 and self.fever_timer % 10 < 5:
            juice_color = TERTIARY
        
        # Juice meter glow
        if self.juice_meter >= self.juice_max:
            pygame.draw.rect(self.canvas, juice_color, (self.W - 32, 18, 14, self.H - 36), 1)

        pygame.draw.rect(self.canvas, (30,40,55), (self.W - 30, 20, 10, self.H - 40))
        pygame.draw.rect(self.canvas, juice_color, (self.W - 30, self.H - 20 - juice_h, 10, juice_h))
        
        # Draw all buttons for the current state
        # Sort by size to ensure smaller buttons (nav) draw on top of larger ones if they overlap
        # This is a simple hack for z-ordering
        for btn in sorted(current_buttons, key=lambda b: b.w * b.h * (b.wheel_scale if hasattr(b, 'wheel_scale') else 1), reverse=False):
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
