"""Seed a tiny starter catalogue for local development only."""
from sqlalchemy import select

from app.core.database import Base, SessionLocal, engine
from app.models.entities import Problem, Topic

STARTER_PROBLEMS = [
    {
        "title": "Two Sum",
        "slug": "two-sum",
        "statement": "Given an integer array nums and an integer target, return indices of two distinct elements whose sum equals target.",
        "difficulty": "easy",
    },
    {
        "title": "Valid Palindrome",
        "slug": "valid-palindrome",
        "statement": "Return whether a string is a palindrome when non-alphanumeric characters are ignored and letter case is ignored.",
        "difficulty": "easy",
    },
]


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        topic = db.scalar(select(Topic).where(Topic.slug == "arrays"))
        if topic is None:
            topic = Topic(name="Arrays", slug="arrays", description="Array fundamentals")
            db.add(topic)
            db.flush()
        for item in STARTER_PROBLEMS:
            exists = db.scalar(select(Problem).where(Problem.slug == item["slug"]))
            if exists is None:
                db.add(Problem(**item, topic_id=topic.id, is_published=True))
        db.commit()


if __name__ == "__main__":
    seed()
