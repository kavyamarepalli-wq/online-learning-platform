# Cloud deployment

| Part | Service |
|---|---|
| Database (PostgreSQL) | Supabase |
| Uploaded files (videos, PDFs, images) | Supabase Storage through its S3 protocol |
| Backend API | Render web service |
| Frontend | Vercel |

These steps were written from the providers' documentation in November 2026. The project has not
been deployed to a live account for you, and dashboard labels can change.

## Free plan limits to know

- Render free web services sleep after 15 minutes without traffic and take about a minute to wake.
  Their disk is erased on restart, which is why files and data live in Supabase.
- Supabase free projects pause after a week of low activity (resume them in the dashboard) and
  limit each uploaded file to 50 MB. Use YouTube links for longer videos.

## Step 1 - Push the code to GitHub

Create an empty repository on GitHub, then from the project folder:

```bash
git init
git add .
git commit -m "Online learning platform"
git branch -M main
git remote add origin https://github.com/YOUR-NAME/online-learning-platform.git
git push -u origin main
```

`.gitignore` already keeps `.env` files, local data and `node_modules` out of the repository.

## Step 2 - Database (Supabase)

1. Create a project and save the database password.
2. Click **Connect**, choose **Session pooler** and copy the connection string:
   `postgresql://postgres.PROJECT-REF:PASSWORD@aws-X-REGION.pooler.supabase.com:5432/postgres`
3. Replace the password placeholder. Percent-encode special characters (`@` becomes `%40`,
   `#` becomes `%23`). Add `?sslmode=require` to the end. This is `DATABASE_URL`.

You do not need to run SQL: the backend creates the tables on first start and enables row level
security on them, so Supabase's public Data API cannot read them. If you do not use the Data API,
you can also switch it off in the project settings.

## Step 3 - File storage (Supabase Storage)

1. In **Storage**, create a bucket, for example `learnsphere`. Keep it **private**.
2. In the Storage settings, enable the **S3 protocol** connection.
3. Create an S3 **access key** and copy both values. The secret is shown once.
4. Note the endpoint, `https://PROJECT-REF.storage.supabase.co/storage/v1/s3`, and the region
   shown on the same page.

These keys can access every bucket. Put them only in the backend's environment variables.

AWS S3 or Cloudflare R2 also work: set the same five `S3_*` variables.

## Step 4 - Backend (Render)

1. **New > Blueprint**, connect the GitHub repository. Render reads `render.yaml`.
2. Enter the values it asks for:

| Variable | Value |
|---|---|
| `DATABASE_URL` | From step 2 |
| `S3_ENDPOINT` | From step 3 |
| `S3_REGION` | From step 3 |
| `S3_BUCKET` | `learnsphere` |
| `S3_ACCESS_KEY_ID` / `S3_SECRET_ACCESS_KEY` | From step 3 |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Your first administrator (8+ characters, letters and numbers) |
| `FRONTEND_URL` | A placeholder such as `https://example.vercel.app` (updated in step 6) |

`SECRET_KEY` is generated automatically; `APP_ENV`, `STORAGE_BACKEND`, `TRUSTED_PROXIES`,
`MAX_UPLOAD_MB` and `PYTHON_VERSION` come from the file.

3. Deploy, then open `https://YOUR-SERVICE.onrender.com/api/health`. It should show
   `{"status":"ok"}`.

After the first successful sign-in you may delete `ADMIN_PASSWORD` from Render.

## Step 5 - Frontend (Vercel)

1. **Add New > Project**, import the same repository.
2. Set **Root Directory** to `frontend`.
3. Add the environment variable `API_URL` = `https://YOUR-SERVICE.onrender.com` (no trailing
   slash, no `/api`).
4. Deploy. Build settings and page rewrites come from `frontend/vercel.json`.

`API_URL` is compiled into the website, so redeploy whenever it changes. Never put secrets in it.

## Step 6 - Connect the two

1. In Render, set `FRONTEND_URL` to your exact Vercel address, e.g.
   `https://your-app.vercel.app`, and save so the service redeploys.
2. This allows browser requests (CORS) and puts the right link on certificates.
3. Extra addresses (such as a custom domain) go in `CORS_ORIGINS`, comma separated.

## Step 7 - Add starter courses (optional)

Run the seed once **from your computer** against the cloud database and storage. Create
`backend/.env` with:

```ini
DATABASE_URL=...
STORAGE_BACKEND=s3
S3_ENDPOINT=...
S3_REGION=...
S3_BUCKET=learnsphere
S3_ACCESS_KEY_ID=...
S3_SECRET_ACCESS_KEY=...
```

```bash
cd backend
pip install -r requirements.txt
python seed.py --password "ChooseAStrongOne123"
```

Then **delete `backend/.env`** (or your local server will keep using the cloud database). The seed
creates instructor and student accounts with that password; change or delete them in the admin
dashboard when you no longer need them. Seeding works only while there are no courses.

## Step 8 - Check the live site

- [ ] Home page lists courses and shows their images
- [ ] Register a student, enroll, play and seek a video
- [ ] Download a study material
- [ ] Complete a course and download the certificate; open its verify link
- [ ] Upload a small video and a PDF as an instructor
- [ ] Log in as admin; refresh a page such as `/courses` (no 404)

## Alternative: one Docker container

The `Dockerfile` builds the frontend and serves it with the API (any container host):

```bash
docker build -t learnsphere .
docker run -p 8000:8000 --env-file production.env learnsphere
```

`production.env` needs `SECRET_KEY`, `DATABASE_URL`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`,
`STORAGE_BACKEND=s3` with the `S3_*` values, and `FRONTEND_URL` set to the container's public
address. Behind a reverse proxy also set `TRUSTED_PROXIES=1` and `PUBLIC_API_URL`.

## Environment variables (backend)

| Name | Required in production | Meaning |
|---|---|---|
| `APP_ENV` | yes (`production`) | Enables production safety checks |
| `SECRET_KEY` | yes, 32+ characters | Signs tokens and file links |
| `DATABASE_URL` | yes | PostgreSQL connection string |
| `FRONTEND_URL` | when hosted separately | CORS origin and certificate links |
| `CORS_ORIGINS` | no | More allowed origins |
| `PUBLIC_API_URL` | no | Public API address if auto-detection is wrong |
| `STORAGE_BACKEND` | yes (`s3`) on hosts with temporary disks | `local` or `s3` |
| `S3_ENDPOINT`, `S3_BUCKET`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY` | with `s3` | Object storage |
| `S3_REGION` | with `s3` | Defaults to `us-east-1` |
| `UPLOAD_DIR` | no | Folder for local storage |
| `MAX_UPLOAD_MB` | no (100) | Largest upload |
| `ADMIN_NAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD` | first start | Creates the first administrator |
| `TRUSTED_PROXIES` | behind a proxy | Usually `1` |
| `TOKEN_HOURS` | no (24) | How long a sign-in lasts |

## Troubleshooting

| Symptom | Check |
|---|---|
| Website says "Cannot reach the server" | Wait for Render to wake; check `API_URL` and that `FRONTEND_URL` matches exactly |
| Database connection fails | Use the **Session pooler** string; check password encoding |
| Upload fails with a storage error | Render logs show the reason; check S3 settings, bucket name and the 50 MB limit |
| Images or videos give 403 | Wrong keys or region, or the S3 protocol is disabled |
| A material opens instead of downloading | The storage provider ignored the download header; save it from the browser |
| `/courses` gives 404 on Vercel | Root Directory must be `frontend` |

## Provider documentation

- https://render.com/docs/blueprint-spec
- https://render.com/docs/free
- https://render.com/docs/python-version
- https://supabase.com/docs/guides/database/connecting-to-postgres
- https://supabase.com/docs/guides/storage/s3/authentication
- https://supabase.com/docs/guides/storage/uploads/file-limits
- https://supabase.com/docs/guides/platform/free-project-pausing
- https://vercel.com/docs/project-configuration/vercel-json
