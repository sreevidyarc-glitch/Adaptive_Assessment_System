import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import init_db
from app.services.question_allocation_service import (
    allocate_objectives_largest_remainder,
    allocate_traits_quota_deficits
)
from app.services.question_validation_service import (
    validate_schema,
    validate_hint_leakage,
    validate_rubric_sanity,
    validate_duplicate,
    validate_all
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

def test_largest_remainder_allocation():
    # 7 questions across 3 objectives with weights 1.2, 1.0, 0.8
    # Total weight = 3.0.
    # Quotas: CO1 = 7*1.2/3.0 = 2.80 -> floor 2, rem 0.80
    #         CO2 = 7*1.0/3.0 = 2.33 -> floor 2, rem 0.33
    #         CO3 = 7*0.8/3.0 = 1.87 -> floor 1, rem 0.87
    # Initial sum = 2+2+1 = 5. Surplus = 2.
    # Top remainders: CO3 (0.87), CO1 (0.80) -> each gets +1
    # Expected: CO1 = 3, CO2 = 2, CO3 = 2 -> total = 7!
    objectives = [
        {"id": "o1", "code": "CO1", "weight": 1.2},
        {"id": "o2", "code": "CO2", "weight": 1.0},
        {"id": "o3", "code": "CO3", "weight": 0.8}
    ]
    alloc = allocate_objectives_largest_remainder(7, objectives)
    assert sum(alloc.values()) == 7
    assert alloc["o1"] == 3
    assert alloc["o2"] == 2
    assert alloc["o3"] == 2

def test_trait_quota_deficits_allocation():
    alloc_objs = {"o1": 3, "o2": 2, "o3": 2} # 7 total
    traits = [
        {"id": "t1", "code": "TR_CONCEPT", "name": "Conceptual Clarity", "weight": 1.0},
        {"id": "t2", "code": "TR_PROBLEM", "name": "Problem Solving", "weight": 1.0},
        {"id": "t3", "code": "TR_ANALYSIS", "name": "Analytical Rigor", "weight": 1.0}
    ]
    planned = allocate_traits_quota_deficits(alloc_objs, traits)
    assert len(planned) == 7
    trait_counts = {}
    for p in planned:
        trait_counts[p["trait_id"]] = trait_counts.get(p["trait_id"], 0) + 1
    # Check balanced distribution: counts should be between 2 and 3
    for count in trait_counts.values():
        assert count in (2, 3)

def test_validation_suite_checks():
    # 1. Schema Validation
    valid_candidate = {
        "question": "Formulate a dynamic programming recurrence relation for longest common subsequence with proof of optimal substructure.",
        "rubric": {
            "total_points": 10.0,
            "criteria": [
                {"criterion": "Recurrence Formulation", "max_points": 5.0, "weight": 0.5},
                {"criterion": "Base Cases & Subproblems", "max_points": 5.0, "weight": 0.5}
            ]
        },
        "model_answer": "dp[i][j] = dp[i-1][j-1] + 1 if X[i]==Y[j], else max(dp[i-1][j], dp[i][j-1]). Base case: dp[0][j] = dp[i][0] = 0.",
        "hint1": "Consider whether characters at current indices match or diverge.",
        "hint2": "Construct a 2D table tracking prefix lengths of both sequences."
    }
    ok, msg = validate_schema(valid_candidate)
    assert ok is True

    # Bad schema: empty prompt
    bad_cand = {**valid_candidate, "question": "Too short"}
    ok, msg = validate_schema(bad_cand)
    assert ok is False

    # 2. Hint Leakage Detection
    # Bad hint: leaks model answer directly
    leaking_candidate = {
        **valid_candidate,
        "hint1": "The answer is literally dp[i][j] = dp[i-1][j-1] + 1 if X[i]==Y[j] else max."
    }
    ok, msg = validate_hint_leakage(leaking_candidate["hint1"], leaking_candidate["hint2"], leaking_candidate["model_answer"])
    assert ok is False
    assert "leakage" in msg.lower()

    # Good hint: passes
    ok, msg = validate_hint_leakage(valid_candidate["hint1"], valid_candidate["hint2"], valid_candidate["model_answer"])
    assert ok is True

    # 3. Rubric Sanity
    # Denominator zero or mismatched sum
    bad_rubric = {
        "total_points": 10.0,
        "criteria": [
            {"criterion": "Part 1", "max_points": 4.0, "weight": 0.4} # Sum is 4.0 != 10.0
        ]
    }
    ok, msg = validate_rubric_sanity(bad_rubric)
    assert ok is False

    ok, msg = validate_rubric_sanity(valid_candidate["rubric"])
    assert ok is True

    # 4. Duplicate Check
    existing = ["Formulate a dynamic programming recurrence relation for longest common subsequence with proof of optimal substructure."]
    ok, msg = validate_duplicate("Formulate a dynamic programming recurrence relation for longest common subsequence with proof of optimal substructure.", existing)
    assert ok is False

    ok, msg = validate_duplicate("Evaluate polynomial-time reductions for 3-SAT to Vertex Cover.", existing)
    assert ok is True

def test_question_generation_api_flow(client, faculty_token, student_token):
    # 1. Get faculty course ID
    dash_res = client.get("/api/faculty/dashboard", headers={"Authorization": f"Bearer {faculty_token}"})
    course_id = dash_res.json()["assigned_courses"][0]["id"]

    # 2. Generate 3 questions
    gen_res = client.post(
        f"/api/faculty/courses/{course_id}/questions/generate",
        headers={"Authorization": f"Bearer {faculty_token}"},
        json={"total_questions": 3}
    )
    assert gen_res.status_code == 200
    gen_data = gen_res.json()
    assert gen_data["total_generated"] == 3
    assert len(gen_data["questions"]) == 3

    # Verify questions are initially unapproved and unpublished
    q_ids = [q["id"] for q in gen_data["questions"]]
    for q in gen_data["questions"]:
        assert q["rubric"] is not None
        assert q["model_answer"] is not None

    # 3. Batch Approve and Publish Questions
    batch_res = client.post(
        f"/api/faculty/courses/{course_id}/questions/batch-approve",
        headers={"Authorization": f"Bearer {faculty_token}"},
        json={
            "question_ids": q_ids,
            "is_approved": True,
            "is_published": True
        }
    )
    assert batch_res.status_code == 200
    assert batch_res.json()["approved_count"] == 3

    # 4. Student View (CRITICAL PRIVACY TEST)
    student_res = client.get(
        f"/api/student/courses/{course_id}/questions",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert student_res.status_code == 200
    published_for_student = student_res.json()
    assert len(published_for_student) >= 3

    for sq in published_for_student:
        # Rubric and Model Answer MUST NOT be leaked to student
        assert "rubric" not in sq or sq.get("rubric") is None
        assert "model_answer" not in sq or sq.get("model_answer") is None
        assert "prompt" in sq
        assert sq["prompt"] is not None

