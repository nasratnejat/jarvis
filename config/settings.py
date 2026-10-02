import os

from dotenv import load_dotenv

load_dotenv(override=True)


# --------------------------------------------------
# Server
# --------------------------------------------------

HOST = os.getenv("JARVIS_HOST", "127.0.0.1")
PORT = int(os.getenv("JARVIS_PORT", "5000"))


# --------------------------------------------------
# AI
# --------------------------------------------------

MODEL = os.getenv("JARVIS_MODEL", "gpt-5.6-luna")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()


# --------------------------------------------------
# Application
# --------------------------------------------------

HISTORY_LIMIT = int(
    os.getenv("JARVIS_HISTORY_LIMIT", "20")
)


# --------------------------------------------------
# Environment
# --------------------------------------------------

DEBUG = os.getenv(
    "JARVIS_DEBUG",
    "false"
).lower() == "true"


# --------------------------------------------------
# Paths
# --------------------------------------------------

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATA_DIR = os.path.join(
    BASE_DIR,
    "data"
)

DATABASE_DIR = os.path.join(
    DATA_DIR,
    "database"
)

MEMORY_DIR = os.path.join(
    DATA_DIR,
    "memory"
)

CACHE_DIR = os.path.join(
    DATA_DIR,
    "cache"
)

LOG_DIR = os.path.join(
    DATA_DIR,
    "logs"
)