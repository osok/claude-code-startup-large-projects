---
name: initialize
description: Reset the project to a blank slate, then ask what to build. Destructive — clears requirement-docs, design-docs, project-docs (except adrs/), activity log, and Document Sequence Tracker.
---

# Initialize Project

When invoked, perform these actions **before** asking what to build:

1. **Reset Current Work section** in `CLAUDE.md` to blank state:
   - `**Seq:** (pending) | **Name:** (pending)`
   - `**Status:** Not Started`
   - `**Current Phase:** Awaiting Requirements`
   - `**Task List:** (none)`
2. **Reset README.md** to minimal template with project name placeholder
3. **Reset Document Sequence Tracker** — Clear all rows except header in `project-docs/document-sequence-tracker.md`
4. **Clear project artifacts** (if they exist):
   - Delete files in `requirement-docs/` (except `README.md` and `_sample-requirements.md`)
   - Delete files in `design-docs/` (except templates)
   - Delete files in `project-docs/` (except `adrs/` folder structure and `document-sequence-tracker.md`)
   - Clear `project-docs/activity.log` if it exists
   - **Do NOT delete `COMPONENTS.md`** — preserved across resets
5. **After all resets complete**, ask: "What would you like to build?"
