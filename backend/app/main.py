from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.core.database import init_db
from app.api.auth import router as auth_router
from app.api.faculty import router as faculty_router
from app.api.student import router as student_router

logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("adaptive_assessment")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Adaptive Assessment Database tables...")
    try:
        init_db()
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
    yield
    logger.info("Shutting down Adaptive Assessment System.")

app = FastAPI(
    title=settings.APP_NAME,
    description="Adaptive Assessment System with Role-Based Authentication, Gemini AI & Privacy Safeguards",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(faculty_router, prefix=settings.API_V1_STR)
app.include_router(student_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "system": settings.APP_NAME,
        "status": "ONLINE",
        "docs_url": "/docs"
    }

@app.get("/api/health")
def health_check():
    return {
        "status": "HEALTHY",
        "database": "CONNECTED",
        "auth_modes": ["FACULTY_EMAIL_PASSWORD_OTP", "STUDENT_ROLL_PASSWORD"],
        "token_lifetimes": {
            "faculty_minutes": settings.FACULTY_TOKEN_EXPIRE_MINUTES,
            "student_minutes": settings.STUDENT_TOKEN_EXPIRE_MINUTES
        }
    }

