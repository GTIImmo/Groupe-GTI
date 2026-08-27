# Note transaction_commerce

> ## ATTENTION -- CETTE NOTE A ETE CORRIGEE LE 27/08/2026
>
> **Son constat est juste, son interpretation est fausse.**
>
> Ce qu'elle a bien vu, et qui reste vrai : les fiches commerce portent toutes
> `idtype = 23` et `offredem = 10`, quelle que soit leur nature reelle -- fonds de
> commerce, local commercial, murs commerciaux, bar, tabac. **C'est HEKTOR qui ecrase**,
> verifie le 27/08 par appel API direct sur l'annonce 62825 et sur les 251 annonces
> immo pro actives : 251 sur 251 portent `idtype = 23`. Rien dans notre code ne le force.
>
> Ce qu'elle a mal interprete : elle dit *"ces IDs ne repondent pas a AnnonceById"* et en
> conclut *"annonce source non exposee par l'API"*, donc un **cas metier**.
> **C'est faux : AnnonceById repond tres bien** (verifie le 27/08 sur 62825).
>
> **La vraie cause : on ne les avait jamais demandees.** `ListAnnonces` etait appele SANS
> le parametre `offre`, et Hektor ne rend alors que les ventes classiques. C'est le defaut
> C.15, trouve le 26/08/2026 -- cinq mois apres cette note.
>
> Consequence : le `case_kind = 'transaction_commerce'` cree ici a range en exception
> metier ce qui etait un defaut d'appel. Il n'est plus applique (les 56 912 lignes de
> `case_dossier_source` sont a `case_kind = NULL`).
>
> ### La lecon
> **Un lot d'objets homogenes absents du miroir n'est pas un cas metier : c'est presque
> toujours une question qu'on n'a pas posee.** Meme piege que le 26/08 -- confondre le nom
> d'un champ dans la REPONSE et le nom du parametre de la REQUETE.
>
> ### La decision du 27/08 (Frederic)
> L'ecrasement par Hektor n'est **pas bloquant**. Quand l'app lira les donnees du SERVEUR,
> **c'est nous qui porterons le type fin** (murs commerciaux, fonds de commerce, entrepot...),
> meme si Hektor continue de rendre 23. Le serveur devient la source de verite sur ce point.
> Cote creation, on enverra a Hektor le code de SON formulaire (murs commerciaux = 5) ; cote
> lecture, on affichera NOTRE valeur.

---


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
