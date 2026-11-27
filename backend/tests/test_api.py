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
    from app.models.entities import QuizQuestion

    session_db = client.app.state.testing_session()
    session_db.add(QuizQuestion(
        category="timed-test",
        topic="Basics",
        prompt="What is 2 + 2?",
        options=["3", "4", "5"],
        correct_index=1,
        explanation="Two plus two equals four.",
        difficulty="easy",
        is_published=True,
    ))
    session_db.commit()
    session_db.close()

    token = register_student(client, "timed-user@example.com")
    headers = {"Authorization": "Bearer " + token}
    started = client.post(
        "/api/assessments/start",
        headers=headers,
        json={"category": "timed-test", "duration_minutes": 5, "question_limit": 1},
    )
    assert started.status_code == 201
    body = started.json()
    assert body["total"] == 1
    assert "correct_index" not in body["questions"][0]

    question_id = body["questions"][0]["id"]
    submitted = client.post(
        "/api/assessments/sessions/" + str(body["session_id"]) + "/submit",
        headers=headers,
        json={"answers": [{"question_id": question_id, "selected_index": 1}]},
    )
    assert submitted.status_code == 200
    assert submitted.json()["score"] == 1
    assert submitted.json()["percentage"] == 100.0

    repeated = client.post(
        "/api/assessments/sessions/" + str(body["session_id"]) + "/submit",
        headers=headers,
        json={"answers": [{"question_id": question_id, "selected_index": 1}]},
    )
    assert repeated.status_code == 409
