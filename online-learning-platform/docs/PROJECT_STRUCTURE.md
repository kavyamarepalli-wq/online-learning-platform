# Project structure

```
online-learning-platform/
├── backend/                    Flask REST API
│   ├── app/
│   │   ├── __init__.py         application factory, headers, CORS, static site
│   │   ├── config.py           environment settings, categories, levels
│   │   ├── db.py               SQLite / PostgreSQL layer
│   │   ├── auth.py             tokens and role checks
│   │   ├── validation.py       input validation
│   │   ├── errors.py           JSON error responses
│   │   ├── storage.py          local and S3 file storage
│   │   ├── uploads.py          upload checks
│   │   ├── urls.py             file links
│   │   ├── pagination.py       paging and search patterns
│   │   ├── ratelimit.py        sign-in rate limiting
│   │   ├── routes/             auth, catalog, learning, manage, admin, files
│   │   └── services/           users, courses, progress, activity, certificate_pdf
│   ├── tests/                  pytest suite
│   ├── tools/make_seed_assets.py   rebuilds sample covers and videos
│   ├── seed_assets/            sample covers and lesson videos
│   ├── seed.py, seed_data.py   starter data
│   ├── manage.py               init-db, create-admin
│   ├── run.py                  development server
│   ├── wsgi.py                 production entry point
│   ├── requirements.txt, pytest.ini, .env.example
├── frontend/                   React single-page app
│   ├── public/                 index.html, favicon.svg
│   ├── src/
│   │   ├── main.jsx, App.jsx, styles.css
│   │   ├── lib/                api, router, auth, hooks, format
│   │   ├── components/         Layout, CourseCard, ui
│   │   └── pages/              Home, Courses, CourseDetails, Login, Register, Learn,
│   │       │                   Quiz, StudentDashboard, Profile, Verify
│   │       ├── manage/         InstructorDashboard, CourseTable, CourseEditor,
│   │       │                   LessonsPanel, MaterialsPanel, QuizzesPanel, CourseStudents
│   │       └── admin/          AdminDashboard, Overview, Users, Monitoring
│   ├── build.mjs, package.json, vercel.json, .env.example
├── database/schema.sql         tables and indexes
├── docs/                       SETUP, DEPLOYMENT, API, DATABASE, TESTING, this file
├── .vscode/                    run and task settings
├── render.yaml                 Render Blueprint (backend)
├── Dockerfile, .dockerignore   optional single-container build
├── .gitignore
└── README.md
```

Created at run time and not committed: `backend/instance/` (SQLite database), `backend/uploads/`,
`frontend/node_modules/` and `frontend/dist/`.
