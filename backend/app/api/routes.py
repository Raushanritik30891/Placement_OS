from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.entities import Problem, Submission
from app.schemas.problem import ProblemRead, SubmissionCreate, SubmissionRead

router = APIRouter()


@router.get("/problems", response_model=list[ProblemRead])
def list_problems(
    difficulty: str | None = None,
    topic_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = select(Problem).where(Problem.is_published.is_(True))
    if difficulty:
        query = query.where(Problem.difficulty == difficulty)
    if topic_id:
        query = query.where(Problem.topic_id == topic_id)
    return list(db.scalars(query.order_by(Problem.id)).all())


@router.get("/problems/{problem_id}", response_model=ProblemRead)
def get_problem(problem_id: int, db: Session = Depends(get_db)):
    problem = db.get(Problem, problem_id)
    if not problem or not problem.is_published:
        raise HTTPException(status_code=404, detail="Problem not found")
    return problem


@router.post("/submissions", response_model=SubmissionRead, status_code=202)
def create_submission(payload: SubmissionCreate, db: Session = Depends(get_db)):
    problem = db.get(Problem, payload.problem_id)
    if not problem or not problem.is_published:
        raise HTTPException(status_code=404, detail="Problem not found")
    # Records an attempt only. The secure Judge0 worker pipeline is not
    # wired into this synchronous endpoint yet; verdict is not authoritative.
    submission = Submission(
        problem_id=payload.problem_id,
        language=payload.language,
        source_code=payload.source_code,
        verdict="queued",
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission
