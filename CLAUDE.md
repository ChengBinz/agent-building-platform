# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run

```bash
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
- `backend/app/engine/` — LLM provider abstraction (stubs, not wired in)
- `backend/app/rag/` — RAG pipeline: loader/chunker/embedder/retriever/vector_store (stubs)
- `backend/app/config.py` — `pydantic-settings` reading from `.env`; provides computed `DATABASE_URL` and `DATABASE_URL_SYNC` properties

### Database models

8 tables: `users`, `roles`, `user_roles` (M2M association), `api_keys`, `conversations`, `messages`, `knowledge_bases`, `documents`, `usage_logs`. Conversations have `kb_ids` (UUID array) for attaching knowledge bases. Messages have `tool_calls` (JSONB) and `extra` (JSONB). UsageLog records per-request token counts and latency.

### API endpoints

| Prefix | Module | Notes |
|---|---|---|
| `/api/v1/auth` | `auth.py` | register, login, refresh, me |
| `/api/v1/` | `chat.py` | conversations CRUD + send message |
| `/api/v1/` | `knowledge.py` | knowledge-bases CRUD |
| `/api/v1/` | `models.py` | static model catalog per provider |
| `/api/v1/` | `monitoring.py` | usage summary + by-model breakdown |
| `/api/v1/` | `admin.py` | user management + system stats (superuser only) |
| `/api/v1/` | `users.py` | (empty/placeholder) |

### Frontend

- `src/router/index.ts` — route guard auto-refreshes token on first visit, redirects unauthenticated users to `/login`
- `src/api/client.ts` — axios instance with JWT Bearer interceptor; 401 responses clear tokens and redirect to `/login`
- `src/stores/auth.ts` — Pinia store: login/register/refreshAccessToken/logout + `isAuthenticated` computed
- `src/views/` — lazy-loaded route components: ChatView, KnowledgeView, ModelsView, MonitorView, Login, admin/AdminUsers, admin/AdminSettings
- `src/types/index.ts` — shared TS interfaces mirroring backend response shapes
- Element Plus with Chinese locale; Pinia for state; `marked` + `highlight.js` for Markdown rendering; ECharts for charts

### Nginx routing

- `/api/` → proxied to `backend:8000` with WebSocket upgrade headers and 300s read timeout (for SSE streaming)
- `/` → serves static SPA from `/usr/share/nginx/html` with `try_files $uri /index.html`

## Key implementation notes

- **Chat is placeholder**: `chat_service.send_message()` returns a hardcoded reply; LLM API is not wired in yet
- **Engine/RAG are stubs**: `backend/app/engine/` and `backend/app/rag/` contain only skeleton files with TODO comments
- **RBAC is not implemented**: `core/permissions.py` is a stub; roles table exists but role checks are not enforced beyond `is_superuser`
- **Token storage**: JWT tokens stored in `localStorage` (not httpOnly cookies)
- **Dev proxy**: Vite dev server proxies `/api` to `localhost:8000` so frontend dev can run standalone without Docker
- **Database URL**: Alembic uses sync URL (`DATABASE_URL_SYNC`) via `psycopg2`; app uses async URL via `asyncpg`
- **Error messages**: Chinese (zh-CN) throughout — user-facing messages, API error details, UI labels
