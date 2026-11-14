import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import init_db
from seed_data import seed

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    init_db()
    seed()

@pytest.fixture
def client():
    return TestClient(app)

def test_faculty_login_flow(client):
    # Step 1: Login Init
    init_res = client.post("/api/auth/faculty/login-init", json={
        "email": "faculty@university.edu",
        "password": "FacultyPass123!"
    })
    assert init_res.status_code == 200
    data = init_res.json()
    assert data["status"] == "OTP_SENT"
    assert "session_ticket" in data
    assert "dev_otp" in data
    ticket = data["session_ticket"]
    otp = data["dev_otp"]

    # Step 2: Invalid OTP
    bad_res = client.post("/api/auth/faculty/verify-otp", json={
        "session_ticket": ticket,
        "otp_code": "000000"
    })
    assert bad_res.status_code == 400

    # Step 2: Valid OTP
    verify_res = client.post("/api/auth/faculty/verify-otp", json={
        "session_ticket": ticket,
        "otp_code": otp
    })
    assert verify_res.status_code == 200
    token_data = verify_res.json()
    assert token_data["role"] == "FACULTY"
    assert token_data["expires_in_minutes"] == 30
    assert "access_token" in token_data

    # Test Faculty Dashboard Access
    fac_token = token_data["access_token"]
    dash_res = client.get("/api/faculty/dashboard", headers={
        "Authorization": f"Bearer {fac_token}"
    })
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert dash_data["faculty_name"] == "Dr. Eleanor Vance"
    # Verify rubrics and model answers are visible to faculty
    assert len(dash_data["recent_questions"]) > 0
    q = dash_data["recent_questions"][0]
    assert q["rubric"] is not None
    assert q["model_answer"] is not None

def test_student_login_and_privacy_safeguards(client):
    # Student Login with Roll Number
    login_res = client.post("/api/auth/student/login", json={
        "identifier": "ROLL2026001",
        "password": "StudentPass123!"
    })
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert token_data["role"] == "STUDENT"
    assert token_data["expires_in_minutes"] == 60
    student_token = token_data["access_token"]

    # Test Student Dashboard
    dash_res = client.get("/api/student/dashboard", headers={
        "Authorization": f"Bearer {student_token}"
    })
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert dash_data["roll_number"] == "ROLL2026001"
    assert len(dash_data["enrolled_courses"]) > 0
    course_id = dash_data["enrolled_courses"][0]["id"]

    # Test Course Questions for Student (CRITICAL PRIVACY CHECK)
    q_res = client.get(f"/api/student/courses/{course_id}/questions", headers={
        "Authorization": f"Bearer {student_token}"
    })
    assert q_res.status_code == 200
    questions = q_res.json()
    assert len(questions) > 0
    for q in questions:
        # Rubric and Model Answer MUST NOT exist in student response
        assert "rubric" not in q or q.get("rubric") is None
        assert "model_answer" not in q or q.get("model_answer") is None
        assert "prompt" in q

    # Authorization Check: Student cannot access faculty endpoints
    forbidden_res = client.get("/api/faculty/dashboard", headers={
        "Authorization": f"Bearer {student_token}"
    })
    assert forbidden_res.status_code == 403

def test_session_logout_revocation(client):
    # Log in student
    login_res = client.post("/api/auth/student/login", json={
        "identifier": "ROLL2026001",
        "password": "StudentPass123!"
    })
    token = login_res.json()["access_token"]

    # Access endpoint before logout
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200

    # Logout
    logout_res = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_res.status_code == 200

    # Access endpoint after logout -> must be 401
    revoked_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert revoked_res.status_code == 401

