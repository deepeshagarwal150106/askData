import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# ── Page config ──────────────────────────────────────────────────────────────
PAGE_CONFIG = dict(
    page_title="DataPulse AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Available LLM models ─────────────────────────────────────────────────────
MODEL_OPTIONS = [
    "openai/gpt-oss-120b",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]


def init_groq_client() -> Groq:
    """Read GROQ_API_KEY from environment and return an initialised Groq client.

    Returns None if the key is not set (callers should handle this gracefully).
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None
    return Groq(api_key=api_key)
