# 后端架构基线文档

## 1. 项目信息

| 项 | 值 |
|---|-----|
| 项目名称 | AI Content Studio |
| 语言/框架 | Python 3.11 + FastAPI |
| ORM | SQLAlchemy 2.0 (async) |
| 数据库 | PostgreSQL 16 |
| 基线版本 | v1 |
| 生成时间 | 2026-06-16 |
| Git commit | 9455dbf |

---

## 2. 目录责任表

| 目录 | 单一职责 | 允许放置 | 禁止放置 | 来源 |
|------|---------|---------|---------|------|
| `backend/app/api/` | HTTP 路由入口，参数提取，权限校验调用 | Router 定义、Depends 注入、HTTPException 抛出 | ORM 查询语句、业务逻辑、数据库事务操作 | FastAPI 推荐 |
| `backend/app/services/` | 业务逻辑编排，数据校验，调用 ORM | 业务规则、跨表操作协调、数据转换 | HTTP 相关对象（Request/Response）、FastAPI Depends | 项目自定义 |
| `backend/app/models/` | ORM 映射定义 | 表结构、字段定义、关系映射 | 业务逻辑、查询辅助函数、数据校验规则 | SQLAlchemy 推荐 |
| `backend/app/schemas/` | 请求/响应数据结构定义 | Pydantic BaseModel、字段校验规则 | 业务逻辑、数据库操作 | FastAPI/Pydantic 推荐 |
| `backend/app/core/` | 基础设施：数据库引擎、配置、安全函数、日志 | 引擎创建、JWT 工具函数、Settings 类、日志配置 | 业务逻辑、请求/响应处理 | 项目自定义 |
| `backend/alembic/` | 数据库迁移脚本 | migration 文件、env.py | 应用代码 | Alembic 推荐 |
| `backend/tests/` | 测试用例 | pytest 测试文件、conftest fixtures | 应用业务代码 | pytest 推荐 |

---

## 3. 分层架构与调用路径

### 3.1 典型请求链路（以 `POST /api/v1/prompts` 为例）

```
1. 请求入口
   └─ app/api/v1/prompts.py:create_prompt()
      ├── 参数提取：FastAPI 自动将 JSON body 解析为 PromptCreate 对象
      ├── 身份认证：get_current_user (app/api/deps.py:15-28)
      │   └─ 解析 Authorization header → JWT 验证 → 数据库查询 User → 返回 User 对象
      └── 权限校验：workspace_service.check_workspace_access()
          └─ 检查当前用户是否属于目标工作空间 + 角色是否允许

2. 业务逻辑
   └─ app/services/prompt_service.py:create_prompt()
      ├── 提取变量：extract_variables(content)
      ├── 创建 Prompt ORM 对象
      ├── 创建 PromptVersion ORM 对象
      └── 返回 Prompt model 对象

3. 数据访问
   └─ SqlAlchemy async Session
      ├── db.add(prompt) → db.flush()
      └── db.add(version) → db.flush()

4. 响应返回
   └─ FastAPI 自动将 Prompt 对象序列化为 PromptResponse (Pydantic)
      └─ 返回 JSON: {"id": "...", "title": "...", ...}

5. 事务管理
   └─ app/core/database.py:get_db()
      ├── 成功：commit()  → 返回响应
      └── 失败：rollback() → HTTPException
```

### 3.2 分层职责速查

| 层 | 文件 | 负责 | 禁止 |
|----|------|------|------|
| Entry | `api/v1/*.py` | 路由定义、参数校验、权限调用、HTTP 状态码 | SQL 查询、事务管理 |
| Auth | `api/deps.py` | Token 解析、用户加载 | 业务权限判断 |
| Business | `services/*.py` | 业务规则、数据编排、跨表协调 | HTTP 对象、FastAPI Depends |
| Data | `models/*.py` | ORM 映射 | 业务逻辑 |
| Schema | `schemas/*.py` | 序列化/反序列化 | 数据库操作 |
| Infra | `core/*.py` | 配置、引擎、安全、日志 | 业务逻辑 |

---

## 4. 技术选型清单

| 技术/框架 | 版本 | 用途 | 类型 |
|----------|------|------|------|
| FastAPI | >=0.115.0 | Web 框架 | 框架原生 |
| uvicorn | >=0.30.0 | ASGI 服务器 | 框架原生 |
| SQLAlchemy | >=2.0.0 (async) | ORM | 框架原生 |
| asyncpg | >=0.30.0 | PostgreSQL 异步驱动 | 框架原生 |
| Pydantic | >=2.0.0 | 数据校验/序列化 | 框架原生 |
| pydantic-settings | >=2.0.0 | 环境变量管理 | 框架原生 |
| python-jose | >=3.3.0 | JWT 编解码 | 框架原生 |
| passlib + bcrypt | >=1.7.4 / >=4.0.0 | 密码哈希 | 框架原生 |
| Alembic | >=1.14.0 | 数据库迁移 | 框架原生 |
| slowapi | >=0.1.9 | API 速率限制 | 框架原生 |
| pytest + httpx | >=8.0.0 | 测试框架 | 框架原生 |
| `get_db` (database.py) | 项目自定义 | 异步 session 生命周期管理（commit/rollback） | 项目自定义 |
| `get_current_user` (deps.py) | 项目自定义 | JWT 解析 + User 加载的 FastAPI Depends | 项目自定义 |
| `check_workspace_access` (workspace_service.py) | 项目自定义 | 工作空间成员 + 角色校验 | 项目自定义 |

### 自定义封装合理性说明

**1. `get_db` (database.py:14-21)**

- 解决问题：在 FastAPI Depends 体系中管理异步 session 的 commit/rollback 生命周期
- 去掉后的代码：每个路由函数需手动 `await session.commit()` / `await session.rollback()`
- 框架能力：SQLAlchemy 本身不提供 FastAPI Depends 集成，此封装合理

**2. `get_current_user` (deps.py:15-28)**

- 解决问题：从 JWT token 提取 user_id → 查数据库 → 返回 User 对象，一次注入完成
- 去掉后的代码：每个路由需手动 3 步：解析 token、查用户、判空
- 框架能力：FastAPI 提供 Depends 机制但不提供 User 加载逻辑，此封装合理

**3. `check_workspace_access` (workspace_service.py)**

- 解决问题：跨所有 API 复用"用户是否属于工作空间 + 角色检查"逻辑
- 去掉后的代码：每个路由需要手动查询 workspace_members 表 + 判断角色
- 框架能力：SQLAlchemy 提供查询能力但不提供业务规则，此封装合理

**4. `JSONFormatter` (logging.py:8-16)**

- 解决问题：结构化 JSON 日志输出
- 去掉后的代码：日志为纯文本，难以被日志系统解析
- 框架能力：Python logging 提供 Formatter 但不提供 JSON 格式，此封装合理

---

## 5. 接口规范

### 5.1 响应结构

**列表查询（统一格式）：**
```json
{
  "code": 0,
  "data": {
    "items": [...],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}
```

**单条操作（Pydantic 直接序列化，无外层包裹）：**
```json
{
  "id": "uuid",
  "title": "...",
  ...
}
```

**成功操作（简单消息）：**
```json
{"message": "Deleted"}
```

### 5.2 错误响应

所有错误通过 `HTTPException` 抛出，FastAPI 自动生成：
```json
{"detail": "Error message"}
```

### 5.3 HTTP 状态码约定

| 场景 | 状态码 |
|------|--------|
| 成功 | 200 |
| 创建成功 | 200 (非 201) |
| 参数校验失败 | 400 |
| 认证失败 | 401 |
| 权限不足 | 403 |
| 资源不存在 | 404 |
| 速率限制 | 429 |

### 5.4 认证方式

- JWT Bearer Token：
  ```
  Authorization: Bearer <access_token>
  ```
- access token 过期时间：30 分钟
- refresh token 过期时间：7 天

---

## 6. 启动与配置

### 6.1 启动命令

```bash
# 开发模式
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Docker 部署
docker compose up -d
```

### 6.2 关键配置项 (.env)

| 变量 | 用途 | 默认值 |
|------|------|--------|
| DATABASE_URL | 异步数据库连接 URL | postgresql+asyncpg://... |
| SECRET_KEY | JWT 签名密钥 | 无默认，必须设置 |
| ACCESS_TOKEN_EXPIRE_MINUTES | Access token 有效期 | 30 |
| REFRESH_TOKEN_EXPIRE_DAYS | Refresh token 有效期 | 7 |
| CORS_ORIGINS | 允许的跨域来源 | http://localhost |
| ADMIN_EMAIL | 默认管理员邮箱 | admin@example.com |
| ADMIN_PASSWORD | 默认管理员密码 | 无默认，必须设置 |

### 6.3 健康检查

```bash
curl http://localhost:8000/api/health
# 返回: {"status": "ok"}
```

---

## 7. 验收记录

| 日期 | 基线版本 | 验收模式 | 通过 | 警告 | 未通过 | 备注 |
|------|---------|---------|------|------|--------|------|
| 2026-06-16 | v1 | 首次全量 | - | - | - | 基线建立 |
| 2026-06-16 | v1 | 首次全量验收 | 2 | 2 | 2 | 有条件通过，export 模块无 service 层 + workspace 跨层 SQL |
| 2026-06-16 | v1 | 阻塞项修复验证 | 4 | 2 | 0 | ✅ 全部通过，export 已有 service 层，workspace 跨层 SQL 已消除 |
| 2026-06-16 | v1 | 增量验收（CI修复后） | 6 | 0 | 0 | ✅ 全部通过，17 commits 均为测试/配置/修复，架构未变 |
| 2026-07-02 | v1 | 增量验收（前端导出+登录修复后） | 5 | 1 | 0 | ⚠️ 有条件通过，RegisterRequest 缺少字段长度校验 |
| 2026-07-03 | v1 | 增量验收（v1.3.0 DeepSeek API） | 5 | 1 | 0 | ⚠️ 有条件通过，contents.py API层含内联SQL查询 |
| 2026-07-03 | v1 | 警告修复（SQL提取至service层） | 6 | 0 | 0 | ✅ 全部通过，API层零SQL，新增 validate_stream_request 消除跨层泄露 |
