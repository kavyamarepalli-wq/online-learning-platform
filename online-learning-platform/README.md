# LearnSphere - Online Learning Platform

A full stack learning platform where students enroll in courses, watch video lessons, download
study materials, take quizzes, track progress and earn verifiable certificates. Instructors
publish courses and administrators manage the platform.

| Layer | Technology |
|---|---|
| Frontend | React 19, plain CSS, built with esbuild |
| Backend | Python, Flask REST API, JWT authentication |
| Database | SQLite (local), PostgreSQL (cloud) |
| File storage | Local disk (local), S3-compatible object storage (cloud) |
| Certificates | PDF generated with ReportLab |
| Deployment | Vercel (frontend), Render (API), Supabase (database and files) |

## Quick start

You need **Python 3.10 or newer**. The ZIP download already contains a built frontend in
`frontend/dist`, so Node.js is only needed if you change the frontend (or cloned from Git).

Open the project folder in VS Code, open a terminal (**Terminal > New Terminal**) and run:

```bash
cd backend
python -m venv .venv
```

Activate the environment:

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1
# Windows Command Prompt
.venv\Scripts\activate.bat
# macOS / Linux
source .venv/bin/activate
```

Then:

```bash
pip install -r requirements.txt
python seed.py
python run.py
```

Open **http://localhost:5000**.

On macOS or Linux use `python3` if `python` is not found. For frontend development and other
details see [docs/SETUP.md](docs/SETUP.md).

## Demo accounts (local only)

`python seed.py` creates these. Password for all: `Learn@12345`

| Role | Email |
|---|---|
| Admin | admin@learnsphere.example |
| Instructor | priya@learnsphere.example, arjun@learnsphere.example |
| Student | ananya@learnsphere.example, rahul@learnsphere.example |

The seed refuses to use this password on a hosted database.

## Features

**Students:** register and log in, search and filter courses, enroll or leave, watch videos with
resume, download materials, take multiple-choice quizzes, see progress percentage, scores and
achievements, download PDF certificates.

**Instructors:** register (needs admin approval), create and publish courses, upload covers,
videos (or link YouTube / MP4), notes and materials, build quizzes, follow student progress and
results.

**Administrators:** overview with enrollment trend and activity, add, edit, deactivate and delete
users, approve instructors, create, update, delete and feature courses, monitor enrollments,
progress, quiz results and activity.

**Anyone:** browse the catalogue and verify a certificate by its ID.

## How completion works

- A video lesson with a known length completes after 90% of it has played; skipping ahead does
  not count. Students can also mark any lesson complete themselves (needed for reading and
  YouTube lessons).
- Progress = (completed lessons + passed quizzes) / (lessons + quizzes).
- At 100% a certificate is issued once. It stays valid if the course later changes or is deleted.
- Correct quiz answers are revealed only after passing or using all attempts.

## Tests

```bash
cd backend
python -m pytest
```

## Documentation

- [Setup instructions](docs/SETUP.md)
- [Project structure](docs/PROJECT_STRUCTURE.md)
- [Database schema](docs/DATABASE.md)
- [API documentation](docs/API.md)
- [Cloud deployment](docs/DEPLOYMENT.md)
- [Testing report](docs/TESTING.md)

## Known limitations

- All courses are free; there is no payment system.
- No email verification or "forgot password" email. An admin can set a new password for a user.
- The sample lesson videos are short, silent slide videos. Replace them with your own.
- Certificate PDFs use built-in fonts, so names in non-Latin scripts will not print correctly.
- Watch time is reported by the browser, so completion is not tamper-proof.
- The sign-in token is kept in browser storage. Rate limits are counted per server process.
