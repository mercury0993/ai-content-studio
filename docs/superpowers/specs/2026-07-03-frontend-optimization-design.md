# Frontend Optimization Design

## Overview

Comprehensive frontend optimization covering performance, code quality, UX polish, and responsive design across all Vue pages.

## Modules

### 1. Common Utilities — `src/utils/common.ts`

Extract duplicated definitions:

- `statusMap: Record<string, { label: string; type: string }>` — shared across ContentList, ReviewCenter, Dashboard
- `truncate(text: string, len: number): string` — duplicated in ContentList, ReviewCenter
- `formatDate(iso: string): string` — replaces scattered `new Date().toLocaleString()` calls

All pages import from `@/utils/common`, removing local duplicates.

### 2. ECharts Memory Leak Fix — `Dashboard.vue`

- `onUnmounted`: call `.dispose()` on all 3 chart instances
- Add `window resize` listener calling `.resize()` on each chart
- Remove listener in `onUnmounted`

### 3. Watch Debounce — `src/composables/useDebouncedWatch.ts`

Composable wrapping `watch` with `setTimeout` debounce (300ms). No external dependency.

```ts
useDebouncedWatch(sources, callback, delay = 300)
```

Used in: ContentList, PromptList, ReviewCenter.

### 4. Skeleton Components — `src/components/`

Three components matching actual page layouts:

- `SkeletonCard.vue` — wide rectangle + small text bar (matches stat cards)
- `SkeletonChart.vue` — tall rectangle (matches chart areas)
- `SkeletonTable.vue` — repeated row bars (matches table layouts)

Pure CSS pulse animation. Shown on first load before data arrives.

### 5. Empty States

Add `<el-empty description="暂无数据" />` to each list page when `items.length === 0 && !loading`.

### 6. Inline Style Cleanup

Move inline `style=""` attributes to `<style scoped>` blocks with named CSS classes across all views.

### 7. Workspace Switcher — `MainLayout.vue`

Add an `<el-select>` in the header (left of the user dropdown) listing all workspaces from the store. Selecting switches `workspaceStore.currentWorkspace`, which automatically triggers data reload in all pages via existing watchers.

### 8. Responsive Dashboard — `Dashboard.vue`

Stat cards: `:xs="12" :sm="12" :md="6" :lg="6"` (2 columns on mobile, 4 on desktop)
Chart rows: `:xs="24" :sm="24" :md="16"` for trend, `:xs="24" :sm="24" :md="8"` for pie, etc.

## Files Changed

| File | Action |
|---|---|
| `src/utils/common.ts` | Create |
| `src/composables/useDebouncedWatch.ts` | Create |
| `src/components/SkeletonCard.vue` | Create |
| `src/components/SkeletonChart.vue` | Create |
| `src/components/SkeletonTable.vue` | Create |
| `src/views/Dashboard.vue` | Modify |
| `src/views/contents/ContentList.vue` | Modify |
| `src/views/prompts/PromptList.vue` | Modify |
| `src/views/reviews/ReviewCenter.vue` | Modify |
| `src/views/workspaces/WorkspaceList.vue` | Modify |
| `src/layouts/MainLayout.vue` | Modify |

## Testing

- Run existing tests: `cd frontend && npx vitest run`
- Manual verification: navigate each page, verify loading states, empty states, workspace switching, responsive behavior
