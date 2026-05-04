# Architecture

**Analysis Date:** 2026/05/03

## Pattern Overview

**Overall:** Event-Driven Workflow Architecture with Tool Integration

**Key Characteristics:**
- LlamaIndex Workflows with `@step` decorator for event-driven step transitions
- Centralized DataSource system providing sync/index/query operations
- TypeScript UI components for frontend
- Shared tooling across applications (datasource, indexing, retrieval)

## Layers

**Application Layer (chat/, data-explore/, deep-serach/, jira-analysis/):**
- Purpose: Application-specific workflows and business logic
- Location: `chat/src/`, `data-explore/src/`, `deep-serach/src/`, `jira-analysis/src/`
- Contains: Workflow implementations, query engines, document generators
- Depends on: datasource, llama-index-core, llama-deploy
- Used by: LlamaDeploy apiserver

**Infrastructure Layer (datasource/):**
- Purpose: Unified data source management and indexing
- Location: `datasource/datasource/`
- Contains: DataSourceManager, SourceManager, indexing strategies, data source implementations
- Depends on: llama-index-core, external APIs (Jira, Confluence)
- Used by: All application projects

**UI Layer:**
- Purpose: Frontend React/TypeScript components
- Location: `chat/ui/`, `data-explore/ui/`, `deep-serach/ui/`, `jira-analysis/ui/`
- Contains: Next.js pages, layout components, progress indicators

**Deployment Layer:**
- Purpose: LlamaDeploy configuration
- Location: `chat/llama_deploy.yml`, etc.
- Contains: Service deployment definitions

## Data Flow

**DataSource Sync Flow:**
1. `SourceManager.sync_source()` triggers sync
2. `_create_source()` instantiates appropriate DataSource (Local/Jira/Confluence)
3. Source `fetch_raw()` fetches data and yields (item_id, raw_data)
4. Source `build_document()` converts raw data to LlamaIndex Document
5. `_build_indexes()` creates vector and BM25 indexes
6. Manifest saved to track sync state

**Query Flow:**
1. Application calls `retriever.retrieve(query)`
2. `HybridRetriever` combines vector and BM25 retrieval
3. Results filtered by metadata
4. Returned as list of document snippets with scores

**Jira Analysis Flow:**
1. `DeepAnalysisWorkflow.start()` receives issue_key
2. `load_issue()` fetches issue via IssueLoader (realtime API)
3. `route_profile()` selects analysis profile based on issue type
4. `retrieve_evidence()` searches vector indexes for related documents
5. `generate_analysis()` calls LLM with evidence
6. `format_output()` structures final result

**State Management:**
- Workflow `Context`: In-memory state via `ctx.data` dictionary
- Chat Memory: `ChatMemoryBuffer` or `SimpleComposableMemory`
- Sync Manifest: JSON file tracking last_sync, status, counts

## Key Abstractions

**BaseDataSource (abstract class):**
- Purpose: Interface for all data source implementations
- Examples: `datasource/datasource/core/sources/local.py`, `jira.py`, `confluence.py`
- Pattern: Template Method - `fetch_raw()` and `build_document()` define the sync contract

**DataSourceManager:**
- Purpose: Orchestrates sync, index building, and querying
- Examples: `datasource/datasource/core/manager.py`
- Pattern: Facade - hides complexity of multi-step operations

**EvidenceRetriever:**
- Purpose: Cross-source evidence retrieval
- Examples: `jira-analysis/src/core/retriever.py`
- Pattern: Strategy - loads and queries multiple vector indexes

**Workflow (LlamaIndex):**
- Purpose: Event-driven step execution
- Examples: `chat/src/workflow.py`, `jira-analysis/src/workflows/deep_analysis.py`
- Pattern: State Machine - @step methods transition between events

## Entry Points

**CLI Entry:**
- Location: `datasource/datasource/cli.py`
- Triggers: `uv run datasource sync jira --project PROJ`
- Responsibilities: Command parsing, SourceManager delegation

**Generate Entry:**
- Location: `chat/src/generate.py`, `data-explore/src/generate.py`, etc.
- Triggers: `uv run generate`
- Responsibilities: Index generation from data sources

**API Server Entry:**
- Location: `llama_deploy/apiserver`
- Triggers: `uv run -m llama_deploy.apiserver`
- Responsibilities: HTTP server for workflow execution

**Workflow Entry:**
- Location: `chat/src/workflow.py`, etc.
- Triggers: LlamaDeploy deployment
- Responsibilities: Agent execution, tool orchestration

## Error Handling

**Strategy:** Layered error handling with logging and result aggregation

**Patterns:**
- Sync errors collected in `SyncResult.errors` list, not thrown immediately
- LLM errors caught and return error message in stream
- Import errors logged with fallback behavior (`get_source_manager()` returns None on failure)

## Cross-Cutting Concerns

**Logging:** Standard Python `logging.getLogger(__name__)`

**Validation:** Pydantic models for configuration (`SourceConfig`, `SourceInfo`)

**Authentication:** Environment variables for API keys (Jira token, Confluence token, OpenAI key)

---

*Architecture analysis: 2026/05/03*