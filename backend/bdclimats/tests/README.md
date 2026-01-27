# Tests

Organisation (pour garder la lisibilité) :
- `api/`
  - `tv/` : tests fonctionnels/validation côté API
  - `tu/` : tests unitaires côté API
- `catalog/`
  - `tv/` : tests de validation côté modèles
  - `tu/` : tests unitaires côté modèles

Priorité actuelle :
- **TV (tests fonctionnels/validation)** d'abord
- **TU** ensuite si nécessaire

Template (TV API)
1) Arrange : créer Dataset / Indicator / ComputationRule
2) Act : appeler l'endpoint via `api_client`
3) Assert : vérifier `status_code` + champs clés
