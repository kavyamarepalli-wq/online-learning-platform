from ..errors import ApiError
from ..urls import thumbnail_url

COURSE_SELECT = """
    SELECT c.*, u.name AS instructor_name, i.headline AS instructor_headline,
           i.bio AS instructor_bio, i.expertise AS instructor_expertise,
           (SELECT COUNT(*) FROM lessons l WHERE l.course_id = c.id) AS lesson_count,
           (SELECT COALESCE(SUM(l.duration_seconds), 0) FROM lessons l WHERE l.course_id = c.id)
               AS duration_seconds,
           (SELECT COUNT(*) FROM quizzes q WHERE q.course_id = c.id) AS quiz_count,
           (SELECT COUNT(*) FROM enrollments e WHERE e.course_id = c.id) AS student_count
    FROM courses c
    JOIN instructors i ON i.user_id = c.instructor_id
    JOIN users u ON u.id = i.user_id
"""


def course_json(row, detail=False):
    data = {key: row[key] for key in (
        "id", "title", "summary", "category", "level", "status", "instructor_id",
        "lesson_count", "quiz_count", "student_count", "created_at", "updated_at")}
    data["duration_seconds"] = int(row["duration_seconds"])
    data["is_featured"] = bool(row["is_featured"])
    data["thumbnail_url"] = thumbnail_url(row["thumbnail_key"])
    data["instructor"] = {"id": row["instructor_id"], "name": row["instructor_name"],
                          "headline": row["instructor_headline"]}
    if detail:
        data["description"] = row["description"]
        data["instructor"].update(bio=row["instructor_bio"], expertise=row["instructor_expertise"])
    return data


def get_course(db, course_id):
    row = db.one(COURSE_SELECT + " WHERE c.id = ?", (course_id,))
    if not row:
        raise ApiError("Course not found.", 404)
    return row
