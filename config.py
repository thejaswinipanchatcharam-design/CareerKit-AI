"""
CareerKit AI - Application Configuration Module
Centralizes all environment variables, security keys, database paths,
upload restrictions, and AI provider parameters.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the CareerKit-AI application
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env if present
load_dotenv(BASE_DIR / ".env")


class Config:
    """Base configuration loaded from environment variables."""

    # Security: Secret key for session management and CSRF protection
    SECRET_KEY = os.getenv(
        "SECRET_KEY", "careerkit-dev-fallback-secret-key-replace-in-production"
    )

    # SQLite Database location
    DATABASE_PATH = os.getenv(
        "DATABASE_PATH", str(BASE_DIR / "data" / "careerkit.db")
    )

    # File Upload & Export Boundaries
    UPLOAD_FOLDER = str(BASE_DIR / "uploads")
    EXPORT_FOLDER = str(BASE_DIR / "exports")
    MAX_CONTENT_LENGTH = int(
        os.getenv("MAX_CONTENT_LENGTH", 10 * 1024 * 1024)
    )  # 10 MB maximum upload
    ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}

    # AI Provider Settings
    AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").strip().lower()

    # Google Gemini API
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

    # Groq API
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()

    # Environment
    ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = os.getenv("FLASK_DEBUG", "1") in ("1", "true", "True")

    @classmethod
    def is_ai_configured(cls) -> bool:
        """Returns True if the active AI provider has an API key configured."""
        if cls.AI_PROVIDER == "gemini":
            return bool(cls.GEMINI_API_KEY)
        elif cls.AI_PROVIDER == "groq":
            return bool(cls.GROQ_API_KEY)
        return False

    @classmethod
    def get_active_provider_info(cls) -> dict:
        """Returns diagnostic info about the active provider without exposing secrets."""
        provider = cls.AI_PROVIDER
        if provider == "gemini":
            return {
                "provider": "Google Gemini",
                "model": cls.GEMINI_MODEL,
                "configured": bool(cls.GEMINI_API_KEY),
                "key_preview": f"...{cls.GEMINI_API_KEY[-4:]}"
                if len(cls.GEMINI_API_KEY) >= 4
                else "Not set",
            }
        elif provider == "groq":
            return {
                "provider": "Groq",
                "model": cls.GROQ_MODEL,
                "configured": bool(cls.GROQ_API_KEY),
                "key_preview": f"...{cls.GROQ_API_KEY[-4:]}"
                if len(cls.GROQ_API_KEY) >= 4
                else "Not set",
            }
        else:
            return {
                "provider": provider,
                "model": "Unknown",
                "configured": False,
                "key_preview": "Unsupported Provider",
            }


class TestConfig(Config):
    """Configuration for automated test execution."""

    TESTING = True
    WTF_CSRF_ENABLED = False  # Allows streamlined route testing with test client
    DATABASE_PATH = ":memory:"  # In-memory database for fast, isolated tests
