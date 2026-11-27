from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


def test_legacy_database_upgrades_to_current_schema(tmp_path, monkeypatch):
    from app.core.config import settings

    database_path = tmp_path / "legacy-placementos.sqlite3"
    database_url = f"sqlite:///{database_path}"
    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY
            )
        """))
        connection.execute(text("""
            CREATE TABLE study_tasks (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                title VARCHAR(180) NOT NULL,
                category VARCHAR(60) NOT NULL DEFAULT 'general',
                due_date VARCHAR(10),
                is_completed BOOLEAN NOT NULL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """))
        connection.execute(text("INSERT INTO users (id) VALUES (1)"))
        connection.execute(text("""
            INSERT INTO study_tasks (id, user_id, title, category, due_date, is_completed)
            VALUES (1, 1, 'Legacy task', 'DSA', '2026-11-01', 0)
        """))
        connection.execute(text("""
            CREATE TABLE alembic_version (
                version_num VARCHAR(32) NOT NULL
            )
        """))
        connection.execute(
            text("INSERT INTO alembic_version (version_num) VALUES (:revision)"),
            {"revision": "0001_placementos_schema"},
        )

    monkeypatch.setattr(settings, "database_url", database_url)
    backend_dir = Path(__file__).resolve().parents[1]
    config = Config(str(backend_dir / "alembic.ini"))
    config.set_main_option("script_location", str(backend_dir / "migrations"))
    command.upgrade(config, "head")

    inspector = inspect(engine)
    task_columns = {column["name"] for column in inspector.get_columns("study_tasks")}
    assert {"plan_id", "day_number", "description", "estimated_minutes", "completed_at"} <= task_columns
    tables = set(inspector.get_table_names())
    assert {"study_plans", "company_profiles", "company_research_sources"} <= tables

    with engine.connect() as connection:
        revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        legacy_task = connection.execute(
            text("SELECT id, title, plan_id, completed_at FROM study_tasks WHERE id = 1")
        ).one()
    assert revision == "0002_studyplan_company_research"
    assert legacy_task.id == 1
    assert legacy_task.title == "Legacy task"
    assert legacy_task.plan_id is None
    assert legacy_task.completed_at is None
    engine.dispose()
