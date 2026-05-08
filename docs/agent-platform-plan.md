# Agent 智能体平台升级计划

## 当前状态

平台本质是一个**多模型聊天客户端** — 选模型、发消息、看历史。距离智能体平台还差三个核心能力：**工具调用**、**知识检索**、**记忆/规划**。

---

## 里程碑 1：Agent 基础模型与配置化（1-2 周）

**目标**：把"对话"升级为"智能体"，智能体可配置、可复用。

### 后端改动

- **新增 `agents` 表**，替代 `conversations` 作为顶层实体：
  - `id` (UUID PK)
  - `user_id` (FK → users)
  - `name` — Agent 名称
  - `description` — 描述
  - `avatar` — 头像 URL/emoji
  - `system_prompt` — 系统提示词（核心：定义 Agent 的行为边界和角色）
  - `model_name` — 默认模型
  - `provider` — 模型提供商
  - `tools` — JSON 数组，启用的工具 ID 列表
  - `kb_ids` — 关联的知识库 ID 列表
  - `created_at` / `updated_at`

- **修改 `conversations` 表**，新增 `agent_id` (FK → agents)，关系变为 `Agent 1—N Conversation`

- **新增 CRUD API**：`/api/v1/agents/`（list/create/get/update/delete）

### 前端改动

- **左侧栏**：从"对话列表"改为两层结构 — 智能体列表 → 选中智能体后展开其对话列表
- **智能体配置面板**（新建组件 `AgentConfig.vue`）：
  - 名称、描述、头像
  - 系统提示词编辑器（支持变量插槽如 `{{user_name}}`）
  - 模型选择
  - 知识库多选
- **对话界面**：顶部显示当前智能体名称 + 配置入口按钮
- **新 Store**：拆出 `agent.ts` Pinia store

### 数据关系

```
User 1—N Agent 1—N Conversation 1—N Message
```

---

## 里程碑 2：工具系统（2-3 周）

**目标**：给 Agent 装上手和眼睛 — 能调用外部工具、能搜知识库。

### 工具注册表（完善 `engine/tool_manager.py`，当前是空壳）

| 工具 | 功能 |
|---|---|
| `WebSearchTool` | 联网搜索 |
| `CodeInterpreterTool` | 代码执行（沙箱） |
| `KnowledgeRetrievalTool` | 从关联的知识库检索 |
| `HttpRequestTool` | 自定义 API 调用 |

每个工具定义：name、description、parameters（JSON Schema），自动拼入 LLM 请求的 `tools` 参数。

### ReAct 循环（新建 `engine/agent_loop.py`）

```
while not finished:
    response = LLM.chat(messages, tools)
    if response has tool_calls:
        results = execute_tools(tool_calls)
        messages.append(results)
    else:
        yield response.content  # 流式输出最终回复
```

- 最大循环次数限制（防止死循环）
- 错误处理：工具调用失败时把错误消息注入 conversation，让 LLM 自行修正

### 后端改动

- `ChatService` 增加 Agent 模式分支：当 Agent 配置了 tools 时走 ReAct 循环
- 工具执行用后台任务，避免阻塞 SSE 流式响应
- 工具执行结果存入 `Message.tool_calls`（JSONB，当前字段已存在但未使用）

### 前端改动

- 消息气泡中展示工具调用过程（折叠卡片：工具名 + 参数 + 结果摘要）
- 智能体配置面板中加入工具多选

---

## 里程碑 3：记忆与规划（2-3 周）

### 短期记忆（对话内）

- 新建 `MemoryService`（当前不存在）
- 新建 `conversation_memories` 表：
  - `id` (UUID PK)
  - `conversation_id` (FK → conversations, CASCADE)
  - `summary` — 摘要文本
  - `message_range` — 摘要覆盖的消息范围
  - `created_at`

- **触发**：每 5 轮对话（10 条消息）自动摘要
- **增量**：已有摘要时合并旧摘要 + 新消息一起生成新摘要
- **缓存**：Redis key `conversation_memory:{id}`，7 天 TTL
- **注入**：`ChatService._build_messages()` 注入摘要为 system message，历史消息裁剪到最近 10 条
- **后台执行**：流式模式中用 `asyncio.create_task` 异步执行，不阻塞
- **清理**：删除对话时级联删除（DB cascade + Redis 缓存删除）

### 长期记忆（跨对话/Agent 级）

- 新建 `agent_memories` 表：
  - `id` (UUID PK)
  - `agent_id` (FK → agents, CASCADE)
  - `key` — 记忆标识
  - `value` — 记忆内容
  - `created_at` / `updated_at`

- 用户显式告诉 Agent "记住 XXX" → 存入长期记忆
- 每次新对话时检索并注入相关长期记忆到 system prompt

### 规划能力

- 新建 `Planner` 模块
- 复杂任务先分解为子任务（步骤列表），逐步执行
- 前端展示当前执行计划（步骤条/树形组件）
- 每步完成后更新计划状态

---

## 技术决策

| 决策点 | 选择 | 原因 |
|---|---|---|
| Agent ↔ Conversation 关系 | 1:N | 复用现有对话系统，改动最小 |
| 工具执行方式 | 后台任务 | 避免阻塞 SSE 流式响应 |
| 前端状态管理 | Pinia 子 store 拆分 | 当前 `chat.ts` 已 200+ 行，按 Agent/Conversation/Tool 拆开 |
| Agent 模板 | `is_template` 标记 | 后期可扩展到一键复制 Agent 配置 |
| RAG 管线 | 先打通最小通路 | `rag/` 目录全是 stub，先让知识检索能跑通 |

---

## 执行优先级

1. **里程碑 1 前半**（最先做）— 新增 `agents` 表 + 前端配置面板，最小改动让平台从"聊天工具"变为"Agent 平台"
2. **里程碑 2** — 工具系统是 Agent 区别于聊天机器人的核心差异
3. **里程碑 3** — 记忆和规划让 Agent 能处理复杂长流程任务
