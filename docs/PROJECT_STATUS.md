# AI Content Studio — 项目状态

## 概览

AI 内容工坊后台管理系统，基于 Prompt 模板的 AI 内容生成、审核、管理平台。

**当前版本：** v1.4.2 | **启动：** `docker compose up -d` | **[Release 历史](https://github.com/mercury0993/ai-content-studio/releases)**

## 功能完成度

| 模块 | 后端 | 前端 | 状态 |
|------|------|------|------|
| 用户认证 | JWT + RBAC (admin/editor/viewer) | 登录/注册 + 路由守卫 | ✅ |
| 工作空间 | CRUD + 成员管理 | 列表/详情 | ✅ |
| Prompt 管理 | CRUD + 变量提取 + 版本历史 | 列表/创建/编辑/版本 | ✅ |
| AI 模型 | CRUD + 启用/禁用 | 配置页 | ✅ |
| 内容生成 | DeepSeek API + SSE 流式 | 流式输出 + 提交审核 | ✅ |
| 审核工作流 | 提交/通过/驳回/批量 + 审计日志 | 审核中心 | ✅ |
| 数据看板 | 统计/趋势/模型使用/排名 | ECharts 4 种图表 | ✅ |
| 内容导出 | Markdown 单篇 + ZIP 批量 | 单篇/批量导出 | ✅ |
| 个人设置 | 资料修改 + 密码修改 | 设置页 | ✅ |
| 前端设计系统 | OKLCH 品牌色 + 动效 + 空状态引导 | 全部页面 | ✅ |
| TypeScript 全覆盖 | 12 个 API 接口类型定义 | 0 处 `as any` | ✅ |
| 基础设施 | Seed 数据 + CI/CD + 健康检查 + 日志 + 迁移 | — | ✅ |
| 安全防护 | RBAC 权限 + 速率限制 + CORS + 密码复杂度 | 按钮级权限 + XSS 防护 | ✅ |

## 技术栈

- **后端:** Python 3.11 + FastAPI + SQLAlchemy 2.0 (async) + Pydantic
- **前端:** Vue 3 + TypeScript + Element Plus + Pinia + Vue Router + ECharts
- **数据库:** PostgreSQL 16
- **部署:** Docker Compose（postgres + backend + frontend/nginx）

## 启动方式

```bash
cp .env.example .env
cp backend/.env.example backend/.env
# 编辑 backend/.env，设置 SECRET_KEY、POSTGRES_PASSWORD、DEEPSEEK_API_KEY
docker compose up -d
```

- 前端：http://localhost
- API 文档：http://localhost:8000/docs
- 管理员账号：`.env` 中 `ADMIN_EMAIL` / `ADMIN_PASSWORD` 配置

## API 端点（共 44 个）

| 模块 | 端点数 | 说明 |
|------|--------|------|
| Auth | 6 | register, login, refresh, me, profile, change-password |
| Workspaces | 7 | CRUD + members |
| Prompts | 7 | CRUD + versions + rollback |
| Models | 6 | CRUD + toggle |
| Contents | 6 | CRUD + generate + generate-stream (SSE) |
| Reviews | 5 | list, submit, approve, reject, batch |
| Dashboard | 5 | stats, trend, model-usage, user-ranking, recent |
| Export | 2 | markdown, zip |

## 安全措施

- 所有密钥通过 `.env` 管理，`.gitignore` 已排除
- CORS 限制（`CORS_ORIGINS` 环境变量）
- API 速率限制（全局 60/min，登录 10/min，注册 5/min）
- 密码复杂度：须同时包含字母和数字
- 按钮级 RBAC 权限控制
- 前端 0 处 XSS 漏洞（无 `innerHTML`/`v-html`）

## 已知问题

1. **流式生成 Token 统计** — 流式模式下暂无法获取，显示"暂不支持"
2. **无 HTTPS** — 本地演示用 HTTP，生产需配置 SSL

## 仓库

- GitHub：https://github.com/mercury0993/ai-content-studio
- 分支：`feature/ai-content-studio`
- 最新版本：v1.4.0
