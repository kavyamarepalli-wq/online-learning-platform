from conftest import ADMIN, PASSWORD


def test_register_login_and_me(world):
    student = world.register("sam@test.example")
    assert student.user["role"] == "student"
    assert "password_hash" not in student.user
    again = world.login("SAM@test.example")
    assert again.get("/auth/me")["user"]["email"] == "sam@test.example"


def test_validation_errors_are_reported_per_field(world):
    body = world.anon.post("/auth/register",
                           {"name": "A", "email": "bad", "password": "short"}, expect=422)
    assert set(body["fields"]) == {"name", "email", "password"}


def test_duplicate_email_and_admin_role_rejected(world):
    world.register("sam@test.example")
    data = {"name": "Sam", "email": "sam@test.example", "password": PASSWORD}
    assert "email" in world.anon.post("/auth/register", data, expect=409)["fields"]
    data.update(email="evil@test.example", role="admin")
    assert "role" in world.anon.post("/auth/register", data, expect=422)["fields"]


def test_passwords_are_hashed(world, app):
    from app.db import connect
    world.register("sam@test.example")
    db = connect(app.config["DATABASE_URL"])
    stored = db.scalar("SELECT password_hash FROM users WHERE email = ?", ("sam@test.example",))
    db.close()
    assert PASSWORD not in stored and stored.startswith(("scrypt:", "pbkdf2:"))


def test_bad_credentials_and_tokens(world):
    world.anon.post("/auth/login", {"email": ADMIN, "password": "wrong-pass1"}, expect=401)
    world.anon.post("/auth/login", {"email": "no@test.example", "password": "x"}, expect=401)
    world.anon.get("/auth/me", expect=401)
    world.anon.call("GET", "/auth/me", 401, headers={"Authorization": "Bearer nonsense"})


def test_login_is_rate_limited(world):
    for _ in range(10):
        world.anon.post("/auth/login", {"email": ADMIN, "password": "wrong-pass1"}, expect=401)
    world.anon.post("/auth/login", {"email": ADMIN, "password": PASSWORD}, expect=429)


def test_password_change_signs_out_old_sessions(world):
    first = world.register("sam@test.example")
    second = world.login("sam@test.example")
    body = first.put("/auth/password",
                     {"current_password": PASSWORD, "new_password": "NewPassw0rd"})
    second.get("/auth/me", expect=401)
    first.token = body["token"]
    first.get("/auth/me")
    world.login("sam@test.example", "NewPassw0rd")


def test_role_protection(world):
    student = world.register("sam@test.example")
    pending = world.register("new@test.example", "instructor")
    student.get("/admin/overview", expect=403)
    student.get("/manage/courses", expect=403)
    pending.get("/manage/courses", expect=403)
    pending.get("/admin/users", expect=403)
    world.anon.get("/student/dashboard", expect=401)
    world.admin().get("/student/dashboard", expect=403)


def test_cors_only_for_configured_origin(world):
    allowed = world.client.open("/api/courses", method="OPTIONS",
                                headers={"Origin": "http://frontend.test"})
    assert allowed.headers["Access-Control-Allow-Origin"] == "http://frontend.test"
    denied = world.client.get("/api/courses", headers={"Origin": "http://evil.test"})
    assert "Access-Control-Allow-Origin" not in denied.headers


def test_unknown_endpoint_returns_json(world):
    assert "error" in world.anon.get("/nope", expect=404)
