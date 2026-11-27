"""Create PlacementOS tables and backfill columns added after the initial starter release.

The migration is intentionally idempotent for the first public development schema:
new databases are created from current metadata, while existing starter databases
receive only the missing columns without dropping user data.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0001_placementos_schema"
down_revision = None
branch_labels = None
depends_on = None


def _add_missing_columns(table_name: str, columns: list[sa.Column]) -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if table_name not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns(table_name)}
    for column in columns:
        if column.name not in existing:
            op.add_column(table_name, column)


def upgrade() -> None:
    # Create all tables introduced after the first starter schema. create_all
    # does not alter existing tables, so legacy table additions are handled below.
    from app.core.database import Base
    from app.models import entities  # noqa: F401 - register all model metadata

    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)

    _add_missing_columns("problems", [
        sa.Column("constraints", sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.Column("input_format", sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.Column("output_format", sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.Column("samples", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("starter_code", sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.Column("hints", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("explanation", sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.Column("time_complexity", sa.String(length=80), nullable=False, server_default=sa.text("''")),
        sa.Column("space_complexity", sa.String(length=80), nullable=False, server_default=sa.text("''")),
        sa.Column("secondary_topics", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("company_tags", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
    ])

    # Legacy submissions predate authentication. Preserve existing rows with
    # a nullable owner; all new submissions are created with a real user_id.
    _add_missing_columns("submissions", [
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("passed_tests", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tests", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("execution_time_ms", sa.Integer(), nullable=True),
        sa.Column("stdout", sa.Text(), nullable=True),
        sa.Column("stderr", sa.Text(), nullable=True),
    ])

    _add_missing_columns("study_tasks", [
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("study_plans.id"), nullable=True),
        sa.Column("day_number", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.Column("estimated_minutes", sa.Integer(), nullable=False, server_default="30"),
    ])

    inspector = inspect(bind)
    if "study_tasks" in inspector.get_table_names():
        task_indexes = {index["name"] for index in inspector.get_indexes("study_tasks")}
        if "ix_study_tasks_plan_id" not in task_indexes:
            op.create_index("ix_study_tasks_plan_id", "study_tasks", ["plan_id"], unique=False)
    if "submissions" in inspector.get_table_names():
        indexes = {index["name"] for index in inspector.get_indexes("submissions")}
        if "ix_submissions_user_id" not in indexes:
            op.create_index("ix_submissions_user_id", "submissions", ["user_id"], unique=False)


def downgrade() -> None:
    # This bootstrap migration may attach new tables to a database containing
    # user data. Automatic destructive downgrade is intentionally unsupported.
    pass
