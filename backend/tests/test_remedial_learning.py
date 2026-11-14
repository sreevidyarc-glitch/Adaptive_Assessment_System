import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import init_db
from app.services.remedial_learning_service import calculate_normalized_learning_gain
from seed_data import seed

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    init_db()
    seed()

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def faculty_token(client):
    init_res = client.post("/api/auth/faculty/login-init", json={
        "email": "faculty@university.edu",
        "password": "FacultyPass123!"
    })
    ticket = init_res.json()["session_ticket"]
    otp = init_res.json()["dev_otp"]

    verify_res = client.post("/api/auth/faculty/verify-otp", json={
        "session_ticket": ticket,
        "otp_code": otp
    })
    return verify_res.json()["access_token"]

@pytest.fixture
def student_token(client):
    login_res = client.post("/api/auth/student/login", json={
        "identifier": "ROLL2026001",
        "password": "StudentPass123!"
    })
    return login_res.json()["access_token"]

# -------------------------------------------------------------
# 1. Exact Mathematical Invariant Tests: Normalized Learning Gain
# -------------------------------------------------------------

def test_normalized_learning_gain_calculations():
    # Case 1: High Learning Gain (g >= 0.70)
    # Pre = 0.20, Post = 0.92
    # g = (0.92 - 0.20) / (1.0 - 0.20) = 0.72 / 0.80 = 0.90
    g1, cat1, _ = calculate_normalized_learning_gain(0.20, 0.92)
    assert pytest.approx(g1, abs=1e-4) == 0.90
    assert cat1 == "HIGH"

    # Case 2: Medium Learning Gain (0.30 <= g < 0.70)
    # Pre = 0.40, Post = 0.70
    # g = (0.70 - 0.40) / (1.0 - 0.40) = 0.30 / 0.60 = 0.50
    g2, cat2, _ = calculate_normalized_learning_gain(0.40, 0.70)
    assert pytest.approx(g2, abs=1e-4) == 0.50
    assert cat2 == "MEDIUM"

    # Case 3: Low Learning Gain (g < 0.30)
    # Pre = 0.50, Post = 0.60
    # g = (0.60 - 0.50) / (1.0 - 0.50) = 0.10 / 0.50 = 0.20
    g3, cat3, _ = calculate_normalized_learning_gain(0.50, 0.60)
    assert pytest.approx(g3, abs=1e-4) == 0.20
    assert cat3 == "LOW"

    # Case 4: Zero Gain
    # Pre = 0.40, Post = 0.40
    g4, cat4, _ = calculate_normalized_learning_gain(0.40, 0.40)
    assert g4 == 0.0
    assert cat4 == "LOW"

def test_normalized_learning_gain_pre_equals_one_invariant():
    """
    CRITICAL INVARIANT from Section 3 lines 161-163:
    IF Pre = 1 THEN RAISE exception: "Normalized gain is undefined when Pre = 1."
    """
    with pytest.raises(ValueError, match="Normalized gain is undefined when Pre = 1"):
        calculate_normalized_learning_gain(1.0, 1.0)

    with pytest.raises(ValueError, match="Normalized gain is undefined when Pre = 1"):
        calculate_normalized_learning_gain(1.0, 0.85)

def test_normalized_learning_gain_range_validation():
    """
    Confirm that Pre and Post are normalized to the interval [0, 1].
    Invalid inputs must raise ValueError.
    """
    with pytest.raises(ValueError, match="must be normalized"):
        calculate_normalized_learning_gain(-0.1, 0.8)

    with pytest.raises(ValueError, match="must be normalized"):
        calculate_normalized_learning_gain(0.2, 1.5)

    with pytest.raises(ValueError, match="must be normalized"):
        calculate_normalized_learning_gain(1.2, 0.8)

# -------------------------------------------------------------
# 2. Remedial Learning Packs API Flow & Privacy
# -------------------------------------------------------------

def test_remedial_learning_packs_generation_and_completion(client, student_token):
    headers = {"Authorization": f"Bearer {student_token}"}
    dash_res = client.get("/api/student/dashboard", headers=headers)
    assert dash_res.status_code == 200
    course_id = dash_res.json()["enrolled_courses"][0]["id"]

    # 1. Fetch personalized remedial learning packs
    packs_res = client.get(f"/api/student/courses/{course_id}/remedial-packs", headers=headers)
    assert packs_res.status_code == 200
    packs = packs_res.json()
    assert isinstance(packs, list)
    assert len(packs) > 0

    # Verify ranking: packs must be ranked in descending order of gap_score G_o,t
    gap_scores = [p["gap_score"] for p in packs]
    assert gap_scores == sorted(gap_scores, reverse=True)

    # Verify content structure & recommendations
    for p in packs:
        assert p["recommendation_type"] in ["FOUNDATIONAL", "REINFORCEMENT"]
        assert len(p["title"]) > 0
        assert len(p["key_concepts"]) > 0
        assert "practice_items" in p
        assert "reading_chunks" in p
        # Rubrics and Model answers must NOT leak into student packs
        assert "rubric" not in p
        assert "model_answer" not in p

    # 2. Mark first pack as completed
    pack_id = packs[0]["id"]
    complete_res = client.patch(f"/api/student/remedial-packs/{pack_id}/complete", headers=headers)
    assert complete_res.status_code == 200
    assert complete_res.json()["is_completed"] is True

# -------------------------------------------------------------
# 3. Post-Assessment with Progressive Hints & Gain Calculation
# -------------------------------------------------------------

def test_post_assessment_and_normalized_gain_flow(client, student_token):
    headers = {"Authorization": f"Bearer {student_token}"}
    dash_res = client.get("/api/student/dashboard", headers=headers)
    course_id = dash_res.json()["enrolled_courses"][0]["id"]

    # 1. Start post-assessment (token validity re-verified)
    start_res = client.post(f"/api/student/courses/{course_id}/post-assessments/start", headers=headers)
    assert start_res.status_code == 200
    post_data = start_res.json()
    session_id = post_data["session_id"]
    assert post_data["session_type"] == "POST"
    assert len(post_data["questions"]) > 0

    # Ensure progressive hints are available but NO rubrics or model answers
    for q in post_data["questions"]:
        assert "prompt" in q
        assert "rubric" not in q
        assert "model_answer" not in q

    # 2. Submit post-assessment responses
    questions = post_data["questions"]
    submissions = [
        {
            "question_id": q["id"],
            "response_text": f"Rigorous post-assessment solution addressing {q['prompt'][:30]} with proofs.",
            "hints_used": 1
        }
        for q in questions[:3]
    ]

    submit_res = client.post(
        f"/api/student/post-assessments/{session_id}/submit",
        json={"responses": submissions},
        headers=headers
    )
    assert submit_res.status_code == 200
    sub_res = submit_res.json()
    assert sub_res["status"] == "COMPLETED"
    assert sub_res["session_type"] == "POST"
    assert "pre_score" in sub_res
    assert "post_score" in sub_res
    assert 0.0 <= sub_res["post_score"] <= 1.0

# -------------------------------------------------------------
# 4. Assessment Reports & Authorization Checks
# -------------------------------------------------------------

def test_student_and_faculty_assessment_reports(client, student_token, faculty_token):
    headers_student = {"Authorization": f"Bearer {student_token}"}
    headers_faculty = {"Authorization": f"Bearer {faculty_token}"}

    dash_res = client.get("/api/student/dashboard", headers=headers_student)
    course_id = dash_res.json()["enrolled_courses"][0]["id"]

    # 1. Student accesses personal assessment report
    stu_report_res = client.get(f"/api/student/courses/{course_id}/assessment-report", headers=headers_student)
    assert stu_report_res.status_code == 200
    stu_report = stu_report_res.json()
    assert "report_id" in stu_report
    assert "pre_score" in stu_report
    assert "mastery_progression" in stu_report
    assert len(stu_report["mastery_progression"]) > 0

    # 2. Student attempting to access faculty report receives 403 Forbidden
    student_faculty_access = client.get(
        f"/api/faculty/courses/{course_id}/assessment-report",
        headers=headers_student
    )
    assert student_faculty_access.status_code == 403

    # 3. Authorized faculty accesses class-level report
    fac_report_res = client.get(f"/api/faculty/courses/{course_id}/assessment-report", headers=headers_faculty)
    assert fac_report_res.status_code == 200
    fac_report = fac_report_res.json()
    assert fac_report["course_id"] == course_id
    assert "total_enrolled_students" in fac_report
    assert "cohort_pre_average" in fac_report
    assert "cohort_post_average" in fac_report
    assert "gain_distribution" in fac_report
    assert "gap_resolution_percentage" in fac_report

    # 4. Unassigned course gives 403 Forbidden
    bogus_course_id = "00000000-0000-0000-0000-000000000000"
    unauth_res = client.get(f"/api/faculty/courses/{bogus_course_id}/assessment-report", headers=headers_faculty)
    assert unauth_res.status_code == 403

