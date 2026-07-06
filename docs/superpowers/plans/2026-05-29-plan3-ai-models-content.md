# AI Content Studio — Plan 3: AI Model Config + Content Generation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add AI model configuration management and mock content generation with frontend streaming effect.

**Architecture:** AI models are configured per-workspace but use mock responses (no real API calls). Content generation creates records with simulated token usage and generation time. Frontend displays content character-by-character using `setInterval`.

**Tech Stack:** Same as previous plans

**Prerequisite:** Plan 1 + Plan 2 completed

---

## Task 1: AI Model Backend

**Files:**
- Create: `backend/app/models/ai_model.py`
- Create: `backend/app/schemas/ai_model.py`
- Create: `backend/app/services/ai_model_service.py`
- Create: `backend/app/api/v1/models.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Create AI Model ORM model**

`backend/app/models/ai_model.py`:
```python
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AIModel(Base):
    __tablename__ = "ai_models"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    api_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    base_url: Mapped[str | None] = mapped_column(String(200), nullable=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    default_params: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 2: Update models/__init__.py**

```python
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.models.prompt import Prompt, PromptVersion
from app.models.ai_model import AIModel

__all__ = ["User", "Workspace", "WorkspaceMember", "Prompt", "PromptVersion", "AIModel"]
```

- [ ] **Step 3: Create AI model schemas**

`backend/app/schemas/ai_model.py`:
```python
import uuid
from datetime import datetime
from pydantic import BaseModel


class AIModelCreate(BaseModel):
    workspace_id: uuid.UUID
    name: str
    provider: str
    api_key: str | None = None
    base_url: str | None = None
    model_name: str
    default_params: dict | None = None


class AIModelUpdate(BaseModel):
    name: str | None = None
    provider: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    model_name: str | None = None
    default_params: dict | None = None


class AIModelResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    provider: str
    base_url: str | None
    model_name: str
    is_active: bool
    default_params: dict | None
    created_at: datetime

    class Config:
        from_attributes = True
```

- [ ] **Step 4: Create AI model service**

`backend/app/services/ai_model_service.py`:
```python
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_model import AIModel
from app.schemas.ai_model import AIModelCreate, AIModelUpdate


async def create_model(db: AsyncSession, req: AIModelCreate) -> AIModel:
    model = AIModel(
        workspace_id=req.workspace_id,
        name=req.name,
        provider=req.provider,
        api_key=req.api_key,
        base_url=req.base_url,
        model_name=req.model_name,
        default_params=req.default_params,
    )
    db.add(model)
    await db.flush()
    return model


async def list_models(db: AsyncSession, workspace_id: uuid.UUID) -> list[AIModel]:
    result = await db.execute(
        select(AIModel).where(AIModel.workspace_id == workspace_id).order_by(AIModel.created_at.desc())
    )
    return list(result.scalars().all())


async def get_model(db: AsyncSession, model_id: uuid.UUID) -> AIModel | None:
    result = await db.execute(select(AIModel).where(AIModel.id == model_id))
    return result.scalar_one_or_none()


async def update_model(db: AsyncSession, model_id: uuid.UUID, req: AIModelUpdate) -> AIModel:
    model = await get_model(db, model_id)
    if not model:
        raise ValueError("Model not found")
    if req.name is not None:
        model.name = req.name
    if req.provider is not None:
        model.provider = req.provider
    if req.api_key is not None:
        model.api_key = req.api_key
    if req.base_url is not None:
        model.base_url = req.base_url
    if req.model_name is not None:
        model.model_name = req.model_name
    if req.default_params is not None:
        model.default_params = req.default_params
    await db.flush()
    return model


async def delete_model(db: AsyncSession, model_id: uuid.UUID) -> None:
    model = await get_model(db, model_id)
    if not model:
        raise ValueError("Model not found")
    await db.delete(model)
    await db.flush()


async def toggle_model(db: AsyncSession, model_id: uuid.UUID) -> AIModel:
    model = await get_model(db, model_id)
    if not model:
        raise ValueError("Model not found")
    model.is_active = not model.is_active
    await db.flush()
    return model
```

- [ ] **Step 5: Create AI model router**

`backend/app/api/v1/models.py`:
```python
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.ai_model import AIModelCreate, AIModelUpdate, AIModelResponse
from app.services import ai_model_service, workspace_service

router = APIRouter(prefix="/models", tags=["models"])


@router.get("", response_model=list[AIModelResponse])
async def list_models(
    workspace_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await workspace_service.check_workspace_access(db, workspace_id, current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Not a member")
    return await ai_model_service.list_models(db, workspace_id)


@router.post("", response_model=AIModelResponse)
async def create_model(
    req: AIModelCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await workspace_service.check_workspace_access(db, req.workspace_id, current_user.id)
    if not member or member.role.value == "viewer":
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return await ai_model_service.create_model(db, req)


@router.get("/{model_id}", response_model=AIModelResponse)
async def get_model(model_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    model = await ai_model_service.get_model(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.put("/{model_id}", response_model=AIModelResponse)
async def update_model(
    model_id: uuid.UUID,
    req: AIModelUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await ai_model_service.update_model(db, model_id, req)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{model_id}")
async def delete_model(model_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        await ai_model_service.delete_model(db, model_id)
        return {"message": "Deleted"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{model_id}/toggle", response_model=AIModelResponse)
async def toggle_model(model_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        return await ai_model_service.toggle_model(db, model_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

- [ ] **Step 6: Register router in main.py**

```python
from app.api.v1.models import router as models_router
app.include_router(models_router, prefix="/api/v1")
```

- [ ] **Step 7: Generate migration and restart**

```bash
cd E:/lx/projects/ai-content-studio/backend
alembic revision --autogenerate -m "add ai_models table"
docker compose restart backend
```

- [ ] **Step 8: Commit**

```bash
git add backend/
git commit -m "feat: AI model configuration — CRUD + toggle active"
```

---

## Task 2: Content Backend — Model + Mock Generation

**Files:**
- Create: `backend/app/models/content.py`
- Create: `backend/app/schemas/content.py`
- Create: `backend/app/services/content_service.py`
- Create: `backend/app/services/ai_service.py`
- Create: `backend/app/api/v1/contents.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Create Content model**

`backend/app/models/content.py`:
```python
import enum
import uuid

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ContentStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class Content(Base):
    __tablename__ = "contents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    prompt_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("prompts.id"), nullable=False)
    model_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ai_models.id"), nullable=False)
    variables_used: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    generated_text: Mapped[str] = mapped_column(Text, nullable=False)
    edited_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ContentStatus] = mapped_column(Enum(ContentStatus), default=ContentStatus.DRAFT, nullable=False)
    token_usage: Mapped[int] = mapped_column(Integer, default=0)
    generation_time_ms: Mapped[int] = mapped_column(Integer, default=0)
    review_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

- [ ] **Step 2: Update models/__init__.py**

```python
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.models.prompt import Prompt, PromptVersion
from app.models.ai_model import AIModel
from app.models.content import Content, ContentStatus

__all__ = ["User", "Workspace", "WorkspaceMember", "Prompt", "PromptVersion", "AIModel", "Content", "ContentStatus"]
```

- [ ] **Step 3: Create content schemas**

`backend/app/schemas/content.py`:
```python
import uuid
from datetime import datetime
from pydantic import BaseModel


class ContentGenerate(BaseModel):
    workspace_id: uuid.UUID
    prompt_id: uuid.UUID
    model_id: uuid.UUID
    variables: dict | None = None


class ContentUpdate(BaseModel):
    edited_text: str | None = None


class ContentResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    prompt_id: uuid.UUID
    model_id: uuid.UUID
    variables_used: dict | None
    generated_text: str
    edited_text: str | None
    status: str
    token_usage: int
    generation_time_ms: int
    review_comment: str | None
    reviewed_by: uuid.UUID | None
    reviewed_at: datetime | None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

- [ ] **Step 4: Create mock AI service**

`backend/app/services/ai_service.py`:
```python
import random
import time

MOCK_CONTENTS = {
    "marketing": """# {title}

## 产品概述

{product_name} 是一款面向 {target_audience} 的创新产品。它采用了先进的技术架构，为用户提供了卓越的使用体验。

## 核心优势

1. **高效性能**：处理速度提升 300%，大幅降低等待时间
2. **智能适配**：自动识别用户需求，提供个性化推荐
3. **安全可靠**：企业级数据加密，保障信息安全

## 使用场景

- 日常办公效率提升
- 团队协作优化
- 数据分析与决策支持

## 总结

{product_name} 将成为您工作中不可或缺的得力助手。""",

    "tech_doc"""# {title}

## 1. 概述

本文档描述了 {product_name} 系统的技术架构和实现细节。

## 2. 系统架构

### 2.1 前端层
- Vue 3 + TypeScript
- Element Plus UI 组件库
- Pinia 状态管理

### 2.2 后端层
- Python FastAPI 异步框架
- SQLAlchemy 2.0 ORM
- PostgreSQL 数据库

### 2.3 部署架构
- Docker 容器化部署
- Nginx 反向代理
- 数据持久化存储

## 3. API 接口

所有接口遵循 RESTful 规范，统一前缀 `/api/v1/`。

## 4. 安全设计

- JWT Token 认证
- bcrypt 密码哈希
- RBAC 角色权限控制""",

    "social_media": """🚀 {product_name} 正式上线！

还在为 {target_audience} 的痛点烦恼吗？试试我们的全新解决方案：

✅ 操作简单，5 分钟上手
✅ 效率提升 300%
✅ 安全可靠，数据加密

立即体验 → [链接]

#效率工具 #创新产品 #{target_audience}""",

    "default": """# {title}

## 背景

在当今快速发展的数字化时代，{target_audience} 面临着前所未有的挑战和机遇。

## 解决方案

{product_name} 提供了一套完整的解决方案：

1. **需求分析**：深入了解用户痛点
2. **方案设计**：量身定制最优方案
3. **实施落地**：高效执行，快速见效

## 预期效果

- 效率提升：预计提升 200-500%
- 成本降低：平均节省 30% 运营成本
- 满意度：用户满意度达 95% 以上

## 下一步

联系我们获取更多详情，开启效率革命之旅。""",
}


def mock_generate(category: str | None, variables: dict | None, title: str = "AI 生成内容") -> dict:
    """Mock AI content generation."""
    template_key = category if category in MOCK_CONTENTS else "default"
    template = MOCK_CONTENTS[template_key]

    # Fill in variables
    vars_used = variables or {}
    vars_used.setdefault("title", title)
    vars_used.setdefault("product_name", "智能助手")
    vars_used.setdefault("target_audience", "企业用户")

    text = template
    for key, value in vars_used.items():
        text = text.replace(f"{{{key}}}", str(value))

    # Simulate metrics
    token_usage = random.randint(500, 2000)
    generation_time_ms = random.randint(800, 3000)

    return {
        "generated_text": text,
        "token_usage": token_usage,
        "generation_time_ms": generation_time_ms,
    }
```

- [ ] **Step 5: Create content service**

`backend/app/services/content_service.py`:
```python
import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content, ContentStatus
from app.models.prompt import Prompt
from app.schemas.content import ContentGenerate, ContentUpdate
from app.services.ai_service import mock_generate


async def generate_content(db: AsyncSession, user_id: uuid.UUID, req: ContentGenerate) -> Content:
    # Get prompt for category
    result = await db.execute(select(Prompt).where(Prompt.id == req.prompt_id))
    prompt = result.scalar_one_or_none()
    if not prompt:
        raise ValueError("Prompt not found")

    # Mock generate
    ai_result = mock_generate(prompt.category, req.variables, prompt.title)

    content = Content(
        workspace_id=req.workspace_id,
        prompt_id=req.prompt_id,
        model_id=req.model_id,
        variables_used=req.variables or {},
        generated_text=ai_result["generated_text"],
        status=ContentStatus.DRAFT,
        token_usage=ai_result["token_usage"],
        generation_time_ms=ai_result["generation_time_ms"],
        created_by=user_id,
    )
    db.add(content)
    await db.flush()
    return content


async def list_contents(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Content], int]:
    query = select(Content).where(Content.workspace_id == workspace_id)
    if status:
        query = query.where(Content.status == ContentStatus(status))

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    query = query.order_by(Content.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return list(result.scalars().all()), total


async def get_content(db: AsyncSession, content_id: uuid.UUID) -> Content | None:
    result = await db.execute(select(Content).where(Content.id == content_id))
    return result.scalar_one_or_none()


async def update_content(db: AsyncSession, content_id: uuid.UUID, req: ContentUpdate) -> Content:
    content = await get_content(db, content_id)
    if not content:
        raise ValueError("Content not found")
    if req.edited_text is not None:
        content.edited_text = req.edited_text
    await db.flush()
    return content


async def delete_content(db: AsyncSession, content_id: uuid.UUID) -> None:
    content = await get_content(db, content_id)
    if not content:
        raise ValueError("Content not found")
    await db.delete(content)
    await db.flush()
```

- [ ] **Step 6: Create content router**

`backend/app/api/v1/contents.py`:
```python
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.content import ContentGenerate, ContentUpdate, ContentResponse
from app.services import content_service, workspace_service

router = APIRouter(prefix="/contents", tags=["contents"])


@router.get("", response_model=dict)
async def list_contents(
    workspace_id: uuid.UUID,
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await workspace_service.check_workspace_access(db, workspace_id, current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Not a member")
    items, total = await content_service.list_contents(db, workspace_id, status, page, page_size)
    return {
        "code": 0,
        "data": {
            "items": [ContentResponse.model_validate(c) for c in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.post("/generate", response_model=ContentResponse)
async def generate_content(
    req: ContentGenerate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await workspace_service.check_workspace_access(db, req.workspace_id, current_user.id)
    if not member or member.role.value == "viewer":
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    try:
        return await content_service.generate_content(db, current_user.id, req)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(content_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    content = await content_service.get_content(db, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    member = await workspace_service.check_workspace_access(db, content.workspace_id, current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Not a member")
    return content


@router.put("/{content_id}", response_model=ContentResponse)
async def update_content(
    content_id: uuid.UUID,
    req: ContentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    content = await content_service.get_content(db, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    member = await workspace_service.check_workspace_access(db, content.workspace_id, current_user.id)
    if not member or member.role.value == "viewer":
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    try:
        return await content_service.update_content(db, content_id, req)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{content_id}")
async def delete_content(content_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    content = await content_service.get_content(db, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    member = await workspace_service.check_workspace_access(db, content.workspace_id, current_user.id)
    if not member or member.role.value == "viewer":
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    try:
        await content_service.delete_content(db, content_id)
        return {"message": "Deleted"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

- [ ] **Step 7: Register router in main.py**

```python
from app.api.v1.contents import router as contents_router
app.include_router(contents_router, prefix="/api/v1")
```

- [ ] **Step 8: Generate migration and restart**

```bash
cd E:/lx/projects/ai-content-studio/backend
alembic revision --autogenerate -m "add contents table"
docker compose restart backend
```

- [ ] **Step 9: Commit**

```bash
git add backend/
git commit -m "feat: content generation — mock AI service + CRUD"
```

---

## Task 3: Frontend — AI Model Pages

**Files:**
- Create: `frontend/src/api/aiModels.ts`
- Create: `frontend/src/views/models/ModelList.vue`
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/layouts/MainLayout.vue`

- [ ] **Step 1: Create AI model API**

`frontend/src/api/aiModels.ts`:
```typescript
import request from './request'

export function listModels(workspaceId: string) {
  return request.get('/models', { params: { workspace_id: workspaceId } })
}

export function createModel(data: {
  workspace_id: string
  name: string
  provider: string
  api_key?: string
  base_url?: string
  model_name: string
  default_params?: Record<string, any>
}) {
  return request.post('/models', data)
}

export function updateModel(id: string, data: Record<string, any>) {
  return request.put(`/models/${id}`, data)
}

export function deleteModel(id: string) {
  return request.delete(`/models/${id}`)
}

export function toggleModel(id: string) {
  return request.patch(`/models/${id}/toggle`)
}
```

- [ ] **Step 2: Create ModelList.vue**

`frontend/src/views/models/ModelList.vue`:
```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useWorkspaceStore } from '@/stores/workspace'
import { listModels, createModel, updateModel, deleteModel, toggleModel } from '@/api/aiModels'
import { ElMessage, ElMessageBox } from 'element-plus'

const workspaceStore = useWorkspaceStore()
const models = ref<any[]>([])
const showCreate = ref(false)
const editingModel = ref<any>(null)
const loading = ref(false)

const form = ref({
  name: '',
  provider: 'openai',
  api_key: '',
  base_url: '',
  model_name: '',
  temperature: 0.7,
  max_tokens: 2000,
})

const providers = [
  { label: 'OpenAI', value: 'openai' },
  { label: 'Claude', value: 'claude' },
  { label: '文心一言', value: 'wenxin' },
]

async function fetchModels() {
  if (!workspaceStore.currentWorkspace) return
  loading.value = true
  try {
    models.value = await listModels(workspaceStore.currentWorkspace.id) as any
  } finally {
    loading.value = false
  }
}

onMounted(fetchModels)

async function handleSubmit() {
  if (!form.value.name || !form.value.model_name) {
    ElMessage.warning('请填写模型名称和模型标识')
    return
  }
  if (!workspaceStore.currentWorkspace) return

  try {
    if (editingModel.value) {
      await updateModel(editingModel.value.id, {
        name: form.value.name,
        provider: form.value.provider,
        api_key: form.value.api_key || undefined,
        base_url: form.value.base_url || undefined,
        model_name: form.value.model_name,
        default_params: { temperature: form.value.temperature, max_tokens: form.value.max_tokens },
      })
      ElMessage.success('更新成功')
    } else {
      await createModel({
        workspace_id: workspaceStore.currentWorkspace.id,
        name: form.value.name,
        provider: form.value.provider,
        api_key: form.value.api_key || undefined,
        base_url: form.value.base_url || undefined,
        model_name: form.value.model_name,
        default_params: { temperature: form.value.temperature, max_tokens: form.value.max_tokens },
      })
      ElMessage.success('创建成功')
    }
    showCreate.value = false
    editingModel.value = null
    resetForm()
    await fetchModels()
  } catch {
    // handled by interceptor
  }
}

function resetForm() {
  form.value = { name: '', provider: 'openai', api_key: '', base_url: '', model_name: '', temperature: 0.7, max_tokens: 2000 }
}

function openEdit(model: any) {
  editingModel.value = model
  form.value = {
    name: model.name,
    provider: model.provider,
    api_key: '',
    base_url: model.base_url || '',
    model_name: model.model_name,
    temperature: model.default_params?.temperature || 0.7,
    max_tokens: model.default_params?.max_tokens || 2000,
  }
  showCreate.value = true
}

async function handleToggle(model: any) {
  await toggleModel(model.id)
  await fetchModels()
}

async function handleDelete(id: string) {
  await ElMessageBox.confirm('确定删除此模型配置？', '提示', { type: 'warning' })
  await deleteModel(id)
  ElMessage.success('已删除')
  await fetchModels()
}
</script>

<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
      <h3>AI 模型配置</h3>
      <el-button type="primary" @click="resetForm(); editingModel = null; showCreate = true">添加模型</el-button>
    </div>

    <el-table :data="models" v-loading="loading" style="width: 100%">
      <el-table-column prop="name" label="模型名称" />
      <el-table-column prop="provider" label="提供商" width="120" />
      <el-table-column prop="model_name" label="模型标识" width="180" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-switch :model-value="row.is_active" @change="handleToggle(row)" />
        </template>
      </el-table-column>
      <el-table-column label="默认参数" width="200">
        <template #default="{ row }">
          <span v-if="row.default_params">
            T={{ row.default_params.temperature }}, Tokens={{ row.default_params.max_tokens }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showCreate" :title="editingModel ? '编辑模型' : '添加模型'" width="500px">
      <el-form label-width="100px">
        <el-form-item label="模型名称">
          <el-input v-model="form.name" placeholder="如：GPT-4o" />
        </el-form-item>
        <el-form-item label="提供商">
          <el-select v-model="form.provider">
            <el-option v-for="p in providers" :key="p.value" :label="p.label" :value="p.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="模型标识">
          <el-input v-model="form.model_name" placeholder="如：gpt-4o" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="form.api_key" type="password" placeholder="模拟模式下可留空" show-password />
        </el-form-item>
        <el-form-item label="Base URL">
          <el-input v-model="form.base_url" placeholder="可选，自定义 API 地址" />
        </el-form-item>
        <el-form-item label="Temperature">
          <el-input-number v-model="form.temperature" :min="0" :max="2" :step="0.1" />
        </el-form-item>
        <el-form-item label="Max Tokens">
          <el-input-number v-model="form.max_tokens" :min="100" :max="8000" :step="100" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">{{ editingModel ? '保存' : '创建' }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>
```

- [ ] **Step 3: Update router**

Add model route:
```typescript
{
  path: 'models',
  component: () => import('@/views/models/ModelList.vue'),
  meta: { title: 'AI 模型' },
},
```

- [ ] **Step 4: Update MainLayout menu**

```vue
<el-menu-item index="/models">
  <el-icon><Cpu /></el-icon>
  <template #title>AI 模型</template>
</el-menu-item>
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/
git commit -m "feat: frontend AI model configuration page"
```

---

## Task 4: Frontend — Content Pages

**Files:**
- Create: `frontend/src/api/contents.ts`
- Create: `frontend/src/views/contents/ContentList.vue`
- Create: `frontend/src/views/contents/ContentCreate.vue`
- Create: `frontend/src/views/contents/ContentDetail.vue`
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/layouts/MainLayout.vue`

- [ ] **Step 1: Create content API**

`frontend/src/api/contents.ts`:
```typescript
import request from './request'

export function listContents(params: {
  workspace_id: string
  status?: string
  page?: number
  page_size?: number
}) {
  return request.get('/contents', { params })
}

export function generateContent(data: {
  workspace_id: string
  prompt_id: string
  model_id: string
  variables?: Record<string, string>
}) {
  return request.post('/contents/generate', data)
}

export function getContent(id: string) {
  return request.get(`/contents/${id}`)
}

export function updateContent(id: string, data: { edited_text?: string }) {
  return request.put(`/contents/${id}`, data)
}

export function deleteContent(id: string) {
  return request.delete(`/contents/${id}`)
}
```

- [ ] **Step 2: Create ContentList.vue**

`frontend/src/views/contents/ContentList.vue`:
```vue
<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkspaceStore } from '@/stores/workspace'
import { listContents, deleteContent } from '@/api/contents'
import { ElMessage, ElMessageBox } from 'element-plus'

const workspaceStore = useWorkspaceStore()
const router = useRouter()
const contents = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const status = ref('')
const loading = ref(false)

const statusMap: Record<string, { label: string; type: string }> = {
  draft: { label: '草稿', type: 'info' },
  pending_review: { label: '待审核', type: 'warning' },
  approved: { label: '已通过', type: 'success' },
  rejected: { label: '已驳回', type: 'danger' },
}

async function fetchContents() {
  if (!workspaceStore.currentWorkspace) return
  loading.value = true
  try {
    const data: any = await listContents({
      workspace_id: workspaceStore.currentWorkspace.id,
      status: status.value || undefined,
      page: page.value,
    })
    contents.value = data.data.items
    total.value = data.data.total
  } finally {
    loading.value = false
  }
}

onMounted(fetchContents)
watch([page, status], fetchContents)

async function handleDelete(id: string) {
  await ElMessageBox.confirm('确定删除？', '提示', { type: 'warning' })
  await deleteContent(id)
  ElMessage.success('已删除')
  await fetchContents()
}

function truncate(text: string, len: number) {
  return text?.length > len ? text.slice(0, len) + '...' : text
}
</script>

<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
      <h3>内容管理</h3>
      <el-button type="primary" @click="router.push('/contents/create')">生成内容</el-button>
    </div>

    <div style="display: flex; gap: 12px; margin-bottom: 16px;">
      <el-select v-model="status" placeholder="状态筛选" clearable>
        <el-option label="草稿" value="draft" />
        <el-option label="待审核" value="pending_review" />
        <el-option label="已通过" value="approved" />
        <el-option label="已驳回" value="rejected" />
      </el-select>
    </div>

    <el-table :data="contents" v-loading="loading" style="width: 100%">
      <el-table-column label="内容预览" min-width="300">
        <template #default="{ row }">
          <span>{{ truncate(row.edited_text || row.generated_text, 80) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusMap[row.status]?.type as any">{{ statusMap[row.status]?.label }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="token_usage" label="Token" width="80" />
      <el-table-column label="生成时间" width="120">
        <template #default="{ row }">
          {{ row.generation_time_ms }}ms
        </template>
      </el-table-column>
      <el-table-column label="创建时间" width="180">
        <template #default="{ row }">
          {{ new Date(row.created_at).toLocaleString() }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button size="small" @click="router.push(`/contents/${row.id}`)">查看</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div style="margin-top: 16px; display: flex; justify-content: flex-end;">
      <el-pagination v-model:current-page="page" :page-size="20" :total="total" layout="prev, pager, next" />
    </div>
  </div>
</template>
```

- [ ] **Step 3: Create ContentCreate.vue (with streaming effect)**

`frontend/src/views/contents/ContentCreate.vue`:
```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkspaceStore } from '@/stores/workspace'
import { listPrompts } from '@/api/prompts'
import { listModels } from '@/api/aiModels'
import { generateContent } from '@/api/contents'
import { ElMessage } from 'element-plus'

const router = useRouter()
const workspaceStore = useWorkspaceStore()

const prompts = ref<any[]>([])
const models = ref<any[]>([])
const selectedPrompt = ref<any>(null)
const selectedModelId = ref('')
const variables = ref<Record<string, string>>({})
const generating = ref(false)
const resultText = ref('')
const showResult = ref(false)
const streamInterval = ref<number | null>(null)

onMounted(async () => {
  if (!workspaceStore.currentWorkspace) return
  const promptData: any = await listPrompts({ workspace_id: workspaceStore.currentWorkspace.id, page_size: 100 })
  prompts.value = promptData.data.items
  models.value = await listModels(workspaceStore.currentWorkspace.id) as any
})

function onPromptChange() {
  const prompt = prompts.value.find((p) => p.id === selectedPrompt.value)
  if (prompt) {
    variables.value = {}
    for (const v of prompt.variables || []) {
      variables.value[v.name] = ''
    }
  }
}

async function handleGenerate() {
  if (!selectedPrompt.value || !selectedModelId.value) {
    ElMessage.warning('请选择 Prompt 和模型')
    return
  }
  if (!workspaceStore.currentWorkspace) return

  // Check required variables
  const prompt = prompts.value.find((p) => p.id === selectedPrompt.value)
  for (const v of prompt?.variables || []) {
    if (v.required && !variables.value[v.name]) {
      ElMessage.warning(`请填写变量 ${v.name}`)
      return
    }
  }

  generating.value = true
  showResult.value = true
  resultText.value = ''

  try {
    const data: any = await generateContent({
      workspace_id: workspaceStore.currentWorkspace.id,
      prompt_id: selectedPrompt.value,
      model_id: selectedModelId.value,
      variables: variables.value,
    })

    // Simulate streaming with setInterval
    const fullText = data.generated_text
    let index = 0
    streamInterval.value = window.setInterval(() => {
      if (index < fullText.length) {
        // Add 1-3 chars per tick for natural feel
        const charsToAdd = Math.floor(Math.random() * 3) + 1
        resultText.value += fullText.slice(index, index + charsToAdd)
        index += charsToAdd
      } else {
        if (streamInterval.value) clearInterval(streamInterval.value)
        generating.value = false
      }
    }, 30)
  } catch {
    generating.value = false
    showResult.value = false
  }
}

function handleCopy() {
  navigator.clipboard.writeText(resultText.value)
  ElMessage.success('已复制到剪贴板')
}
</script>

<template>
  <div>
    <h3>生成内容</h3>
    <el-form label-width="100px" style="max-width: 800px; margin-top: 16px;">
      <el-form-item label="Prompt 模板">
        <el-select v-model="selectedPrompt" placeholder="选择 Prompt" @change="onPromptChange" style="width: 100%;">
          <el-option v-for="p in prompts" :key="p.id" :label="p.title" :value="p.id" />
        </el-select>
      </el-form-item>

      <el-form-item label="AI 模型">
        <el-select v-model="selectedModelId" placeholder="选择模型" style="width: 100%;">
          <el-option v-for="m in models" :key="m.id" :label="`${m.name} (${m.model_name})`" :value="m.id" :disabled="!m.is_active" />
        </el-select>
      </el-form-item>

      <el-form-item v-for="(val, key) in variables" :key="key" :label="key as string">
        <el-input v-model="variables[key]" :placeholder="`请输入 ${key}`" />
      </el-form-item>

      <el-form-item>
        <el-button type="primary" :loading="generating" @click="handleGenerate">生成</el-button>
        <el-button @click="router.push('/contents')">返回列表</el-button>
      </el-form-item>
    </el-form>

    <div v-if="showResult" style="margin-top: 24px; max-width: 800px;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <h4>生成结果</h4>
        <el-button size="small" @click="handleCopy" :disabled="generating">复制</el-button>
      </div>
      <el-input type="textarea" :model-value="resultText" :rows="15" readonly />
    </div>
  </div>
</template>
```

- [ ] **Step 4: Create ContentDetail.vue**

`frontend/src/views/contents/ContentDetail.vue`:
```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getContent, updateContent } from '@/api/contents'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const content = ref<any>(null)
const editText = ref('')
const editing = ref(false)

onMounted(async () => {
  content.value = await getContent(route.params.id as string)
  editText.value = content.value.edited_text || content.value.generated_text
})

async function handleSave() {
  await updateContent(content.value.id, { edited_text: editText.value })
  ElMessage.success('保存成功')
  editing.value = false
  content.value = await getContent(route.params.id as string)
}

function handleCopy() {
  navigator.clipboard.writeText(editText.value)
  ElMessage.success('已复制到剪贴板')
}
</script>

<template>
  <div v-if="content">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
      <h3>内容详情</h3>
      <div>
        <el-button @click="handleCopy">复制</el-button>
        <el-button v-if="!editing" @click="editing = true">编辑</el-button>
        <el-button v-if="editing" type="primary" @click="handleSave">保存</el-button>
        <el-button @click="router.push('/contents')">返回列表</el-button>
      </div>
    </div>

    <el-descriptions :column="2" border style="margin-bottom: 16px;">
      <el-descriptions-item label="状态">{{ content.status }}</el-descriptions-item>
      <el-descriptions-item label="Token 消耗">{{ content.token_usage }}</el-descriptions-item>
      <el-descriptions-item label="生成耗时">{{ content.generation_time_ms }}ms</el-descriptions-item>
      <el-descriptions-item label="创建时间">{{ new Date(content.created_at).toLocaleString() }}</el-descriptions-item>
    </el-descriptions>

    <el-input v-model="editText" type="textarea" :rows="15" :readonly="!editing" />
  </div>
</template>
```

- [ ] **Step 5: Update router**

Add content routes:
```typescript
{
  path: 'contents',
  component: () => import('@/views/contents/ContentList.vue'),
  meta: { title: '内容管理' },
},
{
  path: 'contents/create',
  component: () => import('@/views/contents/ContentCreate.vue'),
  meta: { title: '生成内容' },
},
{
  path: 'contents/:id',
  component: () => import('@/views/contents/ContentDetail.vue'),
  meta: { title: '内容详情' },
},
```

- [ ] **Step 6: Update MainLayout menu**

```vue
<el-menu-item index="/contents">
  <el-icon><EditPen /></el-icon>
  <template #title>内容管理</template>
</el-menu-item>
```

- [ ] **Step 7: Verify full flow**

```bash
docker compose up -d
# Login → Create workspace → Add AI model → Create prompt with {{variables}}
# Go to Contents → Generate → Select prompt → Fill variables → Select model → Generate
# Should see streaming text appear character by character
# View detail → Edit → Save
```

- [ ] **Step 8: Commit**

```bash
git add frontend/src/
git commit -m "feat: frontend content pages — list, generate with streaming, detail/edit"
```

---

## Plan 3 Complete

After this plan, you have:
- AI model CRUD with toggle active/inactive
- Mock content generation with simulated metrics
- Frontend streaming effect (character-by-character)
- Content list with status filter and pagination
- Content create flow: select prompt → fill variables → pick model → generate
- Content detail with edit capability

**Next: Plan 4 — Review Workflow + Dashboard + Export**
