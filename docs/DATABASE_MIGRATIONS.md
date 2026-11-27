# Database migrations

PlacementOS uses Alembic for versioned schema changes. Production startup refuses to run if the database has no Alembic version table; this prevents an old schema from silently being treated as current.

## Local development

From the backend directory:

```bash
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python -m app.seed
python -m app.curriculum_seed
python -m app.sql_seed
uvicorn app.main:app --reload
```

Development may use `AUTO_CREATE_TABLES=true` to create tables for a fresh local database. It does not replace migrations: after upgrading the application, run `alembic upgrade head` to apply new schema revisions.

## Existing starter database

1. Stop the backend and make a database backup.
2. Confirm `DATABASE_URL` points to the intended database.
3. From the backend directory, run `alembic upgrade head`.
4. Start the backend and verify `/health` and the application data.

The bootstrap migration creates the original application schema and adds columns missing from the earliest starter schema. Revision 0002 adds study-plan completion metadata and employer research tables for databases that had already applied revision 0001. The revisions do not intentionally drop user content. Legacy submissions created before accounts existed retain a nullable user association; new submissions are associated with an authenticated user.

## Production

Set `ENVIRONMENT=production` and `AUTO_CREATE_TABLES=false`. Apply migrations as a release step before starting API instances:

```bash
cd backend
alembic upgrade head
```

Do not run migrations concurrently from every web worker. Use a single deployment job with the least-privileged database credential that can apply the migration. Back up the database before schema changes and test the migration against a production-like copy.

## Adding a migration

After changing SQLAlchemy models:

```bash
cd backend
alembic revision --autogenerate -m "describe schema change"
```

Review the generated migration manually, especially constraints, JSON defaults, nullable transitions, indexes and SQLite batch operations. Test both an empty database and an upgraded copy of the previous schema before merging.
