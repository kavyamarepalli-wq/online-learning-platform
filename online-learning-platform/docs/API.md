# API documentation

Base URL: `http://localhost:5000/api` (production: `https://YOUR-API/api`)

## Conventions

- Requests and responses are JSON, except file uploads (`multipart/form-data`) and downloads.
- Authenticated requests send `Authorization: Bearer <token>`.
- Errors use an HTTP status and this shape:

```json
{ "error": "Please fix the highlighted fields.", "fields": { "email": "Enter a valid email address." } }
```

| Status | Meaning |
|---|---|
| 400 | Malformed request |
| 401 | Not signed in, wrong password or expired session |
| 403 | Not allowed (role, approval, not enrolled, bad file link) |
| 404 | Not found (also used for other instructors' courses) |
| 409 | Conflict (duplicate email, already enrolled, no attempts left) |
| 413 | Upload too large |
| 422 | Validation failed; see `fields` |
| 429 | Too many attempts |
| 500 | Server error |

Paginated lists accept `page` and `per_page` (max 50) and return
`{ "items": [], "total": 0, "page": 1, "per_page": 10, "pages": 1 }`.

**Access** below: *Public*, *User* (any signed-in user), *Student*, *Staff* (approved instructor
for own courses, or admin), *Admin*.

## Authentication

| Method | Path | Access | Body / notes |
|---|---|---|---|
| POST | `/auth/register` | Public | `name, email, password, role` (`student` or `instructor`); instructors also `headline`, optional `bio`. Returns `201 {token, user}` |
| POST | `/auth/login` | Public | `email, password` returns `{token, user}` |
| GET | `/auth/me` | User | `{user}` |
| PUT | `/auth/profile` | User | `name`; instructors `headline, bio, expertise` |
| PUT | `/auth/password` | User | `current_password, new_password`; returns a new token and ends other sessions |

Passwords need 8 to 128 characters with a letter and a number.

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"ananya@learnsphere.example","password":"Learn@12345"}'
```

## Catalogue

| Method | Path | Access | Notes |
|---|---|---|---|
| GET | `/health` | Public | `{status: "ok"}` when the database answers |
| GET | `/meta` | Public | Categories and levels |
| GET | `/stats` | Public | Totals and courses per category |
| GET | `/courses` | Public | Query: `q, category, level, featured=1, sort=newest\|popular\|title, page, per_page` |
| GET | `/courses/{id}` | Public | Course, lesson outline, material names, quizzes, `is_enrolled`, `can_manage` |

## Learning

| Method | Path | Access | Notes |
|---|---|---|---|
| POST | `/courses/{id}/enroll` | Student | Enroll |
| DELETE | `/courses/{id}/enroll` | Student | Leave the course |
| GET | `/courses/{id}/learn` | Enrolled or Staff | Lessons with video links, materials with download links, quizzes, progress |
| PUT | `/lessons/{id}/progress` | Student | Any of `position, watched_seconds, completed`. Returns `{lesson, progress}` |
| GET | `/student/dashboard` | Student | `stats, enrollments, results, certificates, achievements` |

Progress object:

```json
{ "enrollment_id": 1, "percentage": 75, "is_completed": false, "completed_at": null,
  "total_lessons": 3, "completed_lessons": 3, "total_quizzes": 1, "passed_quizzes": 0,
  "certificate_id": null }
```

## Quizzes

| Method | Path | Access | Notes |
|---|---|---|---|
| GET | `/quizzes/{id}` | Enrolled or Staff | Questions **without** answers, past attempts, `can_attempt` |
| POST | `/quizzes/{id}/submit` | Student | `{ "answers": { "<questionId>": <optionIndex> } }`. Returns `201 {result, progress}` |
| GET | `/quiz-results/{id}` | Owner or Staff | One attempt with review |

`result.answers_revealed` is `false` until the student passes or has no attempts left; the review
then omits `correct_index` and `explanation`.

## Certificates

| Method | Path | Access | Notes |
|---|---|---|---|
| GET | `/certificates/{id}/download` | Owner or Admin | PDF file |
| GET | `/certificates/verify/{code}` | Public | `{valid, certificate}` |

## Course management (`/manage`)

| Method | Path | Body |
|---|---|---|
| GET | `/manage/courses` | Own courses (admin: all) |
| POST | `/manage/courses` | `title, summary, description, category, level, status`; admin also `instructor_id, is_featured` |
| GET | `/manage/courses/{id}` | Full course including quiz answers |
| PUT | `/manage/courses/{id}` | Same fields as create. Publishing needs at least one lesson |
| DELETE | `/manage/courses/{id}` | Deletes content, files and enrollments |
| POST | `/manage/courses/{id}/thumbnail` | multipart `file` (png, jpg, webp; 5 MB) |
| GET | `/manage/instructors` | Approved instructors (admin; empty for others) |
| POST | `/manage/courses/{id}/lessons` | multipart, see below |
| PUT | `/manage/lessons/{id}` | multipart, see below |
| DELETE | `/manage/lessons/{id}` | |
| PUT | `/manage/courses/{id}/lesson-order` | `{ "lesson_ids": [3, 1, 2] }` |
| POST | `/manage/courses/{id}/materials` | multipart `title, file`, optional `lesson_id` (25 MB) |
| DELETE | `/manage/materials/{id}` | |
| POST | `/manage/courses/{id}/quizzes` | Quiz JSON, see below |
| PUT | `/manage/quizzes/{id}` | Quiz JSON (replaces the questions) |
| DELETE | `/manage/quizzes/{id}` | Also deletes its results |
| GET | `/manage/courses/{id}/students` | Progress of each student |
| GET | `/manage/courses/{id}/results` | Latest 500 quiz attempts |

All `/manage` endpoints need *Staff* access.

Lesson fields: `title`, `content`, `video_type` (`none`, `upload`, `youtube`, `url`),
`duration_seconds`, `video_url` (for `youtube` and `url`), `video` file (mp4 or webm, for
`upload`; may be omitted when editing to keep the current file). Send every field when editing.

Quiz JSON:

```json
{
  "title": "Basics", "description": "", "pass_percentage": 60, "max_attempts": 0,
  "questions": [
    { "prompt": "2 + 2 = ?", "options": ["3", "4"], "correct_index": 1, "explanation": "" }
  ]
}
```

## Administration (`/admin`, Admin only)

| Method | Path | Notes |
|---|---|---|
| GET | `/admin/overview` | Counts, 14-day enrollments, top courses, recent activity |
| GET | `/admin/users` | Query: `q, role, pending=1, page` |
| POST | `/admin/users` | `name, email, password, role`, optional `headline` |
| PUT | `/admin/users/{id}` | `name, email, is_active`, optional `password` |
| DELETE | `/admin/users/{id}` | Not yourself, nor an instructor who has courses |
| PUT | `/admin/instructors/{id}/approval` | `{ "approved": true }` |
| GET | `/admin/enrollments` | Query: `q, page`; includes progress |
| DELETE | `/admin/enrollments/{id}` | Remove a student from a course |
| GET | `/admin/results` | Query: `q, page` |
| GET | `/admin/activity` | Query: `q, page` |

Courses are managed through the `/manage` endpoints.

## Files

| Method | Path | Notes |
|---|---|---|
| GET | `/files/public/{key}` | Course covers only |
| GET | `/files/signed/{key}` | Local storage. Needs `expires` and `signature`; supports range requests |

Clients never build these links: the API returns them. Content links expire after 6 hours. With
S3 storage the API returns pre-signed storage URLs instead.
