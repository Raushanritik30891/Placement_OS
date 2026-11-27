def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_problem_list_is_empty_until_seeded(client):
    response = client.get("/api/problems")
    assert response.status_code == 200
    assert response.json() == []


def test_submission_rejects_unknown_problem(client):
    response = client.post(
        "/api/submissions",
        json={"problem_id": 9999, "language": "python", "source_code": "print('hello')"},
    )
    assert response.status_code == 404
