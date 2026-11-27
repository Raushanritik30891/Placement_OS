from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.entities import (
    CodeExecutionLog, Problem, ProblemTestCase, QuizAttempt, QuizQuestion, StudyTask,
    Submission, Topic, User, UserProblemProgress,
)
from app.schemas.problem import (
    ProblemRead, ProgressUpdate, QuizSubmit, StudyTaskCreate, StudyTaskUpdate,
    SubmissionCreate, SubmissionRead,
)
from app.services.judge import JudgeUnavailable, execute_python
from app.services.sql_sandbox import execute_readonly_query

router = APIRouter()


class SqlQuery(BaseModel):
    query: str = Field(min_length=1, max_length=4000)


class AdminProblemCreate(BaseModel):
    title: str = Field(min_length=3, max_length=180)
    slug: str = Field(min_length=3, max_length=200, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    statement: str = Field(min_length=10)
    difficulty: str = Field(pattern="^(easy|medium|hard)$")
    topic_id: int | None = None
    constraints: str = ""
    input_format: str = ""
    output_format: str = ""
    samples: list[dict] = Field(default_factory=list)
    starter_code: str = "def solve():\n    pass"
    hints: list[str] = Field(default_factory=list)
    explanation: str = ""
    time_complexity: str = ""
    space_complexity: str = ""
    secondary_topics: list[str] = Field(default_factory=list)
    company_tags: list[str] = Field(default_factory=list)
    is_published: bool = False


class AdminTestCaseCreate(BaseModel):
    stdin: str
    expected_output: str
    is_sample: bool = False


@router.get("/overview", tags=["dashboard"])
def overview(db: Session = Depends(get_db)):
    return {
        "published_problems": db.scalar(select(func.count()).select_from(Problem).where(Problem.is_published.is_(True))) or 0,
        "topics": db.scalar(select(func.count()).select_from(Topic)) or 0,
        "assessment_questions": db.scalar(select(func.count()).select_from(QuizQuestion).where(QuizQuestion.is_published.is_(True))) or 0,
        "registered_users": db.scalar(select(func.count()).select_from(User).where(User.is_active.is_(True))) or 0,
        "features": {
            "authentication": True,
            "problem_catalogue": True,
            "read_only_sql_playground": True,
            "quiz_engine": True,
            "study_planner": True,
            "secure_code_execution": bool(settings.judge0_base_url and settings.judge0_secure_deployment_confirmed),
        },
    }


@router.get("/topics", tags=["curriculum"])
def list_topics(db: Session = Depends(get_db)):
    topics = db.scalars(select(Topic).order_by(Topic.name)).all()
    return [{"id": t.id, "name": t.name, "slug": t.slug, "description": t.description} for t in topics]


@router.get("/problems", response_model=list[ProblemRead], tags=["DSA"])
def list_problems(
    q: str | None = Query(default=None, max_length=100),
    difficulty: str | None = Query(default=None, pattern="^(easy|medium|hard)$"),
    topic_id: int | None = None,
    company: str | None = Query(default=None, max_length=80),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = select(Problem).where(Problem.is_published.is_(True))
    if difficulty:
        query = query.where(Problem.difficulty == difficulty)
    if topic_id:
        query = query.where(Problem.topic_id == topic_id)
    if q:
        needle = f"%{q.strip()}%"
        query = query.where((Problem.title.ilike(needle)) | (Problem.statement.ilike(needle)))
    problems = list(db.scalars(query.order_by(Problem.id).offset(offset).limit(limit)).all())
    if company:
        term = company.casefold()
        problems = [p for p in problems if any(term in tag.casefold() for tag in (p.company_tags or []))]
    return problems


@router.get("/problems/{problem_id}", response_model=ProblemRead, tags=["DSA"])
def get_problem(problem_id: int, db: Session = Depends(get_db)):
    problem = db.get(Problem, problem_id)
    if not problem or not problem.is_published:
        raise HTTPException(status_code=404, detail="Problem not found")
    return problem


@router.post("/submissions", response_model=SubmissionRead, status_code=202, tags=["coding judge"])
async def create_submission(
    payload: SubmissionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    problem = db.get(Problem, payload.problem_id)
    if not problem or not problem.is_published:
        raise HTTPException(status_code=404, detail="Problem not found")

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=1)
    recent = db.scalar(
        select(func.count()).select_from(Submission).where(
            Submission.user_id == user.id, Submission.created_at >= cutoff
        )
    ) or 0
    if recent >= settings.max_submissions_per_minute:
        raise HTTPException(status_code=429, detail="Submission rate limit reached. Try again shortly.")

    if not settings.judge0_base_url or not settings.judge0_secure_deployment_confirmed:
        raise HTTPException(
            status_code=503,
            detail="Code execution is not enabled until a hardened Judge0 deployment is configured and verified.",
        )

    test_cases = db.scalars(
        select(ProblemTestCase).where(ProblemTestCase.problem_id == problem.id).order_by(ProblemTestCase.id)
    ).all()
    if not test_cases:
        raise HTTPException(status_code=409, detail="This problem has no validated server-side test cases yet.")

    passed = 0
    total_time = 0
    first_stderr = ""
    final_verdict = "Accepted"
    for case in test_cases:
        try:
            result = await execute_python(payload.source_code, case.stdin)
        except JudgeUnavailable as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=502, detail="The code execution provider is unavailable.") from exc

        if result.get("time"):
            try:
                total_time += int(float(result["time"]) * 1000)
            except (TypeError, ValueError):
                pass
        if result["status"] != "Accepted":
            final_verdict = result["status"]
            first_stderr = result.get("stderr", "")
            break
        if result.get("stdout", "").replace("\r\n", "\n").rstrip() == case.expected_output.replace("\r\n", "\n").rstrip():
            passed += 1
        else:
            final_verdict = "Wrong Answer"

    if passed == len(test_cases):
        final_verdict = "Accepted"
    submission = Submission(
        user_id=user.id,
        problem_id=problem.id,
        language=payload.language,
        source_code=payload.source_code,
        verdict=final_verdict,
        passed_tests=passed,
        total_tests=len(test_cases),
        execution_time_ms=total_time,
        stderr=first_stderr[:8000] or None,
    )
    db.add(submission)
    progress = db.scalar(
        select(UserProblemProgress).where(
            UserProblemProgress.user_id == user.id,
            UserProblemProgress.problem_id == problem.id,
        )
    )
    if progress is None:
        progress = UserProblemProgress(user_id=user.id, problem_id=problem.id, attempts=0)
        db.add(progress)
    progress.attempts += 1
    if final_verdict == "Accepted":
        progress.status = "solved"
    elif progress.status != "solved":
        progress.status = "attempted"
    db.commit()
    db.refresh(submission)
    return submission


@router.get("/progress", tags=["progress"])
def get_progress(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.execute(
        select(UserProblemProgress, Problem)
        .join(Problem, Problem.id == UserProblemProgress.problem_id)
        .where(UserProblemProgress.user_id == user.id)
        .order_by(UserProblemProgress.updated_at.desc())
    ).all()
    return [{
        "problem_id": progress.problem_id,
        "title": problem.title,
        "status": progress.status,
        "attempts": progress.attempts,
        "updated_at": progress.updated_at,
    } for progress, problem in rows]


@router.post("/progress/{problem_id}", tags=["progress"])
def update_progress(
    problem_id: int,
    payload: ProgressUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    problem = db.get(Problem, problem_id)
    if not problem or not problem.is_published:
        raise HTTPException(status_code=404, detail="Problem not found")
    progress = db.scalar(select(UserProblemProgress).where(
        UserProblemProgress.user_id == user.id, UserProblemProgress.problem_id == problem_id
    ))
    if progress is None:
        progress = UserProblemProgress(user_id=user.id, problem_id=problem_id, attempts=0)
        db.add(progress)
    progress.status = payload.status
    db.commit()
    return {"problem_id": problem_id, "status": progress.status}


@router.post("/sql/execute", tags=["SQL playground"])
def execute_sql(payload: SqlQuery):
    try:
        return execute_readonly_query(payload.query)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/sql/tables", tags=["SQL playground"])
def sql_tables():
    return {
        "tables": [
            {"name": "customers", "columns": ["customer_id", "name", "city"]},
            {"name": "orders", "columns": ["order_id", "customer_id", "order_date", "amount", "status"]},
            {"name": "employees", "columns": ["employee_id", "name", "department_id", "salary", "joining_date"]},
            {"name": "departments", "columns": ["department_id", "department_name"]},
        ]
    }


@router.get("/assessments", tags=["assessments"])
def assessment_categories(db: Session = Depends(get_db)):
    rows = db.execute(
        select(QuizQuestion.category, func.count(QuizQuestion.id))
        .where(QuizQuestion.is_published.is_(True))
        .group_by(QuizQuestion.category)
    ).all()
    return [{"category": category, "question_count": count} for category, count in rows]


@router.get("/assessments/{category}", tags=["assessments"])
def assessment_questions(category: str, db: Session = Depends(get_db)):
    questions = db.scalars(select(QuizQuestion).where(
        QuizQuestion.category == category, QuizQuestion.is_published.is_(True)
    ).order_by(QuizQuestion.id)).all()
    if not questions:
        raise HTTPException(status_code=404, detail="No published questions in this category")
    return [{
        "id": q.id, "category": q.category, "topic": q.topic, "prompt": q.prompt,
        "options": q.options, "difficulty": q.difficulty,
    } for q in questions]


@router.post("/assessments/submit", tags=["assessments"])
def submit_assessment(
    payload: QuizSubmit,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ids = [answer.question_id for answer in payload.answers]
    if len(ids) != len(set(ids)):
        raise HTTPException(status_code=422, detail="Duplicate question answers are not allowed")
    questions = db.scalars(select(QuizQuestion).where(
        QuizQuestion.id.in_(ids),
        QuizQuestion.category == payload.category,
        QuizQuestion.is_published.is_(True),
    )).all()
    if len(questions) != len(ids):
        raise HTTPException(status_code=422, detail="One or more questions are not valid for this assessment")
    by_id = {question.id: question for question in questions}
    results = []
    score = 0
    for answer in payload.answers:
        question = by_id[answer.question_id]
        if answer.selected_index >= len(question.options):
            raise HTTPException(status_code=422, detail="Selected option is out of range")
        is_correct = answer.selected_index == question.correct_index
        score += int(is_correct)
        results.append({
            "question_id": question.id,
            "correct": is_correct,
            "correct_index": question.correct_index,
            "explanation": question.explanation,
        })
    attempt = QuizAttempt(user_id=user.id, category=payload.category, score=score, total=len(ids))
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return {"attempt_id": attempt.id, "score": score, "total": len(ids), "percentage": round(score / len(ids) * 100, 1), "results": results}


@router.get("/study-plan", tags=["study planner"])
def list_study_tasks(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    tasks = db.scalars(select(StudyTask).where(StudyTask.user_id == user.id).order_by(StudyTask.id.desc())).all()
    return [{"id": t.id, "title": t.title, "category": t.category, "due_date": t.due_date, "is_completed": t.is_completed} for t in tasks]


@router.post("/study-plan", status_code=201, tags=["study planner"])
def create_study_task(payload: StudyTaskCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task = StudyTask(user_id=user.id, title=payload.title.strip(), category=payload.category, due_date=payload.due_date)
    db.add(task)
    db.commit()
    db.refresh(task)
    return {"id": task.id, "title": task.title, "category": task.category, "due_date": task.due_date, "is_completed": task.is_completed}


@router.patch("/study-plan/{task_id}", tags=["study planner"])
def update_study_task(task_id: int, payload: StudyTaskUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task = db.scalar(select(StudyTask).where(StudyTask.id == task_id, StudyTask.user_id == user.id))
    if not task:
        raise HTTPException(status_code=404, detail="Study task not found")
    task.is_completed = payload.is_completed
    db.commit()
    return {"id": task.id, "is_completed": task.is_completed}


@router.post("/admin/problems", status_code=201, tags=["admin"])
def admin_create_problem(
    payload: AdminProblemCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    if db.scalar(select(Problem).where(Problem.slug == payload.slug)):
        raise HTTPException(status_code=409, detail="Problem slug already exists")
    if payload.topic_id is not None and not db.get(Topic, payload.topic_id):
        raise HTTPException(status_code=404, detail="Topic not found")
    data = payload.model_dump()
    samples = data.pop("samples")
    for sample in samples:
        if not isinstance(sample, dict) or not isinstance(sample.get("input"), str) or not isinstance(sample.get("output"), str):
            raise HTTPException(status_code=422, detail="Each sample must contain string input and output fields")
    problem = Problem(**data, samples=samples)
    db.add(problem)
    db.flush()
    for sample in samples:
        db.add(ProblemTestCase(
            problem_id=problem.id,
            stdin=sample["input"],
            expected_output=sample["output"],
            is_sample=True,
        ))
    db.commit()
    db.refresh(problem)
    return {"id": problem.id, "slug": problem.slug, "is_published": problem.is_published}


@router.post("/admin/problems/{problem_id}/test-cases", status_code=201, tags=["admin"])
def admin_add_test_case(
    problem_id: int,
    payload: AdminTestCaseCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    problem = db.get(Problem, problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    case = ProblemTestCase(problem_id=problem_id, **payload.model_dump())
    db.add(case)
    if payload.is_sample:
        samples = list(problem.samples or [])
        samples.append({"input": payload.stdin, "output": payload.expected_output, "explanation": ""})
        problem.samples = samples
    db.commit()
    return {"id": case.id, "problem_id": problem_id, "is_sample": case.is_sample}

class CodeRunRequest(BaseModel):
    source_code: str = Field(min_length=1, max_length=100_000)
    stdin: str = Field(default="", max_length=20_000)


@router.post("/code/run", tags=["coding judge"])
async def run_custom_code(
    payload: CodeRunRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=1)
    recent = db.scalar(
        select(func.count()).select_from(CodeExecutionLog).where(
            CodeExecutionLog.user_id == user.id, CodeExecutionLog.created_at >= cutoff
        )
    ) or 0
    if recent >= settings.max_submissions_per_minute:
        raise HTTPException(status_code=429, detail="Execution rate limit reached. Try again shortly.")
    if not settings.judge0_base_url or not settings.judge0_secure_deployment_confirmed:
        db.add(CodeExecutionLog(user_id=user.id, status="disabled"))
        db.commit()
        raise HTTPException(
            status_code=503,
            detail="Code execution is disabled until a hardened Judge0 deployment is configured and verified.",
        )
    execution = CodeExecutionLog(user_id=user.id, status="running")
    db.add(execution)
    db.commit()
    try:
        result = await execute_python(payload.source_code, payload.stdin)
    except JudgeUnavailable as exc:
        execution.status = "provider_error"
        db.commit()
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        execution.status = "provider_error"
        db.commit()
        raise HTTPException(status_code=502, detail="The code execution provider is unavailable.") from exc
    execution.status = (result.get("status") or "unknown")[:40]
    db.commit()
    return {
        "status": result["status"],
        "stdout": result["stdout"],
        "stderr": result["stderr"],
        "execution_time": result["time"],
        "memory": result["memory"],
    }


class AdminTopicCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    slug: str = Field(min_length=2, max_length=120, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str = Field(default="", max_length=2000)


class ProblemPublishUpdate(BaseModel):
    is_published: bool


@router.get("/progress/summary", tags=["progress"])
def progress_summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    published = db.scalar(select(func.count()).select_from(Problem).where(Problem.is_published.is_(True))) or 0
    solved = db.scalar(select(func.count()).select_from(UserProblemProgress).where(
        UserProblemProgress.user_id == user.id, UserProblemProgress.status == "solved"
    )) or 0
    attempted = db.scalar(select(func.count()).select_from(UserProblemProgress).where(
        UserProblemProgress.user_id == user.id
    )) or 0
    submissions = db.scalar(select(func.count()).select_from(Submission).where(Submission.user_id == user.id)) or 0
    accepted = db.scalar(select(func.count()).select_from(Submission).where(
        Submission.user_id == user.id, Submission.verdict == "Accepted"
    )) or 0
    quiz_rows = db.execute(select(QuizAttempt.score, QuizAttempt.total).where(QuizAttempt.user_id == user.id)).all()
    quiz_total = sum(row.total for row in quiz_rows)
    quiz_score = sum(row.score for row in quiz_rows)
    quiz_accuracy = round(quiz_score / quiz_total * 100, 1) if quiz_total else None
    return {
        "published_problems": published,
        "solved_problems": solved,
        "attempted_problems": attempted,
        "remaining_problems": max(published - solved, 0),
        "submissions": submissions,
        "accepted_submissions": accepted,
        "accepted_rate": round(accepted / submissions * 100, 1) if submissions else None,
        "quiz_questions_answered": quiz_total,
        "quiz_accuracy": quiz_accuracy,
        "readiness_score": None,
        "readiness_note": "A readiness score is withheld until there are enough timed assessments and verified coding submissions to make it meaningful.",
    }


@router.get("/submissions/history", tags=["coding judge"])
def submission_history(
    limit: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rows = db.execute(
        select(Submission, Problem.title)
        .join(Problem, Problem.id == Submission.problem_id)
        .where(Submission.user_id == user.id)
        .order_by(Submission.created_at.desc())
        .limit(limit)
    ).all()
    return [{
        "id": submission.id,
        "problem_id": submission.problem_id,
        "problem_title": title,
        "verdict": submission.verdict,
        "passed_tests": submission.passed_tests,
        "total_tests": submission.total_tests,
        "execution_time_ms": submission.execution_time_ms,
        "created_at": submission.created_at,
    } for submission, title in rows]


@router.post("/admin/topics", status_code=201, tags=["admin"])
def admin_create_topic(
    payload: AdminTopicCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    if db.scalar(select(Topic).where((Topic.slug == payload.slug) | (Topic.name == payload.name))):
        raise HTTPException(status_code=409, detail="Topic name or slug already exists")
    topic = Topic(**payload.model_dump())
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return {"id": topic.id, "name": topic.name, "slug": topic.slug}


@router.patch("/admin/problems/{problem_id}/publish", tags=["admin"])
def admin_publish_problem(
    problem_id: int,
    payload: ProblemPublishUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    problem = db.get(Problem, problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    if payload.is_published:
        cases = db.scalars(select(ProblemTestCase).where(ProblemTestCase.problem_id == problem_id)).all()
        public_samples = sum(1 for case in cases if case.is_sample)
        hidden_cases = sum(1 for case in cases if not case.is_sample)
        if public_samples < 2 or hidden_cases < 1:
            raise HTTPException(
                status_code=409,
                detail="A problem needs at least two public sample tests and one hidden test case before publishing.",
            )
    problem.is_published = payload.is_published
    db.commit()
    return {"id": problem.id, "is_published": problem.is_published}
