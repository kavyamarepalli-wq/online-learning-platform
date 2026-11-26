"""Settings read from environment variables (and backend/.env during development)."""
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BACKEND_DIR.parent

CATEGORIES = [
    "Web Development",
    "Programming",
    "Databases",
    "Design",
    "Cloud Computing",
    "Data Science",
    "Business",
    "Other",
]
LEVELS = ["Beginner", "Intermediate", "Advanced"]


def _persistent_dev_secret(instance_dir):
    """Keeps local sessions valid across restarts without asking for a secret."""
    path = instance_dir / "dev-secret"
    if not path.exists():
        path.write_text(secrets.token_urlsafe(48), encoding="utf-8")
    return path.read_text(encoding="utf-8").strip()


def load_config(overrides=None):
    load_dotenv(BACKEND_DIR / ".env")
    overrides = overrides or {}

    def env(name, default=""):
        if name in overrides:
            return overrides[name]
        return os.environ.get(name, "").strip() or default

    instance_dir = BACKEND_DIR / "instance"
    app_env = env("APP_ENV", "development")
    database_url = env("DATABASE_URL", f"sqlite:///{instance_dir / 'learnsphere.db'}")
    # Some hosts hand out the older "postgres://" scheme.
    if database_url.startswith("postgres://"):
        database_url = "postgresql://" + database_url[len("postgres://"):]

    secret = env("SECRET_KEY")
    if app_env == "production":
        if len(secret) < 32:
            raise RuntimeError("SECRET_KEY (at least 32 characters) is required in production.")
        if database_url.startswith("sqlite") and not env("ALLOW_SQLITE_IN_PRODUCTION"):
            raise RuntimeError("DATABASE_URL must point to PostgreSQL in production.")
    else:
        instance_dir.mkdir(exist_ok=True)
        secret = secret or _persistent_dev_secret(instance_dir)

    storage = env("STORAGE_BACKEND", "local").lower()
    if storage not in ("local", "s3"):
        raise RuntimeError("STORAGE_BACKEND must be 'local' or 's3'.")

    frontend_url = env("FRONTEND_URL").rstrip("/")
    origins = {frontend_url} if frontend_url else set()
    origins.update(o.strip().rstrip("/") for o in env("CORS_ORIGINS").split(",") if o.strip())
    if app_env == "development":
        origins.update({"http://localhost:5173", "http://127.0.0.1:5173"})

    config = {
        "APP_ENV": app_env,
        "SECRET_KEY": secret,
        "DATABASE_URL": database_url,
        "FRONTEND_URL": frontend_url,
        "CORS_ORIGINS": origins,
        "PUBLIC_API_URL": env("PUBLIC_API_URL").rstrip("/"),
        "STORAGE_BACKEND": storage,
        "UPLOAD_DIR": env("UPLOAD_DIR", str(BACKEND_DIR / "uploads")),
        "MAX_UPLOAD_MB": int(env("MAX_UPLOAD_MB", "100")),
        "S3_ENDPOINT": env("S3_ENDPOINT").rstrip("/"),
        "S3_REGION": env("S3_REGION", "us-east-1"),
        "S3_BUCKET": env("S3_BUCKET"),
        "S3_ACCESS_KEY_ID": env("S3_ACCESS_KEY_ID"),
        "S3_SECRET_ACCESS_KEY": env("S3_SECRET_ACCESS_KEY"),
        "ADMIN_NAME": env("ADMIN_NAME", "Platform Admin"),
        "ADMIN_EMAIL": env("ADMIN_EMAIL").lower(),
        "ADMIN_PASSWORD": env("ADMIN_PASSWORD"),
        "TRUSTED_PROXIES": int(env("TRUSTED_PROXIES", "0")),
        "TOKEN_HOURS": int(env("TOKEN_HOURS", "24")),
        "RATE_LIMITS": env("RATE_LIMITS", "on") != "off",
        "FRONTEND_DIST": env("FRONTEND_DIST", str(PROJECT_DIR / "frontend" / "dist")),
    }
    if storage == "s3":
        missing = [k for k in ("S3_ENDPOINT", "S3_BUCKET", "S3_ACCESS_KEY_ID", "S3_SECRET_ACCESS_KEY")
                   if not config[k]]
        if missing:
            raise RuntimeError("Missing storage settings: " + ", ".join(missing))
    return config
