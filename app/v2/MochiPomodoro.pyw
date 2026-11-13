"""
Mochi Pomodoro  -  desktop focus timer
======================================

Version 2.0.0  ·  matcha latte edition

This program is A SINGLE Python FILE that you can read in full.
- It only uses the Python standard library (tkinter, json, time, math,
  datetime, calendar, pathlib).
- It does NOT connect to the internet (no socket, urllib, http or requests).
- It does NOT ask for administrator permissions or touch the Windows registry.
- It saves your data next to this file:
    mochi_settings.json     your flow, minutes and mochi.
    mochi_days.json         the flows you finish each day (the calendar).

Shortcuts:  Space = start/pause   R = reset   S = skip
            1 / 2 / 3 = Focus / Break / Long break
            T / F / M / C = Timer / Flow / Mochi / Calendar
"""

import calendar
import datetime as dt
import json
import math
import sys
import time
import tkinter as tk
from pathlib import Path

try:  # Only exists on Windows; used for the little chime at the end.
    import winsound
except ImportError:
    winsound = None

APP = "Mochi Pomodoro"
VERSION = "2.0.0"
HERE = Path(__file__).resolve().parent
SETTINGS_FILE = HERE / "mochi_settings.json"
DAYS_FILE = HERE / "mochi_days.json"
NOTE_NAME = "animo de tu mochi.txt"
NOTE_TEXT = "ánimo, tú puedes ♡\n\natt: tu mochi pomodoro ✿\n"

# matcha latte palette
C = {
    "bg": "#F7F2EA",          # oat milk
    "card": "#FFFDF9",
    "ink": "#5A4A42",         # latte
    "muted": "#A8988C",
    "faint": "#CFC2B3",
    "track": "#EDE4D6",
    "line": "#E4D8C6",
    "white": "#FFFFFF",
    "matcha": "#8FB07E",
    "matcha_deep": "#6E9160",
    "matcha_soft": "#E3EDDA",
    "sakura": "#EFA3B7",
    "sakura_deep": "#D9879C",
    "sakura_soft": "#FBE6EB",
    "taro": "#B39DDB",
    "blush": "#F6C1CC",
    "leaf": "#8FB07E",
    "honey": "#F3D27A",
}
# key: (name, tagline, body color, outline / accent color)
FLAVORS = {
    "matcha": ("Matcha", "matcha latte · calm and green", "#DDEBCF", "#8FB07E"),
    "sakura": ("Sakura", "cherry blossom · soft and sweet", "#FCE3EA", "#EFA3B7"),
    "taro": ("Taro", "taro milk tea · a little dreamy", "#ECE4F7", "#B39DDB"),
    "hojicha": ("Hojicha", "roasted tea latte · cozy", "#F1E2CF", "#C49A6C"),
    "yuzu": ("Yuzu", "citrus sunshine · bright", "#FBF1C9", "#E0BC4F"),
    "sesame": ("Black sesame", "nutty and grounded", "#E7E3DF", "#8C847E"),
    "milk": ("Milk", "classic daifuku · pure and simple", "#FFFFFF", "#D3C2AC"),
}
TOPPINGS = [("sprout", "sprout"), ("flower", "sakura"), ("bow", "bow"), ("none", "none")]
FLOWS = {
    "pomodoro": {"name": "Mochi Pomodoro", "sub": "25 focus · 5 break · long every 4",
                 "focus": 25, "short": 5, "long": 15, "rounds": 4},
    "deep": {"name": "Deep Flow", "sub": "50 focus · 10 break · long every 3",
             "focus": 50, "short": 10, "long": 20, "rounds": 3},
    "soft": {"name": "Soft Start", "sub": "15 focus · 3 break · for slow days",
             "focus": 15, "short": 3, "long": 10, "rounds": 4},
    "custom": {"name": "Your Flow", "sub": "you choose the minutes"},
}
MODES = {
    "focus": ("Focus", "time to focus  ✿"),
    "short": ("Break", "sip your latte, stretch"),
    "long": ("Long", "you earned it  ♡"),
}
ORDER = ["focus", "short", "long"]
DEFAULTS = {"flow": "pomodoro", "custom_focus": 40, "custom_break": 8, "goal": 4,
            "flavor": "matcha", "topping": "sprout", "topmost": False, "hello": False}
LIMITS = {"custom_focus": (5, 180), "custom_break": (1, 60), "goal": (1, 12)}
STEPS = {"custom_focus": 5, "custom_break": 1, "goal": 1}
FONT = "Segoe UI" if sys.platform == "win32" else "Helvetica"
W, H = 360, 590
MISSED_AFTER = 60  # seconds of focus before a stopped block counts as "not this time"


def enable_crisp_text():
    """On Windows with scaled displays, keeps the text from looking blurry."""
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass


def desktop_dir():
    """The user's Desktop folder (falls back to this program's folder)."""
    if sys.platform == "win32":
        try:
            import ctypes
            buf = ctypes.create_unicode_buffer(260)
            if ctypes.windll.shell32.SHGetFolderPathW(None, 0x10, None, 0, buf) == 0:
                if Path(buf.value).is_dir():
                    return Path(buf.value)
        except Exception:
            pass
    for cand in (Path.home() / "Desktop", Path.home() / "Escritorio"):
        if cand.is_dir():
            return cand
    return HERE


def mix(a, b, t):
    """Blend two #rrggbb colors (t=0 -> a, t=1 -> b)."""
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(ca, cb))


def fmt_minutes(m):
    return f"{m} min" if m < 60 else f"{m // 60}h {m % 60:02d}m"


class MochiPomodoro:
    def __init__(self, root):
        self.root = root
        self.scale = max(1.0, root.winfo_fpixels("1i") / 96)
        self.cfg = self.load_settings()
        self.days = self.load_days()
        self.view = "timer"
        self.mode = "focus"
        self.done = 0           # focus blocks in the current cycle
        self.running = False
        self.remaining = self.total()
        self.end_at = 0.0
        self.party_until = 0.0
        self.toast_text, self.toast_until = "", 0.0
        today = dt.date.today()
        self.cal_y, self.cal_m, self.cal_sel = today.year, today.month, today
        self.actions = {}

        root.title(APP)
        root.configure(bg=C["bg"])
        root.resizable(False, False)
        root.attributes("-topmost", self.cfg["topmost"])
        self.set_icon()

        self.canvas = tk.Canvas(root, width=self.s(W), height=self.s(H), bg=C["bg"],
                                highlightthickness=0, bd=0)
        self.canvas.pack()
        self.bind_events()
        self.tick()

    # ---------- small drawing helpers ----------
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

    def line(self, *pts, **kw):
        return self.canvas.create_line(*[self.s(p) for p in pts], **kw)

    def poly(self, *pts, **kw):
        return self.canvas.create_polygon(*[self.s(p) for p in pts], **kw)

    def text(self, x, y, txt, **kw):
        return self.canvas.create_text(self.s(x), self.s(y), text=txt, **kw)

    def act(self, name, fn):
        """Registers a click action; returns the tags to put on the clickable items."""
        self.actions[name] = fn
        return ("act", "a:" + name)

    def accent(self):
        return FLAVORS[self.cfg["flavor"]][3]

    def mode_color(self, mode):
        flavor = self.cfg["flavor"]
        if mode == "focus":
            return self.accent()
        if mode == "short":
            return C["sakura"] if flavor == "matcha" else C["matcha"]
        return C["matcha"] if flavor == "taro" else C["taro"]

    def set_icon(self):
        size = 32
        body, edge = FLAVORS[self.cfg["flavor"]][2], FLAVORS[self.cfg["flavor"]][3]
        img = tk.PhotoImage(width=size, height=size)
        for y in range(size):
            row = []
            for x in range(size):
                dx, dy = x - 15.5, y - 17.5
                d = dx * dx / 196 + dy * dy / 144
                if d <= 0.78:
                    row.append(body)
                elif d <= 1:
                    row.append(edge)
                elif abs(x - 16) < 4 and 2 <= y <= 6:
                    row.append(C["leaf"])
                else:
                    row.append(C["bg"])
            img.put("{" + " ".join(row) + "}", to=(0, y))
        self.icon = img
        self.root.iconphoto(True, img)

    # ---------- saved data ----------
    def load_settings(self):
        cfg = dict(DEFAULTS)
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return cfg
        if not isinstance(data, dict):
            return cfg
        if "flow" not in data and isinstance(data.get("focus"), int):
            # settings from v1: keep your minutes as "Your Flow"
            if (data.get("focus"), data.get("short")) != (25, 5):
                cfg["flow"] = "custom"
                cfg["custom_focus"] = data["focus"]
                if isinstance(data.get("short"), int):
                    cfg["custom_break"] = data["short"]
        for k, (lo, hi) in LIMITS.items():
            if isinstance(data.get(k), int):
                cfg[k] = data[k]
            cfg[k] = min(hi, max(lo, cfg[k]))
        if data.get("flow") in FLOWS:
            cfg["flow"] = data["flow"]
        if data.get("flavor") in FLAVORS:
            cfg["flavor"] = data["flavor"]
        if data.get("topping") in dict(TOPPINGS):
            cfg["topping"] = data["topping"]
        cfg["topmost"] = bool(data.get("topmost", False))
        cfg["hello"] = bool(data.get("hello", False))
        return cfg

    def save_settings(self):
        try:
            SETTINGS_FILE.write_text(json.dumps(self.cfg, indent=2), encoding="utf-8")
        except OSError:
            pass  # read-only folder: it just doesn't get saved

    def load_days(self):
        try:
            data = json.loads(DAYS_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        days = {}
        if isinstance(data, dict):
            for key, rec in data.items():
                try:
                    dt.date.fromisoformat(key)
                except (TypeError, ValueError):
                    continue
                if isinstance(rec, dict):
                    days[key] = {k: int(rec.get(k, 0)) for k in ("done", "minutes", "missed", "goal")
                                 if isinstance(rec.get(k, 0), (int, float))}
        return days

    def save_days(self):
        try:
            DAYS_FILE.write_text(json.dumps(self.days, indent=1, sort_keys=True), encoding="utf-8")
        except OSError:
            pass

    def today_rec(self):
        key = dt.date.today().isoformat()
        rec = self.days.setdefault(key, {"done": 0, "minutes": 0, "missed": 0})
        rec["goal"] = self.cfg["goal"]
        return rec

    def status(self, date):
        """'met', 'some', 'missed' or None for a calendar day."""
        rec = self.days.get(date.isoformat())
        if not rec:
            return None
        if rec.get("done", 0) >= rec.get("goal", self.cfg["goal"]):
            return "met"
        if rec.get("done", 0) > 0:
            return "some"
        if rec.get("missed", 0) > 0:
            return "missed"
        return None

    def streak(self):
        day = dt.date.today()
        if self.status(day) != "met":
            day -= dt.timedelta(days=1)  # today is still in progress
        n = 0
        while self.status(day) == "met":
            n += 1
            day -= dt.timedelta(days=1)
        return n

    # ---------- flow ----------
    def plan(self):
        if self.cfg["flow"] == "custom":
            br = self.cfg["custom_break"]
            return {"focus": self.cfg["custom_focus"], "short": br, "long": min(60, br * 3), "rounds": 4}
        return FLOWS[self.cfg["flow"]]

    def total(self, mode=None):
        return self.plan()[mode or self.mode] * 60.0

    def flow_changed(self):
        if not self.running:
            self.remaining = self.total()
        self.done = min(self.done, self.plan()["rounds"] - 1)
        self.save_settings()
        self.render()

    def set_flow(self, key):
        self.cfg["flow"] = key
        self.flow_changed()

    def change(self, key, delta):
        lo, hi = LIMITS[key]
        self.cfg[key] = min(hi, max(lo, self.cfg[key] + delta * STEPS[key]))
        if key == "goal":
            today = self.days.get(dt.date.today().isoformat())
            if today:
                today["goal"] = self.cfg["goal"]
                self.save_days()
            self.save_settings()
            self.render()
            return
        self.cfg["flow"] = "custom"  # touching the minutes picks "Your Flow"
        self.flow_changed()

    def set_flavor(self, key):
        self.cfg["flavor"] = key
        self.set_icon()
        self.save_settings()
        self.render()

    def set_topping(self, key):
        self.cfg["topping"] = key
        self.save_settings()
        self.render()

    def toggle_pin(self):
        self.cfg["topmost"] = not self.cfg["topmost"]
        self.root.attributes("-topmost", self.cfg["topmost"])
        self.save_settings()
        self.render()

    def set_view(self, view):
        self.view = view
        if view == "days":
            today = dt.date.today()
            self.cal_y, self.cal_m, self.cal_sel = today.year, today.month, today
        self.render()

    def shift_month(self, delta):
        m = self.cal_m - 1 + delta
        self.cal_y, self.cal_m = self.cal_y + m // 12, m % 12 + 1
        self.render()

    def select_day(self, date):
        self.cal_sel = date
        self.render()

    def show_toast(self, txt, secs=5):
        self.toast_text, self.toast_until = txt, time.monotonic() + secs

    # ---------- timer ----------
    def current_remaining(self):
        return max(0.0, self.end_at - time.monotonic()) if self.running else self.remaining

    def toggle(self):
        if self.running:
            self.remaining = self.current_remaining()
            self.running = False
        else:
            if self.mode == "focus" and not self.cfg["hello"]:
                self.leave_note()
            self.end_at = time.monotonic() + self.remaining
            self.running = True
        self.render()

    def leave_note(self):
        """First focus block ever: a note from your mochi on the Desktop (never overwrites)."""
        self.cfg["hello"] = True
        self.save_settings()
        try:
            path = desktop_dir() / NOTE_NAME
            if not path.exists():
                path.write_text(NOTE_TEXT, encoding="utf-8-sig")
                self.show_toast("psst… a little note is on your desktop ♡", 7)
        except OSError:
            pass

    def abandon(self):
        """Stopping a focus block you had been working on counts as 'not this time'."""
        if self.mode == "focus" and self.total() - self.current_remaining() >= MISSED_AFTER:
            self.today_rec()["missed"] += 1
            self.save_days()

    def switch(self, mode):
        self.mode = mode
        self.running = False
        self.remaining = self.total()
        self.render()

    def reset(self):
        self.abandon()
        self.switch(self.mode)

    def set_mode(self, mode):
        self.abandon()
        self.switch(mode)

    def next_mode(self):
        if self.mode == "focus":
            return "long" if self.done >= self.plan()["rounds"] else "short"
        if self.mode == "long":
            self.done = 0
        return "focus"

    def skip(self):
        self.abandon()
        self.switch(self.next_mode())

    def finish(self):
        self.running = False
        self.party_until = time.monotonic() + 5
        if self.mode == "focus":
            self.done += 1
            rec = self.today_rec()
            rec["done"] += 1
            rec["minutes"] += self.plan()["focus"]
            self.save_days()
            if rec["done"] == rec["goal"]:
                self.show_toast("daily goal reached! today is matcha green ✿", 7)
        self.switch(self.next_mode())
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
            self.remaining = self.current_remaining()
            if self.remaining <= 0:
                self.finish()
        self.render()
        lively = self.running or self.view == "mochi" or time.monotonic() < self.party_until
        self.root.after(100 if lively else 250, self.tick)

    # ---------- events ----------
    def bind_events(self):
        c = self.canvas
        c.bind("<Button-1>", self.on_click)
        c.bind("<Motion>", self.on_motion)
        r = self.root
        r.bind("<space>", lambda e: self.toggle())
        r.bind("<KeyPress-r>", lambda e: self.reset())
        r.bind("<KeyPress-s>", lambda e: self.skip())
        for i, m in enumerate(ORDER, start=1):
            r.bind(f"<KeyPress-{i}>", lambda e, m=m: self.set_mode(m))
        for key, view in (("t", "timer"), ("f", "flow"), ("m", "mochi"), ("c", "days")):
            r.bind(f"<KeyPress-{key}>", lambda e, v=view: self.set_view(v))

    def on_click(self, _event):
        items = self.canvas.find_withtag("current")
        if not items:
            return
        for tag in self.canvas.gettags(items[0]):
            if tag.startswith("a:") and tag[2:] in self.actions:
                self.actions[tag[2:]]()
                return

    def on_motion(self, _event):
        items = self.canvas.find_withtag("current")
        hand = bool(items) and "act" in self.canvas.gettags(items[0])
        self.canvas.config(cursor="hand2" if hand else "")

    # ---------- drawing ----------
    def render(self):
        self.canvas.delete("all")
        self.actions = {}
        {"timer": self.draw_timer, "flow": self.draw_flow,
         "mochi": self.draw_mochi_view, "days": self.draw_days}[self.view]()
        self.draw_nav()
        if time.monotonic() < self.toast_until:
            self.pill(30, 488, 330, 510, 11, fill=C["card"], outline=C["line"])
            self.text(180, 498, self.toast_text, fill=C["ink"], font=self.font(12))
        clock = self.clock_text()
        self.root.title(f"{clock} · {APP}" if self.running else APP)

    def clock_text(self):
        secs = int(math.ceil(self.current_remaining()))
        return f"{secs // 60:02d}:{secs % 60:02d}"

    def heading(self, title, sub):
        self.text(180, 34, title, fill=C["ink"], font=self.font(20, "bold"))
        if sub:
            self.text(180, 60, sub, fill=C["muted"], font=self.font(12))

    def draw_mochi(self, cx, cy, k=1.0, awake=False, party=False, flavor=None, topping=None):
        c = self.canvas
        now = time.monotonic()
        _, _, body, edge = FLAVORS[flavor or self.cfg["flavor"]]
        topping = topping or self.cfg["topping"]
        ink = C["ink"]

        def e(x, y, rx, ry, **kw):
            return self.oval(cx + x * k, cy + y * k, rx * k, ry * k, **kw)

        def p(x, y):
            return cx + x * k, cy + y * k

        e(0, 30, 34, 5, fill=C["track"], outline="")
        e(0, 0, 42, 27, fill=body, outline=edge, width=self.s(2 * k))
        # topping
        if topping == "sprout":
            e(-7, -30, 8, 4.5, fill=C["leaf"], outline="")
            e(7, -31, 8, 4.5, fill=C["leaf"], outline="")
            self.line(*p(0, -26), *p(0, -34), fill=C["leaf"], width=self.s(2.5 * k), capstyle="round")
        elif topping == "flower":
            fx, fy = 16, -24
            for i in range(5):
                a = math.radians(i * 72 - 90)
                e(fx + 5.5 * math.cos(a), fy + 5.5 * math.sin(a), 4.2, 4.2, fill="#F7B9C8", outline="")
            e(fx, fy, 2.4, 2.4, fill=C["honey"], outline="")
        elif topping == "bow":
            bx, by = -15, -23
            self.poly(*p(bx, by), *p(bx - 11, by - 7), *p(bx - 11, by + 7), fill=C["sakura"], outline="")
            self.poly(*p(bx, by), *p(bx + 11, by - 7), *p(bx + 11, by + 7), fill=C["sakura"], outline="")
            e(bx, by, 3.2, 3.2, fill=C["sakura_deep"], outline="")
        # cheeks
        e(-22, 6, 7, 4, fill=C["blush"], outline="")
        e(22, 6, 7, 4, fill=C["blush"], outline="")
        # eyes: open while working (with a blink), ^ ^ when resting
        for ex in (-13, 13):
            if awake and int(now * 10) % 40 != 0:
                e(ex, -2, 3.5, 4.5, fill=ink, outline="")
            else:
                self.line(*p(ex - 5, 0), *p(ex, -5), *p(ex + 5, 0), fill=ink, width=self.s(2 * k),
                          capstyle="round", joinstyle="round")
        # mouth
        for x0 in (-7, 0):
            x1, y1 = p(x0, -1)
            x2, y2 = p(x0 + 7, 7)
            c.create_arc(self.s(x1), self.s(y1), self.s(x2), self.s(y2), start=180, extent=180,
                         style="arc", outline=ink, width=self.s(1.6 * k))
        if party:
            for i, (sx, sy) in enumerate([(-62, -22), (60, -18), (-52, 20), (54, 22)]):
                twinkle = 1 + 0.35 * math.sin(now * 8 + i)
                self.text(cx + sx * k, cy + sy * k, "✦", fill=edge, font=self.font(14 * twinkle, "bold"))

    def stepper(self, y, label, key, value, active=True):
        ink = C["ink"] if active else C["muted"]
        self.text(36, y, label, anchor="w", fill=ink, font=self.font(13))
        for x, sym, d in ((236, "−", -1), (316, "+", 1)):
            tags = self.act(f"step_{key}_{d}", lambda k=key, d=d: self.change(k, d))
            self.oval(x, y, 13, 13, fill=C["white"], outline=C["track"], width=self.s(2), tags=tags)
            self.text(x, y - 1, sym, fill=C["ink"], font=self.font(15, "bold"), tags=tags)
        self.text(276, y, str(value), fill=ink, font=self.font(15, "bold"))

    # timer view
    def draw_timer(self):
        c = self.canvas
        now = time.monotonic()
        col = self.mode_color(self.mode)
        ink = C["ink"]
        x = 22
        for key in ORDER:
            active = key == self.mode
            tags = self.act(f"tab_{key}", lambda k=key: self.set_mode(k))
            self.pill(x, 16, x + 100, 48, 16, fill=self.mode_color(key) if active else C["track"],
                      outline="", tags=tags)
            self.text(x + 50, 32, MODES[key][0], fill=C["white"] if active else C["muted"],
                      font=self.font(13, "bold"), tags=tags)
            x += 108
        plan = self.plan()
        tags = self.act("chip_flow", lambda: self.set_view("flow"))
        label = f"≋  {FLOWS[self.cfg['flow']]['name']} · {plan['focus']} / {plan['short']}"
        self.text(180, 72, label, fill=C["muted"], font=self.font(12), tags=tags)

        cx, cy, rad = 180, 250, 110
        frac = self.current_remaining() / self.total() if self.total() else 0
        self.oval(cx, cy, rad, rad, outline=C["track"], width=self.s(14))
        if frac > 0.001:
            ext = -359.99 * frac
            c.create_arc(self.s(cx - rad), self.s(cy - rad), self.s(cx + rad), self.s(cy + rad),
                         start=90, extent=ext, style="arc", outline=col, width=self.s(14))
            self.oval(cx, cy - rad, 7, 7, fill=col, outline="")
            ang = math.radians(90 + ext)
            hx, hy = cx + rad * math.cos(ang), cy - rad * math.sin(ang)
            self.oval(hx, hy, 11, 11, fill=C["white"], outline=col, width=self.s(4))

        party = now < self.party_until
        bob = math.sin(now * 4) * 2.5 if self.running else 0
        self.draw_mochi(cx, 196 + bob, awake=self.running, party=party)

        self.text(cx, 266, self.clock_text(), fill=ink, font=self.font(46, "bold"))
        msg = "you did it! ♡" if party else MODES[self.mode][1]
        self.text(cx, 306, msg, fill=C["muted"], font=self.font(12.5))

        n = plan["rounds"]
        start = cx - (n - 1) * 10
        for i in range(n):
            self.oval(start + i * 20, 384, 5, 5, fill=self.mode_color("focus") if i < self.done else C["track"],
                      outline="")
        rec = self.days.get(dt.date.today().isoformat(), {})
        done, goal = rec.get("done", 0), self.cfg["goal"]
        tags = self.act("today", lambda: self.set_view("days"))
        self.text(cx, 406, f"today: {done} / {goal} flows" + ("  ✿" if done >= goal else ""),
                  fill=C["matcha_deep"] if done >= goal else C["muted"], font=self.font(12), tags=tags)

        by = 458
        tags = self.act("reset", self.reset)
        self.oval(96, by, 24, 24, fill=C["white"], outline=C["track"], width=self.s(2), tags=tags)
        self.text(96, by, "↺", fill=ink, font=self.font(20, "bold"), tags=tags)
        tags = self.act("main", self.toggle)
        self.pill(124, by - 26, 236, by + 26, 26, fill=col, outline="", tags=tags)
        self.text(180, by, "❚❚  pause" if self.running else "▶  start", fill=C["white"],
                  font=self.font(15, "bold"), tags=tags)
        tags = self.act("skip", self.skip)
        self.oval(264, by, 24, 24, fill=C["white"], outline=C["track"], width=self.s(2), tags=tags)
        self.text(264, by, "»", fill=ink, font=self.font(22, "bold"), tags=tags)

    # flow view
    def draw_flow(self):
        self.heading("choose your flow", "how do you want to focus today?")
        acc = self.accent()
        y = 84
        for key, info in FLOWS.items():
            sel = key == self.cfg["flow"]
            tags = self.act(f"flow_{key}", lambda k=key: self.set_flow(k))
            self.pill(22, y, 338, y + 58, 18, fill=C["card"], outline=acc if sel else C["line"],
                      width=self.s(2 if sel else 1), tags=tags)
            mins = self.cfg["custom_focus"] if key == "custom" else info["focus"]
            self.oval(52, y + 29, 19, 19, fill=mix(acc, C["white"], .75) if sel else C["track"],
                      outline="", tags=tags)
            self.text(52, y + 29, str(mins), fill=ink_or(acc, sel), font=self.font(13, "bold"), tags=tags)
            sub = info["sub"]
            if key == "custom":
                sub = f"{self.cfg['custom_focus']} focus · {self.cfg['custom_break']} break · you choose"
            self.text(84, y + 20, info["name"], anchor="w", fill=C["ink"], font=self.font(14, "bold"), tags=tags)
            self.text(84, y + 40, sub, anchor="w", fill=C["muted"], font=self.font(11.5), tags=tags)
            if sel:
                self.oval(314, y + 29, 10, 10, fill=acc, outline="", tags=tags)
                self.text(314, y + 29, "✓", fill=C["white"], font=self.font(11, "bold"), tags=tags)
            else:
                self.oval(314, y + 29, 10, 10, fill="", outline=C["track"], width=self.s(2), tags=tags)
            y += 66
        custom = self.cfg["flow"] == "custom"
        self.stepper(368, "your focus (min)", "custom_focus", self.cfg["custom_focus"], custom)
        self.stepper(402, "your break (min)", "custom_break", self.cfg["custom_break"], custom)
        self.stepper(436, "daily goal (flows)", "goal", self.cfg["goal"])
        tags = self.act("pin", self.toggle_pin)
        pin = "◉  always on top" if self.cfg["topmost"] else "○  always on top"
        self.text(180, 470, pin, fill=C["ink"] if self.cfg["topmost"] else C["muted"],
                  font=self.font(12), tags=tags)

    # mochi view
    def draw_mochi_view(self):
        self.heading("your mochi", "pick a flavor and a topping")
        name, tagline, body, edge = FLAVORS[self.cfg["flavor"]]
        self.oval(180, 160, 78, 78, fill=mix(body, C["bg"], .35), outline="")
        bob = math.sin(time.monotonic() * 3) * 2
        self.draw_mochi(180, 168 + bob, k=1.55, awake=True)
        self.text(180, 262, name.lower(), fill=C["ink"], font=self.font(17, "bold"))
        self.text(180, 284, tagline, fill=C["muted"], font=self.font(12))

        self.text(36, 320, "flavor", anchor="w", fill=C["muted"], font=self.font(12, "bold"))
        for i, key in enumerate(FLAVORS):
            x = 48 + i * 44
            sel = key == self.cfg["flavor"]
            tags = self.act(f"flavor_{key}", lambda k=key: self.set_flavor(k))
            if sel:
                self.oval(x, 352, 20, 20, fill="", outline=FLAVORS[key][3], width=self.s(2), tags=tags)
            self.oval(x, 352, 15, 15, fill=FLAVORS[key][2], outline=FLAVORS[key][3],
                      width=self.s(2), tags=tags)

        self.text(36, 394, "topping", anchor="w", fill=C["muted"], font=self.font(12, "bold"))
        for i, (key, label) in enumerate(TOPPINGS):
            x1 = 24 + i * 80
            sel = key == self.cfg["topping"]
            tags = self.act(f"top_{key}", lambda k=key: self.set_topping(k))
            self.pill(x1, 412, x1 + 72, 442, 15, fill=edge if sel else C["track"], outline="", tags=tags)
            self.text(x1 + 36, 427, label, fill=C["white"] if sel else C["muted"],
                      font=self.font(12, "bold"), tags=tags)
        self.text(180, 470, "your mochi keeps you company in the timer ✿", fill=C["muted"],
                  font=self.font(11.5))

    # calendar view
    def draw_days(self):
        self.heading("your flow days", None)
        y, m = self.cal_y, self.cal_m
        self.text(180, 70, f"{calendar.month_name[m].lower()} {y}", fill=C["ink"], font=self.font(14, "bold"))
        for x, sym, d in ((70, "‹", -1), (290, "›", 1)):
            tags = self.act(f"month_{d}", lambda d=d: self.shift_month(d))
            self.oval(x, 70, 13, 13, fill=C["white"], outline=C["track"], width=self.s(2), tags=tags)
            self.text(x, 68, sym, fill=C["ink"], font=self.font(16, "bold"), tags=tags)
        for i, wd in enumerate("MTWTFSS"):
            self.text(36 + i * 48, 104, wd, fill=C["muted"], font=self.font(11, "bold"))

        today = dt.date.today()
        for r, week in enumerate(calendar.Calendar(0).monthdayscalendar(y, m)):
            for col, d in enumerate(week):
                if not d:
                    continue
                date = dt.date(y, m, d)
                x, yy = 36 + col * 48, 136 + r * 42
                st = self.status(date)
                fill, fg = "", (C["faint"] if date > today else C["muted"])
                if st == "met":
                    fill, fg = C["matcha"], C["white"]
                elif st == "some":
                    fill, fg = C["matcha_soft"], C["matcha_deep"]
                elif st == "missed":
                    fill, fg = C["sakura_soft"], C["sakura_deep"]
                outline, width = "", 0
                if date == self.cal_sel:
                    outline, width = self.accent(), 2
                elif date == today:
                    outline, width = C["ink"], 1.5
                tags = self.act(f"day_{date}", lambda dd=date: self.select_day(dd))
                self.oval(x, yy, 16, 16, fill=fill or C["bg"], outline=outline,
                          width=self.s(width) if width else 0, tags=tags)
                self.text(x, yy, str(d), fill=fg, font=self.font(12, "bold" if st else "normal"), tags=tags)

        sel = self.cal_sel
        rec = self.days.get(sel.isoformat())
        when = "today" if sel == today else f"{calendar.month_abbr[sel.month].lower()} {sel.day}"
        if rec and (rec.get("done") or rec.get("missed")):
            goal = rec.get("goal", self.cfg["goal"])
            detail = f"{when} · {rec.get('done', 0)} of {goal} flows · {fmt_minutes(rec.get('minutes', 0))}"
            detail += {"met": "  ✿", "missed": " · tomorrow ♡"}.get(self.status(sel), "")
        elif sel > today:
            detail = f"{when} · a fresh page"
        else:
            detail = f"{when} · no flows yet" if sel == today else f"{when} · a rest day"
        self.text(180, 398, detail, fill=C["ink"], font=self.font(12.5))

        for x, fill, label in ((40, C["matcha"], "goal reached"), (150, C["matcha_soft"], "some flow"),
                               (252, C["sakura_soft"], "not this time")):
            self.oval(x, 430, 7, 7, fill=fill, outline="")
            self.text(x + 12, 430, label, anchor="w", fill=C["muted"], font=self.font(11))

        prefix = f"{y:04d}-{m:02d}"
        month = [r for k, r in self.days.items() if k.startswith(prefix)]
        flows = sum(r.get("done", 0) for r in month)
        mins = sum(r.get("minutes", 0) for r in month)
        streak = self.streak()
        self.text(180, 466, f"this month: {flows} flows · {fmt_minutes(mins)}   ·   streak: {streak} "
                            f"day{'s' if streak != 1 else ''} ✿", fill=C["muted"], font=self.font(11.5))

    # bottom navigation
    def draw_nav(self):
        self.line(24, 518, 336, 518, fill=C["line"], width=self.s(1))
        acc = self.accent()
        for i, (view, label) in enumerate((("timer", "timer"), ("flow", "flow"),
                                           ("mochi", "mochi"), ("days", "days"))):
            x = 45 + i * 90
            on = view == self.view
            col = C["ink"] if on else C["muted"]
            tags = self.act(f"view_{view}", lambda v=view: self.set_view(v))
            self.pill(x - 38, 528, x + 38, 580, 18, fill=mix(acc, C["white"], .72) if on else C["bg"],
                      outline="", tags=tags)
            self.nav_icon(view, x, 545, col, tags)
            self.text(x, 567, label, fill=col, font=self.font(11, "bold" if on else "normal"), tags=tags)

    def nav_icon(self, view, x, y, col, tags):
        w = self.s(1.8)
        if view == "timer":
            self.oval(x, y, 8, 8, outline=col, width=w, tags=tags)
            self.line(x, y, x, y - 5, x + 4, y, fill=col, width=w, capstyle="round", tags=tags)
        elif view == "flow":
            for dy in (-5, 0, 5):
                self.line(x - 9, y + dy, x - 4, y + dy - 2.5, x + 1, y + dy, x + 5, y + dy + 2.5, x + 9, y + dy,
                          fill=col, width=w, smooth=True, capstyle="round", tags=tags)
        elif view == "mochi":
            self.oval(x, y + 1, 10, 7, outline=col, width=w, tags=tags)
            self.oval(x - 3, y - 8, 3, 1.8, fill=col, outline="", tags=tags)
            self.oval(x + 3, y - 8, 3, 1.8, fill=col, outline="", tags=tags)
        else:
            self.pill(x - 9, y - 8, x + 9, y + 9, 3, fill="", outline=col, width=w, tags=tags)
            self.line(x - 9, y - 3, x + 9, y - 3, fill=col, width=w, tags=tags)
            for dx in (-4, 0, 4):
                self.oval(x + dx, y + 3, 1.2, 1.2, fill=col, outline="", tags=tags)


def ink_or(color, on):
    return mix(color, "#000000", .25) if on else C["muted"]


def main():
    enable_crisp_text()
    root = tk.Tk()
    MochiPomodoro(root)
    root.mainloop()


if __name__ == "__main__":
    main()
