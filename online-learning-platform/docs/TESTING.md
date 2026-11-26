# Testing

## Automated API tests

```bash
cd backend
python -m pytest
```

31 tests cover authentication, roles, validation, catalogue search, file protection and uploads,
course management, progress, quiz scoring, certificates, admin functions and storage signing.

To run them against PostgreSQL, set `TEST_DATABASE_URL` to a **disposable** database. Every table
in it is dropped before each test.

## What was verified before delivery

| Check | Result |
|---|---|
| API tests, SQLite | Passed |
| API tests, PostgreSQL 16 | Passed, using a temporary stand-in driver instead of `psycopg` |
| Browser flows in Chromium: student, instructor, admin, certificates | 25 steps passed |
| Same flows with the frontend on a separate port and S3-style storage | Passed against a local stand-in storage server |
| Phone (360 px) and tablet (768 px) layouts | No horizontal page overflow on the checked pages |
| AWS Signature V4 pre-signed URL | Matches the published AWS example |

## Not verified

- Deployment to live Render, Vercel or Supabase accounts
- The real `psycopg` driver, `gunicorn` and the `Dockerfile`
- `npm install` from the public registry (the build used locally installed copies of the same
  versions of React, React DOM, React Icons and esbuild)
- Windows and macOS, Safari and Firefox
- YouTube playback (link handling is tested; the player needs internet access)

## Manual checklist for a viva or demo

1. Register, log in with a wrong password, then log in correctly.
2. Search and filter courses; enroll.
3. Watch a video, reload and see it resume; download the PDF.
4. Fail a quiz, retry and pass; download and verify the certificate.
5. As instructor, create, upload to and publish a course.
6. As admin, approve an instructor and deactivate a student.
