"""Add study plan, activity timestamp and employer research schema.

This revision is safe for databases that have already recorded the initial
bootstrap migration before these newer models/columns were introduced.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0002_studyplan_company_research"
down_revision = "0001_placementos_schema"
branch_labels = None
depends_on = None


def _create_missing_model_tables() -> None:
    from app.models.entities import CompanyProfile, CompanyResearchSource, StudyPlan

    bind = op.get_bind()
    for model in (StudyPlan, CompanyProfile, CompanyResearchSource):
        model.__table__.create(bind=bind, checkfirst=True)


def _add_missing_study_task_columns() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "study_tasks" not in inspector.get_table_names():
        from app.models.entities import StudyTask
        StudyTask.__table__.create(bind=bind, checkfirst=True)
        return

    existing = {column["name"] for column in inspector.get_columns("study_tasks")}
    missing = []
    candidates = [
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("study_plans.id"), nullable=True),
        sa.Column("day_number", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.Column("estimated_minutes", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    ]
    missing = [column for column in candidates if column.name not in existing]
    if missing:
        if bind.dialect.name == "sqlite":
            with op.batch_alter_table("study_tasks", recreate="always") as batch:
                for column in missing:
                    batch.add_column(column)
        else:
            for column in missing:
                op.add_column("study_tasks", column)

    inspector = inspect(bind)
    indexes = {index["name"] for index in inspector.get_indexes("study_tasks")}
    if "ix_study_tasks_plan_id" not in indexes:
        op.create_index("ix_study_tasks_plan_id", "study_tasks", ["plan_id"], unique=False)


def upgrade() -> None:
    _create_missing_model_tables()
    _add_missing_study_task_columns()


def downgrade() -> None:
    # Preserve user plans, completion activity and company evidence on downgrade.
    pass
