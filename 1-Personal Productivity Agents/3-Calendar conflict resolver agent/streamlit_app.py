import csv
import json
import io
import streamlit as st
from datetime import datetime, timedelta, date, time
from dataclasses import dataclass, replace
from typing import List

st.set_page_config(page_title="Calendar Conflict Resolver", page_icon="📅", layout="wide")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {
    background: #ffffff; color: #1E1B4B;
    font-family: 'Segoe UI', sans-serif;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #6B21A8 0%, #4C1D95 100%);
}
[data-testid="stSidebar"] * { color: #ffffff !important; }
[data-testid="stSidebar"] .stButton > button {
    background: #9333EA; color: #fff; border: none;
    border-radius: 8px; width: 100%; padding: 10px 0;
    font-size: 15px; font-weight: 600;
}
[data-testid="stSidebar"] .stButton > button:hover { background: #7E22CE; color: #fff; }
.main-header {
    background: linear-gradient(135deg, #6B21A8, #9333EA);
    color: white; padding: 22px 30px; border-radius: 14px; margin-bottom: 20px;
}
.main-header h1 { margin: 0; font-size: 24px; font-weight: 700; }
.main-header p  { margin: 4px 0 0; font-size: 13px; opacity: 0.85; }
.stat-row { display: flex; gap: 14px; margin-bottom: 20px; flex-wrap: wrap; }
.stat-card {
    flex: 1; min-width: 140px; background: #F5F0FF;
    border: 2px solid #DDD6FE; border-radius: 12px; padding: 14px 18px; text-align: center;
}
.stat-card .num { font-size: 30px; font-weight: 800; color: #6B21A8; }
.stat-card .lbl { font-size: 12px; color: #6B7280; margin-top: 2px; }
.stat-card.high { border-color: #FCA5A5; background: #FFF1F1; }
.stat-card.high .num { color: #DC2626; }
.stat-card.med  { border-color: #FDE68A; background: #FFFBEB; }
.stat-card.med .num  { color: #D97706; }
.stat-card.ok   { border-color: #6EE7B7; background: #F0FDF4; }
.stat-card.ok .num   { color: #059669; }
.section-title {
    font-size: 16px; font-weight: 700; color: #6B21A8;
    border-left: 4px solid #9333EA; padding-left: 10px; margin: 8px 0 14px;
}
.stTabs [data-baseweb="tab-list"] {
    background: #F5F0FF; border-radius: 10px; padding: 4px; gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent; color: #6B21A8;
    border-radius: 8px; font-weight: 600; padding: 8px 20px;
}
.stTabs [aria-selected="true"] { background: #6B21A8 !important; color: #fff !important; }
.conflict-card {
    background: #fff; border: 1.5px solid #DDD6FE;
    border-left: 5px solid #9333EA; border-radius: 10px;
    padding: 14px 18px; margin-bottom: 4px;
    box-shadow: 0 2px 8px rgba(107,33,168,0.07);
}
.conflict-card.high   { border-left-color: #EF4444; background: #FFF8F8; }
.conflict-card.medium { border-left-color: #F59E0B; background: #FFFDF0; }
.cf-title { font-size: 15px; font-weight: 700; color: #1E1B4B; margin-bottom: 6px; }
.cf-row   { font-size: 13px; color: #374151; margin: 3px 0; }
.badge {
    display: inline-block; padding: 2px 10px; border-radius: 20px;
    font-size: 11px; font-weight: 700; margin-left: 6px;
}
.badge-high     { background: #FEE2E2; color: #DC2626; }
.badge-medium   { background: #FEF3C7; color: #D97706; }
.badge-overlap  { background: #EDE9FE; color: #7C3AED; }
.badge-no_buffer{ background: #DBEAFE; color: #1D4ED8; }
.resolved-card {
    background: #F0FDF4; border: 1.5px solid #6EE7B7;
    border-left: 5px solid #059669; border-radius: 10px;
    padding: 12px 16px; margin-bottom: 10px;
}
.resolved-card .rt { font-size: 14px; font-weight: 700; color: #065F46; }
.resolved-card .rs { font-size: 12px; color: #374151; margin-top: 4px; }
.json-box {
    background: #1E1B4B; color: #E9D5FF; border-radius: 10px;
    padding: 20px; font-family: Consolas, monospace; font-size: 13px;
    white-space: pre; overflow-x: auto; max-height: 460px; overflow-y: auto;
}
[data-testid="stFileUploader"] section {
    border: 2px dashed #C4B5FD !important;
    border-radius: 10px !important;
    background: rgba(233,213,255,0.15) !important;
}
</style>
""", unsafe_allow_html=True)

# ── domain ────────────────────────────────────────────────────────────────────
PRIORITY_MAP = {"low": 1, "medium": 2, "high": 3}
PRIORITY_LABEL = {1: "Low", 2: "Medium", 3: "High"}


@dataclass
class Event:
    title: str
    start: datetime
    end: datetime
    priority: int
    event_type: str
    flexible: bool


def parse_dt(s):
    return datetime.strptime(s.strip(), "%Y-%m-%d %H:%M")


def load_events(file_bytes) -> List[Event]:
    reader = csv.DictReader(io.StringIO(file_bytes.decode("utf-8")))
    events = []
    for row in reader:
        events.append(Event(
            title=row["title"],
            start=parse_dt(row["start_time"]),
            end=parse_dt(row["end_time"]),
            priority=PRIORITY_MAP[row["priority"].lower()],
            event_type=row["type"],
            flexible=row["flexible"].lower() == "yes",
        ))
    return sorted(events, key=lambda e: e.start)


def suggest(a: Event, b: Event) -> str:
    if a.priority > b.priority and b.flexible:
        return f"Reschedule '{b.title}'"
    if b.priority > a.priority and a.flexible:
        return f"Reschedule '{a.title}'"
    if a.flexible and b.flexible:
        return "Shorten or reschedule one event"
    return "Requires human decision"


def detect(events: List[Event], buffer_min: int):
    out = []
    for i in range(len(events) - 1):
        a, b = events[i], events[i + 1]
        overlap   = a.end > b.start
        no_buffer = (b.start - a.end) < timedelta(minutes=buffer_min)
        if overlap or no_buffer:
            out.append({
                "event_a":    a.title,
                "event_b":    b.title,
                "type":       "overlap" if overlap else "no_buffer",
                "severity":   "high" if a.priority == 3 or b.priority == 3 else "medium",
                "suggestion": suggest(a, b),
            })
    return out


def events_to_csv(events: List[Event]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["title", "start_time", "end_time", "priority", "type", "flexible"])
    for e in events:
        prio = {1: "low", 2: "medium", 3: "high"}[e.priority]
        w.writerow([e.title, e.start.strftime("%Y-%m-%d %H:%M"),
                    e.end.strftime("%Y-%m-%d %H:%M"),
                    prio, e.event_type, "yes" if e.flexible else "no"])
    return buf.getvalue()


# ── session state init ────────────────────────────────────────────────────────
def ss(key, default):
    if key not in st.session_state:
        st.session_state[key] = default

ss("events",    [])
ss("conflicts", [])
ss("resolved",  [])
ss("dismissed", set())
ss("ran",       False)


# ── sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📅 Calendar\nConflict Resolver")
    st.markdown("---")
    uploaded = st.file_uploader("Upload calendar CSV", type=["csv"])
    st.markdown("---")
    run_btn  = st.button("▶  Run Analysis")
    save_btn = st.button("💾  Save to disk")
    st.markdown("---")
    buffer = st.slider("Buffer gap (minutes)", 0, 30, 10, 1,
                       help="Minimum required gap between back-to-back events")

# ── load events ───────────────────────────────────────────────────────────────
if uploaded:
    new_events = load_events(uploaded.read())
    if new_events != st.session_state.events:
        st.session_state.events    = new_events
        st.session_state.conflicts = []
        st.session_state.resolved  = []
        st.session_state.dismissed = set()
        st.session_state.ran       = False

# ── run detection ─────────────────────────────────────────────────────────────
if run_btn:
    if st.session_state.events:
        st.session_state.conflicts = detect(st.session_state.events, buffer)
        st.session_state.ran       = True
    else:
        st.sidebar.warning("Upload a CSV first.")

# ── save to disk ──────────────────────────────────────────────────────────────
if save_btn:
    if not st.session_state.ran:
        st.sidebar.warning("Run analysis first.")
    else:
        with open("conflicts.json", "w") as f:
            json.dump(st.session_state.conflicts, f, indent=2)
        with open("conflicts.txt", "w") as f:
            f.write("Calendar Conflict Report\n" + "=" * 40 + "\n\n")
            for c in st.session_state.conflicts:
                f.write(f"- {c['event_a']} ↔ {c['event_b']}\n")
                f.write(f"  Type: {c['type']}, Severity: {c['severity']}\n")
                f.write(f"  Suggestion: {c['suggestion']}\n\n")
        st.sidebar.success("Saved conflicts.json + conflicts.txt")

# ── header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <h1>📅 Calendar Conflict Resolver</h1>
  <p>Detect conflicts → review suggestions → reschedule events → export clean calendar</p>
</div>""", unsafe_allow_html=True)

# ── stat cards ────────────────────────────────────────────────────────────────
events    = st.session_state.events
conflicts = st.session_state.conflicts
resolved  = st.session_state.resolved
active    = [c for i, c in enumerate(conflicts)
             if i not in st.session_state.dismissed]
high_ct   = sum(1 for c in active if c["severity"] == "high")

st.markdown(f"""
<div class="stat-row">
  <div class="stat-card">
    <div class="num">{len(events) or "—"}</div>
    <div class="lbl">Events Loaded</div>
  </div>
  <div class="stat-card {'high' if high_ct else ''}">
    <div class="num">{len(active) if st.session_state.ran else "—"}</div>
    <div class="lbl">Active Conflicts</div>
  </div>
  <div class="stat-card high">
    <div class="num">{high_ct if st.session_state.ran else "—"}</div>
    <div class="lbl">High Severity</div>
  </div>
  <div class="stat-card ok">
    <div class="num">{len(resolved)}</div>
    <div class="lbl">Resolved</div>
  </div>
</div>""", unsafe_allow_html=True)

if not events:
    st.info("Upload a CSV file from the sidebar to begin.")
    st.stop()

# ── tabs ──────────────────────────────────────────────────────────────────────
tab_resolve, tab_events, tab_resolved, tab_json = st.tabs([
    "  ⚔️  Resolve Conflicts  ",
    "  📋  Events  ",
    "  ✅  Resolved History  ",
    "  { }  JSON  ",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — RESOLVE CONFLICTS
# ═══════════════════════════════════════════════════════════════════════════════
with tab_resolve:
    if not st.session_state.ran:
        st.info("Click **Run Analysis** in the sidebar to detect conflicts.")
    elif not conflicts:
        st.success("No conflicts detected — your calendar is clean!")
    else:
        active_shown = 0
        for idx, c in enumerate(conflicts):
            if idx in st.session_state.dismissed:
                continue
            active_shown += 1
            sev   = c["severity"]
            ctype = c["type"]

            st.markdown(f"""
<div class="conflict-card {sev}">
  <div class="cf-title">
    {c['event_a']} &nbsp;↔&nbsp; {c['event_b']}
    <span class="badge badge-{sev}">{sev.upper()}</span>
    <span class="badge badge-{ctype}">{ctype.replace('_',' ').title()}</span>
  </div>
  <div class="cf-row">💡 <b>Suggestion:</b> {c['suggestion']}</div>
</div>""", unsafe_allow_html=True)

            # find the two Event objects
            ev_a = next((e for e in st.session_state.events if e.title == c["event_a"]), None)
            ev_b = next((e for e in st.session_state.events if e.title == c["event_b"]), None)

            # ── action buttons ────────────────────────────────────────────────
            suggestion = c["suggestion"]

            # Factory functions so on_click captures values by value, not reference
            def make_open(i, title):
                def _cb():
                    st.session_state[f"open_form_{i}"] = title
                return _cb

            def make_dismiss(i, conflict_str, severity):
                def _cb():
                    st.session_state.dismissed.add(i)
                    st.session_state.pop(f"open_form_{i}", None)
                    st.session_state.resolved.append({
                        "conflict": conflict_str,
                        "action":   "Dismissed by user",
                        "severity": severity,
                    })
                return _cb

            if "Reschedule '" in suggestion:
                target_title = suggestion.split("'")[1]
                other_title  = c["event_b"] if target_title == c["event_a"] else c["event_a"]
                btn_cols = st.columns([2, 2, 1])
                btn_cols[0].button(f"📅 {suggestion}",
                                   key=f"apply_{idx}",
                                   on_click=make_open(idx, target_title),
                                   use_container_width=True)
                btn_cols[1].button(f"📅 Reschedule '{other_title}' instead",
                                   key=f"other_{idx}",
                                   on_click=make_open(idx, other_title),
                                   use_container_width=True)
            elif suggestion == "Shorten or reschedule one event":
                btn_cols = st.columns([2, 2, 1])
                btn_cols[0].button(f"📅 Reschedule '{c['event_a']}'",
                                   key=f"ra_{idx}",
                                   on_click=make_open(idx, c["event_a"]),
                                   use_container_width=True)
                btn_cols[1].button(f"📅 Reschedule '{c['event_b']}'",
                                   key=f"rb_{idx}",
                                   on_click=make_open(idx, c["event_b"]),
                                   use_container_width=True)
            else:
                btn_cols = st.columns([2, 2, 1])
                btn_cols[0].button(f"📅 Reschedule '{c['event_a']}'",
                                   key=f"rha_{idx}",
                                   on_click=make_open(idx, c["event_a"]),
                                   use_container_width=True)
                btn_cols[1].button(f"📅 Reschedule '{c['event_b']}'",
                                   key=f"rhb_{idx}",
                                   on_click=make_open(idx, c["event_b"]),
                                   use_container_width=True)

            btn_cols[2].button("🗑 Dismiss", key=f"dismiss_{idx}",
                               on_click=make_dismiss(
                                   idx,
                                   f"{c['event_a']} ↔ {c['event_b']}",
                                   sev),
                               use_container_width=True)

            # ── inline reschedule form ────────────────────────────────────────
            form_target = st.session_state.get(f"open_form_{idx}")
            if form_target:
                target_ev = next(
                    (e for e in st.session_state.events if e.title == form_target), None)
                if target_ev:
                    st.markdown(
                        f"<div class='section-title'>📝 Reschedule: {form_target}</div>",
                        unsafe_allow_html=True)
                    info_col, form_col = st.columns([1, 2])
                    with info_col:
                        st.markdown(f"""
**Original schedule** *(before change)*
- 🕐 Start: `{target_ev.start.strftime('%H:%M')}`
- 🕐 End: `{target_ev.end.strftime('%H:%M')}`
- 📅 Date: `{target_ev.start.strftime('%Y-%m-%d')}`
- ⭐ Priority: `{PRIORITY_LABEL[target_ev.priority]}`
- 🔄 Flexible: `{'Yes' if target_ev.flexible else 'No'}`

---
*Set new time on the right,\nthen click **Apply Reschedule**.*
""")
                    with form_col:
                        # Keys are required so Streamlit tracks the user's
                        # selections through the form-submit rerun.
                        # Without them it falls back to value= (original time).
                        dk  = f"fd_{idx}"
                        tsk = f"fts_{idx}"
                        tek = f"fte_{idx}"

                        # Seed defaults only on first open for this conflict
                        if dk  not in st.session_state:
                            st.session_state[dk]  = target_ev.start.date()
                        if tsk not in st.session_state:
                            st.session_state[tsk] = target_ev.start.time()
                        if tek not in st.session_state:
                            st.session_state[tek] = target_ev.end.time()

                        with st.form(key=f"form_{idx}"):
                            st.markdown(f"**Set new time for '{form_target}'**")
                            st.date_input("Date", key=dk)
                            col1, col2 = st.columns(2)
                            col1.time_input("New start time", key=tsk)
                            col2.time_input("New end time",   key=tek)
                            sc, cc = st.columns(2)
                            submitted = sc.form_submit_button(
                                "✅ Apply Reschedule", use_container_width=True)
                            cancelled = cc.form_submit_button(
                                "✖ Cancel", use_container_width=True)

                        # Outside the form — st.rerun() is legal here.
                        # Read values from session state (committed on submit).
                        if submitted:
                            new_s = datetime.combine(
                                st.session_state[dk], st.session_state[tsk])
                            new_e = datetime.combine(
                                st.session_state[dk], st.session_state[tek])
                            if new_e <= new_s:
                                st.error("End time must be after start time.")
                            else:
                                st.session_state.events = sorted([
                                    replace(e, start=new_s, end=new_e)
                                    if e.title == form_target else e
                                    for e in st.session_state.events
                                ], key=lambda e: e.start)
                                st.session_state.resolved.append({
                                    "conflict": f"{c['event_a']} ↔ {c['event_b']}",
                                    "action": (
                                        f"Rescheduled '{form_target}' to "
                                        f"{new_s.strftime('%H:%M')}–"
                                        f"{new_e.strftime('%H:%M')}"),
                                    "severity": sev,
                                })
                                st.session_state.dismissed.add(idx)
                                st.session_state.conflicts = detect(
                                    st.session_state.events, buffer)
                                # clean up form keys and close form
                                for k in [dk, tsk, tek, f"open_form_{idx}"]:
                                    st.session_state.pop(k, None)
                                st.rerun()

                        if cancelled:
                            for k in [dk, tsk, tek, f"open_form_{idx}"]:
                                st.session_state.pop(k, None)
                            st.rerun()

            st.markdown("---")

        if active_shown == 0:
            st.success("All conflicts resolved! Download your updated calendar below.")

        # ── download updated calendar ─────────────────────────────────────────
        if resolved:
            st.download_button(
                "⬇  Download updated calendar.csv",
                data=events_to_csv(st.session_state.events),
                file_name="calendar_resolved.csv",
                mime="text/csv",
                use_container_width=True,
            )

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — EVENTS
# ═══════════════════════════════════════════════════════════════════════════════
with tab_events:
    st.markdown('<div class="section-title">Current Calendar Events</div>',
                unsafe_allow_html=True)

    import pandas as pd
    df = pd.DataFrame([{
        "Title":    e.title,
        "Date":     e.start.strftime("%Y-%m-%d"),
        "Start":    e.start.strftime("%H:%M"),
        "End":      e.end.strftime("%H:%M"),
        "Duration": str(e.end - e.start),
        "Priority": PRIORITY_LABEL[e.priority],
        "Type":     e.event_type.capitalize(),
        "Flexible": "Yes" if e.flexible else "No",
    } for e in st.session_state.events])
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.download_button(
        "⬇  Download current calendar.csv",
        data=events_to_csv(st.session_state.events),
        file_name="calendar_current.csv",
        mime="text/csv",
    )

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — RESOLVED HISTORY
# ═══════════════════════════════════════════════════════════════════════════════
with tab_resolved:
    st.markdown('<div class="section-title">Resolution History</div>',
                unsafe_allow_html=True)
    if not resolved:
        st.info("No conflicts resolved yet. Resolve conflicts in the ⚔️ tab.")
    else:
        for r in reversed(resolved):
            st.markdown(f"""
<div class="resolved-card">
  <div class="rt">✅ {r['conflict']}</div>
  <div class="rs">🔧 {r['action']} &nbsp;|&nbsp; was: <b>{r['severity'].upper()}</b></div>
</div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — JSON
# ═══════════════════════════════════════════════════════════════════════════════
with tab_json:
    st.markdown('<div class="section-title">Raw JSON Output</div>',
                unsafe_allow_html=True)
    if not st.session_state.ran:
        st.info("Run analysis first.")
    else:
        json_str = json.dumps(st.session_state.conflicts, indent=2)
        st.markdown(f'<div class="json-box">{json_str}</div>', unsafe_allow_html=True)
        st.download_button("⬇  Download conflicts.json",
                           data=json_str, file_name="conflicts.json",
                           mime="application/json")
