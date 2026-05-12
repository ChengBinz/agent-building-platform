# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run

```bash
# 1. Set up environment
cp .env.example .env
# Edit .env — SECRET_KEY is required (min 32 chars); configure LLM API keys

# Production (Nginx at :80)
docker compose up -d --build

# Development with hot reload (frontend :5173, backend :8000)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build

# Seed default admin user (admin / admin123) + roles
docker compose exec backend python /app/scripts/seed.py

# Run DB migrations manually (production only; dev uses SQLAlchemy create_all)
docker compose exec backend alembic upgrade head
docker compose exec backend alembic revision --autogenerate -m "description"

# Frontend type-check + build
cd frontend && npm run build

# View logs
docker compose logs -f backend
```

Backend uses SQLAlchemy `create_all` for automatic table creation on startup (dev convenience). Alembic is configured but reserved for production migrations.

**No tests exist** — neither backend (`backend/tests/` is empty) nor frontend (no test runner configured).

## Architecture

**Stack**: FastAPI (Python) + Vue 3/TypeScript + PostgreSQL (pgvector) + Qdrant + Redis + Nginx

### Backend (layered pattern)

- `backend/app/api/v1/router.py` — central router mounted at `/api/v1`; each domain module registers its own `APIRouter`
- `backend/app/api/deps.py` — `get_current_user` (JWT via `OAuth2PasswordBearer`) and `get_current_superuser` dependency callables
- `backend/app/core/security.py` — bcrypt password hashing, JWT access/refresh tokens (HS256)
- `backend/app/db/session.py` — async SQLAlchemy engine + session factory; `get_db` yields a session that auto-commits on success and rolls back on exception
- `backend/app/models/` — SQLAlchemy ORM models: all tables use UUID PKs via `UUIDMixin` and timestamps via `TimestampMixin`; relationships use `lazy="selectin"`
- `backend/app/schemas/` — Pydantic request/response schemas
- `backend/app/services/` — business logic, one service class per domain; each receives `AsyncSession` via constructor. `tool_service.py` is a stateless module (no class) providing unified tool resolution and execution across built-in and MCP tools
- `backend/app/config.py` — `pydantic-settings` reading from `.env`

### Agents System

Users interact with "agents" rather than raw LLM models. Each agent has: `name`, `system_prompt`, `model_name`, `provider`, `tools[]`, `kb_ids[]`. Conversations are tied to agents via `agent_id` FK. When creating a conversation under an agent, `kb_ids` and model config are inherited from the agent. `ChatService._retrieve_rag_context()` uses `conv.kb_ids` to search knowledge bases and inject relevant context.

### Tool Calling System

LLM-driven function calling via a decoupled architecture:

```
chat_service → tool_service → 内置工具 (web_search)
                            → MCP 工具 → mcp_client → MCP Server (HTTP JSON-RPC)
```

- **Tool selection**: Users select tools when creating/editing an Agent (`AgentDialog.vue`)
- **LLM decides**: Tool schemas are passed to the LLM as `tools` parameter; the LLM decides when to call them
- **Execution loop**: `send_message_stream()` runs up to 5 tool-calling rounds (LLM → tool_calls → execute → re-invoke LLM)
- **SSE events**: Tool calls/results are sent to frontend as `[TOOL_CALL]{json}` and `[TOOL_RESULT]{json}` SSE events

Key files:
- `backend/app/services/tool_service.py` — unified interface: `get_tool_schemas()`, `execute_tool()`, `get_all_tools_info()`
- `backend/app/services/mcp_client.py` — MCP HTTP client: `call_mcp_tool()`, `discover_tools()`
- `backend/app/tools/registry.py` — built-in tool registry (web_search only)
- `backend/app/engine/openai_compat.py` — streaming `delta.tool_calls` parsing and assembly

### MCP Servers

Standalone processes implementing the MCP protocol (JSON-RPC 2.0 over HTTP). Located in `mcp-servers/`:

- `mcp-servers/weather/server.py` — weather lookup via wttr.in (port 9100)
- `mcp-servers/timezone/server.py` — timezone lookup via Python stdlib (port 9101)

MCP servers expose:
- `POST /` — JSON-RPC endpoint (methods: `initialize`, `tools/list`, `tools/call`)
- `GET /sse` — SSE transport endpoint

User workflow: register MCP server URL in the MCP page → sync tools → select tools on Agent → LLM auto-invokes them.

**Note**: From Docker containers, MCP servers on the host must be accessed via `host.docker.internal` (not `localhost`).

### LLM Engine (`backend/app/engine/`)

All providers route through a single `OpenAICompatProvider` wrapping `AsyncOpenAI`:

- `base.py` — abstract `LLMProvider` with `generate_stream()` returning `AsyncGenerator[StreamChunk]`
- `openai_compat.py` — single concrete provider using `AsyncOpenAI` client; supports `tools` kwarg via `**kwargs`; streaming loop parses `delta.tool_calls` and yields assembled tool call dicts at end of stream
- `registry.py` — maps provider keys to base URLs and instantiates the provider
- `openai.py`, `anthropic.py`, `ollama.py` — dead code; not wired into the registry
- `tool_manager.py` — stub (TODO)

`StreamChunk` types: `{"token": str}` for text, `{"tool_calls": [list]}` for assembled tool calls at stream end.

### RAG Pipeline (`backend/app/rag/`)

Fully implemented end-to-end pipeline:

- `loader.py` — reads .txt/.md files with UTF-8 encoding
- `chunker.py` — recursive character text splitter with overlap (`CHUNK_SIZE=512`, `CHUNK_OVERLAP=50`)
- `embedder.py` — `AsyncOpenAI` wrapper for embedding API calls (batch size 10)
- `vector_store.py` — Qdrant abstraction: one collection per KB (`kb_{uuid}`), cosine distance, dynamic dimension detection
- `retriever.py` — searches multiple KB collections, merges and sorts by score
- `pipeline.py` — background document ingestion task: load → chunk → embed → Qdrant upsert. Uses `asyncio.create_task` with stored references to prevent GC. Fallback chain for API key: per-KB → global ApiKey table → error

Embedding config is user-provided via the Models page (provider="embedding") or per-KB override. No hardcoded API keys in config.

### Database models

16 tables: `users`, `roles`, `user_roles` (M2M), `api_keys`, `conversations`, `messages`, `conversation_memories`, `knowledge_bases`, `documents`, `usage_logs`, `llm_models`, `default_models`, `agents`, `mcp_servers`, `mcp_tools`, `skills`.

Key relationships:
- Conversations have `agent_id` FK and `kb_ids` (UUID array) for RAG
- Knowledge bases have per-KB `embedding_api_key`, `embedding_base_url`, `embedding_model`
- Documents belong to knowledge bases with status tracking (pending → processing → completed/failed)
- Documents store `qdrant_point_ids` (UUID array) for vector cleanup
- MCP servers have user_id FK; MCP tools have server_id FK and user_id FK
- Skills have user_id FK (nullable for system skills), `is_system` flag distinguishes built-in vs user-created

### Conversation Memory System

Multi-turn memory via LLM summarization with Redis caching:

- **Trigger**: After every 5 rounds (10 messages), `MemoryService.check_and_summarize()` generates a summary
- **Incremental**: Previous summary included in summarization prompt for incremental updates
- **Cache**: Redis (`conversation_memory:{id}`, 7-day TTL)
- **Context injection**: `ChatService._build_messages()` injects memory summary as system message, trims history to last 10 messages
- **Background**: Streaming mode uses `asyncio.create_task` with its own DB session

### API endpoints

| Prefix | Module | Notes |
|---|---|---|
| `/api/v1/auth` | `auth.py` | register, login, refresh, me, api-keys CRUD |
| `/api/v1/` | `chat.py` | conversations CRUD + send/send-stream (SSE) |
| `/api/v1/` | `agents.py` | agent CRUD (name, system_prompt, model, provider, tools, kb_ids) |
| `/api/v1/` | `knowledge.py` | knowledge-bases CRUD + document upload/list/delete |
| `/api/v1/` | `models.py` | static model catalog per provider |
| `/api/v1/` | `monitoring.py` | usage summary + by-model breakdown |
| `/api/v1/` | `users.py` | user profile management |
| `/api/v1/` | `admin.py` | user management + system stats (superuser only) |
| `/api/v1/mcp/` | `mcp.py` | MCP servers CRUD + connection test + tool sync; MCP tools list + toggle |
| `/api/v1/tools` | `tools.py` | list all available tools (built-in + MCP) for current user |
| `/api/v1/skills` | `skill.py` | system skills list; user skills CRUD + toggle |
| `/health` | `main.py` | health check |

### SSE Streaming Pattern

**Backend**: `send_message_stream()` returns `StreamingResponse` with `media_type="text/event-stream"`. Event types:
- `data: <token>\n\n` — text token
- `data: [TOOL_CALL]{"name":"...","args":{...}}\n\n` — tool invocation notification
- `data: [TOOL_RESULT]{"name":"...","result":"..."}\n\n` — tool execution result
- `data: [DONE]\n\n` — stream complete

**Frontend**: `api/chat.ts` uses raw `fetch()` with `AbortController` for cancellation. `ReadableStream` reader parses SSE lines, dispatches `[TOOL_CALL]`/`[TOOL_RESULT]` to dedicated callbacks. `stores/chat.ts` manages optimistic message append and tool call rendering.

### Frontend Component Structure

Views are thin orchestrators; logic and UI are in components:

```
views/
  ChatView.vue          → components/chat/ChatSidebar, ChatMain, AgentDialog
  KnowledgeView.vue     → components/knowledge/KbConfigDialog, KbDetailDrawer
  ModelsView.vue        — model catalog cards with API key config
  McpView.vue           → components/mcp/McpServerTab, McpToolTab (2 tabs)
  SkillView.vue         → components/skill/SystemSkillTab, UserSkillTab (2 tabs)
  Login.vue             — tabbed user/admin login+register
  MonitorView.vue       — usage statistics
  admin/AdminUsers.vue  — user management (superuser)
  admin/AdminSettings.vue — system info display
```

- `src/router/index.ts` — route guard with hard admin/user separation: admin → `/admin/users`, regular → `/chat`
- `src/api/client.ts` — axios instance with JWT Bearer interceptor; 401 → redirect `/login`
- `src/stores/` — Pinia stores: auth, chat (optimistic UI + SSE streaming), agent (CRUD + conversations), knowledge (CRUD + document polling)
- `src/types/index.ts` — shared TS interfaces including `ProviderWithKey`
- Element Plus with Chinese locale (zh-cn); `marked` for Markdown rendering
- Vite dev server proxies `/api` → `localhost:8000`

### Default Models

- **Default LLM**: `deepseek-v4-flash` (provider: deepseek)
- **Default Embedding**: `text-embedding-v4` (provider: dashscope, base URL: `https://dashscope.aliyuncs.com/compatible-mode/v1`)
- Embedding API key must be configured by user via Models page — not hardcoded in config

### Infrastructure Services

| Service | Image | Role |
|---|---|---|
| Nginx | `nginx:1.27-alpine` | Reverse proxy `/api/` → `backend:8000`, serves SPA |
| PostgreSQL | `pgvector/pgvector:pg16` | Primary DB with vector extension |
| Qdrant | `qdrant/qdrant:latest` | Vector database |
| Redis | `redis:7-alpine` | Conversation memory cache |
| Frontend | `node:22-alpine` (builder) | Builds SPA for Nginx |

### Nginx routing

- `/api/` → proxied to `backend:8000` with 300s read timeout (SSE), `proxy_buffering off`
- `/` → static SPA with `try_files $uri /index.html`
- `client_max_body_size 50M`

## Key implementation notes

- **Engine is wired**: `ChatService` calls real LLM APIs via `OpenAICompatProvider`; NOT a placeholder
- **Tool calling is real**: LLM receives tool schemas, returns tool_calls, chat_service executes tools and loops back — up to 5 rounds
- **RAG is fully implemented**: Document ingestion runs as background `asyncio.create_task` with stored references to prevent GC; uses `expire_on_commit=False` session; commits before task creation to avoid race conditions
- **Embedding config fallback**: per-KB key → global ApiKey table (provider="embedding") → error. No config.py fallback
- **Dead code**: `engine/openai.py`, `engine/anthropic.py`, `engine/ollama.py` are unused; `engine/tool_manager.py` is a stub; `core/permissions.py` is a stub
- **RBAC not implemented**: roles table exists but only `is_superuser` is enforced
- **Token storage**: JWT in `localStorage` (not httpOnly cookies)
- **Token counting**: approximate `len(full_response) // 2`
- **API Key per provider**: Users configure keys in Models page; stored in `api_keys` table per user
- **Model catalog**: Static list in `api/v1/models.py`; provider `configured` = env var OR user-stored key
- **Error messages**: Chinese (zh-CN) throughout
- **Last-admin protection**: `AdminService` prevents deleting/disabling the last superuser
- **Database URL**: Alembic uses sync URL (`DATABASE_URL_SYNC` via psycopg2); app uses async URL via asyncpg
- **Dependencies**: Python via `requirements.txt`; Node via `package.json` + `package-lock.json`
- **Admin registration gate**: Requires `ADMIN_REGISTRATION_CODE` env var
- **Database migrations**: Dev uses SQLAlchemy `create_all` (auto-create new tables on startup). Alembic is configured for production use only. See `backend/alembic/README.md` for migration guidance
- **MCP servers**: Standalone FastAPI processes in `mcp-servers/`; no MCP SDK dependency — uses plain HTTP JSON-RPC. From Docker containers, access host MCP servers via `host.docker.internal`
