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

Pour allumer en production : variable Vercel `VITE_APP_ANNONCES_LISTE_V2=true` + Redeploy (Frédéric).
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
