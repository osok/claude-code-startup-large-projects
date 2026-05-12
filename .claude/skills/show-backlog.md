---
name: show-backlog
description: Display backlog work items from requirement-docs/Backlog-work-list.md with status, priority, and components.
---

# Show Backlog

Displays the current backlog status.

1. **Read** `requirement-docs/Backlog-work-list.md`. If it does not exist, report: "No backlog file exists yet. Use `/store-work` to create the first entry."
2. **Parse** all `BW-NNN` items and their metadata tables (Status, Priority, Components, Origin).
3. **Display a summary table** with columns: `ID | Title | Status | Priority | Components`.
4. **Show counts** grouped by status: `pending`, `in_progress`, `blocked`, `complete`.
5. **Do not modify** the backlog file. This is a read-only operation.

Also recognized: "list backlog", "what's in the backlog", "show work items", "pending work".
