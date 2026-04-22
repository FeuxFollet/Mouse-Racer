import os
import csv
import tkinter as tk
from tkinter import ttk, font as tkfont
import math

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Theme ─────────────────────────────────────────────────────────────────────
BG        = "#0c0d10"
BG2       = "#12141a"
PANEL     = "#16181f"
BORDER    = "#2d3041"
RED       = "#dc2828"
RED_DIM   = "#821212"
CYAN      = "#3cc8e6"
CYAN_DIM  = "#194f5f"
NEON      = "#64e650"
GOLD      = "#ffc328"
WHITE     = "#f0f0f5"
DIM       = "#64687a"
STRIPE    = "#1e2028"

STATS_DIR = os.path.join(os.getcwd(), "statistics")

# matplotlib dark theme ─────────────────────────────────────────────────────
plt.rcParams.update({
    "figure.facecolor":  BG2,
    "axes.facecolor":    PANEL,
    "axes.edgecolor":    BORDER,
    "axes.labelcolor":   DIM,
    "axes.titlecolor":   WHITE,
    "xtick.color":       DIM,
    "ytick.color":       DIM,
    "grid.color":        STRIPE,
    "grid.alpha":        0.6,
    "text.color":        WHITE,
    "font.family":       "monospace",
    "figure.dpi":        96,
})


# CSV loaders ───────────────────────────────────────────────────────────────
def load_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# Stats calculators ─────────────────────────────────────────────────────────
def ms_fmt(ms):
    if ms is None: return "--:--.--"
    ms = int(ms)
    m  = ms // 60000
    s  = (ms % 60000) // 1000
    cs = (ms % 1000)  // 10
    return f"{m}:{s:02d}.{cs:02d}"


def calc_lap_stats(laps_rows):
    """Return dict of summary stats from lap_checkpoints.csv."""
    if not laps_rows:
        return None

    lap_finish = {}
    all_splits = []

    for row in laps_rows:
        lap    = int(row["lap"])
        cp     = int(row["checkpoint"])
        rt     = int(row["race_time_ms"])
        split  = int(row["split_ms"])
        all_splits.append(split)

        # The last checkpoint in each lap
        if lap not in lap_finish or cp > lap_finish[lap][1]:
            lap_finish[lap] = (rt, cp, split)

    # Reconstruct per-lap total time
    sorted_laps = sorted(lap_finish.keys())
    lap_times   = []
    prev_rt     = 0
    for lap in sorted_laps:
        rt, _, _ = lap_finish[lap]
        lap_times.append(rt - prev_rt)
        prev_rt = rt

    total_ms     = prev_rt
    avg_lap_ms   = sum(lap_times) / len(lap_times) if lap_times else 0
    min_lap_ms   = min(lap_times) if lap_times else 0
    max_lap_ms   = max(lap_times) if lap_times else 0
    avg_split_ms = sum(all_splits) / len(all_splits) if all_splits else 0

    return {
        "total":         total_ms,
        "avg_lap":       avg_lap_ms,
        "avg_checkpoint":avg_split_ms,
        "min_lap":       min_lap_ms,
        "max_lap":       max_lap_ms,
        "lap_times":     lap_times,
    }


def calc_offroad_stats(offroad_rows):
    if not offroad_rows:
        return None
    durations = [int(r["duration_ms"]) for r in offroad_rows]
    return {
        "count":   len(durations),
        "avg_ms":  sum(durations) / len(durations),
        "min_ms":  min(durations),
        "max_ms":  max(durations),
        "total_ms":sum(durations),
    }


def calc_speed_stats(speed_rows):
    if not speed_rows:
        return None
    speeds = [float(r["speed_kmh"]) for r in speed_rows]
    return {
        "top":  max(speeds),
        "avg":  sum(speeds) / len(speeds),
        "speeds": speeds,
        "times":  [float(r["elapsed_s"]) for r in speed_rows],
    }


# Tkinter helpers ───────────────────────────────────────────────────────────
def styled_label(parent, text, fg=WHITE, size=12, bold=False, **kw):
    weight = "bold" if bold else "normal"
    return tk.Label(parent, text=text, fg=fg, bg=parent["bg"],
                    font=("Consolas", size, weight), **kw)


def build_table(parent, columns, rows, col_widths=None):
    """
    Build a ttk.Treeview table inside parent.
    columns – list of header strings
    rows    – list of tuples
    """
    style = ttk.Style()
    style.theme_use("default")
    style.configure("Stats.Treeview",
                    background=PANEL, foreground=WHITE,
                    fieldbackground=PANEL, borderwidth=0,
                    rowheight=28, font=("Consolas", 11))
    style.configure("Stats.Treeview.Heading",
                    background=BG2, foreground=CYAN,
                    relief="flat", font=("Consolas", 11, "bold"))
    style.map("Stats.Treeview",
              background=[("selected", RED_DIM)],
              foreground=[("selected", WHITE)])
    style.map("Stats.Treeview.Heading", relief=[("active", "flat")])

    frame = tk.Frame(parent, bg=BORDER, padx=1, pady=1)
    tv    = ttk.Treeview(frame, columns=columns, show="headings",
                         style="Stats.Treeview",
                         height=len(rows))
    for i, col in enumerate(columns):
        w = (col_widths[i] if col_widths else 160)
        tv.heading(col, text=col)
        tv.column(col, width=w, anchor="center", stretch=False)

    for j, row in enumerate(rows):
        tag = "even" if j % 2 == 0 else "odd"
        tv.insert("", "end", values=row, tags=(tag,))

    tv.tag_configure("even", background=PANEL)
    tv.tag_configure("odd",  background=BG2)
    tv.pack(fill="both", expand=True)
    return frame


# Chart builders ────────────────────────────────────────────────────────────
def build_pie(parent, offroad_stats, lap_stats):
    fig, ax = plt.subplots(figsize=(4.2, 3.4))

    total_race_ms = lap_stats["total"] if lap_stats else 0
    off_ms        = offroad_stats["total_ms"] if offroad_stats else 0
    on_ms         = max(0, total_race_ms - off_ms)

    if total_race_ms == 0:
        ax.text(0.5, 0.5, "no data", ha="center", va="center", color=DIM)
    else:
        sizes  = [on_ms, off_ms]
        labels = ["On Road", "Off Road"]
        colors = [CYAN, RED]
        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, colors=colors,
            autopct="%1.1f%%", startangle=90,
            wedgeprops={"linewidth": 1.5, "edgecolor": BG},
            textprops={"color": WHITE, "fontsize": 10},
        )
        for at in autotexts:
            at.set_fontsize(9)
            at.set_color(BG)
        ax.set_title("On-Road vs Off-Road Time", pad=10, fontsize=11, color=WHITE)

    fig.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    return canvas.get_tk_widget()


def build_line(parent, speed_stats):
    fig, ax = plt.subplots(figsize=(5.8, 3.4))

    if not speed_stats:
        ax.text(0.5, 0.5, "no data", ha="center", va="center", color=DIM,
                transform=ax.transAxes)
    else:
        t = speed_stats["times"]
        s = speed_stats["speeds"]
        ax.plot(t, s, color=NEON, linewidth=1.6, zorder=3)
        ax.fill_between(t, s, alpha=0.12, color=NEON)
        ax.axhline(speed_stats["avg"], color=GOLD, linewidth=1,
                   linestyle="--", label=f"avg {speed_stats['avg']:.1f} km/h")
        ax.set_xlabel("Elapsed (s)")
        ax.set_ylabel("Speed (km/h)")
        ax.set_title("Speed Over Time", fontsize=11)
        ax.grid(True, axis="y")
        ax.legend(fontsize=9, facecolor=PANEL, edgecolor=BORDER, labelcolor=GOLD)

    fig.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    return canvas.get_tk_widget()


def build_histogram(parent, speed_stats):
    fig, ax = plt.subplots(figsize=(5.8, 3.4))

    if not speed_stats:
        ax.text(0.5, 0.5, "no data", ha="center", va="center", color=DIM,
                transform=ax.transAxes)
    else:
        speeds  = speed_stats["speeds"]
        # Each sample = 1 second
        max_spd = max(speeds) if speeds else 1
        bins    = range(0, int(max_spd) + 15, 10)   # 10 km/h wide bands

        # Build manual histogram
        hist_s  = [0] * (len(list(bins)) - 1)
        edges   = list(bins)
        for sp in speeds:
            for i in range(len(edges) - 1):
                if edges[i] <= sp < edges[i + 1]:
                    hist_s[i] += 1
                    break

        bar_x = [(edges[i] + edges[i+1]) / 2 for i in range(len(edges)-1)]
        widths = [edges[i+1] - edges[i] - 2 for i in range(len(edges)-1)]

        bars = ax.bar(bar_x, hist_s, width=widths,
                      color=CYAN, edgecolor=BG, linewidth=0.8, zorder=3)
        # Colour the tallest bar red
        if hist_s:
            peak_i = hist_s.index(max(hist_s))
            bars[peak_i].set_facecolor(RED)

        ax.set_xlabel("Speed (km/h)")
        ax.set_ylabel("Time (s)")
        ax.set_title("Time Spent at Each Speed", fontsize=11)
        ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        ax.grid(True, axis="y")

    fig.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    return canvas.get_tk_widget()


# Main window ───────────────────────────────────────────────────────────────
class StatsViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MOUSE RACER  —  Match Statistics")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.minsize(900, 620)

        self._build_header()
        self._build_selector()
        self._build_notebook()

        self._matches = self._scan_matches()
        self._populate_selector()

    # header ────────────────────────────────────────────────────────────────
    def _build_header(self):
        bar = tk.Frame(self, bg=BG2, height=54)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        tk.Label(bar, text="MOUSE", fg=RED,  bg=BG2,
                 font=("Consolas", 22, "bold")).pack(side="left", padx=(20, 0), pady=10)
        tk.Label(bar, text="RACER", fg=CYAN, bg=BG2,
                 font=("Consolas", 22, "bold")).pack(side="left", padx=(6, 0), pady=10)
        tk.Label(bar, text="// MATCH STATISTICS", fg=DIM, bg=BG2,
                 font=("Consolas", 13)).pack(side="left", padx=14, pady=10)

        # thin accent line
        tk.Frame(self, bg=RED, height=2).pack(fill="x")

    # match selector ────────────────────────────────────────────────────────
    def _build_selector(self):
        bar = tk.Frame(self, bg=BG2, pady=8)
        bar.pack(fill="x", padx=0)

        tk.Label(bar, text="MATCH", fg=DIM, bg=BG2,
                 font=("Consolas", 10, "bold")).pack(side="left", padx=(16, 6))

        self._match_var = tk.StringVar()
        style = ttk.Style()
        style.configure("Sel.TCombobox", fieldbackground=PANEL,
                         background=PANEL, foreground=WHITE,
                         selectbackground=RED_DIM, font=("Consolas", 10))

        self._combo = ttk.Combobox(bar, textvariable=self._match_var,
                                   style="Sel.TCombobox", state="readonly",
                                   width=42, font=("Consolas", 10))
        self._combo.pack(side="left", padx=4)
        self._combo.bind("<<ComboboxSelected>>", lambda _: self._load())

        tk.Button(bar, text="⟳  REFRESH", fg=CYAN, bg=PANEL,
                  activeforeground=WHITE, activebackground=RED_DIM,
                  relief="flat", cursor="hand2", font=("Consolas", 10),
                  padx=10, command=self._refresh).pack(side="left", padx=8)

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

    # notebook ──────────────────────────────────────────────────────────────
    def _build_notebook(self):
        style = ttk.Style()
        style.configure("Dark.TNotebook",        background=BG, borderwidth=0)
        style.configure("Dark.TNotebook.Tab",
                        background=BG2, foreground=DIM,
                        padding=[16, 6], font=("Consolas", 11, "bold"))
        style.map("Dark.TNotebook.Tab",
                  background=[("selected", PANEL)],
                  foreground=[("selected", CYAN)])

        self._nb = ttk.Notebook(self, style="Dark.TNotebook")
        self._nb.pack(fill="both", expand=True, padx=0, pady=0)

        self._tab_tables = tk.Frame(self._nb, bg=BG)
        self._tab_charts = tk.Frame(self._nb, bg=BG)
        self._nb.add(self._tab_tables, text="  SUMMARY  ")
        self._nb.add(self._tab_charts, text="  CHARTS  ")

        self._show_placeholder(self._tab_tables)
        self._show_placeholder(self._tab_charts)

    def _show_placeholder(self, parent):
        for w in parent.winfo_children():
            w.destroy()
        tk.Label(parent, text="Select a match above to view statistics.",
                 fg=DIM, bg=BG, font=("Consolas", 13)).pack(expand=True)

    # match scanning ────────────────────────────────────────────────────────
    def _scan_matches(self):
        if not os.path.isdir(STATS_DIR):
            return []
        entries = []
        for name in sorted(os.listdir(STATS_DIR), reverse=True):
            full = os.path.join(STATS_DIR, name)
            if os.path.isdir(full):
                entries.append((name, full))
        return entries

    def _populate_selector(self):
        names = [m[0] for m in self._matches]
        self._combo["values"] = names
        if names:
            self._combo.current(0)
            self._load()

    def _refresh(self):
        self._matches = self._scan_matches()
        self._populate_selector()

    # Load and Render ─────────────────────────────────────────────────────────
    def _load(self):
        sel = self._match_var.get()
        folder = next((p for n, p in self._matches if n == sel), None)
        if not folder:
            return

        laps_rows    = load_csv(os.path.join(folder, "lap_checkpoints.csv"))
        offroad_rows = load_csv(os.path.join(folder, "off_road.csv"))
        speed_rows   = load_csv(os.path.join(folder, "speed_time.csv"))

        lap_stats    = calc_lap_stats(laps_rows)
        offroad_stats= calc_offroad_stats(offroad_rows)
        speed_stats  = calc_speed_stats(speed_rows)

        self._render_tables(lap_stats, offroad_stats, speed_stats)
        self._render_charts(lap_stats, offroad_stats, speed_stats)

    # Summary tab ───────────────────────────────────────────────────────────
    def _render_tables(self, lap, off, spd):
        tab = self._tab_tables
        for w in tab.winfo_children():
            w.destroy()

        pad = dict(padx=20, pady=10)

        # Label helper ──────────────────────────────────────────────
        def section(text, color=CYAN):
            tk.Label(tab, text=text, fg=color, bg=BG,
                     font=("Consolas", 12, "bold"),
                     anchor="w").pack(fill="x", padx=20, pady=(14, 2))
            tk.Frame(tab, bg=color, height=1).pack(fill="x", padx=20)

        # Lap times ──────────────────────────────────────────────────────
        section("LAP TIMES", CYAN)
        if lap:
            rows = [
                ("Total race time",          ms_fmt(lap["total"])),
                ("Average lap time",          ms_fmt(lap["avg_lap"])),
                ("Average checkpoint split",  ms_fmt(lap["avg_checkpoint"])),
                ("Fastest lap",               ms_fmt(lap["min_lap"])),
                ("Slowest lap",               ms_fmt(lap["max_lap"])),
            ]
        else:
            rows = [("No data", "—")] * 5

        build_table(tab,
                    columns=["Metric", "Value"],
                    rows=rows,
                    col_widths=[260, 160]).pack(fill="x", **pad)

        # Off-road ───────────────────────────────────────────────────────
        section("OFF-ROAD", RED)
        if off:
            rows = [
                ("Times went off road",   str(off["count"])),
                ("Average duration",      ms_fmt(off["avg_ms"])),
                ("Shortest excursion",    ms_fmt(off["min_ms"])),
                ("Longest excursion",     ms_fmt(off["max_ms"])),
            ]
        else:
            rows = [("No off-road events", "—")]

        build_table(tab,
                    columns=["Metric", "Value"],
                    rows=rows,
                    col_widths=[260, 160]).pack(fill="x", **pad)

        # Speed ──────────────────────────────────────────────────────────
        section("SPEED", NEON)
        if spd:
            rows = [
                ("Top speed",     f"{spd['top']:.1f}  km/h"),
                ("Average speed", f"{spd['avg']:.1f}  km/h"),
            ]
        else:
            rows = [("No speed data", "—")]

        build_table(tab,
                    columns=["Metric", "Value"],
                    rows=rows,
                    col_widths=[260, 160]).pack(fill="x", **pad)

    # Charts tab ────────────────────────────────────────────────────────────
    def _render_charts(self, lap, off, spd):
        tab = self._tab_charts
        for w in tab.winfo_children():
            w.destroy()

        # Close any matplotlib figures so memory doesn't pile up
        plt.close("all")

        # Row 0: Pie and Line
        row0 = tk.Frame(tab, bg=BG)
        row0.pack(fill="both", expand=True, padx=10, pady=(10, 4))

        pie_frame = tk.Frame(row0, bg=PANEL, relief="flat",
                             highlightbackground=BORDER, highlightthickness=1)
        pie_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        build_pie(pie_frame, off, lap).pack(fill="both", expand=True, padx=6, pady=6)

        line_frame = tk.Frame(row0, bg=PANEL, relief="flat",
                              highlightbackground=BORDER, highlightthickness=1)
        line_frame.pack(side="left", fill="both", expand=True, padx=(5, 0))
        build_line(line_frame, spd).pack(fill="both", expand=True, padx=6, pady=6)

        # Row 1: histogram
        row1 = tk.Frame(tab, bg=BG)
        row1.pack(fill="both", expand=True, padx=10, pady=(4, 10))

        hist_frame = tk.Frame(row1, bg=PANEL, relief="flat",
                              highlightbackground=BORDER, highlightthickness=1)
        hist_frame.pack(fill="both", expand=True)
        build_histogram(hist_frame, spd).pack(fill="both", expand=True, padx=6, pady=6)


# ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = StatsViewer()
    app.mainloop()