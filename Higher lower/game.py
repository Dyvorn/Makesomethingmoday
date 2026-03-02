import random
import tkinter as tk
from tkinter import ttk

LOW, HIGH = 1, 100


BG = "#07070C"          
CARD = "#0D0D16"        
WHITE = "#F4F4FF"
MUTED = "#B8B8D6"
MAGENTA = "#FF2DFF"
MAGENTA_DIM = "#B100B1"
BORDER = "#2A2A44"

class NeonHigherLower:
    def __init__(self, root):
        self.root = root
        self.root.title("Neon Higher / Lower")
        self.root.configure(bg=BG)
        self.root.minsize(520, 320)

        self.secret = None
        self.turns = 0
        self.low_hint = LOW
        self.high_hint = HIGH

        self._style()
        self._build_ui()
        self.new_game()

    def _style(self):
        style = ttk.Style(self.root)
        
        if "clam" in style.theme_names():
            style.theme_use("clam")  

        style.configure("Card.TFrame", background=CARD)
        style.configure("Neon.TLabel", background=CARD, foreground=WHITE, font=("Segoe UI", 11))
        style.configure("Muted.TLabel", background=CARD, foreground=MUTED, font=("Segoe UI", 10))

        style.configure("Neon.TButton", font=("Segoe UI", 11, "bold"), padding=10)
        style.map(
            "Neon.TButton",
            foreground=[("active", WHITE), ("!disabled", WHITE)],
            background=[("active", MAGENTA_DIM), ("!disabled", MAGENTA)],
        )

        style.configure("Ghost.TButton", font=("Segoe UI", 10), padding=10)
        style.map(
            "Ghost.TButton",
            foreground=[("active", WHITE), ("!disabled", WHITE)],
            background=[("active", "#1A1A2B"), ("!disabled", "#131322")],
        )

        
        style.configure(
            "Neon.TEntry",
            foreground=WHITE,
            fieldbackground="#0A0A12",
            background="#0A0A12",
            insertcolor=WHITE,
            padding=8,
        )

        self.style = style

    def _build_ui(self):
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        outer = tk.Frame(self.root, bg=BG)
        outer.grid(row=0, column=0, sticky="nsew", padx=18, pady=18)
        outer.columnconfigure(0, weight=1)

        
        self.title_canvas = tk.Canvas(
            outer, height=70, bg=BG, highlightthickness=0
        )
        self.title_canvas.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        self._draw_glow_title()

       
        border = tk.Frame(outer, bg=BORDER, padx=2, pady=2)
        border.grid(row=1, column=0, sticky="nsew")
        border.columnconfigure(0, weight=1)

        self.card = ttk.Frame(border, style="Card.TFrame", padding=18)
        self.card.grid(row=0, column=0, sticky="nsew")
        self.card.columnconfigure(0, weight=1)
        self.card.columnconfigure(1, weight=1)

        self.subtitle = ttk.Label(self.card, text="Guess the secret number.", style="Neon.TLabel")
        self.subtitle.grid(row=0, column=0, columnspan=2, sticky="w")

        self.range_label = ttk.Label(self.card, text="", style="Muted.TLabel")
        self.range_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 12))

        self.entry = ttk.Entry(self.card, style="Neon.TEntry", justify="center")
        self.entry.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.entry.bind("<Return>", self.on_guess)

        self.msg = ttk.Label(self.card, text="", style="Neon.TLabel")
        self.msg.grid(row=3, column=0, columnspan=2, sticky="w", pady=(12, 0))

        self.turns_label = ttk.Label(self.card, text="Turns: 0", style="Muted.TLabel")
        self.turns_label.grid(row=4, column=0, columnspan=2, sticky="w", pady=(6, 12))

        self.guess_btn = ttk.Button(self.card, text="GUESS", style="Neon.TButton", command=self.on_guess)
        self.guess_btn.grid(row=5, column=0, sticky="ew", padx=(0, 8))

        self.new_btn = ttk.Button(self.card, text="New game", style="Ghost.TButton", command=self.new_game)
        self.new_btn.grid(row=5, column=1, sticky="ew", padx=(8, 0))

    def _draw_glow_title(self):
        self.title_canvas.delete("all")
        w = self.title_canvas.winfo_reqwidth()
        x = 8
        y = 40
        text = "HIGHER / LOWER"

        
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2), (-2, -2), (2, 2), (-3, 1), (3, -1)]:
            self.title_canvas.create_text(
                x + dx, y + dy, anchor="w", text=text,
                fill=MAGENTA_DIM, font=("Segoe UI", 24, "bold")
            )
        self.title_canvas.create_text(
            x, y, anchor="w", text=text,
            fill=MAGENTA, font=("Segoe UI", 24, "bold")
        )
        self.title_canvas.create_text(
            x, y + 22, anchor="w", text="Neon edition",
            fill=MUTED, font=("Segoe UI", 10)
        )

    def _update_range(self):
        self.range_label.config(text=f"Range: {self.low_hint} — {self.high_hint}")

    def new_game(self):
        self.secret = random.randint(LOW, HIGH)
        self.turns = 0
        self.low_hint = LOW
        self.high_hint = HIGH

        self.msg.config(text="Enter a guess (1–100).")
        self.turns_label.config(text="Turns: 0")
        self._update_range()

        self.entry.delete(0, tk.END)
        self.entry.focus_set()
        self.guess_btn.state(["!disabled"])

    def on_guess(self, event=None):
        raw = self.entry.get().strip()
        try:
            guess = int(raw)
        except ValueError:
            self.msg.config(text="Numbers only.")
            return

        if not (LOW <= guess <= HIGH):
            self.msg.config(text="Out of range.")
            return

        self.turns += 1
        self.turns_label.config(text=f"Turns: {self.turns}")

        if guess < self.secret:
            self.msg.config(text="Higher.")
            self.low_hint = max(self.low_hint, guess + 1)
            self._update_range()
        elif guess > self.secret:
            self.msg.config(text="Lower.")
            self.high_hint = min(self.high_hint, guess - 1)
            self._update_range()
        else:
            self.msg.config(text=f"Correct. Turns: {self.turns}")
            self.guess_btn.state(["disabled"])

        self.entry.delete(0, tk.END)
        self.entry.focus_set()

def main():
    root = tk.Tk()
    app = NeonHigherLower(root)
    root.mainloop()  

if __name__ == "__main__":
    main()
