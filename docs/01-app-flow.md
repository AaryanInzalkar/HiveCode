# HiveCode — App Flow Document

**Version:** 1.0
**Date:** 2026-10-16
**Source:** Derived from HiveCode PRD v1.0 and TRD v1.0
**Purpose:** Complete screen-by-screen, action-by-action specification for an AI coding agent to build without guessing.

---

## 1. Global Navigation & Shell

### 1.1 Layout Structure

```
┌─────────────────────────────────────────────────────────┐
│  TopBar: Logo | Nav links | User avatar | Sign out      │
├──────────┬──────────────────────────────────────────────┤
│          │                                              │
│  SideNav │  Main content area (route-dependent)         │
│  (auth   │                                              │
│  routes  │                                              │
│  only)   │                                              │
│          │                                              │
└──────────┴──────────────────────────────────────────────┘
```

### 1.2 TopBar

| Element | Behavior |
|---|---|
| **Logo** (HiveCode mark) | Click → navigate to `/tasks` (or `/repositories` if no tasks exist) |
| **Nav: Tasks** | Click → navigate to `/tasks`. Active state when on any `/tasks*` route. |
| **Nav: Repositories** | Click → navigate to `/repositories`. Active state when on `/repositories`. |
| **User avatar + name** | Click → dropdown menu: "Sign out", "Account settings" (placeholder) |
| **Sign out** | Click → POST `/api/v1/auth/logout` → clear session cookie → redirect to `/login` |

### 1.3 SideNav (authenticated routes only)

| Item | Icon | Route | Visible when |
|---|---|---|---|
| Tasks | List icon | `/tasks` | Always |
| Repositories | Repo icon | `/repositories` | Always |
| New Task | Plus icon | `/tasks/new` | Always |

- SideNav collapses to icon-only below 768px width.
- SideNav hidden on `/login` route.

### 1.4 Global States

| State | Trigger | UI Behavior |
|---|---|---|
| **Loading (initial)** | Page mount, data fetching | Skeleton screens matching layout shape; spinner in TopBar |
| **Error (page-level)** | API returns 4xx/5xx | Full-page error panel: icon, message, correlation ID, "Retry" button |
| **Empty** | API returns empty list | Contextual empty state per screen (see below) |
| **Session expired** | API returns 401 | Redirect to `/login` with `?next=<current_path>` |
| **Service unavailable** | API returns 503 | Banner at top: "Service temporarily unavailable. Retrying…" with backoff indicator |

---

## 2. Screen: Sign In (`/login`)

### 2.1 Description

Landing page for unauthenticated users. Single call-to-action: sign in with GitHub.

### 2.2 Layout

```
┌─────────────────────────────────────────────┐
│                                             │
│           [HiveCode Logo + Wordmark]        │
│                                             │
│     "Don't stop when code changes.          │
│      Stop when the fix is verified."        │
│                                             │
│         ┌─────────────────────┐             │
│         │  Sign in with GitHub │             │
│         └─────────────────────┘             │
│                                             │
│  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  │
│                                             │
│  [Install the GitHub App]  (conditional)    │
│                                             │
└─────────────────────────────────────────────┘
```

### 2.3 Elements & Actions

| Element | Type | Behavior |
|---|---|---|
| **Sign in with GitHub** | Primary button | Click → GET `/api/v1/auth/github/login` → GitHub OAuth redirect. Button shows loading spinner during redirect. |
| **Install the GitHub App** | Secondary link | Visible only when API returns `app_installed: false`. Click → opens GitHub App installation page in new tab. |

### 2.4 States

| State | Condition | UI |
|---|---|---|
| **Default** | User not authenticated | As shown above |
| **App not installed** | `GET /api/v1/auth/status` returns `{ app_installed: false }` | "Install the GitHub App" link appears below sign-in button with helper text: "HiveCode needs the GitHub App to access your repositories." |
| **Redirecting** | OAuth flow in progress | Button shows spinner, text "Redirecting to GitHub…" |
| **OAuth error** | GitHub returns error | Inline error banner: "GitHub sign-in failed: {reason}. Please try again." |
| **Already authenticated** | Valid session cookie | Redirect to `/tasks` |

---

## 3. Screen: Repositories (`/repositories`)

### 3.1 Description

Lists all GitHub repositories the user has authorized via the HiveCode GitHub App installation.

### 3.2 Layout

```
┌─────────────────────────────────────────────────────────┐
│  Repositories                              [Refresh]    │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐    │
│  │ [Repo icon] owner/repo-name                     │    │
│  │ Python · Default branch: main                   │    │
│  │ Last task: "Fix migration bug" — Verified       │    │
│  │                                      [New Task] │    │
│  └─────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────┐    │
│  │ [Repo icon] owner/another-repo                  │    │
│  │ Python · Default branch: develop                │    │
│  │ No tasks yet                                  │    │
│  │                                      [New Task] │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### 3.3 Elements & Actions

| Element | Type | Behavior |
|---|---|---|
| **Refresh** | Icon button | Click → POST `/api/v1/github/installations/sync` → re-syncs installations from GitHub. Shows spinner during sync. Toast on success: "Repositories synced." Toast on error: "Sync failed: {reason}." |
| **Repository card** | Card | Click → navigate to `/repositories/{repoId}` (future: repo detail). Currently non-navigating. |
| **New Task** (per card) | Button | Click → navigate to `/tasks/new?repository={repoId}` |
| **Language badge** | Badge | Shows detected primary language. "Python" badge is green. Non-Python repos show amber badge with tooltip: "Limited support — Python only in V1." |

### 3.4 States

| State | Condition | UI |
|---|---|---|
| **Loading** | Fetching repositories | Skeleton cards (3 placeholder cards with pulsing gray blocks) |
| **Empty** | No repositories | Centered empty state: repo icon, "No repositories yet", "Install the HiveCode GitHub App to get started.", [Install GitHub App] button |
| **Error** | API failure | Error panel with correlation ID and [Retry] button |
| **Syncing** | Refresh clicked | Refresh icon spins; button disabled |

---

## 4. Screen: New Task (`/tasks/new`)

### 4.1 Description

Form to submit a new engineering task. Multi-section form with live configuration preview.

### 4.2 Layout

```
┌─────────────────────────────────────────────────────────┐
│  New Task                                               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ① Repository                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Select repository ▾                            │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  ② Base ref                                            │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Branch or commit SHA  (default: main)           │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  ③ Objective                                            │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Title *                                         │    │
│  │ Fix duplicate orders in GET /orders             │    │
│  └─────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Describe the issue *                            │    │
│  │ When listing orders, duplicates appear…         │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  ④ Acceptance criteria                                 │
│  ┌─────────────────────────────────────────────────┐    │
│  │ + Add criterion                                 │    │
│  │ ○ "test_list_orders_no_duplicates passes"       │    │
│  │ ○ "existing endpoint tests still pass"          │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  ⑤ Scope (optional)                                     │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Allowed paths: src/orders/**                    │    │
│  │ Protected paths: .github/**, migrations/**      │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  ⑥ Delivery                                             │
│  ○ Create pull request (default)                        │
│  ○ Report only                                          │
│                                                         │
│  ⑦ Budget summary                                       │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Max repair attempts: 3                          │    │
│  │ Time limit: 30 min                              │    │
│  │ Cost limit: $5.00                               │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │           Configuration Preview                  │    │
│  │  (live summary of all settings)                 │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  [Cancel]                              [Submit Task]    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 4.3 Elements & Actions

| Element | Type | Behavior |
|---|---|---|
| **Repository select** | Dropdown | Populated from `GET /api/v1/repositories`. Shows `owner/repo` format. Required. |
| **Base ref** | Text input | Branch name or commit SHA. Resolved to SHA on submit. Default: repository's default branch. |
| **Title** | Text input | Max 200 chars. Required. |
| **Objective** | Textarea | Max 5000 chars. Required. Treated as untrusted input. |
| **Add criterion** | Button | Adds a new acceptance criterion row. Each row: text input + delete button. |
| **Scope paths** | Tag input | User can add allowed path globs. Protected paths shown as read-only tags. |
| **Delivery mode** | Radio | "Create pull request" (default) or "Report only". |
| **Budget summary** | Read-only panel | Shows default limits. Not editable in V1. |
| **Configuration preview** | Read-only panel | Live-updates as user fills form. Shows: repo, ref, objective summary, criteria count, scope, delivery mode, budget. |
| **Cancel** | Button | Click → navigate back to `/tasks` |
| **Submit Task** | Primary button | Click → validate form → POST `/api/v1/tasks` with idempotency key → on 202, navigate to `/tasks/{taskId}` |

### 4.4 Validation Rules

| Field | Rule | Error message |
|---|---|---|
| Repository | Required | "Select a repository" |
| Title | Required, 3–200 chars | "Title must be 3–200 characters" |
| Objective | Required, 20–5000 chars | "Objective must be 20–5000 characters" |
| Base ref | Valid branch or SHA | "Could not resolve ref '{value}'" |
| Acceptance criteria | At least 1 | "Add at least one acceptance criterion" |

### 4.5 States

| State | Condition | UI |
|---|---|---|
| **Default** | Form empty | All fields empty, Submit disabled |
| **Valid** | All required fields pass validation | Submit enabled |
| **Invalid** | Validation fails | Red border on invalid fields, error text below each |
| **Submitting** | POST in flight | Submit button shows spinner, all fields disabled |
| **Success** | 202 response | Navigate to `/tasks/{taskId}` |
| **Error: ambiguous** | 422 `NEEDS_CLARIFICATION` | Inline banner: "This task needs clarification: {questions}" with suggested edits to objective |
| **Error: unsupported repo** | 422 `UNSUPPORTED_REPOSITORY` | Inline banner: "This repository is not supported: {reason}" |
| **Error: quota** | 429 | Inline banner: "Task quota exceeded. Wait for existing tasks to finish." |
| **Error: server** | 5xx | Inline error banner with correlation ID |

---

## 5. Screen: Task History (`/tasks`)

### 5.1 Description

Paginated list of all tasks for the authenticated user.

### 5.2 Layout

```
┌─────────────────────────────────────────────────────────┐
│  Tasks                              [+ New Task]        │
├─────────────────────────────────────────────────────────┤
│  Filter: [All repos ▾]  [All outcomes ▾]  [Search…]   │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐    │
│  │ ◉ Fix duplicate orders in GET /orders          │    │
│  │ owner/repo · main · 2 min ago                   │    │
│  │ ✓ Verified   Attempts: 1/4   $0.42             │    │
│  └─────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────┐    │
│  │ ◉ Resolve migration bug                         │    │
│  │ owner/repo · main · 15 min ago                  │    │
│  │ ✗ Failed   Attempts: 4/4   $1.20               │    │
│  └─────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────┐    │
│  │ ◉ Fix regression in user service               │    │
│  │ owner/repo · develop · 1 hr ago                 │    │
│  │ ◐ Partially verified   Attempts: 2/4   $0.80   │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  [Load more]                                            │
└─────────────────────────────────────────────────────────┘
```

### 5.3 Elements & Actions

| Element | Type | Behavior |
|---|---|---|
| **+ New Task** | Button | Click → navigate to `/tasks/new` |
| **Repository filter** | Dropdown | Filter by repository. Options from user's repos. |
| **Outcome filter** | Dropdown | Filter by outcome: All, Verified, Failed, Blocked, Partially verified |
| **Search** | Text input | Filter by title/objective text. Debounced 300ms. |
| **Task card** | Card | Click → navigate to `/tasks/{taskId}` |
| **Outcome badge** | Badge | Color-coded: Verified=green, Failed=red, Blocked=amber, Partially verified=blue, In progress=pulsing gray |
| **Load more** | Button | Click → fetch next page (cursor pagination). Hidden when no more pages. |

### 5.4 States

| State | Condition | UI |
|---|---|---|
| **Loading** | Initial fetch | Skeleton cards (5 placeholder cards) |
| **Empty (no tasks)** | User has zero tasks | Centered: task icon, "No tasks yet", "Submit your first task to get started", [+ New Task] button |
| **Empty (filtered)** | Filter returns zero results | Centered: "No tasks match your filters", [Clear filters] button |
| **Error** | API failure | Error panel with correlation ID and [Retry] |
| **Loading more** | Fetching next page | Spinner on "Load more" button |

---

## 6. Screen: Task Detail (`/tasks/{taskId}`)

### 6.1 Description

The primary working screen. Shows full task lifecycle with tabbed interface. Polls for updates while task is non-terminal.

### 6.2 Layout

```
┌─────────────────────────────────────────────────────────┐
│  ← Back to tasks                                        │
│                                                         │
│  Fix duplicate orders in GET /orders                    │
│  owner/repo · main · Started 2 min ago                  │
│  ✓ Verified                                             │
│                                                         │
│  [Cancel task]  [Create PR]  [Retry]                    │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  │ Overview │ Timeline │ Attempts │ Checks │ Review │   │
│  │ Report   │ Approvals│          │         │        │   │
├─────────────────────────────────────────────────────────┤
│  (tab content)                                          │
└─────────────────────────────────────────────────────────┘
```

### 6.3 Header Elements & Actions

| Element | Type | Behavior |
|---|---|---|
| **← Back to tasks** | Link | Click → navigate to `/tasks` |
| **Task title** | Text | Read-only |
| **Repo + ref** | Text | Read-only |
| **Outcome badge** | Badge | Same color rules as task history. Shows live stage (e.g., "Running: diagnose") when non-terminal. |
| **Cancel task** | Button (danger) | Visible when task is non-terminal. Click → confirmation dialog → POST `/api/v1/tasks/{id}/cancel`. |
| **Create PR** | Button (primary) | Visible only when `pr_eligible: true` from API. Click → POST `/api/v1/tasks/{id}/pr` → opens PR URL. |
| **Retry** | Button | Visible when task is Blocked due to clarification. Click → navigate to `/tasks/new?resume={taskId}` |

### 6.4 Polling Behavior

| Condition | Behavior |
|---|---|
| Task is non-terminal | Poll `GET /api/v1/tasks/{id}` every 3s. Poll `GET /api/v1/tasks/{id}/events?after_seq={last}` every 3s. |
| Task is terminal | Stop polling. Show final state. |
| Poll fails | Exponential backoff: 3s → 6s → 12s → 30s max. Show "Connection lost — retrying" banner. |
| User switches tabs | Pause polling when tab is hidden (document.visibilitychange). Resume on focus. |

---

### 6.5 Tab: Overview

```
┌─────────────────────────────────────────────────────────┐
│  Objective                                              │
│  ─────────────────────────────────────────────────────  │
│  When listing orders, duplicates appear in the response │
│  because the query lacks a DISTINCT clause…              │
│                                                         │
│  Acceptance criteria                                    │
│  ─────────────────────────────────────────────────────  │
│  ✓ test_list_orders_no_duplicates passes                │
│  ✓ existing endpoint tests still pass                   │
│                                                         │
│  Configuration                                          │
│  ─────────────────────────────────────────────────────  │
│  Repository: owner/repo                                 │
│  Base ref: main (abc1234)                               │
│  Delivery: Create pull request                          │
│  Budget: 3 attempts, 30 min, $5.00                      │
│  Attempts used: 1/4                                     │
│  Cost: $0.42                                            │
│                                                         │
│  Outcome                                                │
│  ─────────────────────────────────────────────────────  │
│  ✓ Verified                                             │
│  All mandatory checks passed.                           │
└─────────────────────────────────────────────────────────┘
```

| Element | Type | Behavior |
|---|---|---|
| **Objective** | Text | Rendered as plain text (not HTML). Scrollable if long. |
| **Acceptance criteria** | List | Checkmark icons. Green if met, red if not, gray if pending. |
| **Configuration** | Key-value list | Read-only. |
| **Outcome** | Panel | Shows outcome badge + machine-readable reason codes. |

---

### 6.6 Tab: Timeline

```
┌─────────────────────────────────────────────────────────┐
│  ● Task created                    2 min ago             │
│  │                                                      │
│  ● Intake validated                2 min ago             │
│  │                                                      │
│  ● Workspace prepared              2 min ago             │
│  │                                                      │
│  ● Baseline tests run              2 min ago             │
│  │  3 pre-existing failures                              │
│  │                                                      │
│  ● Diagnosis complete              1 min ago             │
│  │  Root cause: missing DISTINCT in query                │
│  │                                                      │
│  ● Patch generated (attempt 0)      1 min ago             │
│  │                                                      │
│  ● Validation passed               45 sec ago            │
│  │                                                      │
│  ● Review complete                 30 sec ago            │
│  │                                                      │
│  ● Verified                        30 sec ago            │
│  │                                                      │
│  ● Pull request opened             30 sec ago            │
└─────────────────────────────────────────────────────────┘
```

| Element | Type | Behavior |
|---|---|---|
| **Timeline item** | List item | Icon + title + timestamp. Expandable for details (click to expand/collapse). |
| **Stage connector** | Vertical line | Connects items. Color: green for success, red for failure, gray for pending. |

---

### 6.7 Tab: Attempts & Diff

```
┌─────────────────────────────────────────────────────────┐
│  Attempt 0 (initial)  ✓ Passed                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │  src/orders/service.py                          │    │
│  │  @@ -45,7 +45,8 @@                              │    │
│  │  -    results = session.query(Order).all()      │    │
│  │  +    results = session.query(Order).distinct() │    │
│  │                                                 │    │
│  │  [View full diff]  [Download patch]            │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  Attempt 1 (repair)  ✗ Failed                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │  src/orders/service.py                          │    │
│  │  @@ -45,7 +45,9 @@                              │    │
│  │  (different approach)                           │    │
│  │                                                 │    │
│  │  [View full diff]  [Download patch]            │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

| Element | Type | Behavior |
|---|---|---|
| **Attempt card** | Card | Shows attempt number, kind (initial/repair), status badge. Collapsed by default. |
| **Diff view** | Code block | Syntax-highlighted unified diff. Rendered as text nodes only (never HTML). |
| **View full diff** | Button | Opens modal with full diff, scrollable, with line numbers. |
| **Download patch** | Button | Downloads `.patch` file from signed URL. |

---

### 6.8 Tab: Checks

```
┌─────────────────────────────────────────────────────────┐
│  Check                  Status    Duration   Attempt     │
│  ─────────────────────────────────────────────────────  │
│  install                 ✓ passed  45s        0           │
│  tests.target            ✓ passed  12s        0           │
│  tests.regression        ✓ passed  38s        0           │
│  lint                    ✓ passed  8s         0           │
│  typecheck               ○ skipped  —          0           │
│  scope                   ✓ passed  <1s        0           │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │ tests.target — passed                           │    │
│  │ ┌───────────────────────────────────────────┐   │    │
│  │ │ test_list_orders_no_duplicates PASSED     │   │    │
│  │ │ test_order_total_calculation PASSED       │   │    │
│  │ │ test_order_status_filter PASSED           │   │    │
│  │ └───────────────────────────────────────────┘   │    │
│  │ [View logs]  [View JUnit XML]                  │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

| Element | Type | Behavior |
|---|---|---|
| **Check row** | Table row | Click to expand/collapse detail panel. |
| **Status badge** | Badge | passed=green, failed=red, error=orange, timed_out=amber, skipped=gray, unavailable=gray, cancelled=gray |
| **View logs** | Button | Opens modal with log viewer (lazy-loaded from signed URL, truncated with marker, download button). |
| **View JUnit XML** | Button | Opens modal with XML viewer. |

---

### 6.9 Tab: Review

```
┌─────────────────────────────────────────────────────────┐
│  Independent Review                                     │
│  ─────────────────────────────────────────────────────  │
│  ⚠ Warning (1)                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │ src/orders/service.py:52                        │    │
│  │ Consider adding a test for empty result set     │    │
│  │ Category: missing_test_coverage                 │    │
│  │ Blocks delivery: No                            │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  ℹ Info (1)                                             │
│  ┌─────────────────────────────────────────────────┐    │
│  │ src/orders/service.py:48                        │    │
│  │ Change is minimal and focused                   │    │
│  │ Category: positive_feedback                     │    │
│  │ Blocks delivery: No                            │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  Review model: claude-sonnet-4-20250514                 │
│  Review completed: 30 sec ago                           │
└─────────────────────────────────────────────────────────┘
```

| Element | Type | Behavior |
|---|---|---|
| **Finding card** | Card | Severity icon + color. Expandable for details. |
| **Severity badge** | Badge | critical=red, high=orange, medium=yellow, low=blue, info=gray |
| **Blocks delivery** | Badge | "Yes" = red badge, "No" = gray badge |

---

### 6.10 Tab: Report

```
┌─────────────────────────────────────────────────────────┐
│  Verification Report                                    │
│  ─────────────────────────────────────────────────────  │
│                                                         │
│  Outcome: ✓ Verified                                    │
│  Policy version: v1.2.0                                 │
│  Computed: 2026-10-16T14:32:00Z                        │
│                                                         │
│  Summary                                                │
│  ─────────────────────────────────────────────────────  │
│  Fixed duplicate orders bug by adding DISTINCT clause   │
│  to the order listing query. All tests pass.            │
│                                                         │
│  Changed files (1)                                      │
│  ─────────────────────────────────────────────────────  │
│  M src/orders/service.py (+1, -1)                       │
│                                                         │
│  Check results                                          │
│  ─────────────────────────────────────────────────────  │
│  ✓ install                                              │
│  ✓ tests.target                                         │
│  ✓ tests.regression                                     │
│  ✓ lint                                                 │
│  ○ typecheck (skipped — not configured)                 │
│  ✓ scope                                                │
│                                                         │
│  Attempts: 1/4 used                                     │
│  Cost: $0.42                                            │
│  Duration: 2m 15s                                       │
│                                                         │
│  [Download full report (PDF)]                           │
└─────────────────────────────────────────────────────────┘
```

| Element | Type | Behavior |
|---|---|---|
| **Download full report** | Button | Downloads PDF from signed URL. |
| **Report content** | Generated | All content from deterministic templates. Model narrative in separately labeled section. |

---

### 6.11 Tab: Approvals

```
┌─────────────────────────────────────────────────────────┐
│  Approvals                                              │
│  ─────────────────────────────────────────────────────  │
│                                                         │
│  No approvals required for this task.                    │
│                                                         │
│  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  │
│                                                         │
│  (When approvals exist:)                                │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Scope expansion requested                       │    │
│  │ Action: Allow editing migrations/               │    │
│  │ Requested: 2 min ago                           │    │
│  │ Expires: 23 min remaining                       │    │
│  │                                                 │    │
│  │ ┌───────────────────────────────────────────┐   │    │
│  │ │ Payload (what will be allowed):           │   │    │
│  │ │ { "paths": ["migrations/**"] }            │   │    │
│  │ └───────────────────────────────────────────┘   │    │
│  │                                                 │    │
│  │ [Reject]              [Approve]                 │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

| Element | Type | Behavior |
|---|---|---|
| **Approval card** | Card | Shows action type, requested time, expiry countdown. |
| **Payload** | Code block | Read-only JSON showing exactly what will be approved. |
| **Approve** | Button (primary) | Click → POST `/api/v1/approvals/{id}/approve` → task resumes. |
| **Reject** | Button (danger) | Click → POST `/api/v1/approvals/{id}/reject` → task goes to verdict. |

---

## 7. Global Components

### 7.1 StatusBadge

| Outcome | Color | Icon | Label |
|---|---|---|---|
| Verified | Green | Check circle | "Verified" |
| Failed | Red | X circle | "Failed" |
| Blocked | Amber | Alert triangle | "Blocked" |
| Partially verified | Blue | Half circle | "Partially verified" |
| Running (stage) | Gray (pulsing) | Spinner | "Running: {stage}" |
| Queued | Gray | Clock | "Queued" |
| Awaiting approval | Amber | Pause | "Awaiting approval" |
| Cancelled | Gray | Ban | "Cancelled" |

### 7.2 CheckStatusBadge

| Status | Color | Icon | Label |
|---|---|---|---|
| passed | Green | Check | "Passed" |
| failed | Red | X | "Failed" |
| error | Orange | Alert | "Error" |
| timed_out | Amber | Clock | "Timed out" |
| skipped | Gray | Skip forward | "Skipped" |
| unavailable | Gray | Question | "Unavailable" |
| cancelled | Gray | Ban | "Cancelled" |

### 7.3 LogViewer (Modal)

```
┌─────────────────────────────────────────────────────────┐
│  Logs — tests.target                    [Download] [X]│
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐    │
│  │ ================= test session starts ===========│    │
│  │ platform linux -- Python 3.12.3, pytest-8.0.0  │    │
│  │ collected 3 items                               │    │
│  │                                                 │    │
│  │ tests/test_orders.py::test_list_orders PASSED    │    │
│  │ tests/test_orders.py::test_duplicates PASSED    │    │
│  │ tests/test_orders.py::test_filter PASSED        │    │
│  │                                                 │    │
│  │ ================== 3 passed in 0.42s ===========│    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  ⚠ Output truncated (showing last 100 KB of 250 KB)   │
└─────────────────────────────────────────────────────────┘
```

| Element | Type | Behavior |
|---|---|---|
| **Log content** | Pre-formatted text | Monospace font. Scrollable. Loaded lazily from signed URL. |
| **Truncation marker** | Banner | Shown when log exceeds size limit. "Output truncated (showing last X KB of Y KB)." |
| **Download** | Button | Downloads full log file from signed URL. |
| **Close** | Button | Closes modal. |

### 7.4 ConfirmationDialog (Modal)

```
┌─────────────────────────────────────────┐
│  Cancel task?                           │
│  ─────────────────────────────────────  │
│  This will stop the task and discard    │
│  any in-progress work. Evidence        │
│  collected so far will be retained.    │
│                                         │
│  [Keep running]      [Cancel task]       │
└─────────────────────────────────────────┘
```

| Element | Type | Behavior |
|---|---|---|
| **Title** | Text | Action-specific (e.g., "Cancel task?", "Reject approval?") |
| **Message** | Text | Explains consequences. |
| **Cancel/Dismiss** | Button | Closes dialog, no action. |
| **Confirm** | Button (danger) | Executes the action. |

### 7.5 Toast Notifications

| Type | Position | Duration | Behavior |
|---|---|---|---|
| Success | Bottom-right | 5s | Green check icon + message. Auto-dismiss. |
| Error | Bottom-right | 10s | Red X icon + message + correlation ID. Dismissible. |
| Info | Bottom-right | 5s | Blue info icon + message. Auto-dismiss. |

---

## 8. Navigation Map

```
/login
  ├─ [Sign in with GitHub] → GitHub OAuth → /callback → /tasks
  └─ [Install GitHub App] → external URL (new tab)

/tasks
  ├─ [+ New Task] → /tasks/new
  ├─ [Task card] → /tasks/{taskId}
  └─ [Filter/search] → updates list in-place

/tasks/new
  ├─ [Cancel] → /tasks
  ├─ [Submit] → /tasks/{taskId}
  └─ [Repository select] → filters base ref options

/tasks/{taskId}
  ├─ [← Back] → /tasks
  ├─ [Tab: Overview] → tab switch
  ├─ [Tab: Timeline] → tab switch
  ├─ [Tab: Attempts] → tab switch
  ├─ [Tab: Checks] → tab switch
  ├─ [Tab: Review] → tab switch
  ├─ [Tab: Report] → tab switch
  ├─ [Tab: Approvals] → tab switch
  ├─ [Cancel task] → confirmation dialog → POST cancel
  ├─ [Create PR] → POST /pr → external PR URL
  └─ [Retry] → /tasks/new?resume={taskId}

/repositories
  ├─ [Refresh] → sync installations
  ├─ [New Task] → /tasks/new?repository={repoId}
  └─ [Repo card] → (future: repo detail)
```

---

## 9. Error Code Reference

| HTTP | Code | User-facing message | Action |
|---|---|---|---|
| 401 | `SESSION_EXPIRED` | "Your session has expired. Please sign in again." | Redirect to /login |
| 403 | `REPO_ACCESS_DENIED` | "You don't have access to this repository." | — |
| 404 | `TASK_NOT_FOUND` | "Task not found." | Navigate to /tasks |
| 409 | `TASK_ALREADY_EXISTS` | "A similar task was recently submitted." | Show existing task |
| 422 | `NEEDS_CLARIFICATION` | "This task needs clarification: {questions}" | Pre-fill form |
| 422 | `UNSUPPORTED_REPOSITORY` | "This repository is not supported: {reason}" | — |
| 429 | `QUOTA_EXCEEDED` | "Task quota exceeded. Wait for existing tasks to finish." | — |
| 429 | `RATE_LIMITED` | "Too many requests. Please wait and try again." | — |
| 503 | `SERVICE_UNAVAILABLE` | "Service temporarily unavailable. Retrying…" | Auto-retry with backoff |
| 503 | `SANDBOX_UNAVAILABLE` | "Execution environment unavailable. Please try again later." | — |

---

## 10. Mobile Responsiveness

| Breakpoint | Width | Layout changes |
|---|---|---|
| Desktop | ≥1024px | Full layout with SideNav |
| Tablet | 768–1023px | SideNav collapses to icon-only; task cards stack vertically |
| Mobile | <768px | SideNav hidden (hamburger menu); single-column layout; tabs become horizontal scroll; modals become full-screen sheets |

---

*End of App Flow Document*
