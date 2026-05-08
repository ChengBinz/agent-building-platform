# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run

```bash
# 1. Set up environment
cp .env.example .env
# Edit .env — SECRET_KEY is required; configure LLM API keys

# Production (Nginx at :80)
docker compose up -d --build

# Development with hot reload (frontend :5173, backend :8000)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build

# Seed default admin user (admin / admin123)
docker compose exec backend python /app/scripts/seed.py

# Run DB migrations manually
docker compose exec backend alembic upgrade head
docker compose exec backend alembic revision --autogenerate -m "description"

# Frontend type-check + build
cd frontend && npm run build

# View logs
docker compose logs -f backend
```

Backend runs `alembic upgrade head && uvicorn` automatically on container start.

## Architecture

**Stack**: FastAPI (Python) + Vue 3/TypeScript + PostgreSQL (pgvector) + Qdrant + Redis + Nginx

### Backend (layered pattern)

- `backend/app/api/v1/router.py` — central router mounted at `/api/v1`; each domain module registers its own `APIRouter`
- `backend/app/api/deps.py` — `get_current_user` (JWT via `OAuth2PasswordBearer`) and `get_current_superuser` dependency callables; used by every protected endpoint
- `backend/app/core/security.py` — bcrypt password hashing, JWT access/refresh tokens (HS256), token type enforcement (access vs refresh)
- `backend/app/db/session.py` — async SQLAlchemy engine + session factory; `get_db` yields a session that auto-commits on success and rolls back on exception
- `backend/app/models/` — SQLAlchemy ORM models: all tables use UUID PKs via `UUIDMixin` and timestamps via `TimestampMixin`; relationships use `lazy="selectin"`
- `backend/app/schemas/` — Pydantic request/response schemas
- `backend/app/services/` — business logic, one service class per domain (`AuthService`, `ChatService`, `KnowledgeService`, `MonitoringService`, `AdminService`); each receives `AsyncSession` via constructor
- `backend/app/config.py` — `pydantic-settings` reading from `.env`; provides computed `DATABASE_URL` and `DATABASE_URL_SYNC` properties

### LLM Engine (`backend/app/engine/`)

All supported providers use OpenAI-compatible API via `OpenAICompatProvider`. The provider registry (`registry.py`) maps provider keys to base URLs and instantiates the provider:

- `base.py` — abstract `LLMProvider` with `generate_stream()` returning `AsyncGenerator[StreamChunk]`
- `openai_compat.py` — single concrete provider using `AsyncOpenAI` client; handles OpenAI, DeepSeek, DashScope, Ollama
- `openai.py`, `anthropic.py`, `ollama.py` — provider-specific adapters (stubs, not wired in)
- `tool_manager.py` — built-in tool registry (stub)
- `ChatService.send_message_stream()` calls `get_provider(provider, api_key, base_url)` then iterates over `provider.generate_stream()` yielding SSE-formatted tokens

### RAG Pipeline (`backend/app/rag/`)

Skeleton pipeline (all stubs, TODO to implement):
- `loader.py` → `chunker.py` → `embedder.py` → `vector_store.py` (Qdrant) → `retriever.py`
- `pipeline.py` — end-to-end ingest + query orchestration (stub)

### Database models

9 tables: `users`, `roles`, `user_roles` (M2M association), `api_keys`, `conversations`, `messages`, `conversation_memories`, `knowledge_bases`, `documents`, `usage_logs`. Conversations have `kb_ids` (UUID array) for attaching knowledge bases. Messages have `tool_calls` (JSONB) and `extra` (JSONB). UsageLog records per-request token counts and latency.

### Conversation Memory System

Multi-turn memory via LLM summarization with Redis caching:

- **Trigger**: After every 5 rounds (10 messages) of conversation, `MemoryService.check_and_summarize()` generates a summary of the conversation so far
- **Incremental**: If a previous summary exists, it's included in the summarization prompt for incremental updates
- **Cache**: Redis caches the latest summary (`conversation_memory:{id}`, 7-day TTL) for fast retrieval
- **Context injection**: `ChatService._build_messages()` injects the memory summary as a system message and trims the message history to the last 10 messages, preventing context window explosion
- **Persistence**: Summaries are saved to `conversation_memories` table (FK → conversations, CASCADE on delete)
- **Background**: In streaming mode, summarization runs as an `asyncio.create_task` with its own DB session, non-blocking
- **Cleanup**: Deleting a conversation removes all memories (DB cascade + Redis cache)

### API endpoints

| Prefix | Module | Notes |
|---|---|---|
| `/api/v1/auth` | `auth.py` | register, login, refresh, me, api-keys CRUD |
| `/api/v1/` | `chat.py` | conversations CRUD + send/send-stream (SSE) |
| `/api/v1/` | `knowledge.py` | knowledge-bases CRUD |
| `/api/v1/` | `models.py` | static model catalog per provider |
| `/api/v1/` | `monitoring.py` | usage summary + by-model breakdown |
| `/api/v1/` | `admin.py` | user management + system stats (superuser only) |
| `/api/v1/` | `users.py` | (empty/placeholder) |

### SSE Streaming Pattern

**Backend**: `send_message_stream()` in `chat.py` returns `StreamingResponse(service.send_message_stream(...), media_type="text/event-stream")`. The service method yields `data: <token>\n\n` per chunk and `data: [DONE]\n\n` on completion.

**Frontend**: `api/chat.ts` `sendMessageStream()` uses raw `fetch()` (not axios) with `AbortController` for cancellation. A `ReadableStream` reader parses SSE lines. `stores/chat.ts` manages optimistic message append (user message + assistant placeholder), calls `onToken` callback to append to the placeholder, and handles abort/error.

### Frontend

- `src/router/index.ts` — route guard auto-refreshes token on first visit, redirects unauthenticated users to `/login`. Admin users are restricted to `/admin/*` routes; non-admin users are blocked from admin routes. Redirect logic: admin → `/admin/users`, regular → `/chat`.
- `src/api/client.ts` — axios instance with JWT Bearer interceptor; 401 responses clear tokens and redirect to `/login`. SSE streaming uses raw `fetch()` in `api/chat.ts` instead.
- `src/api/chat.ts` — SSE stream via `ReadableStream.getReader()` with `AbortController` for cancellation.
- `src/stores/auth.ts` — Pinia store: login/register/registerAdmin/refreshAccessToken/fetchUser/logout + `isAuthenticated`/`isAdmin` computeds. Admin registration uses `admin_code` from settings.
- `src/stores/chat.ts` — optimistic UI patterns: appends user message + assistant placeholder immediately, streams content into placeholder. Delete has snapshot-based rollback on API failure. Conversation response includes `memory_summary` field; ChatView shows "记忆已启用" tag when memory is active.
- `src/stores/knowledge.ts` — CRUD store with optimistic list updates and ElMessage feedback.
- `src/views/` — lazy-loaded route components: ChatView, KnowledgeView, ModelsView, MonitorView, Login, admin/AdminUsers, admin/AdminSettings
- `src/types/index.ts` — shared TS interfaces mirroring backend response shapes
- Element Plus with Chinese locale; Pinia for state; `marked` + `highlight.js` for Markdown rendering; ECharts for charts
- `src/utils/storage.ts` — token helpers using `localStorage` (access_token, refresh_token)
- Vite dev server proxies `/api` → `localhost:8000` (`vite.config.ts`)

### Infrastructure Services

| Service | Image | Role |
|---|---|---|
| Nginx | `nginx:1.27-alpine` | Reverse proxy `/api/` → `backend:8000`, serves SPA static files |
| PostgreSQL | `pgvector/pg16` | Primary DB with vector extension |
| Qdrant | `qdrant/qdrant:latest` | Vector database (gRPC on 6334) |
| Redis | `redis:7-alpine` | Session cache (client is stub) |
| Frontend | `node:22-alpine` (builder) | Builds SPA, outputs to volume for Nginx |

### Nginx routing

- `/api/` → proxied to `backend:8000` with WebSocket upgrade headers and 300s read timeout (for SSE streaming), `proxy_buffering off`
- `/` → serves static SPA from `/usr/share/nginx/html` with `try_files $uri /index.html`

## Key implementation notes

- **Engine is wired**: `ChatService` calls real LLM APIs via `OpenAICompatProvider`; this is NOT a placeholder
- **Engine/RAG stubs remaining**: `engine/openai.py`, `engine/anthropic.py`, `engine/ollama.py` are skeletons; `engine/types.py` is a stub; `engine/tool_manager.py` is a stub; all of `rag/` is skeleton code
- **RBAC is not implemented**: `core/permissions.py` is a stub; roles table exists but role checks are not enforced beyond `is_superuser`
- **Token storage**: JWT tokens stored in `localStorage` (not httpOnly cookies)
- **Middleware stubs**: `middleware/tracking_mw.py` and `middleware/logging_mw.py` are placeholders
- **Redis**: Async Redis client in `db/redis.py` — used for conversation memory cache
- **Last-admin protection**: `AdminService` prevents deleting or disabling the last active superuser account
- **Database URL**: Alembic uses sync URL (`DATABASE_URL_SYNC`) via `psycopg2`; app uses async URL via `asyncpg`
- **Dependencies**: Python via `requirements.txt` (no `pyproject.toml`); Node deps via `package.json` with `package-lock.json` (not yarn/pnpm)
- **API Key per provider**: Users configure API keys per provider in the Models page; keys are stored in `api_keys` table per user. Chat resolution: `ChatService._get_api_key()` fetches the user's active key for the conversation's provider
- **Model catalog**: Static list in `api/v1/models.py`; provider `configured` status checks env var OR user-stored API key
- **Error messages**: Chinese (zh-CN) throughout — user-facing messages, API error details, UI labels
