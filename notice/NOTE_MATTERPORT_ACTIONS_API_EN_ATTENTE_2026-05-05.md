# Matterport - actions API mises en attente

Date : 2026-05-05

> ⛔ **ÉTAT AU 04/11/2026 : L'API MATTERPORT EST HORS SERVICE POUR NOUS. TOUT PASSE PAR LA CONSOLE.**
>
> - **L'API publique** (`api.matterport.com`, clé de `matterport/.env`) ne sert plus à rien. Le compte n'a pas la licence développeur :
>   - en mai, elle refusait déjà les écritures ;
>   - depuis la nuit du 02 au 03/11, elle refuse aussi la lecture (`model.locked`) ;
>   - une seconde clé du même compte a le même refus.
> - **ENTRÉE (lire les visites)** : la synchro de nuit `phase2/sync/sync_matterport_models.py`, étape « phase2 sync Matterport links to supabase » de `run_full_pipeline.ps1`, vers 6 h 15. Elle lit par la porte de la console, `my.matterport.com/api/mp/models/graph`.
> - **SORTIE (agir sur une visite)** : les gestes en ligne / hors ligne / archiver / réactiver. Ils passent par le worker (`Console/console_job_worker.js`), qui pilote la console dans un navigateur via `Console/matterport_console_actions.js` (Playwright).
> - **Une seule session pour les deux** : `Console/matterport_storage_state.json`. Si elle expire, la nuit l'écrit en clair ; on la renouvelle avec `node Console/matterport_playwright_login.js`.
> - **L'interrupteur** `MATTERPORT_SOURCE=console|api` (console par défaut) ne concerne que la lecture. Il permettrait de revenir à l'API le jour où la licence serait prise.
> - ⚠ La porte de la console n'est pas documentée par Matterport : elle peut changer sans prévenir.
>
> Le détail du 04/11 est en bas de cette note. Ce qui suit est l'état de mai, gardé tel quel.

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

## 04/11/2026 -- la LECTURE est verrouillee a son tour

- Depuis la nuit du 02 au 03/11, l'API publique refuse aussi la lecture : chaque modele repond `model.locked` (« Unlock the developer license »), et la recherche ne rend plus que la demo « Get Started ». L'etape « phase2 sync Matterport links to supabase » echouait (non bloquante) les nuits du 03 et du 04/11.
- Une seconde cle API du meme compte a exactement le meme refus : le verrou porte sur le COMPTE, pas sur la cle.
- Decision de Frederic (04/11) : lire par la CONSOLE, comme les gestes. `phase2/sync/sync_matterport_models.py` interroge maintenant `https://my.matterport.com/api/mp/models/graph` avec les cookies de `Console/matterport_storage_state.json`, qu'il lit sans jamais les reecrire. Les requetes GraphQL sont inchangees.
- Interrupteur `MATTERPORT_SOURCE` (`console` par defaut, `api` pour revenir a l'ancien chemin), dans `matterport/.env` ou dans l'environnement.
- Controle du 04/11, a blanc (aucune ecriture dans Supabase) :
  - 6 730 modeles lus, contre 6 723 le 02/11 : 7 nouveaux, 0 disparu ;
  - 40 modeles tires au hasard sont identiques champ par champ ;
  - les autres ecarts sont de vraies retouches faites entre-temps (3 renommages, 4 deplacements de dossier, 2 changements d'etat) ;
  - le rattrapage portera sur 22 groupes et 30 liens, avec 1 groupe retire.
- Une session morte repond en HTTP 200 `organization.unspecified` : le script le traduit en « Session console Matterport expiree ... relancer node Console/matterport_playwright_login.js ».
- Fragilite assumee : cette porte n'est pas documentee par Matterport.
