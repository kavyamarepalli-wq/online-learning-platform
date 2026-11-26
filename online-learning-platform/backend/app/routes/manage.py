"""Course management for instructors (their own courses) and administrators (all courses)."""
import json
import re
from urllib.parse import parse_qs, urlsplit

from flask import Blueprint, g, jsonify, request

from ..auth import can_manage, login_required
from ..config import CATEGORIES, LEVELS
from ..db import get_db, now
from ..errors import ApiError
from ..services.activity import log
from ..services.courses import COURSE_SELECT, course_json, get_course
from ..services.progress import progress_rows
from ..uploads import delete_later, save_upload
from ..urls import file_url, thumbnail_url
from ..validation import Validator, json_body

bp = Blueprint("manage", __name__, url_prefix="/manage")
STAFF = ("instructor", "admin")


def owned_course(db, course_id):
    course = get_course(db, course_id)
    if not can_manage(g.user, course):
        # 404 rather than 403: do not reveal other instructors' courses.
        raise ApiError("Course not found.", 404)
    return course


def owned_child(db, table, item_id, label):
    """A lesson, material or quiz that belongs to a course the user manages."""
    row = db.one(f"SELECT * FROM {table} WHERE id = ?", (item_id,))
    if not row:
        raise ApiError(f"{label} not found.", 404)
    return row, owned_course(db, row["course_id"])


def touch(db, course_id):
    db.execute("UPDATE courses SET updated_at = ? WHERE id = ?", (now(), course_id))


# ---------------------------------------------------------------- courses

def _course_form(db, existing=None):
    data = json_body()
    form = Validator(data)
    values = {
        "title": form.string("title", "Title", 3, 150),
        "summary": form.string("summary", "Short summary", 10, 300),
        "description": form.string("description", "Description", 20, 10000),
        "category": form.choice("category", "Category", CATEGORIES),
        "level": form.choice("level", "Level", LEVELS),
        "status": form.choice("status", "Status", ("draft", "published"), default="draft"),
    }
    if g.user["role"] == "admin":
        values["is_featured"] = int(form.boolean(
            "is_featured", bool(existing and existing["is_featured"])))
        fallback = existing["instructor_id"] if existing else None
        instructor_id = form.integer("instructor_id", "Instructor", 1, 2**31 - 1, default=fallback)
        if "instructor_id" not in form.errors and not db.one(
                "SELECT user_id FROM instructors WHERE user_id = ? AND is_approved = 1",
                (instructor_id,)) and instructor_id != fallback:
            form.errors["instructor_id"] = "Choose an approved instructor."
        values["instructor_id"] = instructor_id
    else:
        values["instructor_id"] = existing["instructor_id"] if existing else g.user["id"]
        values["is_featured"] = existing["is_featured"] if existing else 0
    if values["status"] == "published" and (not existing or existing["lesson_count"] == 0):
        form.errors["status"] = "Add at least one lesson before publishing."
    form.check()
    return values


@bp.get("/courses")
@login_required(*STAFF)
def list_courses():
    where, params = "", ()
    if g.user["role"] == "instructor":
        where, params = "WHERE c.instructor_id = ?", (g.user["id"],)
    rows = get_db().all(f"{COURSE_SELECT} {where} ORDER BY c.created_at DESC, c.id DESC", params)
    return jsonify({"items": [course_json(r) for r in rows]})


@bp.get("/instructors")
@login_required(*STAFF)
def instructor_options():
    if g.user["role"] != "admin":
        return jsonify({"items": []})
    return jsonify({"items": get_db().all(
        """SELECT u.id, u.name FROM instructors i JOIN users u ON u.id = i.user_id
           WHERE i.is_approved = 1 AND u.is_active = 1 ORDER BY u.name""")})


@bp.post("/courses")
@login_required(*STAFF)
def create_course():
    db = get_db()
    values = _course_form(db)
    stamp = now()
    columns = list(values) + ["created_at", "updated_at"]
    course_id = db.insert(
        f"INSERT INTO courses ({', '.join(columns)}) VALUES ({', '.join('?' * len(columns))})",
        [*values.values(), stamp, stamp])
    log(db, g.user["id"], "course_created", f"Created '{values['title']}'")
    return jsonify({"course": course_json(get_course(db, course_id), detail=True)}), 201


def _course_content(db, course_id):
    lessons = db.all("SELECT * FROM lessons WHERE course_id = ? ORDER BY position, id", (course_id,))
    for lesson in lessons:
        key = lesson.pop("video_key")
        lesson["file_url"] = file_url(key) if key else None
    materials = db.all("SELECT * FROM study_materials WHERE course_id = ? ORDER BY id", (course_id,))
    for material in materials:
        material["download_url"] = file_url(material.pop("file_key"), material["file_name"])
    quizzes = db.all("SELECT * FROM quizzes WHERE course_id = ? ORDER BY id", (course_id,))
    for quiz in quizzes:
        quiz["questions"] = db.all(
            """SELECT id, prompt, options, correct_index, explanation FROM quiz_questions
               WHERE quiz_id = ? ORDER BY position, id""", (quiz["id"],))
        for question in quiz["questions"]:
            question["options"] = json.loads(question["options"])
    return {"lessons": lessons, "materials": materials, "quizzes": quizzes}


@bp.get("/courses/<int:course_id>")
@login_required(*STAFF)
def course_editor(course_id):
    db = get_db()
    course = owned_course(db, course_id)
    return jsonify({"course": course_json(course, detail=True), **_course_content(db, course_id)})


@bp.put("/courses/<int:course_id>")
@login_required(*STAFF)
def update_course(course_id):
    db = get_db()
    course = owned_course(db, course_id)
    values = _course_form(db, course)
    assignments = ", ".join(f"{name} = ?" for name in values)
    db.execute(f"UPDATE courses SET {assignments}, updated_at = ? WHERE id = ?",
               [*values.values(), now(), course_id])
    log(db, g.user["id"], "course_updated", f"Updated '{values['title']}' ({values['status']})")
    return jsonify({"course": course_json(get_course(db, course_id), detail=True)})


@bp.delete("/courses/<int:course_id>")
@login_required(*STAFF)
def delete_course(course_id):
    db = get_db()
    course = owned_course(db, course_id)
    keys = [course["thumbnail_key"]]
    keys += [r["video_key"] for r in db.all(
        "SELECT video_key FROM lessons WHERE course_id = ?", (course_id,))]
    keys += [r["file_key"] for r in db.all(
        "SELECT file_key FROM study_materials WHERE course_id = ?", (course_id,))]
    db.execute("DELETE FROM courses WHERE id = ?", (course_id,))
    delete_later(*keys)
    log(db, g.user["id"], "course_deleted", f"Deleted '{course['title']}'")
    return jsonify({"message": "Course deleted."})


@bp.post("/courses/<int:course_id>/thumbnail")
@login_required(*STAFF)
def upload_thumbnail(course_id):
    db = get_db()
    course = owned_course(db, course_id)
    saved = save_upload("thumbnail")
    db.execute("UPDATE courses SET thumbnail_key = ?, updated_at = ? WHERE id = ?",
               (saved["key"], now(), course_id))
    delete_later(course["thumbnail_key"])
    return jsonify({"thumbnail_url": thumbnail_url(saved["key"])})


# ---------------------------------------------------------------- lessons

YOUTUBE_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")


def youtube_embed(url):
    """Turns any common YouTube address into its privacy-friendly embed address."""
    parts = urlsplit(url)
    host = (parts.hostname or "").lower().removeprefix("www.").removeprefix("m.")
    video_id = ""
    if host == "youtu.be":
        video_id = parts.path.strip("/")
    elif host in ("youtube.com", "youtube-nocookie.com"):
        if parts.path == "/watch":
            video_id = parse_qs(parts.query).get("v", [""])[0]
        else:
            pieces = parts.path.strip("/").split("/")
            if len(pieces) == 2 and pieces[0] in ("embed", "shorts", "live"):
                video_id = pieces[1]
    if parts.scheme in ("http", "https") and YOUTUBE_ID.match(video_id):
        return f"https://www.youtube-nocookie.com/embed/{video_id}"
    return None


def _lesson_values(existing=None):
    """Reads a multipart lesson form. Returns the column values to save."""
    form = Validator(request.form)
    title = form.string("title", "Lesson title", 3, 150)
    content = form.string("content", "Lesson notes", 0, 20000)
    video_type = form.choice("video_type", "Video source",
                             ("none", "upload", "youtube", "url"), default="none")
    duration = form.integer("duration_seconds", "Duration (seconds)", 0, 86400, default=0)
    url = form.string("video_url", "Video link", 0, 1000)
    old_key = existing["video_key"] if existing else None
    video_key = video_url = None

    if video_type == "youtube":
        video_url = youtube_embed(url)
        if not video_url:
            form.errors["video_url"] = "Enter a valid YouTube video link."
    elif video_type == "url":
        parts = urlsplit(url)
        if parts.scheme != "https" or not parts.netloc:
            form.errors["video_url"] = "Enter an https:// link to an MP4 or WebM file."
        video_url = url
    elif video_type == "none" and not content:
        form.errors["content"] = "A lesson without a video needs written notes."
    form.check()

    if video_type == "upload":
        keeps_old = bool(old_key and existing["video_type"] == "upload")
        saved = save_upload("video", "video", required=not keeps_old)
        video_key = saved["key"] if saved else old_key
    if old_key and old_key != video_key:
        delete_later(old_key)
    return {"title": title, "content": content, "video_type": video_type,
            "video_key": video_key, "video_url": video_url,
            "duration_seconds": 0 if video_type == "none" else duration}


@bp.post("/courses/<int:course_id>/lessons")
@login_required(*STAFF)
def create_lesson(course_id):
    db = get_db()
    owned_course(db, course_id)
    values = _lesson_values()
    values["position"] = db.scalar(
        "SELECT COALESCE(MAX(position), 0) + 1 AS next FROM lessons WHERE course_id = ?",
        (course_id,))
    columns = ["course_id", *values, "created_at"]
    lesson_id = db.insert(
        f"INSERT INTO lessons ({', '.join(columns)}) VALUES ({', '.join('?' * len(columns))})",
        [course_id, *values.values(), now()])
    touch(db, course_id)
    return jsonify({"id": lesson_id}), 201


@bp.put("/lessons/<int:lesson_id>")
@login_required(*STAFF)
def update_lesson(lesson_id):
    db = get_db()
    lesson, course = owned_child(db, "lessons", lesson_id, "Lesson")
    values = _lesson_values(lesson)
    assignments = ", ".join(f"{name} = ?" for name in values)
    db.execute(f"UPDATE lessons SET {assignments} WHERE id = ?", [*values.values(), lesson_id])
    if (values["video_key"], values["video_url"]) != (lesson["video_key"], lesson["video_url"]):
        # A different video: old watch time and resume point no longer apply.
        db.execute("""UPDATE learning_progress SET watched_seconds = 0, last_position = 0
                      WHERE lesson_id = ?""", (lesson_id,))
    touch(db, course["id"])
    return jsonify({"id": lesson_id})


@bp.delete("/lessons/<int:lesson_id>")
@login_required(*STAFF)
def delete_lesson(lesson_id):
    db = get_db()
    lesson, course = owned_child(db, "lessons", lesson_id, "Lesson")
    if course["status"] == "published" and course["lesson_count"] <= 1:
        raise ApiError("A published course needs a lesson. Unpublish it first.", 409)
    db.execute("DELETE FROM lessons WHERE id = ?", (lesson_id,))
    delete_later(lesson["video_key"])
    touch(db, course["id"])
    return jsonify({"message": "Lesson deleted."})


@bp.put("/courses/<int:course_id>/lesson-order")
@login_required(*STAFF)
def reorder_lessons(course_id):
    db = get_db()
    owned_course(db, course_id)
    ids = json_body().get("lesson_ids")
    current = {r["id"] for r in db.all("SELECT id FROM lessons WHERE course_id = ?", (course_id,))}
    if (not isinstance(ids, list) or any(type(i) is not int for i in ids)
            or len(ids) != len(current) or set(ids) != current):
        raise ApiError("Send every lesson id of this course exactly once.", 422)
    for position, lesson_id in enumerate(ids, start=1):
        db.execute("UPDATE lessons SET position = ? WHERE id = ?", (position, lesson_id))
    touch(db, course_id)
    return jsonify({"message": "Order saved."})


# ---------------------------------------------------------------- study materials

@bp.post("/courses/<int:course_id>/materials")
@login_required(*STAFF)
def create_material(course_id):
    db = get_db()
    owned_course(db, course_id)
    form = Validator(request.form)
    title = form.string("title", "Title", 2, 150)
    lesson_id = None
    if request.form.get("lesson_id"):
        lesson_id = form.integer("lesson_id", "Lesson", 1, 2**31 - 1)
        if not db.one("SELECT id FROM lessons WHERE id = ? AND course_id = ?",
                      (lesson_id, course_id)):
            form.errors["lesson_id"] = "Choose a lesson from this course."
    form.check()
    saved = save_upload("material")
    material_id = db.insert(
        """INSERT INTO study_materials (course_id, lesson_id, title, file_key, file_name,
                                        content_type, file_size, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (course_id, lesson_id, title, saved["key"], saved["name"], saved["content_type"],
         saved["size"], now()))
    touch(db, course_id)
    return jsonify({"id": material_id}), 201


@bp.delete("/materials/<int:material_id>")
@login_required(*STAFF)
def delete_material(material_id):
    db = get_db()
    material, course = owned_child(db, "study_materials", material_id, "Material")
    db.execute("DELETE FROM study_materials WHERE id = ?", (material_id,))
    delete_later(material["file_key"])
    touch(db, course["id"])
    return jsonify({"message": "Material deleted."})


# ---------------------------------------------------------------- quizzes

def _quiz_form():
    data = json_body()
    form = Validator(data)
    quiz = {
        "title": form.string("title", "Quiz title", 3, 150),
        "description": form.string("description", "Description", 0, 1000),
        "pass_percentage": form.integer("pass_percentage", "Pass mark", 1, 100, default=60),
        "max_attempts": form.integer("max_attempts", "Maximum attempts", 0, 100, default=0),
    }
    raw = data.get("questions")
    questions = []
    if not isinstance(raw, list) or not 1 <= len(raw) <= 100:
        form.errors["questions"] = "Add between 1 and 100 questions."
        raw = []
    for index, item in enumerate(raw):
        item = item if isinstance(item, dict) else {}
        question = Validator(item)
        prompt = question.string("prompt", "Question", 3, 1000)
        explanation = question.string("explanation", "Explanation", 0, 1000)
        options = item.get("options")
        if (not isinstance(options, list) or not 2 <= len(options) <= 6
                or any(not isinstance(o, str) or not o.strip() or len(o) > 300 for o in options)):
            question.errors["options"] = "Give 2 to 6 non-empty options."
            options = []
        else:
            options = [o.strip() for o in options]
            if len(set(options)) != len(options):
                question.errors["options"] = "Options must be different from each other."
        correct = item.get("correct_index")
        if type(correct) is not int or not 0 <= correct < len(options):
            question.errors["correct_index"] = "Select the correct option."
        for name, message in question.errors.items():
            form.errors[f"questions.{index}.{name}"] = message
        questions.append((prompt, json.dumps(options), correct, explanation, index))
    form.check()
    return quiz, questions


def _save_questions(db, quiz_id, questions):
    db.execute("DELETE FROM quiz_questions WHERE quiz_id = ?", (quiz_id,))
    for values in questions:
        db.execute("""INSERT INTO quiz_questions (quiz_id, prompt, options, correct_index,
                      explanation, position) VALUES (?, ?, ?, ?, ?, ?)""", (quiz_id, *values))


@bp.post("/courses/<int:course_id>/quizzes")
@login_required(*STAFF)
def create_quiz(course_id):
    db = get_db()
    owned_course(db, course_id)
    quiz, questions = _quiz_form()
    quiz_id = db.insert(
        """INSERT INTO quizzes (course_id, title, description, pass_percentage, max_attempts,
                                created_at) VALUES (?, ?, ?, ?, ?, ?)""",
        (course_id, *quiz.values(), now()))
    _save_questions(db, quiz_id, questions)
    touch(db, course_id)
    return jsonify({"id": quiz_id}), 201


@bp.put("/quizzes/<int:quiz_id>")
@login_required(*STAFF)
def update_quiz(quiz_id):
    db = get_db()
    _, course = owned_child(db, "quizzes", quiz_id, "Quiz")
    quiz, questions = _quiz_form()
    db.execute("""UPDATE quizzes SET title = ?, description = ?, pass_percentage = ?,
                  max_attempts = ? WHERE id = ?""", (*quiz.values(), quiz_id))
    _save_questions(db, quiz_id, questions)
    touch(db, course["id"])
    return jsonify({"id": quiz_id})


@bp.delete("/quizzes/<int:quiz_id>")
@login_required(*STAFF)
def delete_quiz(quiz_id):
    db = get_db()
    _, course = owned_child(db, "quizzes", quiz_id, "Quiz")
    db.execute("DELETE FROM quizzes WHERE id = ?", (quiz_id,))
    touch(db, course["id"])
    return jsonify({"message": "Quiz and its results deleted."})


# ---------------------------------------------------------------- monitoring

@bp.get("/courses/<int:course_id>/students")
@login_required(*STAFF)
def course_students(course_id):
    db = get_db()
    owned_course(db, course_id)
    rows = progress_rows(db, "WHERE e.course_id = ?", (course_id,))
    for row in rows:
        row.pop("thumbnail_key")
    return jsonify({"items": rows})


@bp.get("/courses/<int:course_id>/results")
@login_required(*STAFF)
def course_results(course_id):
    db = get_db()
    owned_course(db, course_id)
    rows = db.all("""
        SELECT r.id, r.score, r.total, r.percentage, r.passed, r.submitted_at,
               q.title AS quiz_title, u.name AS student_name, u.email AS student_email
        FROM quiz_results r
        JOIN quizzes q ON q.id = r.quiz_id
        JOIN users u ON u.id = r.student_id
        WHERE q.course_id = ? ORDER BY r.id DESC LIMIT 500""", (course_id,))
    return jsonify({"items": rows})
