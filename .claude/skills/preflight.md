---
name: preflight
description: Diagnostic snapshot of orchestrator state — read-only health check of CLAUDE.md Current Work, latest task list, activity log tail, and hook configuration. Safe to run anytime.
---

# Preflight

Read-only diagnostic that surfaces the current state of orchestration bookkeeping. Run before `/continue` if something feels off, or any time you want a snapshot without modifying state.

## What it reports

1. **Current Work block** from `CLAUDE.md`:
   - `Seq`, `Name`, `Status`, `Current Phase`, `Task List`, `Component` (if set)
2. **Document Sequence Tracker** — read `project-docs/document-sequence-tracker.md` and report the row for the current `Seq` (or "no row for current seq" if missing).
3. **Latest task list** at `project-docs/tasks/{seq}-{short-name}-tasks.md`:
   - Filename and existence
   - Task count by status (`pending`, `in-progress`, `blocked`, `complete`, `failed`)
   - Any `in-progress` tasks (these should be rare — stale or actively-running)
   - Code Review Findings summary (if section present): count of `open`, `resolved`, `verified`, `still_open`
4. **Activity log tail** at `project-docs/activity.log`:
   - Last `log_seq`, last action, last agent
   - Latest `PHASE_TRANSITION` entry (phase + timestamp)
   - Detect malformed JSONL lines in the last 50 entries
5. **Phase consistency** — compare `CLAUDE.md` Current Phase against the latest `PHASE_TRANSITION` in the log. Flag drift.
6. **Hook configuration** — confirm `.claude/settings.json` exists and references `requirements-gate.py` (PreToolUse) and `check-orchestration-bookkeeping.py` (Stop).
7. **Autonomous mode boundaries** — list the four hard-stops (from `CLAUDE.md` § Autonomous Mode) and which apply right now:
   - Requirements approval gate (passes if `Current Phase` is past `Requirements`)
   - Code review findings gate (passes if all CR-IDs `verified`)
   - Testing execution gate (passes only after explicit user authorization)
   - Phase-boundary surprise (no automated check; flagged conceptually)

## What it MUST NOT do

- Do NOT modify any file. This is read-only.
- Do NOT invoke any agent.
- Do NOT advance `Current Phase` or task status.
- Do NOT write to the activity log.

## Output Format

Report as a compact, scannable block:

```
PREFLIGHT — {seq} {short-name}

Current Work
  Status: {status}
  Phase: {phase}
  Component: {component or "-"}
  Task list: {path or "MISSING"}

Tasks ({total})
  pending:     {N}
  in-progress: {N}  {list IDs}
  blocked:     {N}  {list IDs}
  complete:    {N}
  failed:      {N}

Findings ({total})
  open:        {N}
  resolved:    {N}
  verified:    {N}
  still_open:  {N}

Activity log
  Last seq:    {N}
  Last action: {agent}/{action}
  Last phase transition: {phase} at {timestamp}

Phase consistency: {OK | DRIFT: CLAUDE.md says X, log says Y}
Hooks: {OK | MISSING: ...}

Boundaries currently in effect:
  - {boundary 1}
  - {boundary 2}
```

If any drift or misconfiguration is found, end the report with a one-line recommendation (e.g., "Run `/continue` to resume" or "Inspect `project-docs/activity.log` line {N} for malformed JSON").
