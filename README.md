# AI Content Studio

AI 内容工坊后台管理系统 — 基于 Prompt 模板的 AI 内容生成、审核、管理平台。

## 技术栈

- **后端:** Python 3.x + FastAPI + SQLAlchemy 2.0 (async) + Pydantic
- **前端:** Vue 3 + TypeScript + Element Plus + Pinia + Vue Router + ECharts
- **数据库:** PostgreSQL 16
- **部署:** Docker + Docker Compose

## 功能模块

- 用户认证与 RBAC 权限（admin/editor/viewer）
- 多工作空间管理
- Prompt 模板管理（CRUD + 变量提取 + 版本历史）
- AI 模型配置
- AI 内容生成（模拟模式 + 流式输出效果）
- 内容审核工作流（提交/通过/驳回/批量）
- 数据看板（ECharts 图表）
- 内容导出（Markdown/ZIP）

## 快速启动

```bash
# 1. 克隆项目
git clone <repo-url>
cd ai-content-studio

# 2. 配置环境变量
cp backend/.env.example backend/.env

# 3. 启动服务
docker compose up -d

# 4. 访问
# 浏览器打开 http://localhost
# 默认管理员: admin@example.com / REDACTED_PASSWORD
```

## 项目结构

```
ai-content-studio/
├── backend/          # FastAPI 后端
│   └── app/
│       ├── api/v1/   # REST API 路由
│       ├── core/     # 配置、数据库、安全
│       ├── models/   # SQLAlchemy ORM 模型
│       ├── schemas/  # Pydantic 请求/响应模型
│       └── services/ # 业务逻辑层
├── frontend/         # Vue 3 前端
│   └── src/
│       ├── api/      # Axios 接口封装
│       ├── views/    # 页面组件
│       ├── stores/   # Pinia 状态管理
│       ├── router/   # 路由配置
│       ├── layouts/  # 布局组件
│       └── utils/    # 工具函数
├── docker-compose.yml
└── README.md
```

## API 文档

启动后访问 http://localhost:8000/docs 查看 Swagger 文档。

## 功能截图

| 页面 | 说明 |
|------|------|
| 登录页 | JWT 认证，支持注册/登录 |
| 数据看板 | ECharts 图表展示统计信息 |
| Prompt 管理 | CRUD + 变量提取 + 版本历史 |
| 内容生成 | 选择 Prompt → 填变量 → 选模型 → 流式生成 |
| 审核中心 | 提交/通过/驳回/批量审核 |
| AI 模型 | 配置多个 AI 模型（模拟模式） |

## 默认账号

| 角色 | 邮箱 | 密码 |
|------|------|------|
| 管理员 | admin@example.com | REDACTED_PASSWORD |
