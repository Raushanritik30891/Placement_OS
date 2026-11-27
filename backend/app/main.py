from contextlib import asynccontextmanager
from pathlib import Path

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect

from app.api.auth import router as auth_router
from app.api.routes import router
from app.core.config import settings
from app.core.database import Base, engine
from app.models import entities  # noqa: F401 - registers all metadata models


@asynccontextmanager
async def lifespan(_: FastAPI):
    # create_all is suitable for a fresh local install. Use reviewed migrations
    # for schema changes in an existing production database.
    if settings.environment.lower() == "production":
        if "alembic_version" not in inspect(engine).get_table_names():
            raise RuntimeError("Database migrations are missing. Run 'alembic upgrade head' before starting PlacementOS.")
        backend_dir = Path(__file__).resolve().parents[1]
        alembic_config = Config(str(backend_dir / "alembic.ini"))
        script_directory = ScriptDirectory.from_config(alembic_config)
        with engine.connect() as connection:
            current_revision = MigrationContext.configure(connection).get_current_revision()
        expected_revision = script_directory.get_current_head()
        if current_revision != expected_revision:
            raise RuntimeError(
                f"Database revision {current_revision!r} does not match application head "
                f"{expected_revision!r}. Run 'alembic upgrade head' before starting PlacementOS."
            )
    elif settings.auto_create_tables:
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description="Placement preparation, practice and assessment platform.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(auth_router, prefix="/api")
app.include_router(router, prefix="/api")


@app.get("/health", tags=["operations"])
def health():
    from sqlalchemy import text
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ok", "service": settings.app_name, "version": "0.2.0"}
