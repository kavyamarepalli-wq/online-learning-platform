"""Test fixtures. Tests use a throw-away SQLite database by default.

Set TEST_DATABASE_URL to a *disposable* PostgreSQL database to run them against
PostgreSQL. All of its tables are dropped before every test.
"""
import io
import os

import pytest

from app import create_app, ratelimit
from app.db import connect

TABLES = ["activity_logs", "certificates", "quiz_results", "learning_progress", "enrollments",
          "quiz_questions", "quizzes", "study_materials", "lessons", "courses", "instructors",
          "users"]
PASSWORD = "Passw0rd123"
ADMIN = "admin@test.example"
MP4 = b"\x00\x00\x00\x18ftypmp42" + b"0" * 2000
PDF = b"%PDF-1.4\n% test file\n" + b"0" * 100
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 100


@pytest.fixture
def app(tmp_path):
    url = os.environ.get("TEST_DATABASE_URL") or f"sqlite:///{tmp_path / 'test.db'}"
    if url.startswith("postgresql://"):
        db = connect(url)
        for table in TABLES:
            db.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
        db.commit()
        db.close()
    ratelimit.reset()
    return create_app({
        "APP_ENV": "development", "DATABASE_URL": url, "SECRET_KEY": "test-secret-" * 4,
        "UPLOAD_DIR": str(tmp_path / "uploads"), "STORAGE_BACKEND": "local",
        "ADMIN_EMAIL": ADMIN, "ADMIN_PASSWORD": PASSWORD, "PUBLIC_API_URL": "",
        "FRONTEND_URL": "http://frontend.test", "MAX_UPLOAD_MB": "5",
        "FRONTEND_DIST": str(tmp_path / "no-dist"),
    })


class Api:
    """A signed-in (or anonymous) caller of the API."""

    def __init__(self, client, token=None, user=None):
        self.client, self.token, self.user = client, token, user

    def call(self, method, path, expect=None, **options):
        headers = options.pop("headers", {})
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        response = self.client.open(f"/api{path}", method=method, headers=headers, **options)
        if expect is not None:
            assert response.status_code == expect, (response.status_code, response.get_data()[:500])
        return response

    def get(self, path, expect=200):
        return self.call("GET", path, expect).get_json()

    def post(self, path, json=None, expect=201):
        return self.call("POST", path, expect, json=json or {}).get_json()

    def put(self, path, json=None, expect=200):
        return self.call("PUT", path, expect, json=json or {}).get_json()

    def delete(self, path, expect=200):
        return self.call("DELETE", path, expect).get_json()

    def form(self, method, path, fields, files=None, expect=201):
        data = dict(fields)
        for name, (content, filename) in (files or {}).items():
            data[name] = (io.BytesIO(content), filename)
        return self.call(method, path, expect, data=data,
                         content_type="multipart/form-data").get_json()


class World:
    def __init__(self, app):
        self.app = app
        self.client = app.test_client()
        self.anon = Api(self.client)

    def login(self, email, password=PASSWORD):
        body = self.anon.post("/auth/login", {"email": email, "password": password}, expect=200)
        return Api(self.client, body["token"], body["user"])

    def register(self, email, role="student", name="Test Person"):
        body = self.anon.post("/auth/register", {
            "name": name, "email": email, "password": PASSWORD, "role": role,
            "headline": "Teacher of tests", "bio": ""})
        return Api(self.client, body["token"], body["user"])

    def admin(self):
        return self.login(ADMIN)

    def instructor(self, email="teach@test.example"):
        teacher = self.register(email, "instructor", "Tina Teacher")
        self.admin().put(f"/admin/instructors/{teacher.user['id']}/approval", {"approved": True})
        return teacher

    def course(self, teacher, title="Testing 101", publish=True):
        """A published course with two video lessons, a material and a two-question quiz."""
        details = {"title": title, "summary": "A course used by the automated tests.",
                   "description": "Long enough description of the testing course.",
                   "category": "Programming", "level": "Beginner", "status": "draft"}
        course_id = teacher.post("/manage/courses", details)["course"]["id"]
        lessons = [teacher.form(
            "POST", f"/manage/courses/{course_id}/lessons",
            {"title": f"Lesson {n}", "content": "Notes", "video_type": "upload",
             "duration_seconds": "100"},
            {"video": (MP4, "clip.mp4")})["id"] for n in (1, 2)]
        material = teacher.form(
            "POST", f"/manage/courses/{course_id}/materials", {"title": "Handout"},
            {"file": (PDF, "handout.pdf")})["id"]
        quiz = teacher.post(f"/manage/courses/{course_id}/quizzes", quiz_body())["id"]
        if publish:
            teacher.put(f"/manage/courses/{course_id}", {**details, "status": "published"})
        return {"id": course_id, "lessons": lessons, "material": material, "quiz": quiz,
                "details": details}


def quiz_body(**changes):
    body = {"title": "Check", "description": "", "pass_percentage": 50, "max_attempts": 0,
            "questions": [
                {"prompt": "One plus one?", "options": ["1", "2"], "correct_index": 1,
                 "explanation": "Arithmetic."},
                {"prompt": "Two plus two?", "options": ["4", "5", "6"], "correct_index": 0,
                 "explanation": "More arithmetic."}]}
    body.update(changes)
    return body


def answers_for(quiz_view, picks):
    return {"answers": {str(q["id"]): pick for q, pick in zip(quiz_view["questions"], picks)}}


@pytest.fixture
def world(app):
    return World(app)
