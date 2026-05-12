# Project

## IMPORTANT

When you work to compress the context, make sure to include **ALL** of this document, CLAUDE.MD. It has important notes, that while some may not be important in the current conversation they may be in the future conversation. This is **IMPORTANT**.

A tag **END CLAUDE.MD** is placed at the end of this document to help identify what is in the document. Include all up to that point along with the tag for future compressions.

---

## Current Work

**Seq:** (pending) | **Name:** (pending)
**Status:** Not Started
**Current Phase:** Awaiting Requirements
**Task List:** (none)
**Workspace Visible To:** Kanban app (reads `project-docs/tasks/{seq}-{short-name}-tasks.md`), Agent Flow VS Code plugin (reads `project-docs/activity.log`). The orchestrator MUST keep both files consistent at all times so these external watchers reflect the true state of work.

---

## Sub-Agent Index

### Core Workflow Agents

| Agent | Purpose | Docs |
|-------|---------|------|
| Requirements | Interactive requirements elicitation (ISO 29148) | .claude/agents/requirements.md |
| Architect | Architectural decisions, ADRs, standards | .claude/agents/architect.md |
| Requirements Analyzer | Parse ISO 29148 requirements structure | .claude/agents/requirements-analyzer.md |
| Design Orchestrator | Coordinate design document generation | .claude/agents/design-orchestrator.md |
| Task Manager | Orchestrates workflow, tracks tasks | .claude/agents/task-manager.md |

### Specialized Design Agents

| Agent | Purpose | Output Prefix | Docs |
|-------|---------|---------------|------|
| UI/UX Design | UI/UX and style guides | 01-, 90- | .claude/agents/ui-ux-design-agent.md |
| Data Design | Data architecture designs | 02- | .claude/agents/data-design-agent.md |
| Security Design | Security architecture | 03- | .claude/agents/security-design-agent.md |
| Library Design | Component library designs | 10- | .claude/agents/library-design-agent.md |
| Backend Design | Backend service designs | 20- | .claude/agents/backend-design-agent.md |
| Frontend Design | Frontend application designs | 30- | .claude/agents/frontend-design-agent.md |
| Agent Design | Background worker designs | 40- | .claude/agents/agent-design-agent.md |
| Integration Design | API contracts | 50- | .claude/agents/integration-design-agent.md |
| Infrastructure Design | Cloud/Docker/ECS designs | 60- | .claude/agents/infrastructure-design-agent.md |
| ML Design | Machine learning systems (training, serving, monitoring) | 70- | .claude/agents/ml-design-agent.md |

### Data & Infrastructure Agents

| Agent | Purpose | Docs |
|-------|---------|------|
| Data Agent | Schemas, data dictionaries, migrations | .claude/agents/data-agent.md |
| Deployment | Docker compose, AWS CDK, .env | .claude/agents/deployment.md |

### Development Agents

| Agent | Purpose | Docs |
|-------|---------|------|
| Developer | Implements code following conventions | .claude/agents/developer.md |
| Documentation | User docs, developer docs, code docs | .claude/agents/documentation.md |

### Testing Agents

| Agent | Purpose | Docs |
|-------|---------|------|
| Test Designer | Plans tests from design | .claude/agents/test-designer.md |
| Test Coder | Writes test code | .claude/agents/test-coder.md |
| Test Runner | Executes and categorizes tests | .claude/agents/test-runner.md |
| Test Debugger | Deep debugging, routes fixes | .claude/agents/test-debugger.md |

### Code Review Agents

| Agent | Purpose | Docs |
|-------|---------|------|
| Code Reviewer - Requirements | Completeness against requirements | .claude/agents/code-reviewer-requirements.md |
| Code Reviewer - Security | OWASP vulnerabilities | .claude/agents/code-reviewer-security.md |
| Code Reviewer - Integration | Stubs, wiring gaps | .claude/agents/code-reviewer-integration.md |
| Code Reviewer - Conventions | Cross-layer naming/case mismatches (validates against ADR-001) | .claude/agents/code-reviewer-conventions.md |

### Utility Agents

| Agent | Purpose | Docs |
|-------|---------|------|
| Upgrade | Syncs framework files from source (user-invocable only) | .claude/agents/upgrade.md |

---

## Orchestration Model

**The orchestrator role** — managing phases, invoking specialized agents, writing the activity log, maintaining the task list, gating phase transitions — is performed by **the top-level Claude Code session** (the "parent orchestrator").

- The `@task-manager` subagent definition in [.claude/agents/task-manager.md](.claude/agents/task-manager.md) is the **authoritative specification** for the orchestrator role: workflow ordering, status protocol, code review resolution, mid-task request handling, activity-log schema, task-list format, exit gates. The parent orchestrator follows that spec verbatim.
- The parent orchestrator does **not** invoke `@task-manager` as a subagent. In this environment subagents cannot recursively spawn further sub-subagents, so a `task-manager` subagent cannot fulfill its own contract. The parent does the orchestration directly so that specialized agents (`@architect`, `@design-orchestrator`, `@developer`, `@code-reviewer-*`, `@test-coder`, `@test-runner`, `@documentation`, etc.) each run in their own isolated context with their own toolkits — preserving the multi-agent decomposition that is the whole point of the workflow.
- All references to `@task-manager` elsewhere in this document (workflow tables, command flows, "invoke @task-manager" instructions) describe the **role**, not the implementation. The parent orchestrator performs that role.

**Invariants the parent orchestrator MUST preserve:**

1. **Activity log format** — `project-docs/activity.log` is JSONL with the exact schema in [task-manager.md §Activity Log Management](.claude/agents/task-manager.md). Every field (`log_seq`, `work_seq`, `timestamp`, `agent`, `action`, `phase`, `parent_log_seq`, `requirements`, `task_id`, `details`, `files_created`, `files_modified`, `decisions`, `errors`, `duration_ms`) is required. `log_seq` is monotonic across the entire file (never reused, never skipped). The parent reads the last line on resume to continue numbering. **Do not change the schema.**
2. **Task list format** — `project-docs/tasks/{seq}-{short-name}-tasks.md`. The summary table and per-task detail sections follow the exact format in [task-manager.md §Task List Format](.claude/agents/task-manager.md): summary table with columns `ID | Task | Status | Blocked-By | Agent | Notes`; each task gets a `### {ID} — {Task}` detail section with the 8-field metadata table (Status, Agent, Blocked-By, Requirements, Design Ref, Component, Files, Acceptance), a `**Description:**` block, a `**Resolution:**` block, and a `---` separator. **An external Kanban application watches this file. Any deviation breaks tooling.**
3. **Status protocol** — every task transitions `pending` → `in-progress` → `complete` / `blocked` / `failed` individually; status is set in the task list **before** invoking the agent and updated **immediately** when the agent returns. Never batch.
4. **Code review gate** — every CR finding must be `verified` before testing begins. No exceptions, no overrides.

**When the parent orchestrator is invoked** (entry points):

| User says | Parent orchestrator action |
|---|---|
| `lets begin` | Initialize/append to `project-docs/activity.log`, create `project-docs/tasks/{seq}-{short-name}-tasks.md`, begin phase 3 (Architecture) |
| `continue` | Read current task list, identify next actionable task, set `in-progress`, invoke the assigned agent, write `START` entry, etc. |
| Mid-flow | Continue per task-manager.md protocol |

If the agent system at some future date supports `task-manager`-as-subagent with full Task-tool recursion, this section can be revisited — but the format invariants above remain unconditional.

---

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

**Phase advancement:** The orchestrator updates `**Current Phase:**` in the Current Work section of this file at every phase transition, BEFORE invoking the first agent of the new phase. This is what the requirements-gate hook reads and what external watchers (Kanban, Agent Flow) use as the single source of truth for "where are we right now".

---

## Unified Agent Workflow

| Phase | Step | Agent(s) | Output |
|-------|------|----------|--------|
| **Requirements** | 1 | @requirements | Elicit and document requirements (ISO 29148) → `requirement-docs/` |
| **Orchestration** | 2 | Parent orchestrator (per task-manager.md spec) | **Orchestrates all remaining phases (2-17). Sole activity log writer. See [Orchestration Model](#orchestration-model).** |
| **Architecture** | 3a | @architect (ADR-001 first) | Produce `project-docs/adrs/ADR-001-naming-conventions.md` BEFORE any other architectural work. See [Naming Conventions](#naming-conventions). |
| | 3b | @architect | Remaining architectural decisions, ADRs → `project-docs/adrs/` |
| **Design** | 4 | @requirements-analyzer | Parse requirements structure |
| | 5 | @design-orchestrator | Coordinate specialized design agents |
| | 5a | └─ Foundation | @ui-ux-design, @data-design, @security-design (parallel) |
| | 5b | └─ Core | @library-design, @backend-design (parallel) |
| | 5c | └─ Application | @frontend-design, @agent-design, @ml-design (parallel) |
| | 5d | └─ Integration | @integration-design |
| | 5e | └─ Infrastructure | @infrastructure-design |
| | | | Output: `design-docs/` with prefixed documents |
| **Planning** | 6 | @test-designer, @data-agent | Plan tests; define schemas (parallel) |
| | 6a | Parent orchestrator | Create task list |
| **Implementation** | 7 | @developer(s) | Implement code |
| **Review** | 8 | Code reviewers (4, parallel) | @code-reviewer-requirements, @code-reviewer-security, @code-reviewer-integration, @code-reviewer-conventions |
| | 8a | Parent orchestrator | Collect findings into tracker (CR-IDs), route each to correct agent |
| | 8b | @test-designer | Assess findings for test impact, update test plan |
| | 9 | Routed agents | Fix findings: @architect / @design-orchestrator / @developer as appropriate |
| | 9a | Parent orchestrator | Record resolutions in findings tracker |
| | 10 | Code reviewers (re-review) | Verify fixes, check for new issues (only reviewers that had findings) |
| | 10a | Loop to Step 9 | If still-open or new findings, until all verified |
| **Test Prep** | 11 | @test-designer | Review/update test plan |
| | 12 | @documentation, @deployment | Docs and env setup (parallel) |
| **Testing** | 13 | @test-coder → @test-runner | Write & run tests (test runner fires ONLY on explicit user instruction) |
| | 14 | @test-debugger | On failure: diagnose |
| | 15 | Parent orchestrator → Agent | Route fix |
| | 16 | Loop to Step 13 | Until all pass |
| **Finalize** | 17 | @documentation | Final updates |

**Do NOT duplicate design documents for each work item.** Create work-specific docs (`{seq}-requirements-*.md`, `{seq}-design-*.md`) but update foundational docs (01-, 02-, 03-, etc.) in place. See design-orchestrator.md for the full update pattern.

---

## Key Decisions & Concepts

1. **Orchestrator as Sole Writer** — Only the orchestrator role (parent Claude Code session) modifies task lists and the activity log. See [Orchestration Model](#orchestration-model). The `@task-manager` subagent definition is the authoritative spec for how.
2. **Schemas as Source of Truth** - Data Agent maintains authoritative schemas
3. **Convention Files** - Developer/Test Coder load language-specific conventions; all reference [ADR-001 Naming Conventions](#naming-conventions)
4. **Design Templates** - Comprehensive templates for each component type
5. **Mid-Task Requests** - Agents can request work; orchestrator queues
6. **Test Runner Routing** - Routes failures to appropriate agents
7. **No Dates** - All documents are timeless
8. **Environment Isolation** - NEVER pollute the host machine's global environment (see below)
9. **Naming Conventions Decided Up Front** — The Architect's FIRST deliverable is `project-docs/adrs/ADR-001-naming-conventions.md`. See [Naming Conventions](#naming-conventions). No code is written until ADR-001 exists.

---

## CRITICAL: Environment Isolation

**NEVER install packages, dependencies, or tools globally on the host machine.**

| Language | Isolation Method | Setup Command |
|----------|------------------|---------------|
| Python | Virtual environment | `python -m venv .venv && source .venv/bin/activate` |
| Node.js | Local node_modules | `npm install` (no -g flag) |
| Ruby | Bundler with path | `bundle config set --local path 'vendor/bundle'` |
| Go | Go modules | `go mod init` (default behavior) |
| Rust | Cargo (project-local) | Default behavior |
| Java | Maven/Gradle (project-local) | Default behavior |

**Python:** Always create venv before any `pip install`. Never use `sudo pip install`. Add `.venv/`, `__pycache__/` to `.gitignore`.
**Node.js:** Never use `npm install -g` or `yarn global add`. Use `npx` for CLI tools. Add `node_modules/` to `.gitignore`.
**Enforcement:** Deployment Agent sets up environment before installs. Developer Agent verifies environment is active. Test agents use project environment.

---

## Requirement ID Conventions

Requirements include the sequence number to link them to specific work items.

| Pattern | Type | Example |
|---------|------|---------|
| `STK-{SEQ}-NNN` | Stakeholder | STK-002-001 |
| `REQ-{SEQ}-FN-NNN` | Functional | REQ-002-FN-001 |
| `REQ-{SEQ}-INT-UI-NNN` | UI Interface | REQ-002-INT-UI-001 |
| `REQ-{SEQ}-INT-API-NNN` | API Interface | REQ-002-INT-API-001 |
| `REQ-{SEQ}-DATA-NNN` | Data | REQ-002-DATA-001 |
| `REQ-{SEQ}-NFR-PERF-NNN` | Performance | REQ-002-NFR-PERF-001 |
| `REQ-{SEQ}-NFR-SEC-NNN` | Security | REQ-002-NFR-SEC-001 |
| `REQ-{SEQ}-NFR-ACC-NNN` | Accessibility | REQ-002-NFR-ACC-001 |
| `REQ-{SEQ}-NFR-AVAIL-NNN` | Availability | REQ-002-NFR-AVAIL-001 |
| `REQ-{SEQ}-VER-NNN` | Verification | REQ-002-VER-001 |
| `REQ-{SEQ}-DEP-NNN` | Deployment | REQ-002-DEP-001 |

**Note:** `{SEQ}` is the 3-digit sequence number from Current Work (e.g., 001, 002).

---

## Document Sequence Tracker

**File:** `project-docs/document-sequence-tracker.md`

This tracker is maintained in an external file to keep CLAUDE.md concise. Read the file to look up sequence numbers, artifact locations, and statuses.

**Agent instructions:**
- **`new work`**: Read the tracker file to determine the next sequence number. Add a new row when creating a work item.
- **`initialize`**: Clear all rows in the tracker file except the header.
- **`lets begin` / `continue`**: Read the tracker file to understand project history and locate artifacts for the current sequence.

---

## Commands

All workflow commands are implemented as slash-commands (skills) under `.claude/skills/`. Invoke as `/{command}`. Plain English variants ("lets begin", "continue", etc.) are also recognized — the orchestrator dispatches to the same skill file.

| Command | Skill File | Meaning |
|---------|-----------|---------|
| `/initialize` | [.claude/skills/initialize.md](.claude/skills/initialize.md) | Reset project, ask what to build (destructive) |
| `/new-work` | [.claude/skills/new-work.md](.claude/skills/new-work.md) | Start new work item with fresh sequence, interview for requirements |
| `/lets-begin` | [.claude/skills/lets-begin.md](.claude/skills/lets-begin.md) | Phase transition gate — check requirements, get approval, begin autonomous execution |
| `/continue` | [.claude/skills/continue.md](.claude/skills/continue.md) | Resume current work from task list |
| `/preflight` | [.claude/skills/preflight.md](.claude/skills/preflight.md) | Read-only diagnostic of orchestrator state (no writes, no agent invocations) |
| `/store-work` | [.claude/skills/store-work.md](.claude/skills/store-work.md) | Add a work item to the backlog (user-invocable only) |
| `/show-backlog` | [.claude/skills/show-backlog.md](.claude/skills/show-backlog.md) | Display backlog items with status |
| `/doc-archive` | [.claude/skills/doc-archive.md](.claude/skills/doc-archive.md) | Regenerate doc READMEs, build distributable zip |
| `list components` | (component command) | Show all components from COMPONENTS.md |
| `target {id}` | (component command) | Set active component for subsequent work |
| `show component {id}` | (component command) | Display full details of a component |
| `add component` | (component command) | Interactively add a component to COMPONENTS.md |
| `impact {id}` | (component command) | Show components affected by changes to target |
| `untarget` | (component command) | Clear the active component targeting |

**Keyword recognition:** Each skill file's frontmatter `description` field defines when it fires. The natural-language equivalents in the table below are also recognized.

| Skill | Natural-Language Aliases |
|-------|--------------------------|
| `/initialize` | "initialize", "reset project" |
| `/new-work` | "new work", "start new work", "begin new work item" |
| `/lets-begin` | "lets begin", "let's begin", "begin work" |
| `/continue` | "continue", "keep going", "resume" |
| `/preflight` | "preflight", "where are we", "status check", "health check" |
| `/store-work` | "store work", "add to backlog", "backlog this", "save for later", "track this work" |
| `/show-backlog` | "show backlog", "list backlog", "what's in the backlog", "show work items", "pending work" |
| `/doc-archive` | "doc archive", "build documentation archive", "package docs" |

---

### Component Status Lifecycle

Components follow a three-state lifecycle:

```
pending → active → complete
```

| Status | Meaning | Transition Trigger |
|--------|---------|-------------------|
| `pending` | Registered but no work started | Set on `add component` |
| `active` | Currently being worked on | Set on `target {id}` or `new work` (when component-scoped) |
| `complete` | All work finished, tests passing | Set by Task Manager when all tasks for the component are done |

**Rules:**
- `add component` always sets status to `pending`
- `target {id}` sets status to `active` (component is now being worked on)
- `new work` sets status to `active` when the work item is scoped to a component
- Task Manager sets status to `complete` when the component's work item finishes all phases (implementation, review, testing all pass)
- `untarget` does NOT revert status — once `active`, it stays `active` until completed
- A `complete` component can be re-targeted for new work (status returns to `active`)

### Component Commands

Component commands require `COMPONENTS.md` at the project root. If absent: "No COMPONENTS.md found. Create one with `add component` or manually. See `COMPONENTS.EXAMPLE.md` for the expected format."

| Canonical Command | Also Recognized As |
|-------------------|--------------------|
| `list components` | "show all components", "what components exist", "show components" |
| `target {id}` | "work on {id}", "switch to {id}", "focus on {id}" |
| `show component {id}` | "tell me about {id}", "what is {id}", "describe {id}" |
| `add component` | "register a component", "new component", "create component" |
| `impact {id}` | "what depends on {id}", "blast radius of {id}", "who uses {id}" |
| `untarget` | "clear component", "stop targeting", "unfocus" |

### `list components`

1. Check `COMPONENTS.md` exists, read and validate manifest
2. Display table with columns: ID, Name, Type, Path, Status
3. Apply type filter if specified (e.g., "list agent components")
4. Display count summary by type

### `target {id}`

1. Look up `## {id}` in `COMPONENTS.md`. If not found, show valid IDs and suggest closest match
2. Extract all fields from component's detail section
3. **Update component status to `active`** in both the Summary table and the detail section of `COMPONENTS.md`
4. **Update Current Work in CLAUDE.md:**
   - Write `**Component:** {id}` (after Name, before Status)
   - Write `**Path:** {path}` (after Component, before Status) — using the Path from `COMPONENTS.md`
5. Write `### Component Context` sub-section with hydrated metadata
6. Display component details. If already targeted, previous target is replaced silently

### `show component {id}`

1. Look up `## {id}` in `COMPONENTS.md`. If not found, show valid IDs
2. Extract all fields, compute reverse dependencies, check for associated docs
3. Display full component details including dependencies and dependents

### `add component`

1. If `COMPONENTS.md` doesn't exist, offer to create it
2. Prompt for required fields: ID (`[a-z][a-z0-9-]{0,39}`), Name, Type (frontend/backend/library/agent/gateway/infrastructure/other), Path, Description
3. Prompt for optional fields: Language, Dependencies, Deployment, Port, Owner
4. Validate ID uniqueness and format, warn on unknown dependency references
5. Set Status to `pending` (do NOT prompt for status — it follows the lifecycle automatically)
6. Add row to Summary table and new H2 section to `COMPONENTS.md`
7. Ask about scaffolding the source directory

### `impact {id}`

1. Look up `## {id}` in `COMPONENTS.md`. If not found, show valid IDs
2. BFS on reverse dependency graph: find direct dependents, then transitive dependents (track visited nodes for cycles)
3. Display direct and transitive dependents with total count

### `untarget`

1. If no `**Component:**` field in Current Work, display "No component is currently targeted."
2. Remove `**Component:**` line, `**Path:**` line, and `### Component Context` sub-section, preserve all other fields

### Component Context Rules

When a component is targeted, Current Work gains `**Component:** {id}` and `**Path:** {path}` (after Name, before Status) and a `### Component Context` sub-section with a metadata table from COMPONENTS.md.

1. Field is omitted entirely when no component is targeted (backward compatible)
2. Only fields with values are included
3. When a different component is targeted, previous context is replaced
4. `untarget` removes both the field and the sub-section
5. All agents read this section from CLAUDE.md to scope work — Developer uses Path/Language/Dependencies, Test agents use Path/Language, reviewers use Path/Dependencies, Task Manager uses all fields

---

## Model Configuration

**Default Model:** `opus` — Override in agent YAML front-matter with `model: sonnet` or `model: haiku`.

| Agent Category | Model | Rationale |
|----------------|-------|-----------|
| Architecture, Security, Design, Code Reviewers, Task Manager | opus | Complex reasoning and trade-offs |
| Developer, Test Coder, Test Runner, Documentation | sonnet | Standard implementation work |
| Exploration, simple validation | haiku | Quick searches, simple transforms |

---

## Activity Log

Traceability of all agent actions. Designed for machine parsing. Full schema and writer protocol in [task-manager.md §Activity Log Management](.claude/agents/task-manager.md).

- **File:** `project-docs/activity.log`
- **Format:** JSONL (one JSON object per line, UTF-8) — schema defined in task-manager.md and unchanged by the orchestration model. Do NOT alter the field set or order.
- **Sole Writer:** the orchestrator role (see [Orchestration Model](#orchestration-model)). In this environment that is the parent Claude Code session, which writes `log_seq`, `work_seq`, `timestamp`, `parent_log_seq`, `duration_ms` to agent entries directly. Sub-agents return `<log-entry>` blocks; the parent merges the orchestrator-managed fields and appends the line.

### Action Types

| Action | Description | When to Log |
|--------|-------------|-------------|
| `START` | Agent began execution | When agent is invoked |
| `COMPLETE` | Agent finished successfully | When agent returns success |
| `ERROR` | Agent encountered an error | When agent fails |
| `DECISION` | Significant decision made | When architectural/design choice is made |
| `FILE_CREATE` | New file created | When a new file is written |
| `FILE_MODIFY` | Existing file modified | When an existing file is changed |
| `BLOCKED` | Agent blocked, waiting on dependency | When agent cannot proceed |
| `UNBLOCKED` | Agent unblocked, resuming work | When blocking condition resolved |
| `REVIEW_PASS` | Code review passed | When reviewer approves |
| `REVIEW_FAIL` | Code review failed | When reviewer finds issues |
| `TEST_PASS` | Test(s) passed | When test execution succeeds |
| `TEST_FAIL` | Test(s) failed | When test execution fails |
| `PHASE_TRANSITION` | `**Current Phase:**` advanced to a new phase | Immediately AFTER updating CLAUDE.md, BEFORE invoking the first agent of the new phase |
| `TASK_STATUS_CHANGE` | A task moved between statuses (`pending` → `in-progress`, etc.) | Immediately when task list is updated |

**`PHASE_TRANSITION` entry shape:**

```json
{"agent": "orchestrator", "action": "PHASE_TRANSITION", "phase": "{new_phase}", "details": "Transitioned from {old_phase} to {new_phase}", "decisions": ["{summary of transition trigger}"]}
```

**`TASK_STATUS_CHANGE` entry shape:**

```json
{"agent": "orchestrator", "action": "TASK_STATUS_CHANGE", "phase": "{current_phase}", "task_id": "T0NN", "details": "{old_status} → {new_status}"}
```

These two actions exist specifically so external watchers (Kanban app, Agent Flow plugin, the `check-orchestration-bookkeeping` Stop hook) can pin orchestrator state to the log without parsing CLAUDE.md or the task list independently.

### Phase Values

`requirements` | `architecture` | `design` | `planning` | `implementation` | `review` | `testing` | `documentation` | `deployment`

---

## Parallel Execution

### Design Phase Waves

| Wave | Agents | Dependencies |
|------|--------|--------------|
| Foundation | UI-UX Design, Data Design, Security Design | None |
| Core | Library Design, Backend Design | Foundation complete |
| Application | Frontend Design, Agent Design, ML Design | Core complete |
| Integration | Integration Design | Application complete |
| Infrastructure | Infrastructure Design | Integration complete |

**Per-Component Invocation:** Wave agents are invoked once per identified component of the matching type. Example: if requirements-analyzer identifies 2 frontends (`admin-ui` and `user-portal`), the Application wave produces 2 frontend-design-agent invocations (for `30-admin-ui.md` and `30-user-portal.md`) plus 2 ui-ux-design-agent invocations for screen designs (for `90-admin-ui.md` and `90-user-portal.md`). Agents (background workers) have no UI — only agent-design-agent fires for them, never ui-ux-design-agent. ML systems (`components.ml_systems[*]`) have no UI either — only ml-design-agent fires for them, producing `70-ml-{name}.md`. See design-orchestrator.md § Mandatory Component Design Rules for the full mapping.

### Implementation Phase

Parallel Developer agents when: different source directories, no shared utility modifications, separate database tables.

### Testing Phase

Parallel test execution when: independent modules, no shared fixtures requiring sequential setup, database isolation per suite.

### Conflict Resolution

Task Manager detects file conflicts. First completion wins; subsequent agents rebase. Design doc conflicts escalated to user.

---

## Exit Criteria

Task Manager validates exit criteria before phase transitions. Blocks if not met. Allows user override with explicit acknowledgment.

| Phase | Criteria |
|-------|----------|
| **Design** | Mandatory per-component docs created for every component identified by requirements-analyzer (frontends get `30-` + `90-`, backends get `20-`, agents get `40-` with no UI docs, libraries get `10-`); requirements-driven docs (`01-`, `02-`, `03-`, `50-`, `60-`) as warranted by content; requirements traceability complete, no unresolved questions, user approval |
| **Implementation** | **All code review findings verified** (every CR-ID status = `verified` in findings tracker — no `open`, `resolved`, or `still_open` findings may remain), no TODO/FIXME in committed code, no stubs, builds without errors, Conventional Commits |
| **Testing** | Coverage minimum 70% (configurable), all tests passing, no critical/high security findings, performance benchmarks met |
| **Documentation** | User docs complete, developer docs complete, API docs generated, README updated |

---

## Git Requirements

All projects must use Git for version control.

### Branch Strategy

| Branch Pattern | Purpose |
|----------------|---------|
| `main` | Stable, protected - production-ready code |
| `feature/<task-id>-<short-desc>` | Per task/component implementation |
| `fix/<issue-id>-<short-desc>` | Bug fixes |

### Commit Format (Conventional Commits)

```
<type>(<scope>): <description>

[optional body]

Refs: REQ-XXX-FN-NNN
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Conflict Resolution

1. Developer resolves conflicts following existing code patterns
2. Design doc conflicts escalated to user
3. Task Manager tracks conflict resolution status

---

## Code Consistency Enforcement

All code must look like it was designed and developed by one person. Components of the same type must follow identical patterns.

1. **Pattern Conformance** — Inspect existing components of the same type; follow their structure exactly
2. **Base Class Reuse** — Never reimplement functionality from base classes or shared utilities
3. **Structural Uniformity** — Same file organization, constructors, lifecycle methods, configuration
4. **Naming Consistency** — Follow conventions established in ADR-001 (see [Naming Conventions](#naming-conventions)) and by the first component of that type

See developer.md for detailed enforcement steps. Code reviewers flag structural mismatches, base class reimplementation, and naming/organization deviations.

---

## Naming Conventions

**The Architect agent's FIRST deliverable is `project-docs/adrs/ADR-001-naming-conventions.md`.** No other architectural work, no design work, no implementation work proceeds until ADR-001 exists. This rule prevents the class of cross-layer naming bugs (DB column `user_id` vs ORM `userId` vs JSON `userID` vs frontend `User_ID`) that cost dozens of iterations to resolve.

### What ADR-001 must declare

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
| Queue routing keys / event names | `snake_case` (`user.created`) or `dot.notation` | `snake_case` with dot separators |
| File names (per language) | follow language convention | per-language |

### Cross-layer serialization contract

ADR-001 must also explicitly state, for every layer boundary, how identifiers map across it:

- Python `user_id` ↔ JSON: snake-through OR camelCase via Pydantic alias — pick one project-wide
- DB column `user_id` ↔ ORM attribute: matched OR aliased — pick one
- TypeScript `userId` ↔ JSON: camel-through OR snake via serializer — pick one
- Env var `DATABASE_URL` ↔ code constant `DATABASE_URL` — always matched

### Enforcement

- **Architect agent**: produces ADR-001 BEFORE any other ADR. No design phase begins until ADR-001 exists.
- **All `conventions/developer/*.md` files**: reference ADR-001 as the source of truth.
- **All four code reviewers**: check against ADR-001 — `code-reviewer-conventions` is the dedicated agent for this (see [Sub-Agent Index](#code-review-agents)). It runs in parallel with the other three reviewers (Step 8 of Unified Agent Workflow).
- **Exit gate**: ADR-001 must be present and referenced by all design docs before Implementation phase begins.

---

## Working Principles

- Blunt, honest feedback over false agreement
- Right matters more than feelings
- Keep markdown lean - enough for intent, no more
- Document decisions and rationale
- **Approval scope:** when the user approves an approach, treat it as approved for the full phase. Don't re-ask the same approval at each sub-step — re-ask only when the situation materially changes or a new tradeoff appears.
- **Workflow gates override auto mode:** The `lets begin` gate (requirements approval) and the code-review-findings-verified gate (before testing) are unconditional. Auto mode advances WITHIN gates, not THROUGH them.

**END CLAUDE.MD**
