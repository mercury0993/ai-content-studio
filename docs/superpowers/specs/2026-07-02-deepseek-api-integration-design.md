# DeepSeek API Integration Design

**Date:** 2026-07-02
**Status:** Approved

## Goal

Replace mock AI content generation with real DeepSeek API calls, including true SSE streaming.

## Context

Currently `ai_service.py` has `mock_generate()` that returns hardcoded templates. The frontend simulates a typewriter effect with `setInterval`. The `AIModel` table already has `provider`, `api_key`, `base_url`, `model_name`, `default_params` fields — no DB migration needed.

## Design Decisions

### API Key: Global + Per-Model Fallback

- Global `DEEPSEEK_API_KEY` in `.env` as default
- Per-model `api_key` field takes priority if set
- Fallback: model key → global key → error

### Streaming: Real SSE

- New endpoint `POST /api/v1/contents/generate-stream` returns SSE
- Original `POST /api/v1/contents/generate` remains for non-streaming use
- Frontend consumes SSE via `fetch` + `ReadableStream`

### SDK: `openai` Python Package

DeepSeek API is OpenAI-compatible. Using the `openai` SDK with custom `base_url` is cleaner than raw HTTP.

## Implementation Plan

### Backend

1. **`backend/app/core/config.py`** — add `DEEPSEEK_API_KEY: str = ""`
2. **`backend/.env.example`** — add `DEEPSEEK_API_KEY=` entry
3. **`backend/requirements.txt`** — add `openai`
4. **`backend/app/services/ai_service.py`** — rewrite: delete mock code, add `deepseek_generate()` and `deepseek_generate_stream()` using `AsyncOpenAI`
5. **`backend/app/services/content_service.py`** — add `generate_content_stream()` async generator; update `generate_content()` to call real API
6. **`backend/app/api/v1/contents.py`** — add `POST /contents/generate-stream` SSE endpoint

### Frontend

7. **`frontend/src/api/contents.ts`** — add `generateContentStream()` function
8. **`frontend/src/views/contents/ContentCreate.vue`** — replace `setInterval` fake typing with real SSE consumption

## Files Changed

| File | Change |
|------|--------|
| `backend/app/core/config.py` | Add `DEEPSEEK_API_KEY` setting |
| `backend/.env.example` | Add `DEEPSEEK_API_KEY` entry |
| `backend/requirements.txt` | Add `openai` |
| `backend/app/services/ai_service.py` | Rewrite: mock → real API |
| `backend/app/services/content_service.py` | Add streaming method |
| `backend/app/api/v1/contents.py` | Add `/generate-stream` endpoint |
| `frontend/src/api/contents.ts` | Add streaming API function |
| `frontend/src/views/contents/ContentCreate.vue` | Real SSE streaming |
