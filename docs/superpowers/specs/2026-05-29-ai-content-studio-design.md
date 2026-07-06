# AI Content Studio - Design Spec

## Overview

AI 内容工坊后台管理系统。用户通过 Prompt 模板 + 变量填写 + AI 模型选择来生成内容，支持审核工作流、数据看板、内容导出等功能。

**目标：** 面试演示项目，`docker compose up` 一键启动，浏览器访问 `http://localhost` 展示完整功能。

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vue 3 + TypeScript + Element Plus + Pinia + Vue Router + ECharts |
| Backend | Python 3.x + FastAPI + SQLAlchemy 2.0 (async) + Pydantic |
| Database | PostgreSQL |
| Deploy | Docker Compose (postgres + backend + frontend/nginx) |

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| AI Generation | Mock mode — backend returns preset fake content | No API keys needed, zero cost, demo is reliable |
| Streaming Output | Frontend simulated — `setInterval` character-by-character | No backend SSE needed, simpler code, same visual effect |
| Reviewer Assignment | Manual selection from workspace members | Simple, sufficient for demo |
| Dashboard Data | Real database queries | Data changes with operations, demonstrates backend capability |
| Access Port | 80 (http://localhost) | Clean URL for demo |

## Project Structure

```
ai-content-studio/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── auth.py
│   │   │   │   ├── prompts.py
│   │   │   │   ├── contents.py
│   │   │   │   ├── reviews.py
│   │   │   │   ├── models.py
│   │   │   │   ├── workspaces.py
│   │   │   │   └── dashboard.py
│   │   │   └── deps.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── database.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── prompt.py
│   │   │   ├── content.py
│   │   │   ├── workspace.py
│   │   │   └── ai_model.py
│   │   ├── schemas/
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   ├── prompt_service.py
│   │   │   ├── content_service.py
│   │   │   ├── review_service.py
│   │   │   ├── ai_service.py
│   │   │   └── dashboard_service.py
│   │   └── main.py
│   ├── alembic/
│   ├── tests/
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   │   ├── Login.vue
│   │   │   ├── Register.vue
│   │   │   ├── Dashboard.vue
│   │   │   ├── prompts/
│   │   │   ├── contents/
│   │   │   ├── reviews/
│   │   │   ├── models/
│   │   │   ├── workspaces/
│   │   │   └── settings/
│   │   ├── components/
│   │   ├── stores/
│   │   ├── api/
│   │   ├── router/
│   │   └── utils/
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── README.md
```

## Database Schema

### users
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| username | VARCHAR(50) | unique |
| email | VARCHAR(100) | unique |
| hashed_password | VARCHAR(200) | bcrypt |
| role | ENUM(admin, editor, viewer) | default: viewer |
| is_active | BOOLEAN | default: true |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

### workspaces
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| name | VARCHAR(100) | |
| description | TEXT | nullable |
| owner_id | UUID | FK→users |
| created_at | TIMESTAMP | |

### workspace_members
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| workspace_id | UUID | FK→workspaces |
| user_id | UUID | FK→users |
| role | ENUM(admin, editor, viewer) | space-level role |
| joined_at | TIMESTAMP | |

### prompts
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| workspace_id | UUID | FK→workspaces |
| title | VARCHAR(200) | |
| content | TEXT | contains {{variable}} placeholders |
| category | VARCHAR(50) | |
| tags | JSONB | ["marketing", "tech"] |
| variables | JSONB | [{"name":"product","required":true}] |
| version | INTEGER | default: 1 |
| is_favorite | BOOLEAN | default: false |
| created_by | UUID | FK→users |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

### prompt_versions
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| prompt_id | UUID | FK→prompts |
| version | INTEGER | |
| content | TEXT | snapshot |
| created_at | TIMESTAMP | |

### ai_models
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| workspace_id | UUID | FK→workspaces |
| name | VARCHAR(100) | display name |
| provider | VARCHAR(50) | openai/claude/wenxin |
| api_key | TEXT | encrypted storage |
| base_url | VARCHAR(200) | |
| model_name | VARCHAR(100) | |
| is_active | BOOLEAN | default: true |
| default_params | JSONB | {"temperature":0.7,"max_tokens":2000} |

### contents
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| workspace_id | UUID | FK→workspaces |
| prompt_id | UUID | FK→prompts |
| model_id | UUID | FK→ai_models |
| variables_used | JSONB | |
| generated_text | TEXT | |
| edited_text | TEXT | nullable |
| status | ENUM(draft, pending_review, approved, rejected) | default: draft |
| token_usage | INTEGER | simulated |
| generation_time_ms | INTEGER | simulated |
| review_comment | TEXT | nullable |
| reviewed_by | UUID | FK→users, nullable |
| reviewed_at | TIMESTAMP | nullable |
| created_by | UUID | FK→users |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

### audit_logs
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| user_id | UUID | FK→users |
| action | VARCHAR(50) | e.g. "content.status_change" |
| resource_type | VARCHAR(50) | e.g. "content" |
| resource_id | UUID | |
| details | JSONB | |
| created_at | TIMESTAMP | |

## API Design

- Base prefix: `/api/v1/`
- Auth: JWT Bearer token (access + refresh)
- Unified response:
  - Success: `{"code": 0, "message": "success", "data": {...}}`
  - Paginated: `{"code": 0, "data": {"items": [...], "total": 100, "page": 1, "page_size": 20}}`
  - Error: `{"code": 40001, "message": "Not found", "data": null}`

### Endpoints

**Auth**
- POST `/api/v1/auth/register`
- POST `/api/v1/auth/login`
- POST `/api/v1/auth/refresh`
- GET `/api/v1/auth/me`

**Workspaces**
- GET/POST `/api/v1/workspaces`
- GET/PUT/DELETE `/api/v1/workspaces/{id}`
- POST `/api/v1/workspaces/{id}/members`
- DELETE `/api/v1/workspaces/{id}/members/{user_id}`

**Prompts**
- GET/POST `/api/v1/prompts`
- GET/PUT/DELETE `/api/v1/prompts/{id}`
- GET `/api/v1/prompts/{id}/versions`
- POST `/api/v1/prompts/{id}/rollback/{version}`

**AI Models**
- GET/POST `/api/v1/models`
- GET/PUT/DELETE `/api/v1/models/{id}`
- PATCH `/api/v1/models/{id}/toggle`

**Contents**
- GET `/api/v1/contents`
- POST `/api/v1/contents/generate` (mock AI)
- GET/PUT/DELETE `/api/v1/contents/{id}`

**Reviews**
- GET `/api/v1/reviews`
- POST `/api/v1/reviews/{id}/submit`
- POST `/api/v1/reviews/{id}/approve`
- POST `/api/v1/reviews/{id}/reject`
- POST `/api/v1/reviews/batch`

**Dashboard**
- GET `/api/v1/dashboard/stats`
- GET `/api/v1/dashboard/trend`
- GET `/api/v1/dashboard/model-usage`
- GET `/api/v1/dashboard/user-ranking`
- GET `/api/v1/dashboard/recent`

**Export**
- GET `/api/v1/export/markdown/{id}`
- POST `/api/v1/export/zip`

## Frontend Pages (15)

1. `/login` — 登录
2. `/register` — 注册
3. `/dashboard` — 数据看板（ECharts 图表 + 统计卡片）
4. `/workspaces` — 工作空间列表
5. `/workspaces/:id` — 空间详情/成员管理
6. `/prompts` — Prompt 列表（搜索/筛选/分页）
7. `/prompts/create` — 新建 Prompt
8. `/prompts/:id/edit` — 编辑 Prompt
9. `/prompts/:id/versions` — 版本历史
10. `/contents` — 内容列表
11. `/contents/create` — 生成内容（选 Prompt → 填变量 → 选模型 → 生成）
12. `/contents/:id` — 内容详情/编辑
13. `/reviews` — 审核中心
14. `/models` — AI 模型配置
15. `/settings` — 个人设置

## RBAC

Three roles: admin, editor, viewer

**Menu visibility:**
- admin: all menus
- editor: Dashboard, Prompts, Contents, Reviews
- viewer: Dashboard, Contents (read-only)

**Button-level permissions:**
- Create/Edit/Delete: admin + editor
- Approve/Reject: admin + editor
- View: all roles

## AI Mock Behavior

`POST /api/v1/contents/generate` returns preset mock content based on prompt category:
- `marketing`: product description template
- `tech_doc`: technical document template
- `social_media`: social post template
- default: generic article

Simulated metrics: token_usage (random 500-2000), generation_time_ms (random 800-3000).

Frontend renders content character-by-character using `setInterval` for streaming effect.

## Deployment

docker-compose.yml with 3 services:
- `postgres`: PostgreSQL 16, data persisted to named volume
- `backend`: FastAPI app, env vars for DB connection
- `frontend`: Nginx serving Vue build, reverse proxy `/api` → backend:8000

Seed data on first startup:
- Default admin: `admin@example.com` / `admin123`
- Default workspace with sample prompts and AI model config

## Implementation Order

1. Project skeleton (Docker Compose + database + basic config)
2. User auth & RBAC (register/login/JWT/roles)
3. Workspace management (CRUD + members)
4. Prompt template management (CRUD + versions + search)
5. AI model configuration (CRUD + toggle)
6. AI content generation (mock + frontend streaming effect)
7. Content review workflow (submit/approve/reject/batch)
8. Dashboard (ECharts: stats/trend/model-usage/ranking)
9. Content export (Markdown/ZIP)
