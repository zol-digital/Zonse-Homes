---
description: "Use for implementation and bug-fix work anywhere in Zonse Homes. Requires baseline checks, incremental targeted tests, regression verification, environment-aware reporting, and explicit failure attribution."
applyTo: "**"
---

# Continuous Implementation and Verification

Apply this rule to implementation and bug-fix tasks throughout the repository. Verify continuously; do not defer all testing until the end.

## Before changing code

1. Inspect the existing implementation and relevant tests.
2. Run the relevant existing tests and checks to establish a baseline.
3. Record pre-existing failures separately from failures introduced by the change.
4. For backend work, check the actual Python version, installed project dependencies, and available PostgreSQL/Docker infrastructure before relying on them.

## During implementation

For each meaningful logical change:

1. Make the change.
2. Immediately run its focused tests or checks.
3. Inspect the results, investigate failures, and fix regressions caused by the change.
4. Rerun the affected checks successfully before proceeding.

Do not accumulate multiple untested changes. Preserve existing behavior and use the project's actual dependencies; do not weaken tests or substitute dependency versions to manufacture a pass.

## Completion checks

- Run the relevant full regression suite after implementation. For backend changes, run `python -m pytest -q` from `Zonse-backend`.
- Run other applicable checks, including import/startup checks, API endpoint tests, database integration tests, Alembic migration checks, Docker build and Docker Compose validation, environment/dependency compatibility checks, and `git diff --check`.
- Use an isolated test database for database or migration checks; do not run migrations against a shared or production database.
- For frontend-only or documentation-only changes, select checks appropriate to the changed surface. Do not claim backend or infrastructure verification when those checks were not relevant or were not run.

## Environment and failure reporting

For backend verification, the target environment is Python 3.11, PostgreSQL, SQLAlchemy, Alembic, Docker, Docker Compose, and FastAPI. Verify runtime behavior against the actual available environment; static inspection alone is not runtime verification.

If infrastructure is unavailable, run every remaining relevant check and state precisely what could not be tested, what is needed to finish verification, and any unresolved failures. For every failure, identify the component and whether it is pre-existing, environment-related, or introduced by the change. Investigate the cause, fix in-scope regressions, and rerun affected checks. Never suppress errors or use success-shaped fallbacks.

## Final report

Report:

- The outcome using one classification: **VERIFIED COMPLETE**, **PARTIALLY IMPLEMENTED**, **NOT IMPLEMENTED**, **NOT VERIFIED**, or **REQUIRES APPROVAL**.
- Tests and checks run during implementation and after implementation, with exact commands.
- The actual Python runtime version for backend work.
- Passed, failed, skipped, and collection-error counts, plus warnings, when a test runner reports them.
- Database and Docker verification results independently, and any outstanding environment limitations.

A passing pytest suite does not by itself verify PostgreSQL integration, Docker, deployment, or production configuration. Do not claim those categories as verified unless their checks actually ran.
