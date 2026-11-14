import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import init_db
from app.services.mastery_evaluation_service import (
    calculate_rubric_fraction,
    calculate_objective_trait_mastery,
    calculate_learning_gap
)
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
# 1. Exact Mathematical Calculation Tests on Manually Verified Examples
# -------------------------------------------------------------

def test_rubric_fraction_calculations():
    # Standard valid calculation: earned=8, total=10 -> f_i = 0.8
    assert calculate_rubric_fraction(8.0, 10.0) == 0.8
    assert calculate_rubric_fraction(5.0, 10.0) == 0.5
    assert calculate_rubric_fraction(0.0, 10.0) == 0.0
    assert calculate_rubric_fraction(10.0, 10.0) == 1.0

    # Clamping behavior: earned beyond max clamped to 1.0; negative to 0.0
    assert calculate_rubric_fraction(12.0, 10.0) == 1.0
    assert calculate_rubric_fraction(-2.0, 10.0) == 0.0

    # Denominator invariant: total_points <= 0 must raise ValueError
    with pytest.raises(ValueError, match="Rubric denominator"):
        calculate_rubric_fraction(5.0, 0.0)

    with pytest.raises(ValueError, match="Rubric denominator"):
        calculate_rubric_fraction(5.0, -10.0)

def test_objective_trait_mastery_manually_verified_examples():
    """
    Test M_o,t = (1 + sum(w_i * f_i)) / (2 + sum(w_i))
    against manually verified examples.
    """
    # Example 1:
    # w_1 = 2.0, f_1 = 0.8
    # w_2 = 1.0, f_2 = 0.5
    # Numerator:   1 + (2.0 * 0.8 + 1.0 * 0.5) = 1 + (1.6 + 0.5) = 3.1
    # Denominator: 2 + (2.0 + 1.0) = 5.0
    # Expected M = 3.1 / 5.0 = 0.62
    m1 = calculate_objective_trait_mastery([(2.0, 0.8), (1.0, 0.5)])
    assert pytest.approx(m1, abs=1e-5) == 0.62

    # Example 2:
    # w_1 = 2.0, f_1 = 0.0
    # Numerator:   1 + 0 = 1.0
    # Denominator: 2 + 2.0 = 4.0
    # Expected M = 1.0 / 4.0 = 0.25
    m2 = calculate_objective_trait_mastery([(2.0, 0.0)])
    assert pytest.approx(m2, abs=1e-5) == 0.25

    # Example 3:
    # w_1 = 4.0, f_1 = 1.0
    # Numerator:   1 + 4.0 = 5.0
    # Denominator: 2 + 4.0 = 6.0
    # Expected M = 5.0 / 6.0 = 0.833333...
    m3 = calculate_objective_trait_mastery([(4.0, 1.0)])
    assert pytest.approx(m3, abs=1e-5) == 5.0 / 6.0

    # Prior at zero evidence:
    # With no evidence, M_o,t = 1 / 2 = 0.5
    m_prior = calculate_objective_trait_mastery([])
    assert m_prior == 0.5

    # Invariant: Negative weight must raise ValueError
    with pytest.raises(ValueError, match="Evidence weight w_i must be non-negative"):
        calculate_objective_trait_mastery([(-1.0, 0.8)])

def test_learning_gap_calculations_and_recommendations():
    """
    Test G_o,t = max(0, (tau - M_o,t) * w_o)
    and recommendation classification:
    M_o,t < 0.3 -> FOUNDATIONAL
    M_o,t >= 0.3 -> REINFORCEMENT
    """
    tau = 0.75

    # Case A: Low mastery (M = 0.25 < 0.30) with objective weight 1.0
    # G = (0.75 - 0.25) * 1.0 = 0.50
    gap_a, rec_a = calculate_learning_gap(0.25, objective_weight=1.0, tau=tau)
    assert pytest.approx(gap_a, abs=1e-5) == 0.50
    assert rec_a == "FOUNDATIONAL"

    # Case B: High mastery above threshold (M = 0.833333 >= 0.75)
    # G = max(0, (0.75 - 0.833333) * 1.0) = 0.0
    gap_b, rec_b = calculate_learning_gap(5.0 / 6.0, objective_weight=1.0, tau=tau)
    assert gap_b == 0.0
    assert rec_b == "REINFORCEMENT"

    # Case C: Moderate mastery below threshold (M = 0.50) with priority weight 1.2
    # G = (0.75 - 0.50) * 1.2 = 0.25 * 1.2 = 0.30
    gap_c, rec_c = calculate_learning_gap(0.50, objective_weight=1.2, tau=tau)
    assert pytest.approx(gap_c, abs=1e-5) == 0.30
    assert rec_c == "REINFORCEMENT"

# -------------------------------------------------------------
# 2. End-to-End Student Assessment & Privacy Safeguards Integration
# -------------------------------------------------------------

def test_student_start_assessment_and_privacy_safeguards(client, student_token):
    # Get student dashboard to obtain enrolled course ID
    headers = {"Authorization": f"Bearer {student_token}"}
    dash_res = client.get("/api/student/dashboard", headers=headers)
    assert dash_res.status_code == 200
    courses = dash_res.json()["enrolled_courses"]
    assert len(courses) > 0
    course_id = courses[0]["id"]

    # Start assessment session
    start_res = client.post(f"/api/student/courses/{course_id}/assessments/start", headers=headers)
    assert start_res.status_code == 200
    data = start_res.json()
    assert "session_id" in data
    assert data["status"] in ["IN_PROGRESS", "NOT_STARTED"]
    assert "questions" in data
    assert len(data["questions"]) > 0

    # CRITICAL PRIVACY VERIFICATION:
    # Rubrics and Model Answers must NEVER be exposed in student question payloads!
    for q in data["questions"]:
        assert "prompt" in q
        assert "rubric" not in q
        assert "model_answer" not in q
        assert "criteria" not in q

def test_student_submit_assessment_and_mastery_matrix(client, student_token):
    headers = {"Authorization": f"Bearer {student_token}"}
    dash_res = client.get("/api/student/dashboard", headers=headers)
    course_id = dash_res.json()["enrolled_courses"][0]["id"]

    # Start session
    start_res = client.post(f"/api/student/courses/{course_id}/assessments/start", headers=headers)
    assert start_res.status_code == 200
    session_id = start_res.json()["session_id"]
    questions = start_res.json()["questions"]

    # Prepare student responses
    responses = [
        {
            "question_id": q["id"],
            "response_text": f"This is an analytical solution addressing {q['prompt'][:30]} with clear steps.",
            "hints_used": 1
        }
        for q in questions[:3]  # Attempt first 3 questions
    ]

    # Submit assessment
    submit_res = client.post(
        f"/api/student/assessments/{session_id}/submit",
        json={"responses": responses},
        headers=headers
    )
    assert submit_res.status_code == 200
    sub_data = submit_res.json()
    assert sub_data["session_id"] == session_id
    assert sub_data["status"] == "COMPLETED"
    assert "earned_points" in sub_data
    assert "results" in sub_data
    assert len(sub_data["results"]) == len(responses)

    # Verify each result has earned points and fraction f_i, and NO rubric leakage
    for r in sub_data["results"]:
        assert 0.0 <= r["fraction_achieved"] <= 1.0
        assert "rubric" not in r
        assert "model_answer" not in r

    # Fetch personal mastery matrix
    matrix_res = client.get(f"/api/student/courses/{course_id}/mastery-matrix", headers=headers)
    assert matrix_res.status_code == 200
    matrix_data = matrix_res.json()
    assert "matrix" in matrix_data
    assert "ranked_learning_gaps" in matrix_data
    assert len(matrix_data["matrix"]) > 0

    # Verify rows in matrix
    for row in matrix_data["matrix"]:
        assert "objective_code" in row
        assert "traits" in row
        for cell in row["traits"]:
            assert 0.0 <= cell["mastery_value"] <= 1.0
            assert cell["gap_score"] >= 0.0
            assert cell["recommendation_type"] in ["FOUNDATIONAL", "REINFORCEMENT"]

def test_privacy_and_role_authorization_enforcement(client, student_token, faculty_token):
    headers_student = {"Authorization": f"Bearer {student_token}"}
    headers_faculty = {"Authorization": f"Bearer {faculty_token}"}

    dash_res = client.get("/api/student/dashboard", headers=headers_student)
    course_id = dash_res.json()["enrolled_courses"][0]["id"]

    # 1. Student attempting to access class-level mastery matrix MUST receive 403 Forbidden
    student_class_access = client.get(
        f"/api/faculty/courses/{course_id}/mastery-matrix",
        headers=headers_student
    )
    assert student_class_access.status_code == 403

    # 2. Authorized faculty accessing class-level mastery matrix succeeds
    faculty_class_access = client.get(
        f"/api/faculty/courses/{course_id}/mastery-matrix",
        headers=headers_faculty
    )
    assert faculty_class_access.status_code == 200
    fac_data = faculty_class_access.json()
    assert "matrix" in fac_data
    assert "total_enrolled_students" in fac_data
    assert fac_data["total_enrolled_students"] >= 1

    # 3. Accessing unassigned / unenrolled course yields 403 Forbidden
    bogus_course_id = "00000000-0000-0000-0000-000000000000"
    unauth_student_res = client.get(
        f"/api/student/courses/{bogus_course_id}/mastery-matrix",
        headers=headers_student
    )
    assert unauth_student_res.status_code == 403
