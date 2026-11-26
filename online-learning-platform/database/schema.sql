-- Online Learning Platform - database schema (PostgreSQL).
-- The backend applies this file automatically on start-up. For local development
-- with SQLite, "SERIAL PRIMARY KEY" is translated to SQLite's auto-increment key.
-- Timestamps are ISO-8601 UTC text (e.g. 2026-01-31T10:15:00Z) so both engines behave alike.

CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    email           VARCHAR(254) NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    role            VARCHAR(20) NOT NULL CHECK (role IN ('student', 'instructor', 'admin')),
    is_active       INTEGER NOT NULL DEFAULT 1,
    token_version   INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL,
    last_login_at   TEXT
);

CREATE TABLE IF NOT EXISTS instructors (
    user_id         INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    headline        VARCHAR(150) NOT NULL DEFAULT '',
    bio             TEXT NOT NULL DEFAULT '',
    expertise       VARCHAR(200) NOT NULL DEFAULT '',
    is_approved     INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS courses (
    id              SERIAL PRIMARY KEY,
    instructor_id   INTEGER NOT NULL REFERENCES instructors(user_id) ON DELETE RESTRICT,
    title           VARCHAR(150) NOT NULL,
    summary         VARCHAR(300) NOT NULL,
    description     TEXT NOT NULL,
    category        VARCHAR(60) NOT NULL,
    level           VARCHAR(20) NOT NULL CHECK (level IN ('Beginner', 'Intermediate', 'Advanced')),
    thumbnail_key   TEXT,
    status          VARCHAR(20) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'published')),
    is_featured     INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS lessons (
    id               SERIAL PRIMARY KEY,
    course_id        INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    title            VARCHAR(150) NOT NULL,
    content          TEXT NOT NULL DEFAULT '',
    video_type       VARCHAR(10) NOT NULL DEFAULT 'none'
                     CHECK (video_type IN ('none', 'upload', 'youtube', 'url')),
    video_key        TEXT,
    video_url        TEXT,
    duration_seconds INTEGER NOT NULL DEFAULT 0,
    position         INTEGER NOT NULL DEFAULT 0,
    created_at       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS study_materials (
    id              SERIAL PRIMARY KEY,
    course_id       INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    lesson_id       INTEGER REFERENCES lessons(id) ON DELETE SET NULL,
    title           VARCHAR(150) NOT NULL,
    file_key        TEXT NOT NULL,
    file_name       VARCHAR(200) NOT NULL,
    content_type    VARCHAR(150) NOT NULL,
    file_size       INTEGER NOT NULL,
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS quizzes (
    id              SERIAL PRIMARY KEY,
    course_id       INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    title           VARCHAR(150) NOT NULL,
    description     TEXT NOT NULL DEFAULT '',
    pass_percentage INTEGER NOT NULL DEFAULT 60 CHECK (pass_percentage BETWEEN 1 AND 100),
    max_attempts    INTEGER NOT NULL DEFAULT 0,  -- 0 means unlimited
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS quiz_questions (
    id              SERIAL PRIMARY KEY,
    quiz_id         INTEGER NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
    prompt          TEXT NOT NULL,
    options         TEXT NOT NULL,               -- JSON array of answer strings
    correct_index   INTEGER NOT NULL,
    explanation     TEXT NOT NULL DEFAULT '',
    position        INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS enrollments (
    id               SERIAL PRIMARY KEY,
    student_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id        INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    enrolled_at      TEXT NOT NULL,
    last_accessed_at TEXT NOT NULL,
    completed_at     TEXT,
    UNIQUE (student_id, course_id)
);

CREATE TABLE IF NOT EXISTS learning_progress (
    id              SERIAL PRIMARY KEY,
    enrollment_id   INTEGER NOT NULL REFERENCES enrollments(id) ON DELETE CASCADE,
    lesson_id       INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    watched_seconds INTEGER NOT NULL DEFAULT 0,
    last_position   INTEGER NOT NULL DEFAULT 0,
    is_completed    INTEGER NOT NULL DEFAULT 0,
    completed_at    TEXT,
    updated_at      TEXT NOT NULL,
    UNIQUE (enrollment_id, lesson_id)
);

CREATE TABLE IF NOT EXISTS quiz_results (
    id              SERIAL PRIMARY KEY,
    quiz_id         INTEGER NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
    student_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    score           INTEGER NOT NULL,
    total           INTEGER NOT NULL,
    percentage      INTEGER NOT NULL,
    passed          INTEGER NOT NULL,
    answers         TEXT NOT NULL,               -- JSON snapshot of questions and chosen answers
    submitted_at    TEXT NOT NULL
);

-- Certificates keep their own copy of names, so they stay verifiable if a course is deleted.
CREATE TABLE IF NOT EXISTS certificates (
    id              SERIAL PRIMARY KEY,
    code            VARCHAR(40) NOT NULL UNIQUE,
    student_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id       INTEGER REFERENCES courses(id) ON DELETE SET NULL,
    student_name    VARCHAR(100) NOT NULL,
    course_title    VARCHAR(150) NOT NULL,
    instructor_name VARCHAR(100) NOT NULL,
    issued_at       TEXT NOT NULL,
    UNIQUE (student_id, course_id)
);

CREATE TABLE IF NOT EXISTS activity_logs (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action          VARCHAR(60) NOT NULL,
    details         TEXT NOT NULL DEFAULT '',
    created_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_courses_catalog ON courses (status, category, level);
CREATE INDEX IF NOT EXISTS idx_courses_instructor ON courses (instructor_id);
CREATE INDEX IF NOT EXISTS idx_lessons_course ON lessons (course_id, position);
CREATE INDEX IF NOT EXISTS idx_materials_course ON study_materials (course_id);
CREATE INDEX IF NOT EXISTS idx_quizzes_course ON quizzes (course_id);
CREATE INDEX IF NOT EXISTS idx_questions_quiz ON quiz_questions (quiz_id, position);
CREATE INDEX IF NOT EXISTS idx_enrollments_course ON enrollments (course_id);
CREATE INDEX IF NOT EXISTS idx_results_student ON quiz_results (student_id, quiz_id);
CREATE INDEX IF NOT EXISTS idx_activity_created ON activity_logs (created_at);
