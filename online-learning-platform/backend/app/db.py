"""A thin database layer that works with SQLite (local) and PostgreSQL (cloud).

SQL is written with "?" placeholders and kept portable. Rows come back as dicts.
"""
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from flask import current_app, g

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "database" / "schema.sql"


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Database:
    def __init__(self, raw, is_postgres):
        self.raw = raw
        self.is_postgres = is_postgres

    def execute(self, sql, params=()):
        if self.is_postgres:
            sql = sql.replace("%", "%%").replace("?", "%s")
        return self.raw.execute(sql, tuple(params))

    def all(self, sql, params=()):
        return [dict(row) for row in self.execute(sql, params).fetchall()]

    def one(self, sql, params=()):
        rows = self.all(sql, params)
        return rows[0] if rows else None

    def scalar(self, sql, params=()):
        row = self.one(sql, params)
        return next(iter(row.values())) if row else None

    def insert(self, sql, params=()):
        """Runs an INSERT and returns the new row's id."""
        return self.all(sql + " RETURNING id", params)[0]["id"]

    def commit(self):
        self.raw.commit()

    def rollback(self):
        self.raw.rollback()

    def close(self):
        self.raw.close()


def connect(url):
    if url.startswith("sqlite:///"):
        path = url[len("sqlite:///"):]
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        raw = sqlite3.connect(path, timeout=15)
        raw.row_factory = sqlite3.Row
        raw.execute("PRAGMA foreign_keys = ON")
        return Database(raw, is_postgres=False)
    if url.startswith("postgresql://"):
        import psycopg
        from psycopg.rows import dict_row

        # prepare_threshold=None keeps the app compatible with connection poolers.
        raw = psycopg.connect(url, row_factory=dict_row, prepare_threshold=None)
        return Database(raw, is_postgres=True)
    raise RuntimeError("DATABASE_URL must start with sqlite:/// or postgresql://")


def init_db(url):
    """Creates missing tables and indexes. Safe to run repeatedly."""
    db = connect(url)
    try:
        script = SCHEMA_PATH.read_text(encoding="utf-8")
        if db.is_postgres:
            # Stops two server processes creating the same table at the same moment.
            db.execute("SELECT pg_advisory_xact_lock(727274)")
        else:
            script = script.replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
        lines = [line.split("--", 1)[0] for line in script.splitlines()]
        for statement in "\n".join(lines).split(";"):
            if statement.strip():
                db.execute(statement)
        if db.is_postgres:
            # Hosts such as Supabase can expose tables through their own web API. With row
            # level security on and no policies, only the table owner (this app) can read them.
            for table in re.findall(r"CREATE TABLE IF NOT EXISTS (\w+)", script):
                db.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        db.commit()
    finally:
        db.close()


def get_db():
    """The current request's connection (opened on first use)."""
    if "db" not in g:
        g.db = connect(current_app.config["DATABASE_URL"])
    return g.db


def register_db(app):
    @app.after_request
    def commit_or_rollback(response):
        db = g.get("db")
        succeeded = response.status_code < 400
        if db is not None:
            if succeeded:
                db.commit()
            else:
                db.rollback()
        # Files are only removed once the database change that orphaned them is saved.
        keys = g.pop("delete_on_success" if succeeded else "delete_on_failure", [])
        for key in keys:
            if key:
                app.extensions["storage"].delete(key)
        return response

    @app.teardown_appcontext
    def close_db(_error):
        db = g.pop("db", None)
        if db is not None:
            db.close()
