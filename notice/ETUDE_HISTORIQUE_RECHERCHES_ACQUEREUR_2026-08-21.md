# Étude — les recherches acquéreur, depuis le début du projet

Date : 2026-08-21. **Lecture seule.**
Demandée par Frédéric : *« depuis le début j'ai rencontré des difficultés avec les recherches,
liées au manque d'information transmise par Hektor […] ce problème avait déjà été identifié et
le choix était déjà de rendre les recherches de l'app autonomes. Fais une étude sur tout mon
projet à ce sujet — ne te base pas sur les notes de cette semaine ni sur le code. »*

Sources : notes de mai à juillet 2026 + historique git. **Rien de cette semaine.**

---

## 1. Mai — la contrainte d'origine : Hektor ne donne presque rien

`RAPPORT_ANALYSE_FICHES_DETAIL_CONTACT_HEKTOR_2026-05-25.md` établit ce que l'API renvoie
pour une recherche :

```json
{ "offre", "archive", "types", "types_commerces", "activites_commerces",
  "villes", "quartiers", "particularites", "criteres" }
```

> **Aucun identifiant.** Un tableau anonyme.
> *« Il faut normaliser `types`, `villes` et `criteres` avant de pouvoir faire un matching propre. »*

C'est de là que vient tout le reste. **La difficulté n'a jamais été un défaut de conception :
c'est la matière que Hektor accepte de donner.**

## 2. 27 mai — la couche est construite

Commit `915f6cd`. Faute d'identifiant, la clé est fabriquée en hachant
`{contact, rang, contenu}`. Le périmètre poussé vers Supabase : **les recherches actives
seulement** (`RAPPORT_AUDIT_INTEGRATION_CONTACTS_APP_2026-05-27.md`).

## 3. 12 juin — le worker sait écrire dans Hektor

Commit `4cfc581` : *« ajouter / modifier / supprimer […] scrape idCritere en contexte
négociateur, archivage via `modifDateArchiveCritere`, **container recherche étendu (tous
critères + multi-localités)** »*.

> **Point capital** : le worker **sait** envoyer tous les critères. La limite n'a jamais été là.

## 4. 19 juin — le diagnostic complet

`RAPPORT_ANALYSE_SYNC_HEKTOR_SUPABASE_2026-06-19.md` — *« analyse projet-wide suite à la
découverte du trou de sync sur les recherches »*. **Trois facettes :**

| | Défaut | Périmètre |
|---|---|---|
| **A** | orphelinage par clé instable | isolé aux recherches |
| **B** | risque d'écrasement à l'écriture | isolé aux recherches |
| **C** | angle mort `date_maj` | étendu (recherches, relations, mandats) |

**Facette B, nommée précisément** — 16 chemins d'écriture audités, **un seul** est dangereux :

| Chemin | Source du payload | Risque |
|---|---|---|
| `update_hektor_contact_search` | recharge Supabase + applique 5 champs → **renvoie TOUTE la recherche** | 🔴 **ÉCRASEMENT** |
| `update_hektor_annonce_fields` | n'envoie **que** les champs ciblés | 🟢 |
| `update_hektor_contact` | charge **le formulaire Hektor courant** d'abord | 🟢 |
| 13 autres | diff-only ou création neuve | 🟢 |

> **Le patron sûr existait déjà dans le projet** : charger l'état Hektor d'abord, puis appliquer
> les champs. La recherche est le seul chemin qui ne le fait pas.

## 5. 19 juin — LA DÉCISION : « Affinage Supabase-first »

Quatre commits le même jour. Leurs messages disent l'intention mieux que n'importe quel plan :

**`6f6fd4d` (F) — front négociateur :**
> *« "Enregistrer" appelle désormais `editSearchOptimistic` **au lieu de créer un job Hektor
> lourd**. Résultat : **critères écrits direct dans Supabase**, rapprochement recalculé
> sur-le-champ, **push Hektor débouncé en arrière-plan**. »*

**`b516877` (C) — le push de nuit :**
> *« exclut les recherches en cours d'édition app (dirty) du delete ET de l'upsert, **pour ne pas
> écraser les critères affinés dans Supabase par l'ancienne version Hektor**. »*

**`b505771` (E) / `4f8c4c1` (E fix) — le worker :**
> *« efface la ligne `app_search_pending` sur succès, **ou la marque `conflict=true` sur blocage
> Hektor** »* · *« le push saute la recherche dirty dans Supabase **qui garde l'état optimiste** »*

### Ce que ces quatre commits décident, ensemble

```
   la recherche est AFFINEE dans l'app          -> Supabase est la copie de travail
   Hektor est PREVENU ensuite, en differe       -> best-effort
   si Hektor refuse                              -> l'app GARDE sa valeur (conflict)
   le run de nuit NE REECRIT PAS une recherche affinee
```

> **C'est la décision d'autonomie que Frédéric se rappelait.** Elle n'est écrite nulle part sous
> ce mot, mais les quatre commits du 19/06 ne disent rien d'autre : **les critères appartiennent
> à l'app, Hektor n'est plus qu'un destinataire.**

## 6. 26 juin — la décision est reprise dans l'architecture

`notice/RAPPORT_ARCHITECTURE_APP_ET_STRATEGIE_COUPURE_HEKTOR_2026-06-26.md` classe la recherche
parmi les **3 seules éditions optimistes** du projet (avec annonce-champs et contact) :

> *« Recherche : recompute du rapprochement instantané (affinage Supabase-first). »*

Et `notice/NOTE_MOTEUR_RAPPROCHEMENT_ACQUEREUR_2026-06-14.md` avait déjà tranché l'aval :

> *« moteur **natif app, indépendant, app-only** […] tables dédiées app-only […] **pas de retour
> Hektor (décision métier)**. »*

**L'aval était déjà autonome. Le 19/06 rend l'amont autonome aussi.**

---

## 7. Ce qui a été construit — et ce qui a été laissé

| | État |
|---|---|
| L'app écrit ses critères sans attendre Hektor | ✅ fait le 19/06 |
| Le run de nuit ne réécrit pas une recherche affinée | ✅ fait le 19/06 |
| Le rapprochement est recalculé instantanément | ✅ fait le 19/06 |
| Un blocage Hektor laisse la valeur à l'app | ✅ fait le 19/06 |
| **La modale n'expose qu'une partie des critères** | ❌ **jamais traité** |
| **Le chemin d'écriture reste "renvoie tout"** | ❌ **jamais corrigé** (facette B) |
| Clé stable (facette A) | ❌ jusqu'au 21/08 |

### Le trou resté ouvert, mesuré aujourd'hui

La modale n'écrit que **7 champs** : `offerCode`, `priceMin`, `priceMax`, `surfaceMin`,
`roomsMin`, `bedroomsMin`, `landSurfaceMin` (+ types et villes).

Une recherche remplie dans Hektor en porte **douze** : les précédents, plus
`ITEM_SURFACE_MAX`, `ITEM_PIECES_MAX`, `ITEM_CHAMBRE_MAX`, `ITEM_SURFACE_TERRAIN_MAX`,
`ITEM_PRIX_MARGE`, `ITEM_QUARTIER_PONDERATION`.

```
   recherche PAUVRE (3 criteres)   ->  l'app reconstruit les 3   ->  le push PASSE
   recherche RICHE (12 criteres)   ->  l'app en reconstruit 1    ->  le push est BLOQUE
```

**C'est pour cela que 24 modifications ont réussi depuis juin et que la 25ᵉ a échoué : les
24 premières portaient sur des recherches pauvres.**

> ⚠️ Les **colonnes plates** (`prix_min`, `chambre_min`…) restent justes. C'est le paquet
> `criteres_json` qui se vide. Pas de perte métier — une incohérence interne, et un blocage.

---

## 8. Ce que ça veut dire

**Le système fonctionne comme il a été décidé.** Le blocage observé le 21/08 n'est pas une
panne : c'est le garde-fou du 19/06 qui empêche l'app d'écraser chez Hektor des critères
qu'elle ne sait pas porter. **Il protège Hektor de l'app.**

Mais la décision d'autonomie n'a jamais été menée à son terme. Il en résulte un **état
intermédiaire** :

```
   l'app garde sa valeur              -> autonomie OK
   Hektor garde la sienne             -> divergence
   rien ne le signale au negociateur  -> le bandeau rouge n'existe que pour les ANNONCES
   et la divergence est DEFINITIVE    -> le pending en conflit ne repart jamais
```

**Ce n'est ni l'ancien monde ni le nouveau.**

## 9. Les trois sorties possibles

| | Ce que ça demande | Ce que ça donne |
|---|---|---|
| **① Aller au bout de l'autonomie** | assumer que les recherches ne remontent plus à Hektor ; retirer le push | cohérent avec la décision du 19/06. **Hektor ne connaît plus les recherches** |
| **② Réparer l'écriture** | appliquer à la recherche le patron déjà utilisé pour le contact : **charger le formulaire Hektor d'abord**, puis n'appliquer que les champs édités | corrige la facette B. Le push cesse d'écraser, donc de bloquer |
| **③ Compléter la modale** | exposer les 5 critères manquants | traite le symptôme, pas la cause : un critère inconnu de la modale restera perdu |

**Le ② est le seul qui corrige la cause**, et son patron **existe déjà dans le projet** —
`update_hektor_contact` le fait depuis toujours.

Le ① reste le choix de fond, et il est déjà à moitié pris.

---

## 10. Ce qui n'est écrit nulle part et devrait l'être

- **Quel est l'état final voulu pour les recherches ?** Autonomes pour de bon, ou synchronisées ?
  La décision du 19/06 penche pour l'autonomie mais ne le dit pas, et le push subsiste.
- **Que voit le négociateur quand son affinage ne part pas ?** Rien aujourd'hui.
- **Que devient la recherche le jour de la coupure ?** L'app la détient déjà entièrement —
  c'est le seul objet dans ce cas.

Voir `RAPPORT_ANALYSE_SYNC_HEKTOR_SUPABASE_2026-06-19.md` (fondateur),
`RAPPORT_ARCHITECTURE_CIBLE_SYNC_2026-06-19.md`,
`notice/RAPPORT_ARCHITECTURE_APP_ET_STRATEGIE_COUPURE_HEKTOR_2026-06-26.md`,
`notice/NOTE_MOTEUR_RAPPROCHEMENT_ACQUEREUR_2026-06-14.md`,
commits `4cfc581` · `b516877` · `b505771` · `4f8c4c1` · `6f6fd4d`.
