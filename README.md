# AI-Powered Adaptive Assessment System

An academic assessment platform engineered according to the algorithmic, privacy, and security specifications in `integrated_algorithm_auth_privacy.md`.

---

## 🏛️ System Architecture

- **Backend**: FastAPI (Python 3.10+ / 3.15) with Pydantic Settings
- **Database**: PostgreSQL (SQLAlchemy ORM with automated dev fallback to SQLite)
- **Frontend**: React + Vite, Tailwind CSS, Lucide Icons, and Recharts
- **Authentication**: JWT Sessions + Time-based Single-use OTP
- **AI Integration**: Gemini API (Isolated server-side service)
- **NLP & Similarity**: Sentence Transformers (`all-MiniLM-L6-v2`) & Scikit-learn Cosine Similarity

---

## 🔐 Authentication & Privacy Rules

1. **Faculty Experience**:
   - Authentication: Step 1 (Email + Password) $\rightarrow$ Step 2 (Secure 6-digit OTP).
   - Session Lifetime: Max **30 minutes**.
   - Privileged Access: Can review and approve question sets, inspect scoring rubrics, and view model answers.
2. **Student Experience**:
   - Authentication: Institutional Roll Number / Email + Password.
   - Session Lifetime: Max **60 minutes**.
   - Privacy Isolation: Students can view only their personal mastery scores.
   - **Zero Leakage**: Rubrics and model answers are strictly excluded from all student API responses.
3. **Session Revocation**:
   - Logout persists the JWT's `jti` to `token_blacklist`, immediately blocking token reuse.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Node.js** v18+ (tested on v22.18) & **npm**
- **Python** 3.10+ (tested on Python 3.15)
- Optional: PostgreSQL (if offline, SQLite database `./adaptive_assessment.db` is used automatically)

---

### 2. Backend Setup & Run

Open a terminal in the project root:

```bash
cd backend

# 1. Activate the Python virtual environment
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On macOS/Linux:
# source .venv/bin/activate

# 2. (Optional) Re-seed initial academic database with demo faculty & students
python seed_data.py

# 3. Start the FastAPI backend server
python -m uvicorn app.main:app --reload --port 8000
```

Backend will be active at:
- **API Base**: `http://localhost:8000`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/api/health`

---

### 3. Frontend Setup & Run

Open a separate terminal in the project root:

```bash
cd frontend

# Start the Vite development server
npm run dev
```

Frontend will be active at:
- **Web Portal**: `http://localhost:5173`

---

## 🔑 Pre-Seeded Demo Credentials

| Role | Identifier / Email | Password | OTP Flow / Session Notes |
| :--- | :--- | :--- | :--- |
| **Faculty** | `faculty@university.edu` | `FacultyPass123!` | 6-Digit OTP generated in console / dev helper (30 min token) |
| **Student** | `ROLL2026001` (or `student@university.edu`) | `StudentPass123!` | Direct roll-number sign-in (60 min token) |

---

## 🧪 Running Automated Tests

Run backend tests for authentication, authorization role guards, session revocation, and rubric privacy:

```bash
cd backend
.\.venv\Scripts\python.exe -m pytest tests/
```

