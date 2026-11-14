"""
Root entry point for the Adaptive Assessment FastAPI Backend.
Enables running the application using either:
    uvicorn app.main:app
or:
    uvicorn main:app
"""
import os
import uvicorn
from app.main import app

if __name__ == "__main__":
    # Render binds the assigned external port via the PORT environment variable
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
