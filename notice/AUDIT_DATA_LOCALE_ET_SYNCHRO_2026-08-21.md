# Audit — la donnée locale, ce qui est synchronisé et ce qui ne l'est pas

Date : 2026-08-21. **Lecture seule, rien n'a été modifié.**
Demandé par Frédéric : *« fais une réelle vérification et audit de ma data SQL en local, de ce
qui est synchro ou pas avec mon app et Hektor, du fonctionnement du run et du projet. Il faut
arrêter les erreurs, on perd du temps. »*

Méthode : inventaire des 26 tables locales, des 33 tables du miroir et des tables Supabase
(comptages réels) ; puis, pour chaque table locale, recherche dans **603 fichiers de code** de
qui l'écrit et **comment** — reconstruite, vidée/remplie, ou accumulée.

---

## 1. LE FAIT CENTRAL — tout va dans un seul sens

```
   HEKTOR  ->  MIROIR  ->  BASE LOCALE  ->  SUPABASE  ->  L'APP
   (loue)      3,89 Go      2,26 Go          en ligne
```

**Rien ne remonte jamais vers la gauche.** Vérifié : sur les 11 scripts qui touchent à la fois
Supabase et une base SQLite, **aucun n'écrit une valeur venue de Supabase dans une table
locale**. Le seul chemin inverse est `fetch_app_owned_contact_fields`
(`push_contacts_to_supabase.py:467`) — il relit trois champs en ligne
(`birth_date`, `birth_place`, `marital_status`) **pour les réinjecter en ligne**, afin de ne pas
les effacer. Son propre commentaire le dit : *« Le pipeline local ne les porte pas. »*

> **Le serveur n'a jamais su la date de naissance d'un seul client.**
> Ces trois champs n'existent que dans Supabase, depuis le premier jour.

## 2. Le régime de chaque table locale — la distinction qui décide de tout

Une table **reconstruite** ne peut rien *détenir* : ce qu'on y écrit disparaît à 05:30.

| Table locale | Lignes | Régime |
|---|---|---|
| `app_view_generale` | 56 890 · **130 col** | **RECONSTRUITE** — `DROP TABLE` + `CREATE TABLE AS` |
| `app_contact_relation_current` | 165 443 | **RECONSTRUITE** |
| `app_view_demandes_mandat_diffusion` | 22 078 | **RECONSTRUITE** |
| `app_contact_current` | 355 654 | vidée + remplie |
| `app_contact_search_current` | 76 841 | vidée + remplie |
| `app_contact_duplicate_*` | 118 033 | vidée + remplie |
| `app_work_item` | 22 078 | vidée + remplie |
| **`app_dossier`** | **56 890** | **accumulée** — l'identité, jamais effacée |
| **`app_search_registry`** | **76 841** | **accumulée** — les noms figés *(posée le 21/08)* |
| **`app_affaire_ledger`** | **28 981** | **accumulée** — *delete-never* |
| **`app_internal_status`** | **22 240** | **accumulée** — saisies internes |
| **`app_diffusion_*`** | **85** | **accumulée** — configuration |

**Cinq familles sur vingt-six détiennent quelque chose. Le reste est une copie du miroir.**

## 3. Les deux erreurs que cet audit corrige

**① Le plan dit** : *« côté annonces, le serveur local ne détient pas les données »* et *« la
ligne à plat n'est jamais persistée »*. **C'est faux.** `app_view_generale` est une vraie table
du disque : **56 890 lignes, 130 colonnes**, reconstruite chaque nuit en **37 secondes**
(run du 21/08 : `11:17:08 START phase2 refresh views` → `11:17:45 DONE`).

Sur les 168 champs distincts qui partent vers Supabase, **132 sont déjà des colonnes locales** ;
36 seulement sont calculés au moment de l'export (`price_change_*`, `chauffage_console_json`,
`diagnostiques_json`, `dpe_image_url`…).

**② J'ai dit** *« le contact atterrit, l'annonce traverse »*. **Faux aussi.** Les deux sont
dérivés du miroir de la même façon. Le contact a simplement plus de tables (9 contre 2), pas un
statut différent. L'annonce n'est pas le parent pauvre.

> Les deux erreurs viennent de la même faute de méthode : avoir lu un nom
> (`view_generale`, `SQL_REFRESH_VUE_GENERALE`) au lieu d'ouvrir la base.

## 4. Ce qui n'existe QU'EN LIGNE — plus d'un million de lignes

Tout ce que l'app a **inventé** n'a aucune copie sur le serveur :

| | Lignes |
|---|---|
| `app_rapprochement_score_history` | 438 814 |
| `app_console_job_log` | 173 613 |
| `app_dvf_vente` | 83 942 |
| `app_rapprochement` | 66 833 |
| `app_console_job` | 51 578 |
| `app_console_document` | 44 527 |
| `app_commune_loyers` · `_risques` · `_insee` · `ref_commune_geo` | 41 298 |
| `app_archive_annonce_index_current` | 34 468 |
| `app_mandat_register_current` | 23 824 |
| `app_console_document_fingerprint` | 13 862 |
| `app_ticket_migration` | 12 162 |
| `app_historical_annonce_index_current` | 8 802 |
| `app_rapprochement_search_state` | 4 085 |
| notifications, e-mails, estimations, agenda, moniteur… | ~10 000 |
| **TOTAL** | **≈ 1 020 000** |

**Le cerveau n'est pas le serveur. C'est Supabase.** Le serveur est un convertisseur entre
Hektor et Supabase — et il n'a jamais été autre chose.

## 5. Les trois trous trouvés

### A — Les deux tables posées cette semaine ne sont pas sauvegardées chaque nuit

`backup_critical.py:80` protège six tables de `phase2` : `app_dossier`, `app_internal_status`,
`app_diffusion_target`, `app_diffusion_agency_target`, `app_diffusion_refusal_reason`,
`app_contact_audit_run`.

**`app_search_registry` et `app_affaire_ledger` n'y sont pas.** Elles ne sont couvertes que par
l'instantané **hebdomadaire**. Or ce sont exactement des tables du même genre que `app_dossier` :

- `app_search_registry` (76 841) porte les **noms figés**. Sa perte fait recalculer tous les
  hachés → tout ce qui pendait dessous s'orpheline. C'est le sinistre qu'on vient de réparer.
- `app_affaire_ledger` (28 981) porte `app_affaire_id`, la série d'identité des transactions.

> **Jusqu'à 7 jours d'exposition sur les deux tables qui détiennent le plus.**
> Le trou le plus concret de cet audit, et le moins cher à fermer.

### B — Aucun tuyau ne redescend

Pour que le serveur soit *« seul avec Supabase »*, il faudra qu'il **apprenne** de Supabase.
Ce chemin **n'existe pas** aujourd'hui — pas partiellement : pas du tout. C'est le vrai préalable
de la cible, et il n'est écrit nulle part dans le plan.

### C — Le miroir est encore sur le chemin critique, à la LECTURE

Ouvrir une annonce archivée déclenche `prepare_archived_annonce_detail.py`, qui fabrique le
détail **depuis le miroir** et le dépose en ligne avec un **TTL de 2 h**
(`app_archive_annonce_detail_cache` : 3 lignes ; `app_historical_…` : 4). 43 270 annonces
archivées dépendent du miroir à chaque consultation.

## 6. Le vrai problème — un seul, pas plusieurs

```
   les tables locales sont DERIVEES du miroir
      -> a la coupure le miroir gele
      -> elles gelent avec lui
      -> et une valeur ecrite par l'app n'a AUCUN endroit local ou se poser :
         la reconstruction de 05:30 l'effacerait
```

Ce n'est pas un problème d'annonces. C'est le même pour tous les objets. Et **le remède est déjà
posé deux fois cette semaine** : une table **à part, jamais reconstruite**, à côté de la table
dérivée — `app_search_registry` pour les recherches, `app_affaire_ledger` pour les affaires.

> **Le patron existe, il est éprouvé. Il ne reste qu'à l'étendre.**

## 7. Ce que ça change pour le plan

**26bis-① change de nature.** Ce n'est plus *« créer et remplir 1 Go de tables »* : le Go est là,
et il se refait en 37 secondes. C'est :

1. **une table « ce que l'app détient »** pour l'annonce, jamais reconstruite — patron
   `app_search_registry` ;
2. **persister les 36 champs** qui ne sont calculés qu'au moment de partir ;
3. **et surtout ouvrir le tuyau descendant** *(trou B)*, sans lequel rien de tout cela ne sert.

**Et une tâche neuve, avant tout le reste** : mettre `app_search_registry` et
`app_affaire_ledger` dans la sauvegarde de nuit *(trou A)*.

---

---

# CORRECTION ET COMPTE RENDU D'INCIDENT — nuit du 21 au 22/08

## 1. Les chiffres de cet audit sont des ESTIMATIONS, pas des comptages

Tous les nombres de lignes ci-dessus viennent de `pg_stat_user_tables.n_live_tup`. **Ce n'est pas
un comptage** : c'est une estimation tenue par Postgres, qui derive entre deux passages de
menage (autovacuum). Sur une table sans cesse reconstruite, la derive est forte.

```
   app_rapprochement    estimation pg_stat   66 833
                        comptage reel        46 848      -> 30 % d'ecart
```

**Le chiffre juste est 46 848.** Aucune donnee n'a ete perdue : j'avais compare une estimation
a un comptage et conclu a une disparition.

Le total « ~1 020 000 lignes » est donc lui aussi approximatif. **Le seul comptage reel dont on
dispose** vient de la premiere passe complete de la descente : **1 323 943 lignes sur 109 tables
et vues** -- vues comprises, donc avec des doublons (une vue recompte les lignes de sa table).

> **Regle a retenir** : pour un chiffre qui va dans une note ou une decision, faire un
> `COUNT(*)`. `pg_stat` sert a classer par ordre de grandeur, pas a conclure.

## 2. Incident — la base de production est tombee

**Cause : moi.** J'ai lance la descente complete **deux fois en une heure** -- environ 2 800
requetes, dont plusieurs centaines de Mo de JSON (`app_dossier_detail_current` : 249 Mo pour
13 212 lignes, ~19 ko par ligne). Aucun frein entre les requetes.

**Effet** : toute l'API de donnees a repondu **HTTP 522** pendant environ vingt minutes. L'app
etait inutilisable. Il etait un peu apres minuit, donc personne ne travaillait dessus.

**Ce n'etait PAS un bannissement**, et la distinction compte :

| | |
|---|---|
| 429 / 403 | on t'a freine ou ferme la porte |
| **522** | **Cloudflare a transmis, la base n'a jamais repondu** |

Preuve que l'acces n'etait pas en cause : au meme moment, avec les memes identifiants et depuis
la meme machine, l'**API de gestion** repondait normalement (`ACTIVE_HEALTHY`). Seule la base
etait muette.

**Retablissement seul, sans intervention.** Les compteurs `pg_stat` remis a zero et
`last_autovacuum` nul montrent que **le moteur a redemarre** : c'est ce qui l'a liberee.

**Aucune donnee perdue** -- et c'est structurel, pas de la chance : le script de descente ne sait
que LIRE. Sa classe `SupabaseReader` n'a qu'une methode `get` ; ni POST, ni DELETE, ni PATCH.
Verifie apres coup : annonces 13 212, contacts 57 519, recherches 10 746, affaires 28 981 --
tous inchanges.

## 3. Etat reel de la descente : INCOMPLETE

```
   46 tables completes      585 708 lignes
   64 tables A REFAIRE      leur copie locale n'existe plus
```

**Pourquoi les 64 ont disparu, alors que la premiere passe les avait descendues.** Le correctif
pose en cours de soiree -- « une copie ratee ne laisse jamais de table partielle derriere elle »
-- supprime la table quand la copie echoue. Il est juste en soi : une copie tronquee qui se fait
passer pour de la donnee est pire que rien. **Mais il detruit aussi la BONNE copie precedente.**

> **Correctif a poser avant de relancer** : copier dans une table temporaire, puis renommer.
> Une passe ratee laisse alors intacte la copie de la veille.

## 4. Les trois freins a poser avant toute reprise

| | |
|---|---|
| **Copier puis renommer** | une passe ratee ne detruit plus la copie precedente |
| **Un frein entre les requetes**, et les tables lourdes par petits paquets | c'est le debit soutenu qui a fait tomber l'instance |
| **La nuit, une seule passe** | jamais deux d'affilee, jamais pendant une session de travail |

C'est la meme lecon que le rattrapage des documents, qui avait fait bannir notre IP chez Hektor.
Je ne l'avais pas transposee a Supabase.

---

*Sources : inventaire direct des trois supports le 21/08/2026 ; 603 fichiers de code analysés ;
`logs/scheduled/quotidien_2026-08-21_10-35-51.log` ; `phase2/sync/backup_critical.py:80-98` ;
`phase2/sync/push_contacts_to_supabase.py:464-490` ; `phase2/pipeline/view_generale.py:34,469`.*
