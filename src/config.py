import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


def _to_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _to_int(value: str, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

class Config:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    APP_CLOUD_MODE = _to_bool(os.getenv("APP_CLOUD_MODE"), default=False)
    GIT_TIMEOUT_SECONDS = _to_int(os.getenv("GIT_TIMEOUT_SECONDS"), default=180)
    REPO_CACHE_TTL_HOURS = _to_int(os.getenv("REPO_CACHE_TTL_HOURS"), default=24)
    RATE_LIMIT_MAX_REQUESTS = _to_int(os.getenv("RATE_LIMIT_MAX_REQUESTS"), default=5)
    RATE_LIMIT_WINDOW_SECONDS = _to_int(os.getenv("RATE_LIMIT_WINDOW_SECONDS"), default=300)
    
    if GOOGLE_API_KEY:
        genai.configure(api_key=GOOGLE_API_KEY)