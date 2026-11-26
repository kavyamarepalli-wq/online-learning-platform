from werkzeug.security import generate_password_hash

from ..db import now
from ..errors import ApiError


def create_user(db, name, email, password, role, approved=False, headline="", bio="", expertise=""):
    """Creates a user (and the instructor profile when relevant) and returns the id."""
    row = db.one(
        """INSERT INTO users (name, email, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)
           ON CONFLICT (email) DO NOTHING RETURNING id""",
        (name, email, generate_password_hash(password), role, now()))
    if not row:
        message = "An account with this email already exists."
        raise ApiError(message, 409, {"email": message})
    if role == "instructor":
        db.execute(
            """INSERT INTO instructors (user_id, headline, bio, expertise, is_approved, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (row["id"], headline, bio, expertise, int(approved), now()))
    return row["id"]


def public_user(user):
    data = {key: user[key] for key in ("id", "name", "email", "role", "created_at")}
    data["is_active"] = bool(user["is_active"])
    data["last_login_at"] = user.get("last_login_at")
    if user["role"] == "instructor":
        data.update(headline=user.get("headline") or "", bio=user.get("bio") or "",
                    expertise=user.get("expertise") or "",
                    is_approved=bool(user.get("is_approved")))
    return data
