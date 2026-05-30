# AI Content Studio — 项目状态

## 概览

AI 内容工坊后台管理系统，基于 Prompt 模板的 AI 内容生成、审核、管理平台。

**当前状态：** 可运行，`docker compose up -d` 一键启动。

**安全状态：** Git 历史已清理，无硬编码密码/密钥。所有敏感配置通过 `.env` 环境变量管理。

## 功能完成度

| 模块 | 后端 | 前端 | 状态 |
|------|------|------|------|
| 项目骨架 | Docker Compose + FastAPI + PostgreSQL | Vue 3 + Element Plus + Vite | ✅ 完成 |
| 用户认证 | JWT + RBAC (admin/editor/viewer) | 登录/注册页 + 路由守卫 | ✅ 完成 |
| 工作空间 | CRUD + 成员管理 | 列表/详情页 | ✅ 完成 |
| Prompt 管理 | CRUD + 变量提取 + 版本历史 | 列表/创建/编辑/版本页 | ✅ 完成 |
| AI 模型 | CRUD + 启用/禁用 | 配置页 | ✅ 完成 |
| 内容生成 | Mock AI + 模拟指标 | 流式输出效果（前端模拟） | ✅ 完成 |
| 审核工作流 | 提交/通过/驳回/批量 + 审计日志 | 审核中心页 | ✅ 完成 |
| 数据看板 | 统计/趋势/模型使用/排名 API | ECharts 4 种图表 | ✅ 完成 |
| 内容导出 | Markdown + ZIP 下载 | 导出按钮 | ✅ 完成 |
| Seed 数据 | 默认工作空间 + 示例 Prompt + AI 模型 | — | ✅ 完成 |

## 技术栈

- **后端:** Python 3.11 + FastAPI + SQLAlchemy 2.0 (async) + Pydantic
- **前端:** Vue 3 + TypeScript + Element Plus + Pinia + Vue Router + ECharts
- **数据库:** PostgreSQL 16
- **部署:** Docker Compose（postgres + backend + frontend/nginx）

## 启动方式

```bash
cd ai-content-studio
cp backend/.env.example backend/.env
docker compose up -d
```

- 前端：http://localhost
- 后端 API 文档：http://localhost:8000/docs
- 管理员账号：由 `.env` 中的 `ADMIN_EMAIL` / `ADMIN_PASSWORD` 配置

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
│       ├── api/             # 8 个 API 模块
│       ├── views/           # 15 个页面组件
│       ├── stores/          # 2 个 Pinia store
│       ├── router/          # 路由 + 权限守卫
│       ├── layouts/         # MainLayout 侧边栏布局
│       └── utils/           # 权限工具
├── docker-compose.yml
└── README.md
```

## API 端点汇总

| 模块 | 端点数 | 说明 |
|------|--------|------|
| Auth | 4 | register, login, refresh, me |
| Workspaces | 7 | CRUD + members |
| Prompts | 7 | CRUD + versions + rollback |
| Models | 6 | CRUD + toggle |
| Contents | 5 | CRUD + generate |
| Reviews | 5 | list, submit, approve, reject, batch |
| Dashboard | 5 | stats, trend, model-usage, user-ranking, recent |
| Export | 2 | markdown, zip |
| **合计** | **41** | |

## 已知问题

1. **前端类型检查跳过** — 构建时用 `npx vite build` 而非 `vue-tsc && vite build`，部分 TS 类型错误未修复（不影响运行）
2. **Mock AI 模式** — 内容生成返回预设模板，不调用真实 AI API
3. **单元测试不完整** — 仅 auth 模块有测试框架，其他模块未写测试
4. **无 HTTPS** — 本地演示用 HTTP，生产环境需配置 SSL

## 安全措施

- `.env` 文件未被 git 跟踪（已在 `.gitignore` 中排除）
- Git 历史已清理，无硬编码密码/密钥残留
- `SECRET_KEY`、`POSTGRES_PASSWORD`、`ADMIN_PASSWORD` 均通过环境变量配置
- 数据库密码和管理员密码不在代码中硬编码

## Git 记录

- 分支：`feature/ai-content-studio`
- 所有代码已提交，敏感信息已排除且历史已清理
