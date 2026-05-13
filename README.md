# AI Agent Platform

轻量化企业级 AI Agent 部署平台，支持多大模型统一接入、私有化 RAG 知识库、智能 Agent 对话、权限管控与调用监控。

## 技术栈

- **后端**: Python FastAPI + SQLAlchemy + Alembic
- **前端**: Vue 3 + TypeScript + Vite + Element Plus
- **数据库**: PostgreSQL 16 (pgvector)
- **向量库**: Qdrant
- **缓存**: Redis
- **反向代理**: Nginx

## 核心功能

- **多模型接入**: OpenAI、Anthropic、DeepSeek、阿里百炼(DashScope)、Ollama，统一 OpenAI 兼容接口
- **智能体系统**: 创建自定义 Agent，配置系统提示词、模型、关联知识库、选择工具
- **工具调用 (Function Calling)**: LLM 自主决定是否调用工具，支持 MCP 协议扩展工具生态
- **RAG 知识库**: 支持 txt/md 文档上传，自动分块、向量化、Qdrant 存储，对话时自动检索注入上下文
- **SSE 流式对话**: 实时流式输出，支持停止生成
- **对话记忆**: 每 5 轮自动摘要，Redis 缓存，防止上下文溢出
- **权限管控**: 用户/管理员分离，管理员注册码门控
- **调用监控**: 按模型统计 token 用量和调用次数

## 快速开始

### 环境要求

- Docker >= 24.0
- Docker Compose >= 2.0

### 一键部署

```bash
# 1. 复制环境变量配置
cp .env.example .env

# 2. 编辑 .env 填入必要的配置
vim .env

# 3. 构建并启动所有服务
docker compose up -d --build

# 4. 初始化管理员账号
docker compose exec backend python /app/scripts/seed.py

# 5. 访问 http://localhost 登录
```

### 开发模式

```bash
# 启动开发模式（热重载）
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build

# 前端开发服务器 (Vite HMR): http://localhost:5173
# 后端 API: http://localhost:8000
# 生产模式 (Nginx): http://localhost:80
```

### 默认管理员

运行种子脚本后自动创建：

- 用户名: `admin`
- 密码: `admin123`
- 首次登录后请立即修改密码

## 使用流程

1. **配置模型密钥**: 登录后进入「模型配置」页面，填写各 LLM 提供商和 Embedding 的 API Key
2. **创建知识库**: 进入「知识库管理」，新建知识库并上传 txt/md 文档，系统自动分块向量化
3. **配置 MCP 工具**（可选）: 启动 MCP Server，在「MCP 管理」页面添加服务器并同步工具
4. **创建智能体**: 进入对话页面，创建 Agent 并关联知识库、选择模型、选择工具
5. **开始对话**: 选择 Agent 开始对话，LLM 会根据需要自动调用已配置的工具

### 首次配置 MCP 工具

项目内置三个 MCP Server，随 Docker 自动启动：

| 名称 | URL | 功能 |
|------|-----|------|
| 天气 | `http://mcp-weather:9100` | 查询城市天气 |
| 时区 | `http://mcp-timezone:9101` | 查询时区时间 |
| 网页搜索 | `http://mcp-web-search:9102` | 搜索互联网（需配置 `TAVILY_API_KEY`） |

在 **MCP 管理** 页面操作：
1. 点击「新增服务器」，填入名称和 URL（如 `http://mcp-weather:9100`）
2. 点击「测试连接」确认可用
3. 点击「同步工具」导入工具列表
4. 创建/编辑 Agent 时，在工具列表中选择需要的工具

注册一次即可，配置保存在数据库中，重启不会丢失。

## 数据库管理

使用 Alembic 管理数据库迁移，后端启动时自动运行 `alembic upgrade head`。

**修改表结构的流程**：
1. 修改 `backend/app/models/` 下的 ORM 模型
2. 生成迁移脚本：`docker compose exec backend alembic revision --autogenerate -m "描述"`
3. 重启后端服务，迁移自动应用

## 项目结构

```
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/             # API 路由 (auth, chat, agents, knowledge, models, mcp, tools, admin)
│   │   ├── core/               # 安全、JWT
│   │   ├── models/             # SQLAlchemy ORM 模型
│   │   ├── schemas/            # Pydantic 请求/响应模型
│   │   ├── services/           # 业务逻辑 (chat_service, tool_service, mcp_service, mcp_client...)
│   │   ├── engine/             # LLM 引擎 (OpenAI 兼容统一接口，支持 tool_calls 流式解析)
│   │   ├── tools/              # 工具基类和注册表
│   │   ├── rag/                # RAG 流水线 (loader → chunker → embedder → vector_store → retriever)
│   │   └── db/                 # 数据库和 Redis 连接
│   └── alembic/                # 数据库迁移
├── mcp-servers/                # MCP Server (Docker 容器)
│   ├── weather/                # 天气查询 (wttr.in, 端口 9100)
│   ├── timezone/               # 时区查询 (Python stdlib, 端口 9101)
│   ├── web_search/             # 网页搜索 (Tavily API, 端口 9102)
│   ├── Dockerfile              # 共享 Dockerfile
│   └── requirements.txt        # 共享依赖
├── frontend/src/
│   ├── views/                  # 页面组件 (ChatView, KnowledgeView, ModelsView, McpView, Login...)
│   ├── components/
│   │   ├── chat/               # ChatSidebar, ChatMain, AgentDialog
│   │   ├── knowledge/          # KbConfigDialog, KbDetailDrawer
│   │   ├── mcp/                # McpServerTab, McpToolTab
│   │   └── layout/             # AppLayout, HeaderBar, SideNav
│   ├── stores/                 # Pinia 状态管理 (chat, agent, knowledge, auth)
│   ├── api/                    # HTTP 客户端 (axios + SSE fetch)
│   └── types/                  # TypeScript 类型定义
├── docker/                     # Docker 配置
├── scripts/                    # 工具脚本 (seed.py)
└── docker-compose.yml
```

## License

MIT
