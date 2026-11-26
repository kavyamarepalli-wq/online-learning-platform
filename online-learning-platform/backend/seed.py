"""Loads starter instructors, students, courses, videos, materials and quizzes.

    python seed.py                      # local: uses the demo password below
    python seed.py --password "..."     # choose the password (required for a hosted database)

Safe to run more than once: it stops if courses already exist.
"""
import argparse
import json
import sys
import uuid
from io import BytesIO
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from app import create_app
from app.db import connect, now
from app.services.activity import log
from app.services.users import create_user
from app.validation import password_problem
from seed_data import COURSES, INSTRUCTORS, STUDENTS

ASSETS = Path(__file__).resolve().parent / "seed_assets"
DEMO_PASSWORD = "Learn@12345"
ADMIN_EMAIL = "admin@learnsphere.example"
VIDEO_SECONDS = 30


def handbook(course):
    """A PDF study guide built from the lesson notes."""
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    document = SimpleDocTemplate(buffer, pagesize=A4, title=f"{course['title']} - Study Guide")
    story = [Paragraph(f"{course['title']}: Study Guide", styles["Title"])]
    for number, item in enumerate(course["lessons"], start=1):
        story.append(Paragraph(f"{number}. {item['title']}", styles["Heading2"]))
        for block in item["notes"].split("\n\n"):
            safe = block.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            story += [Paragraph(safe, styles["BodyText"]), Spacer(1, 8)]
    document.build(story)
    buffer.seek(0)
    return buffer


def store(app, stream, folder, extension, content_type, download_name=None):
    key = f"{folder}/{uuid.uuid4().hex}.{extension}"
    app.extensions["storage"].save(stream, key, content_type, download_name=download_name)
    return key


def seed(app, password):
    """Returns None if data already exists, otherwise whether an admin was created."""
    db = connect(app.config["DATABASE_URL"])
    try:
        if db.scalar("SELECT COUNT(*) AS total FROM courses"):
            return None
        with_admin = not db.one("SELECT id FROM users WHERE role = 'admin' LIMIT 1")
        if with_admin:
            create_user(db, "Platform Admin", ADMIN_EMAIL, password, "admin")
        instructor_ids = [
            create_user(db, person["name"], person["email"], password, "instructor", approved=True,
                        headline=person["headline"], bio=person["bio"],
                        expertise=person["expertise"])
            for person in INSTRUCTORS]
        for person in STUDENTS:
            create_user(db, person["name"], person["email"], password, "student")

        for course in COURSES:
            stamp = now()
            with open(ASSETS / "thumbnails" / f"{course['slug']}.jpg", "rb") as image:
                thumbnail = store(app, image, "thumbnails", "jpg", "image/jpeg")
            owner = instructor_ids[course["instructor"]]
            course_id = db.insert(
                """INSERT INTO courses (instructor_id, title, summary, description, category, level,
                   thumbnail_key, status, is_featured, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 'published', ?, ?, ?)""",
                (owner, course["title"], course["summary"], course["description"],
                 course["category"], course["level"], thumbnail, int(course["featured"]),
                 stamp, stamp))
            for position, item in enumerate(course["lessons"], start=1):
                with open(ASSETS / "videos" / f"{course['slug']}-{item['slug']}.mp4", "rb") as clip:
                    key = store(app, clip, "videos", "mp4", "video/mp4")
                db.execute(
                    """INSERT INTO lessons (course_id, title, content, video_type, video_key,
                       duration_seconds, position, created_at)
                       VALUES (?, ?, ?, 'upload', ?, ?, ?, ?)""",
                    (course_id, item["title"], item["notes"], key, VIDEO_SECONDS, position, stamp))

            guide = handbook(course)
            size = len(guide.getvalue())
            file_name = f"{course['slug']}-study-guide.pdf"
            key = store(app, guide, "materials", "pdf", "application/pdf", file_name)
            db.execute(
                """INSERT INTO study_materials (course_id, title, file_key, file_name,
                   content_type, file_size, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (course_id, "Course study guide", key, file_name, "application/pdf", size, stamp))

            quiz_id = db.insert(
                """INSERT INTO quizzes (course_id, title, description, pass_percentage,
                   max_attempts, created_at) VALUES (?, ?, ?, 75, 0, ?)""",
                (course_id, f"{course['title']} quiz",
                 "Answer every question. You need 75% to pass.", stamp))
            for position, question in enumerate(course["quiz"]):
                db.execute(
                    """INSERT INTO quiz_questions (quiz_id, prompt, options, correct_index,
                       explanation, position) VALUES (?, ?, ?, ?, ?, ?)""",
                    (quiz_id, question["prompt"], json.dumps(question["options"]),
                     question["correct"], question["explanation"], position))
            log(db, owner, "course_created", f"Created '{course['title']}'")
        db.commit()
        return with_admin
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Load starter data")
    parser.add_argument("--password", help="password for the accounts that are created")
    args = parser.parse_args()
    app = create_app()
    # The public demo password must never reach a hosted database.
    hosted = (app.config["APP_ENV"] == "production"
              or not app.config["DATABASE_URL"].startswith("sqlite"))
    if hosted and (not args.password or args.password == DEMO_PASSWORD):
        sys.exit("For a hosted database, pass your own password:  python seed.py --password \"...\"")
    password = args.password or DEMO_PASSWORD
    problem = password_problem(password)
    if problem:
        sys.exit(problem)

    created_admin = seed(app, password)
    if created_admin is None:
        print("Courses already exist. Nothing was changed.")
        return
    print(f"Added {len(COURSES)} courses.\n\nSign-in accounts (password: {password}):")
    if created_admin:
        print(f"  admin       {ADMIN_EMAIL}")
    for person in INSTRUCTORS:
        print(f"  instructor  {person['email']}")
    for person in STUDENTS:
        print(f"  student     {person['email']}")


if __name__ == "__main__":
    main()
