from conftest import answers_for


def enrolled(world, **quiz_changes):
    teacher = world.instructor()
    course = world.course(teacher)
    if quiz_changes:
        from conftest import quiz_body
        teacher.put(f"/manage/quizzes/{course['quiz']}", quiz_body(**quiz_changes))
    student = world.register("sam@test.example", name="Sam Student")
    student.post(f"/courses/{course['id']}/enroll")
    return teacher, course, student


def test_enrollment_rules(world):
    teacher, course, student = enrolled(world)
    student.post(f"/courses/{course['id']}/enroll", expect=409)
    teacher.post(f"/courses/{course['id']}/enroll", expect=403)
    student.post("/courses/999999/enroll", expect=404)
    draft = world.course(teacher, "Draft", publish=False)
    student.post(f"/courses/{draft['id']}/enroll", expect=404)
    student.delete(f"/courses/{course['id']}/enroll")
    student.get(f"/courses/{course['id']}/learn", expect=403)


def test_watching_marks_a_lesson_complete(world):
    _, course, student = enrolled(world)
    path = f"/lessons/{course['lessons'][0]}/progress"
    body = student.put(path, {"position": 50, "watched_seconds": 50})
    assert not body["lesson"]["is_completed"] and body["progress"]["percentage"] == 0
    body = student.put(path, {"position": 95, "watched_seconds": 95})
    assert body["lesson"]["is_completed"] and body["progress"]["percentage"] == 33
    # Unmarking is respected even though the watch time stays above the threshold.
    assert not student.put(path, {"completed": False})["lesson"]["is_completed"]
    again = student.put(path, {"position": 99, "watched_seconds": 99})
    assert not again["lesson"]["is_completed"]
    assert again["lesson"]["watched_seconds"] == 99
    learn = student.get(f"/courses/{course['id']}/learn")
    assert learn["lessons"][0]["last_position"] == 99
    student.put(path, {"position": -4}, expect=422)


def test_quiz_scoring_and_answer_protection(world):
    _, course, student = enrolled(world, pass_percentage=100, max_attempts=2)
    view = student.get(f"/quizzes/{course['quiz']}")
    assert "correct_index" not in str(view)
    path = f"/quizzes/{course['quiz']}/submit"
    student.post(path, {"answers": {}}, expect=422)
    student.post(path, answers_for(view, [1, 99]), expect=422)
    student.post(path, answers_for(view, [True, 0]), expect=422)
    first = student.post(path, answers_for(view, [1, 1]))["result"]
    assert (first["score"], first["percentage"], first["passed"]) == (1, 50, False)
    assert not first["answers_revealed"] and "correct_index" not in str(first["review"])
    second = student.post(path, answers_for(view, [1, 0]))["result"]
    assert second["passed"] and second["percentage"] == 100 and second["answers_revealed"]
    assert second["review"][0]["correct_index"] == 1
    student.post(path, answers_for(view, [1, 0]), expect=409)
    assert student.get(f"/quizzes/{course['quiz']}")["can_attempt"] is False
    stranger = world.register("eve@test.example")
    stranger.get(f"/quiz-results/{second['id']}", expect=404)
    world.admin().get(f"/quiz-results/{second['id']}")


def test_complete_course_and_certificate(world):
    teacher, course, student = enrolled(world)
    for lesson in course["lessons"]:
        student.put(f"/lessons/{lesson}/progress", {"completed": True})
    dashboard = student.get("/student/dashboard")
    assert dashboard["enrollments"][0]["percentage"] == 66
    assert dashboard["certificates"] == []
    view = student.get(f"/quizzes/{course['quiz']}")
    body = student.post(f"/quizzes/{course['quiz']}/submit", answers_for(view, [1, 0]))
    progress = body["progress"]
    assert progress["percentage"] == 100 and progress["is_completed"]
    certificate_id = progress["certificate_id"]

    dashboard = student.get("/student/dashboard")
    certificate = dashboard["certificates"][0]
    assert certificate["course_title"] == "Testing 101"
    assert dashboard["stats"]["completed"] == 1 and dashboard["stats"]["perfect_scores"] == 1
    earned = {a["code"] for a in dashboard["achievements"] if a["earned"]}
    assert earned == {"first_step", "quiz_taker", "perfect", "graduate"}

    pdf = student.call("GET", f"/certificates/{certificate_id}/download", 200)
    assert pdf.data.startswith(b"%PDF") and "attachment" in pdf.headers["Content-Disposition"]
    other = world.register("eve@test.example")
    other.call("GET", f"/certificates/{certificate_id}/download", 404)
    checked = world.anon.get(f"/certificates/verify/{certificate['code'].lower()}")
    assert checked["certificate"]["student_name"] == "Sam Student"
    world.anon.get("/certificates/verify/LS-0000-0000-0000", expect=404)

    # Issued once, and still verifiable after the course is deleted.
    student.get(f"/courses/{course['id']}/learn")
    assert len(student.get("/student/dashboard")["certificates"]) == 1
    teacher.delete(f"/manage/courses/{course['id']}")
    assert student.get("/student/dashboard")["certificates"][0]["course_id"] is None
    world.anon.get(f"/certificates/verify/{certificate['code']}")


def test_instructor_sees_progress_and_results(world):
    teacher, course, student = enrolled(world)
    view = student.get(f"/quizzes/{course['quiz']}")
    student.post(f"/quizzes/{course['quiz']}/submit", answers_for(view, [0, 0]))
    students = teacher.get(f"/manage/courses/{course['id']}/students")["items"]
    assert students[0]["student_name"] == "Sam Student" and students[0]["percentage"] == 33
    results = teacher.get(f"/manage/courses/{course['id']}/results")["items"]
    assert results[0]["percentage"] == 50
