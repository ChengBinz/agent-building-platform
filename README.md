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
- **智能体系统**: 创建自定义 Agent，配置系统提示词、模型、关联知识库
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
3. **创建智能体**: 进入对话页面，创建 Agent 并关联知识库、选择模型
4. **开始对话**: 选择 Agent 开始对话，系统自动从关联知识库检索相关内容注入上下文

## 项目结构

```
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/             # API 路由 (auth, chat, agents, knowledge, models, admin)
│   │   ├── core/               # 安全、JWT
│   │   ├── models/             # SQLAlchemy ORM 模型
│   │   ├── schemas/            # Pydantic 请求/响应模型
│   │   ├── services/           # 业务逻辑 (ChatService, KnowledgeService, AuthService...)
│   │   ├── engine/             # LLM 引擎 (OpenAI 兼容统一接口)
│   │   ├── rag/                # RAG 流水线 (loader → chunker → embedder → vector_store → retriever)
│   │   └── db/                 # 数据库和 Redis 连接
│   └── alembic/                # 数据库迁移
├── frontend/src/
│   ├── views/                  # 页面组件 (ChatView, KnowledgeView, ModelsView, Login...)
│   ├── components/
│   │   ├── chat/               # ChatSidebar, ChatMain, AgentDialog
│   │   ├── knowledge/          # KbConfigDialog, KbDetailDrawer
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
