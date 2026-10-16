# HiveCode — Code Flow

Entry points, execution order, and function call chains.

---

## 1. System Entry Points

| Entry Point | File | Trigger |
|---|---|---|
| **API server** | `services/hivecode/api/main.py` | `uvicorn hivecode.api.main:app` |
| **Celery worker** | `services/hivecode/worker/app.py` | `celery -A hivecode.worker.app worker` |
| **Celery beat (sweeper)** | `services/hivecode/worker/app.py` | `celery -A hivecode.worker.app beat` |
| **Runner agent** | `services/runner/main.py` | `python -m runner.main` |
| **Frontend** | `apps/web/` | `next dev` / `next start` |

---

## 2. API Request Flow

```
Browser
  │
  ▼
Next.js UI (TanStack Query)
  │  fetch /api/v1/*
  ▼
FastAPI API (services/hivecode/api/)
  │
  ├── Middleware: SessionAuth → CSRFCheck → RateLimit
  │
  ├── Router: /tasks
  │     ├── POST /tasks
  │     │     ├── AuthService.authenticate()
  │     │     ├── TaskService.create_task()
  │     │     │     ├── Policy.validate_scope()
  │     │     │     ├── TaskRepository.insert()
  │     │     │     └── Celery: workflow.run.delay(task_id)
  │     │     └── return 202 { task_id }
  │     │
  │     ├── GET /tasks
  │     │     ├── AuthService.authenticate()
  │     │     └── TaskRepository.list_by_user(user_id, cursor, filters)
  │     │
  │     └── GET /tasks/{id}
  │           ├── AuthService.authenticate()
  │           └── TaskRepository.get_by_id(task_id, user_id)
  │
  ├── Router: /auth
  │     ├── GET /auth/github/login
  │     ├── GET /auth/github/callback
  │     │     ├── AuthService.verify_state()
  │     │     ├── GitHubGateway.exchange_code()
  │     │     ├── AuthService.upsert_user()
  │     │     ├── AuthService.sync_installations()
  │     │     └── AuthService.create_session()
  │     ├── GET /auth/me
  │     └── POST /auth/logout
  │
  └── Router: /events
        └── GET /events?task_id={id}&after_seq={n}
              ├── AuthService.authenticate()
              └── EventRepository.get_events_after(task_id, after_seq)
```

---

## 3. Workflow Execution Flow (Celery Worker)

```
Celery job: workflow.run
  │
  ▼
WorkflowRunner.run(task_id)
  │
  ├── LangGraph StateGraph
  │     │
  │     ├── Node 1: intake_and_validate
  │     │     ├── Policy.validate_repository()
  │     │     ├── Policy.check_quota()
  │     │     └── GitHubGateway.resolve_ref()
  │     │
  │     ├── Node 2: prepare_workspace
  │     │     ├── GitHubGateway.fetch_archive()
  │     │     ├── ArtifactStore.put(workspace)
  │     │     ├── SandboxProvider.submit(install_baseline)
  │     │     └── SandboxProvider.poll() → baseline_results
  │     │
  │     ├── Node 3: diagnose_and_plan
  │     │     ├── LLMClient.generate(role='analyst', ...)
  │     │     ├── Policy.freeze_mandatory_checks()
  │     │     └── ReproductionTest.author_and_run()
  │     │
  │     ├── Node 4: generate_patch (attempt n)
  │     │     ├── LLMClient.generate(role='coder', ...)
  │     │     ├── Policy.apply_edits()
  │     │     ├── Policy.scope_gate()
  │     │     └── Policy.test_file_integrity()
  │     │
  │     ├── Node 5: validate_in_sandbox
  │     │     ├── SandboxProvider.submit(checks)
  │     │     └── SandboxProvider.poll() → check_results
  │     │
  │     ├── Node 6: evaluate_checks
  │     │     └── Policy.evaluate_checks() → route
  │     │
  │     ├── Node 7: classify_failure
  │     │     ├── Policy.classify_failure()
  │     │     └── LLMClient.generate(role='failure_analyst', ...)
  │     │
  │     ├── Node 8: independent_review
  │     │     └── LLMClient.generate(role='reviewer', ...)
  │     │
  │     ├── Node 9: final_verdict
  │     │     └── Policy.compute_verdict()
  │     │
  │     └── Node 10: deliver
  │           ├── ReportBuilder.render()
  │           ├── GitHubGateway.push_branch()
  │           └── GitHubGateway.open_pull_request()
  │
  └── Checkpoint after every node (PostgreSQL)
```

---

## 4. Authentication Flow

```
User clicks "Sign in with GitHub"
  │
  ▼
GET /api/v1/auth/github/login
  │  Generate state + PKCE verifier
  │  Store in short-lived cookie
  │  Redirect to GitHub OAuth
  ▼
GitHub → /api/v1/auth/github/callback?code=...&state=...
  │
  ├── AuthService.verify_state()
  ├── GitHubGateway.exchange_code(code) → access_token
  ├── GitHubGateway.get_user(access_token) → user_profile
  ├── AuthService.upsert_user(user_profile)
  ├── GitHubGateway.get_installations(access_token)
  ├── AuthService.sync_installations(installations)
  ├── AuthService.create_session(user_id)
  │     ├── Generate token (256-bit random)
  │     ├── Generate csrf_secret (32 bytes)
  │     ├── SessionRepository.insert(token_hash, csrf_secret, ...)
  │     └── Set __Host-session cookie
  └── Redirect to /tasks
```

---

## 5. Polling Flow (Frontend)

```
Task Detail page mounts
  │
  ├── useTask(taskId) → GET /tasks/{id}
  │     └── Poll every 3s while non-terminal
  │
  └── useTaskEvents(taskId, afterSeq) → GET /events?task_id={id}&after_seq={n}
        └── Poll every 3s while non-terminal
              └── Append new events to timeline
```

---

## 6. Key Function Call Chains

### 6.1 Task Creation

```
POST /tasks
  → TaskService.create_task()
    → Policy.validate_scope(scope)
    → GitHubGateway.resolve_ref(repo, base_ref) → base_commit_sha
    → TaskRepository.insert(task)
    → Celery.send('workflow.run', task_id)
    → return 202
```

### 6.2 Patch Generation (Attempt N)

```
Node 4: generate_patch
  → LLMClient.generate(role='coder', messages, response_model=EditSet)
  → Policy.apply_edits(base_workspace, edit_set)
    → for each edit: find search_text, replace with replacement
    → generate unified diff
    → compute tree_sha
  → Policy.scope_gate(diff, scope)
    → check allowed paths
    → check protected paths
    → check file/line limits
    → check secret patterns
    → check binary files
  → Policy.test_file_integrity(diff)
    → restore test files to base-commit content
  → TaskAttemptRepository.insert(attempt)
```

### 6.3 Validation

```
Node 5: validate_in_sandbox
  → SandboxProvider.submit(JobSpec)
    → build phases from frozen checks
    → set resource limits
    → set network policy
    → enqueue to runner
  → SandboxProvider.poll(handle)
    → check job status
    → on complete: fetch_result()
  → ResultParser.parse(raw_result)
    → safe XML parse
    → cross-check counts
    → validate test IDs
  → CheckRunRepository.insert(check_run)
```

### 6.4 Verdict

```
Node 9: final_verdict
  → Policy.compute_verdict(evidence, policy)
    → gather all check_runs for final attempt
    → check for blocking conditions → Blocked
    → check primary gate (fail-to-pass) → Failed
    → check for non-passed mandatory → Partially verified
    → all mandatory passed → Verified
  → VerdictRepository.insert(verdict)
  → TaskRepository.update(state='finished', outcome=verdict.outcome)
```

---

## 7. Database Access Flow

```
API/Worker
  → Repository function (e.g., TaskRepository.get_by_id)
    → SQLAlchemy session
      → SELECT * FROM tasks WHERE id = ? AND user_id = ?
        → RLS policy: USING (user_id = current_setting('app.current_user_id'))
      → Row → Pydantic model
    → return model
```

---

## 8. Sandbox Execution Flow

```
Worker
  → SandboxProvider.submit(JobSpec)
    → Runner agent pulls job from queue
    → Creates disposable container
    → Phase 1: install (network: mirror only)
    → Phase 2: tests (network: none)
    → Phase 3: lint (network: none)
    → Upload results to S3 (presigned PUT)
    → Runner returns result manifest
  → SandboxProvider.fetch_result(handle)
    → Download from S3 (presigned GET)
    → Parse and validate
  → CheckRunRepository.insert()
```

---

*End of Code Flow*
