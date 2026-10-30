# Zonse Homes Backend

This backend provides the API foundation for the Zonse Homes marketplace.

## Supported runtime

The backend targets **Python 3.11**. The Docker image uses `python:3.11-slim`; the dependency versions are pinned in `requirements.txt`.

Runtime verification on 2026-10-30 used Python 3.11.9 in `Zonse-backend/.venv` with the declared dependencies. The complete pytest suite passed. The Docker image built, and a dedicated isolated Docker Compose PostgreSQL/backend project reached healthy status; API health, readiness, OpenAPI, initial migration, and Alembic schema-drift checks passed. The unrelated existing containers and volumes were not modified.

## Local Python development

From `Zonse-backend/`, create and activate a virtual environment, then install the pinned dependencies:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

On macOS/Linux, use `python3.11 -m venv .venv` and `source .venv/bin/activate`.

Copy the safe sample environment file from the repository root to `Zonse-backend/.env` and set local values as needed. Never commit `.env`. Docker Compose reads this file for Compose variable substitution. A Python process started directly does not load `.env` automatically; set its configuration in the shell. For example, with the Compose local-development defaults and a database started by Compose:

```powershell
Copy-Item ..\.env.example .env
docker compose up -d db
$env:POSTGRES_SERVER = "localhost"
$env:POSTGRES_PORT = "5432"
$env:POSTGRES_USER = "zonse_user"
$env:POSTGRES_PASSWORD = "zonse_password"
$env:POSTGRES_DB = "zonse_db"
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

The project owner reviewed historical `.env` path entries as part of the transition from a personal GitHub repository to a work-account repository and confirmed that no credentials were exposed. No credential rotation was performed or requested, and this project does not rewrite Git history.

## Configuration

The service reads `PROJECT_NAME`, `API_V1_STR`, `POSTGRES_SERVER`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, and `POSTGRES_PORT` from the process environment. `SQLALCHEMY_DATABASE_URI` may be provided to override the assembled PostgreSQL URL. Session settings are `ENVIRONMENT`, `SESSION_COOKIE_NAME`, `SESSION_LIFETIME_SECONDS`, `SESSION_COOKIE_SAMESITE`, and comma-separated `SESSION_CSRF_TRUSTED_ORIGINS`. `SESSION_COOKIE_SECURE` can explicitly enable Secure cookies outside production; production always requires it to be enabled. `SameSite=None` is rejected unless Secure is enabled. In production, database connection settings must be explicitly supplied; the built-in localhost/PostgreSQL defaults and known sample passwords are rejected. An explicit production `SQLALCHEMY_DATABASE_URI` must contain a non-placeholder password. The root `.env.example` lists development values and placeholders. Docker Compose passes these session settings to the API service. Keep production credentials in your deployment's secret-management configuration and set `ENVIRONMENT=production`.

## API structure

The application is assembled in `app/main.py`. It registers exception handlers and includes the central router in `app/api/router.py`; that router mounts the v1 router under the configured `/api/v1` prefix. Versioned endpoint modules live under `app/api/v1/endpoints/`. Liveness and readiness are provided by `health.py`.

Property request and response schemas are defined in `app/schemas/property.py`. There are currently no property HTTP endpoints; this organization prepares schemas without adding listing behavior or changing the database model.

Registration uses the reusable credential service in `app/security/credentials.py`. It normalizes email addresses, validates the Task 2C password policy, stores Argon2id hashes, sets accounts to `pending_verification`, blocks duplicate case-variant emails, and never exposes password hashes in public responses. `POST /api/v1/auth/login` reuses that credential-authentication service, creates a new opaque server-side session only after eligible authentication succeeds, and returns safe user information. `POST /api/v1/auth/logout` revokes the cookie's session and clears the cookie; repeated logout is safe. `GET /api/v1/auth/me` returns the authenticated user and authoritative assigned roles.

## Profiles, email verification, and password recovery

`GET /api/v1/users/me` and `PATCH /api/v1/users/me` require an authenticated session. The private profile response includes the account email, display name (`full_name`), phone number, verification timestamps, account status, and timestamps; it excludes credentials, role assignments, and private business-verification documents. Only `full_name` and `phone_number` are editable. They are trimmed and length-validated; either can be cleared with `null`. Changing or clearing a phone number clears `phone_verified_at`. Email, roles, account status, password data, and verification state are not profile-editable. There is no public advertiser-profile endpoint, so private contact details and verification documents are not exposed as public profile information.

Email verification uses `POST /api/v1/auth/email-verification/request` and `/confirm`. The request returns a generic `202` response for known and unknown addresses when delivery is configured. A pending account becomes active after verification only if it is still enabled; suspended and disabled accounts retain their status. Password recovery uses `POST /api/v1/auth/password-recovery/request` and `/confirm`. Requests use the same generic response. Confirmation applies the existing Task 2C password policy and Argon2id service, consumes the token in the same transaction as the password change, invalidates other outstanding recovery tokens, and revokes every server-side session. It does not sign the user in.

Both workflows generate random, purpose-bound tokens and persist only SHA-256 digests. Email-verification tokens expire after 24 hours; recovery tokens expire after one hour. Tokens are single-use, previous outstanding tokens are superseded when a new one is issued, and a database-backed 60-second per-account cooldown limits token generation. Raw tokens are sent only to the delivery adapter; they are not returned in API responses or logged. Confirmation failures have a generic response.

No email provider has been selected or configured. The default `get_email_delivery()` dependency is deliberately unavailable and both request endpoints return the same `503` without looking up the submitted address or creating a token. The included `MemoryEmailDelivery` is for automated tests only and refuses to initialize when `ENVIRONMENT=production`. A provider can be integrated by implementing the `EmailDelivery` contract and binding it to that dependency; message bodies are kept in `app/security/email_templates.py`. Delivery is scheduled as an in-process background task after the token transaction commits, and delivery failures produce a sanitized server log entry. This is not a durable queue and does not claim delivery when no provider is configured. Provider selection, credentials/secret management, and production-grade durable delivery remain owner decisions. No IP-based or general distributed request rate limiter is implemented; the per-account database cooldown is enforced across API instances sharing the database.

## Browser sessions and authorization

Session tokens are generated from 32 cryptographically random bytes and delivered only in the configurable `zonse_session` cookie. PostgreSQL stores only the token's SHA-256 digest in `user_sessions`; the raw token is never persisted or returned in response JSON. Sessions have an absolute configurable lifetime (24 hours by default), creation and expiration timestamps, and a revocation timestamp. Each successful login rotates and revokes any existing presented session when its cookie is present. Logout revokes the current token, and `revoke_all_user_sessions()` supports server-side revocation of every session for a user. Sessions are not refreshed on activity; expiration is absolute.

The cookie is HttpOnly, scoped to `/`, and uses `SameSite=Lax` by default. It is Secure automatically when `ENVIRONMENT=production`; insecure production settings and `SameSite=None` without Secure fail configuration at startup. A frontend on a different site must explicitly use `SESSION_COOKIE_SAMESITE=None` (with Secure enabled) to send cookies cross-site. The CSRF policy combines SameSite with exact origin validation on unsafe methods: when `Origin` or `Referer` is present, it must match the request origin or an explicitly configured `SESSION_CSRF_TRUSTED_ORIGINS` entry. Cross-origin `Origin` and `Referer` values are rejected. An unsafe request carrying a session cookie is also rejected if both headers are absent; unauthenticated requests without them remain supported for non-browser clients. Configure trusted frontend origins explicitly when the browser app is hosted on another origin. Frontends using cross-origin cookies must also use credentialed requests and the corresponding CORS policy; CORS is not configured by this task.

Reusable session and authorization dependencies are in `app/security/sessions.py` and `app/security/authorization.py`. Authentication checks server-side session digest, expiry, revocation, current account status, activation, and verified email. Role guards query `user_roles` on every request and allow access when any requested role is assigned; the legacy `users.role` field is not authoritative. Public registration cannot request roles or assign admin. No admin bootstrap or admin self-service endpoint is provided. Before provisioning is implemented, the owner must approve who may assign admin, identity/approval controls, audit requirements, emergency revocation, and the bootstrap process.

Role grants do not establish property ownership. The property-scoped dependency checks `Property.owner_id` directly and returns the same not-found response for absent and non-owned properties. There are no property HTTP endpoints or property-manager/agent assignment tables in this task, so those roles do not confer access to listings. Any future scoped agent/property-manager access must use an explicitly approved assignment model. No distributed login rate limiting is implemented or claimed.

Application errors use this JSON shape:

```json
{
  "error": {
    "code": "not_found",
    "message": "Resource not found"
  }
}
```

Validation errors return `422` with `error.code` set to `validation_error` and sanitized field locations/messages. Database constraint conflicts return `409`; database operation failures return a generic `503`; unexpected errors return a generic `500`. Internal exception details and submitted values are not included in error responses. FastAPI's OpenAPI and request-validation behavior remains enabled.

## Database migrations

Alembic is the version-controlled schema migration system. The application does not create database tables automatically at startup. Apply migrations before starting the API.

From `Zonse-backend/` with the configured database environment:

```powershell
# Create a migration after changing SQLAlchemy models; review the generated file.
python -m alembic revision --autogenerate -m "describe schema change"

# Inspect revisions and the database's current revision.
python -m alembic history
python -m alembic current

# Apply all pending migrations.
python -m alembic upgrade head
```

Downgrades can remove schema objects and data. Review the migration's `downgrade()` first, take an appropriate backup, and confirm the target database before running:

```powershell
python -m alembic downgrade -1
```

Do not run a downgrade against a production database without explicit approval.

If a database already contains application tables, do not apply the initial migration blindly: first compare its schema and migration state, then plan an approved Alembic baseline.

## Identity data model

The additive identity foundation is introduced by Alembic revision `20261030_0002`; the initial migration remains unchanged. It adds user account status, verification timestamps, optional phone number, a nullable unique canonical-email field, and update timestamps. Existing email values are not normalized or copied into `canonical_email` because legacy data has not been audited for collisions. New account-writing code must set and validate the canonical value before it treats that column as a login identifier. Revision `20261030_0003` adds `user_sessions` with a cascading user foreign key, unique token digest, creation/expiry/revocation timestamps, an expiry constraint, and a user/expiry index. Revision `20261030_0004` adds digest-only `user_action_tokens` for email verification and password recovery; its downgrade removes only that token table and index.

Legacy role values remain in `users.role` for compatibility and are not automatically copied into the new `user_roles` association. Existing users are conservatively assigned `pending_verification`, except legacy rows explicitly marked inactive are assigned `disabled`. This avoids activating accounts without email verification. The old role field and `is_active` are retained; no authentication endpoints are implemented by this schema migration.

The schema also provides organizations, revocable organization memberships, organization-level business verification state, submissions, private document references, and review history. Verification documents are represented only by opaque storage references; document upload and public document APIs are not implemented. Certified Business status concerns business identity and registration review only, not property ownership or listing accuracy.

The revision downgrade drops these new identity and organization tables and columns, including any data written to them after upgrade. Back up and review the target before any downgrade; never downgrade a database containing identity data without explicit approval.

## Password security foundation

New password hashes use `pwdlib` with Argon2id (`time_cost=3`, `memory_cost=65536` KiB, `parallelism=4`, 32-byte output, and a 16-byte random salt). Verification accepts only Argon2id hashes whose resource parameters do not exceed those configured limits; unsupported, malformed, or over-limit hashes fail closed. The service is in `app/security/passwords.py`; use `hash_password()` for new credentials, `verify_password()` to verify, and `verify_password_and_update()` to obtain a replacement only after successful verification. `password_hash_needs_rehash()` checks the configured algorithm and parameters, but a true result for an unsupported format does not mean that format can be verified or safely upgraded.

The policy requires at least 12 Unicode code points and caps input at 1024 UTF-8 bytes. Unicode is encoded as UTF-8 without normalization; inputs are never truncated. No character-class composition rule is imposed. Verification applies the same length and encoding checks as new-password validation. Public user responses use `UserResponse` and omit `hashed_password` and internal canonical-email data.

For a future service, call `hash_password(password)` when storing a new credential. Use `verify_password(candidate, stored_hash)` for a check, or `verify_password_and_update(candidate, stored_hash)` when the caller can persist an optional replacement hash in the same authenticated workflow. Never update a stored hash based only on `password_hash_needs_rehash()`; that helper does not authenticate the user.

No prior hashing or password-verification implementation was found in the repository, and the actual legacy database hash formats have not been audited. Verification therefore accepts only well-formed Argon2id hashes and fails closed for unknown or malformed formats. Do not overwrite or migrate existing password values without an owner-approved data audit. The eventual login flow must provide a safe password-reset path for accounts with unrecognized hashes.

## Docker development

Build the production-safe image from `Zonse-backend/`:

```powershell
docker build -t zonse-homes-api .
```

The image includes only the application, Alembic files, and dependency manifest. `.dockerignore` excludes local environment files, Git metadata, virtual environments, caches, tests, and local uploads. The image's default command runs Uvicorn without `--reload`.

Docker Compose is the development workflow (including source bind-mounting and Uvicorn reload). It retains PostgreSQL's named data volume and the persistent development upload volume. Start the database, apply migrations explicitly, then start the API:

```powershell
docker compose up -d db
docker compose run --rm web alembic upgrade head
docker compose up -d web
```

For an already-running backend container, the equivalent migration command is `docker compose exec web alembic upgrade head`. Run migrations as an explicit deployment step before starting/restarting application instances; application startup does not run migrations.

Stop development services without deleting volumes:

```powershell
docker compose down
```

Do not use `docker compose down --volumes` if you need to preserve local database or upload data.

## Health checks and troubleshooting

- Liveness: `GET http://localhost:8000/api/v1/health`
- Readiness (includes a PostgreSQL connectivity check): `GET http://localhost:8000/api/v1/ready`

On PowerShell, check them with `Invoke-RestMethod http://localhost:8000/api/v1/health` and `Invoke-RestMethod http://localhost:8000/api/v1/ready`. Readiness returns HTTP 503 until the database is reachable.

If Compose services do not become healthy, inspect `docker compose ps` and `docker compose logs web db`. Check that Docker Desktop/the Docker daemon is running, the configured port is available, and the same local database settings are passed to both services. For Python issues, confirm `python --version` reports 3.11 and reinstall from `requirements.txt` inside the active virtual environment.

## Tests

Run the automated checks with:

```bash
python -m pytest -q
```

Use the approved Python 3.11 environment for backend checks. Focused session and authorization coverage is in `tests/test_sessions_auth.py`; identity and migration coverage remains in `tests/test_identity_models.py` and `tests/test_migrations.py`. Database migration verification must use an isolated database, never a shared or production database.
