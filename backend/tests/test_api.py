def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_problem_list_is_empty_until_seeded(client):
    response = client.get("/api/problems")
    assert response.status_code == 200
    assert response.json() == []


def register_student(client, email="student@example.com"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "display_name": "Test Student",
            "password": "strong-test-password-2026",
        },
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def test_registration_returns_student_token_and_me(client):
    token = register_student(client)
    me = client.get("/api/auth/me", headers={"Authorization": "Bearer " + token})
    assert me.status_code == 200
    assert me.json()["email"] == "student@example.com"
    assert me.json()["role"] == "student"
    assert "password_hash" not in me.json()


def test_duplicate_registration_is_rejected(client):
    payload = {
        "email": "duplicate@example.com",
        "display_name": "Test Student",
        "password": "strong-test-password-2026",
    }
    assert client.post("/api/auth/register", json=payload).status_code == 201
    assert client.post("/api/auth/register", json=payload).status_code == 409


def test_protected_progress_requires_authentication(client):
    assert client.get("/api/progress").status_code == 401


def test_sql_playground_allows_select(client):
    response = client.post(
        "/api/sql/execute",
        json={"query": "SELECT name, city FROM customers ORDER BY customer_id LIMIT 2"},
    )
    assert response.status_code == 200
    assert response.json()["columns"] == ["name", "city"]
    assert response.json()["rows"] == [["Aarav", "Delhi"], ["Diya", "Pune"]]
    assert response.json()["read_only"] is True


def test_sql_playground_allows_read_only_cte(client):
    response = client.post(
        "/api/sql/execute",
        json={"query": "WITH sample AS (SELECT 7 AS value) SELECT value FROM sample"},
    )
    assert response.status_code == 200
    assert response.json()["rows"] == [[7]]


def test_sql_playground_blocks_mutations(client):
    response = client.post("/api/sql/execute", json={"query": "DELETE FROM customers"})
    assert response.status_code == 400


def test_sql_playground_blocks_multi_statement(client):
    response = client.post(
        "/api/sql/execute",
        json={"query": "SELECT 1; DROP TABLE customers"},
    )
    assert response.status_code == 400


def test_sql_playground_bounds_large_sql_values(client):
    response = client.post(
        "/api/sql/execute",
        json={"query": "SELECT length(randomblob(1000000))"},
    )
    assert response.status_code == 400


def test_submission_requires_authentication(client):
    response = client.post(
        "/api/submissions",
        json={"problem_id": 1, "language": "python", "source_code": "print('hello')"},
    )
    assert response.status_code == 401


def test_custom_code_runner_requires_authentication(client):
    response = client.post(
        "/api/code/run",
        json={"source_code": "print('hello')", "stdin": ""},
    )
    assert response.status_code == 401


def test_custom_code_runner_stays_disabled_without_verified_judge(client):
    token = register_student(client)
    response = client.post(
        "/api/code/run",
        headers={"Authorization": "Bearer " + token},
        json={"source_code": "print('hello')", "stdin": ""},
    )
    assert response.status_code == 503
    assert "hardened Judge0" in response.json()["detail"]


def test_regular_student_cannot_access_admin_routes(client):
    token = register_student(client)
    response = client.post(
        "/api/admin/topics",
        headers={"Authorization": "Bearer " + token},
        json={"name": "Restricted", "slug": "restricted"},
    )
    assert response.status_code == 403


def test_study_tasks_are_persisted_for_current_user(client):
    token = register_student(client)
    headers = {"Authorization": "Bearer " + token}
    created = client.post(
        "/api/study-plan",
        headers=headers,
        json={"title": "Revise SQL joins", "category": "SQL"},
    )
    assert created.status_code == 201
    task_id = created.json()["id"]
    listed = client.get("/api/study-plan", headers=headers)
    assert any(task["id"] == task_id for task in listed.json())
    updated = client.patch(
        "/api/study-plan/" + str(task_id),
        headers=headers,
        json={"is_completed": True},
    )
    assert updated.status_code == 200
    assert updated.json()["is_completed"] is True


def test_dashboard_metrics_are_database_backed(client):
    response = client.get("/api/overview")
    assert response.status_code == 200
    body = response.json()
    assert body["published_problems"] == 0
    assert body["assessment_questions"] == 0
    assert body["features"]["secure_code_execution"] is False


def test_personal_analytics_requires_authentication(client):
    response = client.get("/api/progress/summary")
    assert response.status_code == 401


def test_courses_lessons_and_completion_progress_are_persisted(client):
    from app.models.entities import Course, Lesson

    token = register_student(client, "learner@example.com")
    session = client.app.state.testing_session()
    course = Course(
        title="Test Python Course",
        slug="test-python-course",
        category="python",
        description="A course used in the API test.",
        difficulty="beginner",
    )
    session.add(course)
    session.flush()
    lesson = Lesson(
        course_id=course.id,
        title="Test Lesson",
        slug="test-lesson",
        content="## Lesson\n\nA short test lesson.",
        estimated_minutes=5,
        display_order=1,
        is_published=True,
    )
    session.add(lesson)
    session.commit()
    course_id = course.id
    lesson_id = lesson.id
    session.close()

    courses = client.get("/api/courses")
    assert courses.status_code == 200
    assert any(item["slug"] == "test-python-course" for item in courses.json())

    detail = client.get("/api/courses/test-python-course")
    assert detail.status_code == 200
    assert detail.json()["lessons"][0]["content"].startswith("## Lesson")

    headers = {"Authorization": "Bearer " + token}
    complete = client.post("/api/lessons/" + str(lesson_id) + "/complete", headers=headers)
    assert complete.status_code == 200
    assert complete.json()["is_completed"] is True

    progress = client.get("/api/learning-progress", headers=headers)
    result = next(item for item in progress.json() if item["course_id"] == course_id)
    assert result["completed_lessons"] == 1
    assert result["total_lessons"] == 1
    assert result["percentage"] == 100.0


def test_quiz_answers_are_hidden_until_server_side_submission(client):
    from app.models.entities import QuizQuestion

    session = client.app.state.testing_session()
    session.add(QuizQuestion(
        category="python",
        topic="Testing",
        prompt="Which built-in type is immutable?",
        options=["list", "dict", "tuple", "set"],
        correct_index=2,
        explanation="A tuple is immutable.",
        difficulty="easy",
        is_published=True,
    ))
    session.commit()
    question_id = session.query(QuizQuestion).filter_by(topic="Testing").one().id
    session.close()

    public_questions = client.get("/api/assessments/python")
    assert public_questions.status_code == 200
    assert public_questions.json()[0]["id"] == question_id
    assert "correct_index" not in public_questions.json()[0]

    token = register_student(client, "quiz-user@example.com")
    result = client.post(
        "/api/assessments/submit",
        headers={"Authorization": "Bearer " + token},
        json={"category": "python", "answers": [{"question_id": question_id, "selected_index": 2}]},
    )
    assert result.status_code == 200
    assert result.json()["score"] == 1
    assert result.json()["percentage"] == 100.0
    assert result.json()["results"][0]["correct"] is True
    assert result.json()["results"][0]["explanation"] == "A tuple is immutable."


def test_timed_assessment_session_is_server_graded_and_single_use(client):
    from datetime import datetime
    from app.models.entities import QuizQuestion

    session_db = client.app.state.testing_session()
    session_db.add_all([
        QuizQuestion(
            category="timed-test",
            topic="Basics",
            prompt="What is 2 + 2?",
            options=["3", "4", "5"],
            correct_index=1,
            explanation="Two plus two equals four.",
            difficulty="easy",
            is_published=True,
        ),
        QuizQuestion(
            category="timed-test",
            topic="Arithmetic",
            prompt="What is 5 - 1?",
            options=["3", "4", "5"],
            correct_index=1,
            explanation="Five minus one equals four.",
            difficulty="easy",
            is_published=True,
        ),
    ])
    session_db.commit()
    session_db.close()

    token = register_student(client, "timed-user@example.com")
    headers = {"Authorization": "Bearer " + token}
    started = client.post(
        "/api/assessments/start",
        headers=headers,
        json={"category": "timed-test", "duration_minutes": 5, "question_limit": 2},
    )
    assert started.status_code == 201
    body = started.json()
    assert body["total"] == 2
    assert datetime.fromisoformat(body["ends_at"]).tzinfo is not None
    assert "correct_index" not in body["questions"][0]

    question_id = next(question["id"] for question in body["questions"] if question["prompt"] == "What is 2 + 2?")
    submitted = client.post(
        "/api/assessments/sessions/" + str(body["session_id"]) + "/submit",
        headers=headers,
        json={"answers": [{"question_id": question_id, "selected_index": 1}]},
    )
    assert submitted.status_code == 200
    assert submitted.json()["score"] == 1
    assert submitted.json()["total"] == 2
    assert submitted.json()["percentage"] == 50.0
    assert sum(1 for result in submitted.json()["results"] if not result["correct"]) == 1

    repeated = client.post(
        "/api/assessments/sessions/" + str(body["session_id"]) + "/submit",
        headers=headers,
        json={"answers": [{"question_id": question_id, "selected_index": 1}]},
    )
    assert repeated.status_code == 409


def test_sql_playground_serializes_binary_and_non_finite_values(client):
    response = client.post(
        "/api/sql/execute",
        json={"query": "SELECT zeroblob(4) AS binary_value, 1e999 AS infinite_value"},
    )
    assert response.status_code == 200
    assert response.json()["rows"] == [["hex:00000000", "inf"]]


def test_sql_challenge_grading_keeps_reference_query_private_and_tracks_attempts(client):
    from app.models.entities import SQLProblem

    session = client.app.state.testing_session()
    session.add(SQLProblem(
        title="Customer directory",
        slug="test-customer-directory",
        prompt="Return customer name and city sorted by name.",
        topic="SELECT",
        difficulty="easy",
        reference_query="SELECT name, city FROM customers ORDER BY name, customer_id;",
        explanation="Select the requested columns and sort by name.",
        is_published=True,
    ))
    session.commit()
    problem_id = session.query(SQLProblem).filter_by(slug="test-customer-directory").one().id
    session.close()

    listing = client.get("/api/sql/problems")
    assert listing.status_code == 200
    public_problem = next(item for item in listing.json() if item["id"] == problem_id)
    assert "reference_query" not in public_problem

    assert client.post(
        "/api/sql/problems/" + str(problem_id) + "/submit",
        json={"query": "SELECT name, city FROM customers ORDER BY name, customer_id"},
    ).status_code == 401

    token = register_student(client, "sql-learner@example.com")
    headers = {"Authorization": "Bearer " + token}
    accepted = client.post(
        "/api/sql/problems/" + str(problem_id) + "/submit",
        headers=headers,
        json={"query": "SELECT name, city FROM customers ORDER BY name, customer_id"},
    )
    assert accepted.status_code == 200
    assert accepted.json()["verdict"] == "Accepted"

    wrong = client.post(
        "/api/sql/problems/" + str(problem_id) + "/submit",
        headers=headers,
        json={"query": "SELECT name FROM customers ORDER BY name"},
    )
    assert wrong.status_code == 200
    assert wrong.json()["verdict"] == "Wrong Answer"

    progress = client.get("/api/sql/progress", headers=headers)
    assert progress.status_code == 200
    assert progress.json()["total_submissions"] == 2
    assert progress.json()["accepted_submissions"] == 1
    assert progress.json()["solved_challenges"] == 1


def test_admin_must_add_hidden_tests_before_publishing_problem(client):
    from app.models.entities import User

    token = register_student(client, "content-admin@example.com")
    session = client.app.state.testing_session()
    account = session.query(User).filter_by(email="content-admin@example.com").one()
    account.role = "admin"
    session.commit()
    session.close()
    headers = {"Authorization": "Bearer " + token}

    created = client.post(
        "/api/admin/problems",
        headers=headers,
        json={
            "title": "Admin Test Problem",
            "slug": "admin-test-problem",
            "statement": "Return the sum of two integer values supplied in JSON.",
            "difficulty": "easy",
            "samples": [
                {"input": "{\"a\":1,\"b\":2}", "output": "3", "explanation": "1 + 2 = 3"},
                {"input": "{\"a\":5,\"b\":7}", "output": "12", "explanation": "5 + 7 = 12"},
            ],
            "starter_code": "print(0)",
            "hints": ["Parse the JSON input."],
            "explanation": "Read both values and add them.",
            "time_complexity": "O(1)",
            "space_complexity": "O(1)",
            "is_published": False,
        },
    )
    assert created.status_code == 201
    problem_id = created.json()["id"]

    public_detail = client.get("/api/problems/" + str(problem_id))
    assert public_detail.status_code == 404

    premature_publish = client.patch(
        "/api/admin/problems/" + str(problem_id) + "/publish",
        headers=headers,
        json={"is_published": True},
    )
    assert premature_publish.status_code == 409

    hidden_case = client.post(
        "/api/admin/problems/" + str(problem_id) + "/test-cases",
        headers=headers,
        json={"stdin": "{\"a\":9,\"b\":8}", "expected_output": "17", "is_sample": False},
    )
    assert hidden_case.status_code == 201

    published = client.patch(
        "/api/admin/problems/" + str(problem_id) + "/publish",
        headers=headers,
        json={"is_published": True},
    )
    assert published.status_code == 200
    assert published.json()["is_published"] is True

    public_detail = client.get("/api/problems/" + str(problem_id))
    assert public_detail.status_code == 200
    assert len(public_detail.json()["samples"]) == 2
    assert "test_cases" not in public_detail.json()


def test_content_seed_modules_import_and_match_documented_starter_counts():
    from app import company_seed, curriculum_seed, seed, sql_seed

    assert len(seed.PROBLEMS) == 36
    assert len(seed.QUIZZES) == 36
    assert len(sql_seed.PROBLEMS) == 30
    assert len(curriculum_seed.COURSES) == 8
    assert len(company_seed.COMPANIES) == 23
    assert sum(len(course["lessons"]) for course in curriculum_seed.COURSES) == 27


def test_personalized_study_plan_generates_saved_daily_tasks(client):
    token = register_student(client, "planner-user@example.com")
    headers = {"Authorization": "Bearer " + token}
    generated = client.post(
        "/api/study-plan/generate",
        headers=headers,
        json={
            "duration_days": 30,
            "target_role": "data_engineer",
            "target_company": "TCS",
            "daily_hours": 3,
            "skill_level": "beginner",
            "start_date": "2026-12-01",
        },
    )
    assert generated.status_code == 201
    body = generated.json()
    assert body["duration_days"] == 30
    assert body["target_role"] == "data_engineer"
    assert body["target_company"] == "TCS"
    assert body["task_count"] == 60

    active = client.get("/api/study-plan/active", headers=headers)
    assert active.status_code == 200
    plan = active.json()
    assert plan["id"] == body["id"]
    assert plan["start_date"] == "2026-12-01"
    assert len(plan["tasks"]) == 60
    assert plan["tasks"][0]["day_number"] == 1
    assert plan["tasks"][0]["estimated_minutes"] == 90
    assert plan["tasks"][0]["due_date"] == "2026-12-01"
    assert all(task["plan_id"] == plan["id"] for task in plan["tasks"])

    listed = client.get("/api/study-plan", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 60
    assert all("description" in task for task in listed.json())


def test_new_generated_study_plan_deactivates_previous_plan(client):
    token = register_student(client, "planner-replace@example.com")
    headers = {"Authorization": "Bearer " + token}
    first = client.post(
        "/api/study-plan/generate",
        headers=headers,
        json={"duration_days": 30, "target_role": "general", "daily_hours": 1, "start_date": "2026-12-01"},
    )
    assert first.status_code == 201
    second = client.post(
        "/api/study-plan/generate",
        headers=headers,
        json={"duration_days": 45, "target_role": "software_engineer", "daily_hours": 1, "start_date": "2026-12-02"},
    )
    assert second.status_code == 201
    active = client.get("/api/study-plan/active", headers=headers)
    assert active.status_code == 200
    assert active.json()["id"] == second.json()["id"]
    assert active.json()["duration_days"] == 45


def test_study_plan_generator_requires_login(client):
    response = client.post(
        "/api/study-plan/generate",
        json={"duration_days": 30, "target_role": "general", "daily_hours": 2},
    )
    assert response.status_code == 401


def test_readiness_index_requires_evidence_and_uses_documented_formula(client):
    from app.models.entities import Problem, QuizAttempt, Submission, User, UserProblemProgress

    token = register_student(client, "readiness@example.com")
    session = client.app.state.testing_session()
    user = session.query(User).filter_by(email="readiness@example.com").one()
    first = Problem(
        title="Readiness Problem One", slug="readiness-one",
        statement="A valid problem statement for testing readiness.",
        difficulty="easy", is_published=True,
    )
    second = Problem(
        title="Readiness Problem Two", slug="readiness-two",
        statement="Another valid problem statement for testing readiness.",
        difficulty="easy", is_published=True,
    )
    session.add_all([first, second])
    session.flush()
    session.add(UserProblemProgress(
        user_id=user.id, problem_id=first.id, status="solved", attempts=1,
    ))
    for index in range(10):
        session.add(Submission(
            user_id=user.id,
            problem_id=first.id,
            language="python",
            source_code="print(1)",
            verdict="Accepted" if index < 8 else "Wrong Answer",
            passed_tests=1 if index < 8 else 0,
            total_tests=1,
        ))
    for score in (8, 9, 7):
        session.add(QuizAttempt(user_id=user.id, category="python", score=score, total=10))
    session.commit()
    session.close()

    response = client.get("/api/progress/summary", headers={"Authorization": "Bearer " + token})
    assert response.status_code == 200
    summary = response.json()
    assert summary["accepted_rate"] == 80.0
    assert summary["dsa_coverage"] == 50.0
    assert summary["quiz_accuracy"] == 80.0
    assert summary["readiness_score"] == 71
    assert "40%" in summary["readiness_note"]
    assert "30%" in summary["readiness_note"]


def test_readiness_index_is_withheld_without_minimum_evidence(client):
    token = register_student(client, "not-ready@example.com")
    response = client.get("/api/progress/summary", headers={"Authorization": "Bearer " + token})
    assert response.status_code == 200
    assert response.json()["readiness_score"] is None
    assert "10 verified coding submissions" in response.json()["readiness_note"]


def test_completed_study_task_updates_streak_and_completion_timestamp(client):
    from datetime import datetime, timezone

    token = register_student(client, "streak@example.com")
    headers = {"Authorization": "Bearer " + token}
    created = client.post(
        "/api/study-plan",
        headers=headers,
        json={"title": "Complete SQL revision", "category": "SQL"},
    )
    assert created.status_code == 201
    task_id = created.json()["id"]
    completed = client.patch(
        "/api/study-plan/" + str(task_id),
        headers=headers,
        json={"is_completed": True},
    )
    assert completed.status_code == 200

    session = client.app.state.testing_session()
    from app.models.entities import StudyTask
    task = session.get(StudyTask, task_id)
    assert task.completed_at is not None
    # SQLite returns timezone-aware ORM DateTime values as naive values.
    session.close()

    summary = client.get("/api/progress/summary", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["current_streak_days"] == 1
    assert summary.json()["longest_streak_days"] == 1
    assert summary.json()["last_active_date"] == datetime.now(timezone.utc).date().isoformat()


def test_company_directory_labels_unresearched_patterns_and_lists_official_portal(client):
    from app.models.entities import CompanyProfile

    session = client.app.state.testing_session()
    session.add(CompanyProfile(
        name="Example Employer",
        slug="example-employer",
        category="service",
        career_url="https://careers.example.com",
        description="Official careers portal for employer opportunities.",
        hiring_tracks=["Graduate opportunities"],
        research_status="pending",
        is_published=True,
    ))
    session.commit()
    session.close()

    listing = client.get("/api/companies")
    assert listing.status_code == 200
    company = next(item for item in listing.json() if item["slug"] == "example-employer")
    assert company["career_url"] == "https://careers.example.com"
    assert company["research_status"] == "pending"

    detail = client.get("/api/companies/example-employer")
    assert detail.status_code == 200
    assert detail.json()["research_sources"] == []
    assert detail.json()["research_status"] == "pending"


def test_company_research_sources_require_admin_and_are_recorded(client):
    from app.models.entities import CompanyProfile, User

    session = client.app.state.testing_session()
    company = CompanyProfile(
        name="Research Test Employer",
        slug="research-test-employer",
        category="product",
        career_url="https://careers.example.com",
        description="Career portal for testing research source records.",
        is_published=True,
    )
    session.add(company)
    session.commit()
    company_id = company.id
    session.close()

    token = register_student(client, "research-admin@example.com")
    headers = {"Authorization": "Bearer " + token}
    payload = {
        "title": "Official graduate careers page",
        "url": "https://careers.example.com/graduates",
        "evidence_type": "official",
        "claim": "The employer maintains an official graduate careers information page.",
        "confidence": "high",
    }
    denied = client.post(
        f"/api/admin/companies/{company_id}/sources",
        headers=headers,
        json=payload,
    )
    assert denied.status_code == 403

    session = client.app.state.testing_session()
    account = session.query(User).filter_by(email="research-admin@example.com").one()
    account.role = "admin"
    session.commit()
    session.close()

    added = client.post(
        f"/api/admin/companies/{company_id}/sources",
        headers=headers,
        json=payload,
    )
    assert added.status_code == 201
    detail = client.get("/api/companies/research-test-employer")
    assert detail.status_code == 200
    assert len(detail.json()["research_sources"]) == 1
    assert detail.json()["research_sources"][0]["evidence_type"] == "official"
    assert detail.json()["research_status"] == "has_sources_pending_review"

    reviewed = client.patch(
        f"/api/admin/companies/{company_id}/research-status",
        headers=headers,
        json={"research_status": "reviewed"},
    )
    assert reviewed.status_code == 200
    assert reviewed.json()["research_status"] == "reviewed"
    assert reviewed.json()["last_verified_at"] is not None

    session = client.app.state.testing_session()
    from app.models.entities import Problem
    problem = Problem(
        title="Company Mapping Test",
        slug="company-mapping-test",
        statement="A test problem used to verify company mapping.",
        difficulty="easy",
        is_published=True,
        company_tags=[],
    )
    session.add(problem)
    session.commit()
    problem_id = problem.id
    session.close()

    mapped = client.post(
        f"/api/admin/companies/research-test-employer/problems/{problem_id}",
        headers=headers,
    )
    assert mapped.status_code == 200
    listed = client.get("/api/companies/research-test-employer/problems")
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == problem_id
