import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL

ML_DIR = Path(__file__).resolve().parents[1]

# ml/.env is optional (DATABASE_URL override); the repo-root .env is the shared
# source for POSTGRES_* values. Both are gitignored; see .env.example files.
load_dotenv(ML_DIR / ".env")
load_dotenv(ML_DIR.parent / ".env")


def get_database_url():
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    try:
        return URL.create(
            "postgresql+psycopg2",
            username=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"],
            host=os.environ["POSTGRES_HOST"],
            port=int(os.environ.get("POSTGRES_PORT", 5432)),
            database=os.environ["POSTGRES_DB"],
        ).render_as_string(hide_password=False)
    except KeyError as missing:
        raise RuntimeError(
            f"Database settings missing ({missing}). Set DATABASE_URL in ml/.env "
            "or POSTGRES_* in the repo-root .env."
        ) from None
