# Setup instructions

## 1. Requirements

| Tool | Version | Needed for |
|---|---|---|
| Python | 3.10 or newer | Backend (required) |
| Node.js | 18 or newer (with npm) | Frontend development and builds |
| VS Code | any recent | Recommended editor |

PostgreSQL is **not** needed locally: the backend uses SQLite automatically.

## 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python seed.py                   # demo accounts, 6 courses, videos, PDFs, quizzes
python run.py                    # http://localhost:5000
```

If PowerShell blocks activation, run
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` in that terminal first.

Settings are optional locally. To change any, copy `.env.example` to `.env`.

To start with an empty platform, skip `seed.py` and create your administrator:

```bash
python manage.py create-admin --email you@example.com --name "Your Name"
```

To reset local data, stop the server, delete `backend/instance` and `backend/uploads`, then seed
again.

## 3. Frontend

Open a **second** terminal:

```bash
cd frontend
npm install
npm run dev                      # http://localhost:5173
```

The development server calls the API at `http://localhost:5000`. To use another address, copy
`.env.example` to `.env` and set `API_URL`. Reload the browser after editing source files.

### One server for everything

```bash
cd frontend
npm run build                    # with no .env file, the API address is "same origin"
cd ../backend
python run.py                    # website and API on http://localhost:5000
```

If you created `frontend/.env`, set `API_URL=` (empty) before building for this mode.

## 4. VS Code

- Open the folder that contains `README.md` (**File > Open Folder**).
- Select the interpreter from `backend/.venv` (**Python: Select Interpreter**).
- Press **F5** to run "Backend (Flask)".
- **Terminal > Run Task** offers the frontend tasks.

## 5. First walk-through

1. Log in as `ananya@learnsphere.example`, enroll in a course.
2. Watch the videos, pass the quiz, then download the certificate from **My learning**.
3. Log in as `priya@learnsphere.example` to create a course in the **Instructor studio**. Save it
   as a draft, add a lesson, then set the status to *Published*.
4. Log in as `admin@learnsphere.example` to manage users and watch activity.

## 6. Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: flask` | Activate the virtual environment and run `pip install -r requirements.txt`. |
| "The frontend has not been built" | Run `npm run build` in `frontend`, or use `npm run dev`. |
| "Cannot reach the server" | Start the backend; check `API_URL`. |
| Port 5000 is busy (common on macOS) | Set `PORT=5001` before `python run.py`. For `npm run dev`, also set `API_URL=http://localhost:5001`. |
| "Courses already exist" when seeding | Delete `backend/instance` and `backend/uploads` to start again. |
| Upload says the file is too large | Raise `MAX_UPLOAD_MB` in `backend/.env` (images max 5 MB, materials 25 MB). |
