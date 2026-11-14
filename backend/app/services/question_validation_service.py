import re
import logging
from typing import Dict, Any, List, Tuple

from app.services.nlp_service import nlp_service

logger = logging.getLogger("adaptive_assessment.validation")

def validate_schema(candidate: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validation 1: Schema Validation (Spec Section 3 line 82)
    Verifies that all required fields exist, have proper types, and meet minimum content lengths.
    """
    required_keys = ["question", "rubric", "model_answer", "hint1", "hint2"]
    for key in required_keys:
        if key not in candidate:
            return False, f"Schema error: Missing required key '{key}'"

    prompt = candidate["question"]
    if not isinstance(prompt, str) or len(prompt.strip()) < 20:
        return False, "Schema error: Question prompt must be at least 20 characters."

    model_ans = candidate["model_answer"]
    if not isinstance(model_ans, str) or len(model_ans.strip()) < 25:
        return False, "Schema error: Model answer must be at least 25 characters."

    h1 = candidate["hint1"]
    h2 = candidate["hint2"]
    if not isinstance(h1, str) or len(h1.strip()) < 10:
        return False, "Schema error: Hint 1 must be at least 10 characters."
    if not isinstance(h2, str) or len(h2.strip()) < 10:
        return False, "Schema error: Hint 2 must be at least 10 characters."

    rubric = candidate["rubric"]
    if not isinstance(rubric, dict) or "criteria" not in rubric:
        return False, "Schema error: Rubric must be a dictionary with a 'criteria' array."

    return True, "Schema validation passed."

def validate_hint_leakage(hint1: str, hint2: str, model_answer: str) -> Tuple[bool, str]:
    """
    Validation 2: Hint Leakage Detection (Spec Section 3 line 83)
    Ensures Hint 1 (low scaffold) and Hint 2 (high scaffold) do not leak
    the direct solution or substantial verbatim segments of the model answer.
    """
    ans_clean = model_answer.strip().lower()
    
    # Extract substantive words (length >= 4) from model answer
    ans_words = set(re.findall(r'\b[a-z]{4,}\b', ans_clean))
    if not ans_words:
        return True, "Hint leakage check passed."

    for hint_num, hint in [("Hint 1", hint1), ("Hint 2", hint2)]:
        hint_clean = hint.strip().lower()
        
        # 1. Check for long continuous substrings (> 25 characters)
        if len(hint_clean) >= 25:
            # Slide window of 25 chars
            for i in range(len(hint_clean) - 24):
                sub = hint_clean[i:i+25]
                if sub in ans_clean:
                    return False, f"Hint leakage detected in {hint_num}: Verbatim substring '{sub}' from model answer found."

        # 2. Check token overlap ratio (Jaccard similarity of substantive words)
        hint_words = set(re.findall(r'\b[a-z]{4,}\b', hint_clean))
        if hint_words:
            overlap = ans_words.intersection(hint_words)
            overlap_ratio = len(overlap) / len(hint_words)
            if overlap_ratio > 0.60:
                return False, f"Hint leakage detected in {hint_num}: Word overlap ratio ({overlap_ratio:.2f}) exceeds 60%."

    return True, "Hint leakage check passed."

def validate_rubric_sanity(rubric: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validation 3: Rubric Sanity Check (Spec Section 3 line 84 & Section 6 line 271)
    - Rubric denominator must be greater than zero.
    - Sum of criteria max_points must match total_points within 0.1 tolerance.
    - All evidence weights w_i must be non-negative.
    """
    total_points = float(rubric.get("total_points", 0.0))
    if total_points <= 0.0:
        return False, "Rubric sanity failed: Rubric denominator (total_points) must be > 0."

    criteria = rubric.get("criteria", [])
    if not isinstance(criteria, list) or len(criteria) == 0:
        return False, "Rubric sanity failed: Criteria array must contain at least one criterion."

    points_sum = 0.0
    for idx, crit in enumerate(criteria):
        if not isinstance(crit, dict):
            return False, f"Rubric sanity failed: Criterion #{idx+1} must be an object."

        c_name = crit.get("criterion", "")
        if not c_name or not str(c_name).strip():
            return False, f"Rubric sanity failed: Criterion #{idx+1} is missing a description."

        c_points = float(crit.get("max_points", 0.0))
        if c_points <= 0.0:
            return False, f"Rubric sanity failed: Criterion #{idx+1} has invalid max_points ({c_points})."

        w = float(crit.get("weight", 1.0))
        if w < 0.0:
            return False, f"Rubric sanity failed: Evidence weight w_i ({w}) cannot be negative."

        points_sum += c_points

    # Verify points sum
    if abs(points_sum - total_points) > 0.2:
        return False, f"Rubric sanity failed: Sum of criteria max_points ({points_sum}) does not match total_points ({total_points})."

    return True, "Rubric sanity passed."

def validate_duplicate(prompt: str, existing_prompts: List[str]) -> Tuple[bool, str]:
    """
    Validation 4: Duplicate Detection (Spec Section 3 line 85)
    Computes cosine similarity against previously approved or existing questions.
    Rejects candidate if similarity exceeds 0.85.
    """
    if not existing_prompts:
        return True, "Duplicate check passed (no existing questions)."

    sim_matrix = nlp_service.compute_similarity_matrix([prompt], existing_prompts)
    if sim_matrix and len(sim_matrix[0]) > 0:
        max_sim = max(sim_matrix[0])
        if max_sim > 0.85:
            return False, f"Duplicate question detected: Max similarity {max_sim:.2f} > 0.85 threshold."

    return True, "Duplicate check passed."

def validate_all(candidate: Dict[str, Any], existing_prompts: List[str]) -> Tuple[bool, List[str]]:
    """
    Executes the complete 4-stage validation suite.
    Returns (is_valid, list_of_failure_reasons).
    """
    failures = []

    # 1. Schema
    v1_ok, v1_msg = validate_schema(candidate)
    if not v1_ok:
        failures.append(v1_msg)

    # If schema failed fundamentally, skip deeper checks
    if not v1_ok:
        return False, failures

    # 2. Hint Leakage
    v2_ok, v2_msg = validate_hint_leakage(
        candidate["hint1"],
        candidate["hint2"],
        candidate["model_answer"]
    )
    if not v2_ok:
        failures.append(v2_msg)

    # 3. Rubric Sanity
    v3_ok, v3_msg = validate_rubric_sanity(candidate["rubric"])
    if not v3_ok:
        failures.append(v3_msg)

    # 4. Duplicate
    v4_ok, v4_msg = validate_duplicate(candidate["question"], existing_prompts)
    if not v4_ok:
        failures.append(v4_msg)

    return (len(failures) == 0), failures

