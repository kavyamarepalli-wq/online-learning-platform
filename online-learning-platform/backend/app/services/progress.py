"""Course progress and completion.

A course is made of lessons and quizzes (quizzes with no questions are ignored).
Percentage = (completed lessons + passed quizzes) / (lessons + quizzes).
When everything is done the enrollment is completed and a certificate is issued.
"""
import secrets

from ..db import now
from .activity import log

_HAS_QUESTIONS = "EXISTS (SELECT 1 FROM quiz_questions qq WHERE qq.quiz_id = q.id)"

PROGRESS_SELECT = f"""
    SELECT e.id AS enrollment_id, e.student_id, e.course_id, e.enrolled_at, e.last_accessed_at,
           e.completed_at, s.name AS student_name, s.email AS student_email,
           c.title AS course_title, c.thumbnail_key, c.category, c.level,
           t.name AS instructor_name,
           (SELECT COUNT(*) FROM lessons l WHERE l.course_id = e.course_id) AS total_lessons,
           (SELECT COUNT(*) FROM learning_progress p
             WHERE p.enrollment_id = e.id AND p.is_completed = 1) AS completed_lessons,
           (SELECT COUNT(*) FROM quizzes q
             WHERE q.course_id = e.course_id AND {_HAS_QUESTIONS}) AS total_quizzes,
           (SELECT COUNT(*) FROM quizzes q
             WHERE q.course_id = e.course_id AND {_HAS_QUESTIONS}
               AND EXISTS (SELECT 1 FROM quiz_results r WHERE r.quiz_id = q.id
                           AND r.student_id = e.student_id AND r.passed = 1)) AS passed_quizzes,
           (SELECT cert.id FROM certificates cert
             WHERE cert.student_id = e.student_id AND cert.course_id = e.course_id) AS certificate_id
    FROM enrollments e
    JOIN users s ON s.id = e.student_id
    JOIN courses c ON c.id = e.course_id
    JOIN users t ON t.id = c.instructor_id
"""


def with_percentage(row):
    total = row["total_lessons"] + row["total_quizzes"]
    done = row["completed_lessons"] + row["passed_quizzes"]
    row["percentage"] = (done * 100) // total if total else 0
    row["is_completed"] = row["completed_at"] is not None
    return row


def progress_rows(db, where="", params=(), order="e.enrolled_at DESC, e.id DESC", limit=None, offset=0):
    sql = f"{PROGRESS_SELECT} {where} ORDER BY {order}"
    if limit:
        sql += f" LIMIT {int(limit)} OFFSET {int(offset)}"
    return [with_percentage(row) for row in db.all(sql, params)]


def refresh_completion(db, student_id, course_id):
    """Returns the student's progress, completing the course and issuing a certificate if due."""
    rows = progress_rows(db, "WHERE e.student_id = ? AND e.course_id = ?", (student_id, course_id))
    if not rows:
        return None
    row = rows[0]
    total = row["total_lessons"] + row["total_quizzes"]
    finished = total > 0 and row["completed_lessons"] + row["passed_quizzes"] == total
    if finished and not row["completed_at"]:
        row["completed_at"] = now()
        row["is_completed"] = True
        db.execute("UPDATE enrollments SET completed_at = ? WHERE id = ?",
                   (row["completed_at"], row["enrollment_id"]))
        log(db, student_id, "course_completed", f"Completed '{row['course_title']}'")
    if row["completed_at"] and not row["certificate_id"]:
        code = "LS-" + "-".join(secrets.token_hex(2).upper() for _ in range(3))
        db.execute(
            """INSERT INTO certificates (code, student_id, course_id, student_name, course_title,
                                         instructor_name, issued_at)
               VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT (student_id, course_id) DO NOTHING""",
            (code, student_id, course_id, row["student_name"], row["course_title"],
             row["instructor_name"], now()))
        row["certificate_id"] = db.scalar(
            "SELECT id FROM certificates WHERE student_id = ? AND course_id = ?",
            (student_id, course_id))
        log(db, student_id, "certificate_issued", f"Certificate for '{row['course_title']}'")
    return row
