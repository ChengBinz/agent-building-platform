# AI Agent Platform

轻量化企业级 AI Agent 部署平台，支持多大模型统一接入、私有化 RAG 知识库、智能 Agent 对话、权限管控与调用监控。

## 技术栈

- **后端**: Python FastAPI + SQLAlchemy + Alembic
- **前端**: Vue 3 + TypeScript + Vite + Element Plus
- **数据库**: PostgreSQL 16
- **向量库**: Qdrant
- **缓存**: Redis
- **反向代理**: Nginx

## 快速开始

### 环境要求

- Docker >= 24.0
- Docker Compose >= 2.0

### 一键部署

```bash
# 1. 复制环境变量配置
cp .env.example .env

# 2. 编辑 .env 填入必要的配置（SECRET_KEY 必填）
vim .env

# 3. 启动所有服务
docker compose up -d

# 4. 访问
# http://localhost
```

### 开发模式

```bash
# 启动开发模式（热重载）
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 前端开发服务器: http://localhost:5173
# 后端 API: http://localhost:8000
```

### 默认管理员

首次启动后，运行种子脚本创建默认管理员：

```bash
docker compose exec backend python /app/scripts/seed.py
```

## 项目结构

```
├── backend/          # FastAPI 后端
│   ├── app/
│   │   ├── api/      # API 路由
│   │   ├── core/     # 安全、权限
│   │   ├── models/   # 数据库模型
│   │   ├── schemas/  # Pydantic 模型
│   │   ├── services/ # 业务逻辑
│   │   ├── engine/   # LLM 引擎抽象
│   │   ├── rag/      # RAG 流水线
│   │   └── middleware/
│   └── alembic/      # 数据库迁移
├── frontend/         # Vue 3 前端
│   └── src/
│       ├── views/    # 页面组件
│       ├── components/
│       ├── stores/   # Pinia 状态
│       └── api/      # HTTP 客户端
├── docker/           # Docker 配置
├── scripts/          # 工具脚本
└── docker-compose.yml
```

## License

MIT
