import json
import re
import logging
from typing import Optional, Dict, Any, List
from app.core.config import settings

logger = logging.getLogger("adaptive_assessment.gemini")

class GeminiService:
    """
    Server-side isolated AI service for adaptive assessment question generation,
    rubric creation, and response evaluation.
    API key is never exposed to frontend.
    """
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        self._client = None
        if self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
                logger.info(f"Gemini client initialized with model {self.model_name}")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini client: {e}")

    def is_configured(self) -> bool:
        return bool(self._client and self.api_key)

    def is_available(self) -> bool:
        return self.is_configured()

    def evaluate_student_response(
        self,
        question_prompt: str,
        rubric_criteria: List[Dict[str, Any]],
        total_rubric_points: float,
        model_answer: Optional[str],
        student_response: str,
        hints_used: int = 0
    ) -> Dict[str, Any]:
        """
        Evaluates a student response against rubric criteria using Gemini API.
        """
        if self.is_configured():
            try:
                system_prompt = (
                    "You are an academic assessor. Evaluate the student response against the provided rubric criteria. "
                    "Return strictly JSON with keys: 'earned_points' (float), 'feedback' (str), and "
                    "'criteria_scores' (list of {criterion: str, earned_points: float, max_points: float})."
                )
                user_prompt = (
                    f"Question: {question_prompt}\n"
                    f"Model Answer: {model_answer or 'N/A'}\n"
                    f"Total Rubric Points: {total_rubric_points}\n"
                    f"Rubric Criteria: {json.dumps(rubric_criteria)}\n"
                    f"Student Response: {student_response}\n"
                    f"Hints Used: {hints_used}\n"
                )
                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=f"{system_prompt}\n\n{user_prompt}",
                    config={"response_mime_type": "application/json"}
                )
                raw_text = response.text.strip()
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]
                parsed = json.loads(raw_text.strip())
                earned = float(parsed.get("earned_points", 0.0))
                return {
                    "earned_points": min(earned, total_rubric_points),
                    "details": parsed
                }
            except Exception as e:
                logger.warning(f"Gemini evaluation failed: {e}")
        return {}


    def generate_assessment_question(
        self,
        objective_code: str,
        objective_description: str,
        trait_name: str,
        context_chunks: List[str] = None,
        retry_feedback: Optional[str] = None,
        variation_index: int = 0
    ) -> Dict[str, Any]:
        """
        Generates Question, Rubric (total 10.0 pts), Model Answer, Hint 1, and Hint 2.
        Supports structured JSON parsing from Gemini API and deterministic academic fallback.
        """
        context_snippet = "\n---\n".join(context_chunks[:3]) if context_chunks else "No specific course chunks provided."

        if self.is_configured():
            try:
                system_prompt = (
                    "You are a university academic examiner. Generate a rigorous assessment question based on the provided "
                    "Course Objective and Assessment Trait. Return STRICT JSON with keys: "
                    "'question', 'rubric' (must contain 'total_points': 10.0 and 'criteria' array with sum of max_points=10.0 and non-negative weights), "
                    "'model_answer', 'hint1' (low scaffold hint that does NOT leak the answer), and 'hint2' (high scaffold guidance that does NOT leak the answer)."
                )

                user_prompt = (
                    f"Objective: {objective_code} - {objective_description}\n"
                    f"Assessment Trait: {trait_name}\n"
                    f"Context Chunks:\n{context_snippet}\n"
                )
                if retry_feedback:
                    user_prompt += f"\nATTENTION: A previous generation attempt failed validation: {retry_feedback}. Fix this issue completely."

                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=f"{system_prompt}\n\n{user_prompt}",
                    config={
                        "response_mime_type": "application/json"
                    }
                )
                
                # Parse JSON
                raw_text = response.text.strip()
                # Clean markdown json fencing if present
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]

                parsed = json.loads(raw_text.strip())
                # Ensure rubric total_points
                if "rubric" in parsed:
                    parsed["rubric"]["total_points"] = 10.0
                return parsed
            except Exception as e:
                logger.warning(f"Gemini API call or JSON parsing error: {e}. Falling back to structured academic template.")

        # High-Fidelity Academic Generation Fallback
        templates = [
            {
                "prompt_prefix": f"Analyze the core principles of {objective_description}.",
                "sub_question": f"Focusing on {trait_name.lower()}, formulate the underlying mathematical or algorithmic relationships and evaluate edge-case constraints."
            },
            {
                "prompt_prefix": f"Construct an optimal algorithmic formulation addressing {objective_description}.",
                "sub_question": f"Demonstrate how {trait_name.lower()} governs state transitions and proof of correctness."
            },
            {
                "prompt_prefix": f"Critically evaluate trade-offs in {objective_description}.",
                "sub_question": f"Examine computational complexity and invariant properties aligned with {trait_name.lower()}."
            }
        ]
        chosen = templates[variation_index % len(templates)]
        question_text = f"{chosen['prompt_prefix']} {chosen['sub_question']}"

        return {
            "question": question_text,
            "rubric": {
                "total_points": 10.0,
                "criteria": [
                    {
                        "criterion": f"Formulation and technical accuracy of {objective_code}",
                        "max_points": 4.0,
                        "weight": 0.4
                    },
                    {
                        "criterion": f"Demonstration of {trait_name} and analytical justification",
                        "max_points": 3.0,
                        "weight": 0.3
                    },
                    {
                        "criterion": "Mathematical completeness and consideration of edge-case bounds",
                        "max_points": 3.0,
                        "weight": 0.3
                    }
                ]
            },
            "model_answer": (
                f"An authoritative response for {objective_code} establishes the formal problem definitions, identifies invariant properties, "
                f"and calculates asymptotic complexity bounds. It systematically applies {trait_name} to verify termination criteria and subproblem independence."
            ),
            "hint1": f"Begin by reviewing the fundamental definition and recurrences associated with {objective_code}.",
            "hint2": f"Structure your response around state transitions and verify correctness using the principle of {trait_name}."
        }

gemini_service = GeminiService()
