# Note diffusion lecture / ecriture

Date: 22/03/2026

## Objet

Preparer correctement le modele SQL pour :

- lire l'etat reel de diffusion par portail
- garder l'identifiant technique `idPasserelle`
- permettre plus tard une ecriture API propre :
  - ajout d'annonce a une passerelle
  - retrait d'annonce d'une passerelle

## Point API retenu

D'apres le retour de Romain :

- `exportReporting` et `DetailedBroadcastList` sont en lecture
- l'ecriture se fait via :
  - `/Api/Passerelle/addAnnonceToPasserelle/`
  - `/Api/Passerelle/removeAnnonceToPasserelle/`
  - `/Api/Annonce/ListPasserelles/`
  - `/Api/Annonce/Diffuse/`

Conclusion :

- le snapshot de lecture ne doit pas etre confondu avec l'intention d'ecriture
- il faut conserver `hektor_broadcast_id` comme cle technique de passerelle

## Tables retenues

### 1. Stock brut existant

- `hektor_broadcast`
- `hektor_broadcast_listing`

Ces tables gardent la lecture brute telle qu'exposee par Hektor.

### 2. Catalogue de passerelles

- `hektor_broadcast_portal`

But :

- 1 ligne = 1 `idPasserelle`
- conserver :
  - `hektor_broadcast_id`
  - `passerelle_key`
  - `listing_count`
  - flags `supports_read` / `supports_write`

Cette table devient la reference pour une future ecriture `add/remove`.

### 3. Etat courant annonce x passerelle

- `hektor_annonce_broadcast_state`

But :

- 1 ligne = 1 observation courante annonce / passerelle / commercial
- normaliser l'etat courant lu depuis `DetailedBroadcastList`

Champs importants :

- `hektor_broadcast_id`
- `hektor_annonce_id`
- `passerelle_key`
- `commercial_id`
- `current_state`
- `export_status`
- `is_success`
- `is_error`

Regle actuelle :

- `export_status = exported` -> `current_state = broadcasted`
- `export_status` vide -> `current_state = unknown`
- autre valeur -> `current_state = error`

### 4. Cible future d'ecriture

- `hektor_annonce_broadcast_target`

But :

- stocker l'intention metier independamment du snapshot Hektor

Champs importants :

- `hektor_broadcast_id`
- `hektor_annonce_id`
- `target_state`
- `source_ref`
- `note`
- `last_applied_at`
- `last_apply_status`
- `last_apply_error`

## Lecture metier a retenir

Etat courant :

- `hektor_annonce_broadcast_state`

Intention metier :

- `hektor_annonce_broadcast_target`

Ecart a piloter plus tard :

- `target_state` vs `current_state`

## Pourquoi ce modele

Ce modele evite trois erreurs frequentes :

1. utiliser le nom de portail comme cle d'ecriture au lieu de `idPasserelle`
2. confondre "etat observe" et "etat souhaite"
3. devoir refondre la couche SQL le jour ou l'ecriture API sera activee

## Requetes utiles

Etat courant par annonce :

```sql
SELECT hektor_annonce_id, passerelle_key, current_state, export_status
FROM hektor_annonce_broadcast_state
ORDER BY hektor_annonce_id, passerelle_key;
```

Passerelles disponibles pour ecriture :

```sql
SELECT hektor_broadcast_id, passerelle_key
FROM hektor_broadcast_portal
WHERE supports_write = 1
ORDER BY passerelle_key, hektor_broadcast_id;
```

Annonces en erreur de diffusion :

```sql
SELECT hektor_annonce_id, passerelle_key, export_status
FROM hektor_annonce_broadcast_state
WHERE is_error = 1;
```
