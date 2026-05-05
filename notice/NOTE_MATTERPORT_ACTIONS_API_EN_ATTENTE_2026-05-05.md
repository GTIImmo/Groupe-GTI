# Matterport - actions API mises en attente

Date : 2026-05-05

## Contexte

Le projet sait maintenant lire Matterport, matcher les modèles avec Hektor par numéro de mandat, créer des groupes Matterport et pousser les liens dans Supabase.

En revanche, les actions qui modifient Matterport sont retirées du code actif tant que le support Matterport n'a pas confirmé le déverrouillage de la Model API.

Erreur constatée sur un modèle actif/public :

```text
model.locked
Unlock the developer license to enable access to this model
```

Exemple testé :

```text
Hektor annonce : 62013
Mandat : 18558
Matterport model : Rt4rHP4jpFX
Nom : Maison-Unieux-18558
State : active
Visibility : public
```

## Actions volontairement retirées du code actif

- Renommer un modèle Matterport via `patchModel`.
- Modifier `description` via `patchModel`.
- Remplir `internalId` via `patchModel`.
- Changer `active/inactive` via `updateModelState`.
- Changer `public/private/unlisted/password` via `updateModelAccessVisibility`.
- Modifier l'adresse via `updateModelAddress`.

## Mutations Matterport à reprendre après réponse support

### Remplir internalId

```graphql
mutation PatchModel($id: ID!, $patch: ModelPatch!) {
  patchModel(id: $id, patch: $patch) {
    id
    name
    internalId
    state
    visibility
    modified
  }
}
```

Variables :

```json
{
  "id": "Rt4rHP4jpFX",
  "patch": {
    "internalId": "18558"
  }
}
```

### Changer state

```graphql
mutation UpdateModelState($id: ID!, $state: ModelStateChange!, $allowActivate: Boolean) {
  updateModelState(id: $id, state: $state, allowActivate: $allowActivate) {
    id
    name
    internalId
    state
    visibility
    modified
  }
}
```

Valeurs :

```text
active
inactive
```

Attention : `allowActivate: true` peut avoir un impact de facturation selon le compte Matterport.

### Changer visibility

```graphql
mutation UpdateModelAccessVisibility($id: ID!, $visibility: ModelAccessVisibility!, $password: String) {
  updateModelAccessVisibility(id: $id, visibility: $visibility, password: $password) {
    id
    name
    internalId
    state
    visibility
    modified
  }
}
```

Valeurs :

```text
public
private
unlisted
password
```

## Règle actuelle du projet

Le script actif `phase2/sync/sync_matterport_models.py` est read-only côté Matterport.

Il peut :

- scanner Matterport ;
- matcher avec Hektor ;
- générer les fichiers CSV/JSON de contrôle ;
- upserter les groupes et liens Matterport dans Supabase.

Il ne peut pas :

- modifier Matterport ;
- renommer ;
- changer state ;
- changer visibility ;
- remplir internalId.

Ces actions seront réintroduites uniquement après confirmation Matterport.
