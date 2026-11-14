import io
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import init_db
from app.services.text_extraction_service import extract_text_from_file, parse_and_chunk_course_material
from app.services.nlp_service import nlp_service
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
    # Authenticate faculty
    init_res = client.post("/api/auth/faculty/login-init", json={
        "email": "faculty@university.edu",
        "password": "FacultyPass123!"
    })
    data = init_res.json()
    ticket = data["session_ticket"]
    otp = data["dev_otp"]

    verify_res = client.post("/api/auth/faculty/verify-otp", json={
        "session_ticket": ticket,
        "otp_code": otp
    })
    return verify_res.json()["access_token"]

def test_text_extraction_and_chunking():
    sample_text = """
Module 1: Dynamic Programming Principles
Dynamic programming is an optimization technique that breaks down complex problems into overlapping subproblems with optimal substructure.
We formulate recurrence relations and solve base cases using memoization tables.
The 0/1 Knapsack problem demonstrates optimal substructure where item choices depend on remaining capacity.

Module 2: Graph Algorithmic Structures
Graph theory studies vertices and edges representing relational networks.
Single-source shortest path problems find minimum edge weights from a source node to all destinations.
The Bellman-Ford algorithm iteratively relaxes edges |V|-1 times and effectively identifies negative-weight cycles.
Dijkstra's greedy approach achieves optimal complexity when all edge weights are strictly non-negative.
"""
    raw_bytes = sample_text.strip().encode("utf-8")
    extracted = extract_text_from_file(raw_bytes, "lecture_notes.txt")
    assert "Dynamic programming" in extracted

    chunks = parse_and_chunk_course_material(extracted)
    assert len(chunks) >= 4
    
    # Verify module names are preserved
    modules = {c["module_name"] for c in chunks}
    assert any("Dynamic Programming" in m for m in modules)
    assert any("Graph" in m for m in modules)

def test_nlp_objective_mapping_and_coverage_gaps():
    chunks = [
        {"module_name": "Module 1", "chunk_index": 0, "content": "Recursive state transitions and dynamic programming memoization tables optimize subproblem computations."},
        {"module_name": "Module 2", "chunk_index": 1, "content": "Single-source and all-pairs shortest path algorithms on directed cyclic graphs using edge relaxations."}
    ]

    objectives = [
        {"id": "co1-id", "code": "CO1", "description": "Formulate recursive state transitions and dynamic programming memoization tables.", "weight": 1.2},
        {"id": "co2-id", "code": "CO2", "description": "Analyze single-source and all-pairs shortest path algorithms on directed acyclic and cyclic graphs.", "weight": 1.0},
        {"id": "co3-id", "code": "CO3", "description": "Evaluate NP-completeness reductions and polynomial-time verification mechanisms.", "weight": 0.8}
    ]

    result = nlp_service.map_chunks_to_objectives(chunks, objectives, similarity_threshold=0.25)
    
    assert len(result["mapped_chunks"]) == 2
    # Chunk 0 should map to CO1
    assert result["mapped_chunks"][0]["mapped_objective_code"] == "CO1"
    # Chunk 1 should map to CO2
    assert result["mapped_chunks"][1]["mapped_objective_code"] == "CO2"

    # CO3 was not covered in chunks, must be reported as a Coverage Gap
    gaps = [g["code"] for g in result["coverage_gaps"]]
    assert "CO3" in gaps
    assert "CO1" not in gaps
    assert "CO2" not in gaps

def test_course_material_upload_api_flow(client, faculty_token):
    # Fetch faculty dashboard to obtain course_id
    dash_res = client.get("/api/faculty/dashboard", headers={"Authorization": f"Bearer {faculty_token}"})
    course_id = dash_res.json()["assigned_courses"][0]["id"]

    sample_content = """
Module 1: Dynamic Programming Foundations
Dynamic programming formulates recursive state transitions and stores solutions in memoization tables to avoid redundant subproblem calculations.
We analyze optimal substructure properties in knapsack and longest common subsequence algorithms.

Module 2: Shortest Paths and Graph Theory
Graph algorithms compute single-source shortest path trees across cyclic directed graphs.
Bellman-Ford repeatedly relaxes all edges to detect negative cycle anomalies.
"""
    file_bytes = io.BytesIO(sample_content.encode("utf-8"))

    # Upload material
    res = client.post(
        f"/api/faculty/courses/{course_id}/materials/upload",
        headers={"Authorization": f"Bearer {faculty_token}"},
        files={"file": ("algorithms_syllabus.txt", file_bytes, "text/plain")},
        data={"similarity_threshold": "0.20"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["filename"] == "algorithms_syllabus.txt"
    assert data["total_chunks"] >= 2
    assert len(data["objective_summaries"]) == 3

    # CO3 (NP-completeness) should be detected as a coverage gap!
    gap_codes = [g["code"] for g in data["coverage_gaps"]]
    assert "CO3" in gap_codes

    # Fetch mapping via GET endpoint
    get_res = client.get(
        f"/api/faculty/courses/{course_id}/materials/mapping?similarity_threshold=0.20",
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["total_chunks"] == data["total_chunks"]
    assert len(get_data["chunks"]) > 0

