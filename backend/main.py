"""
Development entrypoint.

Run with:  python main.py
Production: uvicorn app.main:app --host 0.0.0.0 --port 20285 --workers 4
"""
import uvicorn

from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=not settings.is_production,
    )
