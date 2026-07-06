# Backend + Frontend Optimization Plan

> **Goal:** Fix high-impact performance, security, and stability issues across backend and frontend.

**Architecture:** Three workstreams — backend performance (N+1 queries, indexes, rate limits), backend security (api_key encryption, CORS), and frontend stability (error handling, auth interceptor, permission fix).

---

## Backend Stream A: Performance

### Task A1: Fix batch_review N+1 queries
**File:** `backend/app/services/review_service.py`
- Fetch all contents in one `WHERE id IN (...)` query
- Batch workspace membership check instead of per-item

### Task A2: Fix export_service per-item prompt fetch
**File:** `backend/app/services/export_service.py`
- Pre-fetch all related prompts in one query before the loop

### Task A3: Merge dashboard 4 COUNT queries into 1
**File:** `backend/app/services/dashboard_service.py`
- Use conditional aggregation in a single SQL query

### Task A4: Add database indexes
**Files:** `backend/app/models/content.py`, `backend/app/models/prompt.py`, `backend/app/models/audit_log.py`
- Add `Index("ix_contents_ws_status", "workspace_id", "status")`
- Add `Index("ix_contents_ws_created", "workspace_id", "created_at")`
- Add `Index("ix_prompts_ws_category", "workspace_id", "category")`
- Add indexes on audit_log for resource_type + resource_id and user_id

### Task A5: Rate limit content generation endpoints
**File:** `backend/app/api/v1/contents.py`
- Apply rate limiter to `/generate` and `/generate-stream`

---

## Backend Stream B: Security

### Task B1: Encrypt api_key at rest
**File:** `backend/app/models/ai_model.py`, `backend/app/services/model_service.py`
- Use Fernet symmetric encryption for api_key storage
- Decrypt on read

### Task B2: Restrict CORS
**File:** `backend/app/core/main.py`
- Replace `allow_headers=["*"]` with explicit headers

### Task B3: Skip auto-commit for GET requests
**File:** `backend/app/core/database.py`
- Skip `commit()` when request method is GET/HEAD/OPTIONS

---

## Frontend Stream C: Stability

### Task C1: Add global error handler
**Files:** `frontend/src/main.ts`, `frontend/src/App.vue`
- Add `app.config.errorHandler` in main.ts
- Add `onErrorCaptured` in App.vue

### Task C2: Fix Dashboard error handling
**File:** `frontend/src/views/Dashboard.vue`
- Wrap fetchDashboard in try/catch with error feedback

### Task C3: Fix export API bypassing auth interceptor
**File:** `frontend/src/api/export.ts`
- Replace raw `fetch` with configured axios instance

### Task C4: Fix permission check strictness
**File:** `frontend/src/utils/permission.ts`
- Use exact path match instead of `startsWith`

### Task C5: Add confirmation dialogs
**Files:** `frontend/src/views/reviews/ReviewCenter.vue`, `frontend/src/layouts/MainLayout.vue`
- Confirm before approve, submit review, logout

### Task C6: Consistent password validation
**Files:** `frontend/src/views/Register.vue`, `frontend/src/views/Settings.vue`
- Add 8-char minimum check in Register
- Unify to 8-char minimum in Settings

### Task C7: Shared auth layout (Login/Register CSS dedup)
**File:** New — `frontend/src/components/AuthLayout.vue`
**Files:** `frontend/src/views/Login.vue`, `frontend/src/views/Register.vue`
- Extract shared login-page/login-panel styles into reusable wrapper

---

## Verification

- Backend: `pytest backend/tests/ -v`
- Frontend: `npx vue-tsc --noEmit && npx vitest run && npx vite build`
- All existing tests must pass
