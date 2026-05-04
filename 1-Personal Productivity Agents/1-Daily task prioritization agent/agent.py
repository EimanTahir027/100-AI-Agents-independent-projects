import csv
import json
from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Dict, Optional, Tuple

# ----------------------------
# Configuration (tweakable)
# ----------------------------
EFFORT_DEFAULTS_MIN = {"S": 15, "M": 45, "L": 90}
IMPACT_MAP = {"low": 1, "medium": 2, "high": 3}

WEIGHTS = {
    "urgency": 2.0,
    "importance": 3.0,
    "quickwin_bonus": 1.0,
    "blocked_penalty": 5.0,
}

TOP3_COUNT = 3
NEXT5_COUNT = 5

# Optional: Set a daily time budget in minutes (0 = unlimited)
AVAILABLE_MIN = 0


@dataclass
class Task:
    title: str
    description: str
    deadline: Optional[date]
    effort_min: int
    impact: int
    blocked: bool
    tags: List[str]


def parse_date(s: str) -> Optional[date]:
    s = (s or "").strip()
    if not s:
        return None
    return datetime.strptime(s, "%Y-%m-%d").date()


def parse_effort(s: str) -> int:
    s = (s or "").strip()
    if not s:
        return EFFORT_DEFAULTS_MIN["M"]
    if s.upper() in EFFORT_DEFAULTS_MIN:
        return EFFORT_DEFAULTS_MIN[s.upper()]
    # supports "25m" or "25"
    s = s.lower().replace("min", "").replace("m", "").strip()
    try:
        val = int(s)
        return max(5, val)
    except ValueError:
        return EFFORT_DEFAULTS_MIN["M"]


def parse_bool(s: str) -> bool:
    return (s or "").strip().lower() in {"yes", "true", "1", "y"}


def days_until(d: Optional[date]) -> Optional[int]:
    if d is None:
        return None
    return (d - date.today()).days


def urgency_score(days_left: Optional[int]) -> float:
    """
    Returns urgency on a 0–5 scale.
    """
    if days_left is None:
        return 0.5  # small baseline urgency for no-deadline tasks
    if days_left < 0:
        return 5.0  # overdue
    if days_left == 0:
        return 5.0  # due today
    if days_left == 1:
        return 4.0
    if days_left <= 3:
        return 3.0
    if days_left <= 7:
        return 2.0
    return 1.0


def quickwin_bonus(effort_min: int) -> float:
    return 1.0 if effort_min <= 15 else 0.0


def compute_score(task: Task) -> Tuple[float, Dict[str, float]]:
    dleft = days_until(task.deadline)
    urg = urgency_score(dleft)
    imp = float(task.impact)
    qwb = quickwin_bonus(task.effort_min) * WEIGHTS["quickwin_bonus"]
    bpen = WEIGHTS["blocked_penalty"] if task.blocked else 0.0

    score = (WEIGHTS["urgency"] * urg) + (WEIGHTS["importance"] * imp) + qwb - bpen
    breakdown = {
        "urgency": urg,
        "importance": imp,
        "quickwin": qwb,
        "blocked_penalty": bpen,
        "final_score": score,
    }
    return score, breakdown


def reason(task: Task, breakdown: Dict[str, float]) -> str:
    reasons = []

    dleft = days_until(task.deadline)
    if dleft is not None:
        if dleft < 0:
            reasons.append("Overdue")
        elif dleft == 0:
            reasons.append("Due today")
        elif dleft <= 3:
            reasons.append("Due soon")
    else:
        reasons.append("No deadline")

    if task.impact == 3:
        reasons.append("High impact")
    elif task.impact == 2:
        reasons.append("Medium impact")

    if task.effort_min <= 15:
        reasons.append("Quick win")

    if task.blocked:
        reasons.append("Blocked (needs unblock step)")

    return ", ".join(reasons)


def read_tasks(path: str) -> List[Task]:
    tasks: List[Task] = []
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = (row.get("title") or "").strip()
            if not title:
                continue
            desc = (row.get("description") or "").strip()
            deadline = parse_date(row.get("deadline") or "")
            effort_min = parse_effort(row.get("effort") or "")
            impact_str = (row.get("impact") or "medium").strip().lower()
            impact = IMPACT_MAP.get(impact_str, 2)
            blocked = parse_bool(row.get("blocked") or "no")
            tags = [t.strip() for t in (row.get("tags") or "").split(",") if t.strip()]

            tasks.append(Task(
                title=title,
                description=desc,
                deadline=deadline,
                effort_min=effort_min,
                impact=impact,
                blocked=blocked,
                tags=tags
            ))
    return tasks


def build_plan(tasks: List[Task]) -> Dict:
    scored = []
    for t in tasks:
        s, breakdown = compute_score(t)
        scored.append((t, s, breakdown))

    # Sort by score desc, then effort asc (tie-break), then title
    scored.sort(key=lambda x: (-x[1], x[0].effort_min, x[0].title.lower()))

    unblocked = [(t, s, b) for (t, s, b) in scored if not t.blocked]
    blocked = [(t, s, b) for (t, s, b) in scored if t.blocked]

    # Apply daily time budget if set
    if AVAILABLE_MIN > 0:
        budget_top = []
        used = 0
        for item in unblocked:
            t = item[0]
            if used + t.effort_min <= AVAILABLE_MIN:
                budget_top.append(item)
                used += t.effort_min
        unblocked = budget_top

    top3 = unblocked[:TOP3_COUNT]
    next5 = unblocked[TOP3_COUNT:TOP3_COUNT + NEXT5_COUNT]

    # Defer: remaining unblocked that are low urgency and low impact
    defer = []
    for (t, s, b) in unblocked[TOP3_COUNT + NEXT5_COUNT:]:
        dleft = days_until(t.deadline)
        low_urg = (urgency_score(dleft) <= 1.0)
        low_imp = (t.impact <= 1)
        if low_urg and low_imp:
            defer.append((t, s, b))

    def serialize(items):
        out = []
        for (t, s, b) in items:
            out.append({
                "title": t.title,
                "description": t.description,
                "deadline": t.deadline.isoformat() if t.deadline else None,
                "effort_min": t.effort_min,
                "impact": t.impact,
                "blocked": t.blocked,
                "tags": t.tags,
                "score": round(s, 2),
                "reason": reason(t, b),
                "score_breakdown": {k: round(v, 2) for k, v in b.items()},
            })
        return out

    plan = {
        "generated_on": date.today().isoformat(),
        "top3": serialize(top3),
        "next5": serialize(next5),
        "unblock": serialize(blocked),
        "defer": serialize(defer),
        "assumptions": {
            "effort_defaults_min": EFFORT_DEFAULTS_MIN,
            "impact_map": IMPACT_MAP,
            "weights": WEIGHTS,
            "top3_count": TOP3_COUNT,
            "next5_count": NEXT5_COUNT,
            "available_min": AVAILABLE_MIN,
        }
    }
    return plan


def render_summary(plan: Dict) -> str:
    lines = []
    lines.append(f"Daily Task Prioritization Plan ({plan['generated_on']})")
    lines.append("=" * 45)

    def section(name: str, items: List[Dict]):
        lines.append(f"\n{name}")
        lines.append("-" * len(name))
        if not items:
            lines.append("  (none)")
            return
        for i, it in enumerate(items, 1):
            dl = it["deadline"] or "none"
            lines.append(
                f"{i}. {it['title']}  | deadline: {dl} | effort: {it['effort_min']}m | score: {it['score']}"
            )
            lines.append(f"   Why: {it['reason']}")

    section("TOP 3 (Do these first)", plan["top3"])
    section("NEXT 5", plan["next5"])
    section("UNBLOCK (Blocked tasks)", plan["unblock"])
    section("DEFER (Low urgency/impact)", plan["defer"])

    return "\n".join(lines)


def main():
    tasks = read_tasks("tasks.csv")
    if not tasks:
        print("No tasks found in tasks.csv")
        return

    plan = build_plan(tasks)

    with open("plan.json", "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2)

    summary = render_summary(plan)
    with open("plan.txt", "w", encoding="utf-8") as f:
        f.write(summary)

    print(summary)
    print("\nSaved: plan.json and plan.txt")


if __name__ == "__main__":
    main()
