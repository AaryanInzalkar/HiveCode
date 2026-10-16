# HiveCode — Implementation Plan

**Version:** 1.0
**Date:** 2026-10-16
**Source:** Derived from HiveCode PRD v1.0 and TRD v1.0
**Purpose:** Step-by-step phase plan with deliverables for building HiveCode.

---

## Summary of Understanding

HiveCode is a verification-first, self-correcting AI engineering pipeline. It accepts a GitHub repository and a bounded engineering objective, diagnoses the issue, generates a patch, validates it in an isolated sandbox, responds to failures with bounded retries, and delivers an evidence-backed report and pull request.

**Core principle:** The final status is computed by deterministic backend policy from recorded execution evidence — never accepted from an LLM's self-assessment.

**MVP scope:** Python repositories, GitHub integration, Docker-isolated validation, max 3 repair attempts, verification report + PR creation.

---

## Phase 0: Spikes & Decision De-risking

**Goal:** Resolve the four largest technical unknowns before building on them.

| Spike | Question | Deliverable |
|---|---|---|
| LangGraph + Postgres checkpointer | Does LangGraph's checkpointing and approval interrupt model fit our workflow? | Go/no-go for TD-05 |
| Docker + gVisor sandbox | Can we achieve per-phase networking and resource isolation? | Go/no-go for TD-09 |
| GitHub App permissions | Does installation token support collaborator permission check (AUTH-08)? | Go/no-go for TD-07 |
| LLM candidates on seeded bugs | Which model/provider balances quality, tool support, latency, cost? | Model selection for D-01 |

**Deliverables:**
- Written go/no-go decisions for TD-05, TD-07, TD-09, D-01
- Thin working vertical slice: sandboxed pytest run + resumed workflow
- Benchmark suite: 10 seeded bugs with expected outcomes

**Estimated effort:** 1–2 weeks

---

## Phase 1: Foundation

**Goal:** Project scaffolding, CI, authentication, database, task API, local environment.

### 1.1 Repository Setup

| Task | Deliverable |
|---|---|
| Create monorepo structure | `hivecode/` with `apps/web/`, `services/hivecode/`, `services/runner/`, `images/`, `infra/`, `benchmarks/` |
| Python project setup | `pyproject.toml` with uv, Ruff, mypy strict, pytest, Hypothesis, import-linter |
| Next.js project setup | `apps/web/` with App Router, TypeScript strict, Tailwind, shadcn/ui, TanStack Query |
| Docker Compose | Local environment: Postgres, Redis, MinIO, API, worker, runner, web |
| CI pipeline | GitHub Actions: lint, type check, unit tests, security scans |

### 1.2 Database & Models

| Task | Deliverable |
|---|---|
| SQLAlchemy models | All tables from backend schema |
| Alembic setup | Initial migration + migration test in CI |
| Database roles | Migration, app, readonly roles |
| RLS policies | Row-level security on user-owned tables |

### 1.3 Authentication & Sessions

| Task | Deliverable |
|---|---|
| GitHub OAuth flow | Sign-in, callback, session creation |
| Session management | Cookie spec, idle/absolute timeout, revocation |
| CSRF protection | Double-submit pattern, Origin allowlist |
| Security headers | CSP, HSTS, X-Content-Type-Options, frame-ancestors |
| Rate limiting | Redis token bucket per user/IP |

### 1.4 Task API

| Task | Deliverable |
|---|---|
| POST /tasks | Create task with idempotency key |
| GET /tasks | List tasks (paginated, filterable) |
| GET /tasks/{id} | Task detail with current state |
| POST /tasks/{id}/cancel | Cancel task |
| GET /tasks/{id}/events | Event stream (polling) |
| GET /repositories | List authorized repositories |
| POST /github/installations/sync | Sync installations |

### 1.5 Local Environment

| Task | Deliverable |
|---|---|
| Docker Compose stack | All services running locally |
| Mock adapters | Fake GitHub, fake LLM (replay mode), fake sandbox |
| Seed data | Test user, test repository, sample tasks |

**Deliverables:**
- Signed-in user can create and read a task and its events
- Cross-user access tests pass
- CI green with security scans
- Migrations upgrade cleanly

**Estimated effort:** 3 weeks

---

## Phase 2: Inspection & Diagnosis

**Goal:** GitHub App integration, repository fetching, code inspection, diagnosis, baseline run, frozen mandatory checks.

### 2.1 GitHub App Integration

| Task | Deliverable |
|---|---|
| GitHub App auth | Installation token minting, webhook verification |
| Archive fetch | Download repo at pinned SHA, store in object storage |
| Python detection | Detect Python version, install method, test command |
| Repository validation | Size limits, project markers, supported config |

### 2.2 Read-Only Tools

| Task | Deliverable |
|---|---|
| `read_file` | Read file content from workspace |
| `search` | Ripgrep-style search |
| `symbol_lookup` | Python AST symbol lookup |
| `list_files` | Directory structure |
| Policy layer | All tools validated against scope policy |

### 2.3 Diagnosis & Planning

| Task | Deliverable |
|---|---|
| Analyst agent | Role prompt, output schema (diagnosis + plan) |
| Context assembly | File search + AST lookup within token budget |
| Plan structure | Root cause, evidence, affected files, proposed changes |
| Baseline run | Install deps, run tests on unmodified commit |
| Pre-existing failure detection | Compare baseline failures to identify pre-existing |

### 2.4 Mandatory Checks

| Task | Deliverable |
|---|---|
| Check freezing | Freeze required_checks at node 3, immutable after |
| Reproduction test | Author test if none exists; must fail on base commit |
| Fail-to-pass validation | Target test fails on base, must pass on patch |

**Deliverables:**
- Diagnosis cites real files and test output
- Unsupported repositories get actionable errors
- Mandatory checks are immutable after freeze
- Reproduction test demonstrates the bug

**Estimated effort:** 3 weeks

---

## Phase 3: Patch Generation & Sandbox

**Goal:** Structured edits, scope gate, test-file integrity, sandbox provider, result parsing, check-run capture.

### 3.1 Patch Generation

| Task | Deliverable |
|---|---|
| Coder agent | Role prompt, structured edit output schema |
| Edit application | Backend applies edits, rejects non-matching |
| Diff generation | Backend generates unified diff |
| Patch hashing | SHA-256 of patch, tree_sha of patched workspace |

### 3.2 Scope & Policy Gate

| Task | Deliverable |
|---|---|
| Path validation | Allowed/protected path checking |
| File/line limits | Max 15 files, 500 changed lines per attempt |
| Secret detection | Pattern + entropy detectors on diffs |
| Binary file detection | Reject binary changes |
| Permission/mode change detection | Reject permission changes |
| Test-file integrity | Restore test files to base-commit content |

### 3.3 Sandbox Provider

| Task | Deliverable |
|---|---|
| SandboxProvider interface | `submit`, `poll`, `cancel`, `fetch_result` |
| JobSpec builder | Phases, limits, network policy |
| Docker runner | Container per phase, resource limits |
| Command catalog | `pip_install_requirements`, `pytest_selected`, `pytest_full`, `ruff_check`, `mypy_check` |
| Network policy | Install: mirror only; Tests: none |
| Result parsing | Safe XML parser, cross-checks, evidence validation |

### 3.4 Check-Run Capture

| Task | Deliverable |
|---|---|
| Check execution | Dispatch frozen checks through command catalog |
| Evidence storage | Logs, JUnit XML, result manifest in object storage |
| Status recording | passed/failed/error/timed_out/skipped/unavailable/cancelled |
| Flaky detection | Re-run environmental failures, flag if results differ |

**Deliverables:**
- Patches apply deterministically
- Scope violations rejected
- Sandbox escape suite passes
- Evidence stored with hashes

**Estimated effort:** 3 weeks

---

## Phase 4: Self-Correction Loop

**Goal:** Failure classification, repair loop, no-progress stop, independent review, verdict engine, approvals, kill switch, crash resume.

### 4.1 Failure Classification

| Task | Deliverable |
|---|---|
| Rule-based classifier | pre_existing, environmental, patch_related, unknown |
| Failure analyst LLM | Reclassify ambiguous cases only |
| Sanitized excerpts | Feed relevant failure output to repair agent |

### 4.2 Repair Loop

| Task | Deliverable |
|---|---|
| Repair router | patch_related failures consume repair attempt |
| No-progress stop | Same patch hash or same failing test set → stop |
| Budget check | Don't start repair if below minimum time/cost threshold |
| Attempt tracking | DB-enforced ceiling (0..3) |

### 4.3 Independent Review

| Task | Deliverable |
|---|---|
| Reviewer agent | Isolated from coder reasoning, reviews final diff |
| Finding schema | severity, category, file_path, line, message, blocks_delivery |
| Review policy | Critical unresolved findings block delivery |

### 4.4 Verdict Engine

| Task | Deliverable |
|---|---|
| `compute_verdict()` | Pure function: evidence + policy → verdict |
| Outcome computation | Ordered rules: Blocked → Failed → Partially verified → Verified |
| Property-based tests | Hypothesis: failed mandatory → not Verified; stale tree_sha → not Verified |
| Report generation | Deterministic templates from stored evidence |

### 4.5 Approvals & Safety

| Task | Deliverable |
|---|---|
| Approval flow | Gated actions create approvals row, pause task |
| Approval expiry | 24h expiry → Blocked (APPROVAL_EXPIRED) |
| Kill switch | Global flag halts new sandbox jobs and LLM calls |
| Cancellation | Takes effect at next node boundary, retains evidence |
| Crash resume | Idempotency keys, continue from last checkpoint |

**Deliverables:**
- Retry ceiling never exceeded in tests
- Hypothesis properties pass
- Crash-resume test passes
- No false Verified on seeded and adversarial tasks

**Estimated effort:** 4 weeks

---

## Phase 5: Delivery UI

**Goal:** Task history, detail tabs, diff and log viewers, report, cancellation, PR creation.

### 5.1 Frontend Pages

| Task | Deliverable |
|---|---|
| Sign in page | GitHub OAuth, app install CTA |
| Repositories page | Repo list, sync, new task CTA |
| New task page | Multi-section form, config preview, validation |
| Task history page | Paginated list, filters, search |
| Task detail page | Header, tabs, polling, actions |

### 5.2 Task Detail Tabs

| Task | Deliverable |
|---|---|
| Overview tab | Objective, criteria, configuration, outcome |
| Timeline tab | Chronological event stream |
| Attempts tab | Patch history with diff viewer |
| Checks tab | Check results table, log viewer, JUnit viewer |
| Review tab | Reviewer findings panel |
| Report tab | Verification report, download PDF |
| Approvals tab | Pending approvals, approve/reject |

### 5.3 PR Creation

| Task | Deliverable |
|---|---|
| PR endpoint | POST /tasks/{id}/pr with idempotency |
| Branch push | Push hivecode/* branch |
| PR body | Verification report, evidence links, change summary |
| Draft mode | Draft PR for Partially verified with approval |

### 5.4 Polling & Real-Time Updates

| Task | Deliverable |
|---|---|
| Task polling | GET /tasks/{id} every 3s while non-terminal |
| Event polling | GET /tasks/{id}/events?after_seq= every 3s |
| Backoff | Exponential backoff on failure |
| Tab visibility | Pause when hidden, resume on focus |

**Deliverables:**
- End-to-end Playwright flow from sign-in to PR on staging test repository
- UI statuses match API evidence
- Partially verified never styled as success

**Estimated effort:** 3 weeks

---

## Phase 6: Hardening

**Goal:** Resource limits, budgets, alerts, backups, production environment, security tests, benchmark baseline.

### 6.1 Resource Limits & Budgets

| Task | Deliverable |
|---|---|
| Per-task budgets | Wall-clock, tokens, cost limits |
| Per-user quotas | Concurrent tasks, daily cost cap |
| Sandbox limits | CPU, memory, PIDs, disk, log cap |
| Load shedding | 503 SERVICE_BUSY when queue age exceeds limit |

### 6.2 Observability

| Task | Deliverable |
|---|---|
| Structured logging | JSON logs with correlation_id, redaction |
| OpenTelemetry | Spans for API, workflow nodes, sandbox jobs, LLM calls |
| Metrics | Tasks by outcome, repair attempts, durations, cost |
| Alerts | INV-8 violations, stuck tasks, queue age, heartbeat loss |

### 6.3 Backup & Recovery

| Task | Deliverable |
|---|---|
| RDS backups | Automated with PITR |
| Artifact lifecycle | Retention-based deletion |
| Restore rehearsal | Quarterly restore test |

### 6.4 Security Tests

| Task | Deliverable |
|---|---|
| IDOR tests | Cross-user access attempts |
| CSRF tests | CSRF protection validation |
| Prompt injection corpus | Repository files, issues, test output |
| Sandbox escape suite | Network scan, metadata, fork bomb, memory bomb, disk fill, forged JUnit |

### 6.5 Benchmark

| Task | Deliverable |
|---|---|
| Seeded-bug repositories | 30–50 tasks across categories |
| Withheld tests | Not visible to agents |
| Benchmark harness | Run on model/prompt/workflow changes |
| Metrics | Verified success rate, false-Verified count, retry compliance |

### 6.6 Production Environment

| Task | Deliverable |
|---|---|
| Terraform IaC | All infrastructure as code |
| Staging environment | Separate GitHub App, test repositories |
| Production environment | Separate accounts, secrets, WAF |
| Chaos drills | Kill worker, kill runner, drop Redis, break connectivity |

**Deliverables:**
- Chaos drills pass
- Restore rehearsal done
- Benchmark report meets or revises targets with explanation
- Threat-model review signed off

**Estimated effort:** 3–4 weeks

---

## Dependency Graph

```
Phase 0 (Spikes)
    │
    ▼
Phase 1 (Foundation)
    │
    ▼
Phase 2 (Inspection) ──────┐
    │                        │
    ▼                        │
Phase 3 (Patch & Sandbox) ──┤
    │                        │
    ▼                        │
Phase 4 (Self-Correction) ──┤
    │                        │
    ▼                        │
Phase 5 (Delivery UI) ──────┘
    │
    ▼
Phase 6 (Hardening)
```

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Plausible but incorrect fixes pass visible tests | High | High | Fail-to-pass rule, test-file integrity, independent review, withheld tests |
| Container escape through shared kernel | Low | Critical | Separate VPC, gVisor, no credentials, kill switch |
| Prompt injection causes harmful tool use | High | Medium | Policy validation, protected paths, human merge |
| Repository environments hard to reproduce | High | Medium | Narrow MVP matrix, baseline run, bounded re-runs |
| Cost and latency exceed budget | Medium | Medium | Per-task budgets, focused context, replay mode |
| Test reporting manipulated by repo code | Medium | High | Runner-sourced exit codes, restored test config, cross-checks |
| LangGraph/Celery semantics cause lost work | Medium | Medium | M0 spike, idempotency keys, leases, crash-resume tests |
| GitHub permission model allows broad write | Medium | Medium | Branch prefix enforcement, protected branches |
| Private code sent to LLM provider | Medium | High | Contractual no-training, consent, minimization, redaction |
| Overengineering delays core loop | Medium | Medium | Single workflow, M0 timebox, deferrals |

---

## Open Decisions

| ID | Decision | Options | Proposed default | Needed by |
|---|---|---|---|---|
| D-01 | LLM provider/model per role | Candidates from M0 | Best on benchmark under cost cap | M0 end |
| D-02 | Keep LangGraph or fallback | LangGraph; custom state machine | LangGraph if spike passes | M0 end |
| D-03 | Supported Python versions | 3.10–3.12, pip, pytest, 200MB | Section 9.8 matrix | M2 |
| D-04 | Runner isolation level | Docker; gVisor; microVM; managed | Docker + gVisor in separate VPC | M0 end |
| D-05 | Mandatory checks for Verified | Section 8.5 set | Default set | M2 |
| D-06 | PR policy for non-Verified | None; draft with approval; always draft | Draft only for Partially verified with approval | M4 |
| D-07 | Subset regression → Verified? | Never; only if user configures | Only if user configures | M2 |
| D-08 | Retention periods | See DB-13 | 30d logs, 12mo reports | M6 |
| D-09 | Resume after clarification | New task; resume same | New task prefilled | M5 |
| D-10 | SSE instead of polling | Polling; SSE | Polling | After beta |
| D-11 | Frontend hosting | Vercel; ECS | ECS for same-origin | M1 |
| D-12 | Store GitHub user tokens | Don't store; store encrypted | Don't store | M0 end |
| D-13 | Third-party LLM tracing | Off; opt-in; self-hosted | Off by default | M6 |
| D-14 | Benchmark composition | 30–50 tasks across categories | Section 12.5 | M2 start |
| D-15 | Per-user quotas | 2 active tasks; daily cost cap | From baseline cost | M6 |

---

## Technology Stack Summary

| Layer | Technology |
|---|---|
| Frontend | Next.js (App Router), React, TypeScript strict, Tailwind CSS, shadcn/ui, TanStack Query v5 |
| Backend | Python 3.12, FastAPI, Pydantic v2 |
| Database | PostgreSQL 16+, SQLAlchemy 2.x, Alembic, psycopg 3 |
| Queue | Redis + Celery (acks_late, prefork, concurrency 1) |
| Workflow | LangGraph with PostgreSQL checkpointer |
| LLM | Provider-independent LLMClient adapter |
| GitHub | GitHub App; REST + GraphQL |
| Execution | Docker on dedicated runner hosts |
| Artifacts | S3-compatible private object storage |
| IaC | Terraform |
| CI/CD | GitHub Actions |
| Testing | pytest, Hypothesis, Vitest, Playwright, MSW |

---

*End of Implementation Plan*
