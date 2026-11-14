import math
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger("adaptive_assessment.allocation")

def allocate_objectives_largest_remainder(
    total_questions: int,
    objectives: List[Dict[str, Any]]
) -> Dict[str, int]:
    """
    Allocates N questions across course learning objectives using the
    Hamilton-Hare Largest Remainder Method (Spec Section 3 line 61-63).
    
    Guarantees:
    1. sum(allocations.values()) == total_questions exactly.
    2. Fractional remainders prioritize surplus distribution.
    """
    if total_questions <= 0 or not objectives:
        return {}

    total_weight = sum(float(obj.get("weight", 1.0) or 1.0) for obj in objectives)
    if total_weight <= 0:
        total_weight = len(objectives)

    # Step 1: Compute exact quotas, integer floors, and fractional remainders
    quotas: List[Dict[str, Any]] = []
    initial_sum = 0

    for obj in objectives:
        w = float(obj.get("weight", 1.0) or 1.0)
        exact_quota = (total_questions * w) / total_weight
        floor_quota = math.floor(exact_quota)
        remainder = exact_quota - floor_quota

        quotas.append({
            "id": obj["id"],
            "code": obj.get("code", ""),
            "floor_quota": floor_quota,
            "remainder": remainder
        })
        initial_sum += floor_quota

    # Step 2: Determine surplus questions to distribute
    surplus = total_questions - initial_sum

    # Step 3: Sort by descending remainder (break ties deterministically by code)
    quotas.sort(key=lambda x: (x["remainder"], x["code"]), reverse=True)

    # Step 4: Add 1 to top 'surplus' objectives
    allocations: Dict[str, int] = {}
    for i, item in enumerate(quotas):
        extra = 1 if i < surplus else 0
        allocations[item["id"]] = item["floor_quota"] + extra

    logger.info(f"Largest Remainder Question Allocation for N={total_questions}: {allocations}")
    return allocations

def allocate_traits_quota_deficits(
    allocated_objectives: Dict[str, int],
    traits: List[Dict[str, Any]],
    objective_metadata: Dict[str, Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Allocates questions across assessment traits using remaining quota deficits
    (Spec Section 3 line 64-66).
    
    For each planned question, selects the trait with the highest remaining quota deficit:
    D(t) = target_quota(t) - current_count(t)
    """
    if not allocated_objectives or not traits:
        return []

    total_questions = sum(allocated_objectives.values())
    if total_questions <= 0:
        return []

    # Calculate target quota for each trait (balanced distribution)
    trait_weights = [float(t.get("weight", 1.0) or 1.0) for t in traits]
    total_trait_weight = sum(trait_weights) or len(traits)

    trait_targets = {
        t["id"]: (total_questions * float(t.get("weight", 1.0) or 1.0)) / total_trait_weight
        for t in traits
    }
    trait_counts = {t["id"]: 0 for t in traits}

    planned_questions: List[Dict[str, Any]] = []

    # Map each question of each objective to a trait based on remaining quota deficit
    for obj_id, count in allocated_objectives.items():
        obj_meta = (objective_metadata or {}).get(obj_id, {})
        for q_idx in range(count):
            # Calculate current quota deficits
            # D(t) = target(t) - count(t)
            best_trait = max(
                traits,
                key=lambda t: (
                    trait_targets[t["id"]] - trait_counts[t["id"]],
                    -trait_counts[t["id"]]
                )
            )

            # Assign and update
            trait_counts[best_trait["id"]] += 1

            planned_questions.append({
                "objective_id": obj_id,
                "objective_code": obj_meta.get("code", "CO"),
                "objective_description": obj_meta.get("description", ""),
                "trait_id": best_trait["id"],
                "trait_code": best_trait.get("code", "TR"),
                "trait_name": best_trait.get("name", "Assessment Trait")
            })

    return planned_questions

