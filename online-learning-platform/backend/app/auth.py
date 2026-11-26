"""Token based authentication and role checks."""
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import current_app, g, request

from .db import get_db
from .errors import ApiError

USER_QUERY = """
    SELECT u.*, i.headline, i.bio, i.expertise, i.is_approved
    FROM users u LEFT JOIN instructors i ON i.user_id = u.id
    WHERE u.id = ?
"""


def create_token(user):
    expires = datetime.now(timezone.utc) + timedelta(hours=current_app.config["TOKEN_HOURS"])
    payload = {"sub": str(user["id"]), "ver": user["token_version"], "exp": expires}
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


def load_user():
    """Returns the signed-in user or None. Raises 401 for a bad or expired token."""
    if "user" in g:
        return g.user
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        g.user = None
        return None
    try:
        payload = jwt.decode(header[7:], current_app.config["SECRET_KEY"], algorithms=["HS256"],
                             options={"require": ["exp", "sub"]})
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, ValueError):
        raise ApiError("Your session has expired. Please log in again.", 401)
    # Loaded on every request so deactivation and password changes apply immediately.
    user = get_db().one(USER_QUERY, (user_id,))
    if not user or not user["is_active"] or user["token_version"] != payload.get("ver"):
        raise ApiError("Your session is no longer valid. Please log in again.", 401)
    g.user = user
    return user


def login_required(*roles):
    """Decorator: requires a signed-in user, optionally with one of the given roles."""
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = load_user()
            if not user:
                raise ApiError("Please log in to continue.", 401)
            if roles and user["role"] not in roles:
                raise ApiError("You do not have permission to do that.", 403)
            if user["role"] == "instructor" and roles and not user["is_approved"]:
                raise ApiError("Your instructor account is waiting for admin approval.", 403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


def can_manage(user, course):
    if not user:
        return False
    if user["role"] == "admin":
        return True
    return (user["role"] == "instructor" and bool(user["is_approved"])
            and course["instructor_id"] == user["id"])
