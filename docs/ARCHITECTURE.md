# PlacementOS Architecture

## Current foundation
- Frontend: React, TypeScript and Vite.
- Backend: FastAPI with Pydantic schemas.
- Persistence: SQLAlchemy; SQLite for local development, PostgreSQL intended for shared/production data.
- Code execution: Judge0 adapter boundary. A separately operated hardened sandbox is required before accepting untrusted code.
- Local orchestration: Docker Compose.

## Logical modules
Identity and roles; curriculum/topics/lessons; DSA problems and tags; test cases and submissions; Python and data-library exercises; SQL practice and isolated SQL playground; aptitude/reasoning; employer profiles and source-backed mappings; study plans and progress; measured readiness analytics; admin content management and audit trail.

## Security boundaries
- Never expose hidden test cases through student-facing APIs.
- Never execute submitted code inside the FastAPI process.
- Configure Judge0 with network disabled by default, strict resource/time/process limits, non-root execution and ephemeral isolated storage.
- Store secrets in environment variables or a production secret manager.
- Enforce server-side authorization for admin actions and hidden test access.
- Add validation, rate limits, quotas, audit logs and secure auth before public launch.

## Data direction
Expand the starter SQLAlchemy model through reviewed migrations. Add indexes, foreign keys and constraints around user, problem, submission and assessment relationships.

## Deployment direction
Use PostgreSQL for shared data. Isolate the judge service from application credentials and public ingress. Add TLS, backups, health checks, structured logs and monitoring before production.
