"""Configuration loaded from environment / .env file."""
import os
from dotenv import load_dotenv

load_dotenv()

# --- API tokens ---
WAQI_TOKEN = os.getenv("WAQI_TOKEN", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENWEATHER_KEY = os.getenv("OPENWEATHER_KEY", "")  # optional fallback source

# --- Model / endpoints ---
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
WAQI_BASE_URL = "https://api.waqi.info"

# --- Cache TTLs (seconds) ---
AQI_TTL = int(os.getenv("AQI_TTL", "300"))      # 5 min for air data
PLAN_TTL = int(os.getenv("PLAN_TTL", "600"))    # 10 min for generated plans

# --- Supported areas: friendly name -> WAQI station/city keyword ---
AREAS = {
    "lahore": "lahore",
    "lahore-cantt": "@8245",          # example station id; swap for real
    "karachi": "karachi",
    "karachi-korangi": "karachi/korangi",
    "islamabad": "islamabad",
    "islamabad-diplomatic-enclave": "@10670",   # example station id; swap for real
}
DEFAULT_AREA = "lahore"

CACHE_DB = os.getenv("CACHE_DB", "saafhawa.db")
