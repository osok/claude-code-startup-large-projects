# Claude Code Sub-Agents for Large Projects

A comprehensive framework of specialized sub-agents for Claude Code, designed for the complete software development lifecycle of large-scale applications.

## Overview

This framework provides 26 coordinated AI agents that work together to build your application:

- **Requirements Agent** - Elicits requirements using ISO 29148 standard
- **Architect Agent** - Makes technology and structure decisions
- **Design Orchestrator** - Coordinates 9 specialized design agents
- **Developer Agent** - Writes code following best practices
- **Test Agents** - Plan, write, and run tests
- **Code Review Agents** - Check requirements, security, integration
- **Documentation Agent** - Creates user and developer docs

The **Task Manager** coordinates everything, tracking what's done and what's next.

Use `@upgrade` to keep your framework files in sync with the latest version.

## Prerequisites

This framework requires the **[claude-code-project-memory-mcp](https://github.com/osok/claude-code-project-memory-mcp)** MCP server. The Memory MCP provides persistent, semantic knowledge across sessions - enabling code consistency enforcement, cross-work-item learning, and intelligent decision-making across all 26 agents.

Install and configure it before using this template. See the [claude-code-project-memory-mcp repository](https://github.com/osok/claude-code-project-memory-mcp) for setup instructions.

## Quick Start

### 1. Create Your Project

```bash
gh repo create my-project --template osok/claude-code-startup-large-projects --clone
cd my-project
```

### 2. Initialize

```
initialize
```

### 3. Begin Work

```
lets begin
```

This will:
- Check for existing requirements in `requirement-docs/`
- If none exist, help you create them
- If they exist, ask for your approval
- Once approved, run the full agent workflow

Use `continue` to resume work in new sessions.

## Included Agents (26 total)

### Core Workflow Agents

| Agent | What It Does |
|-------|--------------|
| **Requirements** | Interviews you to understand what to build |
| **Architect** | Makes technology choices, defines structure |
| **Requirements Analyzer** | Parses ISO 29148 requirements structure |
| **Design Orchestrator** | Coordinates specialized design agents |
| **Task Manager** | Coordinates agents, tracks progress |

### Specialized Design Agents

| Agent | Output Prefix | What It Does |
|-------|---------------|--------------|
| **UI/UX Design** | 01-, 90- | UI/UX patterns and style guides |
| **Data Design** | 02- | Data architecture and models |
| **Security Design** | 03- | Security architecture and threat models |
| **Library Design** | 10- | Shared component libraries |
| **Backend Design** | 20- | Backend services and APIs |
| **Frontend Design** | 30- | Frontend applications |
| **Agent Design** | 40- | Background workers and jobs |
| **Integration Design** | 50- | API contracts between systems |
| **Infrastructure Design** | 60- | Cloud, Docker, deployment |

### Implementation Agents

| Agent | What It Does |
|-------|--------------|
| **Data Agent** | Defines schemas and data structures |
| **Deployment** | Docker, env configs, infrastructure |
| **Developer** | Writes application code |
| **Documentation** | Writes user and developer docs |

### Testing Agents

| Agent | What It Does |
|-------|--------------|
| **Test Designer** | Plans what tests are needed |
| **Test Coder** | Writes test code |
| **Test Runner** | Runs tests, reports results |
| **Test Debugger** | Deep debugging across all layers |

### Code Review Agents

| Agent | What It Does |
|-------|--------------|
| **Code Reviewer - Requirements** | Verifies completeness against requirements |
| **Code Reviewer - Security** | Checks OWASP vulnerabilities |
| **Code Reviewer - Integration** | Finds stubs, wiring gaps |

### Utility Agents

| Agent | What It Does |
|-------|--------------|
| **Upgrade** | Syncs framework files from source (user-invocable only) |

## Language Support

Pre-built conventions for 27 technologies:

**Backend**: Go, Java, Python, TypeScript, Rust, C#/.NET, Ruby, PHP, Kotlin, Scala, Elixir

**Frontend**: React, Vue, Angular, Svelte, Next.js, Nuxt

**Mobile**: Swift, Kotlin Android, Flutter/Dart, React Native

**Infrastructure**: Terraform, Kubernetes, Bash/Shell, SQL

**Emerging**: Zig, Solidity

## Component Registry

For large multi-component projects, the **Component Registry** lets you catalog, identify, and target individual components (frontends, backends, libraries, agents) so work can be directed at a specific component.

### Setup

Create a `COMPONENTS.md` file at your project root (see `COMPONENTS.EXAMPLE.md` for the format). Each component declares an ID, name, type, path, and description. Optional fields include language, dependencies, deployment target, and port.

### Component Commands

| Command | What It Does |
|---------|-------------|
| `list components` | Show all components (supports type filtering) |
| `target {id}` | Set active component for subsequent work |
| `show component {id}` | Display full details of a component |
| `add component` | Interactively add a component to the manifest |
| `impact {id}` | Show components affected by changes |
| `untarget` | Clear component targeting |

### How It Works

1. Create `COMPONENTS.md` with your project's components
2. Use `target {id}` to set the active component
3. Run `new work` -- the framework scopes requirements, design, and implementation to that component
4. Agents receive component context (path, language, type, dependencies) automatically
5. All features are opt-in: projects without `COMPONENTS.md` work exactly as before

## Project Structure

```
your-project/
├── .claude/agents/       # Agent definitions
├── CLAUDE.md             # Project memory and status
├── COMPONENTS.md         # Component registry manifest (optional, user-created)
├── COMPONENTS.EXAMPLE.md # Sample manifest for reference
├── conventions/          # Coding standards by language
├── requirement-docs/     # ISO 29148 requirements
├── design-docs/          # Generated design documents
├── design-templates/     # Design document templates
├── project-docs/         # Task lists, ADRs, schemas
├── developer-docs/       # Docs for contributors
└── user-docs/            # Docs for end users
```

## Commands

| Command | When to Use |
|---------|-------------|
| `initialize` | Reset project to blank state |
| `new work` | Start a new work item - creates requirements doc, interviews you |
| `lets begin` | Check requirements exist, get approval, start workflow |
| `continue` | Resume work via Task Manager |
| `list components` | Show all components from COMPONENTS.md |
| `target {id}` | Set active component for subsequent work |
| `show component {id}` | Display full details of a component |
| `add component` | Interactively add a component to COMPONENTS.md |
| `impact {id}` | Show components affected by changes to target |
| `untarget` | Clear the active component targeting |
| `@upgrade` | Sync framework files with latest version |

### `new work` Command

The primary way to start new development:

1. **Creates new sequence** (002, 003, etc.)
2. **Prompts for description** → generates short name
3. **Creates requirements doc**: `requirement-docs/{seq}-requirements-{short_name}.md`
4. **Asks how to provide requirements**:
   - Upload/paste your own requirements
   - Interview mode - agent asks structured questions
5. **Uses ISO/IEC/IEEE 29148:2018** format for requirements

### `continue` Command

Resume work from where you left off:

1. **Invokes Task Manager** - The primary coordinator for all work
2. **Reads current state** - Task list, activity log, CLAUDE.md
3. **Resets stale tasks** - Any `in-progress` tasks reset to `pending`
4. **Finds next task** - First actionable task with dependencies met
5. **Routes to agent** - Invokes appropriate agent for the task
6. **Tracks progress** - Updates task list and activity log

**Important:** Always use `continue` to resume work. Don't invoke agents directly - let Task Manager coordinate.

### `@upgrade` Command

Keep your framework files in sync with the latest version:

1. **Invoke**: Type `@upgrade` in the console
2. **Choose source**:
   - Default GitHub repo: `osok/claude-code-startup-large-projects`
   - Different GitHub repo
   - Local directory (useful if you have unreleased changes)
3. **Review changes**: Agent shows what will be updated/added
4. **Confirm**: Approve the upgrade

**What gets upgraded**:
- `.claude/agents/*.md` - All agent definitions
- `CLAUDE.md` - Framework sections (preserves your project-specific content)
- `conventions/` - Coding standards
- `design-templates/` - Design document templates

**What's preserved**:
- Your `Current Work` section in CLAUDE.md
- Your `Document Sequence Tracker` entries
- Any custom agents you've created
- All your project files (requirements, designs, code)

## Memory MCP Integration

All 26 agents are integrated with the [claude-code-project-memory-mcp](https://github.com/osok/claude-code-project-memory-mcp) server, which provides:

- **Persistent knowledge** - Decisions, patterns, and context survive across sessions
- **Semantic search** - Find relevant prior work using natural language queries
- **Code consistency enforcement** - Ensures all components of the same type follow the same patterns, naming, and structure
- **Base class reuse detection** - Prevents reimplementation of functionality that exists in parent classes or shared utilities
- **Cross-work-item learning** - Design decisions from earlier work items inform later ones
- **Requirement traceability** - Trace requirements through design, implementation, and testing

Each agent uses memory at specific points in its workflow (documented in `## Memory Integration` sections within each agent definition). Key operations include `memory_search`, `code_search`, `check_consistency`, `index_file`, and `get_design_context`.

## How It Works

1. **Document-based coordination** - Agents communicate via markdown files
2. **Task Manager as orchestrator** - One agent controls workflow
3. **Schemas as source of truth** - Data Agent maintains authoritative schemas
4. **Smart failure routing** - Test failures route to appropriate agents
5. **Activity logging** - All agent actions logged to `project-docs/activity.log` (JSONL format)
6. **Memory-backed consistency** - All agents use the Memory MCP for persistent knowledge and code pattern enforcement

## Document Strategy

**Work-specific documents** (created per work item):
- `requirement-docs/{seq}-requirements-{short_name}.md` - Requirements
- `design-docs/{seq}-design-{short_name}.md` - Design overview

**Foundational documents** (updated, not duplicated):
- `design-docs/01-style-guide.md` - Single style guide
- `design-docs/02-data-architecture.md` - Single data architecture
- `design-docs/03-security-architecture.md` - Single security doc
- Other design docs (10-, 20-, 30-, etc.) - Updated to incorporate new work

When adding new features, design agents **update existing docs** with sections labeled `## Seq {NNN}: {Short Name}` rather than creating duplicates.

## Workflow

```mermaid
flowchart TB
    subgraph Requirements["📋 Requirements Phase"]
        REQ[Requirements Agent]
    end

    subgraph Architecture["🏗️ Architecture Phase"]
        ARCH[Architect Agent]
    end

    subgraph Design["📐 Design Phase"]
        RA[Requirements Analyzer]
        DO[Design Orchestrator]

        subgraph Foundation["Foundation Layer"]
            direction LR
            UIUX[UI/UX Design]
            DATA_D[Data Design]
            SEC_D[Security Design]
        end

        subgraph Core["Core Layer"]
            direction LR
            LIB[Library Design]
            BACK[Backend Design]
        end

        subgraph Application["Application Layer"]
            direction LR
            FRONT[Frontend Design]
            AGENT_D[Agent Design]
        end

        INT_D[Integration Design]
        INFRA[Infrastructure Design]
    end

    subgraph Planning["📝 Planning Phase"]
        direction LR
        TD[Test Designer]
        DA[Data Agent]
        TM[Task Manager]
    end

    subgraph Implementation["💻 Implementation Phase"]
        DEV[Developer]
    end

    subgraph Review["🔍 Review Phase"]
        direction LR
        CR_REQ[Code Reviewer<br/>Requirements]
        CR_SEC[Code Reviewer<br/>Security]
        CR_INT[Code Reviewer<br/>Integration]
    end

    subgraph TestPrep["🧪 Test Prep Phase"]
        direction LR
        TD2[Test Designer]
        DOC[Documentation]
        DEPLOY[Deployment]
    end

    subgraph Testing["✅ Testing Phase"]
        TC[Test Coder]
        TR[Test Runner]
        TDB[Test Debugger]
    end

    subgraph Finalize["📚 Finalize Phase"]
        DOC2[Documentation]
    end

    %% Main Flow
    REQ --> ARCH
    ARCH --> RA
    RA --> DO
    DO --> Foundation
    Foundation --> Core
    Core --> Application
    Application --> INT_D
    INT_D --> INFRA
    INFRA --> Planning
    TD & DA --> TM
    TM --> DEV
    DEV --> Review
    CR_REQ & CR_SEC & CR_INT --> FIX{Gaps Found?}
    FIX -->|Yes| TM
    TM -.->|Design Gap| DO
    TM -.->|Data Gap| DA
    TM -.->|Code Gap| DEV
    FIX -->|No| TestPrep
    TD2 & DOC & DEPLOY --> TC
    TC --> TR
    TR --> PASS{Tests Pass?}
    PASS -->|No| TDB
    TDB --> TM
    TM -.->|Route Fix| DEV
    TM -.->|Route Fix| TC
    TM -.->|Route Fix| DO
    PASS -->|Yes| DOC2
    DOC2 --> DONE((Complete))

    %% Styling
    classDef phase fill:#e1f5fe,stroke:#01579b
    classDef agent fill:#fff3e0,stroke:#e65100
    classDef decision fill:#fce4ec,stroke:#880e4f
    classDef done fill:#e8f5e9,stroke:#1b5e20

    class REQ,ARCH,RA,DO,UIUX,DATA_D,SEC_D,LIB,BACK,FRONT,AGENT_D,INT_D,INFRA,TD,DA,TM,DEV,CR_REQ,CR_SEC,CR_INT,TD2,DOC,DEPLOY,TC,TR,TDB,DOC2 agent
    class FIX,PASS decision
    class DONE done
```

### Workflow Phases

| Phase | Agents | Output |
|-------|--------|--------|
| **Requirements** | Requirements | `requirement-docs/` |
| **Architecture** | Architect | `project-docs/adrs/` |
| **Design** | Requirements Analyzer → Design Orchestrator → 9 Specialized Agents | `design-docs/` |
| **Planning** | Test Designer, Data Agent, Task Manager | Test plan, schemas, task list |
| **Implementation** | Developer | Application code |
| **Review** | 3 Code Reviewers (parallel) | Review reports |
| **Test Prep** | Test Designer, Documentation, Deployment | Updated plans, docs, env |
| **Testing** | Test Coder → Test Runner → Test Debugger | Tests, results, fixes |
| **Finalize** | Documentation | Final docs |

## Tips

- Be specific in requirements - more detail = better output
- Answer agent questions thoughtfully
- Review designs before implementation
- Use `continue` to resume sessions

## License

MIT
