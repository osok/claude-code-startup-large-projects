---
name: lets-begin
description: Phase transition gate — verify requirements approved, then advance into autonomous Architecture → Design → Planning → Implementation → Review execution.
---

# Lets Begin

**This is THE gate** where the user hands off from Requirements to autonomous execution. The requirements-gate hook is enforcing the boundary — invoking this skill is what crosses it.

1. **Check for requirements** in `requirement-docs/` (skip `README.md` and `_sample-requirements.md`).
2. **If no requirements exist:** Invoke `@requirements` agent to collect interactively. Stop here until requirements are produced.
3. **If requirements exist:** Present a concise summary (3-5 bullets) and ask user for approval.
   - If user wants changes, allow modifications via `@requirements` agent, then re-present.
   - If user denies, stop.
4. **Once user explicitly approves:**
   - Update `**Current Phase:**` in `CLAUDE.md` Current Work to `Architecture`.
   - Update `**Status:**` to `In Progress (Autonomous)`.
   - Update Document Sequence Tracker row status to `Architecture`.
5. **Begin autonomous execution** per the Orchestration Model and Unified Agent Workflow in `CLAUDE.md`. The parent Claude Code session takes the orchestrator role — performing the protocol in `.claude/agents/task-manager.md` directly:
   - Initialize `project-docs/activity.log` (or read last `log_seq` if it exists).
   - Step 3a: Invoke `@architect` to produce `project-docs/adrs/ADR-001-naming-conventions.md` FIRST (see CLAUDE.md § Naming Conventions). No further architectural work proceeds until ADR-001 exists.
   - Step 3b onward: Continue per task-manager.md workflow order.
6. **Update `**Current Phase:**`** at every phase boundary BEFORE invoking the first agent of the new phase.

**Boundaries (HARD stops during autonomous execution):**
- Code review findings gate — every CR-ID must be `verified` before Testing.
- Testing execution gate — orchestrator prepares the testing phase but waits for explicit user instruction to fire the test runner.
- Phase-boundary surprises — material scope changes stop and report.
