"""Public pages: course catalogue, course details and platform statistics."""
from flask import Blueprint, jsonify, request

from ..auth import can_manage, load_user
from ..config import CATEGORIES, LEVELS
from ..db import get_db
from ..errors import ApiError
from ..pagination import page_args, paged, search_pattern
from ..services.courses import COURSE_SELECT, course_json, get_course

bp = Blueprint("catalog", __name__)

SORTS = {
    "newest": "c.created_at DESC, c.id DESC",
    "popular": "student_count DESC, c.id DESC",
    "title": "LOWER(c.title) ASC, c.id ASC",
}


@bp.get("/health")
def health():
    get_db().scalar("SELECT 1 AS ok")
    return jsonify({"status": "ok"})


@bp.get("/meta")
def meta():
    return jsonify({"categories": CATEGORIES, "levels": LEVELS})


@bp.get("/stats")
def stats():
    db = get_db()
    counts = db.one("""
        SELECT (SELECT COUNT(*) FROM courses WHERE status = 'published') AS courses,
               (SELECT COUNT(*) FROM users WHERE role = 'student') AS students,
               (SELECT COUNT(*) FROM instructors WHERE is_approved = 1) AS instructors,
               (SELECT COUNT(*) FROM certificates) AS certificates
    """)
    categories = db.all("""SELECT category, COUNT(*) AS total FROM courses
                           WHERE status = 'published' GROUP BY category ORDER BY category""")
    return jsonify({**counts, "categories": categories})


@bp.get("/courses")
def list_courses():
    where, params = ["c.status = 'published'"], []
    query = request.args.get("q", "").strip()
    if query:
        pattern = search_pattern(query)
        columns = ("c.title", "c.summary", "c.category", "u.name")
        where.append("(" + " OR ".join(f"LOWER({col}) LIKE ? ESCAPE '\\'" for col in columns) + ")")
        params += [pattern] * len(columns)
    for name, column in (("category", "c.category"), ("level", "c.level")):
        value = request.args.get(name, "")
        if value:
            where.append(f"{column} = ?")
            params.append(value)
    if request.args.get("featured") == "1":
        where.append("c.is_featured = 1")

    clause = " WHERE " + " AND ".join(where)
    order = SORTS.get(request.args.get("sort"), SORTS["newest"])
    page, size, offset = page_args(9)
    db = get_db()
    total = db.scalar(f"""SELECT COUNT(*) AS total FROM courses c
                          JOIN users u ON u.id = c.instructor_id {clause}""", params)
    rows = db.all(f"{COURSE_SELECT} {clause} ORDER BY {order} LIMIT {size} OFFSET {offset}", params)
    return jsonify(paged([course_json(r) for r in rows], total, page, size))


@bp.get("/courses/<int:course_id>")
def course_details(course_id):
    db = get_db()
    user = load_user()
    row = get_course(db, course_id)
    enrollment = None
    if user and user["role"] == "student":
        enrollment = db.one("SELECT id FROM enrollments WHERE student_id = ? AND course_id = ?",
                            (user["id"], course_id))
    manager = can_manage(user, row)
    if row["status"] != "published" and not (manager or enrollment):
        raise ApiError("Course not found.", 404)

    # Only the outline is public; video and file links come from the learning endpoint.
    lessons = db.all("""SELECT id, title, duration_seconds, video_type FROM lessons
                        WHERE course_id = ? ORDER BY position, id""", (course_id,))
    materials = db.all("""SELECT id, title, file_name, file_size FROM study_materials
                          WHERE course_id = ? ORDER BY id""", (course_id,))
    quizzes = db.all("""
        SELECT q.id, q.title, q.pass_percentage,
               (SELECT COUNT(*) FROM quiz_questions x WHERE x.quiz_id = q.id) AS question_count
        FROM quizzes q WHERE q.course_id = ? ORDER BY q.id""", (course_id,))
    return jsonify({
        "course": course_json(row, detail=True),
        "lessons": lessons,
        "materials": materials,
        "quizzes": quizzes,
        "is_enrolled": enrollment is not None,
        "can_manage": manager,
    })
