#!/usr/bin/env python3
"""PreToolUse gate: block implementation edits while Current Work is in Requirements phase.

Wired as a PreToolUse hook in .claude/settings.json. Reads the tool call from
stdin (Claude Code hook protocol), inspects CLAUDE.md's `## Current Work`
status line, and blocks Write/Edit/MultiEdit/NotebookEdit on implementation
files when the work item has not yet passed the `lets begin` gate.

Why: the workflow in CLAUDE.md requires the user to review/amend a freshly
written requirements doc before any architecture/design/implementation work
starts. Auto mode otherwise barrels straight through and the user loses the
chance to correct course before code is written. See
`feedback_workflow_gates_override_auto_mode.md` in user memory.

Allowed during the Requirements phase:
  - Edits anywhere under `requirement-docs/`
  - Edits to CLAUDE.md itself (so status can be updated)
  - Edits to `project-docs/document-sequence-tracker.md`
  - Edits to `.claude/**` (so this hook itself is debuggable)
  - Edits to memory paths under `~/.claude/projects/.../memory/`

Override: include the literal token `OVERRIDE-REQUIREMENTS-GATE` in any user
message in the recent transcript and the hook will pass-through. Use this only
for genuine emergencies.

Exit codes:
  0 → allow
  2 → deny (stderr becomes the reason shown to Claude)
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

GATED_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
OVERRIDE_TOKEN = "OVERRIDE-REQUIREMENTS-GATE"

# Phases that mean "no implementation yet". Match is case-insensitive against
# the value of the `**Current Phase:**` line under `## Current Work` in
# CLAUDE.md, after stripping trailing punctuation/markdown. Match is exact —
# narrative mentions of the word "requirements" inside the Status sentence
# (e.g. "Architecture — requirements approved (`lets begin`)") do NOT trigger
# the gate.
GATED_PHASE_MARKERS = frozenset(
    {
        "requirements",
        "not started",
        "awaiting requirements",
    }
)

ALLOWED_PATH_PREFIXES = (
    "requirement-docs/",
    "project-docs/document-sequence-tracker.md",
    ".claude/",
    "CLAUDE.md",
    "README.md",
    "MEMORY.md",
)

# Absolute-path allow list (memory store outside the project root).
ALLOWED_ABS_PREFIXES = (
    "/home/michael/.claude/projects/",
)


def read_payload() -> dict:
    try:
        return json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return {}


def current_phase(claude_md: Path) -> str:
    """Return the lower-cased value of the `**Current Phase:**` line under
    ## Current Work, with trailing markdown/punctuation stripped. Empty string
    if the file or field is absent.
    """
    if not claude_md.exists():
        return ""
    text = claude_md.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"^##\s+Current Work\s*$(.*?)(?=^##\s)", text, flags=re.M | re.S)
    if not match:
        return ""
    section = match.group(1)
    m = re.search(r"^\*\*Current Phase:\*\*\s*(.+)$", section, flags=re.M)
    if not m:
        return ""
    raw = m.group(1).strip().lower()
    # Strip trailing markdown decorations (em-dashes, dashes, asterisks, periods)
    return re.sub(r"[\s\-—*.:]+$", "", raw).strip()


def in_gated_phase(phase: str) -> bool:
    if not phase:
        return False
    return phase in GATED_PHASE_MARKERS


def is_allowed_path(file_path: str, project_root: Path) -> bool:
    if not file_path:
        return True  # nothing to gate
    p = Path(file_path)

    # Absolute path: check absolute allow-list, otherwise compare against project root.
    if p.is_absolute():
        s = str(p)
        for prefix in ALLOWED_ABS_PREFIXES:
            if s.startswith(prefix):
                return True
        try:
            rel = p.relative_to(project_root)
        except ValueError:
            # Outside the project entirely — not our gate to enforce.
            return True
        rel_str = str(rel)
    else:
        rel_str = str(p)

    if rel_str.startswith("./"):
        rel_str = rel_str[2:]
    return any(rel_str == ap.rstrip("/") or rel_str.startswith(ap) for ap in ALLOWED_PATH_PREFIXES)


def transcript_has_override(transcript_path: str | None) -> bool:
    if not transcript_path:
        return False
    p = Path(transcript_path)
    if not p.exists():
        return False
    try:
        # Scan only the recent tail — overrides are meant to be one-shot.
        with p.open("r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()[-50:]
    except OSError:
        return False
    for line in lines:
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("type") != "user":
            continue
        msg = obj.get("message", {})
        content = msg.get("content")
        if isinstance(content, str):
            if OVERRIDE_TOKEN in content:
                return True
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and OVERRIDE_TOKEN in str(block.get("text", "")):
                    return True
    return False


def main() -> int:
    payload = read_payload()
    tool_name = payload.get("tool_name", "")
    if tool_name not in GATED_TOOLS:
        return 0

    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""

    cwd = Path(payload.get("cwd") or Path.cwd())
    claude_md = cwd / "CLAUDE.md"

    phase = current_phase(claude_md)
    if not in_gated_phase(phase):
        return 0

    if is_allowed_path(file_path, cwd):
        return 0

    if transcript_has_override(payload.get("transcript_path")):
        return 0

    print(
        "BLOCKED by requirements gate: Current Work is in the Requirements phase "
        f"(phase: {phase or 'unknown'}).\n"
        "The user must review the requirements doc and say `lets begin` before "
        "implementation files may be edited.\n"
        f"Attempted to edit: {file_path}\n"
        "Allowed during this phase: requirement-docs/**, CLAUDE.md, README.md, "
        "project-docs/document-sequence-tracker.md, .claude/**, memory paths.\n"
        "To override for one tool call, include the literal token "
        f"`{OVERRIDE_TOKEN}` in your next user message.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
