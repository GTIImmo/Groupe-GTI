# Adresse privée — pourquoi on ne la persiste PAS côté app (et ce qu'il faudra faire à la coupure)

**Date : 2026-08-17. Conclusion d'investigation. AUCUN correctif à appliquer.**
**Cette note existe pour éviter qu'on refasse le même faux diagnostic.**

---

## Le constat qui met sur une fausse piste

En lisant `app_edit_annonce_optimistic`, on remarque que `json_map` et `col_map` ne
contiennent **aucune entrée** pour `adresse`, `villeprivee`, `codeprive` ni `address`,
alors que tous les autres champs saisissables y sont.

On en déduit naturellement : *« l'adresse privée n'est écrite dans aucune colonne durable ;
elle ne survit que parce que Hektor la stocke et que le pipeline la relit ; donc à la
coupure elle deviendra saisie-mais-jamais-conservée. C'est un oubli, il faut l'ajouter
au mappage. »*

**Ce raisonnement est faux.** Un correctif avait été écrit sur cette base le 2026-08-17 ;
il a été supprimé sans être appliqué.

---

## Pourquoi c'est faux : l'adresse privée est un RÉSULTAT, pas une valeur

Deux commentaires du code disent l'essentiel :

> `App.tsx:1344` — « Pas de "Complément d'adresse" : **Hektor compose l'adresse privée = rue
> de la localité + ADRESSE_COMPL** ; la rue suffit (elle pilote la localité). »

> `App.tsx:21829` — « Hektor renvoie l'adresse privée en **UNE ligne** (rue + complément
> composés, ex. "10 Place Bellecour BAT B"). Afficher une case complément à part la laissait
> toujours vide → suppression. »

Autrement dit :

| | |
|---|---|
| Ce que le négociateur saisit (`adresse`) | une **entrée** qui pilote la localité Hektor, via la géolocalisation BAN |
| Ce que Hektor renvoie (`adresse_detail`, `adresse_privee_listing`) | le **résultat composé et normalisé** : rue + complément |

La lecture le confirme (`App.tsx:2544`) : le formulaire lit `adresse_privee_listing` puis
`adresse_detail` — deux formes du résultat, **jamais la saisie brute**.

**Conséquence du correctif envisagé** : on tape « 10 Place Bellecour », Hektor renvoie
« 10 Place Bellecour BAT B ». Écrire la saisie dans `adresse_detail` écrase le composé par
le brut, puis les deux se battent à chaque synchro. On aurait créé une divergence
permanente là où il n'y a aujourd'hui qu'un délai d'affichage — délai déjà couvert par le
calque optimiste.

---

## Ce qui est vrai en revanche : à la coupure, personne ne composera plus

Quand Hektor s'éteint, la composition disparaît avec lui. L'app doit alors fabriquer
l'adresse elle-même. Elle a déjà presque tout :

| Élément | État aujourd'hui |
|---|---|
| Rue, commune, code postal privés | ✅ saisis dans l'app (wizard, groupe « secteur ») |
| Latitude / longitude | ✅ l'app géolocalise déjà (Géoplateforme, `api.ts:3162`, déclenché `App.tsx:23764`) |
| **Complément d'adresse** (`ADRESSE_COMPL`) | ⚠️ **lu** en brut, mais **retiré du formulaire** — non éditable |
| Colonnes app pour conserver les composants | ❌ n'existent pas |
| Règle de composition | ❌ portée par Hektor |

**Travail réel à la coupure — trois points, tous petits :**
1. rendre `ADRESSE_COMPL` saisissable (il avait été retiré parce que Hektor le composait déjà) ;
2. persister les composants (rue, complément, commune, CP) dans des colonnes app-owned ;
3. composer la ligne côté app — la règle est simplement « rue + complément ».

Aucun partenaire, aucun contrat, aucune API tierce : c'est une concaténation. À ranger
avec l'étape de coupure, pas avant.

---

## Le signal à retenir pour les prochains diagnostics

> **Quand un champ est SAISI sous une clé et LU sous d'autres clés, c'est qu'une
> transformation existe entre les deux.** L'absence de mappage direct n'est alors pas un
> oubli : c'est la marque d'un aller-retour assumé.

Ici : saisie sous `adresse`, lecture sous `adresse_privee_listing` / `adresse_detail`.
Trois clés pour un concept — le signe qu'il fallait chercher la transformation avant de
conclure au défaut.

*(Même famille d'erreur que la décision (b) sur le blob annonce, §9 de
`NOTE_CONTRAT_AUTORITE_2026-08-17.md` : un mécanisme délibéré pris pour une lacune.)*
