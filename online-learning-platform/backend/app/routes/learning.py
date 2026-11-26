"""Student features: enrolling, lessons, quizzes, progress and certificates."""
import json

from flask import Blueprint, current_app, g, jsonify, send_file

from ..auth import can_manage, login_required
from ..db import get_db, now
from ..errors import ApiError
from ..services.activity import log
from ..services.certificate_pdf import render_certificate
from ..services.courses import course_json, get_course
from ..services.progress import progress_rows, refresh_completion
from ..urls import api_base, file_url, thumbnail_url
from ..validation import Validator, json_body

bp = Blueprint("learning", __name__)


def find_enrollment(db, student_id, course_id):
    return db.one("SELECT * FROM enrollments WHERE student_id = ? AND course_id = ?",
                  (student_id, course_id))


def course_access(db, course_id):
    """The signed-in user may study if enrolled, or preview if they manage the course."""
    course = get_course(db, course_id)
    enrollment = None
    if g.user["role"] == "student":
        enrollment = find_enrollment(db, g.user["id"], course_id)
    if not enrollment and not can_manage(g.user, course):
        raise ApiError("Enroll in this course to access its content.", 403)
    return course, enrollment


def progress_json(row):
    if not row:
        return None
    return {key: row[key] for key in (
        "enrollment_id", "percentage", "is_completed", "completed_at", "total_lessons",
        "completed_lessons", "total_quizzes", "passed_quizzes", "certificate_id")}


@bp.post("/courses/<int:course_id>/enroll")
@login_required("student")
def enroll(course_id):
    db = get_db()
    course = get_course(db, course_id)
    if course["status"] != "published":
        raise ApiError("This course is not open for enrollment.", 404)
    stamp = now()
    created = db.one(
        """INSERT INTO enrollments (student_id, course_id, enrolled_at, last_accessed_at)
           VALUES (?, ?, ?, ?) ON CONFLICT (student_id, course_id) DO NOTHING RETURNING id""",
        (g.user["id"], course_id, stamp, stamp))
    if not created:
        raise ApiError("You are already enrolled in this course.", 409)
    log(db, g.user["id"], "enrolled", f"Enrolled in '{course['title']}'")
    # Earlier quiz passes still count if the student re-enrolls.
    refresh_completion(db, g.user["id"], course_id)
    return jsonify({"message": "You are enrolled.", "enrollment_id": created["id"]}), 201


@bp.delete("/courses/<int:course_id>/enroll")
@login_required("student")
def unenroll(course_id):
    db = get_db()
    course = get_course(db, course_id)
    if not find_enrollment(db, g.user["id"], course_id):
        raise ApiError("You are not enrolled in this course.", 404)
    db.execute("DELETE FROM enrollments WHERE student_id = ? AND course_id = ?",
               (g.user["id"], course_id))
    log(db, g.user["id"], "unenrolled", f"Left '{course['title']}'")
    return jsonify({"message": "You have left the course."})


@bp.get("/courses/<int:course_id>/learn")
@login_required()
def learn(course_id):
    db = get_db()
    course, enrollment = course_access(db, course_id)
    done = {}
    summary = None
    if enrollment:
        db.execute("UPDATE enrollments SET last_accessed_at = ? WHERE id = ?",
                   (now(), enrollment["id"]))
        summary = refresh_completion(db, g.user["id"], course_id)
        done = {p["lesson_id"]: p for p in db.all(
            "SELECT * FROM learning_progress WHERE enrollment_id = ?", (enrollment["id"],))}

    lessons = []
    for row in db.all("SELECT * FROM lessons WHERE course_id = ? ORDER BY position, id", (course_id,)):
        state = done.get(row["id"], {})
        lessons.append({
            "id": row["id"], "title": row["title"], "content": row["content"],
            "video_type": row["video_type"],
            "video_url": file_url(row["video_key"]) if row["video_type"] == "upload"
            else row["video_url"],
            "duration_seconds": row["duration_seconds"],
            "is_completed": bool(state.get("is_completed")),
            "watched_seconds": state.get("watched_seconds", 0),
            "last_position": state.get("last_position", 0),
        })

    materials = [{
        "id": m["id"], "lesson_id": m["lesson_id"], "title": m["title"],
        "file_name": m["file_name"], "file_size": m["file_size"],
        "download_url": file_url(m["file_key"], m["file_name"]),
    } for m in db.all("SELECT * FROM study_materials WHERE course_id = ? ORDER BY id", (course_id,))]

    quizzes = db.all("""
        SELECT q.id, q.title, q.description, q.pass_percentage, q.max_attempts,
               (SELECT COUNT(*) FROM quiz_questions x WHERE x.quiz_id = q.id) AS question_count,
               (SELECT COUNT(*) FROM quiz_results r WHERE r.quiz_id = q.id AND r.student_id = ?)
                   AS attempts_used,
               (SELECT MAX(r.percentage) FROM quiz_results r
                 WHERE r.quiz_id = q.id AND r.student_id = ?) AS best_percentage,
               (SELECT MAX(r.passed) FROM quiz_results r
                 WHERE r.quiz_id = q.id AND r.student_id = ?) AS passed
        FROM quizzes q WHERE q.course_id = ? ORDER BY q.id
    """, (g.user["id"], g.user["id"], g.user["id"], course_id))
    for quiz in quizzes:
        quiz["passed"] = bool(quiz["passed"])

    return jsonify({
        "course": course_json(course, detail=True),
        "lessons": lessons,
        "materials": materials,
        "quizzes": quizzes,
        "progress": progress_json(summary),
        "preview": enrollment is None,
    })


@bp.put("/lessons/<int:lesson_id>/progress")
@login_required("student")
def save_progress(lesson_id):
    db = get_db()
    lesson = db.one("SELECT * FROM lessons WHERE id = ?", (lesson_id,))
    if not lesson:
        raise ApiError("Lesson not found.", 404)
    enrollment = find_enrollment(db, g.user["id"], lesson["course_id"])
    if not enrollment:
        raise ApiError("Enroll in this course to track progress.", 403)

    data = json_body()
    form = Validator(data)
    position = form.integer("position", "Position", 0, 86400, default=0)
    watched = form.integer("watched_seconds", "Watched time", 0, 86400, default=0)
    completed = data.get("completed")
    if completed is not None and not isinstance(completed, bool):
        form.errors["completed"] = "Must be true or false."
    form.check()

    stamp = now()
    db.execute("""INSERT INTO learning_progress (enrollment_id, lesson_id, updated_at)
                  VALUES (?, ?, ?) ON CONFLICT (enrollment_id, lesson_id) DO NOTHING""",
               (enrollment["id"], lesson_id, stamp))
    state = db.one("SELECT * FROM learning_progress WHERE enrollment_id = ? AND lesson_id = ?",
                   (enrollment["id"], lesson_id))

    duration = lesson["duration_seconds"]
    watched = max(state["watched_seconds"], min(watched, duration) if duration else watched)
    if "position" not in data:
        position = state["last_position"]
    is_completed = bool(state["is_completed"])
    if completed is not None:
        is_completed = completed
    elif duration and watched >= duration * 0.9 and state["watched_seconds"] < duration * 0.9:
        # Completes once, on crossing 90%, so "mark incomplete" is not undone by autosave.
        is_completed = True
    completed_at = (state["completed_at"] or stamp) if is_completed else None

    db.execute("""UPDATE learning_progress SET watched_seconds = ?, last_position = ?,
                  is_completed = ?, completed_at = ?, updated_at = ? WHERE id = ?""",
               (watched, position, int(is_completed), completed_at, stamp, state["id"]))
    db.execute("UPDATE enrollments SET last_accessed_at = ? WHERE id = ?", (stamp, enrollment["id"]))
    if is_completed and not state["is_completed"]:
        log(db, g.user["id"], "lesson_completed", f"Completed lesson '{lesson['title']}'")

    summary = refresh_completion(db, g.user["id"], lesson["course_id"])
    return jsonify({
        "lesson": {"id": lesson_id, "is_completed": is_completed,
                   "watched_seconds": watched, "last_position": position},
        "progress": progress_json(summary),
    })


# ---------------------------------------------------------------- quizzes

def _load_quiz(db, quiz_id):
    quiz = db.one("SELECT * FROM quizzes WHERE id = ?", (quiz_id,))
    if not quiz:
        raise ApiError("Quiz not found.", 404)
    questions = db.all("SELECT * FROM quiz_questions WHERE quiz_id = ? ORDER BY position, id",
                       (quiz_id,))
    return quiz, questions


def _attempts(db, quiz_id, student_id):
    rows = db.all("""SELECT id, score, total, percentage, passed, submitted_at FROM quiz_results
                     WHERE quiz_id = ? AND student_id = ? ORDER BY id DESC""", (quiz_id, student_id))
    for row in rows:
        row["passed"] = bool(row["passed"])
    return rows


def result_json(db, result, quiz, for_student=True):
    """A stored attempt. Students see correct answers only once they can no longer benefit."""
    review = json.loads(result["answers"])
    reveal = True
    if for_student:
        attempts = _attempts(db, quiz["id"], result["student_id"])
        exhausted = quiz["max_attempts"] and len(attempts) >= quiz["max_attempts"]
        reveal = bool(exhausted or any(a["passed"] for a in attempts))
    if not reveal:
        for item in review:
            item.pop("correct_index", None)
            item.pop("explanation", None)
    return {
        "id": result["id"], "quiz_id": quiz["id"], "quiz_title": quiz["title"],
        "course_id": quiz["course_id"], "score": result["score"], "total": result["total"],
        "percentage": result["percentage"], "passed": bool(result["passed"]),
        "pass_percentage": quiz["pass_percentage"], "submitted_at": result["submitted_at"],
        "answers_revealed": reveal, "review": review,
    }


@bp.get("/quizzes/<int:quiz_id>")
@login_required()
def quiz_details(quiz_id):
    db = get_db()
    quiz, questions = _load_quiz(db, quiz_id)
    course, enrollment = course_access(db, quiz["course_id"])
    attempts = _attempts(db, quiz_id, g.user["id"])
    return jsonify({
        "quiz": {key: quiz[key] for key in (
            "id", "course_id", "title", "description", "pass_percentage", "max_attempts")},
        "course_title": course["title"],
        # The correct answers are deliberately left out.
        "questions": [{"id": q["id"], "prompt": q["prompt"], "options": json.loads(q["options"])}
                      for q in questions],
        "attempts": attempts,
        "can_attempt": bool(enrollment and questions and
                            (not quiz["max_attempts"] or len(attempts) < quiz["max_attempts"])),
        "preview": enrollment is None,
    })


@bp.post("/quizzes/<int:quiz_id>/submit")
@login_required("student")
def submit_quiz(quiz_id):
    db = get_db()
    quiz, questions = _load_quiz(db, quiz_id)
    enrollment = find_enrollment(db, g.user["id"], quiz["course_id"])
    if not enrollment:
        raise ApiError("Enroll in this course to take its quizzes.", 403)
    if not questions:
        raise ApiError("This quiz has no questions yet.", 409)
    # Locks the enrollment row (PostgreSQL), so parallel submissions cannot beat the limit.
    db.execute("UPDATE enrollments SET last_accessed_at = ? WHERE id = ?", (now(), enrollment["id"]))
    if quiz["max_attempts"] and len(_attempts(db, quiz_id, g.user["id"])) >= quiz["max_attempts"]:
        raise ApiError("You have used all attempts for this quiz.", 409)

    answers = json_body().get("answers")
    if not isinstance(answers, dict):
        raise ApiError("Answer every question before submitting.", 422)

    review, score = [], 0
    for question in questions:
        options = json.loads(question["options"])
        chosen = answers.get(str(question["id"]))
        if type(chosen) is not int or not 0 <= chosen < len(options):
            raise ApiError("Answer every question before submitting.", 422)
        correct = chosen == question["correct_index"]
        score += correct
        review.append({
            "prompt": question["prompt"], "options": options, "chosen_index": chosen,
            "is_correct": correct, "correct_index": question["correct_index"],
            "explanation": question["explanation"],
        })

    total = len(questions)
    percentage = (score * 100) // total
    passed = percentage >= quiz["pass_percentage"]
    result_id = db.insert(
        """INSERT INTO quiz_results (quiz_id, student_id, score, total, percentage, passed,
                                     answers, submitted_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (quiz_id, g.user["id"], score, total, percentage, int(passed), json.dumps(review), now()))
    log(db, g.user["id"], "quiz_submitted",
        f"Scored {percentage}% on '{quiz['title']}' ({'passed' if passed else 'not passed'})")
    summary = refresh_completion(db, g.user["id"], quiz["course_id"])
    result = db.one("SELECT * FROM quiz_results WHERE id = ?", (result_id,))
    return jsonify({"result": result_json(db, result, quiz),
                    "progress": progress_json(summary)}), 201


@bp.get("/quiz-results/<int:result_id>")
@login_required()
def quiz_result(result_id):
    db = get_db()
    result = db.one("SELECT * FROM quiz_results WHERE id = ?", (result_id,))
    if not result:
        raise ApiError("Result not found.", 404)
    quiz = db.one("SELECT * FROM quizzes WHERE id = ?", (result["quiz_id"],))
    own = result["student_id"] == g.user["id"]
    if not own and not can_manage(g.user, get_course(db, quiz["course_id"])):
        raise ApiError("Result not found.", 404)
    return jsonify({"result": result_json(db, result, quiz, for_student=own)})


# ---------------------------------------------------------------- dashboard

def achievements(stats):
    definitions = [
        ("first_step", "First Step", "Enroll in your first course", stats["enrolled"], 1),
        ("learner", "Dedicated Learner", "Complete 5 lessons", stats["lessons_completed"], 5),
        ("quiz_taker", "Quiz Winner", "Pass your first quiz", stats["quizzes_passed"], 1),
        ("perfect", "Perfect Score", "Score 100% on a quiz", stats["perfect_scores"], 1),
        ("graduate", "Graduate", "Earn your first certificate", stats["certificates"], 1),
        ("scholar", "Scholar", "Earn 3 certificates", stats["certificates"], 3),
    ]
    return [{"code": code, "title": title, "description": text,
             "progress": min(value, target), "target": target, "earned": value >= target}
            for code, title, text, value, target in definitions]


@bp.get("/student/dashboard")
@login_required("student")
def dashboard():
    db = get_db()
    uid = g.user["id"]
    for row in db.all("SELECT course_id FROM enrollments WHERE student_id = ?", (uid,)):
        refresh_completion(db, uid, row["course_id"])
    enrollments = progress_rows(db, "WHERE e.student_id = ?", (uid,),
                                order="e.last_accessed_at DESC, e.id DESC")
    for row in enrollments:
        row["thumbnail_url"] = thumbnail_url(row.pop("thumbnail_key"))

    results = db.all("""
        SELECT r.id, r.score, r.total, r.percentage, r.passed, r.submitted_at, r.quiz_id,
               q.title AS quiz_title, c.title AS course_title, c.id AS course_id
        FROM quiz_results r
        JOIN quizzes q ON q.id = r.quiz_id
        JOIN courses c ON c.id = q.course_id
        WHERE r.student_id = ? ORDER BY r.id DESC""", (uid,))
    for row in results:
        row["passed"] = bool(row["passed"])
    certificates = db.all("""SELECT id, code, course_id, course_title, instructor_name, issued_at
                             FROM certificates WHERE student_id = ? ORDER BY id DESC""", (uid,))
    lessons_completed = db.scalar("""
        SELECT COUNT(*) AS total FROM learning_progress p
        JOIN enrollments e ON e.id = p.enrollment_id
        WHERE e.student_id = ? AND p.is_completed = 1""", (uid,))
    stats = {
        "enrolled": len(enrollments),
        "completed": sum(1 for e in enrollments if e["is_completed"]),
        "lessons_completed": lessons_completed,
        "quizzes_passed": len({r["quiz_id"] for r in results if r["passed"]}),
        "perfect_scores": sum(1 for r in results if r["percentage"] == 100),
        "average_score": round(sum(r["percentage"] for r in results) / len(results))
        if results else None,
        "certificates": len(certificates),
    }
    return jsonify({"stats": stats, "enrollments": enrollments, "results": results,
                    "certificates": certificates, "achievements": achievements(stats)})


# ---------------------------------------------------------------- certificates

@bp.get("/certificates/<int:certificate_id>/download")
@login_required()
def download_certificate(certificate_id):
    certificate = get_db().one("SELECT * FROM certificates WHERE id = ?", (certificate_id,))
    if not certificate or (g.user["role"] != "admin" and certificate["student_id"] != g.user["id"]):
        raise ApiError("Certificate not found.", 404)
    # Without FRONTEND_URL, this server is also serving the website.
    site = current_app.config["FRONTEND_URL"] or api_base()
    verify_url = f"{site}/verify/{certificate['code']}"
    return send_file(render_certificate(certificate, verify_url), mimetype="application/pdf",
                     as_attachment=True, download_name=f"certificate-{certificate['code']}.pdf")


@bp.get("/certificates/verify/<code>")
def verify_certificate(code):
    certificate = get_db().one(
        """SELECT code, student_name, course_title, instructor_name, issued_at
           FROM certificates WHERE code = ?""", (code.strip().upper()[:40],))
    if not certificate:
        raise ApiError("No certificate matches that ID.", 404)
    return jsonify({"valid": True, "certificate": certificate})
