# Note transaction_commerce

Date: 22/03/2026

## Constat

Apres correction du bootstrap `ListAnnonces`, il reste un petit lot de dossiers presents dans
`case_dossier_source` mais absents de `hektor_annonce`.

Verification faite :

- ces IDs ne repondent pas a `AnnonceById`
- ils sont cependant encore references par :
  - `hektor_offre`
  - `hektor_compromis`
  - parfois `hektor_vente`

## Nature des dossiers

Les dossiers concernes sont homogenes :

- `idtype = 23`
- `offredem = 10`

Les titres observes dans les payloads transactionnels montrent qu'il s'agit de fiches commerce /
immobilier professionnel :

- fonds de commerce
- local commercial
- local professionnel
- murs commerciaux
- bar / restaurant
- tabac / presse / loto

## Interpretation retenue

Ces dossiers ne doivent plus etre interpretes comme un trou generique de synchronisation.

Ils correspondent a un cas metier particulier :

- transaction visible
- annonce source non exposee par l'API annonce

Le projet les classe donc explicitement comme :

- `case_kind = 'transaction_commerce'`

## Regles retenues dans `case_dossier_source`

Ajout de :

- `annonce_source_status`
  - `present`
  - `missing`

Conservation de :

- `case_kind`

Regle de marquage :

- `annonce_source_status = 'present'` si `hektor_annonce` existe
- `annonce_source_status = 'missing'` sinon
- `case_kind = 'transaction_commerce'` si :
  - annonce source absente
  - et type transactionnel commerce detecte via `idtype = 23` et `offredem = 10`

## Lecture a retenir

Cas normaux :

- `annonce_source_status = 'present'`

Cas metier reconnus :

- `annonce_source_status = 'missing'`
- `case_kind = 'transaction_commerce'`

Vraies anomalies restantes :

- `annonce_source_status = 'missing'`
- `case_kind IS NULL`

## Requetes utiles

```sql
SELECT *
FROM case_dossier_source
WHERE case_kind = 'transaction_commerce';
```

```sql
SELECT *
FROM case_dossier_source
WHERE annonce_source_status = 'missing'
  AND COALESCE(case_kind, '') <> 'transaction_commerce';
```
