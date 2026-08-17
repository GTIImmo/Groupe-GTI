# Conception Phase 1 — l'app devient autoritaire et réactive (C6 + C7)

**Date : 2026-08-17. Conception Claude, à valider. AUCUN code.**
**Pilotée par `NOTE_CONTRAT_AUTORITE_2026-08-17.md`. Correctifs C6 et C7 de l'audit global.**
**Principe directeur : construire l'état FINAL, pas un échafaudage — l'app devra tout gérer à la fin.**

---

## 1. L'objectif, en une phrase

> **Ce que le négociateur écrit dans l'app est définitif : plus rien ne peut l'écraser, et rien ne l'attend.**

Deux conséquences visibles :
- **Fin des bugs d'effacement** (la classe de bugs la plus coûteuse du projet).
- **App instantanée** : éditer = écrire, terminé. Zéro worker dans le parcours utilisateur.

---

## 1bis. ⛔ INVARIANT ABSOLU — les workers doivent continuer à fonctionner jusqu'à la coupure finale

**Consigne Frédéric (2026-08-17), prioritaire sur toute simplification :**
> *Conserver les règles Hektor (IDs, etc.) pour que les workers fonctionnent toujours, jusqu'à la coupure finale.*

Tant qu'un worker écrit dans Hektor, il a besoin de **savoir quoi viser**. Retirer un de ces éléments « parce qu'il paraît inutile côté app » **casse l'écriture Hektor en silence**. Liste des éléments **intouchables avant la coupure** (vérifiée dans le code) :

| Élément | Qui l'utilise | Conséquence si retiré/modifié |
|---|---|---|
| `hektor_annonce_id` | ciblage de tous les jobs annonce (`console_job_worker.js:1312-1349`) | `"Job without dossier or annonce id"` → **tout job annonce échoue** |
| `hektor_contact_id` | ciblage des jobs contact/recherche/mandant | idem côté contact |
| **`idUser` du négociateur** (`hektor_user_id`, `negociateur_email`) | **impersonation** : `switchHektorUserContextWithPlaywright` → `?call=authenticate&mode=autologin&idUser=…` (`:1542, 1557, 1648-1668, 1752`) | **403 Hektor** ou action exécutée **sous le mauvais négociateur** ⇒ c'est la raison de l'arbitrage n°2 du contrat |
| **`search_index`** | ciblage des éditions/suppressions de recherche (`resolveContactSearchTargetCritereId`) + PK de `app_search_pending` + les 2 RPC optimistes | **suppression de la mauvaise recherche** (cf. C4) |
| **`base_snapshot`** (+ `_date_maj`) | garde-fou anti-écrasement lu par `handleUpdateHektorAnnonceFields`, `handleUpdateHektorContact`, `guardContactSearchOverwrite` | ⚠️ **le worker plante ou pousse à l'aveugle** |
| `app_console_job` + files `*_pending` | toute la mécanique d'envoi | plus rien ne part vers Hektor |
| `numero_mandat`, états diffusion/signature | retours de service (champs 🔵) | perte du retour |

### Conséquences directes sur CE plan

1. **Étape 6 (nettoyage du calque) — ne PAS retirer `base_snapshot` ni `conflict` du modèle.**
   Le worker les **lit**. On ne retire que **l'overlay d'affichage** (`app_optimistic_overlay`) et la **lecture overlay-first du front** — c'est ça qui donne la réactivité. Le `base_snapshot` continue d'être **écrit et transmis** au worker jusqu'à la coupure. *(Le §6 est corrigé en ce sens.)*
2. **Surrogate `app_contact_id` (décision Phase 0)** : il **s'ajoute**, il ne **remplace pas**. `hektor_contact_id` reste stocké et transmis aux jobs.
3. **C3 (clé recherche)** : changer `contact_search_key` est sans danger pour les workers (ils ne l'utilisent pas), **mais `search_index` doit rester intact** tant que C4 n'a pas basculé le ciblage sur `idCritere`.
4. **Affectation négociateur** : reste 🔵 HEKTOR jusqu'à la dernière phase (déjà tranché).
5. **Garde-fou (§7)** : on le rend *non bloquant*, on ne le **supprime pas** — il continue de lire `base_snapshot`.

> **Règle de conduite** : avant de retirer quoi que ce soit, se demander *« un worker s'en sert-il pour viser Hektor ? »*. Si oui → **on garde jusqu'à la coupure**, quitte à ce que ce soit redondant côté app.

---

## 2. Le principe : Hektor perd son autorité, pas sa fonction

Aujourd'hui Hektor a **deux casquettes**. On ne lui en retire qu'**une**.

| Casquette | Aujourd'hui | Après Phase 1 |
|---|---|---|
| **Remplir** (apporter ce que l'app n'a pas : nouveaux biens, retours de service) | ✅ | ✅ **conservé** |
| **Faire autorité** (reconstruire, écraser ce que l'app possède) | ✅ | ❌ **retiré** |

> **Règle unique à implanter partout** : *un flux entrant a le droit de **remplir** un champ vide ou non possédé ; jamais d'**écraser** un champ 🟢 APP.*

C'est la correction d'ordre de la revue externe (point G) : on **rétrograde** le read-through, on ne l'arrête pas.

---

## 3. Les trois portes d'entrée à traiter

L'autorité de Hektor s'exerce par **trois** chemins distincts. Les traiter tous, sinon la fuite subsiste.

| # | Porte | Fichier / fonction | Fréquence |
|---|---|---|---|
| **P1** | **Import de nuit — annonces** | `push_upgrade_to_supabase.py` (reconstruit `app_dossier_current` + `app_dossier_detail_current`) | 1×/nuit |
| **P2** | **Import de nuit — contacts** | `push_contacts_to_supabase.py` (delete+réinsert contacts/relations/recherches) | 1×/nuit |
| **P3** | **Read-through à la demande** | `refresh_console_data` / `refresh_console_contact_data` → `push_single_annonce_to_supabase.py` | à chaque ouverture de fiche |

---

## 4. Le mécanisme retenu : la liste blanche (déjà éprouvé chez toi)

**On ne fabrique rien de neuf.** Le patron existe et fonctionne : `fetch_app_owned_contact_fields` protège déjà naissance / lieu / matrimonial de façon **permanente**.

**Comment ça marche** : l'écriture se fait en `UPSERT merge-duplicates`, qui ne met à jour **que les colonnes présentes dans le payload**. Donc :

> **Retirer un champ 🟢 du payload de nuit = la valeur de l'app est préservée automatiquement.**

Pas de verrou, pas de comparaison, pas de nouvelle table. C'est une **soustraction**, pas une addition — d'où le faible risque.

### 4.1 Le cas « seed une fois »
Un champ 🟢 (ex. le prix) vient **initialement** de Hektor. Il faut donc l'écrire **à la première apparition**, puis ne plus y toucher.

**Règle** : le payload inclut un champ 🟢 **si et seulement si** la ligne est **nouvelle** (absente de Supabase).
- Ligne nouvelle → payload complet (seed).
- Ligne existante → payload **amputé des champs 🟢**.

Concrètement : lire la liste des clés déjà présentes (le code le fait **déjà** — `remote_dossiers` dans `push_upgrade_to_supabase.py:1146`, `present_contact_ids` dans `push_contacts_to_supabase.py:676`), puis découper le payload en deux lots : *nouvelles lignes* (complet) et *lignes existantes* (amputé).

### 4.2 Le blob descriptif (le gros morceau)
Le contenu descriptif de l'annonce (surface, pièces, DPE, équipements…) vit dans `app_dossier_detail_current.detail_payload_json` — **un seul champ JSON**. On ne peut donc pas simplement « retirer une colonne ».

**Deux options :**
- **(a) Fusion de blob** : à l'écriture, relire le blob existant et **réinjecter les clés 🟢** par-dessus la version Hektor. *Plus de code, mais granularité par champ.*
- **(b) Blob entier 🟢** : une fois la ligne seedée, l'import **ne réécrit plus le blob du tout** (seules les colonnes 🔵 de `app_dossier_current` sont rafraîchies). *Beaucoup plus simple, et c'est l'état final visé.*

### 🔴 DÉCISION (b) ANNULÉE le 2026-08-17 — NE PAS APPLIQUER

> **L'option (b) était fondée sur une hypothèse FAUSSE** : que le blob `detail_payload_json` était
> purement descriptif. Vérification faite après coup (~130 clés inspectées en base), il transporte
> aussi des données Hektor **vivantes** — diffusion, offres/compromis/ventes, mandats, photos,
> propriétaires, notes. Appliquer (b) aurait **gelé** ces remontées.
>
> **Les deux options (a) et (b) sont donc à refaire** : elles étaient toutes deux formulées sur cette
> prémisse. Prérequis avant réécriture : **inventaire exhaustif des ~130 clés du blob**, classées
> APP / HEKTOR / SYSTÈME avec leur source d'écriture, validé par Frédéric.
> Détail complet de la correction : §9 de `NOTE_CONTRAT_AUTORITE_2026-08-17.md`.
>
> **Le reste de cette note reste valide** : le principe (§2), les trois portes (§3), le mécanisme de
> liste blanche **au niveau des colonnes** (§4, §4.1), l'invariant workers (§1bis), l'ordre (§8) et
> les tests (§9). Seul le traitement du blob est en suspens.

<details><summary>Texte d'origine de la décision (b) — conservé pour trace</summary>

**DÉCISION : option (b) — blob entièrement APP après seed** *(Frédéric, 2026-08-17, sur recommandation Claude — recommandation erronée)*

Puisque l'app doit tout gérer à la fin, le blob descriptif lui appartient **entièrement**. L'option (a) aurait été un échafaudage à démonter plus tard.

**Réserve levée (vérifiée le 2026-08-17) — aucune exception n'est nécessaire :**

| Source | Ce qu'elle alimente | Verdict |
|---|---|---|
| `sync_hektor_chauffages.py` (nocturne, 50/j) | écrit dans la table **locale** `hektor_annonce_chauffage_detail`, qui alimente le blob à la reconstruction | ✅ **pas d'exception** — le chauffage est **déjà éditable dans l'app** (`formatChauff`, `typeChauff`, `energieChauff`, wizard étape 5, `App.tsx:1446`) |
| `sync_console_missing_fields.py` | table locale `hektor_annonce_console_detail` | ✅ **non concerné** — **désactivé par défaut** (`RunConsoleMissingFields=False` dans le run quotidien) |
| `sync_console_contact_missing.py` | naissance / lieu / matrimonial du contact | ✅ **déjà en mécanisme ②** (protection permanente existante) |

**Conclusion** : ces scrapes existent parce que l'**API** Hektor ne renvoie pas ces champs — c'est un trou de **lecture**, pas d'**écriture**. L'app sait déjà les écrire.

⇒ Ils changent donc de rôle : de **source permanente** ils deviennent des **outils de seed/backfill**, utiles uniquement pour les biens que l'app n'a pas encore édités. Ils s'éteignent naturellement à mesure que le parc est seedé. **Le chauffage est un champ 🟢 APP ordinaire, sans traitement particulier.**

*(Conséquence assumée, identique à celle du prix ou de la surface : si un négociateur modifie le chauffage **dans Hektor** après le seed, la valeur n'arrivera plus. C'est exactement la règle « une seule porte d'écriture = l'app ».)*

</details>

**⚠ Rappel : tout le bloc ci-dessus (option (b) et sa « réserve levée ») est ANNULÉ.** L'analyse des
scrapes Console (chauffage éditable dans l'app, `sync_console_missing_fields` désactivé) reste juste
et réutilisable ; c'est la conclusion « donc on gèle le blob entier » qui est fausse.

---

## 5. Le read-through (P3) — rétrogradation

Il fait aujourd'hui deux choses ; on n'en garde qu'une.

- ✅ **Garder** : rafraîchir les champs 🔵 (retour de diffusion, de signature, numéro de mandat) et **remplir** une fiche absente.
- ❌ **Retirer** : reconstruire les champs 🟢.

**Bonne nouvelle** : la protection existe **déjà partiellement** — `push_single_annonce_to_supabase.py:523` saute une annonce dont un `pending` est en cours (`dirty_annonce_skipped`). Mais c'est la protection **①, temporaire** : dès le pending consommé, l'autorité revient à Hektor.

**Changement** : appliquer la **même liste blanche** qu'en P1/P2 au chemin read-through → la protection devient **permanente**, indépendante du pending.

⇒ Effet de bord bénéfique : **le read-through cesse d'être une menace**, donc le calque n'a plus besoin de s'en défendre.

---

## 6. Le calque optimiste — nettoyage, PAS préalable

`app_optimistic_overlay`, `base_snapshot`, flag `conflict` : cette machinerie n'existe **que** pour survivre à un read-through qui pouvait écraser. Une fois l'autorité retirée (§5), elle devient du **poids mort**.

**Ordre impératif (correction G)** : rétrograder d'abord, simplifier ensuite. Simplifier avant, ce serait retirer l'armure avant d'avoir désarmé l'adversaire.

**Ce qui tombe, une fois §5 acquis** *(corrigé par l'invariant §1bis)* :
- l'overlay `app_optimistic_overlay` (l'écriture en colonne suffit) ;
- la lecture « overlay d'abord » dans le front ;
- l'usage **bloquant** du flag `conflict` pour les champs 🟢 (il devient informatif : on pousse et on notifie, cf. §7).

**Ce qui RESTE — ne pas y toucher avant la coupure (invariant §1bis)** :
- ⛔ **`base_snapshot` (+ `_date_maj`) : conservé, écrit et transmis** — le worker le **lit** (`handleUpdateHektorAnnonceFields`, `handleUpdateHektorContact`, `guardContactSearchOverwrite`). Le retirer casse l'écriture Hektor.
- ⛔ **`search_index`**, **`hektor_*_id`**, **`idUser` du négociateur** : ciblage Hektor.
- La file `*_pending` — qui devient simplement la **file d'envoi** du lot 2×/jour.

> La réactivité vient du **front** (plus d'overlay à écrire ni à consulter) et de la **fin de la menace d'écrasement** — **pas** du démontage de la mécanique d'envoi, qui doit survivre jusqu'à la coupure.

⇒ **Gain de réactivité** : le parcours d'édition n'a plus d'overlay à écrire, plus de garde-fou à consulter, plus de read-through à craindre.

---

## 7. Le garde-fou anti-écrasement — à inverser (champs 🟢 seulement)

Aujourd'hui, avant de pousser vers Hektor, le worker compare le `date_maj` : si Hektor a bougé depuis l'édition, il **renonce** et passe en `conflict` — *Hektor gagne*.

**Après Phase 1**, pour un champ 🟢 : **l'app gagne**, donc on pousse. Le garde-fou n'a plus lieu d'être.

⚠️ **Nuance à ne pas rater** : le garde-fou protège aussi contre l'écrasement d'une saisie faite **dans Hektor par un négociateur**. Il reste donc utile **tant que les négociateurs travaillent encore dans Hektor**.

**Recommandation** : garder le garde-fou **actif mais non bloquant** pendant la cohabitation — au lieu de renoncer, on **pousse et on notifie** (« la valeur Hektor a été remplacée »). Il s'éteint à la bascule des négociateurs. C'est cohérent avec « une seule porte d'écriture = l'app ».

---

## 8. Ordre d'exécution (et réversibilité)

| Étape | Action | Réversible ? |
|---|---|---|
| **1** | Figer la liste blanche 🟢 en un **seul endroit partagé** (une constante lue par P1, P2, P3 — surtout pas trois copies) | ✅ |
| **2** | **P3** — appliquer la liste au read-through (le plus fréquent, effet immédiat) | ✅ retirer la liste |
| **3** | **P1 + P2** — appliquer la liste à l'import de nuit + logique « seed une fois » | ✅ |
| **4** | Retirer la ligne 446-449 de `push_contacts_to_supabase.py` (le « Hektor gagne » explicite) | ✅ |
| **5** | Rendre le garde-fou non bloquant sur les champs 🟢 (§7) | ✅ |
| **6** | **Nettoyage** : simplifier le calque (§6) | ⚠️ moins trivial — faire en dernier, une fois 1-5 validés en production |

**Chaque étape est une soustraction** → revenir en arrière = remettre le champ dans la liste. C'est ce qui rend la Phase 1 sûre.

---

## 9. Comment tester (méthode cadastre, sur bien témoin)

1. **Non-écrasement** : éditer un champ 🟢 (prix, surface) → attendre l'import de nuit → **la valeur de l'app est toujours là**. C'est LE test.
2. **Remplissage préservé** : créer un bien **dans Hektor** → l'import de nuit le **fait apparaître** dans l'app (le seed fonctionne encore).
3. **Retour de service** : vérifier qu'un changement d'état de diffusion / un numéro de mandat **arrive bien** (champs 🔵 non bridés).
4. **Read-through** : ouvrir une fiche éditée → la valeur app **ne clignote pas** et ne revient pas.
5. **Réactivité** : chronométrer une édition — aucune attente worker perceptible.
6. **Non-régression rapprochement** : une édition de prix/surface **recalcule** toujours les correspondances.

---

## 10. Ce que la Phase 1 NE fait pas (limites assumées)

- **Ne touche pas aux recherches** : leur volet du contrat exige C4 puis C3 (delete+réinsert nocturne sous clé instable). Piste parallèle.
- **Ne change pas le rythme d'envoi** vers Hektor (c'est la Phase 2 / variante A).
- **Ne rapatrie pas les photos** (C9) ni ne remplace les 3 services externes.
- **Ne rend pas les créations optimistes** (Phase 2b) : créer un bien attendra encore Hektor.

---

## 11. Décisions — toutes prises

| Décision | Choix |
|---|---|
| Blob descriptif (§4.2) | **(b)** — entièrement APP après seed ; **aucune exception nécessaire** (réserve levée, cf. §4.2) |
| Identité contact | surrogate `app_contact_id` |
| Stockage | statu quo (local maître, cloud sélectif) |
| Worker 2×/jour | variante A puis B |
| Contrat d'autorité | complet (`NOTE_CONTRAT_AUTORITE_2026-08-17.md`, 4 arbitrages tranchés) |

**⇒ La conception de la Phase 1 est COMPLÈTE. Plus aucune décision en attente pour la mettre en œuvre.**

Restent deux points mineurs, sans impact sur la Phase 1 : politique orphelins (proposition : delete-never) et ordre journalier push/pull (proposition : push puis pull).
