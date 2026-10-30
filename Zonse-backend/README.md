# Zonse Homes Backend

This backend provides the API foundation for the Zonse Homes marketplace.

## Supported runtime

The backend targets **Python 3.11**. The Docker image uses `python:3.11-slim`; the dependency versions are pinned in `requirements.txt`.

Runtime verification on 2026-10-30 was limited to Python 3.14.2 because Python 3.11 was not installed. The full test suite could not be collected with the declared SQLAlchemy 2.0.28 on Python 3.14.2. Docker Compose was available, but the Docker daemon was not, so image build and container checks were not run. Python 3.11/Docker instructions below are documented workflows, not claims that those runtime checks passed.

## Local Python development

From `Zonse-backend/`, create and activate a virtual environment, then install the pinned dependencies:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

On macOS/Linux, use `python3.11 -m venv .venv` and `source .venv/bin/activate`.

Copy the safe sample environment file from the repository root to `Zonse-backend/.env` and set local values as needed. Never commit `.env`. Start the API after applying database migrations:

```powershell
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

## Configuration

The service reads PostgreSQL settings from environment variables. Docker Compose passes database settings to both services and uses local-development defaults when a variable is unset. These defaults are not production credentials. Keep production credentials in your deployment's secret-management configuration.

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
pytest
```
