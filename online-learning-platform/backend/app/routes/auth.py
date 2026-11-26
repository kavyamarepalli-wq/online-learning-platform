"""Registration, sign-in and the signed-in user's own account."""
from flask import Blueprint, g, jsonify
from werkzeug.security import check_password_hash, generate_password_hash

from .. import ratelimit
from ..auth import USER_QUERY, create_token, login_required
from ..db import get_db, now
from ..errors import ApiError
from ..services.activity import log
from ..services.users import create_user, public_user
from ..validation import Validator, json_body

bp = Blueprint("auth", __name__)

# Compared against when the email is unknown, so both failures take similar time.
_DUMMY_HASH = generate_password_hash("not-a-real-password")


def _session(user):
    return {"token": create_token(user), "user": public_user(user)}


@bp.post("/auth/register")
def register():
    ratelimit.limit("register", 50, 3600)
    form = Validator(json_body())
    name = form.string("name", "Name", 2, 100)
    email = form.email()
    password = form.password()
    # Administrators can never be created through public registration.
    role = form.choice("role", "Role", ("student", "instructor"), default="student")
    headline = bio = ""
    if role == "instructor":
        headline = form.string("headline", "Professional headline", 3, 150)
        bio = form.string("bio", "Short bio", 0, 2000)
    form.check()

    db = get_db()
    user_id = create_user(db, name, email, password, role, headline=headline, bio=bio)
    db.execute("UPDATE users SET last_login_at = ? WHERE id = ?", (now(), user_id))
    log(db, user_id, "registered", f"{name} registered as {role}")
    user = db.one(USER_QUERY, (user_id,))
    return jsonify(_session(user)), 201


@bp.post("/auth/login")
def login():
    form = Validator(json_body())
    email = form.email()
    password = form.data.get("password")
    if not isinstance(password, str) or not password:
        form.errors["password"] = "Password is required."
    form.check()
    ratelimit.limit("login", 10, 300, email)

    db = get_db()
    row = db.one("SELECT id, password_hash, is_active FROM users WHERE email = ?", (email,))
    valid = check_password_hash(row["password_hash"] if row else _DUMMY_HASH, password[:128])
    if not row or not valid:
        raise ApiError("Incorrect email or password.", 401)
    if not row["is_active"]:
        raise ApiError("This account has been deactivated. Contact the administrator.", 403)
    db.execute("UPDATE users SET last_login_at = ? WHERE id = ?", (now(), row["id"]))
    log(db, row["id"], "logged_in", email)
    return jsonify(_session(db.one(USER_QUERY, (row["id"],))))


@bp.get("/auth/me")
@login_required()
def me():
    return jsonify({"user": public_user(g.user)})


@bp.put("/auth/profile")
@login_required()
def update_profile():
    form = Validator(json_body())
    name = form.string("name", "Name", 2, 100)
    is_instructor = g.user["role"] == "instructor"
    if is_instructor:
        headline = form.string("headline", "Professional headline", 3, 150)
        bio = form.string("bio", "Short bio", 0, 2000)
        expertise = form.string("expertise", "Expertise", 0, 200)
    form.check()

    db = get_db()
    db.execute("UPDATE users SET name = ? WHERE id = ?", (name, g.user["id"]))
    if is_instructor:
        db.execute("UPDATE instructors SET headline = ?, bio = ?, expertise = ? WHERE user_id = ?",
                   (headline, bio, expertise, g.user["id"]))
    return jsonify({"user": public_user(db.one(USER_QUERY, (g.user["id"],)))})


@bp.put("/auth/password")
@login_required()
def change_password():
    ratelimit.limit("password", 10, 300, str(g.user["id"]))
    form = Validator(json_body())
    current = form.data.get("current_password")
    new = form.password("new_password")
    if not isinstance(current, str) or not check_password_hash(g.user["password_hash"], current):
        form.errors["current_password"] = "Your current password is incorrect."
    form.check()

    db = get_db()
    # Raising token_version signs out every other session.
    db.execute("""UPDATE users SET password_hash = ?, token_version = token_version + 1
                  WHERE id = ?""", (generate_password_hash(new), g.user["id"]))
    log(db, g.user["id"], "password_changed")
    return jsonify(_session(db.one(USER_QUERY, (g.user["id"],))))
