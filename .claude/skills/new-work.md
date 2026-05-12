---
name: new-work
description: Start a new work item with fresh sequence number; interview for requirements. Does NOT reset existing project artifacts.
---

# New Work Item

Creates a new work item without resetting existing project artifacts.

1. **Determine next sequence number** from `project-docs/document-sequence-tracker.md` (3-digit zero-padded, e.g., 001 → 002 → 003). Create the tracker file if missing (use the header from `CLAUDE.md` § Document Sequence Tracker).
2. **Prompt for work description**, generate `short_name` (lowercase, hyphens, max 30 chars), confirm with user.
3. **Check for component targeting** (if `COMPONENTS.md` exists, ask if work is for a specific component).
4. **Update Current Work section** in `CLAUDE.md` with:
   - new seq, short_name
   - `**Status:** Requirements Gathering`
   - `**Current Phase:** Requirements`
   - If component-scoped, add `**Component:**` field and `### Component Context` sub-section (per CLAUDE.md § Component Context Rules)
5. **If component-scoped**, update component status to `active` in `COMPONENTS.md` (Summary table and detail section) — follows the Component Status Lifecycle.
6. **Update Document Sequence Tracker** in `project-docs/document-sequence-tracker.md` with new row (seq, short_name, component if targeted, status=Requirements).
7. **Create requirements document scaffold** in `requirement-docs/` with ISO 29148 structure: `requirement-docs/{seq}-requirements-{short-name}.md`.
8. **Ask user about requirements source:** upload/paste OR interview.
9. **If interview selected**, invoke `@requirements` agent for elicitation.

**Note:** The `requirements-gate.py` PreToolUse hook will block writes to implementation files until `**Current Phase:**` is advanced past `Requirements` (which happens when `/lets-begin` runs). Requirements docs themselves are always writeable.
