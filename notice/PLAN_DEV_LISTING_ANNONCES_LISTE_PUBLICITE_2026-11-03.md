# Plan de développement — listing Annonces : vue Liste + vue Publicité (03/11/2026)

> **Maquette validée par Frédéric le 03/11/2026** (« oui j'aime bien », version 8) :
> https://claude.ai/artifact/1ASo32rVwFg5aS1PUJu2k2 (planches Bureau 1280 px, Téléphone, Ce qui change, Bouton Action).
> Socle d'audit : `notice/AUDIT_CYCLE_ANNONCE_MANDAT_DIFFUSION_2026-11-03.md`.
> **Rien n'est codé.** Chaque lot attend son « vas-y ». Une seule tâche en code à la fois.
>
> Écran concerné : menu **Annonces** = `screen === 'mandats'` → `MandatsScreen` (App.tsx ~26793, table ~26919-27192)
> et `MobileMandatCards` (~39707). ⚠ `MandatsScreen` sert AUSSI l'écran Estimations (mode estimation) :
> **ne pas toucher le mode estimation.** `screen === 'annonces'` / `StockScreen` = code mort.

---

## Lot 0 — Les prérequis de données (lecture et mesure seulement)

*Feu vert : j'enchaîne sans attendre — rien n'est écrit, rien n'est changé.*

- **0a. La diffusion par portail est figée depuis le 26/10.** `data/hektor.sqlite` →
  `hektor_broadcast_listing.synced_at` max = `2026-10-26T04:25:12Z` (mesuré le 03/11). Le Supabase
  `app_mandat_broadcasts_current` porte `refreshed_at` du jour, mais il est **reconstruit depuis ce miroir figé**.
  Même famille que [la panne de juillet](mémoire `diffusion-portails-gelee-juillet`). À trouver : quelle étape du
  run ne descend plus `list_broadcasts` depuis le 26/10 (pannes Hektor 27-28/10 ? étape sautée ?).
  ⛔ **Sans ça, la vue Publicité afficherait des cases fausses.** Bloquant pour le lot 3, pas pour le lot 1.
- **0b. `has_diffusion_error` vaut 0 partout** alors que 9 annonces actives ont un portail `is_error`. Lire
  l'agrégat de `phase2/pipeline/view_generale.py` (~l. 62-69). Sert au point orange (lots 1 et 3).
- **0c. Les numéros Hektor de Paper, Etreproprio, Superimmo par agence.** Seuls Bien'ici et Leboncoin sont dans
  `defaultDiffusionAgencyTargets` (api.ts ~306-340), `phase2/schema_phase2.sql`,
  `phase2/sync/hektor_diffusion_writeback.py` et `app_diffusion_agency_target`. Superimmo = 21 dans
  `NOTE_REPRISE_DIFFUSION_API_2026-04-01.md` (à reconfirmer). Outil existant :
  `python phase2/checks/passerelle_par_agence.py` (une requête Hektor en lecture, ou `--hors-ligne`).
- **0d. Le libellé humain de `paper`** — à demander à Frédéric.

### ✅ Résultats du lot 0 (03/11/2026, lecture seule — rien écrit, rien appelé chez Hektor)

**0a — CAUSE TROUVÉE : le run ne lit que 5 pages sur 80.**
- Le brut du jour (`raw_api_response`, `list_broadcasts`, run 5491, 03/11 04:19) porte `version: v2` et une
  réponse **paginée** : `metadata.total = 1588`, `perPage = 20`, et après la 5ᵉ page `nextPage = 5`.
- Le run de nuit tourne en mode `update`, où `resolve_generic_max_pages()` (sync_raw.py ~1665) plafonne les listes
  génériques à `--update-max-pages` = **5** (défaut, l. 1728). `broadcasts` n'a pas d'exception (contrairement à
  mandats, compromis, offres, ventes).
- `broadcast_reponse_complete()` (normalize_source.py ~146) voit `nextPage` non nul → **refuse à juste titre** de
  mettre à jour → `hektor_broadcast_listing` reste au **26/10 04:25:12Z** (1 546 lignes). Le garde-fou a fait son
  travail ; ⚠ mais **aucune alerte** n'a sonné en 8 jours.
- Probable déclencheur (non prouvé, le brut d'avant n'est pas gardé) : le passage à `version=v2` / le changement de
  forme de Hektor entre le 23/10 et le 02/11 (mémoire `api-hektor-sans-version-ancienne-forme`) — la liste n'était
  pas paginée avant, elle l'est maintenant.
- Détail : la page 0 et la page 1 sont **identiques** (Hektor compte à partir de 1) → une requête perdue par nuit.
- **Remède proposé (à valider, modification du run de nuit)** : exempter `broadcasts` du plafond en mode update
  (≈ 80 requêtes par nuit, très loin des ~13 000 du quota), puis rafraîchir avec
  `phase2/sync/rafraichir_passerelles.py` (lit le brut, n'appelle pas Hektor). ⛔ Il faut d'abord **une descente
  complète** (le run, ou une descente ciblée des broadcasts = ~80 requêtes) → **accord obligatoire**.
  Ajouter une alerte quand la réponse est refusée pour « incomplète ».

**0a bis — PLUS GRAVE QUE LA PAGINATION : la forme a changé, et la nuit EFFACE (mesuré le 03/11).**
- Au 26/10 une diffusion s'écrivait `{annonce_id, commercial{nom,prenom}, export_status}` et une passerelle `nom`.
  Depuis : `{propertyId, agent{lastName,firstName}, exportStatus, exportWarnings}` et `code`.
- `upsert_broadcast_listings` (normalize_source.py) **efface** les lignes de chaque passerelle aperçue sur les 5
  pages lues (Bien'ici n° 2, 3, 4, 5 = Ambert, Annonay, Brioude, Craponne ; ~83 annonces), puis ne réinscrit
  **rien** (pas d'`annonce_id`). Ces 4 passerelles ont **disparu** de `hektor_broadcast_listing`, et
  `hektor_broadcast.nom` est passé à NULL pour elles.

**🔧 Correctif PRÉPARÉ le 03/11 — DORMANT, interrupteur `APP_PASSERELLES_V2` absent du `.env` (= éteint).**
- `sync_raw.py` `resolve_generic_max_pages` : allumé, `broadcasts` lit **toutes** les pages en mode update (~80).
- `normalize_source.py` : `passerelles_v2_actif()`, `broadcast_bilan_pages()` ; allumé, lit les **deux formes** ;
  **n'efface rien** si la réponse est incomplète (verrou 1 : `nextPage` ; verrou 2 : diffusions distinctes lues
  < `metadata.total`) ; écrit au journal `[passerelles] REFUS …` ou `[passerelles] COMPLETE …`.
- Éteint : comportement d'avant **à l'identique** (épreuve).
- **Épreuve hors ligne** (copies de `data/hektor.sqlite`, script `scratchpad/epreuve_passerelles.py`, base réelle
  intacte : 1 546 lignes, 26/10 04:25) : éteint = inchangé ; allumé + réponse du jour = REFUS, 0 effacement, noms
  rétablis ; allumé + fausse « complète » (5 pages) = REFUS par le verrou 2. ⚠ La 1ʳᵉ version sans verrou 2 effaçait
  1 546 → 80 sur une fausse complète : c'est ce qui l'a fait ajouter.
- ✅ **ÉPROUVÉ EN RÉEL le 03/11 (demandé par Frédéric avant d'allumer)** : lecture seule chez Hektor,
  `DetailedBroadcastList` pages 0 à 80 = **81 requêtes en 268 s**, `total = 1598`, dernière page sans suite ;
  écrit UNIQUEMENT dans une copie (`scratchpad/essai_api/`), base réelle vérifiée intacte après (1 546, 26/10).
  - ⚠ **L'essai a trouvé un défaut** : le verrou 1 s'appuyait sur `broadcast_reponse_complete`, qui exige
    qu'AUCUNE page n'annonce de suite → refusait toute réponse paginée. Remplacé, en mode v2, par
    `broadcast_reponse_complete_v2` (un seul passage, pages contiguës, dernière page sans suite, ≥ 1 passerelle).
  - Rejoué sur la copie : `[passerelles] COMPLETE : 37 passerelles` ; **1 598 lignes = le total de Hektor** ;
    Bien'ici 2-5 **revenus** (27 + 20 + 18 + 18) ; 0 passerelle sans nom ; **392 annonces en ligne**.
    Par portail : Bien'ici 307 · Etreproprio 356 · Paper 356 · Superimmo 303 · Leboncoin 276.
    Écart avec le 26/10 : Bien'ici +94 / −14, Leboncoin +15 / −19, les trois autres +10 / −18.
  - 7 diffusions non exportées, toutes `pending` (63013, 63184) : c'est « en attente d'export », pas une erreur —
    `derive_broadcast_state` les classe pourtant en `error` (à revoir pour l'écran : « en attente »).
- ⚠ `sync_raw.py` porte AUSSI une modification non commitée d'une autre session (`APP_RELIRE_DETAIL_MANDAT_ABSENT`) :
  ne pas la commiter avec celle-ci.
- **Allumer** (accord de Frédéric) : ajouter `APP_PASSERELLES_V2=1` au `.env` → effet au prochain run (05:00).
  Contrôler au matin : journal du run `[passerelles] COMPLETE`, `hektor_broadcast_listing.synced_at` du jour,
  ~1 588 lignes, Bien'ici 2-5 revenus. **Retour arrière** : retirer la ligne du `.env` (le brut n'est jamais purgé ;
  `phase2/sync/rafraichir_passerelles.py` refabrique l'état).
- ✅ **ALLUMÉ le 03/11/2026 par accord de Frédéric** (« Oui, allume ») : `APP_PASSERELLES_V2=1` ajouté en fin de
  `.env` (l. 120), copie datée `.env.avant_passerelles_v2_20261103`. Vérifié : `load_env()` le lit,
  `passerelles_v2_actif()` = vrai, `resolve_generic_max_pages(update, 'broadcasts')` = None (le run passe
  `--max-pages 0` = `$DailyRawMaxPages` par défaut). Premier passage : **run de 05:00 le 04/11**.
- ⏰ **CONTRÔLE DU 04/11 AU MATIN** :
  1. journal du run : `[passerelles] COMPLETE : … passerelle(s), … diffusion(s)` (et pas `REFUS`) ;
  2. `data/hektor.sqlite` : `hektor_broadcast_listing` ≈ 1 600 lignes, `synced_at` du 04/11, Bien'ici 2-5 présents ;
  3. Supabase `app_mandat_broadcasts_current` : ~390 annonces en ligne ; regarder si les 13 vieilles lignes
     `error/pending` ont été remplacées (sinon : nettoyage à décider) ;
  4. durée de l'étape `phase1 sync_raw update` : ~+4 min attendues (81 requêtes à 1/s + marge).
  ⛔ Si `REFUS` : rien n'est effacé (c'est le but) ; lire la raison au journal avant toute chose.
- Reste à faire : une alerte au moniteur sur `[passerelles] REFUS` (comme `data.miroir_filet`) ; afficher
  `pending` comme « en attente » et non « erreur » ; commiter `normalize_source.py` et **seulement mon morceau** de
  `sync_raw.py` (l'autre session a une modification en cours dans le même fichier).

**0b — Les « 9 portails en erreur » ne viennent PAS de Hektor.**
- Les 13 lignes `is_error` de `app_mandat_broadcasts_current` (9 annonces actives) sont `current_state = error`,
  `export_status = pending`, datées du 05/06 au 24/10.
- Pour ces 9 annonces, la liste de Hektor (au 26/10) donne **tous les portails `exported`**, y compris ceux marqués
  en erreur chez nous. Et le miroir local `hektor_annonce_broadcast_state` n'a **aucune** ligne en erreur → d'où
  `has_diffusion_error = 0` partout, ce qui est **juste**.
- Ce sont donc de **vieilles lignes d'erreur restées chez nous** (écrites hors du chemin de nuit, jamais remplacées).
  ⚠ L'auteur exact de ces lignes n'est pas prouvé. ⚠ La maquette affiche « 9 en erreur » : chiffre à retirer.
- Conséquence pour l'écran : le point orange doit se fonder sur ce que dit Hektor (`exportStatus` / `exportWarnings`
  du listing), pas sur ces lignes. Nettoyage à décider (écriture en base → accord).

**0c — Les numéros de passerelles (au 26/10, à reconfirmer après 0a).**
- **etreproprio = 19, paper = 20, superimmo = 21** : UNE passerelle chacune pour **toutes** les agences
  (364 / 364 / 311 annonces).
- Bien'ici et Leboncoin : une passerelle par agence (Bien'ici 6 à 23, Leboncoin 45 à 61) — la carte agence →
  numéro se contrôle avec `phase2/checks/passerelle_par_agence.py` (une fois 0a réparé).

**0d — Le libellé de `paper`** : à demander à Frédéric.

## Lot 1 — La vue Liste (front seulement)

*Feu vert : « vas-y » requis (modification de code existant). Derrière un interrupteur `VITE_APP_ANNONCES_LISTE_V2`,
éteint = rendu d'aujourd'hui à l'identique.*

Ce qui est fait :
- Nouveau rendu de ligne en **grille façon Contacts** dans `MandatsScreen`, branche « Annonces » seulement.
  Colonnes : Bien (photo + nombre de photos, titre, type, type de mandat, « Sous offre / Sous compromis »,
  ville + CP, « À compléter · raison », N° mandat · N° annonce) · Prix (ancien barré, variation, « il y a N j ») ·
  Mandat (bouclier Validé / Non validé / Sans mandat + barre de période) · Négociateur (initiales, nom, agence) ·
  Diffusion (antenne seule) · Actions.
- **Toutes les données sont déjà dans la ligne** (`MandatRecord` / vue `app_dossiers_current`, `select *`) :
  `images_preview_json(_app)`, `price_change_last_old_value`, `price_change_last_detected_at`,
  `mandat_date_debut/fin`, `mandat_type`, `validation_diffusion_state`, `diffusable`, `nb_portails_actifs`,
  `has_diffusion_error`, `commercial_nom`, `agence_nom`, `ville`, `code_postal`. Aucune requête par ligne.
- **Le bouton Action animé** : on garde `buildMandatActionModel` (App.tsx ~8441) et `latestActionRequest` tels
  quels ; seul le **déclencheur** de `MandatActionMenu` (~12638) change de forme (pilule icône + type + état) et
  gagne les animations (respect de `prefers-reduced-motion`). Mêmes tons : neutral / creation / correction /
  rejected. « Sans mandat » devient un bouton en pointillés.
- **Boutons** : réutiliser les règles `.ra` d'`annuaire-contacts-v2.css`. ⚠ Elles sont scopées sous
  `.annuaire-v2` (l. 153-161) → soit poser la classe `annuaire-v2` sur le conteneur, soit recopier les 8 règles sous
  le nouveau scope (préféré : pas d'effet de bord sur l'annuaire).
- **Tri par en-tête** (date d'entrée, prix, fin de mandat, acquéreurs) : aujourd'hui l'ordre est imposé côté serveur
  (api.ts ~6833-6836). ⚠ Le tri « acquéreurs » ne peut être que local à la page (le compte vient d'une RPC par lot).
- Colonne « Vues 30 j » retirée (aucune donnée).
- CSS dans un fichier neuf `annonces-liste-v2.css`, tout scopé.

Ce que ça pourrait casser ailleurs (à contrôler) :
- les **lignes légères** (archives, Vendu/Clos, brouillons) gardent leur bouton « Charger / Ouvrir » ;
- les **lignes provisoires** (création en cours / en erreur, bouton « Retirer ») ;
- le **drilldown des Stats** et les **Priorités** qui changent le titre et filtrent ;
- l'écran **Estimations** (même composant) ;
- la largeur : **1280 × 665 sans défilement horizontal** (écran de Frédéric).

À trancher avant ce lot :
- le bouton **« Modifier »** : la fiche (cockpit) se modifie en ligne ; ce bouton ouvrirait la même fiche que la
  flèche. Le garder (et ouvrir directement la rubrique « Le bien »), ou le retirer ?
- **« Acceptée » en vert pendant 48 h** (proposé, lu sur `processed_at`) : oui ou non ?

### ✅ Lot 1 CODÉ le 03/11/2026 — DORMANT (`VITE_APP_ANNONCES_LISTE_V2` absent = éteint), NON COMMITÉ

Décisions de Frédéric (03/11) : « Modifier » ouvre la fiche sur **Le bien** ; « Acceptée » reste **vert 48 h** ;
on garde **« Paper »**.

Fichiers :
- **`src/AnnoncesListeV2.tsx`** (neuf) : interrupteur, `AnnonceV2Colgroup/Head/Cells/Reperes`,
  `demanderRubriqueAOuverture` / `prendreRubriqueDemandee`. Ne calcule rien de métier : reçoit ce que l'écran calculait.
- **`src/annonces-liste-v2.css`** (neuf) : tout sous `.av3` ; boutons `.ra` recopiés d'`annuaire-contacts-v2.css`.
- **`src/App.tsx`** (+113 / −5, uniquement ces points) : import ; `actionPillState` + `ACTION_PILL_ICON` (même
  priorité que `buildMandatActionModel`) ; `MandatActionMenu` prop `variant="pill"` ; `MandatsScreen` : `listeV2`
  (mode Annonces seulement), classe `av3`, colgroup / en-tête / cellules / repères ; `CockpitDetail` : rubrique
  initiale `prendreRubriqueDemandee() ?? 'synthese'`.

Adaptations faites À LA MESURE (aperçu factice 5196, 1280 × 665) :
- ⚠ Le menu latéral libellé de l'app ne laisse que **909 px** à la liste (la maquette avait un rail d'icônes) :
  le **négociateur passe dans la cellule Bien** (initiales, nom · agence), une colonne de moins.
- ⚠ Des règles anciennes imposent `width: 7.5% !important` aux cellules **par position** → neutralisées sous `.av3`,
  et `thead th:first-child { width: 100% }` pour que la colonne Bien prenne le reste (sinon 159 px).
- ⚠ La fenêtre « Actions disponibles » n'est stylée que sous `.row-actions` → le bouton est enveloppé dans
  `span.row-actions.av3-slot` en `display: contents`.
- Colonnes mesurées : Bien 303 · Prix 106 · Mandat 146 · Diffusion 78 · Actions 276 ; boutons à 1 209 px pour un
  bord à 1 218 ; aucun défilement horizontal.

Contrôles faits : `npm run build` vert (deux fois) ; allumé : « Modifier » → fiche sur **Le Bien** ; flèche → fiche
sur la synthèse ; menu « Actions disponibles » identique à aujourd'hui (Valider · Ajouter, Hektor · Ouvrir) ;
**témoin éteint** (port 5197) : 7 colonnes d'avant, bouton « Action », 0 pilule ; **Estimations** inchangé allumé.
⚠ Non contrôlé : données réelles (le factice n'a que 3 annonces, aucune demande → seul l'état gris « Actions » a été
vu à l'écran) ; animations des autres états ; lignes légères, provisoires et brouillons à l'écran.
⚠ Hauteur des lignes : ~154 px en factice (Contacts : ~96) — à regarder sur vraies données.
**Comparaison avec la maquette (demandée par Frédéric, 03/11), mesurée élément par élément :**
- ⚠⚠ L'ancienne liste peignait en gris TOUT texte de cellule (`.app-shell-modern .listing-table-wrap td span
  { color: #626969 !important }`) : titre, bouclier et **antenne invisible** (gris sur vert), pastilles sans chiffre ;
  et imposait marges (10px !important), fond des lignes, en-tête (#9da0a0, 900) et fond gris de la 1ʳᵉ cellule
  sélectionnée. → bloc « PRIORITÉ » en fin de `annonces-liste-v2.css` (préfixe `.app-shell.app-shell-modern`).
- Après correction, conforme à la maquette : photo 88 × 66 · titre 14,5/700 #222323 · étiquettes 11 px · prix 15/800 ·
  bouclier 11,5/800 coloré · antenne 38 px blanche sur vert + chiffre · boutons 34 px rayon 9 · flèche #c5005f ·
  filet magenta au survol · en-tête #5c6163 / 800 / #fafbfb.
- Pilule élargie **124 → 136 px** (colonne Actions 288) : avec **Inter**, la police de l'app (et de Contacts), « VALIDATION »
  et « À corriger » étaient coupés. Écart assumé : la maquette était en Hanken Grotesk, l'app reste en Inter.
- États colorés vus à l'écran par simulation dans la page de test (bleu « Envoyée », orange « À corriger », rouge
  « Refusée ») : texte entier, rien de coupé ; liste toujours sans défilement à 1280 px (boutons à 1 199 / 1 218).
- Écarts restants, dus à la place : négociateur dans la cellule Bien (nom parfois tronqué), lignes ~100-158 px selon
  le contenu (Bien ≈ 291 px à 1280 avec le menu latéral déplié).

⭐ **03/11, décision de Frédéric (« je ne veux pas une variable ») : la V2 est la liste PAR DÉFAUT.**
`APP_ANNONCES_LISTE_V2` vaut vrai si la variable est ABSENTE ; l'ancien rendu reste dans `MandatsScreen` comme
**secours** : `VITE_APP_ANNONCES_LISTE_V2=false` sur Vercel + Redeploy le fait revenir sans toucher au code.
(Tentative de poser la variable par l'outil : 403 « droits supplémentaires requis » — inutile désormais.)
Vérifié : build vert ; aperçu 5197 SANS variable → nouvelle liste (5 colonnes, 3 pilules, pas de défilement).
En ligne dès le push de Frédéric.
Pour voir en local : configuration d'aperçu `hektor-mock-bienvu-liste-v2` (port 5196, `C:\Hektor\.claude\launch.json`).

## Lot 2 — Le haut de page

*Feu vert : « vas-y » requis.* Volontairement minimal : la barre d'outils et la bande **Stats** restent celles
d'aujourd'hui (masquée par défaut, même ordre). Seuls changements : les onglets **Liste / Publicité** à côté du
titre « Annonces actives » dans la carte de la liste. Peut être fondu dans le lot 1.

## Lot 3 — La vue Publicité (front)

*Feu vert : « vas-y » requis. Dépend de 0a, 0b, 0c et du lot 4.*

- Charger l'état par portail **pour les 50 lignes de la page** : une requête `app_mandat_broadcasts_current`
  `.in('app_dossier_id', …)`.
- Une case par portail si `diffusable = 1` ; sinon une bande « Faire la demande » (négociateur →
  `createDiffusionRequest` `demande_diffusion`, circuit existant) / « Valider et rendre diffusable » (admin →
  geste du Pilotage) / « Créer le mandat » (sans numéro).
- Cocher / décocher = **le chemin existant** de la Console : `saveDiffusionTargets` puis
  `applyDiffusionTargetsOnHektor` (api.ts ~7946 / ~8023). ⚠⚠ `saveDiffusionTargets` fait **DELETE puis INSERT de
  tout le jeu** : il faut renvoyer l'état COMPLET des 5 portails, sinon une case cochée en retire quatre.
  ⚠ `ensureDiffusable: true` force Diffuse : sans effet ici (on n'affiche les cases que si diffusable), à garder en tête.
- État « Envoyé » optimiste jusqu'au retour ; relecture des broadcasts de l'annonce après.
- Cartes de présence par portail et puces « À traiter » : un comptage agrégé (lecture).
- Seule action de ligne : la flèche « Ouvrir la fiche » (décision du 03/11).
- Charge Hektor : un clic ≈ 2-3 requêtes (PATCH Diffuse + add/remove). Pas d'action groupée (retirée de la maquette).

## Lot 4 — Les droits côté serveur

*Feu vert : **accord obligatoire** (backend Render, se déploie seul au push).*

- **La règle de Frédéric (03/11)** : un négociateur coche et décoche ses portails **dès que l'annonce est
  diffusable** (validée + Diffusable coché par un admin).
- Aujourd'hui `/hektor-diffusion/apply` appelle `assert_admin` (admin ou manager, `supabase_admin.py` ~216-224).
  À ouvrir au commercial **à deux conditions** : `diffusable = 1` sur le dossier ET accès au dossier
  (`app_console_can_access_dossier`). Les autres routes (`/validation`, `/diffusable`, `/accept`) restent admin.
- Corrige au passage l'incohérence relevée : la Console s'ouvre pour un négociateur et ses cibles sont enregistrées
  puis refusées (403).

## Lot 5 — Le téléphone

*Feu vert : « vas-y » requis.* `MobileMandatCards` (App.tsx ~39707) : carte photo + prix, bouclier, antenne,
deux gros boutons (Acquéreurs, Ouvrir la fiche) + « ⋯ » ; onglet Publicité : 5 cases ou le bouton de la demande.
⚠ Rendu à part ≤ 1180 px (tablette comprise) ; classes `mobile-list-card` partagées → classe propre.

## Lot 6 — Contrôles (à chaque lot)

- `npm run build` dans `apps/hektor-v1` (jamais `tsc --noEmit`) ; `git checkout -- vite.config.js vite.config.d.ts` après.
- Aperçu `hektor-mock-bienvu` (port 5198) : **1280 × 665**, 768, 390 ; mesure `scrollWidth` (aucun débordement).
- **Témoin inverse** : interrupteur éteint = ancien rendu identique.
- Lot 3 : preuve réelle sur le bac à sable **62774** (cocher puis décocher un portail) — **écriture chez Hektor,
  accord obligatoire**.

## Ordre recommandé

**0 → 1 (+2) → 5 → 4 → 3.** La vue Liste ne dépend de rien ; la vue Publicité attend des données fraîches (0a), les
numéros de passerelles (0c) et les droits (4).

## 03/11 soir -- bouton Action redessine, et lot 4 (serveur) ecrit

- **Bouton Action = « sceau de suivi »** (`57e5e4f`, NON pousse) : 112 px au lieu de 126, hauteur 34. L'anneau autour de l'icone = le chemin de la demande en 3 crans (1 = envoyee, 2 = en cours / a corriger, plein = decision). Memes tons, memes libelles (`actionPillState`). Chevron retire. Colonne Actions 264 px. Vu dans l'apercu (7 etats), menu toujours ouvert au clic, 0 defilement a 1280.
- **Lot 4 serveur** (`dd59dc5`, NON pousse -- Render se deploie au push) : `/apply` et `/persist-state` ouverts au negociateur si l'annonce est diffusable ET dans son perimetre ; `ensureDiffusable`, validation et diffusable ignores pour lui. Epreuve hors ligne 10/10.
- Reste : lot 3 (onglets Liste / Publicite + cases), essai reel sur 62774 avec accord.

## 03/11 soir (suite) -- lot 3 Vue Publicite CODE (`19baf05`, NON pousse)

- **En ligne avant** : `0d1f608` sert sur Render (`/health`) et Vercel (READY) -> les droits negos (lot 4) sont ACTIFS.
- **Onglets Liste / Publicite** dans l'en-tete de la carte (grille passee a 3 colonnes). Onglet retenu par navigateur (localStorage, en try/catch).
- **Cases** LB BI PA EP SI (56 px chacune) : en ligne = `portails_resume` de la ligne ; erreur = `app_mandat_broadcasts_current.is_error` (`loadPortailsEnErreur`, une lecture par page).
- **Un clic** = `saveDiffusionTargets` avec UNE cible (numero : 19/20/21 communs, sinon `previewDefaultDiffusionTargets` pour BI/LB) puis `/apply` ensureDiffusable=false -> UN ordre chez Hektor. La case ne change qu'apres la reponse ; puis `persist-state` (portails_resume, nb). Refus affiche sur la case.
- **Non diffusable** : bande « Faire la demande » / « Corriger » / « Demande envoyee » ; sans mandat ou fiche legere : texte.
- **Fenetre Diffusion existante** retouchee (2 points) : repli 19/20/21 au lieu du NOM du portail comme numero (defaut ancien) ; completee par les cibles d'agence manquantes (avant : seulement si aucune cible).
- **Bouton Action** : `td span { margin-top: 4px }` (styles.css l. 5001) + gris `!important` decalaient le texte et eteignaient le sceau -> annules. 116 px, sceau 26, 70 px de texte (mesure : « A corriger » 60, « ANNULATION » 60) ; « Sans mandat » en 10,5 px.
- **Controle** : build vert ; apercu 1280 px sans defilement ; clic -> envoi (bloque) -> echec affiche, fiche NON ouverte ; telephone inchange (cartes a part).
- ⚠ **L'apercu local ecrit par `hektor_diffusion_writeback.py`** (api locale) : NE PAS cliquer une case en mode local sur un vrai numero de dossier.
- ⚠ **Reserve Leboncoin** : des annonces sont encore publiees sur les ANCIENNES passerelles LB 35-44 alors que la table d'agence donne 45-61. Decocher LB sur l'une d'elles enverrait le retrait au mauvais numero. A eprouver sur 62774, puis mesurer combien sont concernees.
- **Reste** : push ; essai reel (cocher puis decocher PA sur 62774) avec accord ; alerte REFUS au moniteur ; telephone (lot 5).

## 03/11 18:00 -- ESSAI REEL de la vue Publicite : VERT (accord de Frederic)

- **En ligne** : `79cad52` (contient `19baf05`) sur Vercel READY ; Render sur `0d1f608` (lot 4).
- **Cible** : 62774 est CLOS (hors liste) et le seul essai diffusable (62963) n'a pas de mandat -> Frederic a choisi une VRAIE annonce : **61713 / mandat 18433, Local commercial, Courpiere**, validee, diffusable, sur Bien'ici seul, 0 cible avant.
- **Par l'ecran, dans son Chrome (compte admin)**, vue Publicite, case Paper :
  - cocher : « envoi » puis **en ligne en 9 s** ; fiche NON ouverte ; base : cible 20/paper enabled au nom de Frederic, `portails_resume` = `bienicidirect, paper`, validation `valide` et diffusable `1` INCHANGES ; **Hektor relu a part** (GET ListPasserelles) : passerelles 11 bienicidirect + **20 paper**.
  - decocher : « retrait » puis **absente en 7 s** ; base : `bienicidirect`, 1 portail ; **Hektor relu** : 11 bienicidirect seul. -> RETOUR EXACT a l'etat d'avant.
- Reste en base une ligne cible `20/paper disabled` (trace du geste, sans effet).
- ⚠ **Pas encore eprouve** : un clic par un NEGOCIATEUR (le lot 4 en ligne le permet) ; Bien'ici / Leboncoin (numero d'agence ; Courpiere = 11) ; la reserve des anciennes passerelles LB 35-44.
- Onglet de Frederic remis sur « Liste » apres l'essai.

## 03/11 18:15 -- ESSAI REEL LEBONCOIN : VERT, et la reserve des anciens numeros TOMBE

- **61713 (Courpiere), par l'ecran dans le Chrome de Frederic** : Leboncoin coche -> en ligne en **11 s** ; Hektor relu a part : passerelle **46 leboncoinDirect** (compte 496094) + 11 bienicidirect ; base : `bienicidirect, leboncoinDirect`, validation/diffusable intacts. Decoche -> absente en **9 s** ; Hektor : 11 seul ; base : `bienicidirect`. RETOUR EXACT.
- Le numero vient de `app_diffusion_agency_target` (Courpiere : LB 46, BI 11) -- les deux confirmes par Hektor.
- ⭐ **Reserve « anciennes passerelles LB 35-44 » : TOMBEE.** `hektor_broadcast` garde 139 lignes sur 35-44, mais ces passerelles n'ont plus ete relues depuis le 07/07 au 06/10 (45-61 : le 26/10). Hektor relu sur 3 annonces de ces vieilles listes (63167, 62985, 61397) : publiees sur **51, 54, 52**, exactement les numeros de la table d'agence (et BI 8, 4, 17 aussi). Les lignes 35-44 sont des RESTES non purges, pas des publications.
- Note (non traite) : ces restes peuvent encore nourrir `app_mandat_broadcasts_current` ; sans effet sur les cases (elles lisent `portails_resume`). A regarder si un « en erreur » fantome apparait.
- Reste en base une ligne cible `46/leboncoinDirect disabled` (trace).
- ⚠ Toujours pas eprouve : un clic par un NEGOCIATEUR.

## 03/11 soir -- vue Publicite, 2e passe : cartes de presence cliquables (`ad4d555`, NON pousse)

- Retour de Frederic : « la vue publicite ne correspond pas encore a la maquette, il manque les stats en haut cliquables, affine le design ».
- **6 cartes « Presence sur les portails »** (site GTI + LB BI PA EP SI) : en ligne / diffusables, barre, « N absentes ». `loadPresencePortails` : memes filtres que la liste (sauf le filtre de carte et `diffusable`), lecture par lots de 1 000 sur `app_dossiers_current`.
- **Clic = filtre de la liste**, cote serveur : portail -> filtre facultatif NEUF `absentDe` (`diffusable = 1` ET `portails_resume` sans ce portail ; aussi dans le filtre local, « un filtre est pose » et le refus des index legers) ; site GTI -> le filtre Diffusable existant (`non_diffusable`). Barre noire « Retirer le filtre », page remise a 1.
- **Design de la maquette** : en-tetes de portail en pastilles de couleur, cellule Bien courte (type · N° · ville, photo 96x72), signaux sous le prix (Mandat echu / Encore en ligne · statut / Visible nulle part), cases bord 2 px rayon 8, bande au bouton plein (« Faire la demande », « En attente » grise, « Corriger »), textes de la maquette.
- **Chiffres attendus en ligne** (SQL du 03/11, liste active 705) : GTI 438 diffusables (267 non) ; LB 270 · BI 218 · PA 291 · EP 291 · SI 289. LB et BI = les Stats existantes.
- Controle : build vert ; apercu 1280 px : 6 cartes sur UNE ligne, 0 defilement ; carte LB -> barre « Diffusables absentes de Leboncoin · 2 », liste 3 -> 2, « Retirer le filtre » -> 3.
- ⚠ **Le commit a d'abord embarque 16 morceaux d'une autre session** (FicheMandatManquante, fichier non suivi) -> defait (`reset --soft`), mes seuls morceaux re-indexes, commit `ad4d555` construit SEUL dans une copie a part : vert.
- ⚠ Non fait : la requete `absentDe` n'a tourne qu'en local (mode sans base) -- a verifier en ligne apres le push (comparer aux chiffres ci-dessus). Bandes admin (« Valider et rendre diffusable ») : non, le geste reste « Faire la demande » pour tous.

## 03/11 soir -- cartes de presence VERIFIEES EN LIGNE (`2345012`, bundle index-DecvJ--t.js)

- Lu dans le Chrome de Frederic (lecture seule, aucun clic de case) : cartes **438 · 270 · 218 · 291 · 291 · 289** = EXACTEMENT le SQL ; 6 sur une ligne a 1280 px ; 0 defilement.
- Filtre Paper : **147** annonces, aucune de la page sur Paper (requete `absentDe` juste cote serveur), 1 s. Filtre Site GTI : **267**, toutes en bande. « Retirer le filtre » : 705.
- 2 lignes du filtre Paper en bande « Pas de mandat » : 63419 et 63339, diffusable = 1 SANS numero de mandat (fiches « [Sans titre] », type « 0 ») -- comportement voulu. ⚠ Le libelle « Type 0 » vient de `libelleTypeBien` (aussi dans la Liste) : a regarder a part.
- Onglet de Frederic remis sur « Liste ».

## 03/11 soir -- TITRES DES ANNONCES : audit fait, SORTI en chantier a part (decision de Frederic)

- **Mesure (705 actives)** : 179 « [Sans titre] <n° dossier> » (fabrique par `phase2/pipeline/view_generale.py` l. 283 quand Hektor n'a ni `titre` ni `texte_principal_titre`) -- 122 sans mandat non diffusables, 29 avec mandat non diffusables, **19 diffusables deja EN LIGNE** (ex. 59109, 52931, 52231). 54 titres tout en MAJUSCULES, 86 de plus de 70 caracteres.
- **Hektor relu (API, lecture seule)** : 59109 et 52931 ont `textes[].titre` = `" "` / `""` alors que la description est remplie ; temoin 61713 a son titre. -> le titre n'a JAMAIS ete saisi, notre synchro ne perd rien.
- **Pistes proposees, rien code** : A titre de secours a l'affichage (« Maison a <ville> », italique) ; B carte « Titre a saisir » (179) pour faire corriger par la fiche ; C titre redige depuis la description, valide par le nego, envoye chez Hektor (ecriture Hektor) ; D casse normale pour les titres TOUT EN MAJUSCULES (formule prototypee : minuscules + majuscule en tete et apres « ! . – », sigles T2/F3/GTI gardes, villes recapitalisees ; limites : accents absents non restituables, lieux hors liste, affichage seul).
- ⛔ **Frederic, 03/11 : « laisse, c'est un chantier a part ».** Ne pas le reprendre dans ce chantier.

## 03/11 soir -- « version retenue » codee : vignette Bien + colonne Mandat + TELEPHONE (lot 5) (`09495a3`, non pousse)

- Iterations de Frederic : colonne Prix remise « comme avant » (`bc4b686`) ; ecarts > x3 masques (2 cas, erreurs de saisie dans Hektor) ; plusieurs maquettes (pistes A/B, A1-A4, portail/CRM/qualite, ligne entiere A/B) ; decision finale : photo NUE (nombre de photos seul), STATUT a cote du type de bien, TYPE de mandat dans la colonne Mandat, ville en surtitre, negociateur en entier.
- Bureau : `BienPrixCells` (Liste) reecrite ; colonne Mandat = bouclier + N°, type (Exclusif magenta), periode ; pastille « fiche mandat manquante » (autre session) gardee. Lignes 126 px a 1280 (156-178 avant).
- Telephone : `AnnonceCarteMobile` (AnnoncesListeV2.tsx), branchee dans `MobileMandatCards` pour l'ecran Annonces seulement (prop `vignetteV2`). Estimations / Suivi inchanges.
- Reste : vue Publicite AU TELEPHONE (onglets + cases) pas faite ; la cellule Bien de la vue Publicite (bureau) garde son ancien dessin (type · N° · ville) ; essai par un negociateur.

## 04/11 matin -- CONTROLE DU CORRECTIF DES PASSERELLES (1er run avec APP_PASSERELLES_V2=1) : VERT, + 1 defaut trouve

1. **Journal** `logs/scheduled/quotidien_2026-11-04_04-00-02.log` : `[passerelles] COMPLETE : 37 passerelle(s), 1620 diffusion(s) ecrite(s), 0 sans numero d'annonce` (2 fois : update + rejeu), **aucun REFUS** ; run termine `exit 0` a 06:19:22.
2. **`data/hektor.sqlite`** : `hektor_broadcast_listing` = **1 600 lignes, toutes du 04/11 04:30:50**, 393 annonces ; Bien'ici 2-5 **revenus** (27 + 20 + 20 + 18) ; 0 passerelle sans nom ; les 139 restes LB 35-44 **purges** ; 1 597 exported + 3 pending.
3. **Supabase** `app_mandat_broadcasts_current` : 333 annonces ; **comparaison annonce par annonce avec la lecture de la nuit : 333 / 333 IDENTIQUES** (memes portails, 0 en trop). Bien'ici en ligne **213 -> 309**. Les 60 annonces de Hektor absentes de Supabase sont toutes **« Vendu »** pour l'app (`app_historical_annonce_index_current`) -- hors liste active, mais Hektor les compte encore DIFFUSEES (surtout Etreproprio + Paper ; 59 ventes, n° 21xxx-29xxx et 4 recents) : ⚠ a regarder avec Frederic (references « vendu » des portails ?), rien conclu.
4. **Duree** `phase1 sync_raw update` : 04:00:03 -> 05:25:23 = **85 min 20 s** (78-80 min les 3 nuits d'avant) : **+5 min**, attendu ~+4.
- ⚠⚠ **DEFAUT TROUVE (non corrige)** : les 13 vieilles lignes « error » NE SE REMPLACENT PAS. 12 lignes / 8 annonces (18680, 61680, 61757, 62171, 62817, 62881, 63193, 63234) sont **« error » dans Supabase alors que Hektor les dit « exported » cette nuit** (et notre `hektor_annonce_broadcast_state` local aussi). Cause lue dans `phase2/sync/push_upgrade_to_supabase.py` l. 1617-1629 : l'envoi ne remplace les lignes d'une annonce que si l'ensemble de cles (dossier, portail, commercial) change -- **un changement d'ETAT n'est jamais envoye**. Effet ecran : 8 annonces ont des cases ORANGE « en erreur » a tort dans la vue Publicite. Remede propose : ajouter `current_state` (ou `export_status`) a la cle comparee (et au `select` distant). = modification du run de nuit -> « vas-y » de Frederic.
- Rappel : les 3 « error » du jour sont des **pending** (61452, 62495, 63232, Leboncoin, nego POMBAR) classes en erreur par `derive_broadcast_state` -- a afficher « en attente ».
- Hors chantier, note : l'etape « phase2 sync Matterport links » echoue depuis le 03/11 (HTTP 401 Matterport) -- un acces refuse, pas lie aux passerelles.

## 04/11 -- DEFAUT DE L'ENVOI CORRIGE : l'etat des passerelles entre dans la cle (`push_upgrade_to_supabase.py`, accord « audit d'abord puis vas-y »)

- **Audit** : la liste envoyee vient de `hektor_annonce_broadcast_state` (`export_app_payload.py` l. 722-740, fraiche chaque nuit) ; la table `app_mandat_broadcast_current` de `phase2.sqlite` (perimee, 02/11) ne sert PAS a l'envoi. Chaque nuit, toutes les annonces diffusees sont « changees » (leur etat est reecrit a chaque run) donc toutes examinees ; mais la comparaison (dossier, portail, commercial) ignorait l'etat -> jamais de remplacement pour un simple changement d'etat. Voisins verifies : `--full-rebuild` (reecrit tout), `push_single_annonce_to_supabase.py` (efface + reecrit le dossier), purge / suppression : non concernes.
- **Remede** : `broadcast_compare_keys()` (cle + `current_state`), utilisee pour les deux cotes ; le `select` distant lit `current_state`. Mecanisme de remplacement inchange.
- **Epreuve** (`scratchpad/epreuve_cle_etat_passerelles.py`, lecture seule, LE code) : 14 014 ids demandes, 1 471 lignes relues (pas de coupure : paquets de 500 ids) ; remplaces avant 0 / apres **8 = les 8 annonces** ; temoin inverse 0.
- ⚠ Correction de mon propos : la « coupure a 1 000 lignes » n'existe que si un paquet de 500 ids depasse 1 000 lignes -- vrai dans mon 1er essai (333 ids), PAS dans l'envoi reel. `fetch_rows_by_ids` ne pagine toujours pas : un risque dormant si un paquet grossit (note, non traite).
- ⏰ **Controle de la nuit du 05/11** : `app_mandat_broadcast_current` ne doit plus porter que les vraies attentes (`error` = `pending` chez Hektor, 3 au 04/11) ; les 12 lignes des 8 annonces doivent etre `broadcasted`, datees du 05/11.
- Retour arriere : revenir sur le commit (les lignes deja corrigees restent justes).

## 04/11 -- vue Publicite AU TELEPHONE codee (non poussee)

- Logique partagee : `usePubliciteAnnonces` (App.tsx, avant `MandatsScreen`) = le code du 03/11 deplace tel quel ; `MandatsScreen` et `MobileMandatCards` l'appellent.
- Telephone : onglets, cartes de presence defilantes + filtre, cartes d'annonce en mode Publicite (`AnnonceCarteMobile` prop `pub`) avec 5 cases de 44 px ou la bande.
- Piege : un element de grille sans `min-width: 0` -> la rangee defilante elargissait la liste a 734 px (corrige).
- Reste : essai reel d'une case AU TELEPHONE (meme code que le bureau, deja eprouve sur 61713) ; essai par un negociateur.

## 04/11 -- antenne lisible (bureau) + les deux fenetres au telephone (non pousse)

- Antenne (`5b718ed`) : le span de l'antenne etait coupe par `.listing-table-wrap td span { overflow: hidden }` -> chiffre et erreur tronques ; coupure levee, pastilles agrandies (chiffre vert sur blanc, erreur orange « ! »).
- Fenetres au telephone (`modales-telephone.css` + ajouts `.rq-mobile` dans App.tsx) : panneau du bas, en-tete compact, barre fixe ; demande = onglets du type, suivi 3 etapes, reponses rapides, carte de resume reparee (ecrasee a 56 px) ; statut = pastilles + description, grille du formulaire reparee (rangee a 2 px), champs 46 px, avertissement « Clos ».
- Non fait (de la maquette) : blocs repliables du formulaire de statut ; libelle du bouton (« Envoyer vers Offre » garde) ; la pastille choisie ne defile pas seule dans la rangee.
- ⚠ Non verifie : l'effet d'une cloture sur l'offre / le compromis (vu sur l'essai du 21/10, pas retrouve comme regle dans le code) -- l'avertissement ne l'affirme pas.

## 12/11 -- PASSERELLES DE NOUVEAU FIGEES DEPUIS LE 06/11 : cause trouvee, correctif CODE (`normalize_source.py`, non commite)

- **Constat** : `hektor_broadcast_listing` arrete au 05/11 04:28 ; journaux du run : « COMPLETE » les 04 et 05/11 puis « REFUS : pages de 2/3 passages differents » chaque nuit du 06 au 12/11. Aucune alerte (le moniteur ne surveille pas les passerelles). Effet dans l'app : 16 annonces « en ligne » que Hektor a retirees (8 sous offre, 1 sous compromis, 7 actives), 12 actives mises en ligne chez Hektor et inconnues de l'app.
- **Cause** : `raw_api_response` garde UNE ligne par page, mise a jour en place. La liste a RETRECI (81 pages le 05/11, 80 le 06/11, 78 le 12/11) : les pages 79-81 des vieilles nuits ne sont plus remplacees et se melangent au passage frais -> le garde-fou du 03/11 refuse a vie. Second verrou mort aussi : `broadcast_bilan_pages` lisait le `total` de la vieille page 81 (1 601 au lieu de 1 551). Les epreuves du 03/11 n'avaient vu qu'une liste stable ou qui grandit.
- ⚠ L'`id` d'une page n'est PAS chronologique (une page relue garde son id) : la vieille page 81 du 05/11 a l'id le plus grand.
- **Correctif** : `broadcast_pages_dernier_passage()` -- seules les pages du dernier passage (reconnu par `fetched_at`) ; les 4 lecteurs du brut `list_broadcasts` y passent (garde-fou v2, bilan/total, deballage, ancien garde-fou). Interrupteur eteint : toutes les pages, comme avant.
- **Controle (vrai code, copie en memoire, base reelle en lecture seule)** : allume -> garde-fou OK (79 pages), total 1 551, table 1 601 lignes du 05/11 -> **1 551 lignes du jour**, par portail BI 296 · LB 265 · Paper 347 · EP 347 · SI 296, **0 en trop / 0 manquante** face a Hektor, tout `exported`. Temoins : ancien code allume = le REFUS exact des journaux ; interrupteur eteint = identique avant/apres (et vide la table : il doit rester allume).
- Le correctif du 04/11 (etat dans la cle de l'envoi) est, lui, efficace : 0 fausse erreur dans Supabase.
- Reste : une alerte du moniteur sur ce refus ; les 60 ventes encore diffusees par Hektor sur Paper / Etreproprio (sujet Hektor).
