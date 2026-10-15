import os
from pathlib import Path

from dotenv import load_dotenv

# ml/.env holds local credentials (gitignored); see ml/.env.example
load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def get_database_url():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set. Copy ml/.env.example to ml/.env and fill it in.")
    return url
