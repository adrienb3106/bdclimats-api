# Tests (pytest) — Template & conventions

Ce dossier contient les tests du projet, organisés par domaine :
- `api/` : tests d'API (DRF)
- `catalog/` : tests modèles/ORM

## Template d'un test API
Structure recommandée (Arrange / Act / Assert) :

1) **Arrange**
   - Créer les objets nécessaires (Dataset, Indicator, ComputationRule)
   - Préparer les données d'entrée

2) **Act**
   - Appeler l'endpoint via `APIClient`

3) **Assert**
   - Vérifier le `status_code`
   - Vérifier les champs clés de la réponse

Exemple (pseudo-code) :
```
# Arrange
dataset = Dataset.objects.create(...)
indicator = Indicator.objects.create(...)
ComputationRule.objects.create(...)

# Act
response = api_client.post("/api/indicators/<id>/compute/", {...})

# Assert
assert response.status_code == 200
assert response.data["result"] == ...
```

## Template d'un test model
Structure recommandée :
1) Créer des objets valides
2) Appeler `full_clean()` si on teste la validation
3) Vérifier contraintes/erreurs via `pytest.raises`

Exemple (pseudo-code) :
```
indicator = Indicator(code="...", unit="   ", dataset=dataset)
with pytest.raises(ValidationError):
    indicator.full_clean()
```

## Conventions
- Nommer les fichiers `test_*.py`
- Nommer les fonctions `test_*`
- Garder les tests courts et orientés comportement
