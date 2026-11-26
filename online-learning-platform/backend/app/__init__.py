"""Application factory."""
import os
from pathlib import Path

from flask import Flask, request, send_from_directory
from flask.json.provider import DefaultJSONProvider
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import load_config
from .db import connect, init_db, register_db
from .errors import ApiError, error_response, register_error_handlers
from .storage import build_storage


def create_app(overrides=None):
    app = Flask(__name__, static_folder=None)
    app.config.update(load_config(overrides))
    app.config["MAX_CONTENT_LENGTH"] = (app.config["MAX_UPLOAD_MB"] + 1) * 1024 * 1024
    app.json = DefaultJSONProvider(app)
    app.json.sort_keys = False

    if app.config["TRUSTED_PROXIES"]:
        hops = app.config["TRUSTED_PROXIES"]
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=hops, x_proto=hops, x_host=hops)

    app.extensions["storage"] = build_storage(app.config)
    init_db(app.config["DATABASE_URL"])
    _bootstrap_admin(app)

    register_error_handlers(app)
    register_db(app)
    _register_headers(app)

    from .routes import admin, auth, catalog, files, learning, manage
    for module in (auth, catalog, learning, manage, admin, files):
        app.register_blueprint(module.bp, url_prefix="/api" + (module.bp.url_prefix or ""))

    _register_frontend(app)
    return app


def _bootstrap_admin(app):
    """Creates the first administrator from ADMIN_EMAIL / ADMIN_PASSWORD, if configured."""
    email, password = app.config["ADMIN_EMAIL"], app.config["ADMIN_PASSWORD"]
    if not email or not password:
        return
    from .services.users import create_user
    from .validation import password_problem

    db = connect(app.config["DATABASE_URL"])
    try:
        if db.one("SELECT id FROM users WHERE role = 'admin' LIMIT 1"):
            return
        problem = password_problem(password)
        if problem:
            raise RuntimeError(f"ADMIN_PASSWORD is not acceptable: {problem}")
        if db.one("SELECT id FROM users WHERE email = ?", (email,)):
            app.logger.warning("ADMIN_EMAIL already belongs to another account; no admin created.")
            return
        try:
            create_user(db, app.config["ADMIN_NAME"], email, password, "admin")
            db.commit()
        except ApiError:
            db.rollback()  # another server process created it a moment earlier
    finally:
        db.close()


def _register_headers(app):
    @app.after_request
    def add_headers(response):
        origin = request.headers.get("Origin", "")
        if request.path.startswith("/api") and origin in app.config["CORS_ORIGINS"]:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Expose-Headers"] = "Content-Disposition"
            response.headers["Access-Control-Max-Age"] = "600"
        response.vary.add("Origin")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        if request.path.startswith("/api") and "Cache-Control" not in response.headers:
            response.headers["Cache-Control"] = "no-store"
        return response


def _register_frontend(app):
    """Serves the built frontend from the same server when frontend/dist exists."""
    dist = Path(app.config["FRONTEND_DIST"])

    @app.get("/")
    @app.get("/<path:path>")
    def frontend(path=""):
        if path == "api" or path.startswith("api/"):
            return error_response("Unknown API endpoint.", 404)
        if not (dist / "index.html").exists():
            return error_response("The frontend has not been built. See docs/SETUP.md.", 404)
        if path and os.path.isfile(os.path.join(dist, path)):
            return send_from_directory(dist, path)
        if path.startswith("assets/"):
            return error_response("File not found.", 404)
        response = send_from_directory(dist, "index.html")
        response.headers["Cache-Control"] = "no-cache"
        return response
