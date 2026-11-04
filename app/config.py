"""Application configuration, read from environment variables (or a .env file)."""
import os
from urllib.parse import quote_plus

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def build_database_uri() -> str:
    """Use Amazon RDS (MySQL) when DB_HOST is set, otherwise a local SQLite file."""
    if os.getenv("DATABASE_URL"):
        return os.environ["DATABASE_URL"]
    host = os.getenv("DB_HOST", "").strip()
    if not host:
        return "sqlite:///" + os.path.join(BASE_DIR, "nimbus_local.db")
    user = quote_plus(os.getenv("DB_USER", "admin"))
    password = quote_plus(os.getenv("DB_PASSWORD", ""))
    port = os.getenv("DB_PORT", "3306")
    name = os.getenv("DB_NAME", "nimbus")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}?charset=utf8mb4"


# Demo data must never be passed off as live data. It is off unless switched on.
DEMO_FALLBACK_DEFAULT = False


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = build_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Recycle connections so RDS idle timeouts don't break requests. On MySQL each
    # Gunicorn worker keeps at most 3 + 2 connections, so 3 workers x 3 servers
    # stay well inside what a small RDS instance accepts.
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 280,
                                 **({"pool_size": 3, "max_overflow": 2}
                                    if SQLALCHEMY_DATABASE_URI.startswith("mysql") else {})}

    MARKET_DATA_PROVIDER = os.getenv("MARKET_DATA_PROVIDER", "yahoo").lower()
    DEMO_FALLBACK = _bool("DEMO_FALLBACK", DEMO_FALLBACK_DEFAULT)
    CACHE_TTL = int(os.getenv("CACHE_TTL", "900"))
    SNAPSHOT_ARCHIVE_BUCKET = os.getenv("SNAPSHOT_ARCHIVE_BUCKET", "")

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = _bool("SESSION_COOKIE_SECURE", False)
    SESSION_COOKIE_SAMESITE = "Lax"
    MAX_COMPARE_TICKERS = 5
    # The Save form carries the comparison shown on screen: up to ~0.5 MB for 5 companies over 5 years.
    MAX_FORM_MEMORY_SIZE = 4 * 1024 * 1024

    # Set by the CloudFormation user data; shown in the footer so you can tell which
    # server answered and which commit it runs (empty when running locally).
    NIMBUS_COMMIT = os.getenv("NIMBUS_COMMIT", "")
    NIMBUS_INSTANCE_ID = os.getenv("NIMBUS_INSTANCE_ID", "")


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {}
    MARKET_DATA_PROVIDER = "demo"
    SECRET_KEY = "test"
