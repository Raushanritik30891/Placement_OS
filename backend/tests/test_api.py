def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_problem_list_is_empty_until_seeded(client):
    response = client.get("/api/problems")
    assert response.status_code == 200
    assert response.json() == []


def test_registration_returns_student_token_and_me(client):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "student@example.com",
            "display_name": "Test Student",
            "password": "strong-test-password-2026",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["user"]["role"] == "student"
    assert "password_hash" not in body["user"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == "student@example.com"


def test_duplicate_registration_is_rejected(client):
    payload = {
        "email": "duplicate@example.com",
        "display_name": "Test Student",
        "password": "strong-test-password-2026",
    }
    assert client.post("/api/auth/register", json=payload).status_code == 201
    assert client.post("/api/auth/register", json=payload).status_code == 409


def test_protected_progress_requires_authentication(client):
    response = client.get("/api/progress")
    assert response.status_code == 401


def test_sql_playground_allows_select(client):
    response = client.post(
        "/api/sql/execute",
        json={"query": "SELECT name, city FROM customers ORDER BY customer_id LIMIT 2"},
    )
    assert response.status_code == 200
    assert response.json()["columns"] == ["name", "city"]
    assert response.json()["rows"] == [["Aarav", "Delhi"], ["Diya", "Pune"]]
    assert response.json()["read_only"] is True


def test_sql_playground_blocks_mutations(client):
    response = client.post(
        "/api/sql/execute",
        json={"query": "DELETE FROM customers"},
    )
    assert response.status_code == 400


def test_sql_playground_blocks_multi_statement(client):
    response = client.post(
        "/api/sql/execute",
        json={"query": "SELECT 1; DROP TABLE customers"},
    )
    assert response.status_code == 400


def test_submission_requires_authentication(client):
    response = client.post(
        "/api/submissions",
        json={"problem_id": 1, "language": "python", "source_code": "print('hello')"},
    )
    assert response.status_code == 401


def test_dashboard_metrics_are_database_backed(client):
    response = client.get("/api/overview")
    assert response.status_code == 200
    body = response.json()
    assert body["published_problems"] == 0
    assert body["assessment_questions"] == 0
    assert body["features"]["secure_code_execution"] is False
