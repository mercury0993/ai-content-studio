# AI Content Studio — Plan 4: Review Workflow + Dashboard + Export

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add content review workflow (submit/approve/reject/batch), data dashboard with ECharts, and content export (Markdown/ZIP).

**Architecture:** Reviews extend the Content status machine. Dashboard queries aggregate data from contents/audit_logs tables. Export generates Markdown files or ZIP archives.

**Tech Stack:** Same as previous plans + ECharts (already in frontend dependencies)

**Prerequisite:** Plan 1 + Plan 2 + Plan 3 completed

---

## Task 1: Review Backend — Audit Log Model + Review Service + API

**Files:**
- Create: `backend/app/models/audit_log.py`
- Create: `backend/app/schemas/review.py`
- Create: `backend/app/services/review_service.py`
- Create: `backend/app/api/v1/reviews.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Create AuditLog model**

`backend/app/models/audit_log.py`:
```python
import uuid

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 2: Update models/__init__.py**

```python
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.models.prompt import Prompt, PromptVersion
from app.models.ai_model import AIModel
from app.models.content import Content, ContentStatus
from app.models.audit_log import AuditLog

__all__ = ["User", "Workspace", "WorkspaceMember", "Prompt", "PromptVersion", "AIModel", "Content", "ContentStatus", "AuditLog"]
```

- [ ] **Step 3: Create review schemas**

`backend/app/schemas/review.py`:
```python
import uuid
from datetime import datetime
from pydantic import BaseModel


class ReviewSubmit(BaseModel):
    reviewer_id: uuid.UUID


class ReviewAction(BaseModel):
    comment: str | None = None


class BatchReview(BaseModel):
    content_ids: list[uuid.UUID]
    action: str  # "approve" or "reject"
    comment: str | None = None


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    action: str
    resource_type: str
    resource_id: uuid.UUID
    details: dict | None
    created_at: datetime

    class Config:
        from_attributes = True
```

- [ ] **Step 4: Create review service**

`backend/app/services/review_service.py`:
```python
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content, ContentStatus
from app.models.audit_log import AuditLog


def _log_audit(db: AsyncSession, user_id: uuid.UUID, action: str, resource_type: str, resource_id: uuid.UUID, details: dict | None = None):
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
    )
    db.add(log)


async def submit_for_review(db: AsyncSession, content_id: uuid.UUID, reviewer_id: uuid.UUID, user_id: uuid.UUID) -> Content:
    result = await db.execute(select(Content).where(Content.id == content_id))
    content = result.scalar_one_or_none()
    if not content:
        raise ValueError("Content not found")
    if content.status not in (ContentStatus.DRAFT, ContentStatus.REJECTED):
        raise ValueError(f"Cannot submit content with status '{content.status}'")

    old_status = content.status.value
    content.status = ContentStatus.PENDING_REVIEW
    content.reviewed_by = reviewer_id
    content.review_comment = None
    await db.flush()

    _log_audit(db, user_id, "content.submit", "content", content_id, {"from": old_status, "to": "pending_review"})
    await db.flush()
    return content


async def approve_content(db: AsyncSession, content_id: uuid.UUID, reviewer_id: uuid.UUID, comment: str | None = None) -> Content:
    result = await db.execute(select(Content).where(Content.id == content_id))
    content = result.scalar_one_or_none()
    if not content:
        raise ValueError("Content not found")
    if content.status != ContentStatus.PENDING_REVIEW:
        raise ValueError("Content is not pending review")

    content.status = ContentStatus.APPROVED
    content.reviewed_by = reviewer_id
    content.review_comment = comment
    content.reviewed_at = datetime.now(timezone.utc)
    await db.flush()

    _log_audit(db, reviewer_id, "content.approve", "content", content_id, {"comment": comment})
    await db.flush()
    return content


async def reject_content(db: AsyncSession, content_id: uuid.UUID, reviewer_id: uuid.UUID, comment: str | None = None) -> Content:
    result = await db.execute(select(Content).where(Content.id == content_id))
    content = result.scalar_one_or_none()
    if not content:
        raise ValueError("Content not found")
    if content.status != ContentStatus.PENDING_REVIEW:
        raise ValueError("Content is not pending review")
    if not comment:
        raise ValueError("Rejection requires a comment")

    content.status = ContentStatus.REJECTED
    content.reviewed_by = reviewer_id
    content.review_comment = comment
    content.reviewed_at = datetime.now(timezone.utc)
    await db.flush()

    _log_audit(db, reviewer_id, "content.reject", "content", content_id, {"comment": comment})
    await db.flush()
    return content


async def batch_review(db: AsyncSession, content_ids: list[uuid.UUID], action: str, reviewer_id: uuid.UUID, comment: str | None = None) -> int:
    count = 0
    for cid in content_ids:
        try:
            if action == "approve":
                await approve_content(db, cid, reviewer_id, comment)
            elif action == "reject":
                await reject_content(db, cid, reviewer_id, comment)
            count += 1
        except ValueError:
            continue
    return count


async def list_reviews(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Content], int]:
    query = select(Content).where(Content.workspace_id == workspace_id)
    if status:
        query = query.where(Content.status == ContentStatus(status))
    else:
        # Default: show pending_review
        query = query.where(Content.status == ContentStatus.PENDING_REVIEW)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    query = query.order_by(Content.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return list(result.scalars().all()), total
```

- [ ] **Step 5: Create review router**

`backend/app/api/v1/reviews.py`:
```python
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.content import ContentResponse
from app.schemas.review import ReviewSubmit, ReviewAction, BatchReview
from app.services import review_service, workspace_service

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("", response_model=dict)
async def list_reviews(
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
    items, total = await review_service.list_reviews(db, workspace_id, status, page, page_size)
    return {
        "code": 0,
        "data": {
            "items": [ContentResponse.model_validate(c) for c in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.post("/{content_id}/submit", response_model=ContentResponse)
async def submit_for_review(
    content_id: uuid.UUID,
    req: ReviewSubmit,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await review_service.submit_for_review(db, content_id, req.reviewer_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{content_id}/approve", response_model=ContentResponse)
async def approve(
    content_id: uuid.UUID,
    req: ReviewAction,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role.value == "viewer":
        raise HTTPException(status_code=403, detail="Viewers cannot review")
    try:
        return await review_service.approve_content(db, content_id, current_user.id, req.comment)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{content_id}/reject", response_model=ContentResponse)
async def reject(
    content_id: uuid.UUID,
    req: ReviewAction,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role.value == "viewer":
        raise HTTPException(status_code=403, detail="Viewers cannot review")
    try:
        return await review_service.reject_content(db, content_id, current_user.id, req.comment)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batch")
async def batch_review(
    req: BatchReview,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role.value == "viewer":
        raise HTTPException(status_code=403, detail="Viewers cannot review")
    count = await review_service.batch_review(db, req.content_ids, req.action, current_user.id, req.comment)
    return {"code": 0, "message": f"Reviewed {count} items", "data": {"count": count}}
```

- [ ] **Step 6: Register router in main.py**

```python
from app.api.v1.reviews import router as reviews_router
app.include_router(reviews_router, prefix="/api/v1")
```

- [ ] **Step 7: Generate migration and restart**

```bash
cd E:/lx/projects/ai-content-studio/backend
alembic revision --autogenerate -m "add audit_logs table"
docker compose restart backend
```

- [ ] **Step 8: Commit**

```bash
git add backend/
git commit -m "feat: review workflow — submit, approve, reject, batch + audit logs"
```

---

## Task 2: Dashboard Backend

**Files:**
- Create: `backend/app/services/dashboard_service.py`
- Create: `backend/app/api/v1/dashboard.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Create dashboard service**

`backend/app/services/dashboard_service.py`:
```python
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content, ContentStatus
from app.models.prompt import Prompt
from app.models.ai_model import AIModel
from app.models.user import User


async def get_stats(db: AsyncSession, workspace_id: uuid.UUID) -> dict:
    prompt_count = (await db.execute(
        select(func.count()).where(Prompt.workspace_id == workspace_id)
    )).scalar()

    content_count = (await db.execute(
        select(func.count()).where(Content.workspace_id == workspace_id)
    )).scalar()

    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_generated = (await db.execute(
        select(func.count()).where(
            Content.workspace_id == workspace_id,
            Content.created_at >= month_start,
        )
    )).scalar()

    pending_review = (await db.execute(
        select(func.count()).where(
            Content.workspace_id == workspace_id,
            Content.status == ContentStatus.PENDING_REVIEW,
        )
    )).scalar()

    return {
        "prompt_count": prompt_count,
        "content_count": content_count,
        "monthly_generated": monthly_generated,
        "pending_review": pending_review,
    }


async def get_trend(db: AsyncSession, workspace_id: uuid.UUID, days: int = 30) -> list[dict]:
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)

    result = await db.execute(
        select(
            cast(Content.created_at, Date).label("date"),
            func.count().label("count"),
        )
        .where(
            Content.workspace_id == workspace_id,
            Content.created_at >= start,
        )
        .group_by(cast(Content.created_at, Date))
        .order_by(cast(Content.created_at, Date))
    )

    # Fill in missing dates
    data_map = {str(row.date): row.count for row in result.all()}
    trend = []
    for i in range(days):
        d = (start + timedelta(days=i)).strftime("%Y-%m-%d")
        trend.append({"date": d, "count": data_map.get(d, 0)})
    return trend


async def get_model_usage(db: AsyncSession, workspace_id: uuid.UUID) -> list[dict]:
    result = await db.execute(
        select(
            AIModel.name,
            func.count(Content.id).label("count"),
        )
        .outerjoin(Content, Content.model_id == AIModel.id)
        .where(AIModel.workspace_id == workspace_id)
        .group_by(AIModel.name)
    )
    return [{"name": row.name, "count": row.count} for row in result.all()]


async def get_user_ranking(db: AsyncSession, workspace_id: uuid.UUID, limit: int = 10) -> list[dict]:
    result = await db.execute(
        select(
            User.username,
            func.count(Content.id).label("count"),
        )
        .outerjoin(Content, Content.created_by == User.id)
        .where(Content.workspace_id == workspace_id)
        .group_by(User.username)
        .order_by(func.count(Content.id).desc())
        .limit(limit)
    )
    return [{"username": row.username, "count": row.count} for row in result.all()]


async def get_recent(db: AsyncSession, workspace_id: uuid.UUID, limit: int = 10) -> list[Content]:
    result = await db.execute(
        select(Content)
        .where(Content.workspace_id == workspace_id)
        .order_by(Content.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
```

- [ ] **Step 2: Create dashboard router**

`backend/app/api/v1/dashboard.py`:
```python
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.content import ContentResponse
from app.services import dashboard_service, workspace_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
async def stats(
    workspace_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await workspace_service.check_workspace_access(db, workspace_id, current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Not a member")
    data = await dashboard_service.get_stats(db, workspace_id)
    return {"code": 0, "data": data}


@router.get("/trend")
async def trend(
    workspace_id: uuid.UUID,
    days: int = Query(30, ge=7, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await workspace_service.check_workspace_access(db, workspace_id, current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Not a member")
    data = await dashboard_service.get_trend(db, workspace_id, days)
    return {"code": 0, "data": data}


@router.get("/model-usage")
async def model_usage(
    workspace_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await workspace_service.check_workspace_access(db, workspace_id, current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Not a member")
    data = await dashboard_service.get_model_usage(db, workspace_id)
    return {"code": 0, "data": data}


@router.get("/user-ranking")
async def user_ranking(
    workspace_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await workspace_service.check_workspace_access(db, workspace_id, current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Not a member")
    data = await dashboard_service.get_user_ranking(db, workspace_id)
    return {"code": 0, "data": data}


@router.get("/recent")
async def recent(
    workspace_id: uuid.UUID,
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await workspace_service.check_workspace_access(db, workspace_id, current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Not a member")
    items = await dashboard_service.get_recent(db, workspace_id, limit)
    return {"code": 0, "data": [ContentResponse.model_validate(c) for c in items]}
```

- [ ] **Step 3: Register router in main.py**

```python
from app.api.v1.dashboard import router as dashboard_router
app.include_router(dashboard_router, prefix="/api/v1")
```

- [ ] **Step 4: Commit**

```bash
git add backend/
git commit -m "feat: dashboard API — stats, trend, model usage, user ranking"
```

---

## Task 3: Frontend — Review Pages

**Files:**
- Create: `frontend/src/api/reviews.ts`
- Create: `frontend/src/views/reviews/ReviewCenter.vue`
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/layouts/MainLayout.vue`

- [ ] **Step 1: Create review API**

`frontend/src/api/reviews.ts`:
```typescript
import request from './request'

export function listReviews(params: {
  workspace_id: string
  status?: string
  page?: number
  page_size?: number
}) {
  return request.get('/reviews', { params })
}

export function submitForReview(contentId: string, reviewerId: string) {
  return request.post(`/reviews/${contentId}/submit`, { reviewer_id: reviewerId })
}

export function approveContent(contentId: string, comment?: string) {
  return request.post(`/reviews/${contentId}/approve`, { comment })
}

export function rejectContent(contentId: string, comment: string) {
  return request.post(`/reviews/${contentId}/reject`, { comment })
}

export function batchReview(contentIds: string[], action: string, comment?: string) {
  return request.post('/reviews/batch', { content_ids: contentIds, action, comment })
}
```

- [ ] **Step 2: Create ReviewCenter.vue**

`frontend/src/views/reviews/ReviewCenter.vue`:
```vue
<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useWorkspaceStore } from '@/stores/workspace'
import { listReviews, approveContent, rejectContent, batchReview } from '@/api/reviews'
import { listMembers } from '@/api/workspaces'
import { submitForReview } from '@/api/reviews'
import { ElMessage, ElMessageBox } from 'element-plus'

const workspaceStore = useWorkspaceStore()
const reviews = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const statusFilter = ref('')
const loading = ref(false)
const selectedIds = ref<string[]>([])
const showSubmitDialog = ref(false)
const showRejectDialog = ref(false)
const members = ref<any[]>([])
const submitForm = ref({ content_id: '', reviewer_id: '' })
const rejectForm = ref({ content_id: '', comment: '' })

const statusMap: Record<string, { label: string; type: string }> = {
  draft: { label: '草稿', type: 'info' },
  pending_review: { label: '待审核', type: 'warning' },
  approved: { label: '已通过', type: 'success' },
  rejected: { label: '已驳回', type: 'danger' },
}

async function fetchReviews() {
  if (!workspaceStore.currentWorkspace) return
  loading.value = true
  try {
    const data: any = await listReviews({
      workspace_id: workspaceStore.currentWorkspace.id,
      status: statusFilter.value || undefined,
      page: page.value,
    })
    reviews.value = data.data.items
    total.value = data.data.total
  } finally {
    loading.value = false
  }
}

async function fetchMembers() {
  if (!workspaceStore.currentWorkspace) return
  members.value = await listMembers(workspaceStore.currentWorkspace.id) as any
}

onMounted(() => {
  fetchReviews()
  fetchMembers()
})
watch([page, statusFilter], fetchReviews)

async function handleApprove(id: string) {
  await approveContent(id)
  ElMessage.success('已通过')
  await fetchReviews()
}

function openReject(id: string) {
  rejectForm.value = { content_id: id, comment: '' }
  showRejectDialog.value = true
}

async function handleReject() {
  if (!rejectForm.value.comment) {
    ElMessage.warning('请填写驳回理由')
    return
  }
  await rejectContent(rejectForm.value.content_id, rejectForm.value.comment)
  ElMessage.success('已驳回')
  showRejectDialog.value = false
  await fetchReviews()
}

function openSubmit(id: string) {
  submitForm.value = { content_id: id, reviewer_id: '' }
  showSubmitDialog.value = true
}

async function handleSubmitForReview() {
  if (!submitForm.value.reviewer_id) {
    ElMessage.warning('请选择审核人')
    return
  }
  await submitForReview(submitForm.value.content_id, submitForm.value.reviewer_id)
  ElMessage.success('已提交审核')
  showSubmitDialog.value = false
  await fetchReviews()
}

async function handleBatch(action: string) {
  if (selectedIds.value.length === 0) {
    ElMessage.warning('请选择要审核的内容')
    return
  }
  if (action === 'reject') {
    const { value } = await ElMessageBox.prompt('请输入驳回理由', '批量驳回', { inputType: 'textarea' })
    await batchReview(selectedIds.value, 'reject', value)
  } else {
    await batchReview(selectedIds.value, 'approve')
  }
  ElMessage.success('批量操作成功')
  selectedIds.value = []
  await fetchReviews()
}

function handleSelectionChange(rows: any[]) {
  selectedIds.value = rows.map((r: any) => r.id)
}

function truncate(text: string, len: number) {
  return text?.length > len ? text.slice(0, len) + '...' : text
}
</script>

<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
      <h3>审核中心</h3>
      <div>
        <el-button @click="handleBatch('approve')" :disabled="selectedIds.length === 0">批量通过</el-button>
        <el-button type="danger" @click="handleBatch('reject')" :disabled="selectedIds.length === 0">批量驳回</el-button>
      </div>
    </div>

    <el-select v-model="statusFilter" placeholder="状态筛选" clearable style="margin-bottom: 16px;">
      <el-option label="待审核" value="pending_review" />
      <el-option label="已通过" value="approved" />
      <el-option label="已驳回" value="rejected" />
      <el-option label="草稿" value="draft" />
    </el-select>

    <el-table :data="reviews" v-loading="loading" @selection-change="handleSelectionChange" style="width: 100%">
      <el-table-column type="selection" width="55" />
      <el-table-column label="内容预览" min-width="250">
        <template #default="{ row }">
          <span>{{ truncate(row.edited_text || row.generated_text, 60) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusMap[row.status]?.type as any">{{ statusMap[row.status]?.label }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="审核意见" width="200">
        <template #default="{ row }">
          <span v-if="row.review_comment">{{ row.review_comment }}</span>
          <span v-else style="color: #999;">—</span>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" width="180">
        <template #default="{ row }">
          {{ new Date(row.created_at).toLocaleString() }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="240">
        <template #default="{ row }">
          <template v-if="row.status === 'draft'">
            <el-button size="small" type="primary" @click="openSubmit(row.id)">提交审核</el-button>
          </template>
          <template v-if="row.status === 'pending_review'">
            <el-button size="small" type="success" @click="handleApprove(row.id)">通过</el-button>
            <el-button size="small" type="danger" @click="openReject(row.id)">驳回</el-button>
          </template>
        </template>
      </el-table-column>
    </el-table>

    <div style="margin-top: 16px; display: flex; justify-content: flex-end;">
      <el-pagination v-model:current-page="page" :page-size="20" :total="total" layout="prev, pager, next" />
    </div>

    <!-- Submit dialog -->
    <el-dialog v-model="showSubmitDialog" title="提交审核">
      <el-form>
        <el-form-item label="选择审核人">
          <el-select v-model="submitForm.reviewer_id" placeholder="选择审核人" style="width: 100%;">
            <el-option v-for="m in members" :key="m.user_id" :label="`${m.username} (${m.email})`" :value="m.user_id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSubmitDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitForReview">提交</el-button>
      </template>
    </el-dialog>

    <!-- Reject dialog -->
    <el-dialog v-model="showRejectDialog" title="驳回">
      <el-form>
        <el-form-item label="驳回理由">
          <el-input v-model="rejectForm.comment" type="textarea" :rows="3" placeholder="请输入驳回理由" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRejectDialog = false">取消</el-button>
        <el-button type="danger" @click="handleReject">驳回</el-button>
      </template>
    </el-dialog>
  </div>
</template>
```

- [ ] **Step 3: Update router**

```typescript
{
  path: 'reviews',
  component: () => import('@/views/reviews/ReviewCenter.vue'),
  meta: { title: '审核中心' },
},
```

- [ ] **Step 4: Update MainLayout menu**

```vue
<el-menu-item index="/reviews">
  <el-icon><Checked /></el-icon>
  <template #title>审核中心</template>
</el-menu-item>
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/
git commit -m "feat: frontend review center — submit, approve, reject, batch"
```

---

## Task 4: Frontend — Dashboard with ECharts

**Files:**
- Create: `frontend/src/api/dashboard.ts`
- Create: `frontend/src/views/Dashboard.vue` (replace placeholder)

- [ ] **Step 1: Create dashboard API**

`frontend/src/api/dashboard.ts`:
```typescript
import request from './request'

export function getStats(workspaceId: string) {
  return request.get('/dashboard/stats', { params: { workspace_id: workspaceId } })
}

export function getTrend(workspaceId: string, days: number = 30) {
  return request.get('/dashboard/trend', { params: { workspace_id: workspaceId, days } })
}

export function getModelUsage(workspaceId: string) {
  return request.get('/dashboard/model-usage', { params: { workspace_id: workspaceId } })
}

export function getUserRanking(workspaceId: string) {
  return request.get('/dashboard/user-ranking', { params: { workspace_id: workspaceId } })
}

export function getRecent(workspaceId: string, limit: number = 10) {
  return request.get('/dashboard/recent', { params: { workspace_id: workspaceId, limit } })
}
```

- [ ] **Step 2: Replace Dashboard.vue**

`frontend/src/views/Dashboard.vue`:
```vue
<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useWorkspaceStore } from '@/stores/workspace'
import { getStats, getTrend, getModelUsage, getUserRanking, getRecent } from '@/api/dashboard'
import * as echarts from 'echarts'
import { nextTick } from 'vue'

const workspaceStore = useWorkspaceStore()

const stats = ref({ prompt_count: 0, content_count: 0, monthly_generated: 0, pending_review: 0 })
const recentItems = ref<any[]>([])

let trendChart: echarts.ECharts | null = null
let modelChart: echarts.ECharts | null = null
let rankingChart: echarts.ECharts | null = null

async function fetchDashboard() {
  if (!workspaceStore.currentWorkspace) return
  const wsId = workspaceStore.currentWorkspace.id

  const [statsData, trendData, modelData, rankingData, recentData]: any[] = await Promise.all([
    getStats(wsId),
    getTrend(wsId),
    getModelUsage(wsId),
    getUserRanking(wsId),
    getRecent(wsId),
  ])

  stats.value = statsData.data
  recentItems.value = recentData.data

  await nextTick()
  renderTrendChart(trendData.data)
  renderModelChart(modelData.data)
  renderRankingChart(rankingData.data)
}

function renderTrendChart(data: { date: string; count: number }[]) {
  const el = document.getElementById('trend-chart')
  if (!el) return
  if (!trendChart) trendChart = echarts.init(el)
  trendChart.setOption({
    title: { text: '近 30 天生成趋势', left: 'center' },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: data.map((d) => d.date.slice(5)) },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{ data: data.map((d) => d.count), type: 'line', smooth: true, areaStyle: { opacity: 0.3 } }],
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  })
}

function renderModelChart(data: { name: string; count: number }[]) {
  const el = document.getElementById('model-chart')
  if (!el) return
  if (!modelChart) modelChart = echarts.init(el)
  modelChart.setOption({
    title: { text: '模型使用占比', left: 'center' },
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie',
      radius: '60%',
      data: data.map((d) => ({ name: d.name, value: d.count })),
      emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' } },
    }],
  })
}

function renderRankingChart(data: { username: string; count: number }[]) {
  const el = document.getElementById('ranking-chart')
  if (!el) return
  if (!rankingChart) rankingChart = echarts.init(el)
  rankingChart.setOption({
    title: { text: '用户生成量排名', left: 'center' },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: data.map((d) => d.username) },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{ data: data.map((d) => d.count), type: 'bar' }],
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  })
}

onMounted(fetchDashboard)
watch(() => workspaceStore.currentWorkspace, fetchDashboard)

const statusMap: Record<string, { label: string; type: string }> = {
  draft: { label: '草稿', type: 'info' },
  pending_review: { label: '待审核', type: 'warning' },
  approved: { label: '已通过', type: 'success' },
  rejected: { label: '已驳回', type: 'danger' },
}
</script>

<template>
  <div>
    <h3>数据看板</h3>

    <!-- Stats cards -->
    <el-row :gutter="16" style="margin-bottom: 24px;">
      <el-col :span="6">
        <el-card shadow="hover">
          <div style="text-align: center;">
            <div style="font-size: 32px; font-weight: bold; color: #409EFF;">{{ stats.prompt_count }}</div>
            <div style="color: #999;">Prompt 总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div style="text-align: center;">
            <div style="font-size: 32px; font-weight: bold; color: #67C23A;">{{ stats.content_count }}</div>
            <div style="color: #999;">内容总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div style="text-align: center;">
            <div style="font-size: 32px; font-weight: bold; color: #E6A23C;">{{ stats.monthly_generated }}</div>
            <div style="color: #999;">本月生成</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div style="text-align: center;">
            <div style="font-size: 32px; font-weight: bold; color: #F56C6C;">{{ stats.pending_review }}</div>
            <div style="color: #999;">待审核</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Charts -->
    <el-row :gutter="16" style="margin-bottom: 24px;">
      <el-col :span="16">
        <el-card>
          <div id="trend-chart" style="height: 300px;"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <div id="model-chart" style="height: 300px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-bottom: 24px;">
      <el-col :span="12">
        <el-card>
          <div id="ranking-chart" style="height: 300px;"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header><span>最近生成记录</span></template>
          <el-table :data="recentItems" style="width: 100%;" max-height="260">
            <el-table-column label="内容" min-width="200">
              <template #default="{ row }">
                {{ (row.edited_text || row.generated_text || '').slice(0, 40) }}...
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="statusMap[row.status]?.type as any" size="small">{{ statusMap[row.status]?.label }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="时间" width="140">
              <template #default="{ row }">
                {{ new Date(row.created_at).toLocaleString() }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>
```

- [ ] **Step 3: Verify**

```bash
docker compose up -d
# Login → Dashboard should show stats cards and charts
# Generate some content → charts should update
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/
git commit -m "feat: dashboard with ECharts — stats, trend, model usage, ranking"
```

---

## Task 5: Content Export Backend

**Files:**
- Create: `backend/app/api/v1/export.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Create export router**

`backend/app/api/v1/export.py`:
```python
import io
import uuid
import zipfile

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.content import Content, ContentStatus
from app.models.prompt import Prompt
from app.services import workspace_service

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/markdown/{content_id}")
async def export_markdown(
    content_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Content).where(Content.id == content_id))
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    if content.status != ContentStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Only approved content can be exported")

    member = await workspace_service.check_workspace_access(db, content.workspace_id, current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Not a member")

    text = content.edited_text or content.generated_text
    prompt_result = await db.execute(select(Prompt).where(Prompt.id == content.prompt_id))
    prompt = prompt_result.scalar_one_or_none()
    filename = f"{prompt.title if prompt else 'content'}_{str(content.id)[:8]}.md"

    return StreamingResponse(
        io.BytesIO(text.encode("utf-8")),
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/zip")
async def export_zip(
    content_ids: list[uuid.UUID],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Content).where(Content.id.in_(content_ids)))
    contents = list(result.scalars().all())

    if not contents:
        raise HTTPException(status_code=404, detail="No contents found")

    # Verify access
    for c in contents:
        member = await workspace_service.check_workspace_access(db, c.workspace_id, current_user.id)
        if not member:
            raise HTTPException(status_code=403, detail="Not a member of one or more workspaces")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, content in enumerate(contents):
            text = content.edited_text or content.generated_text
            prompt_result = await db.execute(select(Prompt).where(Prompt.id == content.prompt_id))
            prompt = prompt_result.scalar_one_or_none()
            filename = f"{prompt.title if prompt else 'content'}_{str(content.id)[:8]}.md"
            zf.writestr(filename, text)

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=contents.zip"},
    )
```

- [ ] **Step 2: Register router in main.py**

```python
from app.api.v1.export import router as export_router
app.include_router(export_router, prefix="/api/v1")
```

- [ ] **Step 3: Commit**

```bash
git add backend/
git commit -m "feat: content export — markdown and zip download"
```

---

## Task 6: Frontend — Export Integration

**Files:**
- Modify: `frontend/src/views/contents/ContentDetail.vue`

- [ ] **Step 1: Add export buttons to ContentDetail.vue**

Add to the button area in `ContentDetail.vue`:
```vue
<el-button @click="handleExportMarkdown">导出 Markdown</el-button>
```

Add the handler function:
```typescript
async function handleExportMarkdown() {
  const token = localStorage.getItem('access_token')
  const resp = await fetch(`/api/v1/export/markdown/${content.value.id}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!resp.ok) {
    ElMessage.error('导出失败')
    return
  }
  const blob = await resp.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `content_${content.value.id.slice(0, 8)}.md`
  a.click()
  URL.revokeObjectURL(url)
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/
git commit -m "feat: frontend export markdown button"
```

---

## Task 7: Seed Data + Final Docker Build

**Files:**
- Modify: `backend/app/main.py`

- [ ] **Step 1: Enhance seed data in main.py lifespan**

Update the seed section in `backend/app/main.py` to also create a default workspace and sample AI model:

```python
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceMemberRole
from app.models.ai_model import AIModel
from app.models.prompt import Prompt

# In the lifespan function, after creating admin:
async with async_session() as db:
    # ... existing admin creation ...

    # Create default workspace
    result = await db.execute(select(Workspace).where(Workspace.name == "Default Workspace"))
    if not result.scalar_one_or_none():
        admin = (await db.execute(select(User).where(User.email == "admin@example.com"))).scalar_one()
        ws = Workspace(name="Default Workspace", description="默认工作空间", owner_id=admin.id)
        db.add(ws)
        await db.flush()

        # Add admin as workspace member
        member = WorkspaceMember(workspace_id=ws.id, user_id=admin.id, role=WorkspaceMemberRole.ADMIN)
        db.add(member)

        # Add sample AI model
        model = AIModel(
            workspace_id=ws.id,
            name="GPT-4o (Mock)",
            provider="openai",
            model_name="gpt-4o",
            is_active=True,
            default_params={"temperature": 0.7, "max_tokens": 2000},
        )
        db.add(model)

        # Add sample prompts
        from app.models.prompt import PromptVersion
        prompt1 = Prompt(
            workspace_id=ws.id,
            title="产品营销文案",
            content="请为 {{product_name}} 写一段面向 {{target_audience}} 的营销文案，突出产品的核心优势。",
            category="marketing",
            tags=["营销", "文案"],
            variables=[{"name": "product_name", "required": True}, {"name": "target_audience", "required": True}],
            version=1,
            created_by=admin.id,
        )
        db.add(prompt1)
        await db.flush()
        db.add(PromptVersion(prompt_id=prompt1.id, version=1, content=prompt1.content))

        prompt2 = Prompt(
            workspace_id=ws.id,
            title="技术文档生成",
            content="请为 {{product_name}} 编写一份技术架构文档，包含系统概述、技术栈、架构设计和部署方案。",
            category="tech_doc",
            tags=["技术", "文档"],
            variables=[{"name": "product_name", "required": True}],
            version=1,
            created_by=admin.id,
        )
        db.add(prompt2)
        await db.flush()
        db.add(PromptVersion(prompt_id=prompt2.id, version=1, content=prompt2.content))

        prompt3 = Prompt(
            workspace_id=ws.id,
            title="社交媒体帖子",
            content="请为 {{product_name}} 写一条面向 {{target_audience}} 的社交媒体推广帖子，包含 emoji 和话题标签。",
            category="social_media",
            tags=["社交媒体", "推广"],
            variables=[{"name": "product_name", "required": True}, {"name": "target_audience", "required": True}],
            version=1,
            created_by=admin.id,
        )
        db.add(prompt3)
        await db.flush()
        db.add(PromptVersion(prompt_id=prompt3.id, version=1, content=prompt3.content))

        await db.commit()
```

- [ ] **Step 2: Full rebuild and verify**

```bash
cd E:/lx/projects/ai-content-studio
docker compose down -v
docker compose up -d --build
# Wait for startup, then open http://localhost
# Login: admin@example.com / admin123
# Should see: Dashboard with stats, default workspace, sample prompts, AI model
# Create content → Generate → See streaming → Submit for review → Approve → Export
```

- [ ] **Step 3: Final commit**

```bash
git add .
git commit -m "feat: seed data — default workspace, sample prompts, AI model"
```

---

## Task 8: README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write README**

```markdown
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
# 默认管理员: admin@example.com / admin123
```

## 项目结构

```
ai-content-studio/
├── backend/          # FastAPI 后端
├── frontend/         # Vue 3 前端
├── docker-compose.yml
└── README.md
```

## API 文档

启动后访问 http://localhost:8000/docs 查看 Swagger 文档。
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README"
```

---

## Plan 4 Complete

After this plan, the full AI Content Studio is complete:
- Review workflow with submit/approve/reject/batch
- Audit logs for all status changes
- Dashboard with 4 ECharts visualizations + stats cards
- Content export (Markdown single + ZIP batch)
- Seed data (default workspace, admin, sample prompts, AI model)
- README documentation

**All 4 plans done. Run `docker compose up -d` and open http://localhost to demo.**
