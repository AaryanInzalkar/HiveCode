# HiveCode — Decision Log

All meaningful decisions made during code changes are logged here with reasoning.

---

## 2026-10-17 — Project Initialization

### Decision 1: Monorepo structure with separate services

**Decision:** Use a monorepo with `services/hivecode/` (Python backend) and `apps/web/` (Next.js frontend) as separate packages.

**Reasoning:** The TRD specifies a modular monolith with separate deployable units. A monorepo keeps everything in one place while maintaining clear boundaries between the API, worker, runner, and frontend.

---

### Decision 2: Python 3.12 with pyproject.toml

**Target version:** Python 3.12+

**Decision:** Use `pyproject.toml` with `uv` as the package manager. All tool configuration (Ruff, mypy, pytest, import-linter) goes in `pyproject.toml`.

**Reasoning:** `pyproject.toml` is the modern Python standard. `uv` is faster than pip and provides lockfile reproducibility. Centralizing tool config reduces file sprawl.

---

### Decision 3: SQLAlchemy 2.x with Alembic

**Decision:** Use SQLAlchemy 2.x with async sessions in the API and sync sessions in workers (Celery is sync). Alembic for migrations.

**Reasoning:** The TRD specifies this stack. Async in the API handles concurrent polling efficiently. Sync in workers simplifies Celery integration.

---

### Decision 4: LangGraph for workflow orchestration

**Decision:** Use LangGraph with PostgreSQL checkpointer, wrapped behind our own `WorkflowState` and node functions.

**Reasoning:** LangGraph provides checkpointing and human-in-the-loop interrupts needed for approvals and crash resume. Wrapping it limits lock-in (TD-05, D-02).

---

### Decision 5: Next.js with App Router for frontend

**Decision:** Use Next.js 15 with App Router, TypeScript strict, Tailwind CSS, shadcn/ui primitives, TanStack Query v5.

**Reasoning:** The TRD specifies this stack. TanStack Query handles polling and caching for the read-heavy dashboard. shadcn/ui provides consistent components without a runtime dependency.

---

### Decision 6: FastAPI with Pydantic v2

**Decision:** Use FastAPI with Pydantic v2 for all request/response validation. OpenAPI generated automatically.

**Reasoning:** FastAPI provides typed contracts, OpenAPI generation, and async I/O. Pydantic v2 is the modern standard with better performance.

---

### Decision 7: Redis + Celery for job queue

**Decision:** Use Redis as the broker with Celery (`acks_late`, `prefork`, concurrency 1 per process).

**Reasoning:** Mature ack, time-limit, and revoke support. Redis is already needed for rate limits. Durable state is in PostgreSQL, so queue loss is recoverable.

---

### Decision 8: UUIDv7 for primary keys

**Decision:** Use UUIDv7 (time-ordered) for all primary keys, generated in the application layer.

**Reasoning:** Time-ordered UUIDs provide index locality for chronological queries (task history, event traces). Generated in the DB would require a custom type; app-level generation is simpler.

---

### Decision 9: Session tokens as opaque 256-bit random values

**Decision:** Sessions use a random 256-bit opaque token stored as a `__Host-` prefixed cookie. Only SHA-256 hash is stored in the database.

**Reasoning:** Opaque tokens provide instant revocation (no token in JavaScript). The `__Host-` prefix enforces Secure + Path=/ + no Domain. Hash storage means a DB leak doesn't expose live sessions.

---

### Decision 10: CSRF via double-submit cookie pattern

**Decision:** CSRF protection uses the double-submit pattern: server delivers a CSRF secret via `GET /me`, client sends it as `X-CSRF-Token` header on unsafe methods.

**Reasoning:** Stateless CSRF protection that doesn't require server-side storage per request. Combined with `SameSite=Lax` cookies and Origin checking.

---

### Decision 11: Task API is asynchronous

**Decision:** Task execution is asynchronous. `POST /tasks` persists the task and enqueues one Celery job, returning 202 immediately.

**Reasoning:** Tasks take minutes to complete. The frontend polls for updates. This keeps the API responsive and allows the sweeper to recover from crashes.

---

### Decision 12: Repository-level module boundaries

**Decision:** Enforce module boundaries with import-linter in CI. The `policy/` module imports nothing with I/O. `agents/` cannot import `github/` or `sandbox/`.

**Reasoning:** Prevents circular dependencies and enforces the architectural invariants. The `policy/` module must be pure and exhaustively testable.

---

### Decision 12: Custom UUIDv7 implementation

**Decision:** Use a custom UUIDv7 implementation (`uuid6` package) rather than database-generated UUIDs.

**Reasoning:** Time-ordered UUIDs provide index locality for chronological queries. The `uuid6` package is lightweight and well-tested. Application-level generation avoids database-specific UUID functions.

---

### Decision 13: Repository pattern for all database access

**Decision:** All database access goes through repository functions in `db/repositories.py`. No raw queries outside repositories.

**Reasoning:** Centralizes ownership filtering, makes testing easier, and enforces the architectural invariant that all queries are owner-scoped.

---

### Decision 14: Policy module is pure — no I/O imports

**Decision:** The `policy/` module contains only pure functions. It must not import `db`, `github`, `sandbox`, or `llm` modules. Enforced by import-linter in CI.

**Reasoning:** The verdict engine and scope policy must be exhaustively unit-testable and deterministic. Any I/O dependency would make testing harder and introduce non-determinism.

---

### Decision 15: Celery with acks_late and concurrency 1

**Decision:** Celery is configured with `task_acks_late=True`, `task_reject_on_worker_lost=True`, `worker_prefetch_multiplier=1`, and `worker_concurrency=1`.

**Reasoning:** One workflow per worker process isolates memory and cancellation. `acks_late` ensures tasks are not lost if a worker crashes. Concurrency 1 prevents resource contention.

---

### Decision 16: Docker Compose for local development

**Decision:** Local development uses Docker Compose with Postgres, Redis, MinIO, API, worker, beat, and web services.

**Reasoning:** Provides a production-like environment locally. MinIO is S3-compatible for artifact storage. All services are containerized for consistency.

---

### Decision 17: Security headers middleware

**Decision:** All API responses include security headers via middleware: CSP, X-Content-Type-Options, X-Frame-Options, Referrer-Policy, HSTS.

**Reasoning:** Defense in depth against XSS, clickjacking, and MIME sniffing. Applied globally so no endpoint is missed.

---

### Decision 18: Correlation ID on every request

**Decision:** Every request gets a correlation ID (generated or propagated from header). Included in all responses and logs.

**Reasoning:** Enables end-to-end request tracing across API, worker, runner, and external calls. Critical for debugging distributed workflows.

---

## Open Decisions (Pending)

| ID | Decision | Status | Needed By |
|---|---|---|---|
| D-01 | LLM provider/model per role | OPEN | M0 end |
| D-03 | Supported Python versions | OPEN | M2 |
| D-05 | Mandatory checks for Verified | OPEN | M2 |
| D-11 | Frontend hosting (Vercel vs ECS) | OPEN | M1 |

---

*End of Decision Log*
