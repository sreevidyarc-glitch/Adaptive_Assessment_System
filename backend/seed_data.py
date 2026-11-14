"""
Seed data script for the Adaptive Assessment System.
Creates default Faculty, Student accounts, Course, Objectives, Traits, Questions with Rubrics,
and Mastery Scores.
"""
import sys
import os

# Add parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal, init_db
from app.core.security import hash_password
from app.models.user import User, RoleEnum
from app.models.course import Course, CourseObjective, FacultyAssignment, CourseEnrollment
from app.models.question import Trait, Question, Rubric, ModelAnswer
from app.models.assessment import MasteryScore, AssessmentSession, AssessmentStatusEnum

def seed():
    print("Initializing tables...")
    init_db()
    db = SessionLocal()

    try:
        # 1. Seed Faculty
        faculty = db.query(User).filter(User.email == "faculty@university.edu").first()
        if not faculty:
            faculty = User(
                email="faculty@university.edu",
                full_name="Dr. Eleanor Vance",
                hashed_password=hash_password("FacultyPass123!"),
                role=RoleEnum.FACULTY,
                department="Computer Science & Engineering"
            )
            db.add(faculty)
            db.commit()
            db.refresh(faculty)
            print("Created Faculty account: faculty@university.edu / FacultyPass123!")
        else:
            print("Faculty account already exists.")

        # 2. Seed Student
        student = db.query(User).filter(User.email == "student@university.edu").first()
        if not student:
            student = User(
                email="student@university.edu",
                roll_number="ROLL2026001",
                full_name="Alex Chen",
                hashed_password=hash_password("StudentPass123!"),
                role=RoleEnum.STUDENT,
                department="Computer Science & Engineering"
            )
            db.add(student)
            db.commit()
            db.refresh(student)
            print("Created Student account: ROLL2026001 (student@university.edu) / StudentPass123!")
        else:
            print("Student account already exists.")

        # 3. Seed Traits
        traits_data = [
            ("TR_CONCEPT", "Conceptual Clarity", "Understanding of foundational mathematical and computational principles"),
            ("TR_PROBLEM", "Problem Solving", "Translating problem statements into algorithmic solutions"),
            ("TR_ANALYSIS", "Analytical Rigor", "Mathematical verification of time/space complexity and invariants")
        ]
        traits = {}
        for code, name, desc in traits_data:
            trait = db.query(Trait).filter(Trait.code == code).first()
            if not trait:
                trait = Trait(code=code, name=name, description=desc)
                db.add(trait)
                db.commit()
                db.refresh(trait)
            traits[code] = trait

        # 4. Seed Course
        course = db.query(Course).filter(Course.course_code == "CS401").first()
        if not course:
            course = Course(
                course_code="CS401",
                title="Design & Analysis of Algorithms",
                description="Core algorithmic paradigms: greedy algorithms, dynamic programming, graph flows, and amortized complexity."
            )
            db.add(course)
            db.commit()
            db.refresh(course)
            print("Created Course: CS401")

        # 5. Seed Objectives
        co1 = db.query(CourseObjective).filter(CourseObjective.course_id == course.id, CourseObjective.code == "CO1").first()
        if not co1:
            co1 = CourseObjective(
                course_id=course.id,
                code="CO1",
                description="Formulate recursive state transitions and dynamic programming memoization tables.",
                weight=1.2
            )
            db.add(co1)

        co2 = db.query(CourseObjective).filter(CourseObjective.course_id == course.id, CourseObjective.code == "CO2").first()
        if not co2:
            co2 = CourseObjective(
                course_id=course.id,
                code="CO2",
                description="Analyze single-source and all-pairs shortest path algorithms on directed acyclic and cyclic graphs.",
                weight=1.0
            )
            db.add(co2)

        co3 = db.query(CourseObjective).filter(CourseObjective.course_id == course.id, CourseObjective.code == "CO3").first()
        if not co3:
            co3 = CourseObjective(
                course_id=course.id,
                code="CO3",
                description="Evaluate NP-completeness reductions and polynomial-time verification mechanisms.",
                weight=0.8
            )
            db.add(co3)

        db.commit()
        db.refresh(co1)
        db.refresh(co2)
        db.refresh(co3)

        # 6. Faculty Assignment
        assignment = db.query(FacultyAssignment).filter(
            FacultyAssignment.faculty_id == faculty.id,
            FacultyAssignment.course_id == course.id
        ).first()
        if not assignment:
            assignment = FacultyAssignment(faculty_id=faculty.id, course_id=course.id)
            db.add(assignment)

        # 7. Student Enrollment
        enrollment = db.query(CourseEnrollment).filter(
            CourseEnrollment.student_id == student.id,
            CourseEnrollment.course_id == course.id
        ).first()
        if not enrollment:
            enrollment = CourseEnrollment(student_id=student.id, course_id=course.id)
            db.add(enrollment)

        db.commit()

        # 8. Seed Questions with Rubrics and Model Answers
        q1 = db.query(Question).filter(Question.course_id == course.id, Question.prompt.like("%Bellman-Ford%")).first()
        if not q1:
            q1 = Question(
                course_id=course.id,
                objective_id=co2.id,
                trait_id=traits["TR_ANALYSIS"].id,
                prompt="Explain how the Bellman-Ford algorithm detects negative-weight cycles in a directed graph. Contrast its complexity with Dijkstra's algorithm.",
                hint1="Consider what happens during the |V|-th relaxation iteration if a negative cycle exists.",
                hint2="Remember Dijkstra's greedy choice assumes non-negative edge weights.",
                is_approved=True,
                approved_by=faculty.id,
                is_published=True
            )
            db.add(q1)
            db.commit()
            db.refresh(q1)

            # Privileged Rubric (Visible to Faculty Only)
            r1 = Rubric(
                question_id=q1.id,
                total_points=10.0,
                criteria=[
                    {"criterion": "Explanation of |V|-th iteration relaxation condition", "max_points": 4.0, "weight": 0.4},
                    {"criterion": "Complexity comparison (O(VE) vs O((V+E)log V))", "max_points": 3.0, "weight": 0.3},
                    {"criterion": "Correct negative cycle proof rationale", "max_points": 3.0, "weight": 0.3}
                ]
            )
            # Privileged Model Answer (Visible to Faculty Only)
            m1 = ModelAnswer(
                question_id=q1.id,
                content="Bellman-Ford relaxes all edges |V|-1 times. If any edge can still be relaxed in the |V|-th pass, a reachable negative-weight cycle exists. Dijkstra greedily visits nodes and cannot correct previously finalized distances under negative edges.",
                explanation="Standard reference from CLRS Chapter 24."
            )
            db.add(r1)
            db.add(m1)

        q2 = db.query(Question).filter(Question.course_id == course.id, Question.prompt.like("%Knapsack%")).first()
        if not q2:
            q2 = Question(
                course_id=course.id,
                objective_id=co1.id,
                trait_id=traits["TR_PROBLEM"].id,
                prompt="Formulate the 2D dynamic programming recurrence relation for the 0/1 Knapsack problem with capacity W and items {(w_i, v_i)}.",
                hint1="Define dp[i][w] as the maximum value achievable considering the first i items.",
                hint2="At step i, branch between excluding item i vs including item i (if w_i <= w).",
                is_approved=False,  # PENDING APPROVAL IN FACULTY DASHBOARD
                is_published=False
            )
            db.add(q2)
            db.commit()
            db.refresh(q2)

            r2 = Rubric(
                question_id=q2.id,
                total_points=10.0,
                criteria=[
                    {"criterion": "Correct base cases definition", "max_points": 3.0, "weight": 0.3},
                    {"criterion": "Accurate inclusion/exclusion recursive relation", "max_points": 5.0, "weight": 0.5},
                    {"criterion": "Boundary and capacity constraints check", "max_points": 2.0, "weight": 0.2}
                ]
            )
            m2 = ModelAnswer(
                question_id=q2.id,
                content="dp[i][w] = max(dp[i-1][w], dp[i-1][w-w_i] + v_i) for w >= w_i, otherwise dp[i-1][w]. Base case: dp[0][w] = dp[i][0] = 0.",
                explanation="Demonstrates optimal substructure and overlapping subproblems."
            )
            db.add(r2)
            db.add(m2)

        db.commit()

        # 9. Seed Student Mastery Scores
        tau = 0.75  # Target mastery threshold from specification
        mastery_samples = [
            (co1.id, traits["TR_CONCEPT"].id, 0.82, "REINFORCEMENT"),
            (co1.id, traits["TR_PROBLEM"].id, 0.64, "REINFORCEMENT"),
            (co2.id, traits["TR_ANALYSIS"].id, 0.48, "REINFORCEMENT"),
            (co3.id, traits["TR_CONCEPT"].id, 0.22, "FOUNDATIONAL"),  # Below 0.3 -> Foundational pack
        ]

        for obj_id, trait_id, m_val, rec_type in mastery_samples:
            existing = db.query(MasteryScore).filter(
                MasteryScore.student_id == student.id,
                MasteryScore.course_id == course.id,
                MasteryScore.objective_id == obj_id,
                MasteryScore.trait_id == trait_id
            ).first()
            if not existing:
                gap = (tau - m_val) * 1.0
                score = MasteryScore(
                    student_id=student.id,
                    course_id=course.id,
                    objective_id=obj_id,
                    trait_id=trait_id,
                    mastery_value=m_val,
                    gap_score=max(0.0, gap),
                    recommendation_type=rec_type
                )
                db.add(score)

        db.commit()
        print("Database seeded successfully with initial Faculty, Student, and Assessment data!")

    finally:
        db.close()

if __name__ == "__main__":
    seed()

