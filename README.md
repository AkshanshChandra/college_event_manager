# ADAPPT Competition Portal

A team-based technology competition platform: Google Form registration sync, domain-specific
problem statements, weekly hints, and a Round 1 submission pipeline (PPT/PDF + demo video) with
S3-backed storage and organizer administration.

## 1. Architecture

```
Google Form → Google Sheet → backend sync service → PostgreSQL
                                                         │
Participant/Admin ── React SPA ── REST API (FastAPI) ───┤
                                                         │
                                             S3 (files) ─┘ · SMTP/console (email)
```

- **Auth**: JWT access/refresh tokens. Participant accounts are created lazily — only once a
  registered email requests portal access — and activated via a one-time emailed link (never a
  plaintext password).
- **Authorization**: role-based (`participant` / `admin`) FastAPI dependencies on every route.
  Participants are further scoped to their own team via `team_id` ownership checks (see
  `app/services/submissions.py::assert_window_open_for_upload` and the `_assert_owns_storage_key`
  checks in `app/api/routes/uploads.py`).
- **Storage**: an abstract `StorageBackend` (`app/services/storage.py`) with two implementations —
  `LocalDiskStorage` for development and `S3Storage` for production — behind the same
  presigned-upload/download interface, so swapping backends requires only an env var change.
- **Email**: an abstract `EmailBackend` with a `console` backend (logs instead of sending, for
  local development) and an `smtp` backend.
- **Registration sync**: `app/services/registration_sync.py` normalizes rows from either a local
  CSV (development) or a live Google Sheet (`app/integrations/google_forms.py`) into the
  `registrations` table, with dedup-by-email and validation.

## 2. Tech Stack

- **Frontend**: React 19, Vite, Tailwind CSS v4, React Router, Axios, Lucide icons
- **Backend**: Python 3.13, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, `python-jose` + `passlib[bcrypt]`
- **Database**: PostgreSQL
- **Storage**: AWS S3 (production) / local disk (development)
- **Email**: SMTP (production) / console (development)

## 3. Folder Structure

```
backend/
  app/
    api/routes/       # FastAPI route modules
    auth/              # JWT + password hashing, route dependencies
    config/            # pydantic-settings
    database/          # SQLAlchemy engine/session
    integrations/       # Google Sheets client
    models/             # SQLAlchemy ORM models
    schemas/            # Pydantic request/response models
    services/           # business logic (accounts, submissions, storage, email, audit, sync)
    main.py
  alembic/               # migrations
  scripts/seed.py        # dev/demo seed data
  dev_data/registrations.csv
  tests/

frontend/
  src/
    components/ui/       # design-system primitives (Button, Card, Table, Dialog, …)
    contexts/             # Auth, Toast
    hooks/
    layouts/              # Public / Participant / Admin shells
    pages/public|participant|admin/
    services/             # axios API clients
    utils/
```

## 4. Environment Setup

### Backend

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit as needed
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env   # only needed if the frontend is deployed separately from the API
```

## 5. Database Setup

Requires a local PostgreSQL server (e.g. `brew install postgresql@17 && brew services start postgresql@17`).

```bash
createdb adappt
cd backend && source venv/bin/activate
alembic upgrade head
```

## 6. Google Integration Setup

For local development, leave `REGISTRATION_SYNC_MODE=csv` — the sync reads
`backend/dev_data/registrations.csv` (columns: Timestamp, Team Name, Team Leader Name, Team
Leader Email, Phone, College, Domain, Team Members).

For production:

1. Create a Google Cloud service account with the Sheets API enabled.
2. Share the Google Form's response spreadsheet with the service account's email (viewer access).
3. Set in `.env`:
   ```
   REGISTRATION_SYNC_MODE=google_sheets
   GOOGLE_SERVICE_ACCOUNT_JSON=/path/to/service-account.json
   GOOGLE_SHEET_ID=<spreadsheet id from its URL>
   GOOGLE_SHEET_WORKSHEET=Form Responses 1
   ```
4. Trigger a sync from Admin → Dashboard → "Sync Registrations", or `POST /api/admin/sync-registrations`.

## 7. AWS S3 Setup

For local development, leave `STORAGE_BACKEND=local` — uploads are written to
`backend/uploads/` and served through a signed-URL dev route that mirrors S3 presigned-URL
semantics (no AWS account needed).

For production:

1. Create a **private** S3 bucket (block all public access).
2. Create an IAM user/role with `s3:PutObject`, `s3:GetObject`, `s3:DeleteObject` scoped to that
   bucket only.
3. Set in `.env`:
   ```
   STORAGE_BACKEND=s3
   AWS_ACCESS_KEY_ID=...
   AWS_SECRET_ACCESS_KEY=...
   AWS_REGION=...
   S3_BUCKET_NAME=...
   ```
4. Configure CORS on the bucket to allow `PUT` from the frontend's origin.

## 8. Email Setup

For local development, leave `EMAIL_BACKEND=console` — activation and submission-confirmation
emails are logged to the backend's stdout instead of being sent.

For production, set `EMAIL_BACKEND=smtp` and the `SMTP_HOST` / `SMTP_PORT` / `SMTP_USERNAME` /
`SMTP_PASSWORD` / `EMAIL_FROM_ADDRESS` vars. `app/services/email.py` isolates all email-sending
behind `EmailBackend`, so swapping to a provider SDK (SES, SendGrid, Postmark) later only touches
that one file.

## 9. Local Development

```bash
# Terminal 1 — backend
cd backend && source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
npm run dev
```

The Vite dev server proxies `/api` to `http://localhost:8000` (see `frontend/vite.config.js`), so
the frontend can be opened directly at `http://localhost:5173`.

## 10. Migrations

```bash
cd backend && source venv/bin/activate
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

## 11. Seed Data

```bash
cd backend && source venv/bin/activate
python -m scripts.seed
```

Creates (all clearly marked `[SAMPLE]` where user-facing): an admin account
(`admin@adappt.dev` / `ChangeMe123!` — **change this immediately**), three domains
(Healthcare, Fintech, Sustainability) with sample problem statements, two sample hints, Round 1
competition settings, and syncs the bundled `dev_data/registrations.csv`.

## 12. Tests

```bash
cd backend && source venv/bin/activate
createdb adappt_test   # once
pytest
```

Covers: activation/login flow, unregistered-email rejection, cross-team data isolation,
domain-scoped problem statement/hint visibility, submission deadline enforcement, file
type/size validation, and admin-only route protection.

## 13. Production Deployment

- **Frontend**: `npm run build` in `frontend/`, upload `dist/` to an S3 bucket served via
  CloudFront.
- **Backend**: containerize with Docker and run on EC2 (or any container host) behind a reverse
  proxy terminating TLS. Set all secrets via environment variables — never bake them into the
  image.
- **Database**: a managed PostgreSQL instance (e.g. RDS).
- **Files**: the S3 bucket configured in step 7.
- Run `alembic upgrade head` as part of the deploy step, before starting new backend instances.

## 14. Security Considerations

- Passwords are hashed with bcrypt (`passlib`); plaintext passwords are never stored or emailed.
- Portal accounts are activated via a single-use, expiring, hashed token — never a permanent
  emailed password.
- All admin routes require `role=admin`; all participant routes require `role=participant` and a
  bound `team_id`. Cross-team access to problem statements, hints, and submissions is enforced
  server-side, not just hidden in the UI.
- Upload deadlines and file type/size limits are enforced server-side
  (`app/services/submissions.py`), not just disabled in the UI.
- S3 objects are private; downloads go through short-lived presigned URLs generated only by
  authorized routes (admin, or the owning participant).
- Rate limiting (`slowapi`) is applied to `/auth/login` and `/auth/request-access` to slow down
  credential/enumeration attempts.
- Admin-impacting actions (settings changes, publishing content, downloading submissions, syncing
  registrations) are recorded in `audit_logs`.

## 15. Troubleshooting

- **`alembic upgrade head` fails with an enum error**: drop and recreate the dev database — this
  usually means migrations were generated against a stale model definition.
- **Uploads 404 in local dev**: confirm `STORAGE_BACKEND=local` and that the backend process has
  write access to `LOCAL_STORAGE_DIR`.
- **"We could not find this email…" on Request Access**: the email must exist in the
  `registrations` table — run a sync first (Admin → Dashboard → Sync Registrations, or seed the
  dev CSV).
- **CORS errors in the browser**: ensure `CORS_ORIGINS` in the backend `.env` includes the exact
  frontend origin you're loading from.
