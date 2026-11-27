from pydantic import BaseModel, Field


class ProblemRead(BaseModel):
    id: int
    title: str
    slug: str
    statement: str
    difficulty: str
    topic_id: int | None = None

    model_config = {"from_attributes": True}


class SubmissionCreate(BaseModel):
    problem_id: int
    language: str = "python"
    source_code: str = Field(min_length=1, max_length=100_000)


class SubmissionRead(BaseModel):
    id: int
    problem_id: int
    language: str
    verdict: str

    model_config = {"from_attributes": True}
