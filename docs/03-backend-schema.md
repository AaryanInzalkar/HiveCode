# HiveCode — Backend Schema

**Version:** 1.0
**Date:** 2026-10-16
**Source:** Derived from HiveCode PRD v1.0 and TRD v1.0
**Purpose:** Complete database schema, authentication/session handling, permissions, and data ownership rules for implementation.

---

## 1. Schema Overview

### 1.1 Entity Relationship Diagram

```
users ──1──*── sessions
 │
 ├──1──*──*── repositories  (via user_repository_grants)
 │
 ├──1──*── tasks ──1──1── repositories
 │            │
 │            ├──1──*── task_attempts ──1──*── check_runs
 │            │
 │            ├──1──*── task_events
 │            │
 │            ├──1──*── artifacts
 │            │
 │            ├──1──*── review_findings
 │            │
 │            ├──1──*── approvals
 │            │
 │            ├──1──*── llm_calls
 │            │
 │            ├──1──1── verdicts
 │            │
 │            └──1──0..1── pull_requests
 │
github_installations ──1──*── repositories

idempotency_keys ──1──1── users
audit_log ──1──0..1── users (actor)
```

### 1.2 Conventions

| Convention | Rule |
|---|---|
| Primary keys | UUIDv7 (time-ordered, generated in application) |
| Timestamps | `timestamptz`, stored in UTC |
| Foreign keys | Always `ON DELETE CASCADE` for child tables, `ON DELETE RESTRICT` for referenced tables |
| Enumerations | PostgreSQL `CHECK` constraints (not native enums, for flexibility) |
| Large content | Stored in object storage; DB holds key, size, SHA-256, content type |
| Append-only tables | `task_events`, `audit_log`, `verdicts` — no UPDATE/DELETE |

---

## 2. Core Tables

### 2.1 `users`

Application users authenticated via GitHub OAuth.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `uuid` | PK | UUIDv7 |
| `github_user_id` | `bigint` | UNIQUE, NOT NULL | GitHub's numeric user ID |
| `github_login` | `text` | NOT NULL | GitHub username |
| `display_name` | `text` | | Display name from GitHub |
| `avatar_url` | `text` | | GitHub avatar URL |
| `email` | `text` | | GitHub email (nullable) |
| `created_at` | `timestamptz` | NOT NULL, DEFAULT now() | |
| `last_login_at` | `timestamptz` | | |
| `disabled_at` | `timestamptz` | | Set when user is suspended |

**Indexes:**
- `idx_users_github_user_id` on `(github_user_id)` — unique lookup

---

### 2.2 `sessions`

Opaque server-side sessions. Raw token is never stored.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `uuid` | PK | UUIDv7 |
| `user_id` | `uuid` | FK → users.id, NOT NULL, ON DELETE CASCADE | |
| `token_hash` | `bytea` | NOT NULL, UNIQUE | SHA-256 of opaque 256-bit token |
| `csrf_secret` | `bytea` | NOT NULL | 32-byte random secret for double-submit CSRF |
| `created_at` | `timestamptz` | NOT NULL, DEFAULT now() | |
| `idle_expires_at` | `timestamptz` | NOT NULL | 24h from last activity (P) |
| `absolute_expires_at` | `timestamptz` | NOT NULL | 7 days from creation (P) |
| `revoked_at` | `timestamptz` | | Set on logout or admin revocation |
| `ip` | `inet` | | IP at creation |
| `user_agent` | `text` | | User agent at creation |

**Indexes:**
- `idx_sessions_user_id` on `(user_id)` — list user's sessions
- `idx_sessions_token_hash` on `(token_hash)` — session lookup (unique)

---

### 2.3 `github_installations`

GitHub App installations.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `uuid` | PK | UUIDv7 |
| `github_installation_id` | `bigint` | UNIQUE, NOT NULL | GitHub's installation ID |
| `account_login` | `text` | | GitHub account login |
| `account_type` | `text` | NOT NULL, CHECK IN ('Organization','User') | |
| `permissions` | `jsonb` | NOT NULL, DEFAULT '{}' | GitHub App permissions |
| `suspended_at` | `timestamptz` | | |
| `created_at` | `timestamptz` | NOT NULL, DEFAULT now() | |
| `updated_at` | `timestamptz` | NOT NULL, DEFAULT now() | |

**Indexes:**
- `idx_installations_github_id` on `(github_installation_id)` — unique lookup

---

### 2.4 `repositories`

GitHub repositories accessible via installations.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `uuid` | PK | UUIDv7 |
| `installation_id` | `uuid` | FK → github_installations.id, NOT NULL, ON DELETE CASCADE | |
| `github_repo_id` | `bigint` | UNIQUE, NOT NULL | GitHub's repo ID |
| `full_name` | `text` | NOT NULL | `owner/repo` format |
| `default_branch` | `text` | NOT NULL, DEFAULT 'main' | |
| `is_private` | `boolean` | NOT NULL, DEFAULT false | |
| `language` | `text` | | Primary language |
| `enabled` | `boolean` | NOT NULL, DEFAULT true | |
| `created_at` | `timestamptz` | NOT NULL, DEFAULT now() | |
| `updated_at` | `timestamptz` | NOT NULL, DEFAULT now() | |

**Indexes:**
- `idx_repos_installation_id` on `(installation_id)` — list repos per installation
- `idx_repos_github_repo_id` on `(github_repo_id)` — unique lookup

---

### 2.5 `user_repository_grants`

Cache of user permissions on repositories.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `user_id` | `uuid` | FK → users.id, NOT NULL, ON DELETE CASCADE | PK part 1 |
| `repository_id` | `uuid` | FK → repositories.id, NOT NULL, ON DELETE CASCADE | PK part 2 |
| `permission` | `text` | NOT NULL, CHECK IN ('read','write','admin') | |
| `verified_at` | `timestamptz` | NOT NULL, DEFAULT now() | Last GitHub verification |
| `expires_at` | `timestamptz` | NOT NULL | TTL: 10 min for reads (P) |

**Indexes:**
- PK on `(user_id, repository_id)`
- `idx_grants_repo_id` on `(repository_id)` — reverse lookup

---

### 2.6 `tasks`

The central entity. One user-submitted objective against one repository at one pinned base commit.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `uuid` | PK | UUIDv7 |
| `user_id` | `uuid` | FK → users.id, NOT NULL, ON DELETE CASCADE | Task owner |
| `repository_id` | `uuid` | FK → repositories.id, NOT NULL, ON DELETE RESTRICT | |
| `correlation_id` | `uuid` | NOT NULL, UNIQUE | Propagated to logs, traces, PR body |
| `title` | `text` | NOT NULL, CHECK (char_length BETWEEN 3 AND 200) | |
| `objective` | `text` | NOT NULL, CHECK (char_length BETWEEN 20 AND 5000) | Untrusted user text |
| `acceptance_criteria` | `jsonb` | NOT NULL, DEFAULT '[]' | `[{id, kind, description, test_id?}]` |
| `scope` | `jsonb` | NOT NULL, DEFAULT '{}' | `{allowed_paths: [], protected_paths: []}` |
| `required_checks` | `jsonb` | NULL | Frozen at node 3; immutable after set (trigger) |
| `base_ref` | `text` | NOT NULL | Branch or tag name |
| `base_commit_sha` | `char(40)` | NOT NULL | Pinned at creation |
| `state` | `text` | NOT NULL, DEFAULT 'queued', CHECK IN ('queued','running','awaiting_approval','cancel_requested','finished','cancelled') | |
| `stage` | `text` | NULL, CHECK IN ('inspect','baseline','diagnose','reproduce','patch','validate','classify','repair','review','verdict','deliver') | |
| `outcome` | `text` | NULL, CHECK IN ('verified','failed','blocked','partially_verified') | Set only with state='finished' |
| `repair_attempts_used` | `smallint` | NOT NULL, DEFAULT 0, CHECK (BETWEEN 0 AND 3) | Hard DB ceiling (INV-5) |
| `budget` | `jsonb` | NOT NULL, DEFAULT '{}' | `{max_attempts: 3, time_limit_s: 1800, cost_limit_usd: 5.00}` |
| `usage` | `jsonb` | NOT NULL, DEFAULT '{}' | `{time_used_s, tokens_in, tokens_out, cost_usd}` |
| `config_snapshot` | `jsonb` | NOT NULL | `{policy_version, prompt_versions, model_ids, runner_image_digests}` |
| `lease_owner` | `text` | NULL | Worker ID holding the lease |
| `lease_expires_at` | `timestamptz` | NULL | |
| `heartbeat_at` | `timestamptz` | NULL | |
| `cancel_requested_at` | `timestamptz` | NULL | |
| `started_at` | `timestamptz` | NULL | |
| `finished_at` | `timestamptz` | NULL | |
| `created_at` | `timestamptz` | NOT NULL, DEFAULT now() | |
| `updated_at` | `timestamptz` | NOT NULL, DEFAULT now() | |
| `version` | `integer` | NOT NULL, DEFAULT 0 | Optimistic concurrency |

**Indexes:**
- `idx_tasks_user_id_created_at` on `(user_id, created_at DESC)` — history list
- `idx_tasks_repository_id` on `(repository_id)` — filter by repo
- `idx_tasks_state` on `(state)` — sweeper queries
- `idx_tasks_correlation_id` on `(correlation_id)` — unique lookup

**Triggers:**
- `trg_tasks_required_checks_immutable`: `required_checks` may be written once (NULL → value). Subsequent updates rejected.
- `trg_tasks_outcome_immutable`: `outcome` may be written once. Subsequent updates rejected.
- `trg_tasks_verified_requires_verdict`: `outcome = 'verified'` requires a matching `verdicts` row.

**Check constraints:**
```sql
CHECK (state IN ('queued','running','awaiting_approval','cancel_requested','finished','cancelled'))
CHECK (outcome IS NULL OR outcome IN ('verified','failed','blocked','partially_verified'))
CHECK ((state = 'finished') = (outcome IS NOT NULL))  -- outcome only on finished tasks
CHECK (repair_attempts_used BETWEEN 0 AND 3)
```

---

### 2.7 `task_attempts`

One candidate patch. Attempt 0 is initial; 1–3 are repairs.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `uuid` | PK | UUIDv7 |
| `task_id` | `uuid` | FK → tasks.id, NOT NULL, ON DELETE CASCADE | |
| `attempt_no` | `smallint` | NOT NULL, CHECK (BETWEEN 0 AND 3) | 0=initial, 1..3=repairs |
| `kind` | `text` | NOT NULL, CHECK IN ('initial','repair') | |
| `status` | `text` | NOT NULL, DEFAULT 'running', CHECK IN ('running','validated','failed','abandoned') | |
| `patch_artifact_id` | `uuid` | FK → artifacts.id, ON DELETE SET NULL | |
| `patch_sha256` | `char(64)` | NOT NULL | SHA-256 of patch content |
| `tree_sha` | `char(40)` | NOT NULL | Git tree SHA of patched workspace |
| `failure_classification` | `jsonb` | | `{class, evidence_refs: []}` |
| `started_at` | `timestamptz` | NOT NULL, DEFAULT now() | |
| `finished_at` | `timestamptz` | | |

**Indexes:**
- `idx_attempts_task_id` on `(task_id)` — list attempts
- UNIQUE `(task_id, attempt_no)` — prevent duplicate attempt numbers

---

### 2.8 `check_runs`

A named validation step executed in the sandbox.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `uuid` | PK | UUIDv7 |
| `task_id` | `uuid` | FK → tasks.id, NOT NULL, ON DELETE CASCADE | |
| `attempt_id` | `uuid` | FK → task_attempts.id, ON DELETE CASCADE, NULL | NULL for baseline runs |
| `check_key` | `text` | NOT NULL | `install`, `tests.target`, `tests.regression`, `lint`, `typecheck`, `scope` |
| `run_seq` | `smallint` | NOT NULL, DEFAULT 1 | Increments for bounded infra re-runs |
| `is_mandatory` | `boolean` | NOT NULL | Copied from frozen required_checks |
| `status` | `text` | NOT NULL, CHECK IN ('passed','failed','error','timed_out','skipped','unavailable','cancelled') | |
| `exit_code` | `integer` | | From runner, not repository |
| `duration_ms` | `integer` | | |
| `tree_sha` | `char(40)` | NOT NULL | Must equal attempt's tree_sha |
| `counts` | `jsonb` | | `{collected, passed, failed, errors, skipped, target_test_ids: [{id, status}]}` |
| `runner_image_digest` | `text` | NOT NULL | Immutable image digest |
| `command_id` | `text` | NOT NULL | Command catalog ID (not free-form shell) |
| `log_artifact_id` | `uuid` | FK → artifacts.id, ON DELETE SET NULL | |
| `junit_artifact_id` | `uuid` | FK → artifacts.id, ON DELETE SET NULL | |
| `flaky_suspected` | `boolean` | NOT NULL, DEFAULT false | Set when re-run changed result |
| `created_at` | `timestamptz` | NOT NULL, DEFAULT now() | |

**Indexes:**
- `idx_check_runs_attempt_id` on `(attempt_id)` — list checks per attempt
- `idx_check_runs_task_id` on `(task_id)` — list all checks for task
- UNIQUE `(attempt_id, check_key, run_seq)` — prevent duplicate runs

---

### 2.9 `task_events`

Ordered, gapless event trace per task. Append-only.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `bigserial` | PK | |
| `task_id` | `uuid` | FK → tasks.id, NOT NULL, ON DELETE CASCADE | |
| `seq` | `integer` | NOT NULL | Gapless per task, assigned in transaction |
| `type` | `text` | NOT NULL | Event type (see below) |
| `stage` | `text` | | Current stage |
| `attempt_no` | `smallint` | | Current attempt |
| `data` | `jsonb` | NOT NULL, DEFAULT '{}' | Small, redacted payload |
| `correlation_id` | `uuid` | NOT NULL | |
| `created_at` | `timestamptz` | NOT NULL, DEFAULT now() | |

**Event types:**
- `task_created`, `intake_validated`, `workspace_prepared`, `baseline_complete`
- `diagnosis_complete`, `plan_created`, `reproduction_test_authored`
- `patch_generated`, `scope_check_passed`, `scope_check_failed`
- `check_started`, `check_completed`, `check_failed`
- `failure_classified`, `repair_started`, `review_completed`
- `verdict_computed`, `pr_created`, `task_cancelled`
- `approval_requested`, `approval_decided`
- `error`, `blocked`

**Indexes:**
- `idx_task_events_task_id_seq` on `(task_id, seq)` — chronological fetch
- UNIQUE `(task_id, seq)` — gapless enforcement

---

### 2.10 `artifacts`

Object storage references for large content.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `uuid` | PK | UUIDv7 |
| `task_id` | `uuid` | FK → tasks.id, NOT NULL, ON DELETE CASCADE | |
| `attempt_id` | `uuid` | FK → task_attempts.id, ON DELETE CASCADE, NULL | |
| `kind` | `text` | NOT NULL, CHECK IN ('diff','plan','diagnosis','log','junit','report','workspace','transcript') | |
| `storage_key` | `text` | NOT NULL, UNIQUE | Object storage key |
| `size_bytes` | `bigint` | NOT NULL | |
| `sha256` | `char(64)` | NOT NULL | Content hash |
| `content_type` | `text` | NOT NULL | MIME type |
| `redaction_version` | `text` | NOT NULL, DEFAULT 'v1' | Redaction pipeline version |
| `created_at` | `timestamptz` | NOT NULL, DEFAULT now() | |
| `expires_at` | `timestamptz` | | Retention-based expiry |

**Indexes:**
- `idx_artifacts_task_id` on `(task_id)` — list artifacts
- `idx_artifacts_attempt_id` on `(attempt_id)` — list per attempt
- `idx_artifacts_expires_at` on `(expires_at)` — reaper queries

---

### 2.11 `review_findings`

Independent reviewer findings. Never merged into check_runs.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `uuid` | PK | UUIDv7 |
| `task_id` | `uuid` | FK → tasks.id, NOT NULL, ON DELETE CASCADE | |
| `attempt_id` | `uuid` | FK → task_attempts.id, ON DELETE CASCADE | |
| `severity` | `text` | NOT NULL, CHECK IN ('critical','high','medium','low','info') | |
| `category` | `text` | NOT NULL | e.g., `missing_test_coverage`, `regression_risk`, `scope_violation` |
| `file_path` | `text` | | |
| `line` | `integer` | | |
| `message` | `text` | NOT NULL | |
| `evidence` | `jsonb` | NOT NULL, DEFAULT '{}' | Supporting data |
| `blocks_delivery` | `boolean` | NOT NULL, DEFAULT false | |
| `created_at` | `timestamptz` | NOT NULL, DEFAULT now() | |

**Indexes:**
- `idx_review_findings_task_id` on `(task_id)` — list findings
- `idx_review_findings_attempt_id` on `(attempt_id)` — list per attempt

---

### 2.12 `approvals`

Human-in-the-loop approval records.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `uuid` | PK | UUIDv7 |
| `task_id` | `uuid` | FK → tasks.id, NOT NULL, ON DELETE CASCADE | |
| `action_type` | `text` | NOT NULL, CHECK IN ('scope_expansion','pr_nonverified','test_modification','protected_path') | |
| `requested_payload` | `jsonb` | NOT NULL | Exact payload being approved |
| `payload_hash` | `char(64)` | NOT NULL | SHA-256 of payload; approval valid only for this hash |
| `status` | `text` | NOT NULL, DEFAULT 'pending', CHECK IN ('pending','approved','rejected','expired') | |
| `requested_at` | `timestamptz` | NOT NULL, DEFAULT now() | |
| `decided_by` | `uuid` | FK → users.id, ON DELETE SET NULL | |
| `decided_at` | `timestamptz` | | |
| `expires_at` | `timestamptz` | NOT NULL | 24h from request (P) |

**Indexes:**
- `idx_approvals_task_id` on `(task_id)` — list approvals
- `idx_approvals_status` on `(status)` — pending approvals

---

### 2.13 `verdicts`

Final outcome computed by the verdict engine. Append-only.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `task_id` | `uuid` | PK, FK → tasks.id, NOT NULL, ON DELETE CASCADE | One verdict per task |
| `outcome` | `text` | NOT NULL, CHECK IN ('verified','failed','blocked','partially_verified') | |
| `reasons` | `jsonb` | NOT NULL, DEFAULT '[]' | Machine-readable reason codes |
| `evidence` | `jsonb` | NOT NULL | `{check_run_ids: [], tree_sha, artifact_hashes: []}` |
| `policy_version` | `text` | NOT NULL | Verdict engine version |
| `computed_at` | `timestamptz` | NOT NULL, DEFAULT now() | |

---

### 2.14 `llm_calls`

Record of every LLM API call.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `uuid` | PK | UUIDv7 |
| `task_id` | `uuid` | FK → tasks.id, NOT NULL, ON DELETE CASCADE | |
| `attempt_id` | `uuid` | FK → task_attempts.id, ON DELETE CASCADE, NULL | |
| `role` | `text` | NOT NULL | `analyst`, `coder`, `reviewer`, `failure_analyst` |
| `provider` | `text` | NOT NULL | e.g., `anthropic`, `openai` |
| `model` | `text` | NOT NULL | Model ID |
| `prompt_version` | `text` | NOT NULL | Versioned prompt identifier |
| `input_tokens` | `integer` | NOT NULL | |
| `output_tokens` | `integer` | NOT NULL | |
| `cost_usd` | `numeric(10,6)` | NOT NULL | |
| `latency_ms` | `integer` | NOT NULL | |
| `status` | `text` | NOT NULL, CHECK IN ('success','error','timeout','cancelled') | |
| `transcript_artifact_id` | `uuid` | FK → artifacts.id, ON DELETE SET NULL | Redacted transcript |
| `created_at` | `timestamptz` | NOT NULL, DEFAULT now() | |

**Indexes:**
- `idx_llm_calls_task_id` on `(task_id)` — list calls per task
- `idx_llm_calls_created_at` on `(created_at)` — cost aggregation

---

### 2.15 `pull_requests`

GitHub pull requests created by HiveCode.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `task_id` | `uuid` | PK, FK → tasks.id, NOT NULL, ON DELETE CASCADE | One PR per task |
| `github_pr_number` | `integer` | NOT NULL | |
| `url` | `text` | NOT NULL | |
| `head_branch` | `text` | NOT NULL | `hivecode/task-{id}` |
| `head_sha` | `char(40)` | NOT NULL | |
| `base_sha` | `char(40)` | NOT NULL | |
| `outcome_at_creation` | `text` | NOT NULL | Outcome when PR was created |
| `draft` | `boolean` | NOT NULL, DEFAULT false | |
| `created_by` | `uuid` | FK → users.id, ON DELETE SET NULL | |
| `created_at` | `timestamptz` | NOT NULL, DEFAULT now() | |

---

### 2.16 `idempotency_keys`

Idempotency for mutating API endpoints.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `user_id` | `uuid` | FK → users.id, NOT NULL, ON DELETE CASCADE | PK part 1 |
| `route` | `text` | NOT NULL | PK part 2, e.g., `POST /tasks` |
| `key` | `text` | NOT NULL | PK part 3, client-generated key |
| `request_hash` | `char(64)` | NOT NULL | SHA-256 of request body |
| `response_status` | `integer` | NOT NULL | |
| `response_body` | `jsonb` | NOT NULL | |
| `created_at` | `timestamptz` | NOT NULL, DEFAULT now() | |
| `expires_at` | `timestamptz` | NOT NULL | 24h |

**Indexes:**
- PK on `(user_id, route, key)`

---

### 2.17 `audit_log`

Security-relevant audit trail. Append-only.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `bigserial` | PK | |
| `actor_user_id` | `uuid` | FK → users.id, ON DELETE SET NULL | NULL for system actors |
| `action` | `text` | NOT NULL | `task_created`, `approval_decided`, `task_cancelled`, `pr_created`, `login`, `logout`, `kill_switch`, `permission_changed` |
| `target_type` | `text` | NOT NULL | `task`, `approval`, `user`, `system` |
| `target_id` | `uuid` | | |
| `metadata` | `jsonb` | NOT NULL, DEFAULT '{}' | |
| `ip` | `inet` | | |
| `created_at` | `timestamptz` | NOT NULL, DEFAULT now() | |

**Indexes:**
- `idx_audit_log_actor` on `(actor_user_id)` |
- `idx_audit_log_target` on `(target_type, target_id)` |
- `idx_audit_log_created_at` on `(created_at)` |

---

### 2.18 `webhook_deliveries`

GitHub webhook deduplication.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `uuid` | PK | UUIDv7 |
| `github_delivery_id` | `text` | UNIQUE, NOT NULL | GitHub's delivery ID |
| `event` | `text` | NOT NULL | `installation`, `pull_request`, etc. |
| `received_at` | `timestamptz` | NOT NULL, DEFAULT now() | |
| `processed_at` | `timestamptz` | | |

---

## 3. Authentication & Session Handling

### 3.1 Session Flow

```
1. User clicks "Sign in with GitHub"
2. Server generates: state (random 32 bytes), PKCE verifier (random 32 bytes)
3. Server stores state + PKCE challenge in short-lived HttpOnly cookie
4. Redirect to GitHub OAuth with state + code_challenge
5. GitHub redirects back to /api/v1/auth/github/callback?code=...&state=...
6. Server validates state, exchanges code for access token
7. Server calls GET /user → upsert user
8. Server calls GET /user/installations → upsert installations, repos, grants
9. Server generates: session token (random 256-bit), CSRF secret (random 32 bytes)
10. Server stores: SHA-256(token) in sessions, CSRF secret in sessions
11. Server sets cookie: __Host-session=<token>; Secure; HttpOnly; SameSite=Lax; Path=/
12. Redirect to /tasks
```

### 3.2 Cookie Specification

| Attribute | Value | Reason |
|---|---|---|
| Name | `__Host-session` | Prefix enforces Secure + Path=/ + no Domain |
| Value | Opaque 256-bit token | Raw token never stored server-side |
| Secure | Yes | HTTPS only |
| HttpOnly | Yes | Not accessible via JavaScript |
| SameSite | Lax | CSRF protection for top-level navigations |
| Path | / | |
| Max-Age | 7 days | Absolute session lifetime |

### 3.3 CSRF Protection

| Aspect | Implementation |
|---|---|
| Mechanism | Double-submit cookie pattern |
| Header | `X-CSRF-Token` required on all unsafe methods (POST, PUT, PATCH, DELETE) |
| Token delivery | `GET /api/v1/auth/me` returns `{ csrf_secret }` |
| Validation | Header value must match session's `csrf_secret` |
| Origin check | `Origin` header must match allowlist |

### 3.4 Session Lifecycle

| Event | Action |
|---|---|
| Login | Create session, rotate any prior session cookie |
| Idle timeout (24h) | Session expired; next request gets 401 |
| Absolute timeout (7d) | Session expired; next request gets 401 |
| Logout | Set `revoked_at`, clear cookie |
| Admin revocation | Set `revoked_at` for all user sessions |

---

## 4. Permissions & Authorization

### 4.1 Permission Model

| Permission | Level | Actions |
|---|---|---|
| `read` | Repository | View repo, create tasks |
| `write` | Repository | Create tasks, create PRs |
| `admin` | Repository | All write actions, manage grants |

### 4.2 Authorization Matrix

| Action | Required permission | Re-verification |
|---|---|---|
| List repositories | `read` on any installed repo | Cached (10 min TTL) |
| Create task | `read` on target repo | Always re-verified |
| View task | Task owner only | N/A |
| Cancel task | Task owner only | N/A |
| Create PR | `write` on target repo | Always re-verified |
| Approve action | Task owner only | N/A |
| View audit log | Admin (system) | N/A |

### 4.3 Data Ownership Rules

| Rule | Implementation |
|---|---|
| Tasks are single-owner | Only `tasks.user_id` can read or act on a task |
| Cross-user access returns 404 | Not 403 — prevents task ID enumeration |
| All queries owner-scoped | Repository functions take authenticated principal |
| RLS as defense in depth | PostgreSQL row-level security on user-owned tables |

### 4.4 GitHub App Permissions

| Permission | Level | Reason |
|---|---|---|
| Metadata | Read | Mandatory for App listing |
| Contents | Read/Write | Read source, create branches/commits |
| Pull requests | Read/Write | Open PRs, read PR state |
| Issues | Read (optional) | Import issue text |
| Workflows | None | Not requested; `.github/**` is protected |
| Administration | None | Not requested |
| Secrets | None | Not requested |
| Environments | None | Not requested |

---

## 5. Database Roles

| Role | Privileges | Usage |
|---|---|---|
| `hivecode_migration` | DDL (CREATE, ALTER, DROP) | Alembic migrations only |
| `hivecode_app` | DML (SELECT, INSERT, UPDATE) on all tables; no UPDATE/DELETE on append-only tables | Runtime application |
| `hivecode_readonly` | SELECT only | Analytics, reporting |

No superuser at runtime. Each component uses its own role.

---

## 6. Row-Level Security (Defense in Depth)

```sql
-- Enable RLS on user-owned tables
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE artifacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE approvals ENABLE ROW LEVEL SECURITY;

-- Policy: users can only see their own tasks
CREATE POLICY tasks_owner_isolation ON tasks
  FOR ALL TO hivecode_app
  USING (user_id = current_setting('app.current_user_id')::uuid);

-- Similar policies for other tables via tasks join
```

---

## 7. Retention Policy

| Data | Retention | Action |
|---|---|---|
| Raw logs | 30 days | Delete artifact + DB row |
| LLM transcripts | 30 days (private repos) | Delete on user request |
| Diffs, reports, verdicts | 12 months | Archive to cold storage |
| Check summaries | 12 months | |
| Audit log | 12 months | |
| Task events | 12 months | |

---

## 8. Migration Rules

| Rule | Requirement |
|---|---|
| Tool | Alembic |
| Strategy | Expand/contract — backward compatible |
| CI gate | Migration test: upgrade from previous release, downgrade where defined |
| Review | All migrations reviewed in CI |

---

*End of Backend Schema*
