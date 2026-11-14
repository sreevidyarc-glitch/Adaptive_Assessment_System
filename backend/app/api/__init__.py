from app.api.auth import router as auth_router
from app.api.faculty import router as faculty_router
from app.api.student import router as student_router

__all__ = ["auth_router", "faculty_router", "student_router"]

