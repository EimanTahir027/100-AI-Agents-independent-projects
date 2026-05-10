import csv
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List

# ── colours ──────────────────────────────────────────────────────────────────
C = {
    "bg":           "#FFFFFF",
    "sidebar":      "#6B21A8",
    "sidebar_dark": "#4C1D95",
    "accent":       "#9333EA",
    "accent_light": "#E9D5FF",
    "accent_mid":   "#C4B5FD",
    "text_light":   "#FFFFFF",
    "text_dark":    "#1E1B4B",
    "text_muted":   "#6B7280",
    "row_alt":      "#F5F0FF",
    "sev_high":     "#EF4444",
    "sev_medium":   "#F59E0B",
    "sev_low":      "#10B981",
    "border":       "#DDD6FE",
}

FONT_TITLE  = ("Segoe UI", 18, "bold")
FONT_HEAD   = ("Segoe UI", 11, "bold")
FONT_BODY   = ("Segoe UI", 10)
FONT_SMALL  = ("Segoe UI", 9)
FONT_MONO   = ("Consolas", 9)

PRIORITY_MAP = {"low": 1, "medium": 2, "high": 3}
BUFFER_MINUTES = 10


@dataclass
class Event:
    title: str
    start: datetime
    end: datetime
    priority: int
    event_type: str
    flexible: bool


def parse_datetime(s):
    return datetime.strptime(s.strip(), "%Y-%m-%d %H:%M")


def read_calendar(path):
    events = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            events.append(Event(
                title=row["title"],
                start=parse_datetime(row["start_time"]),
                end=parse_datetime(row["end_time"]),
                priority=PRIORITY_MAP[row["priority"].lower()],
                event_type=row["type"],
                flexible=row["flexible"].lower() == "yes",
            ))
    return sorted(events, key=lambda e: e.start)


def suggest_resolution(a, b):
    if a.priority > b.priority and b.flexible:
        return f"Reschedule '{b.title}'"
    if b.priority > a.priority and a.flexible:
        return f"Reschedule '{a.title}'"
    if a.flexible and b.flexible:
        return "Shorten or reschedule one event"
    return "Requires human decision"


def detect_conflicts(events):
    conflicts = []
    for i in range(len(events) - 1):
        a, b = events[i], events[i + 1]
        overlap   = a.end > b.start
        no_buffer = (b.start - a.end) < timedelta(minutes=BUFFER_MINUTES)
        if overlap or no_buffer:
            conflicts.append({
                "event_a":  a.title,
                "event_b":  b.title,
                "type":     "overlap" if overlap else "no_buffer",
                "severity": "high" if a.priority == 3 or b.priority == 3 else "medium",
                "suggestion": suggest_resolution(a, b),
            })
    return conflicts


# ── App ───────────────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Calendar Conflict Resolver")
        self.geometry("1100x680")
        self.minsize(900, 580)
        self.configure(bg=C["bg"])
        self.resizable(True, True)

        self._csv_path = tk.StringVar(value="No file loaded")
        self._events: List[Event] = []
        self._conflicts = []

        self._style()
        self._build()

    # ── ttk style ────────────────────────────────────────────────────────────
    def _style(self):
        s = ttk.Style(self)
        s.theme_use("clam")

        s.configure("Treeview",
                     background=C["bg"], fieldbackground=C["bg"],
                     foreground=C["text_dark"], font=FONT_BODY,
                     rowheight=28, borderwidth=0)
        s.configure("Treeview.Heading",
                     background=C["accent"], foreground=C["text_light"],
                     font=FONT_HEAD, relief="flat", padding=(8, 6))
        s.map("Treeview",
              background=[("selected", C["accent_light"])],
              foreground=[("selected", C["text_dark"])])
        s.map("Treeview.Heading", background=[("active", C["sidebar"])])

        s.configure("Vertical.TScrollbar",
                     background=C["accent_mid"], troughcolor=C["bg"],
                     borderwidth=0, arrowcolor=C["sidebar"])

    # ── layout ───────────────────────────────────────────────────────────────
    def _build(self):
        # ── sidebar ──────────────────────────────────────────────────────────
        sidebar = tk.Frame(self, bg=C["sidebar"], width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="📅", font=("Segoe UI Emoji", 32),
                 bg=C["sidebar"], fg=C["text_light"]).pack(pady=(30, 4))
        tk.Label(sidebar, text="Conflict\nResolver",
                 font=("Segoe UI", 14, "bold"),
                 bg=C["sidebar"], fg=C["text_light"],
                 justify="center").pack()

        tk.Frame(sidebar, bg=C["sidebar_dark"], height=1).pack(
            fill="x", padx=20, pady=24)

        self._sidebar_btn("Load CSV", self._load_csv, sidebar)
        self._sidebar_btn("Run Analysis", self._run, sidebar)
        self._sidebar_btn("Save Outputs", self._save, sidebar)
        self._sidebar_btn("Clear", self._clear, sidebar)

        # file label
        tk.Frame(sidebar, bg=C["sidebar_dark"], height=1).pack(
            fill="x", padx=20, pady=20)
        tk.Label(sidebar, text="Loaded file:", font=FONT_SMALL,
                 bg=C["sidebar"], fg=C["accent_mid"]).pack(padx=14, anchor="w")
        tk.Label(sidebar, textvariable=self._csv_path, font=FONT_SMALL,
                 bg=C["sidebar"], fg=C["text_light"],
                 wraplength=190, justify="left").pack(padx=14, anchor="w")

        # stats frame at bottom
        self._stat_frame = tk.Frame(sidebar, bg=C["sidebar_dark"])
        self._stat_frame.pack(side="bottom", fill="x", pady=16, padx=14)
        self._lbl_events    = self._stat_lbl("Events: —")
        self._lbl_conflicts = self._stat_lbl("Conflicts: —")
        self._lbl_high      = self._stat_lbl("High severity: —")

        # ── main area ────────────────────────────────────────────────────────
        main = tk.Frame(self, bg=C["bg"])
        main.pack(side="left", fill="both", expand=True)

        # header
        hdr = tk.Frame(main, bg=C["accent_light"], pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Calendar Conflict Resolver",
                 font=FONT_TITLE, bg=C["accent_light"],
                 fg=C["text_dark"]).pack(side="left", padx=20)
        self._status_lbl = tk.Label(hdr, text="Load a CSV to begin",
                                    font=FONT_SMALL, bg=C["accent_light"],
                                    fg=C["text_muted"])
        self._status_lbl.pack(side="right", padx=20)

        # notebook tabs
        nb = ttk.Notebook(main)
        nb.pack(fill="both", expand=True, padx=16, pady=12)

        self._tab_events    = self._make_tab(nb, "Events")
        self._tab_conflicts = self._make_tab(nb, "Conflicts")
        self._tab_json      = self._make_tab(nb, "JSON Output")

        nb.add(self._tab_events,    text="  📋 Events  ")
        nb.add(self._tab_conflicts, text="  ⚠️ Conflicts  ")
        nb.add(self._tab_json,      text="  { } JSON  ")

        self._build_events_tab()
        self._build_conflicts_tab()
        self._build_json_tab()

    def _sidebar_btn(self, text, cmd, parent):
        btn = tk.Button(parent, text=text, command=cmd,
                        font=FONT_HEAD,
                        bg=C["accent"], fg=C["text_light"],
                        activebackground=C["sidebar_dark"],
                        activeforeground=C["text_light"],
                        relief="flat", cursor="hand2",
                        padx=12, pady=8, bd=0)
        btn.pack(fill="x", padx=14, pady=5)

    def _stat_lbl(self, text):
        lbl = tk.Label(self._stat_frame, text=text, font=FONT_SMALL,
                       bg=C["sidebar_dark"], fg=C["accent_mid"],
                       anchor="w")
        lbl.pack(fill="x", padx=8, pady=2)
        return lbl

    def _make_tab(self, nb, name):
        f = tk.Frame(nb, bg=C["bg"])
        return f

    # ── Events tab ───────────────────────────────────────────────────────────
    def _build_events_tab(self):
        cols = ("Title", "Start", "End", "Priority", "Type", "Flexible")
        self._tree_events = self._make_tree(self._tab_events, cols,
                                            widths=[200, 140, 140, 80, 90, 70])

    # ── Conflicts tab ────────────────────────────────────────────────────────
    def _build_conflicts_tab(self):
        cols = ("Event A", "Event B", "Type", "Severity", "Suggested Action")
        self._tree_conflicts = self._make_tree(
            self._tab_conflicts, cols,
            widths=[180, 180, 90, 80, 260])
        self._tree_conflicts.tag_configure("high",   background="#FEE2E2")
        self._tree_conflicts.tag_configure("medium", background="#FEF9C3")
        self._tree_conflicts.tag_configure("low",    background="#D1FAE5")

    # ── JSON tab ─────────────────────────────────────────────────────────────
    def _build_json_tab(self):
        frame = tk.Frame(self._tab_json, bg=C["bg"])
        frame.pack(fill="both", expand=True)

        sb = tk.Scrollbar(frame)
        sb.pack(side="right", fill="y")

        self._txt_json = tk.Text(frame, font=FONT_MONO,
                                  bg="#1E1B4B", fg="#E9D5FF",
                                  insertbackground="white",
                                  selectbackground=C["accent"],
                                  relief="flat", bd=0,
                                  yscrollcommand=sb.set,
                                  state="disabled")
        self._txt_json.pack(fill="both", expand=True, padx=(0, 0))
        sb.config(command=self._txt_json.yview)

    # ── helper: treeview with scrollbar ──────────────────────────────────────
    def _make_tree(self, parent, cols, widths):
        frame = tk.Frame(parent, bg=C["bg"])
        frame.pack(fill="both", expand=True, padx=4, pady=4)

        sb = ttk.Scrollbar(frame, orient="vertical")
        sb.pack(side="right", fill="y")

        tree = ttk.Treeview(frame, columns=cols, show="headings",
                             yscrollcommand=sb.set, selectmode="browse")
        tree.pack(fill="both", expand=True)
        sb.config(command=tree.yview)

        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center", minwidth=60)

        tree.tag_configure("alt", background=C["row_alt"])
        return tree

    # ── actions ──────────────────────────────────────────────────────────────
    def _load_csv(self):
        path = filedialog.askopenfilename(
            title="Select calendar CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not path:
            return
        try:
            self._events = read_calendar(path)
            self._csv_path.set(path.split("/")[-1].split("\\")[-1])
            self._populate_events()
            self._set_status(f"Loaded {len(self._events)} events — click Run Analysis")
            self._lbl_events.config(text=f"Events: {len(self._events)}")
        except Exception as e:
            messagebox.showerror("Load Error", str(e))

    def _run(self):
        if not self._events:
            messagebox.showwarning("No data", "Please load a CSV file first.")
            return
        self._conflicts = detect_conflicts(self._events)
        self._populate_conflicts()
        self._populate_json()

        high = sum(1 for c in self._conflicts if c["severity"] == "high")
        self._lbl_conflicts.config(text=f"Conflicts: {len(self._conflicts)}")
        self._lbl_high.config(text=f"High severity: {high}")
        self._set_status(
            f"Analysis complete — {len(self._conflicts)} conflicts found "
            f"({high} high severity)")

    def _save(self):
        if not self._conflicts:
            messagebox.showwarning("Nothing to save", "Run analysis first.")
            return
        with open("conflicts.json", "w", encoding="utf-8") as f:
            json.dump(self._conflicts, f, indent=2)
        with open("conflicts.txt", "w", encoding="utf-8") as f:
            f.write("Calendar Conflict Report\n" + "=" * 40 + "\n\n")
            for c in self._conflicts:
                f.write(f"- Conflict between {c['event_a']} and {c['event_b']}\n")
                f.write(f"  Type: {c['type']}, Severity: {c['severity']}\n")
                f.write(f"  Suggested Action: {c['suggestion']}\n\n")
        self._set_status("Saved conflicts.json and conflicts.txt")
        messagebox.showinfo("Saved", "conflicts.json and conflicts.txt saved.")

    def _clear(self):
        self._events = []
        self._conflicts = []
        self._csv_path.set("No file loaded")
        for tree in (self._tree_events, self._tree_conflicts):
            tree.delete(*tree.get_children())
        self._txt_json.config(state="normal")
        self._txt_json.delete("1.0", "end")
        self._txt_json.config(state="disabled")
        self._lbl_events.config(text="Events: —")
        self._lbl_conflicts.config(text="Conflicts: —")
        self._lbl_high.config(text="High severity: —")
        self._set_status("Cleared — load a CSV to begin")

    # ── populate helpers ──────────────────────────────────────────────────────
    def _populate_events(self):
        tree = self._tree_events
        tree.delete(*tree.get_children())
        for i, e in enumerate(self._events):
            tag = "alt" if i % 2 else ""
            tree.insert("", "end", tags=(tag,), values=(
                e.title,
                e.start.strftime("%H:%M"),
                e.end.strftime("%H:%M"),
                {1: "Low", 2: "Medium", 3: "High"}[e.priority],
                e.event_type.capitalize(),
                "Yes" if e.flexible else "No",
            ))

    def _populate_conflicts(self):
        tree = self._tree_conflicts
        tree.delete(*tree.get_children())
        for c in self._conflicts:
            tree.insert("", "end", tags=(c["severity"],), values=(
                c["event_a"],
                c["event_b"],
                c["type"].replace("_", " ").title(),
                c["severity"].capitalize(),
                c["suggestion"],
            ))

    def _populate_json(self):
        txt = self._txt_json
        txt.config(state="normal")
        txt.delete("1.0", "end")
        txt.insert("end", json.dumps(self._conflicts, indent=2))
        txt.config(state="disabled")

    def _set_status(self, msg):
        self._status_lbl.config(text=msg)


if __name__ == "__main__":
    app = App()
    app.mainloop()
