# bdclimats-api

Backend Django + PostgreSQL, exécuté via Docker Compose.

## Prérequis
- Docker Desktop (avec `docker compose`)

## Configuration
1. Copier `.env.example` en `.env`
2. Renseigner au minimum `DJANGO_SECRET_KEY` et `POSTGRES_PASSWORD`
Génerer une clé : `python -c "import secrets; print(secrets.token_urlsafe(64))"`

## Démarrage
- Lancer les services :
  - `docker compose up -d --build`
- Appliquer les migrations :
  - `docker compose run --rm web python bdclimats/manage.py migrate`

## Accès
- Application : http://localhost:8000

## Commandes utiles
- Créer un superuser :
  - `docker compose run --rm web python bdclimats/manage.py createsuperuser`
  Accès admin : http://localhost:8000/admin
- Arrêter :
  - `docker compose down`
- Réinitialiser DB (supprime les données) :
  - `docker compose down -v`

### Créer app Django
- Dans le container (depuis la racine Django, là où se trouve `manage.py`) :
`docker compose exec web sh -lc "cd /app/bdclimats && python manage.py startapp catalog"`
- Ajouter l'app à settings.py
- Vérifier que la configuration est OK: 
`docker compose exec web sh -lc "python /app/bdclimats/manage.py check"`
- Génerer la migration (après avoir modifié le code de l app):
`docker compose exec web sh -lc "python /app/bdclimats/manage.py makemigrations"`
- Appliquer la migration: 
`docker compose exec web sh -lc "python /app/bdclimats/manage.py migrate"`
