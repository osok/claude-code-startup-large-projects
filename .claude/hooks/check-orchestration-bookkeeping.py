#!/usr/bin/env python3
"""Check project-docs/activity.log + project-docs/tasks/ for drift.

Wired as a Stop hook in .claude/settings.json. Runs at end of every Claude turn.
Emits a systemMessage if drift is detected so the parent can self-correct on the
next turn — does not block, does not fail the turn, just nudges.

Drift checks:

  1. Activity log monotonicity — log_seq must be strictly increasing with no
     skips or duplicates within the recent tail.
  2. Activity log JSONL well-formedness — every line in the recent tail must
     parse as JSON.
  3. Task summary table ↔ detail block parity — every TXXX in the summary
     table must have a matching `### TXXX — ...` detail block, and vice versa.
  4. In-progress task ↔ activity log consistency — every task marked
     `in-progress` in the summary table must either:
       - have a recent log entry referencing it (any action), OR
       - if its last log action is COMPLETE / TEST_PASS / REVIEW_PASS, the
         summary table is stale.
  5. Phase transition consistency — CLAUDE.md `**Current Phase:**` must match
     the phase from the latest PHASE_TRANSITION entry in the activity log. If
     CLAUDE.md is past the initial phase but no PHASE_TRANSITION exists, the
     orchestrator advanced phases without logging the transition.

Silent no-op when project-docs/ doesn't exist (so the hook is harmless in any
project that doesn't follow this orchestration model).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PROJECT_DOCS = Path("project-docs")
TASKS_DIR = PROJECT_DOCS / "tasks"
ACTIVITY_LOG = PROJECT_DOCS / "activity.log"
CLAUDE_MD = Path("CLAUDE.md")

# How far back to scan the log. 200 lines is ~1-2 hours of busy orchestration.
LOG_TAIL_LINES = 200

TERMINAL_ACTIONS = {"COMPLETE", "TEST_PASS", "REVIEW_PASS"}

# Phases the orchestrator advances through during autonomous execution.
# Order matters: each entry must be reached via a PHASE_TRANSITION log entry
# OR via initial workflow start (no prior phase recorded).
KNOWN_PHASES = (
    "awaiting requirements",
    "requirements",
    "architecture",
    "design",
    "planning",
    "implementation",
    "review",
    "test prep",
    "testing",
    "documentation",
    "deployment",
    "complete",
)


def find_latest_task_list() -> Path | None:
    if not TASKS_DIR.exists():
        return None
    candidates = sorted(
        TASKS_DIR.glob("*-tasks.md"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def extract_seq_from_task_list(path: Path) -> str | None:
    """Extract the sequence number from a task list filename.

    Filename format: `{seq}-{short-name}-tasks.md` (e.g. `131-enumeration-orchestrator-tasks.md`).
    Returns the seq as a string for direct comparison against `work_seq` in log entries.
    """
    m = re.match(r"^(\d+)-", path.name)
    return m.group(1) if m else None


def parse_summary_table(content: str) -> dict[str, str]:
    """Return {task_id: status} from the summary table.

    Recognises rows of the form `| TXXX | ... | <status> | ... |`.
    """
    rows: dict[str, str] = {}
    in_table = False
    for line in content.splitlines():
        if line.startswith("| ID | Task |"):
            in_table = True
            continue
        if in_table:
            if not line.startswith("|"):
                in_table = False
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= 3 and re.match(r"^T\d+$", cells[0]):
                rows[cells[0]] = cells[2]
    return rows


def parse_detail_blocks(content: str) -> set[str]:
    """Return set of task IDs that have `### TXXX — ...` detail headers."""
    return set(re.findall(r"^### (T\d+)\s+—", content, re.MULTILINE))


def tail_log(n: int) -> list[dict]:
    if not ACTIVITY_LOG.exists():
        return []
    lines = ACTIVITY_LOG.read_text().splitlines()[-n:]
    parsed: list[dict] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            parsed.append(json.loads(line))
        except json.JSONDecodeError:
            parsed.append({"_malformed": line})
    return parsed


def check_log_monotonicity(entries: list[dict]) -> list[str]:
    issues: list[str] = []
    last_seq: int | None = None
    for e in entries:
        if "_malformed" in e:
            issues.append(f"Malformed JSONL line: {e['_malformed'][:80]}")
            continue
        seq = e.get("log_seq")
        if seq is None:
            issues.append(f"Entry missing log_seq: {json.dumps(e)[:80]}")
            continue
        if not isinstance(seq, int):
            issues.append(f"log_seq is not an integer: {seq!r}")
            continue
        if last_seq is not None:
            if seq < last_seq:
                issues.append(f"log_seq went backwards: {last_seq} → {seq}")
            elif seq == last_seq:
                issues.append(f"Duplicate log_seq: {seq}")
            elif seq > last_seq + 1:
                issues.append(f"log_seq skipped: {last_seq} → {seq}")
        last_seq = seq
    return issues


def check_summary_vs_detail(summary: dict[str, str], details: set[str]) -> list[str]:
    """Check parity between summary table rows and per-task detail blocks.

    Pending tasks legitimately can be summary-only — detail blocks are written
    incrementally as tasks become in-progress (the agent dispatch fills them in).
    Only non-pending tasks are checked against the detail-block set.
    """
    issues: list[str] = []
    non_pending = {tid for tid, status in summary.items() if status != "pending"}
    missing_details = non_pending - details
    only_in_details = details - set(summary.keys())
    if missing_details:
        issues.append(
            f"Non-pending summary tasks with no detail block: {sorted(missing_details)}"
        )
    if only_in_details:
        issues.append(
            f"Detail blocks present for tasks not in summary table: {sorted(only_in_details)}"
        )
    return issues


def check_status_consistency(
    summary: dict[str, str],
    log_entries: list[dict],
    current_seq: str | None,
) -> list[str]:
    """Cross-check task statuses against the activity log.

    Two failure modes:
    1. Task is `in-progress` but no recent log entry references it (might be
       legitimately running, or might be stale).
    2. Task summary says `pending`/`in-progress` but the log's last action for
       that task is terminal (COMPLETE/TEST_PASS/REVIEW_PASS) — stale, the
       summary was never flipped after completion.

    `current_seq` filters log entries to the active sequence so prior-sequence
    task IDs (TXXX collide across sequences) don't leak into this comparison.
    """
    issues: list[str] = []

    # Map task_id → last action, filtered to the active sequence's log entries.
    last_action: dict[str, str] = {}
    for e in log_entries:
        if "_malformed" in e:
            continue
        if current_seq is not None and str(e.get("work_seq")) != current_seq:
            continue
        tid = e.get("task_id")
        if not tid or not isinstance(tid, str):
            continue
        last_action[tid] = e.get("action", "?")

    # 1. in-progress tasks with no recent log activity
    for tid, status in summary.items():
        if status != "in-progress":
            continue
        if tid not in last_action:
            issues.append(
                f"Task {tid} is `in-progress` in summary but no recent log entry references it"
            )

    # 2. tasks with terminal log action but non-terminal summary status
    for tid, status in summary.items():
        if status == "complete":
            continue
        action = last_action.get(tid)
        if action in TERMINAL_ACTIONS:
            issues.append(
                f"Task {tid}: log shows {action} but summary says `{status}` "
                f"(flip status to `complete`)"
            )

    return issues


def current_phase_from_claude_md() -> str:
    """Return lower-cased value of `**Current Phase:**` under `## Current Work`, or empty."""
    if not CLAUDE_MD.exists():
        return ""
    text = CLAUDE_MD.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^##\s+Current Work\s*$(.*?)(?=^##\s)", text, flags=re.M | re.S)
    if not m:
        return ""
    section = m.group(1)
    m2 = re.search(r"^\*\*Current Phase:\*\*\s*(.+)$", section, flags=re.M)
    if not m2:
        return ""
    raw = m2.group(1).strip().lower()
    return re.sub(r"[\s\-—*.:]+$", "", raw).strip()


def check_phase_transition(log_entries: list[dict], claude_phase: str) -> list[str]:
    """Verify the current phase in CLAUDE.md matches the latest PHASE_TRANSITION in the log.

    Drift signals:
    - CLAUDE.md says one phase, but the latest PHASE_TRANSITION entry says another.
    - CLAUDE.md is not in a known phase (typo or stale value).
    - No PHASE_TRANSITION entry exists but CLAUDE.md is past the initial phase.
    """
    issues: list[str] = []
    if not claude_phase:
        return issues
    if claude_phase not in KNOWN_PHASES:
        issues.append(
            f"CLAUDE.md `**Current Phase:**` value is not a known phase: '{claude_phase}'"
        )

    # Find the most recent PHASE_TRANSITION entry.
    last_phase_in_log: str | None = None
    for e in reversed(log_entries):
        if "_malformed" in e:
            continue
        if e.get("action") == "PHASE_TRANSITION":
            phase = e.get("phase") or ""
            if isinstance(phase, str):
                last_phase_in_log = phase.strip().lower()
            break

    if last_phase_in_log is None:
        # First-run case: no PHASE_TRANSITION yet. Only complain if CLAUDE.md has
        # moved past the entry phases.
        if claude_phase not in {"awaiting requirements", "requirements", "not started"}:
            issues.append(
                f"CLAUDE.md phase is `{claude_phase}` but no PHASE_TRANSITION entry "
                "exists in the activity log — orchestrator advanced phase without logging it"
            )
        return issues

    if last_phase_in_log != claude_phase:
        issues.append(
            f"Phase drift: CLAUDE.md says `{claude_phase}` but latest "
            f"PHASE_TRANSITION log entry shows `{last_phase_in_log}` — one of them is stale"
        )
    return issues


def main() -> None:
    # Drain stdin (hook contract); we don't need its content.
    try:
        sys.stdin.read()
    except Exception:
        pass

    if not PROJECT_DOCS.exists():
        return  # Not an orchestration project; silent no-op

    issues: list[str] = []

    log_entries = tail_log(LOG_TAIL_LINES)
    issues.extend(check_log_monotonicity(log_entries))
    issues.extend(check_phase_transition(log_entries, current_phase_from_claude_md()))

    task_list = find_latest_task_list()
    if task_list:
        content = task_list.read_text()
        summary = parse_summary_table(content)
        details = parse_detail_blocks(content)
        current_seq = extract_seq_from_task_list(task_list)
        issues.extend(check_summary_vs_detail(summary, details))
        issues.extend(check_status_consistency(summary, log_entries, current_seq))

    if issues:
        msg = (
            "Orchestration bookkeeping drift detected (last task list: "
            f"{task_list.name if task_list else 'none'}):\n"
            + "\n".join(f"  - {i}" for i in issues)
        )
        print(json.dumps({"systemMessage": msg, "suppressOutput": True}))


if __name__ == "__main__":
    main()
