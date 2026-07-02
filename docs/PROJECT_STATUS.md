# AI Content Studio — 项目状态

## 概览

AI 内容工坊后台管理系统，基于 Prompt 模板的 AI 内容生成、审核、管理平台。

**当前状态：** v1.3.0，`docker compose up -d` 一键启动。已接入 DeepSeek API，支持真实 AI 生成 + SSE 流式输出。

**安全状态：** Git 历史已清理，无硬编码密码/密钥。所有敏感配置通过 `.env` 环境变量管理。CORS 已限制，API 已加速率限制。

## 功能完成度

| 模块 | 后端 | 前端 | 状态 |
|------|------|------|------|
| 项目骨架 | Docker Compose + FastAPI + PostgreSQL | Vue 3 + Element Plus + Vite | ✅ 完成 |
| 用户认证 | JWT + RBAC (admin/editor/viewer) | 登录/注册页 + 路由守卫 | ✅ 完成 |
| 工作空间 | CRUD + 成员管理 | 列表/详情页 | ✅ 完成 |
| Prompt 管理 | CRUD + 变量提取 + 版本历史 | 列表/创建/编辑/版本页 | ✅ 完成 |
| AI 模型 | CRUD + 启用/禁用 | 配置页 | ✅ 完成 |
| 内容生成 | DeepSeek API + SSE 真流式 | 流式输出 + 提交审核 | ✅ 完成 |
| 审核工作流 | 提交/通过/驳回/批量 + 审计日志 | 审核中心页 | ✅ 完成 |
| 数据看板 | 统计/趋势/模型使用/排名 API | ECharts 4 种图表 | ✅ 完成 |
| 内容导出 | Markdown 单篇 + ZIP 批量下载 | 单篇导出按钮 + 批量选择导出 | ✅ 完成 |
| 个人设置 | 个人资料修改 + 密码修改 | 设置页 | ✅ 完成 |
| Seed 数据 | 默认工作空间 + 示例 Prompt + AI 模型 | — | ✅ 完成 |
| 按钮级权限 | `canEdit()` 应用于所有操作按钮 | 5 个页面按钮控制 | ✅ 完成 |
| 速率限制 | slowapi 全局限 60/min，auth 更严格 | — | ✅ 完成 |
| CORS 限制 | 通过环境变量 `CORS_ORIGINS` 配置 | — | ✅ 完成 |
| 结构化日志 | JSON 格式请求日志 | — | ✅ 完成 |
| Docker 健康检查 | backend 容器健康检查 | — | ✅ 完成 |
| CI/CD | GitHub Actions 自动测试/构建 | — | ✅ 完成 |
| 单元测试 | 6 个测试文件覆盖全部 API 模块 | — | ✅ 完成 |
| Alembic 迁移 | 全部 7 张表的完整迁移 | — | ✅ 完成 |

## 技术栈

- **后端:** Python 3.11 + FastAPI + SQLAlchemy 2.0 (async) + Pydantic
- **前端:** Vue 3 + TypeScript + Element Plus + Pinia + Vue Router + ECharts
- **数据库:** PostgreSQL 16
- **部署:** Docker Compose（postgres + backend + frontend/nginx）

## 启动方式

```bash
cd ai-content-studio
cp .env.example .env
cp backend/.env.example backend/.env
docker compose up -d
```

- 前端：http://localhost
- 后端 API 文档：http://localhost:8000/docs
- 管理员账号：由 `.env` 中的 `ADMIN_EMAIL` / `ADMIN_PASSWORD` 配置

## DeepSeek API 配置

1. 在 `backend/.env` 中设置 `DEEPSEEK_API_KEY=你的key`
2. 重建容器：`docker compose build backend && docker compose up -d`
3. 在系统内创建 AI 模型：提供商选 DeepSeek，模型标识 `deepseek-chat`，Base URL 自动填充
4. 新功能：SSE 真流式输出、一键提交审核、注册自动加入工作空间、导出不再限制审核状态

## 文件结构

```
ai-content-studio/
├── backend/
│   └── app/
│       ├── api/v1/          # 8 个路由模块（auth, workspaces, prompts, models, contents, reviews, dashboard, export）
│       ├── core/            # config, database, security
│       ├── models/          # 7 个 ORM 模型（User, Workspace, WorkspaceMember, Prompt, PromptVersion, AIModel, Content, AuditLog）
│       ├── schemas/         # 6 个 Pydantic schema 模块
│       ├── services/        # 8 个业务 service
│       └── main.py          # FastAPI 入口 + seed 数据
├── frontend/
│   └── src/
│       ├── api/             # 9 个 API 模块
│       ├── views/           # 15 个页面组件
│       ├── stores/          # 2 个 Pinia store
│       ├── router/          # 路由 + 权限守卫
│       ├── layouts/         # MainLayout 侧边栏布局
│       └── utils/           # 权限工具
├── docker-compose.yml
├── .env.example
└── README.md
```

## API 端点汇总

| 模块 | 端点数 | 说明 |
|------|--------|------|
| Auth | 6 | register, login, refresh, me, update profile, change password |
| Workspaces | 7 | CRUD + members |
| Prompts | 7 | CRUD + versions + rollback |
| Models | 6 | CRUD + toggle |
| Contents | 6 | CRUD + generate + generate-stream (SSE) |
| Reviews | 5 | list, submit, approve, reject, batch |
| Dashboard | 5 | stats, trend, model-usage, user-ranking, recent |
| Export | 2 | markdown, zip |
| **合计** | **44** | |

## 已知问题与待改进

### 功能层面
1. **流式生成 Token 统计** — 流式模式下 token 消耗暂无法获取，显示"暂不支持"；非流式模式正常统计

### 生产就绪层面
2. **无 HTTPS** — 本地演示用 HTTP，生产环境需配置 SSL

## 安全措施

- `.env` 文件未被 git 跟踪（已在 `.gitignore` 中排除）
- Git 历史已清理，无硬编码密码/密钥残留
- `SECRET_KEY`、`POSTGRES_PASSWORD`、`ADMIN_PASSWORD` 均通过环境变量配置
- 数据库密码和管理员密码不在代码中硬编码
- CORS 通过 `CORS_ORIGINS` 环境变量限制（默认仅 `http://localhost`）
- API 速率限制：全局限 60 req/min，登录 10/min，注册 5/min
- 密码复杂度：注册/修改密码须同时包含字母和数字
- 按钮级权限控制：viewer 角色看不到编辑/删除/审批按钮

## Git 记录

- 仓库：https://github.com/mercury0993/ai-content-studio
- 分支：`feature/ai-content-studio`
- 所有代码已提交，敏感信息已排除且历史已清理
- 最新版本：v1.3.0（DeepSeek API 接入 + SSE 真流式 + 审核优化 + Bug 修复）
- [GitHub Releases](https://github.com/mercury0993/ai-content-studio/releases)
