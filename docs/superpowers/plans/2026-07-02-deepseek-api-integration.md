# DeepSeek API Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace mock AI content generation with real DeepSeek API calls and true SSE streaming.

**Architecture:** Backend uses `openai` Python SDK (DeepSeek is OpenAI-compatible) with `AsyncOpenAI`. API key resolves via per-model config → global `DEEPSEEK_API_KEY` env var. New `POST /contents/generate-stream` SSE endpoint streams chunks to frontend, which consumes via `fetch` + `ReadableStream`.

**Tech Stack:** Python 3.11+, FastAPI, openai SDK, Vue 3, TypeScript

---

### Task 1: Add DEEPSEEK_API_KEY config

**Files:**
- Modify: `backend/app/core/config.py`
- Modify: `backend/.env.example`

- [ ] **Step 1: Add DEEPSEEK_API_KEY to Settings class**

```python
# backend/app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/ai_content_studio"
    SECRET_KEY: str = ""  # Must be set via .env
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    CORS_ORIGINS: str = "http://localhost"
    DEEPSEEK_API_KEY: str = ""  # Global fallback API key for DeepSeek


settings = Settings()

if not settings.SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set. Please configure it in backend/.env")
```

- [ ] **Step 2: Add DEEPSEEK_API_KEY to .env.example**

```
# backend/.env.example — append this line at the end:
DEEPSEEK_API_KEY=
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/core/config.py backend/.env.example
git commit -m "feat: add DEEPSEEK_API_KEY config setting"
```

---

### Task 2: Add openai dependency

**Files:**
- Modify: `backend/pyproject.toml`

- [ ] **Step 1: Add openai to dependencies**

```toml
# backend/pyproject.toml — add "openai>=1.0.0" to the dependencies list
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "sqlalchemy[asyncio]>=2.0.0",
    "asyncpg>=0.30.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "bcrypt>=4.0.0,<5.0.0",
    "python-multipart>=0.0.9",
    "alembic>=1.14.0",
    "slowapi>=0.1.9",
    "openai>=1.0.0",
]
```

- [ ] **Step 2: Install the new dependency locally to verify**

Run: `pip install openai>=1.0.0`
Expected: Package installs successfully

- [ ] **Step 3: Commit**

```bash
git add backend/pyproject.toml
git commit -m "feat: add openai SDK dependency for DeepSeek API"
```

---

### Task 3: Rewrite ai_service.py — mock → real DeepSeek API

**Files:**
- Modify: `backend/app/services/ai_service.py`

- [ ] **Step 1: Replace entire file content**

```python
import time

from openai import AsyncOpenAI

from app.core.config import settings


def _build_model_config(model) -> dict:
    return {
        "api_key": model.api_key or settings.DEEPSEEK_API_KEY,
        "base_url": model.base_url or "https://api.deepseek.com",
        "model_name": model.model_name,
        "default_params": model.default_params or {},
    }


def _build_prompt_text(prompt_content: str, variables: dict | None) -> str:
    text = prompt_content
    for key, value in (variables or {}).items():
        text = text.replace(f"{{{key}}}", str(value))
    return text


async def deepseek_generate(prompt_text: str, model) -> dict:
    """Non-streaming generation. Returns dict with generated_text, token_usage, generation_time_ms."""
    api_key = model.api_key or settings.DEEPSEEK_API_KEY
    if not api_key:
        raise ValueError("未配置 DeepSeek API Key，请在模型配置或环境变量中设置")

    client = AsyncOpenAI(
        api_key=api_key,
        base_url=model.base_url or "https://api.deepseek.com",
    )

    start_time = time.time()
    response = await client.chat.completions.create(
        model=model.model_name,
        messages=[{"role": "user", "content": prompt_text}],
        **(model.default_params or {}),
    )
    elapsed_ms = int((time.time() - start_time) * 1000)

    return {
        "generated_text": response.choices[0].message.content or "",
        "token_usage": response.usage.total_tokens if response.usage else 0,
        "generation_time_ms": elapsed_ms,
    }


async def deepseek_generate_stream(prompt_text: str, model):
    """Streaming generation. Yields text chunks as they arrive."""
    api_key = model.api_key or settings.DEEPSEEK_API_KEY
    if not api_key:
        raise ValueError("未配置 DeepSeek API Key，请在模型配置或环境变量中设置")

    client = AsyncOpenAI(
        api_key=api_key,
        base_url=model.base_url or "https://api.deepseek.com",
    )

    stream = await client.chat.completions.create(
        model=model.model_name,
        messages=[{"role": "user", "content": prompt_text}],
        stream=True,
        **(model.default_params or {}),
    )

    async for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/services/ai_service.py
git commit -m "feat: replace mock AI with real DeepSeek API using openai SDK"
```

---

### Task 4: Update content_service.py — use real API + add streaming

**Files:**
- Modify: `backend/app/services/content_service.py`

- [ ] **Step 1: Replace entire file content**

```python
import time
import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content, ContentStatus
from app.models.prompt import Prompt
from app.models.ai_model import AIModel
from app.schemas.content import ContentGenerate, ContentUpdate
from app.services import ai_service


async def generate_content(db: AsyncSession, user_id: uuid.UUID, req: ContentGenerate) -> Content:
    prompt_result = await db.execute(select(Prompt).where(Prompt.id == req.prompt_id))
    prompt = prompt_result.scalar_one_or_none()
    if not prompt:
        raise ValueError("Prompt not found")

    model_result = await db.execute(select(AIModel).where(AIModel.id == req.model_id))
    model = model_result.scalar_one_or_none()
    if not model:
        raise ValueError("Model not found")

    prompt_text = ai_service._build_prompt_text(prompt.content, req.variables)
    ai_result = await ai_service.deepseek_generate(prompt_text, model)

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


async def generate_content_stream(db: AsyncSession, user_id: uuid.UUID, req: ContentGenerate):
    prompt_result = await db.execute(select(Prompt).where(Prompt.id == req.prompt_id))
    prompt = prompt_result.scalar_one_or_none()
    if not prompt:
        raise ValueError("Prompt not found")

    model_result = await db.execute(select(AIModel).where(AIModel.id == req.model_id))
    model = model_result.scalar_one_or_none()
    if not model:
        raise ValueError("Model not found")

    prompt_text = ai_service._build_prompt_text(prompt.content, req.variables)

    start_time = time.time()
    full_text = ""

    async for chunk in ai_service.deepseek_generate_stream(prompt_text, model):
        full_text += chunk
        yield chunk

    # Save generated content to DB after stream completes
    generation_time_ms = int((time.time() - start_time) * 1000)
    content = Content(
        workspace_id=req.workspace_id,
        prompt_id=req.prompt_id,
        model_id=req.model_id,
        variables_used=req.variables or {},
        generated_text=full_text,
        status=ContentStatus.DRAFT,
        token_usage=0,
        generation_time_ms=generation_time_ms,
        created_by=user_id,
    )
    db.add(content)
    await db.flush()


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
    await db.refresh(content)
    return content


async def delete_content(db: AsyncSession, content_id: uuid.UUID) -> None:
    content = await get_content(db, content_id)
    if not content:
        raise ValueError("Content not found")
    await db.delete(content)
    await db.flush()
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/services/content_service.py
git commit -m "feat: add streaming content generation with DeepSeek API"
```

---

### Task 5: Add SSE streaming endpoint

**Files:**
- Modify: `backend/app/api/v1/contents.py`

- [ ] **Step 1: Add import and streaming endpoint**

Add `StreamingResponse` to the FastAPI imports and add the new endpoint after the existing `/generate` endpoint. The full file becomes:

```python
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
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


@router.post("/generate-stream")
async def generate_content_stream(
    req: ContentGenerate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await workspace_service.check_workspace_access(db, req.workspace_id, current_user.id)
    if not member or member.role.value == "viewer":
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    try:
        return StreamingResponse(
            content_service.generate_content_stream(db, current_user.id, req),
            media_type="text/plain",
            headers={"X-Accel-Buffering": "no"},
        )
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

- [ ] **Step 2: Commit**

```bash
git add backend/app/api/v1/contents.py
git commit -m "feat: add SSE streaming endpoint for content generation"
```

---

### Task 6: Add streaming API function to frontend

**Files:**
- Modify: `frontend/src/api/contents.ts`

- [ ] **Step 1: Add generateContentStream function**

```typescript
// frontend/src/api/contents.ts
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

export async function generateContentStream(
  data: {
    workspace_id: string
    prompt_id: string
    model_id: string
    variables?: Record<string, string>
  },
  onChunk: (text: string) => void,
  onDone: () => void,
  onError: (error: string) => void,
) {
  const token = localStorage.getItem('access_token')
  try {
    const response = await fetch('/api/v1/contents/generate-stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: '生成失败' }))
      onError(err.detail || '生成失败')
      return
    }

    const reader = response.body!.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      onChunk(decoder.decode(value, { stream: true }))
    }
    onDone()
  } catch {
    onError('网络请求失败')
  }
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

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api/contents.ts
git commit -m "feat: add streaming content generation API function"
```

---

### Task 7: Update ContentCreate.vue — real SSE streaming

**Files:**
- Modify: `frontend/src/views/contents/ContentCreate.vue`

- [ ] **Step 1: Replace the script section to use real streaming**

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkspaceStore } from '@/stores/workspace'
import { listPrompts } from '@/api/prompts'
import { listModels } from '@/api/aiModels'
import { generateContentStream } from '@/api/contents'
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

  await generateContentStream(
    {
      workspace_id: workspaceStore.currentWorkspace.id,
      prompt_id: selectedPrompt.value,
      model_id: selectedModelId.value,
      variables: variables.value,
    },
    (chunk: string) => {
      resultText.value += chunk
    },
    () => {
      generating.value = false
    },
    (error: string) => {
      ElMessage.error(error)
      generating.value = false
      showResult.value = false
    },
  )
}

function handleCopy() {
  navigator.clipboard.writeText(resultText.value)
  ElMessage.success('已复制到剪贴板')
}
</script>
```

The `<template>` section remains unchanged.

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/contents/ContentCreate.vue
git commit -m "feat: replace simulated typing with real SSE streaming"
```

---

### Task 8: Install openai in Docker image

**Files:**
- Modify: `backend/Dockerfile`

- [ ] **Step 1: Verify Dockerfile picks up the new dependency**

The current Dockerfile runs `uv pip install --system --no-cache ".[dev]"` which reads `pyproject.toml` dependencies. The new `openai` dependency added in Task 2 will be installed automatically. No Dockerfile change needed.

- [ ] **Step 2: Rebuild and verify**

```bash
docker compose build backend
docker compose up -d
curl http://localhost:8000/api/health
```

Expected: `{"status": "ok"}`

- [ ] **Step 3: Commit if any Dockerfile changes were needed**

No changes needed — skip commit.

---

### Post-Implementation Verification

- [ ] Rebuild Docker: `docker compose build backend && docker compose up -d`
- [ ] Check health: `curl http://localhost:8000/api/health`
- [ ] Configure a DeepSeek model in the UI with `provider=deepseek`, `model_name=deepseek-chat`, `base_url=https://api.deepseek.com`
- [ ] Test non-streaming: POST to `/api/v1/contents/generate`
- [ ] Test streaming: POST to `/api/v1/contents/generate-stream`
- [ ] Verify content is saved to DB after streaming completes
- [ ] Verify frontend shows streaming text in real-time
