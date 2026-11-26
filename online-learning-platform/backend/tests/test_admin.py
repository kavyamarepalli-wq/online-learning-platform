from conftest import PASSWORD, answers_for


def test_overview_and_monitoring(world):
    teacher = world.instructor()
    course = world.course(teacher)
    student = world.register("sam@test.example", name="Sam Student")
    student.post(f"/courses/{course['id']}/enroll")
    view = student.get(f"/quizzes/{course['quiz']}")
    student.post(f"/quizzes/{course['quiz']}/submit", answers_for(view, [1, 0]))
    admin = world.admin()
    overview = admin.get("/admin/overview")
    assert overview["counts"]["students"] == 1 and overview["counts"]["enrollments"] == 1
    assert len(overview["enrollments_by_day"]) == 14
    assert overview["enrollments_by_day"][-1]["total"] == 1
    assert overview["top_courses"][0]["students"] == 1
    assert admin.get("/admin/enrollments?q=sam")["total"] == 1
    assert admin.get("/admin/enrollments?q=nobody")["total"] == 0
    assert admin.get("/admin/results?q=check")["items"][0]["percentage"] == 100
    assert admin.get("/admin/activity?q=enrolled")["total"] >= 1
    enrollment = admin.get("/admin/enrollments")["items"][0]["enrollment_id"]
    admin.delete(f"/admin/enrollments/{enrollment}")
    assert admin.get("/admin/enrollments")["total"] == 0


def test_manage_users(world):
    admin = world.admin()
    created = admin.post("/admin/users", {
        "name": "New Person", "email": "np@test.example", "password": PASSWORD,
        "role": "student"})["user"]
    person = world.login("np@test.example")
    update = {"name": "Renamed Person", "email": "np@test.example", "is_active": False}
    admin.put(f"/admin/users/{created['id']}", update)
    person.get("/auth/me", expect=401)
    world.anon.post("/auth/login", {"email": "np@test.example", "password": PASSWORD}, expect=403)
    admin.put(f"/admin/users/{created['id']}", {**update, "is_active": True,
                                               "password": "Another123"})
    world.login("np@test.example", "Another123")
    assert admin.get("/admin/users?q=renamed")["total"] == 1
    assert admin.get("/admin/users?role=student")["total"] == 1
    admin.delete(f"/admin/users/{created['id']}")
    assert admin.get("/admin/users?role=student")["total"] == 0
    me = admin.user["id"]
    admin.delete(f"/admin/users/{me}", expect=409)
    admin.put(f"/admin/users/{me}", {"name": "Admin", "email": "admin@test.example",
                                     "is_active": False}, expect=422)


def test_instructor_approval_and_deletion_guard(world):
    admin = world.admin()
    pending = world.register("new@test.example", "instructor")
    assert admin.get("/admin/users?pending=1")["total"] == 1
    admin.put(f"/admin/instructors/{pending.user['id']}/approval", {"approved": True})
    course = world.course(pending)
    admin.delete(f"/admin/users/{pending.user['id']}", expect=409)
    admin.put(f"/admin/instructors/{pending.user['id']}/approval", {"approved": False})
    pending.get("/manage/courses", expect=403)
    admin.delete(f"/manage/courses/{course['id']}")
    admin.delete(f"/admin/users/{pending.user['id']}")


def test_admin_creates_and_reassigns_courses(world):
    admin = world.admin()
    first, second = world.instructor(), world.instructor("two@test.example")
    details = {"title": "Admin made", "summary": "Created by the administrator.",
               "description": "A description that is long enough.", "category": "Other",
               "level": "Advanced", "status": "draft", "is_featured": True}
    admin.post("/manage/courses", details, expect=422)
    course = admin.post("/manage/courses",
                        {**details, "instructor_id": first.user["id"]})["course"]
    assert course["is_featured"]
    admin.put(f"/manage/courses/{course['id']}", {**details, "instructor_id": second.user["id"]})
    assert [c["id"] for c in second.get("/manage/courses")["items"]] == [course["id"]]
    assert first.get("/manage/courses")["items"] == []
    assert len(admin.get("/manage/instructors")["items"]) == 2


def test_instructor_cannot_feature_own_course(world):
    teacher = world.instructor()
    course = world.course(teacher)
    teacher.put(f"/manage/courses/{course['id']}",
                {**course["details"], "status": "published", "is_featured": True})
    assert world.anon.get("/courses?featured=1")["total"] == 0
