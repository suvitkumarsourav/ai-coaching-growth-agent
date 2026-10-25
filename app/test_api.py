
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_home():
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<html" in response.text.lower()

def test_get_courses():
    response = client.get("/courses")

    assert response.status_code == 200
    assert "courses" in response.json()


def test_get_career_roadmaps():
    response = client.get("/research/roadmaps")

    assert response.status_code == 200
    assert "roadmaps" in response.json()


def test_get_learning_resources():
    response = client.get("/research/resources")

    assert response.status_code == 200
    assert "resources" in response.json()


def test_ai_question_validation():
    response = client.post(
        "/ai/ask",
        json={"question": ""},
    )

    assert response.status_code == 422


def test_career_guidance_validation():
    response = client.post(
        "/ai/career-guidance",
        json={
            "current_level": "Beginner",
            "career_goal": "Become an AI Engineer",
            "weekly_hours": 0,
        },
    )

    assert response.status_code == 422


def test_reply_draft_validation():
    response = client.post(
        "/ai/reply-draft",
        json={
            "student_message": "Hi",
            "course_name": "ML",
            "verified_course_details": "Fee is 12000",
        },
    )

    assert response.status_code == 422
