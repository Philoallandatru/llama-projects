# Codebase Structure

**Analysis Date:** 2026/05/03

## Directory Layout

```
llama-projects/
├── .claude/              # Project planning and memory
├── .planning/            # Planning documents (newly created)
├── .venv/                # Python virtual environment
├── chat/                 # RAG chat application
├── data-explore/         # Financial report generator
├── datasource/          # Data source management system
├── deep-serach/          # Deep research workflow
├── jira-analysis/        # Jira issue analysis system
├── docs/                 # Design documents
├── pyproject.toml        # Workspace root config
└── README.md            # Monorepo overview
```

## Directory Purposes

**chat/:**
- Purpose: RAG chat application with citation support
- Contains: `src/` (workflow, query, index, settings), `ui/` (TypeScript frontend), `tests/`
- Key files: `src/workflow.py`, `src/query.py`, `src/citation.py`

**data-explore/:**
- Purpose: Multi-agent financial report generator
- Contains: `src/` (workflow, agent_tool, interpreter, document_generator), `ui/`
- Key files: `src/workflow.py`, `src/interpreter.py`, `src/document_generator.py`

**datasource/:**
- Purpose: Unified data source management (Phase 6 complete)
- Contains: `datasource/core/` (manager, sources, indexing, metadata), `tests/`, `benchmarks/`
- Key files: `datasource/core/manager.py`, `datasource/core/sources/*.py`

**deep-serach/:**
- Purpose: Multi-perspective deep research workflow
- Contains: `src/` (workflow, index, settings, utils), `ui/`
- Key files: `src/workflow.py`, `src/utils.py`

**jira-analysis/:**
- Purpose: Jira issue deep analysis system (Phase 1 in progress)
- Contains: `src/core/` (issue_loader, retriever, router, llm_client), `src/profiles/`, `src/workflows/`, `ui/`
- Key files: `src/workflows/deep_analysis.py`, `src/core/retriever.py`, `src/core/router.py`

## Key File Locations

**Entry Points:**
- `datasource/datasource/cli.py`: CLI commands (sync, index, query)
- `chat/src/generate.py`: Chat index generation
- `chat/src/api.py`: Chat API endpoints

**Configuration:**
- `pyproject.toml`: Root workspace config with all dependencies
- `chat/pyproject.toml`: Chat-specific dependencies (not found - uses root)
- `jira-analysis/pyproject.toml`: Jira analysis dependencies

**Core Logic:**
- `datasource/datasource/core/manager.py`: DataSourceManager orchestration
- `datasource/datasource/core/sources/base.py`: BaseDataSource abstract class
- `chat/src/workflow.py`: Chat AgentWorkflow
- `jira-analysis/src/workflows/deep_analysis.py`: DeepAnalysisWorkflow

**Testing:**
- `datasource/tests/`: Unit and integration tests for datasource
- `chat/tests/`: Chat integration tests
- `jira-analysis/tests/`: Jira analysis E2E tests

## Naming Conventions

**Files:**
- Python: `lowercase_with_underscores.py`
- TypeScript: `PascalCase.tsx` for components, `camelCase.ts` for utilities
- Config: `llama_deploy.yml`, `pyproject.toml`

**Directories:**
- Python packages: `lowercase_with_underscores/`
- TypeScript: `kebab-case/` or `camelCase/`

**Classes:**
- PascalCase: `SourceManager`, `DeepAnalysisWorkflow`, `BaseDataSource`
- Events: `PascalCaseEvent`: `LoadIssueEvent`, `RouteEvent`, `RetrieveEvent`

## Where to Add New Code

**New DataSource Type:**
- Primary code: `datasource/datasource/core/sources/new_source.py`
- Inherit from `BaseDataSource`
- Register in `SourceManager._create_source()`

**New Workflow Step:**
- Implementation: Add `@step` method in appropriate workflow class
- Events: Define in same file as workflow

**New Analysis Profile (Jira):**
- Prompts: `jira-analysis/src/profiles/prompts/`
- Config: `jira-analysis/src/profiles/config.json`

**New UI Component:**
- Implementation: `chat/ui/components/` or respective `ui/`
- Follow existing patterns for progress events

## Special Directories

**.claude/plans/:**
- Purpose: Project planning and design documents
- Generated: No
- Committed: Yes

**.planning/codebase/:**
- Purpose: Codebase analysis documents (STACK, ARCHITECTURE, etc.)
- Generated: Yes (this analysis)
- Committed: Yes

**node_modules/ (in chat/, jira-analysis/):**
- Purpose: TypeScript dependencies
- Generated: Yes (npm install)
- Committed: No (.gitignore)

**.venv/, worktrees/*/.venv/:**
- Purpose: Python virtual environments
- Generated: Yes (uv sync)
- Committed: No (.gitignore)

---

*Structure analysis: 2026/05/03*