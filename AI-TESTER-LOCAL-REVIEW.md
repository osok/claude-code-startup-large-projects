# AI-Tester-Local → Startup-Large Migration Review

Inline-reviewable proposal for porting changes from `/ai/work/claude-code/ai-tester-local` into this project, plus modernization recommendations.

## How to use this document

Each item has an **Approve / Deny** checkbox you mark inline, and a **Notes:** line for caveats. Each item is labeled:

- `[TRANSFER]` — copy from ai-tester-local as-is (or with trivial adaptation).
- `[TRANSFER+ADAPT]` — copy with named, specific adaptations called out.
- `[RECOMMEND]` — Claude's modernization suggestion, not present in ai-tester-local.
- `[SKIP]` — present in ai-tester-local but identified as project-specific noise; flagged here only so you can confirm I correctly excluded it.

After you mark this up, I'll apply only the **Approve**d items.

---

## Section 1 — Orchestration Model (Replace @task-manager subagent with main orchestrator)

This is the largest behavioral change. It threads through CLAUDE.md, every agent doc, and the workflow tables.

### 1.1 [TRANSFER+ADAPT] Add an "Orchestration Model" section to CLAUDE.md

- [ XX ] Approve  [ ] Deny

Add the ai-tester-local CLAUDE.md `## Orchestration Model` section (lines 89–113 there) verbatim, with the same invariants list. Key points it codifies:

- The orchestrator role is performed by the **top-level Claude Code session** ("parent orchestrator"), NOT by spawning `@task-manager` as a subagent.
- `.claude/agents/task-manager.md` remains the **authoritative spec** for *how* the orchestrator behaves (workflow ordering, status protocol, code review resolution, mid-task request handling, activity-log schema, task-list format, exit gates). The parent follows it verbatim.
- All references to `@task-manager` elsewhere in CLAUDE.md/agents describe the **role**, not an invocation target.
- Five invariants the parent MUST preserve: activity log format/schema; task list format; status protocol; code review gate; memory protocol (we removed Memory MCP, so we'll drop or rewrite this fifth invariant — see 1.3).

**Adaptation needed:** Drop the Memory MCP invariant (5) since we just stripped Memory MCP, or replace it with a more general "agent return-value validation" invariant. **Recommendation:** drop the memory bullet entirely; the other four invariants stand on their own.

**Notes:**

### 1.2 [TRANSFER+ADAPT] Rewrite "Unified Agent Workflow" table to remove `@task-manager` rows

- [XX] Approve  [ ] Deny

In ai-tester-local CLAUDE.md the workflow table still says "@task-manager invokes …", which is misleading after the orchestration-model change. Replace those rows with "Parent orchestrator (per task-manager.md spec)" wording. Functionally identical, but readers stop expecting a subagent.

**Notes:**

### 1.3 [RECOMMEND] Update "Key Decisions & Concepts" item #1 in CLAUDE.md

- [XX ] Approve  [ ] Deny

Current text in our CLAUDE.md: `1. **Task Manager as Sole Writer** - Only Task Manager modifies task lists`

Proposed replacement: `1. **Orchestrator as Sole Writer** — Only the orchestrator role (parent Claude Code session) modifies task lists and the activity log. See [Orchestration Model](#orchestration-model). The @task-manager subagent definition is the authoritative spec for how.`

**Notes:**

### 1.4 [RECOMMEND] Add a top-of-task-manager.md callout: "This file is a specification, not an invocation target"

- [XX ] Approve  [ ] Deny

Insert a 2-line note at the top of `.claude/agents/task-manager.md`:

> **NOTE:** This file specifies the orchestrator role. In this environment the role is performed by the parent Claude Code session, not by spawning `@task-manager` as a subagent. Subagents cannot recursively spawn further sub-subagents, which would defeat the multi-agent decomposition. The parent reads this spec and performs it directly.

**Notes:**

### 1.5 [RECOMMEND] Sweep agent docs for `Task Manager invokes...` / `@task-manager` references

- [ XX] Approve  [ ] Deny

Scan all 26 agent files and replace incoming-edge references to `@task-manager` with "the orchestrator" where the phrasing implies a callable subagent. Leave outgoing references (`return result to Task Manager`) alone — agents still return to whoever called them; the orchestrator just *is* that caller now.

Lightweight sweep — likely <30 edits total across the 26 files.

**Notes:**

---

## Section 2 — Hooks (Currently absent in startup-large)

Both ai-tester-local hooks are pure-Python, zero-dependency, and project-portable.

### 2.1 [TRANSFER] Add `.claude/hooks/requirements-gate.py` (PreToolUse)

- [XX ] Approve  [ ] Deny

Blocks `Write|Edit|MultiEdit|NotebookEdit` on implementation files while Current Work is in the Requirements phase. Reads `**Current Phase:**` from CLAUDE.md's `## Current Work` block. Allows edits to:
- `requirement-docs/**`
- `CLAUDE.md` itself
- `project-docs/document-sequence-tracker.md` (only if we adopt 4.1)
- `.claude/**`
- Memory paths under `~/.claude/projects/.../memory/`

Override token: `OVERRIDE-REQUIREMENTS-GATE` in a user message bypasses for one tool call.

**Why this matters for your autonomy model:** This is exactly the mechanism that keeps "let Claude run autonomously after requirements approval" honest — Claude **physically cannot** start writing code until you say `lets begin` (which the gate detects by reading the updated phase line in CLAUDE.md).

**Adaptation needed:** Add a `**Current Phase:**` field to CLAUDE.md's Current Work section (we don't have it yet — see 5.1).

**Notes:**

### 2.2 [TRANSFER] Add `.claude/hooks/check-orchestration-bookkeeping.py` (Stop)

- [ XX] Approve  [ ] Deny

Stop hook that runs at end of every Claude turn. Does NOT block — emits a `systemMessage` if bookkeeping drift is detected so the parent can self-correct on the next turn. Silent no-op when `project-docs/` doesn't exist.

Drift checks:
1. **Activity log monotonicity** — `log_seq` strictly increasing, no skips/dupes.
2. **JSONL well-formedness** — every recent line parses.
3. **Task summary ↔ detail parity** — every non-pending TXXX in the summary table has a matching `### TXXX —` detail block, and vice versa.
4. **In-progress task ↔ activity log consistency** — every `in-progress` row in the summary either has a recent log entry referencing it OR its last log action is terminal (COMPLETE/TEST_PASS/REVIEW_PASS), in which case the summary is stale.

LOG_TAIL_LINES = 200, TERMINAL_ACTIONS = {COMPLETE, TEST_PASS, REVIEW_PASS}.

**Why this matters for your watchability model:** When you're watching via Kanban + Agent Flow, this hook is what nudges Claude to flip stale `in-progress` rows back into shape before the Kanban app shows them wrong.

**Notes:**

### 2.3 [TRANSFER] Add `.claude/settings.json` wiring

- [XX ] Approve  [ ] Deny

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Write|Edit|MultiEdit|NotebookEdit",
      "hooks": [{"type": "command", "command": "python3 .claude/hooks/requirements-gate.py", "timeout": 5}]
    }],
    "Stop": [{
      "hooks": [{"type": "command", "command": "python3 .claude/hooks/check-orchestration-bookkeeping.py 2>/dev/null || true", "timeout": 10}]
    }]
  }
}
```

`settings.local.json` (the per-user override file) is excluded — it's developer-specific and shouldn't be committed.

**Notes:**

---

## Section 3 — Commands as Slash Commands (Skills) vs Keywords

Per your direction: some command gates better as skills (`/slash` triggered), some remain as keywords. Below is my categorization. Each item: approve the categorization, or override.

### 3.1 [RECOMMEND] Convert to slash command (skill): `/new-work`

- [ XX] Approve  [ ] Deny

**Why slash:** Discrete entry point that takes input parameters (work description, optional component). Naturally maps to a slash command with arguments. Slash discoverability via `/` autocomplete also helps you remember it exists.

**Notes:**

### 3.2 [RECOMMEND] Convert to slash command (skill): `/lets-begin`

- [ XX] Approve  [ ] Deny

**Why slash:** This is THE phase-transition gate where you hand off from Requirements to autonomous execution. Slash command makes it explicit and discoverable. Pairs cleanly with the requirements-gate hook: invoking the skill updates `**Current Phase:**` in CLAUDE.md, the hook stops blocking.

**Notes:**

### 3.3 [RECOMMEND] Convert to slash command (skill): `/continue`

- [ XX] Approve  [ ] Deny

**Why slash:** Frequent resumption command. Slash form is faster to type.

**Notes:**

### 3.4 [RECOMMEND] Convert to slash command (skill): `/initialize`

- [ XX] Approve  [ ] Deny

**Why slash:** Destructive reset; slash form makes the intent unmistakable and harder to fire by accident in mid-conversation.

**Notes:**

### 3.5 [KEEP AS KEYWORD] Component commands (`list components`, `target {id}`, `show component {id}`, `add component`, `impact {id}`, `untarget`)

- [ XX] Approve  [ ] Deny

**Why keyword:** Fluent in-conversation usage ("target gateway-auth and let's investigate the deps"). Slash form adds typing friction for what's effectively a query/navigation language. Also: there are 6 of them with arguments, and slash autocomplete gets crowded.

**Notes:**

### 3.6 [RECOMMEND] Convert to slash command (skill): `/store-work` and `/show-backlog` (after 4.4 adopted)

- [XX ] Approve  [ ] Deny

**Why slash:** Discrete actions, infrequent, naturally parameterized. Slash form distinguishes "add to backlog" from in-conversation chatter.

**Notes:**

### 3.7 [RECOMMEND] Convert to slash command (skill): `/doc-archive` (after 4.5 adopted)

- [XX ] Approve  [ ] Deny

**Why slash:** Discrete, infrequent, no parameters. Classic slash-command shape.

**Notes:**

### 3.8 [RECOMMEND] Skill implementation pattern

- [XX ] Approve  [ ] Deny

Each skill lives at `.claude/skills/{name}.md` with:

```yaml
---
name: {name}
description: One-line trigger description
---

# {Title}

{Same workflow content currently in CLAUDE.md under the `### {command} Workflow` heading}
```

CLAUDE.md keeps a short pointer table `| Command | Skill File | Trigger |` and removes the long workflow blocks (they live in the skill files now). Net effect: CLAUDE.md gets shorter and more navigable; skill content is loaded on-demand when the slash command fires.

**Notes:**

---

## Section 4 — CLAUDE.md Additions

### 4.1 [TRANSFER] Externalize Document Sequence Tracker

- [ XX] Approve  [ ] Deny

Replace the inline `## Document Sequence Tracker` table in CLAUDE.md with a pointer to `project-docs/document-sequence-tracker.md`. The tracker is read/written frequently (every `new work`), and keeping it inline bloats CLAUDE.md which is always loaded.

CLAUDE.md keeps:
```
## Document Sequence Tracker

**File:** `project-docs/document-sequence-tracker.md`

This tracker is maintained in an external file to keep CLAUDE.md concise. Read the file to look up sequence numbers, artifact locations, and statuses.

**Agent instructions:**
- **`new work`**: Read the tracker file to determine the next sequence number. Add a new row when creating a work item.
- **`initialize`**: Clear all rows in the tracker file except the header.
- **`lets begin` / `continue`**: Read the tracker file to understand project history and locate artifacts for the current sequence.
```

`project-docs/document-sequence-tracker.md` gets created on first `new work` with header rows.

**Notes:**

### 4.2 [TRANSFER+ADAPT] Add `**Current Phase:**` field to Current Work section

- [XX ] Approve  [ ] Deny

ai-tester-local's Current Work block has `**Current Phase:** Phase 1 — Requirements`. We need this field for two reasons:
- The requirements-gate hook reads it (see 2.1).
- It makes phase state machine-readable for the Kanban app / Agent Flow.

Add to CLAUDE.md template:
```
**Seq:** ... | **Name:** ...
**Status:** ...
**Current Phase:** Phase 1 — Requirements
```

Phase names match the hook's gated markers: `Requirements`, `Not Started`, `Awaiting Requirements`, `Architecture`, `Design`, `Planning`, `Implementation`, `Review`, `Testing`, `Documentation`, `Complete`.

**Adaptation:** Update the `initialize` skill / workflow and `new work` skill / workflow to set this field; update the orchestrator to advance it at every phase transition.

**Notes:**

### 4.3 [SKIP] Do NOT transfer "Tests Run in Docker — No Exceptions" section

- [XX ] Approve  [ ] Deny

ai-tester-local has 50+ lines about Docker-only test execution. **This is project-specific to ai-tester-local** (which has core/backend/frontend/PM-agent Docker test images). Generic startup-large should not impose this. Keep environment isolation rules (which we already have), but no Docker mandate.

Marking as "Approve" means: confirm I'm correctly excluding this.

**Notes:**

### 4.4 [TRANSFER] Add `store work` / `show backlog` commands

- [XX ] Approve  [ ] Deny

ai-tester-local adds two commands for managing a backlog at `requirement-docs/Backlog-work-list.md`:

- **`store work`** — adds a `BW-NNN` work item to the backlog with priority, components, origin, references, what-exists, what-is-missing fields. Useful when you discover work mid-flow that shouldn't derail the current sequence.
- **`show backlog`** — displays the backlog summary with status counts.

Together they let Claude park "we should also fix X" findings instead of either dropping them or expanding scope mid-sequence. Pairs well with the no-unsolicited-backlog rule (5.4): only added when user asks.

**Notes:**

### 4.5 [TRANSFER+ADAPT] Add `doc-archive` command

- [XX ] Approve  [ ] Deny

Regenerates all doc overview READMEs (parallel) and packages everything into a zip:
1. Launch 4 parallel documentation agents to update `project-docs/adrs/README.md`, `project-docs/README.md`, `design-docs/README.md`, `dev-docs/README.md`.
2. Run `./scripts/build_docs_archive.sh` to zip `dev-docs/ + project-docs/ + requirement-docs/ + design-docs/`.

**Adaptation:** The script doesn't exist in startup-large yet. I'd need to create `scripts/build_docs_archive.sh`. Want me to (a) include the script creation in the migration, (b) wait until you actually need an archive, or (c) skip entirely?

**Notes:**

### 4.6 [RECOMMEND] Mandatory "Naming Conventions ADR" as Architect's first deliverable

- [ ] Approve  [ ] Deny

**Revised from original [SKIP] after user discussion (see below).**

Add a workflow rule to the Architect agent: **before any other architectural decision, the Architect produces `project-docs/adrs/ADR-001-naming-conventions.md`** declaring case style PER LAYER and the cross-layer serialization contract. This ADR is then referenced by every convention file under `conventions/developer/*.md`, every Code Reviewer, and the new Conventions Reviewer (see 6.7).

**ADR-001 must cover, at minimum:**

| Layer | Decision required | Default if architect has no preference |
|---|---|---|
| Python identifiers | `snake_case` (functions, vars), `PascalCase` (classes), `UPPER_SNAKE` (constants) | snake_case / PascalCase / UPPER_SNAKE |
| TypeScript/JavaScript | `camelCase` (vars, funcs), `PascalCase` (types, components), `UPPER_SNAKE` (consts) | camelCase / PascalCase / UPPER_SNAKE |
| Go (if applicable) | `camelCase` (private), `PascalCase` (exported) — **dictated by the language**; no choice | language-mandated |
| Java/Kotlin (if applicable) | `camelCase` / `PascalCase` / `UPPER_SNAKE` | camelCase / PascalCase / UPPER_SNAKE |
| SQL tables & columns | one of `snake_case` / `camelCase` | `snake_case` |
| Environment variables | always `SCREAMING_SNAKE_CASE` | SCREAMING_SNAKE_CASE (not negotiable) |
| YAML/JSON config keys | one of `snake_case` / `camelCase` / `kebab-case` | `snake_case` |
| URL path segments | typically `kebab-case` | `kebab-case` |
| JSON API field names (on the wire) | `snake_case` or `camelCase` | match the **producing** language's idiom |
| Queue routing keys / event names | one of `snake_case` (`user.created`) or `dot.notation` | `snake_case` with dot separators |
| File names (per language) | follow language convention | per-language |

**Cross-layer serialization contract** — ADR-001 must also explicitly state, for every layer boundary, how identifiers map:

- Python `user_id` → JSON `user_id` (snake-through) OR `userId` (via Pydantic alias) — pick one project-wide
- DB column `user_id` → ORM attribute `user_id` (matched) OR `userId` (aliased) — pick one
- TypeScript `userId` → JSON `userId` (camel-through) OR `user_id` (via serializer) — pick one
- Env var `DATABASE_URL` → code constant `DATABASE_URL` (matched) — non-negotiable

**Why this works where "one case for everything" fails:** Go literally uses case as language syntax (`getThing` is private, `GetThing` is public — you cannot force snake_case without breaking compilation). Forcing all layers to one style fights linters, breaks framework conventions (React props, etc.), and produces un-idiomatic code that every developer reading it has to mentally unwrap. The architect decides each layer's case ONCE, the mapping is explicit, and after that everything is mechanical.

**Adaptation needed:**
- New constraint in `architect.md`: first ADR produced MUST be naming conventions; no further architecture work proceeds until ADR-001 exists.
- Every file in `conventions/developer/` adds a line at the top: "See `project-docs/adrs/ADR-001-naming-conventions.md` for project-wide case decisions and cross-layer mappings."
- All three existing code reviewers reference ADR-001 in their reviews.

**Notes:**

### 4.7 [TRANSFER] Add Activity Log "Sole Writer" clarification

- [ XX] Approve  [ ] Deny

Update CLAUDE.md's `## Activity Log` section "Sole Writer" line:

Current: `**Sole Writer:** Task Manager (adds log_seq, work_seq, timestamp, parent_log_seq, duration_ms to agent entries)`

Proposed: `**Sole Writer:** the orchestrator role (see [Orchestration Model](#orchestration-model)). In this environment that is the parent Claude Code session, which writes log_seq, work_seq, timestamp, parent_log_seq, duration_ms to agent entries directly. Sub-agents return <log-entry> blocks; the parent merges the orchestrator-managed fields and appends the line.`

**Notes:**

### 4.8 [RECOMMEND] Drop the "IMPORTANT preserve CLAUDE.md in compression" preamble

- [ ] Approve  [ XX] Deny, I have found that this to be not true, it is has fixed a lot of the drift that I have been seeing over time.

ai-tester-local has a 4-line preamble asking that CLAUDE.md be preserved in context compression with an `END CLAUDE.MD` tag. **Not needed in current Claude Code** — CLAUDE.md is always re-loaded via the system reminder mechanism, so context compression doesn't drop it. Skip this addition.

Marking as "Approve" means: confirm I'm correctly excluding this.

**Notes:**

---

## Section 5 — Bake User Feedback into Agent Behavior

ai-tester-local accumulated 13 user-feedback memory files. The behaviors they encode should be codified into our agent docs / CLAUDE.md so the same lessons don't have to be re-learned.

### 5.1 [TRANSFER] Strict task list status keywords (no synonyms)

- [ xx] Approve  [ ] Deny

From `feedback_status_field_strict_keyword.md`: the **Status** field in the task list summary table accepts ONLY the literal keywords `pending`, `in-progress`, `blocked`, `complete`, `failed`. No synonyms ("done", "todo", "wip"), no decorations ("in progress" with space, "complete ✓"). The external Kanban app parses these literally.

Add a sentence to task-manager.md `### Statuses` section: "These are literal keyword values. Do not substitute synonyms or add decorations — the external Kanban application parses them exactly."

**Notes:**

### 5.2 [TRANSFER] Em-dash delimiter in task headers

- [ xx] Approve  [ ] Deny

From `feedback_task_list_format.md`: task detail headers MUST use em-dash: `### T001 — Create schema` (not hyphen, not en-dash). The Stop hook's `check_summary_vs_detail` parser keys on `### (T\d+)\s+—` (literal em-dash). Hyphen breaks the parity check.

Add a sentence to task-manager.md Task Detail Rules: "Use em-dash (`—`, U+2014), not hyphen, in task detail headers. The bookkeeping hook parses on em-dash specifically."

**Notes:**

### 5.3 [TRANSFER] Task list created BEFORE execution, not during

- [ xxx] Approve  [ ] Deny

From `feedback_tasklist_before_execution.md` and `feedback_task_list_first.md`: the full task list is created at the end of Planning phase (step 6a in workflow). No tasks should be executed before the task list exists with all expected tasks listed. New tasks discovered mid-execution are inserted into the task list before their agent is invoked.

Add to task-manager.md: existing language already covers this. Verify wording is strong enough and add one line: "Task list MUST exist in full before Implementation phase begins. New tasks added during Implementation are inserted into the file before the agent for that task is invoked."

**Notes:**

### 5.4 [TRANSFER] No premature testing

- [xx ] Approve  [ ] Deny

From `feedback_no_premature_testing.md`: **Claude NEVER launches tests unless the user EXPLICITLY says to run them.** This was violated multiple times in ai-tester-local with real cost. The phase gate already enforces "no testing while code review findings open", but this rule is broader: even when the gate would allow it, don't actually fire the test runner without user direction.

Add to test-runner.md as a **CRITICAL** constraint at the top:
> **CRITICAL: Never execute tests autonomously.** Tests run only when the user explicitly says so (`run tests`, `test now`, etc.). Phase advancement to "Testing" prepares the environment and test plan but does not fire the test runner. The orchestrator stops at the Testing-phase boundary and waits for explicit user instruction.

**Adaptation note for your autonomy vision:** You wanted the orchestrator autonomous through Implementation → Review → Documentation. Testing was implicit in that. **I'd recommend keeping a manual gate at the Testing boundary** based on this feedback — but flag it as a choice. If you want fully autonomous testing, override this item.

**Notes:**

### 5.5 [TRANSFER] No unsolicited backlog entries

- [ xx] Approve  [ ] Deny

From `feedback_no_unsolicited_backlog.md`: don't file backlog items (`store work`) unless the user asks. Claude discovering "this should be done later" must surface it in conversation, not silently add to the backlog.

Add to the `store work` skill/command doc: "Only invoked by user request. Do not file backlog items autonomously — surface discovered work in conversation and let the user decide whether it goes in the backlog, the current task list, or nowhere."

**Notes:**

### 5.6 [TRANSFER] No redundant approval requests

- [ xx] Approve  [ ] Deny

From `feedback_no_redundant_approval.md`: once the user has approved an approach for a given phase, don't re-ask for the same approval at every sub-step. Get explicit approval at phase boundaries (e.g., `lets begin`) and trust it through the phase. Re-ask only when the situation materially changes.

Add to CLAUDE.md Working Principles: "Approval scope: when the user approves an approach, treat it as approved for the full phase. Don't re-ask the same approval at each sub-step — re-ask only when the situation materially changes or a new tradeoff appears."

**Notes:**

### 5.7 [TRANSFER] No speculative memory writes

- [ xxx] Approve  [ ] Deny

From `feedback_no_speculative_memory.md`: never write data to memory / audit / activity records before the actual value is known. (E.g., don't log `"files_created": ["src/foo.go"]` before foo.go is actually written.) The activity log is an after-the-fact record, not a plan.

Add to task-manager.md activity log section: "Log entries are written AFTER the action completes, with actual values. Never pre-write log entries with anticipated values; if the action fails or values change, the log is wrong and bookkeeping drift cascades."

**Notes:**

### 5.8 [TRANSFER] Workflow gates override auto mode

- [xxx ] Approve  [ ] Deny

From `feedback_workflow_gates_override_auto_mode.md`: even in auto mode, the `lets begin` / requirements-approval gate is never bypassed. The user must explicitly approve requirements before any architecture/design/implementation work starts.

Add to CLAUDE.md Working Principles: "Workflow gates override auto mode. The `lets begin` gate (requirements approval) and the code-review-findings-verified gate (before testing) are unconditional. Auto mode advances WITHIN gates, not THROUGH them."

**Notes:**

### 5.9 [SKIP] Be-analytical-first / Chrome-only / No-vendor-patching

- [xx ] Approve  [ ] Deny

Three feedback files that are ai-tester-local-specific:
- `feedback_be_analytical_first.md` — generic enough that current "Working Principles" already covers it.
- `feedback_chrome_only.md` — Chrome DevTools MCP usage specific to ai-tester-local's browser automation. N/A here.
- `feedback_no_vendor_patching.md` — about not patching `vendor/mcp-tools/` tarballs. N/A here.

Marking as "Approve" means: confirm I'm correctly excluding these.

**Notes:**

---

## Section 6 — Modernization Recommendations (Not in ai-tester-local)

These align with the autonomy + watchability vision you described.

### 6.1 [RECOMMEND] Define "Autonomous Mode" explicitly in CLAUDE.md

- [ xx] Approve  [ ] Deny

Add a new section after Orchestration Model:

```markdown
## Autonomous Mode

Once `lets begin` is invoked and requirements are approved, the orchestrator proceeds autonomously through Architecture, Design, Planning, Implementation, and Review phases — making decisions, documenting them, and advancing the task list without user prompts.

**The user observes via:**
- Kanban app (reading `project-docs/tasks/{seq}-{short-name}-tasks.md`)
- Agent Flow VS Code plugin (reading `project-docs/activity.log`)

**Autonomous mode boundaries (HARD stops the orchestrator MUST respect):**
1. **Requirements approval gate** — never bypassed (enforced by `.claude/hooks/requirements-gate.py`)
2. **Code review findings gate** — every CR-ID `verified` before Testing
3. **Testing execution gate** — orchestrator prepares the testing phase but waits for explicit user instruction to fire the test runner (see test-runner.md)
4. **Phase-boundary surprises** — if the orchestrator discovers something that materially changes scope or contradicts an approved decision, it stops and reports rather than deciding unilaterally

**Within those boundaries, the orchestrator does NOT ask:**
- Routine architectural decisions (documented in ADRs)
- Routine design choices (documented in design-docs/)
- Routing of code review findings to fix agents
- Re-review loops
- Documentation generation
```

**Notes:**

### 6.2 [RECOMMEND] Add `**Current Phase:**` advancement to the orchestrator spec

- [xx ] Approve  [ ] Deny

In task-manager.md, add an explicit step at every phase boundary: "Update `**Current Phase:**` field in CLAUDE.md to the new phase before invoking the first agent of that phase." This is what makes the requirements-gate hook unblock at the right moment AND what gives the Kanban app / Agent Flow a single source of truth for "where are we right now".

**Notes:**

### 6.3 [RECOMMEND] Activity log schema additions for Agent Flow watchability

- [xx ] Approve  [ ] Deny

Two optional fields that are zero-cost for the orchestrator and high-value for an external watcher:

- `phase_transition: {from: "design", to: "planning"}` — included only on the first log entry of a new phase. Lets Agent Flow render phase boundaries cleanly.
- `task_status_change: {task_id: "T015", from: "in-progress", to: "complete"}` — included on COMPLETE entries with a `task_id`. Lets the Kanban app react to status flips without re-parsing the markdown.

**Decision:** Are these worth adding, or do you prefer the schema stay minimal and let watchers parse what they need?

**Notes:**

### 6.4 [RECOMMEND] Add a `**Workspace Visible To:**` field (optional)

- [ xx] Approve  [ ] Deny

In Current Work section, optional line: `**Workspace Visible To:** kanban, agent-flow` — declares which external watchers are active for this work item. Skill / hook behavior can adapt (e.g., if kanban isn't listed, the strict em-dash rule could relax). Marginal value; flagging in case it resonates.

**Notes:**

### 6.5 [RECOMMEND] Pre-flight check skill: `/preflight`

- [xx ] Approve  [ ] Deny

A new skill that runs before `/lets-begin` and reports:
- Requirements doc exists and parses
- All REQ-IDs are well-formed
- Component context is set if work is component-scoped
- `project-docs/` exists, activity log is appendable
- Hooks are wired and executable

Lets you catch setup gaps before triggering the autonomy phase. Optional but cheap.

**Notes:**

### 6.6 [RECOMMEND] Stop-hook: emit phase-transition systemMessages

- [xx ] Approve  [ ] Deny

Extend `check-orchestration-bookkeeping.py` to additionally emit a systemMessage when the most recent log entry crosses a phase boundary (`phase` field differs from prior). Gives the parent orchestrator a self-reminder when phase transitions are happening — useful for catching cases where the orchestrator forgot to update `**Current Phase:**` in CLAUDE.md.

**Notes:**

### 6.7 [RECOMMEND] New code reviewer agent: `code-reviewer-conventions`

- [ ] Approve  [ ] Deny

**Added from user discussion of 4.6 — the dedicated "juggernaut catcher" for cross-layer naming/case mismatches.**

Add a fourth code reviewer that runs in parallel with the existing three (requirements, security, integration). Its sole job is catching the class of bugs that cost "20 iterations to resolve, fixing one error at a time" — silent serialization breaks caused by case/naming drift across layer boundaries.

**File:** `.claude/agents/code-reviewer-conventions.md`

**What it checks:**

1. **Per-layer case compliance against ADR-001** — every Python identifier matches the Python rule, every TS identifier matches the TS rule, every SQL column matches the SQL rule, every env var matches `SCREAMING_SNAKE_CASE`, etc.
2. **Cross-layer boundary integrity:**
   - DB column ↔ ORM model attribute (matched or aliased per ADR-001)
   - ORM attribute ↔ API serializer output (matched or aliased per ADR-001)
   - API JSON field ↔ frontend type / API client (matched or aliased)
   - Env var name ↔ code reference (`os.environ["DATABASE_URL"]` matches `.env.example`)
   - Queue routing key (producer) ↔ subscription pattern (consumer)
   - Config file key ↔ code reader (YAML/JSON keys match what the parser asks for)
   - URL path segment ↔ router declaration
   - GraphQL/protobuf schema names ↔ generated code usage
3. **Inconsistent variants of the same concept** — flags `user_id` / `userId` / `userID` / `UserID` appearing for the same logical field across files, even if each is locally correct, because the cross-layer mapping wasn't applied.
4. **Drift from ADR-001** — flags any net-new case style that wasn't declared in ADR-001 (e.g., a `kebab-case` config key in a project that declared `snake_case` config).

**Outputs (findings tracker entries):**

```
| CR-N | conventions | high | Field 'userId' in src/types/User.ts not aliased to 'user_id' for API boundary (ADR-001 §JSON serialization) | Developer | T0XX | open | |
| CR-N | conventions | medium | Env var 'database_url' in docker-compose.yml violates SCREAMING_SNAKE_CASE rule | Developer | T0XX | open | |
```

**When it runs:**
- Same trigger as the other 3 reviewers (Step 8 of Unified Agent Workflow), in parallel with them.
- Re-review loop (Step 10) applies identically: if it finds issues, fixes are routed through the standard CR resolution workflow until status = `verified`.
- The Implementation → Testing exit gate (all CR-IDs `verified`) automatically extends to this reviewer's findings — no separate gate logic needed.

**Why a dedicated agent vs. extending an existing one:**
- Security reviewer is focused on OWASP — naming isn't security.
- Integration reviewer focuses on stubs and wiring gaps — adjacent, but its prompt is tuned to "does this code path exist", not "do these strings match".
- Requirements reviewer checks against REQ-IDs — different axis.
- A focused prompt + explicit ADR-001 loading + boundary-pair checklist gets dramatically better results than bolting checks onto a reviewer that has other priorities.

**Updates needed elsewhere:**
- `CLAUDE.md` Sub-Agent Index → add row in "Code Review Agents" table.
- `CLAUDE.md` Unified Agent Workflow → Step 8 lists 4 reviewers in parallel (not 3).
- `task-manager.md` Code Review Resolution Workflow → mention the 4th reviewer where it lists severities and routing.

**Notes:**

---

## Section 7 — Things deliberately NOT transferred (confirm correct exclusion)

These are ai-tester-local-specific and should NOT come over:

### 7.1 [SKIP] All ai-tester-local domain content

- [xx] Approve  [ ] Deny  (Approve = "yes, correctly excluded")

Things like ADR-080 naming conventions, processor categories table, enumeration architecture references, dev-docs/ structure, Docker test image specifics, `core` library specifics, `pm-agent` specifics, the Seq 138 work item content, etc.

**Notes:**

### 7.2 [SKIP] ai-tester-local's MEMORY.md project notes

- [ xx] Approve  [ ] Deny  (Approve = "yes, correctly excluded")

The 50+ project-memory entries in `/home/michael/.claude/projects/-ai-work-claude-code-ai-tester-local/memory/MEMORY.md` are project-state snapshots specific to that project's git history. Not portable. Your startup-large project will build its own memory over time.

**Notes:**

### 7.3 [SKIP] `scheduled_tasks.lock` and `settings.local.json`

- [xx ] Approve  [ ] Deny  (Approve = "yes, correctly excluded")

Per-user/runtime files that don't belong in source control or in the framework template.

**Notes:**

---

## Section 8 — Order of Implementation

If items 1.1–7.3 are approved/denied, I propose this implementation order (single PR, but ordered commits so we can checkpoint):

1. **Foundation:** Add CLAUDE.md preserve-preamble (4.8 denied my drop-recommendation = ADD it), 4.7 (activity log clarification), 4.2 (Current Phase field), 4.1 (sequence tracker externalization), 1.1 (orchestration model), 1.3, 1.4
2. **Hooks:** 2.1, 2.2, 2.3
3. **Skill conversion:** 3.8 (pattern), then 3.1, 3.2, 3.3, 3.4, 3.6, 3.7 — keeping keyword equivalents per CLAUDE.md table for back-compat
4. **Workflow language sweep:** 1.2, 1.5
5. **New commands:** 4.4 (store work / show backlog), 4.5 (doc-archive)
6. **Naming conventions:** 4.6 (architect produces ADR-001 first) + 6.7 (new `code-reviewer-conventions` agent)
7. **Behavior codification:** 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8
8. **Modernization:** 6.1 (autonomous mode section), 6.2 (phase advancement), 6.3 (log additions), 6.4 (workspace-visible-to, if approved), 6.5 (preflight skill), 6.6 (phase-transition systemMessage)

Each step is a single Conventional Commit. Run after each step: a smoke check that CLAUDE.md still parses and the hooks (if installed) run without error.

- [xx ] Approve order  [ ] Reorder  (specify in notes)

**Notes:**

---

## Sign-off

When you've marked up this document, tell me to "apply approved items" (or similar) and I'll work through the order above, skipping any **Deny**'d items. I'll commit after each Section.

**General notes / overrides / context I missed:**
