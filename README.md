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

## Useful commands
- Create a superuser:
  - `docker compose run --rm web python bdclimats/manage.py createsuperuser`
- Stop:
  - `docker compose down`
- Reset DB (removes data):
  - `docker compose down -v`

## Tests (with reports)
We provide a simple test runner that generates:
- a readable log: `reports/test-report.txt`
- JUnit XML files: `reports/TEST-*.xml`

Run tests:
  - `python .\scripts\run_tests.py`

Notes:
- The Docker image must be rebuilt after dependency changes:
  - `docker compose build`
- The JUnit XML is produced by a custom Django test runner:
  - `bdclimats/test_runner.py`

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
