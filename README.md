# bdclimats-api

Backend Django + PostgreSQL, run with Docker Compose.

## Prerequisites
- Docker Desktop (with `docker compose`)

## Configuration
1. Copy `.env.example` to `.env`
2. Set at least `DJANGO_SECRET_KEY` and `POSTGRES_PASSWORD`
   - Generate a key:
     `python -c "import secrets; print(secrets.token_urlsafe(64))"`

## Start
- Build and start services:
  - `docker compose up -d --build`

## Access
- API: http://localhost:8000
- Admin: http://localhost:8000/admin

## Compute endpoint (data input)
The compute endpoint accepts points in **ISO 8601** with a `value` (nullable).

Two input modes are supported:

1) **Inline data (default)**  
Send points directly in the request body:
```json
{"values":[{"timestamp":"2026-01-27T10:00:00Z","value":12.3},{"timestamp":"2026-01-27T11:00:00+01:00","value":null}]}
```

2) **Dataset source URL**  
Set `use_dataset=true` and define `Dataset.source_url`:
- `file://...` **only in DEBUG** (dev mode)
- `http(s)://...` in dev and prod

The URL must return JSON like:
```json
{"values":[{"timestamp":"2026-01-27T10:00:00Z","value":12.3}]}
```

Notes:
- `timestamp` must be ISO 8601 (timezone optional)
- `value` can be a number or `null`

### Local HTTP dataset (Docker)
If the API runs in Docker and your JSON file is served from the host:
- Start a local server at the repo root:
  - `python -m http.server 8001`
- Use this URL in `Dataset.source_url`:
  - `http://host.docker.internal:8001/data/ds_test.json`

If you start the server inside `data/`, the URL becomes:
- `http://host.docker.internal:8001/ds_test.json`

## Useful commands
- Create a superuser:
  - `docker compose run --rm web python bdclimats/manage.py createsuperuser`
- Stop:
  - `docker compose down`
- Reset DB (removes data):
  - `docker compose down -v`

## Tests (with reports + coverage)
Run tests (JUnit XML + log):
- `python scripts/run_tests.py`

Run tests + coverage (JUnit XML + log + coverage.xml):
- `python scripts/run_tests.py --coverage`

Outputs:
- `reports/test-report.txt`
- `reports/TEST-*.xml`
- `reports/coverage.xml` (coverage run only)

Notes:
- The Docker image must be rebuilt after dependency changes:
  - `docker compose build`
- JUnit XML is produced by a custom Django test runner:
  - `bdclimats/test_runner.py`
- Coverage configuration is in:
  - `backend/.coveragerc`

## Django app creation (inside container)
- From the Django root (`/app/bdclimats`):
  - `docker compose exec web sh -lc "cd /app/bdclimats && python manage.py startapp catalog"`
- Add the app to `settings.py`
- Check configuration:
  - `docker compose exec web sh -lc "cd /app/bdclimats && python manage.py check"`
- Create migrations:
  - `docker compose exec web sh -lc "cd /app/bdclimats && python manage.py makemigrations"`
- Apply migrations:
  - `docker compose exec web sh -lc "cd /app/bdclimats && python manage.py migrate"`
