"""Administrator dashboard: users, enrollments, results and platform activity."""
from datetime import datetime, timedelta, timezone

from flask import Blueprint, g, jsonify, request
from werkzeug.security import generate_password_hash

from ..auth import USER_QUERY, login_required
from ..db import get_db
from ..errors import ApiError
from ..pagination import page_args, paged, search_pattern
from ..services.activity import log
from ..services.progress import PROGRESS_SELECT, progress_rows
from ..services.users import create_user, public_user
from ..validation import Validator, json_body

bp = Blueprint("admin", __name__, url_prefix="/admin")


def _search(columns):
    """WHERE conditions for the ?q= parameter across several columns."""
    query = request.args.get("q", "").strip()
    if not query:
        return [], []
    condition = " OR ".join(f"LOWER({c}) LIKE ? ESCAPE '\\'" for c in columns)
    return [f"({condition})"], [search_pattern(query)] * len(columns)


def _where(conditions):
    return " WHERE " + " AND ".join(conditions) if conditions else ""


@bp.get("/overview")
@login_required("admin")
def overview():
    db = get_db()
    counts = db.one("""
        SELECT (SELECT COUNT(*) FROM users WHERE role = 'student') AS students,
               (SELECT COUNT(*) FROM users WHERE role = 'instructor') AS instructors,
               (SELECT COUNT(*) FROM instructors WHERE is_approved = 0) AS pending_instructors,
               (SELECT COUNT(*) FROM courses) AS courses,
               (SELECT COUNT(*) FROM courses WHERE status = 'published') AS published_courses,
               (SELECT COUNT(*) FROM enrollments) AS enrollments,
               (SELECT COUNT(*) FROM enrollments WHERE completed_at IS NOT NULL) AS completions,
               (SELECT COUNT(*) FROM quiz_results) AS quiz_attempts,
               (SELECT COUNT(*) FROM quiz_results WHERE passed = 1) AS quiz_passes,
               (SELECT COUNT(*) FROM certificates) AS certificates
    """)
    today = datetime.now(timezone.utc).date()
    days = [(today - timedelta(days=offset)).isoformat() for offset in range(13, -1, -1)]
    per_day = {r["day"]: r["total"] for r in db.all(
        """SELECT SUBSTR(enrolled_at, 1, 10) AS day, COUNT(*) AS total FROM enrollments
           WHERE enrolled_at >= ? GROUP BY SUBSTR(enrolled_at, 1, 10)""", (days[0],))}
    top = db.all("""
        SELECT c.id, c.title, COUNT(e.id) AS students, COUNT(e.completed_at) AS completions
        FROM courses c LEFT JOIN enrollments e ON e.course_id = c.id
        GROUP BY c.id, c.title ORDER BY students DESC, c.id LIMIT 5""")
    return jsonify({
        "counts": counts,
        "enrollments_by_day": [{"date": d, "total": per_day.get(d, 0)} for d in days],
        "top_courses": top,
        "recent_activity": _activity(db, "", (), 8, 0),
    })


def _activity(db, where, params, limit, offset):
    return db.all(f"""
        SELECT a.id, a.action, a.details, a.created_at, u.name AS user_name, u.role AS user_role
        FROM activity_logs a LEFT JOIN users u ON u.id = a.user_id
        {where} ORDER BY a.id DESC LIMIT {int(limit)} OFFSET {int(offset)}""", params)


@bp.get("/activity")
@login_required("admin")
def activity():
    db = get_db()
    conditions, params = _search(["a.action", "a.details", "u.name"])
    clause = _where(conditions)
    page, size, offset = page_args(20)
    total = db.scalar(f"""SELECT COUNT(*) AS total FROM activity_logs a
                          LEFT JOIN users u ON u.id = a.user_id {clause}""", params)
    return jsonify(paged(_activity(db, clause, params, size, offset), total, page, size))


# ---------------------------------------------------------------- users

@bp.get("/users")
@login_required("admin")
def list_users():
    db = get_db()
    conditions, params = _search(["u.name", "u.email"])
    role = request.args.get("role", "")
    if role:
        conditions.append("u.role = ?")
        params.append(role)
    if request.args.get("pending") == "1":
        conditions.append("i.is_approved = 0")
    clause = _where(conditions)
    page, size, offset = page_args(10)
    source = "FROM users u LEFT JOIN instructors i ON i.user_id = u.id"
    total = db.scalar(f"SELECT COUNT(*) AS total {source} {clause}", params)
    rows = db.all(f"""
        SELECT u.*, i.headline, i.bio, i.expertise, i.is_approved,
               (SELECT COUNT(*) FROM enrollments e WHERE e.student_id = u.id) AS enrollment_count,
               (SELECT COUNT(*) FROM courses c WHERE c.instructor_id = u.id) AS course_count
        {source} {clause} ORDER BY u.id DESC LIMIT {size} OFFSET {offset}""", params)
    items = [{**public_user(r), "enrollment_count": r["enrollment_count"],
              "course_count": r["course_count"]} for r in rows]
    return jsonify(paged(items, total, page, size))


@bp.post("/users")
@login_required("admin")
def add_user():
    form = Validator(json_body())
    name = form.string("name", "Name", 2, 100)
    email = form.email()
    password = form.password()
    role = form.choice("role", "Role", ("student", "instructor", "admin"))
    headline = form.string("headline", "Headline", 0, 150)
    form.check()
    db = get_db()
    user_id = create_user(db, name, email, password, role, approved=True, headline=headline)
    log(db, g.user["id"], "user_created", f"Added {role} {email}")
    return jsonify({"user": public_user(db.one(USER_QUERY, (user_id,)))}), 201


def _target(db, user_id):
    user = db.one(USER_QUERY, (user_id,))
    if not user:
        raise ApiError("User not found.", 404)
    return user


@bp.put("/users/<int:user_id>")
@login_required("admin")
def edit_user(user_id):
    db = get_db()
    user = _target(db, user_id)
    data = json_body()
    form = Validator(data)
    name = form.string("name", "Name", 2, 100)
    email = form.email()
    active = form.boolean("is_active", bool(user["is_active"]))
    password = form.password() if data.get("password") else None
    if user_id == g.user["id"]:
        if not active:
            form.errors["is_active"] = "You cannot deactivate your own account."
        if password:
            form.errors["password"] = "Change your own password from your profile page."
    if "email" not in form.errors and db.one(
            "SELECT id FROM users WHERE email = ? AND id <> ?", (email, user_id)):
        form.errors["email"] = "An account with this email already exists."
    form.check()

    db.execute("UPDATE users SET name = ?, email = ?, is_active = ? WHERE id = ?",
               (name, email, int(active), user_id))
    if password:
        db.execute("""UPDATE users SET password_hash = ?, token_version = token_version + 1
                      WHERE id = ?""", (generate_password_hash(password), user_id))
    elif not active and user["is_active"]:
        db.execute("UPDATE users SET token_version = token_version + 1 WHERE id = ?", (user_id,))
    log(db, g.user["id"], "user_updated",
        f"Updated {email} ({'active' if active else 'deactivated'})")
    return jsonify({"user": public_user(db.one(USER_QUERY, (user_id,)))})


@bp.delete("/users/<int:user_id>")
@login_required("admin")
def delete_user(user_id):
    db = get_db()
    user = _target(db, user_id)
    if user_id == g.user["id"]:
        raise ApiError("You cannot delete your own account.", 409)
    if db.one("SELECT id FROM courses WHERE instructor_id = ? LIMIT 1", (user_id,)):
        raise ApiError("This instructor still has courses. Reassign or delete them first, "
                       "or deactivate the account instead.", 409)
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    log(db, g.user["id"], "user_deleted", f"Deleted {user['role']} {user['email']}")
    return jsonify({"message": "User deleted."})


@bp.put("/instructors/<int:user_id>/approval")
@login_required("admin")
def approve_instructor(user_id):
    db = get_db()
    user = _target(db, user_id)
    if user["role"] != "instructor":
        raise ApiError("That user is not an instructor.", 404)
    form = Validator(json_body())
    approved = form.boolean("approved")
    form.check()
    db.execute("UPDATE instructors SET is_approved = ? WHERE user_id = ?",
               (int(approved), user_id))
    log(db, g.user["id"], "instructor_approved" if approved else "instructor_suspended",
        user["email"])
    return jsonify({"user": public_user(db.one(USER_QUERY, (user_id,)))})


# ---------------------------------------------------------------- monitoring

@bp.get("/enrollments")
@login_required("admin")
def enrollments():
    db = get_db()
    conditions, params = _search(["s.name", "s.email", "c.title"])
    clause = _where(conditions)
    page, size, offset = page_args(10)
    total = db.scalar(f"SELECT COUNT(*) AS total FROM ({PROGRESS_SELECT} {clause}) AS rows_found",
                      params)
    rows = progress_rows(db, clause, params, limit=size, offset=offset)
    for row in rows:
        row.pop("thumbnail_key")
    return jsonify(paged(rows, total, page, size))


@bp.delete("/enrollments/<int:enrollment_id>")
@login_required("admin")
def remove_enrollment(enrollment_id):
    db = get_db()
    rows = progress_rows(db, "WHERE e.id = ?", (enrollment_id,))
    if not rows:
        raise ApiError("Enrollment not found.", 404)
    db.execute("DELETE FROM enrollments WHERE id = ?", (enrollment_id,))
    log(db, g.user["id"], "enrollment_removed",
        f"Removed {rows[0]['student_email']} from '{rows[0]['course_title']}'")
    return jsonify({"message": "Enrollment removed."})


@bp.get("/results")
@login_required("admin")
def results():
    db = get_db()
    conditions, params = _search(["u.name", "u.email", "q.title", "c.title"])
    clause = _where(conditions)
    page, size, offset = page_args(10)
    source = """FROM quiz_results r
                JOIN quizzes q ON q.id = r.quiz_id
                JOIN courses c ON c.id = q.course_id
                JOIN users u ON u.id = r.student_id"""
    total = db.scalar(f"SELECT COUNT(*) AS total {source} {clause}", params)
    rows = db.all(f"""
        SELECT r.id, r.score, r.total, r.percentage, r.passed, r.submitted_at,
               q.title AS quiz_title, c.title AS course_title,
               u.name AS student_name, u.email AS student_email
        {source} {clause} ORDER BY r.id DESC LIMIT {size} OFFSET {offset}""", params)
    return jsonify(paged(rows, total, page, size))
