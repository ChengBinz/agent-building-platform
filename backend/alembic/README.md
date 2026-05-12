# Alembic 数据库迁移指南

## 常用命令

```bash
# 自动检测模型变更并生成迁移脚本
docker compose exec backend alembic revision --autogenerate -m "描述信息"

# 执行所有待执行的迁移
docker compose exec backend alembic upgrade head

# 回滚到上一个版本
docker compose exec backend alembic downgrade -1

# 查看当前版本
docker compose exec backend alembic current

# 查看迁移历史
docker compose exec backend alembic history
```

## ⚠️ 已存在表的处理（重要）

### 问题描述

当数据库中已经存在表时，直接运行 `alembic upgrade head` 会报错：
```
sqlalchemy.exc.ProgrammingError: relation "xxx" already exists
```

### 解决方案

#### 方案一：跳过已存在的表（推荐）

在迁移脚本的 `upgrade()` 函数中，使用 `op.create_table_check()` 或手动检查表是否存在：

```python
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

def upgrade() -> None:
    # 获取数据库连接
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()

    # 只创建不存在的表
    if "mcp_servers" not in existing_tables:
        op.create_table(
            "mcp_servers",
            # ... 表定义
        )
```

#### 方案二：重置迁移版本（适用于开发环境）

```bash
# 1. 删除所有迁移文件
rm backend/alembic/versions/*.py

# 2. 清空 alembic_version 表
docker compose exec postgres psql -U agent -d agent_platform -c "DELETE FROM alembic_version;"

# 3. 重新初始化
docker compose exec backend alembic revision --autogenerate -m "init"
docker compose exec backend alembic upgrade head
```

#### 方案三：标记当前版本（适用于生产环境）

```bash
# 标记当前数据库状态为最新版本，不执行任何 SQL
docker compose exec backend alembic stamp head
```

## 新增表的最佳实践

### 1. 创建迁移脚本

```bash
docker compose exec backend alembic revision --autogenerate -m "add new_table"
```

### 2. 编辑迁移脚本

在生成的迁移脚本中，添加表存在性检查：

```python
"""add new_table

Revision ID: xxx
Revises: previous_revision
Create Date: 2026-05-12 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "xxx"
down_revision: Union[str, None] = "previous_revision"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()

    if "new_table" not in existing_tables:
        op.create_table(
            "new_table",
            sa.Column("id", sa.UUID(), nullable=False),
            # ... 其他列
            sa.PrimaryKeyConstraint("id"),
        )


def downgrade() -> None:
    op.drop_table("new_table")
```

### 3. 执行迁移

```bash
docker compose exec backend alembic upgrade head
```

## 常见问题

### Q: 迁移脚本顺序混乱怎么办？

A: 删除所有迁移文件，清空 `alembic_version` 表，重新生成：

```bash
rm backend/alembic/versions/*.py
docker compose exec postgres psql -U agent -d agent_platform -c "DELETE FROM alembic_version;"
docker compose exec backend alembic revision --autogenerate -m "init"
docker compose exec backend alembic upgrade head
```

### Q: 如何查看当前数据库有哪些表？

A: 连接数据库查看：

```bash
docker compose exec postgres psql -U agent -d agent_platform -c "\dt"
```

### Q: 迁移失败如何回滚？

A: 使用 `downgrade` 命令：

```bash
# 回滚到上一个版本
docker compose exec backend alembic downgrade -1

# 回滚到指定版本
docker compose exec backend alembic downgrade <revision_id>

# 回滚所有
docker compose exec backend alembic downgrade base
```

### Q: 如何跳过某个迁移？

A: 手动标记版本：

```bash
# 标记为已执行（不实际执行 SQL）
docker compose exec backend alembic stamp <revision_id>
```

## 版本文件命名规范

```
<序号>_<描述>.py

示例：
001_init_all_tables.py
002_add_mcp_tables.py
003_add_skill_tables.py
```

## 注意事项

1. **生产环境**：执行迁移前务必备份数据库
2. **开发环境**：可以使用 `alembic stamp head` 快速同步状态
3. **团队协作**：迁移文件必须提交到 Git
4. **自动检测**：`--autogenerate` 只检测模型定义的变更，不会检测数据变更
5. **手动修改**：如果手动修改了数据库结构，需要重新生成迁移脚本或使用 `stamp` 同步
