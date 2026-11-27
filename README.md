# PlacementOS

A structured placement preparation and coding practice platform for Indian engineering freshers (2026–2027).

> **Status: foundation / early development.** The complete 200-problem bank, secure coding judge, SQL sandbox, full learning modules, authentication and production admin system are not yet complete.

## Current foundation
- FastAPI backend, SQLAlchemy data models and problem/submission API foundation
- React + TypeScript + Vite responsive dashboard
- Judge0 adapter boundary (requires separately configured, hardened Judge0 service)
- Docker Compose development setup
- Backend tests and GitHub Actions workflow
- Architecture, research and implementation roadmap

## Structure
```
backend/     FastAPI app, models, schemas, services and tests
frontend/    React + TypeScript application
infra/       Local container orchestration
docs/        Architecture, research framework and roadmap
.github/     CI workflow
```

## Run locally

Backend (Python 3.11+):
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```
API docs: http://127.0.0.1:8000/docs

Frontend:
```bash
cd frontend
npm install
npm run dev
```

Docker:
```bash
docker compose -f infra/docker-compose.yml up --build
```

Tests:
```bash
cd backend && pytest
```

## Security
Never run learner submissions using Python `eval` / `exec` or an unrestricted process on the API server. The current Judge0 module is only an integration boundary. Before accepting untrusted submissions, deploy Judge0 with network disabled by default, strict CPU/memory/time/process limits, non-root execution, ephemeral storage and no access to application secrets. Keep hidden tests server-side.

## Research integrity
Company-specific assessment patterns and eligibility change. See [docs/RESEARCH.md](docs/RESEARCH.md): the evidence-backed employer matrix remains pending and claims must be rechecked against official sources.

## Roadmap
See [docs/ROADMAP.md](docs/ROADMAP.md) and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## License
MIT — see [LICENSE](LICENSE).
