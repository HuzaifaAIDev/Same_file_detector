# Universal File Comparer

A document similarity & comparison platform: upload a set of BASE files and a
set of COMPARE files, and get a fuzzy-text-similarity score + EXACT / SIMILAR
/ DIFFERENT classification for each comparison file, powered by OCR + text
extraction across PDF, DOCX, XLSX, PPTX, TXT, CSV, JSON, and image formats.

This is v2.0 of the original single-file prototype (`api.py` + `detector.py`).
The extraction/similarity engine's behavior is unchanged; everything around
it — architecture, security, auth, persistence, and UI — has been rebuilt.

## What changed from v1, and why

| Area | v1 | v2 |
|---|---|---|
| File input | Server-side file **paths** supplied by the client (arbitrary file read risk) | Real file **upload** (multipart), validated by extension/size |
| Auth | None | JWT register/login/refresh, bcrypt password hashing, **email OTP verification** |
| Registration | — | Two-step: submit details → verify 6-digit email OTP → account created |
| Password reset | — | Email OTP → short-lived reset token → new password |
| Admin / test accounts | — | Auto-provisioned from `.env` on startup (no manual script) |
| Roles | — | `user` / `admin`, with admin-only user management endpoints |
| Persistence | None (results returned once, then gone) | SQLite (dev) / PostgreSQL (prod) via SQLAlchemy; comparison history per user |
| Architecture | 2 files | Layered: `api / services / repositories / models / schemas / core` |
| Logging | `print()` / `traceback.print_exc()` | Rotating file logs: app, error, security, access |
| Security | None | Security headers, rate limiting, input validation, sandboxed legacy path mode |
| Errors | Mixed HTTPException usage | Centralized exception hierarchy, no stack traces leaked to clients |
| Frontend | Bare HTML form | Dark-mode dashboard: OTP entry, password strength meter, drag-and-drop upload, toasts, admin panel |
| Tests | 1 manual script (`test.py`) | `pytest` suite (auth incl. OTP flows, compare, health) run in CI |
| Deployment | Manual `python api.py` | Dockerfile + docker-compose (app + Postgres), `.env.example` |

**The old path-based `/compare` behavior still exists**, at
`POST /api/v1/compare/paths`, but is **disabled by default** (see
`ENABLE_LOCAL_PATH_COMPARE` below) because letting a client name arbitrary
server file paths is a real vulnerability. If you enable it, paths are
sandboxed to `ALLOWED_LOCAL_ROOT`.

> **Note on the frontend stack:** this project's UI is server-rendered
> Jinja2 + vanilla JS + CSS (not React). All auth/OTP/admin features below
> are built against that stack to stay consistent with the rest of the app.

### Explicitly out of scope for this pass

Alembic migrations (schema changes here go through SQLAlchemy's
`create_all`, same as before — see "Database changes" below), PDF/Excel/CSV
report export, semantic embeddings/NER, and a full multi-cloud IaC setup.
None of those are in this version. Happy to build out whichever of these
matters most to you next.

## Architecture

```
backend/
  app/
    api/v1/        # routers: auth, admin, compare, health
    core/           # config, logging, security (JWT/bcrypt/OTP), validators, seed, exceptions
    database/       # SQLAlchemy engine/session
    middleware/      # security headers, rate limiting
    models/          # User, OTPVerification, ComparisonJob, ComparisonResult
    repositories/    # DB access, one class per aggregate
    schemas/         # Pydantic request/response models
    services/        # extraction_service, comparison_service, otp_service, email_service
    utils/           # upload validation, safe-path handling
    main.py          # app factory, middleware wiring, startup seeding, exception handlers
  tests/             # pytest suite
  main.py            # dev entrypoint (python main.py)
  requirements.txt
frontend/
  templates/index.html   # login / register / OTP / forgot-password / admin panel
  static/css/style.css
  static/js/app.js
```

## Running locally (Windows, macOS, Linux)

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
copy .env.example .env       # or: cp .env.example .env
# edit .env and set a real SECRET_KEY

python main.py
```

Then open **http://localhost:20285**. API docs are at
**http://localhost:20285/api/docs** (Swagger) and **/api/redoc**.

OCR requires [Tesseract](https://github.com/tesseract-ocr/tesseract) to be
installed separately and pointed to by `TESSERACT_CMD` in `.env` (defaults to
the standard Windows install path). Without it, image/scanned-PDF OCR is
skipped gracefully — text-based formats still work.

### Running tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest -q
```

## Email OTP flows

**Registration:** submit first/last name, username, email, and password →
a 6-digit numeric code is emailed → the user enters it within 5 minutes (max
5 attempts) → the account is created only after that succeeds. Requesting a
new code invalidates the previous one; resend is rate-limited to once every
60 seconds.

**Forgot password:** enter your email → 6-digit code emailed (same rules as
above) → verifying it returns a short-lived (10-minute) reset token → submit
a new password (with confirmation + strength validation) using that token.

**Local development without a real mail server:** if `SMTP_HOST` is left
blank in `.env` (the default), OTP codes are written to
`backend/logs/app.log` instead of being emailed, so the whole flow is
testable out of the box. Set `SMTP_HOST`/`SMTP_USERNAME`/`SMTP_PASSWORD`/etc.
to send real email.

## Admin login & test users

On startup, the app checks whether the admin account (and each configured
test user) already exists by email/username, and creates any that are
missing — this replaces the old `create_admin.py` script. Nothing is ever
duplicated; re-running the app is always safe.

Configure these in `.env` (see `.env.example` for the full list):

- `ADMIN_EMAIL` / `ADMIN_USERNAME` / `ADMIN_PASSWORD` / etc. — one admin account.
- `TEST_USER_1_EMAIL` ... `TEST_USER_5_EMAIL` (+ names/usernames) plus one
  shared `TEST_USERS_PASSWORD` — up to 5 pre-verified test accounts. Leave a
  test user's fields blank to skip creating it.

All seeded accounts are created already **verified and active**, so you can
sign in immediately without going through the OTP flow.

## Roles & admin panel

Every user has a `role` of `user` or `admin`. Admins get an **Admin** button
in the top bar (hidden for regular users) leading to a user-management panel
where they can suspend, reactivate, or permanently delete any other account.
Regular users never see admin-only UI or can call admin-only endpoints
(enforced server-side via `get_current_admin`, not just hidden in the UI).

## Database changes

This release adds an `otp_verifications` table and new columns on `users`
(`username`, `first_name`, `last_name` replacing the old single `full_name`
column). There's no Alembic migration chain in this project — schema is
created via `Base.metadata.create_all()` on startup (see `init_db()` in
`app/database/session.py`), same approach as before.

- **Fresh install / dev SQLite:** nothing to do — the new tables/columns are
  created automatically on first run.
- **Existing Postgres database with real user data:** `create_all()` will
  add the new `otp_verifications` table automatically, but it **will not**
  add the new `NOT NULL` columns (`username`, `first_name`, `last_name`) to
  an existing `users` table, and will not backfill them from the old
  `full_name` column. Run something like this once, by hand, before
  deploying this version:

  ```sql
  ALTER TABLE users ADD COLUMN username VARCHAR(50);
  ALTER TABLE users ADD COLUMN first_name VARCHAR(150);
  ALTER TABLE users ADD COLUMN last_name VARCHAR(150);

  -- backfill from the old full_name column (adjust the split however fits your data)
  UPDATE users SET
    first_name = COALESCE(split_part(full_name, ' ', 1), ''),
    last_name  = COALESCE(NULLIF(split_part(full_name, ' ', 2), ''), ''),
    username   = lower(split_part(email, '@', 1)) || '_' || substr(id, 1, 6);

  ALTER TABLE users ALTER COLUMN username SET NOT NULL;
  ALTER TABLE users ALTER COLUMN first_name SET NOT NULL;
  ALTER TABLE users ALTER COLUMN last_name SET NOT NULL;
  ALTER TABLE users ADD CONSTRAINT users_username_key UNIQUE (username);

  ALTER TABLE users DROP COLUMN full_name;
  ```

  Adjust the backfill logic to your actual data before running it in
  production — this is a starting point, not a guarantee-safe script.

## Running with Docker

```bash
export SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
export POSTGRES_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))")
docker compose up --build
```

This starts the API (port 20285) backed by PostgreSQL. For a single-container
run against SQLite instead:

```bash
docker build -t file-comparer .
docker run -p 20285:20285 -e SECRET_KEY=changeme file-comparer
```

## Configuration (environment variables)

See `backend/.env.example` for the full list with defaults. Key ones:

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | JWT signing key — **must** be set to a real secret in production |
| `DATABASE_URL` | `sqlite:///./app_data.db` (dev) or `postgresql+psycopg2://...` (prod) |
| `ENABLE_LOCAL_PATH_COMPARE` | `false` by default; enables the legacy path-based compare endpoint |
| `MAX_UPLOAD_SIZE_MB` / `MAX_FILES_PER_REQUEST` | Upload limits |
| `RATE_LIMIT_REQUESTS` / `RATE_LIMIT_WINDOW_SECONDS` | Per-IP rate limiting |
| `TESSERACT_CMD` | Path to the tesseract binary |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USERNAME` / `SMTP_PASSWORD` / `SMTP_FROM` | Outbound mail for OTP codes; leave `SMTP_HOST` blank to log codes instead of emailing them |
| `OTP_EXPIRE_MINUTES` / `OTP_RESEND_SECONDS` / `OTP_MAX_ATTEMPTS` | OTP expiry, resend cooldown, and max verify attempts |
| `ADMIN_EMAIL` / `ADMIN_USERNAME` / `ADMIN_PASSWORD` / etc. | Auto-provisioned admin account |
| `TEST_USER_1_EMAIL` ... `TEST_USER_5_EMAIL` / `TEST_USERS_PASSWORD` | Auto-provisioned test accounts |

## API overview

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/api/v1/auth/register` | – | Submit registration details, sends email OTP |
| POST | `/api/v1/auth/register/verify` | – | Verify OTP, creates the account |
| POST | `/api/v1/auth/register/resend` | – | Resend registration OTP (60s cooldown) |
| POST | `/api/v1/auth/login` | – | Get access + refresh tokens (requires verified + active) |
| POST | `/api/v1/auth/refresh` | – | Exchange a refresh token for a new access token |
| GET | `/api/v1/auth/me` | ✓ | Current user profile |
| POST | `/api/v1/auth/change-password` | ✓ | Change password (while logged in) |
| POST | `/api/v1/auth/forgot-password` | – | Send password-reset OTP |
| POST | `/api/v1/auth/forgot-password/resend` | – | Resend reset OTP (60s cooldown) |
| POST | `/api/v1/auth/forgot-password/verify` | – | Verify reset OTP, returns a short-lived reset token |
| POST | `/api/v1/auth/reset-password` | – | Set a new password using a reset token |
| GET | `/api/v1/admin/users` | ✓ admin | List all users |
| POST | `/api/v1/admin/users/{id}/suspend` | ✓ admin | Deactivate a user |
| POST | `/api/v1/admin/users/{id}/activate` | ✓ admin | Reactivate a user |
| DELETE | `/api/v1/admin/users/{id}` | ✓ admin | Permanently delete a user |
| POST | `/api/v1/compare` | ✓ | Upload BASE + COMPARE files, run comparison |
| POST | `/api/v1/compare/paths` | ✓ | Legacy path-based compare (disabled by default) |
| GET | `/api/v1/compare/history` | ✓ | List past comparison jobs |
| GET | `/api/v1/compare/history/{id}` | ✓ | Full results for one job |
| GET | `/api/v1/health` | – | Liveness/DB health check |

## Deploying

The Docker image is a standard Python/Uvicorn container and runs as-is on
Railway, Render, AWS (ECS/App Runner), Azure Container Apps, or any host that
accepts a Dockerfile — point `DATABASE_URL` at a managed Postgres instance and
set `SECRET_KEY`/`CORS_ORIGINS` for your domain. For production, run behind a
reverse proxy (nginx/Caddy/your platform's LB) that terminates TLS.

## License

MIT — see `LICENSE`.
