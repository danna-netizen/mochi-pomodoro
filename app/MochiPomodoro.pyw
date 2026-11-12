"""
Mochi Pomodoro  -  temporizador Pomodoro de escritorio
======================================================

Version 1.0.0

Este programa es UN SOLO ARCHIVO de Python que puedes leer completo.
- Solo usa la libreria estandar de Python (tkinter, json, time, math).
- NO se conecta a internet (no importa socket, urllib, http ni requests).
- NO pide permisos de administrador ni toca el registro de Windows.
- El unico archivo que escribe es "mochi_settings.json", junto a este
  archivo, para recordar tus minutos. Puedes borrarlo cuando quieras.

Atajos:  Espacio = empezar/pausar   R = reiniciar   S = saltar
         1 / 2 / 3 = Enfoque / Descanso / Descanso largo
"""

import json
import math
import sys
import time
import tkinter as tk
from pathlib import Path

try:  # Solo existe en Windows; se usa para el sonidito al terminar.
    import winsound
except ImportError:
    winsound = None

APP = "Mochi Pomodoro"
VERSION = "1.0.0"
SETTINGS_FILE = Path(__file__).resolve().with_name("mochi_settings.json")

COLORS = {
    "bg": "#FFF7F9",
    "ink": "#4B3A46",
    "muted": "#B49AAA",
    "track": "#F7E4EB",
    "white": "#FFFFFF",
    "blush": "#FFB8CB",
    "leaf": "#8CCB9B",
}
MODES = {
    "focus": {"tab": "Enfoque", "color": "#FF8FB1", "soft": "#FFE6EE", "msg": "a concentrarse  ✿"},
    "short": {"tab": "Descanso", "color": "#6FC7B6", "soft": "#DDF5F0", "msg": "estira y toma agüita"},
    "long": {"tab": "Largo", "color": "#A98EF0", "soft": "#ECE6FD", "msg": "te lo ganaste  ♡"},
}
ORDER = ["focus", "short", "long"]
DEFAULTS = {"focus": 25, "short": 5, "long": 15, "rounds": 4, "topmost": False}
LIMITS = {"focus": (1, 120), "short": (1, 60), "long": (1, 90), "rounds": (2, 8)}
FONT = "Segoe UI" if sys.platform == "win32" else "Helvetica"
W, H = 340, 500


def enable_crisp_text():
    """En Windows con pantallas escaladas evita que el texto se vea borroso."""
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass


class MochiPomodoro:
    def __init__(self, root):
        self.root = root
        self.scale = max(1.0, root.winfo_fpixels("1i") / 96)
        self.cfg = self.load_settings()
        self.mode = "focus"
        self.done = 0          # pomodoros del ciclo actual
        self.today = 0         # pomodoros completados desde que abriste la app
        self.running = False
        self.remaining = self.cfg["focus"] * 60.0
        self.end_at = 0.0
        self.party_until = 0.0
        self.settings_open = False

        root.title(APP)
        root.configure(bg=COLORS["bg"])
        root.resizable(False, False)
        root.attributes("-topmost", self.cfg["topmost"])
        self.set_icon()

        self.canvas = tk.Canvas(root, width=self.s(W), height=self.s(H), bg=COLORS["bg"],
                                highlightthickness=0, bd=0)
        self.canvas.pack()
        self.settings = tk.Frame(root, bg=COLORS["bg"])
        self.build_settings()
        self.bind_events()
        self.tick()

    # ---------- utilidades ----------
    def s(self, v):
        return int(round(v * self.scale))

    def font(self, px, weight="normal"):
        return (FONT, -self.s(px), weight)

    def pill(self, x1, y1, x2, y2, r, **kw):
        s = self.s
        x1, y1, x2, y2, r = s(x1), s(y1), s(x2), s(y2), s(r)
        pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
               x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
        return self.canvas.create_polygon(pts, smooth=True, **kw)

    def oval(self, cx, cy, rx, ry, **kw):
        s = self.s
        return self.canvas.create_oval(s(cx - rx), s(cy - ry), s(cx + rx), s(cy + ry), **kw)

    def text(self, x, y, txt, **kw):
        return self.canvas.create_text(self.s(x), self.s(y), text=txt, **kw)

    def set_icon(self):
        size = 32
        img = tk.PhotoImage(width=size, height=size)
        for y in range(size):
            row = []
            for x in range(size):
                dx, dy = x - 15.5, y - 17.5
                if dx * dx / 196 + dy * dy / 144 <= 1:
                    row.append(MODES["focus"]["color"])
                elif abs(x - 16) < 4 and 2 <= y <= 6:
                    row.append(COLORS["leaf"])
                else:
                    row.append(COLORS["bg"])
            img.put("{" + " ".join(row) + "}", to=(0, y))
        self.icon = img
        self.root.iconphoto(True, img)

    # ---------- ajustes ----------
    def load_settings(self):
        cfg = dict(DEFAULTS)
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            for k, (lo, hi) in LIMITS.items():
                if isinstance(data.get(k), int):
                    cfg[k] = min(hi, max(lo, data[k]))
            cfg["topmost"] = bool(data.get("topmost", False))
        except (OSError, ValueError):
            pass
        return cfg

    def save_settings(self):
        try:
            SETTINGS_FILE.write_text(json.dumps(self.cfg, indent=2), encoding="utf-8")
        except OSError:
            pass  # carpeta de solo lectura: simplemente no se guarda

    def build_settings(self):
        rows = [("Enfoque (min)", "focus"), ("Descanso (min)", "short"),
                ("Descanso largo (min)", "long"), ("Pomodoros por ciclo", "rounds")]
        self.setting_vars = {}
        for i, (label, key) in enumerate(rows):
            tk.Label(self.settings, text=label, bg=COLORS["bg"], fg=COLORS["ink"],
                     font=self.font(13)).grid(row=i, column=0, sticky="w", padx=(self.s(28), self.s(10)),
                                              pady=self.s(4))
            var = tk.StringVar(value=str(self.cfg[key]))
            self.setting_vars[key] = var
            for col, (sym, step) in enumerate([("−", -1), (None, 0), ("+", 1)], start=1):
                if sym is None:
                    tk.Label(self.settings, textvariable=var, width=3, bg=COLORS["bg"], fg=COLORS["ink"],
                             font=self.font(14, "bold")).grid(row=i, column=col)
                    continue
                b = tk.Label(self.settings, text=sym, width=2, bg=COLORS["track"], fg=COLORS["ink"],
                             font=self.font(14, "bold"), cursor="hand2")
                b.grid(row=i, column=col, padx=self.s(2))
                b.bind("<Button-1>", lambda e, k=key, d=step: self.change_setting(k, d))
        tk.Label(self.settings, text="", bg=COLORS["bg"]).grid(row=len(rows), column=0, pady=self.s(4))

    def change_setting(self, key, delta):
        lo, hi = LIMITS[key]
        self.cfg[key] = min(hi, max(lo, self.cfg[key] + delta))
        self.setting_vars[key].set(str(self.cfg[key]))
        if key == self.mode and not self.running:
            self.remaining = self.cfg[key] * 60.0
        self.save_settings()
        self.render()

    def toggle_settings(self):
        self.settings_open = not self.settings_open
        if self.settings_open:
            self.settings.pack(fill="x")
        else:
            self.settings.pack_forget()
        self.render()

    def toggle_pin(self):
        self.cfg["topmost"] = not self.cfg["topmost"]
        self.root.attributes("-topmost", self.cfg["topmost"])
        self.save_settings()
        self.render()

    # ---------- temporizador ----------
    def total(self):
        return self.cfg[self.mode] * 60.0

    def toggle(self):
        if self.running:
            self.remaining = max(0.0, self.end_at - time.monotonic())
            self.running = False
        else:
            self.end_at = time.monotonic() + self.remaining
            self.running = True
        self.render()

    def reset(self):
        self.running = False
        self.remaining = self.total()
        self.render()

    def set_mode(self, mode):
        self.mode = mode
        self.reset()

    def next_mode(self, completed):
        if self.mode == "focus":
            if completed:
                self.done += 1
                self.today += 1
            return "long" if self.done >= self.cfg["rounds"] else "short"
        if self.mode == "long":
            self.done = 0
        return "focus"

    def skip(self):
        self.set_mode(self.next_mode(completed=False))

    def finish(self):
        self.running = False
        self.party_until = time.monotonic() + 5
        self.set_mode(self.next_mode(completed=True))
        self.alert()

    def alert(self):
        if winsound:
            try:
                winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
            except RuntimeError:
                self.root.bell()
        else:
            self.root.bell()
        self.root.deiconify()
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.after(1500, lambda: self.root.attributes("-topmost", self.cfg["topmost"]))

    def tick(self):
        if self.running:
            self.remaining = max(0.0, self.end_at - time.monotonic())
            if self.remaining <= 0:
                self.finish()
        self.render()
        self.root.after(100 if self.running else 250, self.tick)

    # ---------- dibujo ----------
    def bind_events(self):
        c = self.canvas
        actions = {
            "tab_focus": lambda: self.set_mode("focus"),
            "tab_short": lambda: self.set_mode("short"),
            "tab_long": lambda: self.set_mode("long"),
            "btn_main": self.toggle,
            "btn_reset": self.reset,
            "btn_skip": self.skip,
            "lnk_settings": self.toggle_settings,
            "lnk_pin": self.toggle_pin,
        }
        for tag, fn in actions.items():
            c.tag_bind(tag, "<Button-1>", lambda e, f=fn: f())
            c.tag_bind(tag, "<Enter>", lambda e: c.config(cursor="hand2"))
            c.tag_bind(tag, "<Leave>", lambda e: c.config(cursor=""))
        r = self.root
        r.bind("<space>", lambda e: self.toggle())
        r.bind("<KeyPress-r>", lambda e: self.reset())
        r.bind("<KeyPress-s>", lambda e: self.skip())
        for i, m in enumerate(ORDER, start=1):
            r.bind(f"<KeyPress-{i}>", lambda e, m=m: self.set_mode(m))

    def render(self):
        c = self.canvas
        c.delete("all")
        m = MODES[self.mode]
        now = time.monotonic()

        # pestañas
        x = 18
        for key in ORDER:
            active = key == self.mode
            tag = f"tab_{key}"
            self.pill(x, 18, x + 96, 50, 16, fill=MODES[key]["color"] if active else COLORS["track"],
                      outline="", tags=tag)
            self.text(x + 48, 34, MODES[key]["tab"], fill=COLORS["white"] if active else COLORS["muted"],
                      font=self.font(13, "bold"), tags=tag)
            x += 104

        # anillo de progreso
        cx, cy, rad = 170, 205, 118
        frac = self.remaining / self.total() if self.total() else 0
        self.oval(cx, cy, rad, rad, outline=COLORS["track"], width=self.s(14))
        if frac > 0.001:
            ext = -359.99 * frac
            c.create_arc(self.s(cx - rad), self.s(cy - rad), self.s(cx + rad), self.s(cy + rad),
                         start=90, extent=ext, style="arc", outline=m["color"], width=self.s(14))
            self.oval(cx, cy - rad, 7, 7, fill=m["color"], outline="")
            ang = math.radians(90 + ext)
            hx, hy = cx + rad * math.cos(ang), cy - rad * math.sin(ang)
            self.oval(hx, hy, 11, 11, fill=COLORS["white"], outline=m["color"], width=self.s(4))

        # mochi
        bob = math.sin(now * 4) * 2.5 if self.running else 0
        my = 150 + bob
        self.oval(cx, my + 30, 34, 5, fill=COLORS["track"], outline="")
        self.oval(cx, my, 42, 27, fill=m["soft"], outline=m["color"], width=self.s(2))
        self.oval(cx - 7, my - 30, 8, 4.5, fill=COLORS["leaf"], outline="")
        self.oval(cx + 7, my - 31, 8, 4.5, fill=COLORS["leaf"], outline="")
        c.create_line(self.s(cx), self.s(my - 26), self.s(cx), self.s(my - 34), fill=COLORS["leaf"],
                      width=self.s(2.5), capstyle="round")
        self.oval(cx - 22, my + 6, 7, 4, fill=COLORS["blush"], outline="")
        self.oval(cx + 22, my + 6, 7, 4, fill=COLORS["blush"], outline="")
        party = now < self.party_until
        ink = COLORS["ink"]
        for ex in (cx - 13, cx + 13):
            if self.running and int(now * 10) % 40 != 0:
                self.oval(ex, my - 2, 3.5, 4.5, fill=ink, outline="")
            else:  # ojitos cerrados ^ ^ (en pausa, o parpadeando)
                c.create_line(self.s(ex - 5), self.s(my), self.s(ex), self.s(my - 5), self.s(ex + 5), self.s(my),
                              fill=ink, width=self.s(2), capstyle="round", joinstyle="round")
        c.create_arc(self.s(cx - 7), self.s(my - 1), self.s(cx), self.s(my + 7), start=180, extent=180,
                     style="arc", outline=ink, width=self.s(1.6))
        c.create_arc(self.s(cx), self.s(my - 1), self.s(cx + 7), self.s(my + 7), start=180, extent=180,
                     style="arc", outline=ink, width=self.s(1.6))
        if party:
            for i, (sx, sy) in enumerate([(cx - 62, my - 22), (cx + 60, my - 18), (cx - 52, my + 20), (cx + 54, my + 22)]):
                twinkle = 1 + 0.35 * math.sin(now * 8 + i)
                self.text(sx, sy, "✦", fill=m["color"], font=self.font(14 * twinkle, "bold"))

        # tiempo
        secs = int(math.ceil(self.remaining))
        clock = f"{secs // 60:02d}:{secs % 60:02d}"
        self.text(cx, 228, clock, fill=ink, font=self.font(46, "bold"))
        self.text(cx, 268, "¡terminaste! ♡" if party else m["msg"], fill=COLORS["muted"], font=self.font(13))
        self.root.title(f"{clock} · {APP}" if self.running else APP)

        # puntitos del ciclo
        n = self.cfg["rounds"]
        start = cx - (n - 1) * 10
        for i in range(n):
            filled = i < self.done
            self.oval(start + i * 20, 352, 5, 5, fill=MODES["focus"]["color"] if filled else COLORS["track"],
                      outline="")
        self.text(cx, 374, f"hoy: {self.today} pomodoro{'s' if self.today != 1 else ''}",
                  fill=COLORS["muted"], font=self.font(12))

        # botones
        by = 425
        self.oval(76, by, 24, 24, fill=COLORS["white"], outline=COLORS["track"], width=self.s(2), tags="btn_reset")
        self.text(76, by, "↺", fill=ink, font=self.font(20, "bold"), tags="btn_reset")
        self.pill(114, by - 26, 226, by + 26, 26, fill=m["color"], outline="", tags="btn_main")
        label = "❚❚  pausa" if self.running else "▶  empezar"
        self.text(170, by, label, fill=COLORS["white"], font=self.font(15, "bold"), tags="btn_main")
        self.oval(264, by, 24, 24, fill=COLORS["white"], outline=COLORS["track"], width=self.s(2), tags="btn_skip")
        self.text(264, by, "»", fill=ink, font=self.font(22, "bold"), tags="btn_skip")

        # pie
        self.text(115, 482, "✦ ajustes" + (" ▴" if self.settings_open else " ▾"),
                  fill=ink if self.settings_open else COLORS["muted"], font=self.font(12), tags="lnk_settings")
        pin = "◉ siempre visible" if self.cfg["topmost"] else "○ siempre visible"
        self.text(232, 482, pin, fill=ink if self.cfg["topmost"] else COLORS["muted"], font=self.font(12),
                  tags="lnk_pin")


def main():
    enable_crisp_text()
    root = tk.Tk()
    MochiPomodoro(root)
    root.mainloop()


if __name__ == "__main__":
    main()
