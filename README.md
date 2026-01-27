# bdclimats-api

API Django + DRF avec PostgreSQL, lancée via Docker Compose. Elle expose un petit
catalogue d’indicateurs climatiques et un endpoint de calcul à partir de points
bruts.

## Stack
- Django 5 + Django REST Framework
- PostgreSQL 16 (Docker)
- Docker Compose

## Démarrage rapide
1) Copier `.env.example` vers `.env`
2) Renseigner au minimum `DJANGO_SECRET_KEY` et `POSTGRES_PASSWORD`
   - Générer une clé : `python -c "import secrets; print(secrets.token_urlsafe(64))"`
3) Build et démarrage :
   - `docker compose up -d --build`
4) Créer un superuser :
   - `docker compose run --rm web python bdclimats/manage.py createsuperuser`

## Accès
- API root : `http://localhost:8000/api/`
- Admin : `http://localhost:8000/admin/`
- Page d’aide : `http://localhost:8000/api/help/`

## Configuration (variables d’environnement)
Requises :
- `DJANGO_SECRET_KEY`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`

Optionnelles :
- `DJANGO_DEBUG` (1/0)
- `DJANGO_ALLOWED_HOSTS` (séparés par des virgules)

## Modèle de données (concepts)
- Dataset : métadonnées d’une source de points (inclut `source_url`)
- Indicator : code, nom, unité, fréquence, lié à un dataset
- ComputationRule : règle versionnée pour un indicator (opération + params)

## Endpoints API (principaux)
- `GET/POST /api/indicators/`
- `GET/POST /api/datasets/`
- `GET/POST /api/computation-rules/`
- `POST /api/indicators/{id}/compute/`
- `GET /health/`

L’API navigable DRF est activée sur `/api/`.

## Endpoint compute (en prose)
L’endpoint compute accepte une liste de points `{timestamp, value}`.

Deux modes d’entrée :
1) Points inline (défaut) : envoyer `values` dans le body.
2) Source dataset : `use_dataset=true` et `Dataset.source_url` défini.

Si `rule_version` est fourni, cette version est utilisée. Sinon, la dernière
règle active est appliquée. Les valeurs peuvent être `null` si `dropna=true`.

Exemple de payload (inline) :
```json
{
  "values": [
    {"timestamp": "2026-01-27T10:00:00Z", "value": 12.3},
    {"timestamp": "2026-01-27T11:00:00+01:00", "value": null}
  ],
  "rule_version": 2
}
```

Exemple de payload (dataset) :
```json
{"use_dataset": true, "rule_version": 2}
```

`source_url` doit retourner :
```json
{"values":[{"timestamp":"2026-01-27T10:00:00Z","value":12.3}]}
```

Notes :
- `timestamp` doit être ISO 8601 (timezone optionnelle).
- `value` peut être un nombre ou `null`.
- `file://...` autorisé uniquement en DEBUG.
- `http(s)://...` autorisé en dev et prod.

### Dataset local en HTTP (Docker)
Si l’API tourne dans Docker et que le JSON est sur l’hôte :
1) Lancer un serveur local à la racine du repo : `python -m http.server 8001`
2) Utiliser `http://host.docker.internal:8001/data/ds_test.json`

Si le serveur est lancé dans `data/`, l’URL devient :
`http://host.docker.internal:8001/ds_test.json`

## Logs et request_id
Chaque requête a un request_id unique.
- Ajouté dans le header `X-Request-ID`
- Affiché dans les logs sous la forme `[request_id] ...`

## Healthcheck
Endpoint simple pour vérifier que l’API répond :
- `GET /health/` -> `{"status":"ok"}`

## Tests (Docker, avec rapports)
Exécuter les tests (JUnit XML + log) :
- `python scripts/run_tests.py`

Tests + couverture (JUnit XML + coverage) :
- `python scripts/run_tests.py --coverage`

Organisation des tests :
- `backend/bdclimats/tests/api/tv/` : tests validation API
- `backend/bdclimats/tests/api/tu/` : tests unitaires API
- `backend/bdclimats/tests/catalog/tv/` : tests validation models
- `backend/bdclimats/tests/catalog/tu/` : tests unitaires models

Sorties :
- `reports/test-report.txt`
- `reports/TEST-*.xml`
- `reports/coverage.xml` (coverage uniquement)
- `reports/htmlcov/index.html` (rapport HTML)

## Lint / Format
- Format (Black) : `python -m black backend`
- Lint (Ruff) : `python -m ruff check backend`

Notes :
- Rebuild de l’image Docker après changement de dépendances :
  - `docker compose build`
- Config coverage : `backend/.coveragerc`

## Commandes utiles
- Stop : `docker compose down`
- Reset DB (supprime les données) : `docker compose down -v`
