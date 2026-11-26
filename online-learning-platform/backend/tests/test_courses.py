from urllib.parse import urlsplit

from conftest import MP4, PDF, PNG, quiz_body


def fetch(world, url, **options):
    parts = urlsplit(url)
    return world.client.get(f"{parts.path}?{parts.query}", **options)


def test_cannot_publish_without_a_lesson(world):
    teacher = world.instructor()
    details = {"title": "Empty", "summary": "Nothing in here yet.",
               "description": "A description that is long enough.", "category": "Other",
               "level": "Beginner", "status": "published"}
    body = teacher.post("/manage/courses", details, expect=422)
    assert "status" in body["fields"]


def test_catalog_search_filter_and_drafts(world):
    teacher = world.instructor()
    world.course(teacher, "Python Basics")
    world.course(teacher, "Advanced SQL")
    draft = world.course(teacher, "Secret Draft", publish=False)
    listing = world.anon.get("/courses")
    assert listing["total"] == 2
    assert world.anon.get("/courses?q=PYTHON")["items"][0]["title"] == "Python Basics"
    assert world.anon.get("/courses?q=tina")["total"] == 2
    assert world.anon.get("/courses?q=%25")["total"] == 0
    assert world.anon.get("/courses?q=' OR 1=1 --")["total"] == 0
    assert world.anon.get("/courses?category=Design")["total"] == 0
    assert world.anon.get("/courses?level=Beginner&sort=title")["items"][0]["title"] == "Advanced SQL"
    assert world.anon.get("/courses?sort=popular&per_page=1&page=2")["pages"] == 2
    world.anon.get(f"/courses/{draft['id']}", expect=404)
    teacher.get(f"/courses/{draft['id']}")
    assert world.anon.get("/stats")["courses"] == 2


def test_public_details_never_expose_files_or_answers(world):
    teacher = world.instructor()
    course = world.course(teacher)
    body = world.anon.get(f"/courses/{course['id']}")
    text = str(body)
    assert "videos/" not in text and "materials/" not in text and "correct_index" not in text
    world.anon.get(f"/courses/{course['id']}/learn", expect=401)
    student = world.register("sam@test.example")
    student.get(f"/courses/{course['id']}/learn", expect=403)
    student.get(f"/quizzes/{course['quiz']}", expect=403)


def test_signed_file_links(world):
    teacher = world.instructor()
    course = world.course(teacher)
    student = world.register("sam@test.example")
    student.post(f"/courses/{course['id']}/enroll")
    learn = student.get(f"/courses/{course['id']}/learn")
    video_url = learn["lessons"][0]["video_url"]
    whole = fetch(world, video_url)
    assert whole.status_code == 200 and whole.data == MP4
    part = fetch(world, video_url, headers={"Range": "bytes=0-9"})
    assert part.status_code == 206 and len(part.data) == 10
    material = fetch(world, learn["materials"][0]["download_url"])
    assert material.data == PDF
    assert "attachment" in material.headers["Content-Disposition"]
    assert fetch(world, video_url.replace("signature=", "signature=0")).status_code == 403
    assert fetch(world, video_url.replace("expires=", "expires=1")).status_code == 403
    path = urlsplit(video_url).path
    assert world.client.get(path).status_code == 403
    assert world.client.get(path.replace("/signed/", "/public/")).status_code == 404


def test_instructors_cannot_touch_each_others_courses(world):
    owner, other = world.instructor(), world.instructor("other@test.example")
    course = world.course(owner)
    other.get(f"/manage/courses/{course['id']}", expect=404)
    other.put(f"/manage/courses/{course['id']}", course["details"], expect=404)
    other.delete(f"/manage/courses/{course['id']}", expect=404)
    other.delete(f"/manage/lessons/{course['lessons'][0]}", expect=404)
    other.delete(f"/manage/materials/{course['material']}", expect=404)
    other.put(f"/manage/quizzes/{course['quiz']}", quiz_body(), expect=404)
    other.get(f"/manage/courses/{course['id']}/students", expect=404)
    other.get(f"/courses/{course['id']}/learn", expect=403)
    assert other.get("/manage/courses")["items"] == []


def test_upload_validation_and_thumbnail(world):
    teacher = world.instructor()
    course = world.course(teacher)
    base = f"/manage/courses/{course['id']}"
    teacher.form("POST", f"{base}/materials", {"title": "Script"},
                 {"file": (b"<script>", "x.html")}, expect=422)
    teacher.form("POST", f"{base}/materials", {"title": "Fake"},
                 {"file": (b"not a pdf", "x.pdf")}, expect=422)
    teacher.form("POST", f"{base}/thumbnail", {}, {"file": (b"<svg/>", "x.svg")}, expect=422)
    teacher.form("POST", f"{base}/materials", {"title": "Huge"},
                 {"file": (b"%PDF-" + b"0" * (7 * 1024 * 1024), "big.pdf")}, expect=413)
    url = teacher.form("POST", f"{base}/thumbnail", {}, {"file": (PNG, "c.png")},
                       expect=200)["thumbnail_url"]
    assert world.client.get(urlsplit(url).path).data == PNG


def test_lesson_video_sources(world):
    teacher = world.instructor()
    course = world.course(teacher)
    base = f"/manage/courses/{course['id']}/lessons"
    lesson = teacher.form("POST", base, {
        "title": "From YouTube", "video_type": "youtube",
        "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=10"})["id"]
    editor = teacher.get(f"/manage/courses/{course['id']}")
    saved = next(x for x in editor["lessons"] if x["id"] == lesson)
    assert saved["video_url"] == "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ"
    for bad in ("https://evil.example/watch?v=dQw4w9WgXcQ", "javascript:alert(1)"):
        teacher.form("POST", base, {"title": "Bad link", "video_type": "youtube",
                                    "video_url": bad}, expect=422)
        teacher.form("POST", base, {"title": "Bad link", "video_type": "url",
                                    "video_url": bad.replace("https", "http")}, expect=422)
    teacher.form("POST", base, {"title": "Empty", "video_type": "none"}, expect=422)
    teacher.form("POST", base, {"title": "No file", "video_type": "upload"}, expect=422)


def test_edit_reorder_and_delete_clean_up_files(world, app):
    from pathlib import Path
    teacher = world.instructor()
    course = world.course(teacher)
    root = Path(app.config["UPLOAD_DIR"])
    count = lambda: sum(1 for p in root.rglob("*") if p.is_file())  # noqa: E731
    assert count() == 3
    first, second = course["lessons"]
    teacher.form("PUT", f"/manage/lessons/{first}",
                 {"title": "Renamed", "content": "n", "video_type": "upload"}, expect=200)
    assert count() == 3
    teacher.form("PUT", f"/manage/lessons/{first}",
                 {"title": "Renamed", "content": "n", "video_type": "upload"},
                 {"video": (MP4, "new.mp4")}, expect=200)
    assert count() == 3
    teacher.put(f"/manage/courses/{course['id']}/lesson-order", {"lesson_ids": [second, first]})
    editor = teacher.get(f"/manage/courses/{course['id']}")
    assert [x["id"] for x in editor["lessons"]] == [second, first]
    teacher.put(f"/manage/courses/{course['id']}/lesson-order", {"lesson_ids": [first]}, expect=422)
    teacher.delete(f"/manage/lessons/{first}")
    teacher.delete(f"/manage/lessons/{second}", expect=409)
    teacher.delete(f"/manage/courses/{course['id']}")
    assert count() == 0
    world.anon.get(f"/courses/{course['id']}", expect=404)


def test_quiz_validation(world):
    teacher = world.instructor()
    course = world.course(teacher)
    bad = quiz_body(questions=[{"prompt": "Question?", "options": ["only"], "correct_index": 3}])
    body = teacher.post(f"/manage/courses/{course['id']}/quizzes", bad, expect=422)
    assert "questions.0.options" in body["fields"]
    teacher.post(f"/manage/courses/{course['id']}/quizzes", quiz_body(questions=[]), expect=422)
