# PlacementOS

PlacementOS is a placement preparation and coding practice workspace for Indian engineering freshers (2026–2027).

> **Current status: usable development foundation, not the finished platform.** The working features and known gaps are listed below. The 200-problem bank, 100 SQL questions, complete courses, full company research, production auth hardening, and production deployment are not finished.

## Implemented foundation

- FastAPI backend with SQLAlchemy data models.
- Registration/login using Argon2 password hashing and signed bearer tokens.
- Student/admin role checks. Public registration always creates a student.
- Original DSA starter bank: 36 problems with public samples, hints, starter Python and server-side test cases.
- Monaco Editor coding workspace with run-sample, custom-input and submit actions (requires verified Judge0 configuration to execute code).
- Judge0 integration, explicitly disabled until a hardened deployment is configured and confirmed.
- Read-only SQLite SQL playground with query timeouts, row limits and authorizer restrictions.
- Python, SQL, aptitude and Core CS starter quizzes; randomized timed assessment sessions, server-side deadlines/grading, auto-submit support and saved attempts.
- 27 original introductory lessons across Python, SQL/DBMS, DSA, Data Engineering, Python libraries, Core CS, aptitude and AI/ML, with per-user completion tracking.
- 30 original SQL challenges with server-held reference queries, verdicts and saved user attempts.
- Personal study tasks and problem progress.
- User progress summary and submission history APIs.
- Admin APIs and admin workspace for topics, problem drafts, hidden test cases and publishing.
- Employer directory for 23 companies with official career-portal starting links, evidence-source records, review status and company-tagged practice mappings. Eligibility and assessment research remains pending until sources are added and reviewed.
- Alembic schema migrations, legacy starter-schema upgrade path and production startup guard
- Docker Compose development setup.
- GitHub Actions backend tests and frontend production build.

## Structure

```
backend/     FastAPI app, models, schemas, services and tests
frontend/    React + TypeScript + Vite + Monaco Editor
infra/       Local Docker Compose
docs/        Architecture, research, roadmap and admin setup
.github/     CI workflow
```

## Local setup

### Backend

Python 3.11+ recommended.

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python -m app.seed
python -m app.curriculum_seed
python -m app.sql_seed
uvicorn app.main:app --reload
```

API docs: http://127.0.0.1:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The default API URL is `http://localhost:8000/api`. Override it with `VITE_API_BASE_URL` when needed.

### Docker Compose (development only)

```bash
cp backend/.env.example backend/.env
docker compose -f infra/docker-compose.yml up --build
```

The Compose stack starts the API and frontend. It uses the development database configuration from `backend/.env`; use a managed PostgreSQL database and a reviewed migration workflow for production. Do not expose the development configuration to the internet.

## Tests

```bash
cd backend && pytest -q
cd ../frontend && npm install && npm run build
```

CI runs both checks on pushes and pull requests.

## Code execution safety

The application does not execute user code with Python `eval` / `exec` or a local unrestricted process. Judge0 calls are gated by configuration. Keep `JUDGE0_SECURE_DEPLOYMENT_CONFIRMED=false` until an operator has deployed and verified an isolated Judge0 environment with network disabled by default, non-root execution, CPU/memory/time/process limits, ephemeral storage, container cleanup and no access to app/database secrets. The flag is an operator assertion, not a substitute for those controls.

## SQL playground

Each query uses a fresh in-memory SQLite database populated with a small **synthetic training dataset**. Only read-only SELECT/CTE statements are accepted. Writes, schema changes, attachment and most PRAGMA operations are denied. This is a learning playground, not a connection to production/business data.

## Admin

See [docs/ADMIN_SETUP.md](docs/ADMIN_SETUP.md) for safe role promotion and content-management instructions. Admin registration is not public. A trusted operator can promote a verified account with `python -m app.admin_cli promote-admin verified-admin@example.com` from the backend folder; the command requires interactive confirmation.

## Research integrity and remaining work

See [docs/RESEARCH.md](docs/RESEARCH.md) for the employer-research evidence standard and [docs/ROADMAP.md](docs/ROADMAP.md) for unfinished modules. Company-pattern claims must be verified against official employer sources; candidate reports must be labelled anecdotal.

Major work still pending includes the 200-problem bank (only 36 are currently seeded), expansion of the SQL challenge bank beyond 30 toward 100, deeper course lessons and practical datasets, complete company-by-company hiring research, larger timed mock-test sets, a validated readiness score, study streaks, advanced admin operations, PostgreSQL migrations, production monitoring/backups and a deployed secure Judge0 service.

## License

MIT — see [LICENSE](LICENSE).
