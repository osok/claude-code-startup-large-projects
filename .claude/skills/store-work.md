---
name: store-work
description: Add a work item to the backlog (requirement-docs/Backlog-work-list.md) for future work. User-invocable only — never file backlog items unsolicited.
---

# Store Work

Adds a work item to the backlog for future work.

> **CRITICAL — user-invocation only.** Only file a backlog item when the user explicitly asks (e.g., "store work", "backlog this", "add to backlog"). Agents and the orchestrator MUST NOT file backlog items on their own initiative, even when they discover incomplete or deferred work. See feedback memory `feedback_no_unsolicited_backlog`.

1. **Read the backlog file** at `requirement-docs/Backlog-work-list.md`. If it does not exist, create it with this header:

   ```markdown
   # Backlog Work List

   Items captured here are NOT scheduled work. They are deferred ideas, partial work, or follow-up tasks the user has explicitly asked to track.

   **Status legend:** `pending` (not started) | `in_progress` (being worked) | `blocked` (waiting on something) | `complete` (done)

   ---
   ```

2. **Determine next ID** — scan the file for the highest `BW-NNN`, increment by 1, zero-pad to 3 digits.
3. **Ask the user** what work needs to be done. Gather:
   - **Title** (short, descriptive)
   - **Description** (what needs to happen)
   - **Priority** (High / Medium / Low — suggest based on context)
   - **Components** affected (if known)
   - **Origin** (how this was discovered — code review, user request, bug, etc.)
4. **Research references** — search for related requirement docs, design docs, task lists, and existing code (stubs, TODOs) relevant to this work item. Include file paths and specific references.
5. **Append the work item** using this template:

   ```markdown
   ### BW-NNN: {Title}

   | Field | Value |
   |-------|-------|
   | **ID** | BW-NNN |
   | **Status** | `pending` |
   | **Priority** | {High/Medium/Low} |
   | **Components** | {component list} |
   | **Origin** | {how discovered} |

   **Description:**
   {detailed description}

   **References:**
   {requirement IDs, file paths, task list references, existing code locations}

   **What exists:**
   {any stubs, partial implementations, or related code already in place}

   **What is missing:**
   {specific deliverables needed}

   ---
   ```

6. **Confirm to user** with the BW ID and a summary.
