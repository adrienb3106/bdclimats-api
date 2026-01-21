# bdclimats-api

Backend Django + PostgreSQL, exécuté via Docker Compose.

## Prérequis
- Docker Desktop (avec `docker compose`)

## Configuration
1. Copier `.env.example` en `.env`
2. Renseigner au minimum `DJANGO_SECRET_KEY` et `POSTGRES_PASSWORD`

## Démarrage
- Lancer les services :
  - `docker compose up --build`
- Appliquer les migrations :
  - `docker compose run --rm web python bdclimats/manage.py migrate`

## Accès
- Application : http://localhost:8000

## Commandes utiles
- Créer un superuser :
  - `docker compose run --rm web python bdclimats/manage.py createsuperuser`
- Arrêter :
  - `docker compose down`
- Réinitialiser DB (supprime les données) :
  - `docker compose down -v`
