# HiveCode

**Don't stop when code changes. Stop when the fix is verified.**

A verification-first, self-correcting AI software engineering pipeline. Accepts a GitHub repository and a bounded engineering objective, diagnoses the issue, generates a patch, validates it in an isolated sandbox, responds to failures with bounded retries, and delivers an evidence-backed report and pull request.

## Architecture

```
hivecode/
├── apps/web/               # Next.js frontend
├── services/hivecode/      # Python backend (API, worker, policy, workflow)
│   ├── src/hivecode/
│   │   ├── api/            # FastAPI routers, middleware, dependencies
│   │   ├── auth/           # GitHub OAuth, sessions, CSRF
│   │   ├── config.py       # Application settings
│   │   ├── db/             # SQLAlchemy models, repositories, migrations
│   │   ├── policy/         # Pure functions: scope, verdict, retry
│   │   ├── worker/         # Celery app, tasks, sweeper
│   │   ├── workflow/       # LangGraph workflow (Phase 2+)
│   │   ├── agents/         # LLM role definitions (Phase 2+)
│   │   ├── tools/          # Read-only tools (Phase 2+)
│   │   ├── sandbox/        # Sandbox provider (Phase 3+)
│   │   ├── github/         # GitHub gateway (Phase 2+)
│   │   ├── llm/            # LLM client adapter (Phase 2+)
│   │   ├── artifacts/      # Object storage (Phase 2+)
│   │   ├── reports/        # Report builder (Phase 4+)
│   │   └── observability/  # Logging, tracing, metrics
│   ├── tests/              # Unit and integration tests
│   ├── migrations/         # Alembic migrations
│   ├── pyproject.toml      # Python project config
│   └── Dockerfile
├── services/runner/        # Runner agent (Phase 3+)
├── images/                 # Runner images (Phase 3+)
├── infra/                  # Terraform (Phase 6)
├── benchmarks/             # Seeded-bug repositories (Phase 6)
├── docs/                   # Design documents
├── decisions.md            # Decision log
├── flow.md                 # Code flow documentation
└── docker-compose.yml      # Local development environment
```

## Quick Start

### Prerequisites

- Docker + Docker Compose
- Python 3.12+
- Node.js 20+

### Local Development

```bash
# Clone the repository
git clone https://github.com/your-org/hivecode.git
cd hivecode

# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec api alembic upgrade head

# API is available at http://localhost:8000
# Web UI is available at http://localhost:3000
# MinIO console is available at http://localhost:9001
```

### Running Tests

```bash
cd services/hivecode
python -m pytest tests/ -v
```

## Development Phases

| Phase | Scope | Status |
|---|---|---|
| 0: Spikes | LangGraph, Docker+gVisor, GitHub App perms, LLM candidates | Pending |
| 1: Foundation | Repo setup, CI, auth, DB, task API, local Compose | In Progress |
| 2: Inspection | GitHub App, read-only tools, diagnosis, baseline, frozen checks | Pending |
| 3: Patch & Sandbox | Structured edits, scope gate, Docker sandbox, result parsing | Pending |
| 4: Self-Correction | Failure classification, repair loop, verdict engine, approvals | Pending |
| 5: Delivery UI | All screens, tabs, diff/log viewers, PR creation, polling | Pending |
| 6: Hardening | Budgets, alerts, backups, security tests, benchmark, production | Pending |

## Documentation

- [App Flow](docs/01-app-flow.md) — Screen-by-screen specification
- [UI/UX Design Brief](docs/02-uiux-design-brief.md) — Visual design specification
- [Backend Schema](docs/03-backend-schema.md) — Database schema and auth
- [Implementation Plan](docs/04-implementation-plan.md) — Phase-by-phase plan
- [Decision Log](decisions.md) — All meaningful decisions with reasoning
- [Code Flow](flow.md) — Entry points and execution order

## License

Proprietary — All rights reserved.
