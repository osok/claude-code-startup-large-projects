---
name: continue
description: Resume current work item from its task list. The parent orchestrator picks up where it left off, advancing the next actionable task per task-manager.md protocol.
---

# Continue

Resumes work from the current task list. **The parent Claude Code session performs the orchestrator role** (per [Orchestration Model](../../CLAUDE.md#orchestration-model)) — it does NOT spawn `@task-manager` as a subagent.

1. **Read `CLAUDE.md` Current Work** to identify `Seq`, `Name`, `Current Phase`, and any `Component:` field.
2. **Read the task list** at `project-docs/tasks/{seq}-{short-name}-tasks.md`. If missing, report and stop.
3. **Read `project-docs/activity.log`** tail to recover `log_seq` and last action context.
4. **Reset stale tasks** — any task with status `in-progress` is from an interrupted session. Set those back to `pending` and log a `DECISION` entry: "Reset stale task {ID} to pending after session resume".
5. **Find next actionable task** — first `pending` task whose `Blocked-By` dependencies are all `complete`. If only `blocked` tasks remain whose blocker is now `complete`, unblock them.
6. **Honor autonomous-mode boundaries** (see `CLAUDE.md` § Autonomous Mode):
   - Stop before firing `@test-runner` unless the user has explicitly authorized this run.
   - Stop if every code review finding is not yet `verified` and the next task would advance into Testing.
   - Stop if a phase-boundary surprise materially changes scope.
7. **Update task list** — set the chosen task to `in-progress` BEFORE invoking the agent. Write a `START` log entry. Pass component context if `**Component:**` is set in Current Work.
8. **Invoke the assigned agent** (per the task's `Agent` field) via the Task tool, then immediately on return:
   - Update task status to `complete` / `blocked` / `failed`.
   - Append `COMPLETE` or `ERROR` log entry with `duration_ms` and `parent_log_seq` linkage.
   - Update the per-task detail section's `**Resolution:**` block.
9. **Repeat from step 5** until: all tasks complete, a hard-stop boundary is hit, the user intervenes, or a phase transition is required.
10. **At phase transitions**, update `**Current Phase:**` in `CLAUDE.md` Current Work BEFORE invoking the first agent of the new phase. Write a `DECISION` log entry recording the transition.

**Important:** Do NOT invoke individual agents directly outside this loop — the orchestrator preserves the activity log and task list invariants. See `.claude/agents/task-manager.md` for the full spec the orchestrator follows.
