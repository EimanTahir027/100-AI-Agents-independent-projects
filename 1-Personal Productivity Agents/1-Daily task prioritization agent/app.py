import json
import io
import pandas as pd
import streamlit as st
from datetime import date, datetime
from agent import (
    Task, build_plan, render_summary,
    WEIGHTS, EFFORT_DEFAULTS_MIN, IMPACT_MAP,
    parse_effort, parse_bool, parse_date,
    TOP3_COUNT, NEXT5_COUNT,
)

st.set_page_config(page_title="Daily Task Prioritizer", page_icon="📋", layout="wide")

# ── Session state defaults ──────────────────────────────────────────────────
if "tasks" not in st.session_state:
    st.session_state.tasks = []
if "plan" not in st.session_state:
    st.session_state.plan = None

# ── Sidebar: weights & budget ───────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")

    st.subheader("Scoring Weights")
    w_urgency = st.slider("Urgency weight", 0.0, 5.0, WEIGHTS["urgency"], 0.5)
    w_importance = st.slider("Importance weight", 0.0, 5.0, WEIGHTS["importance"], 0.5)
    w_quickwin = st.slider("Quick-win bonus", 0.0, 3.0, WEIGHTS["quickwin_bonus"], 0.5)
    w_blocked = st.slider("Blocked penalty", 0.0, 10.0, WEIGHTS["blocked_penalty"], 0.5)

    st.subheader("Daily Budget")
    available_min = st.number_input(
        "Available minutes today (0 = unlimited)", min_value=0, value=0, step=15
    )

    st.subheader("Bucket Sizes")
    top_n = st.number_input("Top N tasks", min_value=1, max_value=10, value=TOP3_COUNT)
    next_n = st.number_input("Next N tasks", min_value=1, max_value=10, value=NEXT5_COUNT)

# ── Helpers ─────────────────────────────────────────────────────────────────

def _safe_str(val, default="") -> str:
    if pd.isna(val) if not isinstance(val, (list, dict)) else False:
        return default
    return str(val).strip()


def tasks_from_df(df: pd.DataFrame) -> list[Task]:
    tasks = []
    for _, row in df.iterrows():
        title = _safe_str(row.get("title", ""))
        if not title:
            continue
        tasks.append(Task(
            title=title,
            description=_safe_str(row.get("description", "")),
            deadline=parse_date(_safe_str(row.get("deadline", ""))),
            effort_min=parse_effort(_safe_str(row.get("effort", ""))),
            impact=IMPACT_MAP.get(_safe_str(row.get("impact", "medium")).lower(), 2),
            blocked=parse_bool(_safe_str(row.get("blocked", "no"))),
            tags=[t.strip() for t in _safe_str(row.get("tags", "")).split(",") if t.strip()],
        ))
    return tasks


def run_plan(tasks: list[Task]) -> dict:
    import agent as ag
    ag.WEIGHTS["urgency"] = w_urgency
    ag.WEIGHTS["importance"] = w_importance
    ag.WEIGHTS["quickwin_bonus"] = w_quickwin
    ag.WEIGHTS["blocked_penalty"] = w_blocked
    ag.AVAILABLE_MIN = available_min
    ag.TOP3_COUNT = int(top_n)
    ag.NEXT5_COUNT = int(next_n)
    return build_plan(tasks)


IMPACT_LABEL = {1: "🟢 Low", 2: "🟡 Medium", 3: "🔴 High"}
BUCKET_COLOR = {
    "top3": "#1f77b4",
    "next5": "#2ca02c",
    "unblock": "#ff7f0e",
    "defer": "#7f7f7f",
}


def render_task_card(item: dict, rank: int | None = None):
    impact_label = IMPACT_LABEL.get(item["impact"], "")
    tags = " ".join(f"`{t}`" for t in item.get("tags", []))
    deadline = item["deadline"] or "No deadline"
    blocked_badge = " 🔒 **BLOCKED**" if item["blocked"] else ""
    rank_prefix = f"**{rank}.** " if rank else ""

    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"{rank_prefix}### {item['title']}{blocked_badge}")
            if item["description"]:
                st.caption(item["description"])
            if tags:
                st.markdown(tags)
        with col2:
            st.metric("Score", item["score"])
            st.caption(f"Impact: {impact_label}")

        col3, col4, col5 = st.columns(3)
        col3.info(f"📅 {deadline}")
        col4.info(f"⏱️ {item['effort_min']} min")
        col5.success(f"💡 {item['reason']}")

        with st.expander("Score breakdown"):
            bd = item["score_breakdown"]
            cols = st.columns(4)
            cols[0].metric("Urgency", bd["urgency"])
            cols[1].metric("Importance", bd["importance"])
            cols[2].metric("Quick-win", bd["quickwin"])
            cols[3].metric("Blocked penalty", -bd["blocked_penalty"])


def render_plan(plan: dict):
    sections = [
        ("🏆 Top Priority", plan["top3"], "Do these first today"),
        ("📋 Next Up", plan["next5"], "Work on these after the top tasks"),
        ("🔓 Need to Unblock", plan["unblock"], "Take action to unblock these"),
        ("💤 Defer", plan["defer"], "Low urgency — skip for today"),
    ]

    for title, items, subtitle in sections:
        st.subheader(title)
        st.caption(subtitle)
        if not items:
            st.info("None")
        else:
            for i, item in enumerate(items, 1):
                render_task_card(item, i)
        st.divider()


# ── Main UI ─────────────────────────────────────────────────────────────────
st.title("📋 Daily Task Prioritization Agent")
st.caption(f"Today: {date.today().isoformat()}")

tab_upload, tab_manual, tab_plan = st.tabs(["📂 Upload CSV", "✏️ Add Tasks Manually", "📊 Today's Plan"])

# ── Tab 1: Upload CSV ────────────────────────────────────────────────────────
with tab_upload:
    st.markdown("Upload your `tasks.csv` file. Required column: `title`. Optional: `description`, `deadline` (YYYY-MM-DD), `effort`, `impact`, `blocked`, `tags`.")

    uploaded = st.file_uploader("Choose a CSV file", type="csv")
    if uploaded:
        df = pd.read_csv(uploaded)
        st.dataframe(df, use_container_width=True)
        if st.button("Load tasks from CSV", type="primary"):
            st.session_state.tasks = tasks_from_df(df)
            st.session_state.plan = None
            st.success(f"Loaded {len(st.session_state.tasks)} tasks.")

    st.markdown("**No file? Use the default `tasks.csv` in the project folder:**")
    if st.button("Load tasks.csv from disk"):
        try:
            df = pd.read_csv("tasks.csv")
            st.session_state.tasks = tasks_from_df(df)
            st.session_state.plan = None
            st.success(f"Loaded {len(st.session_state.tasks)} tasks from tasks.csv.")
            st.dataframe(df, use_container_width=True)
        except FileNotFoundError:
            st.error("tasks.csv not found in the current directory.")

# ── Tab 2: Manual entry ──────────────────────────────────────────────────────
with tab_manual:
    st.subheader("Add a new task")

    with st.form("add_task_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        title = col1.text_input("Title *")
        desc = col2.text_input("Description")

        col3, col4, col5 = st.columns(3)
        deadline_val = col3.date_input("Deadline (optional)", value=None)
        effort_val = col4.selectbox("Effort", ["15m", "25m", "30m", "45m", "60m", "90m", "S", "M", "L"])
        impact_val = col5.selectbox("Impact", ["low", "medium", "high"], index=1)

        col6, col7 = st.columns(2)
        blocked_val = col6.checkbox("Blocked?")
        tags_val = col7.text_input("Tags (comma-separated)")

        submitted = st.form_submit_button("Add Task", type="primary")
        if submitted:
            if not title.strip():
                st.error("Title is required.")
            else:
                st.session_state.tasks.append(Task(
                    title=title.strip(),
                    description=desc.strip(),
                    deadline=deadline_val if deadline_val else None,
                    effort_min=parse_effort(effort_val),
                    impact=IMPACT_MAP.get(impact_val, 2),
                    blocked=blocked_val,
                    tags=[t.strip() for t in tags_val.split(",") if t.strip()],
                ))
                st.session_state.plan = None
                st.success(f"Added: {title}")

    if st.session_state.tasks:
        st.subheader(f"Current tasks ({len(st.session_state.tasks)})")
        for i, t in enumerate(st.session_state.tasks):
            col_a, col_b = st.columns([5, 1])
            dl = t.deadline.isoformat() if t.deadline else "no deadline"
            col_a.markdown(f"**{t.title}** — {dl} | {t.effort_min}m | impact {t.impact} {'🔒' if t.blocked else ''}")
            if col_b.button("Remove", key=f"rm_{i}"):
                st.session_state.tasks.pop(i)
                st.session_state.plan = None
                st.rerun()

        if st.button("Clear all tasks", type="secondary"):
            st.session_state.tasks = []
            st.session_state.plan = None
            st.rerun()

# ── Tab 3: Plan ──────────────────────────────────────────────────────────────
with tab_plan:
    if not st.session_state.tasks:
        st.info("No tasks loaded yet. Go to 'Upload CSV' or 'Add Tasks Manually' first.")
    else:
        col_gen, col_dl_txt, col_dl_json = st.columns([2, 1, 1])

        with col_gen:
            if st.button("Generate Plan", type="primary", use_container_width=True):
                st.session_state.plan = run_plan(st.session_state.tasks)

        if st.session_state.plan:
            plan = st.session_state.plan

            summary_txt = render_summary(plan)
            with col_dl_txt:
                st.download_button(
                    "Download plan.txt",
                    data=summary_txt,
                    file_name="plan.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
            with col_dl_json:
                st.download_button(
                    "Download plan.json",
                    data=json.dumps(plan, indent=2),
                    file_name="plan.json",
                    mime="application/json",
                    use_container_width=True,
                )

            total = sum(len(plan[k]) for k in ("top3", "next5", "unblock", "defer"))
            top_effort = sum(t["effort_min"] for t in plan["top3"])
            all_effort = sum(t["effort_min"] for k in ("top3", "next5") for t in plan[k])

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total tasks", total)
            m2.metric("Top tasks effort", f"{top_effort} min")
            m3.metric("Top + Next effort", f"{all_effort} min")
            m4.metric("Blocked", len(plan["unblock"]))

            st.divider()
            render_plan(plan)
