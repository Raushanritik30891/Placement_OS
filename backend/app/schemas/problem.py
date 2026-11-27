from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class SampleCase(BaseModel):
    input: str
    output: str
    explanation: str = ""


class ProblemRead(BaseModel):
    id: int
    title: str
    slug: str
    statement: str
    difficulty: str
    topic_id: int | None = None
    constraints: str = ""
    input_format: str = ""
    output_format: str = ""
    samples: list[SampleCase] = Field(default_factory=list)
    starter_code: str = ""
    hints: list[str] = Field(default_factory=list)
    explanation: str = ""
    time_complexity: str = ""
    space_complexity: str = ""
    secondary_topics: list[str] = Field(default_factory=list)
    company_tags: list[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class SubmissionCreate(BaseModel):
    problem_id: int
    language: str = Field(default="python", pattern="^python$")
    source_code: str = Field(min_length=1, max_length=100_000)


class SubmissionRead(BaseModel):
    id: int
    problem_id: int
    language: str
    verdict: str
    passed_tests: int
    total_tests: int
    execution_time_ms: int | None = None

    model_config = {"from_attributes": True}


class ProgressUpdate(BaseModel):
    status: str = Field(pattern="^(attempted|solved|review)$")


class QuizAnswer(BaseModel):
    question_id: int
    selected_index: int = Field(ge=0)


class QuizSubmit(BaseModel):
    category: str
    answers: list[QuizAnswer] = Field(min_length=1, max_length=100)


class StudyTaskCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    category: str = Field(default="general", max_length=50)
    due_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")


class StudyTaskUpdate(BaseModel):
    is_completed: bool


class QuizSessionStart(BaseModel):
    category: str = Field(min_length=2, max_length=40)
    duration_minutes: int = Field(default=20, ge=1, le=180)
    question_limit: int = Field(default=20, ge=1, le=100)


class QuizSessionAnswers(BaseModel):
    answers: list[QuizAnswer] = Field(default_factory=list, max_length=100)


class StudyPlanGenerate(BaseModel):
    duration_days: Literal[30, 45, 60] = 30
    target_role: Literal["general", "software_engineer", "data_engineer", "ai_ml"] = "general"
    target_company: str = Field(default="", max_length=100)
    daily_hours: int = Field(default=3, ge=1, le=12)
    skill_level: Literal["beginner", "intermediate"] = "beginner"
    start_date: date = Field(default_factory=date.today)


class CompanyResearchSourceCreate(BaseModel):
    title: str = Field(min_length=3, max_length=240)
    url: str = Field(min_length=12, max_length=1000, pattern=r"^https://")
    evidence_type: Literal["official", "candidate_report", "practice_pattern", "original_problem"]
    claim: str = Field(min_length=10, max_length=5000)
    confidence: Literal["high", "medium", "low"] = "medium"


class CompanyResearchReviewUpdate(BaseModel):
    research_status: Literal["pending", "reviewed"]
