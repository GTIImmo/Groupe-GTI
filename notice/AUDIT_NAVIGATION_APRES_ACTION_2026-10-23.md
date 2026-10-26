# Audit — retirer la modale « Suivi de l'action » : la navigation et les rafraîchissements qui manquent

**23/10/2026 · audit en lecture seule, rien n'a été modifié.**
Demande de Frédéric : *retirer la modale pour tous (négociateurs, admin, manager). Elle ne garde un rôle
que parce que l'ergonomie n'est pas celle d'un logiciel normal. Après une création, l'objet doit s'ouvrir tout
de suite (il est déjà chez nous) ; après une modification, l'écran doit se rafraîchir tout seul. Les workers
Hektor sont devenus des mises à jour en arrière-plan.*

> ⚠ Les numéros de ligne de `App.tsx` **bougent** : une autre session y a fait 3 commits pendant cet audit
> (⑧, 16:47 → 17:09). Chaque renvoi porte aussi le **nom de la fonction** : c'est lui qui fait foi.

---

## 1. Ce qu'est la modale, et ce qu'elle porte vraiment

`HektorActionStatusPopup` (App.tsx ~9195) est **de l'affichage pur** : elle n'écrit rien en base et ne
commande aucun worker. Elle est montée à deux endroits (mobile ~22741, bureau ~23720).

**Qui la voit** (règle d'accès de la base `app_console_job_select_scope`, mesurée) :
- admin / manager : les travaux de **tout le monde** ;
- négociateur : les siens, plus les gestes d'annonce des biens auxquels il a accès.

Le poll interroge toutes les 5 s les travaux `pending`/`running` (`loadActiveHektorActionJobs`, api.ts ~10920).
Il **ne filtre pas l'auteur**.

**Ce qu'elle porte, en plus de l'affichage :**

| # | rôle | où |
|---|---|---|
| 1 | le bouton **« Ouvrir le détail »** après la création d'une annonce : **le seul chemin pour ouvrir l'annonce créée** | `openHektorActionAppDossier` (~16071) |
| 2 | l'avertissement **« N photos partiront dès que Hektor aura rendu le numéro, ne fermez pas cet onglet »** | dans la modale, l. ~9255 |
| 3 | le seul signe, pour un **négociateur**, que l'action est finie ou a échoué (l'écran Santé est réservé à l'admin) | — |

⭐ **La modale n'est PAS ce qui fait marcher les choses.** Le suivi des travaux (état `hektorActionJobs` et
poll de 5 s) en est **indépendant**, et **cinq mécanismes en dépendent : ils doivent rester** :
1. le verrou anti-double action sur une annonce (`activeAdminAnnonceJobIds`) ;
2. le masquage de la ligne en cours de suppression (`deletingAppDossierIds`) ;
3. l'état « préparation » des fiches archive, Vendu/Clos et brouillon (`preparingArchiveDetailIds`, `lightweightDetailJob`) ;
4. **la file des photos choisies à la création et le scan d'estimation** (effets ~14168-14298) ;
5. le `beforeunload` quand des photos attendent.

⚠ **Le piège n° 1 du retrait** : l'effet qui retrouve la fiche d'une annonce créée (`hektorActionLinkedDossiers`,
~14087) lit `visibleHektorActionPopupJobs`, c'est-à-dire **la liste de la modale**, pas `hektorActionJobs`.
Il faut le **rebrancher** ; sinon la file des photos de création ne retrouve plus son dossier.

---

## 2. Ce qui est DÉJÀ instantané (rien à faire)

| geste | pourquoi c'est déjà bon |
|---|---|
| modifier une annonce | `editAnnonceOptimistic` → événement `hektor:annonce-updated` → rechargement immédiat. Le travail Hektor naît **10 min plus tard** (balayage, debounce 600 s) |
| modifier un contact | `editContactOptimistic` → `hektor:contact-updated`, même schéma |
| modifier une recherche | `editSearchOptimistic` → `hektor:search-updated`, plus des relectures à 25 / 55 / 90 s après le retour de Hektor |
| archiver / réactiver un contact | patch local de l'annuaire (`handleOptimisticContactArchive`) |
| supprimer un contact | retrait local (`handleOptimisticContactDeleted`) |
| supprimer une annonce | retrait local des listes et fermeture de la fiche |
| documents (ajouter / supprimer / préparer) | le panneau a son propre état « en cours » et relit toutes les 8 s |
| photos (ajouter / supprimer / couverture / réordonner / masquer) | le panneau a ses propres relectures (9 s, 22 s, 25 s…) |
| fin de n'importe quel travail | rechargement général +600 ms si le travail concerne l'écran affiché (`jobConcernsThisScreen` ~13939) |

---

## 3. LA MESURE QUI CHANGE TOUT : nos numéros sont connus AU CLIC

Interrupteurs en base (mesurés le 23/10) : `c9_annonce_nait_dans_app`, `annonce_nait_complete`,
`annonce_saisie_gardee`, `contact_nait_complet`, `affaire_nait_complete`, `annonce_retour_controle` et
`contact_retour_controle` sont **tous sur `on`**.

| création | ce que porte le travail **au clic** | preuve |
|---|---|---|
| **annonce** | `payload_json.app_dossier_id` = **notre numéro** (10000001, 10000006, 10000009) | 3 dernières créations |
| **contact** | `payload_json.app_identite` = **notre numéro ≥ 20 000 000**, et la ligne est **déjà dans `app_contact_current`** au même instant | lecture de `app_create_contact_optimistic` : `nextval('app_contact_identite_seq')` puis `insert into app_contact_current` |

⛔ **Mais le front n'utilise jamais ce numéro.** « Ouvrir le détail » cherche l'annonce **par le numéro de
Hektor** (`hektorCreatedAnnonceId`). Il attend donc le retour de Hektor, alors que l'annonce existe chez nous
depuis la première seconde. Les créations de contact ne lisent aucun numéro.

Durées réelles sur 30 jours (médiane / 9ᵉ décile) : création d'annonce **59 s / 141 s**, de contact
**15 s / 18 s**, changement de statut **55 s / 70 s**, envoi de photo **755 s / 1 446 s**.
**C'est cette attente que la modale fait patienter. Avec notre numéro, il n'y a plus rien à attendre.**

---

## 4. Le tableau de l'audit — objets × gestes

Légende : ✅ déjà bon · 🔧 correctif proposé (§5) · ⏳ attend vraiment Hektor (indicateur dans l'objet, §5-C)
· — sans objet · ❔ non mesuré.

|  | créer | modifier | supprimer / archiver | lire / remonter |
|---|---|---|---|---|
| **annonce** | 🔧 **A1** | ✅ | ✅ supprimer · 🔧 **B1** archiver, désarchiver | ✅ (préparer archive / historique / brouillon : état en ligne déjà là) |
| **statut d'annonce, négociateur, activation d'un brouillon** | — | 🔧 **B1** | — | — |
| **contact** | 🔧 **A2** | ✅ | ✅ | ✅ (relecture à l'ouverture, silencieuse) |
| **recherche** | 🔧 **A3** | ✅ | 🔧 **B2** | ✅ |
| **relation (mandant)** | 🔧 **A4** (créer, lier) | 🔧 **A4** | 🔧 **A4** (délier) | — |
| **transaction** (offre, compromis, vente) | 🔧 **F2** (voir §8) | 🔧 **F1 / F2** | 🔧 **F1** | 🔧 **F2** (rubrique Affaires) |
| **mandat** | ⏳ **C1** (numéro PROTEXA via Hektor) | ⛔ fermé par décision (⑦-7) | 🔧 **B1** (clôture via le statut) | — |
| **document / photo** | ✅ panneaux · ⏳ **C2** photos de la création | ✅ | ✅ | ✅ |
| **Matterport** | — | ⏳ **C3** | ⏳ **C3** | — |
| **RDV / visite** | ✅ (§8) | ✅ | ✅ | ✅ (bon de visite = impression, rien n'est écrit) |
| **demandes** (diffusion, baisse, annulation) | ✅ (§8) | ✅ correction | ✅ refus · ⏳ **F6** acceptation d'une annulation | — |
| **documents générés / signatures** | 🔧 **F4** avis de valeur · ⏳ **F5** cadastre, mandat, avenant | — | 🔧 **F3** annuler une signature | 🔧 **F3** relancer |

---

## 5. Les correctifs proposés

### A — Créations : ouvrir l'objet créé TOUT DE SUITE, avec notre numéro

| | geste | aujourd'hui | proposé |
|---|---|---|---|
| **A1** | créer une annonce (`handleCreateDraftAnnonce`) | la fenêtre de saisie se ferme ; rien ne s'ouvre ; l'annonce n'apparaît en liste qu'au rechargement de fin de travail (≈ 1 min) | ouvrir **la fiche** par `payload_json.app_dossier_id`, **et** recharger la liste tout de suite. La fiche est déjà remplie (8a pièce 2 : 116 champs sur 116 à 1,3 s) |
| **A2** | créer un contact (`HektorContactIdentityForm`, mode create, ~38440 ; hôtes : annuaire, mobile, agenda) | la fenêtre se ferme ; rien ne s'ouvre ; la ligne « En création… » n'est pas cliquable | ouvrir **la fiche contact** par `payload_json.app_identite` (≥ 20 M) et recharger l'annuaire. ⚠ Depuis **l'agenda**, il faut probablement plutôt **rendre le contact à la saisie du RDV** que naviguer : à trancher |
| **A3** | ajouter une recherche (`ContactSearchModal`) | la fenêtre se ferme ; la recherche n'apparaît qu'au rechargement suivant | recharger tout de suite les recherches de la fiche ouverte. ❔ Une recherche a-t-elle un numéro chez nous au clic ? **Non mesuré** : à vérifier avant de promettre plus |
| **A4** | mandant : créer, lier, modifier, délier (`HektorMandantContactForm`, `…EditForm`) | le formulaire se ferme ; le bloc `MandantsEnCreation` ne se recharge qu'au changement d'annonce | recharger le bloc des mandants de la fiche tout de suite |

### B — Changements d'état : l'écran doit refléter le geste tout de suite

Ces gestes sont **déjà écrits chez nous au clic** (RPC `*_optimistic`), mais l'écran ne se recharge pas : il
attend la fin du travail Hektor (≈ 30 s à 2 min).

| | geste | proposé |
|---|---|---|
| **B1** | archiver / désarchiver une annonce, changer le statut (y compris clore), affecter un négociateur, activer un brouillon | après le clic : rechargement immédiat de la fiche et des listes (le même événement `hektor:annonce-updated` que la modification). ⚠ **Activer un brouillon n'est PAS optimiste** (insertion directe) : un état « activation en cours » **dans la fiche**, à la place |
| **B2** | supprimer une recherche | la retirer de la fiche tout de suite, comme on le fait déjà pour un contact supprimé |

### C — Ce qui attend VRAIMENT Hektor : un indicateur DANS l'objet, pas une modale

| | geste | pourquoi on attend | proposé |
|---|---|---|---|
| **C1** | numéro de mandat automatique | le numéro vient de Hektor / PROTEXA | dans la fiche, le champ affiche « numéro en cours d'attribution… », puis se remplit à la fin du travail (le rechargement existe déjà) |
| **C2** | photos choisies à la création d'annonce | l'envoi d'une photo exige le numéro Hektor de l'annonce | une **bannière dans la fiche** de l'annonce neuve : « 3 photos en attente d'envoi — ne fermez pas cet onglet ». On garde le `beforeunload`. ⭐ **La vraie solution** serait de déposer les photos chez nous dès le clic et de laisser le **worker** les envoyer après la création : plus rien ne dépendrait de l'onglet. Mais c'est un changement du worker, un chantier à part |
| **C3** | Matterport (mettre en ligne, hors ligne, archiver, réactiver) | aucune écriture chez nous | le bouton affiche « en cours… » jusqu'à la fin du travail |

### D — Les échecs : la cloche existe déjà, avec deux trous

> ⛔ **HORS PÉRIMÈTRE — décision de Frédéric du 23/10 : « la question est juste de la navigation et du
> front ».** D touche le worker : il est **noté pour mémoire, pas proposé**.

Le worker écrit déjà chaque échec dans la **cloche** (`notifyJobFailureBestEffort`, console_job_worker.js ~19010).
C'est le bon canal pour remplacer la modale. Deux trous :

| | trou | proposé |
|---|---|---|
| **D1** | la cloche va au **négociateur du bien**, pas à **celui qui a cliqué** (chaîne : charge du travail → négociateur du dossier → adresse de repli). Si Pauline agit sur le bien d'un négociateur et que ça échoue, **c'est le négociateur qui est prévenu, pas elle** | prévenir **aussi** l'auteur (`requested_by`) |
| **D2** | ces types **ne préviennent personne** : `matterport_*`, `sync_hektor_photos`, `unlink_hektor_mandant`, `exit_hektor_draft_annonce`, les `prepare_*` | les ajouter à `JOB_TYPES_A_NOTIFIER`, avec un libellé |

D1 et D2 touchent **le worker** : il faut un « vas-y », puis redémarrer **les 4 services**, file vide.

### E — Le retrait lui-même

1. retirer les **deux** montages de `HektorActionStatusPopup` ;
2. **garder** l'état `hektorActionJobs` et le poll de 5 s (les cinq dépendances du §1) ;
3. **rebrancher** l'effet `hektorActionLinkedDossiers` sur `hektorActionJobs` (le piège n° 1) ;
4. le faire **derrière un interrupteur** (`app_setting`, par ex. `suivi_action_modale` = `on`/`off`). On
   coupe, on regarde, on peut revenir en arrière en une ligne.

---

## 6. Ce que ça pourrait casser ailleurs

- **Les photos de la création** : si on coupe le suivi des travaux **en même temps** que la modale, elles ne
  partent plus. D'où E-2 et E-3. **Ne retirer que l'affichage.**
- **L'admin ne voit plus en direct les gestes des négociateurs.** C'est voulu ; il garde l'écran Santé.
  Mais tant que D1 n'est pas fait, **un admin qui agit n'est pas prévenu de son propre échec.**
- **Les travaux du balayage 10 min plus tard** (`update_*` sans auteur) : `jobConcernsThisScreen` les traite
  comme « me concernent » et **recharge l'écran ouvert à ce moment-là**. C'est déjà le cas aujourd'hui.
  Mais la modale ne sera plus là pour expliquer ce rafraîchissement surprise. ❔ **Non mesuré** : ce
  rechargement fait-il perdre une saisie en cours, le défilement ou la sélection ?
- **A1 / A2 ouvrent une fiche par NOTRE numéro.** Il faut vérifier que `loadDossier…` et la fiche contact
  acceptent un numéro ≥ 10 M / ≥ 20 M **avant** le retour de Hektor. La mesure du 22/10 dit oui pour la liste
  et la fiche d'annonce ; ❔ **non éprouvé pour la fiche contact**.
- **La session ⑧ modifie `App.tsx` en ce moment.** Une seule tâche en code à la fois : à coordonner.

## 7. Ordre suggéré (à décider par Frédéric)

> ⚠ **Remplacé par le §8.6**, qui couvre aussi les autres registres et s'en tient au front.

1. **A1 + A2** : c'est le cœur de la demande, et le numéro est déjà là.
2. **B1 + B2 + A3 + A4** : rafraîchissements immédiats, front seul.
3. **C1 + C2 (bannière) + C3** : indicateurs dans l'objet.
4. **D1 + D2** : worker. Il faut un « vas-y » et un redémarrage des 4 services.
5. **E** : retrait derrière interrupteur, **en dernier**, quand A à D sont en place.

Tout le front (A, B, C, E) est **réversible** et **n'écrit rien chez Hektor**. Seul D touche le worker.

---

## 8. LES AUTRES REGISTRES — gestes hors modale (complément du 23/10, demandé par Frédéric)

> Les §1 à §7 ne couvraient que les gestes suivis par la modale. Ici : **tous les autres gestes d'écriture**,
> registre par registre. Relevé dans le code par un agent, puis **vérifié par moi** sur les deux constats
> les plus graves (`handleGesteHektor` et la rubrique Affaires). ⚠ **Lecture du code seulement, aucun essai à
> l'écran** : « ne se met pas à jour » veut dire « aucun rechargement dans le code ».

**Mesure en base (tous les temps)** : il existe **9 types de travaux lancés par l'écran que la modale ne suit
pas**. Volume sur 90 jours : `change_hektor_offre_status` 21, `delete_hektor_compromis` 14,
`cancel_hektor_compromis` 13, `delete_hektor_vente` 12, `generate_cadastre_document` 8,
`generate_estimation_pdf` 5, `unlink_hektor_mandant` 3, `generate_mandat_document` 0, signatures 0.
Les **demandes** (`app_diffusion_request`) n'ont **rien reçu depuis le 02/06** : 9 en tout, dont une demande
de diffusion **toujours en attente depuis le 02/06**.

### 8.1 Le défaut qui revient partout : des rubriques qui ne se relisent JAMAIS

Le rechargement général (`dataReloadKey`) relit la liste, la fiche, le contact et les dates de clôture.
**Il ne relit PAS** :

| rubrique | pourquoi | conséquence |
|---|---|---|
| **Affaires** de la fiche (offres, compromis, ventes, répartition, commission, conditions, note, notaires) — `CockpitDetail`, effet sur `[ckDossierIdPourRegistre]` ; idem mobile `MobileDossierDetail` | elle ne se recharge **qu'au changement de fiche** (vérifié) | **toute** écriture d'affaire n'apparaît qu'à la **réouverture** de la fiche |
| **Documents** du cockpit (`ckDocs`, états de signature) et `MandatSignatureTracker` | dépend du seul numéro de dossier | une signature relancée ou annulée ne change pas d'état à l'écran |
| `ConsoleDocumentsPanel` | relit toutes les 8 s **seulement** si un document est marqué « en cours » | un document **généré** (avis de valeur, cadastre) n'apparaît pas |

⭐ **C'est LE correctif transversal (F0)** : brancher ces trois rubriques sur le même signal de
rechargement. Un seul geste répare F1, F2, F3 et une partie de F4 / F5.

### 8.2 Ce qui ne se met PAS à jour du tout

| | registre · geste | clic | ce qui est déjà chez nous | proposé |
|---|---|---|---|---|
| **F1** | Affaires · **refuser / accepter une offre, annuler / supprimer un compromis, supprimer une vente** | `handleGesteHektor` | ⭐ **tout, au clic** : `app_geste_affaire_optimistic` écrit l'état dans le registre (et **fait redescendre le statut du bien** pour un compromis supprimé) | recharger la fiche, les listes **et** la rubrique Affaires tout de suite (F0). ⚠ Ces travaux ne sont **pas suivis** (ni `rememberHektorActionJob`, ni la liste des types). Si Hektor refuse, le worker **remet l'ancien état en base**, et **l'écran ne le montre jamais** : il faut les suivre |
| **F2** | Affaires · **créer / modifier une offre, un compromis, une vente** (`handleChangeHektorAnnonceStatus`) | modale de statut | l'affaire naît chez nous avec **notre numéro ≥ 1 000 000**, puis répartition, commission, conditions, note et notaires | la liste se recharge à la fin du travail (≈ 55 s), **mais la rubrique Affaires jamais** → F0, et rechargement **au clic** |
| **F3** | Documents · **relancer / annuler une signature** | `handleRelanceSignature`, `handleCancelSignature`, `MandatSignatureTracker` | — (travaux `relance_signature` / `cancel_signature_procedure`) | relire les signatures à la fin du travail (F0) ; les suivre |
| **F4** | Estimations · **générer l'avis de valeur PDF** (liste et éditeur) | `submitEstimationPdf`, `EstimationDocumentEditor.submit` | — (travail `generate_estimation_pdf`, **non suivi**) | suivre le travail, puis relire Documents à la fin. Option : ouvrir le PDF quand il est prêt |
| **F7** | Contact · **e-mail envoyé** depuis la fiche | `ContactEmailComposerModal.handleSubmit` | — (Gmail) | relire l'onglet Échanges après l'envoi |
| **F8** | Bandeaux **« Abandonner ce geste »** (fiche annonce, fiche contact) | `GesteAbandonneBanner`, `AnnonceEditStatusBanner`, `ContactEditStatusBanner` | les valeurs sont **remises en base** | recharger la fiche : sinon **elle affiche encore les valeurs abandonnées** |
| **F9** | Admin · **créer un utilisateur** | `handleCreateAppUser` | — | recharger la liste des utilisateurs (comme le fait déjà la modification) |

### 8.3 Ce qui attend la fin du travail Hektor

| | geste | proposé |
|---|---|---|
| **F5** | plan cadastral, mandat et avenant générés | indicateur « en cours de génération » **dans le bloc Documents**, puis relecture à la fin (F0). L'éditeur de mandat sonde déjà seul (4 s, jusqu'à 150 s) : à garder |
| **F6** | **acceptation d'une demande d'annulation** : la date de clôture est écrite tout de suite, mais le registre attend la fin du travail « Clos » | recharger le registre au clic (front seul). Le circuit dort (aucune demande depuis le 02/06) |
| **F10** | **retirer un mandant** : le bouton dit « Retiré du bien… », mais la ligne ne disparaît de la liste des mandants qu'à la fin du travail | la retirer tout de suite (le lien est déjà retiré chez nous) |

### 8.4 Ce qui est DÉJÀ bon — rien à faire

- **Registre des mandats** : corriger la date de clôture (rechargement immédiat), demander une annulation ou une baisse.
- **Demandes** : créer, corriger, refuser ; accepter une diffusion ou une baisse (l'écran attend la réponse **directe** de Hektor, puis se met à jour).
- **Valider / Diffusable / passerelles** : appel direct à Hektor, puis mise à jour de l'écran. Ce n'est pas optimiste, mais c'est juste à l'arrivée.
- **Agenda / RDV**, sur tous les écrans (planning, fiche annonce, fiche contact, rapprochement) : créer, modifier, supprimer → le planning se recharge.
- **Rapprochement** : proposer, écarter, rétablir, e-mail, relances → mise à jour locale immédiate.
- **Notifications** (marquer lu), **Santé** (alertes), « personne perdue » (fermer), sources d'estimation, « Reporter dans la fiche ».

### 8.5 Trouvé en passant — NOTÉ, PAS TRAITÉ

- Les échecs **avalés en silence** : la suppression d'un RDV depuis le rapprochement (`catch { /* best-effort */ }`)
  et « Rétablir » un bien écarté (`.catch(() => {})`). Une action qui rate sans le dire, contraire à la règle
  « une action a une fin visible ».
- **Code mort** : `SuiviMandatsScreen`, `SuiviMandatsScreenV2Legacy`, `handleSaveDiffusionTargets`,
  `handleApplyDiffusionTargetsOnHektor`, `editAffaireOptimistic`, `setDossierDiffusable`,
  `createSyncConsoleDocumentsJob`, `createAnnonceProvisional`, et 4 fonctions `create…Job` d'édition (§5 du
  relevé d'origine).
- **Non trouvés** dans l'écran : le passage d'une estimation à un mandat, l'enregistrement d'un avis de valeur
  (seule la génération du PDF écrit), les commentaires libres.

### 8.6 L'ordre complet — FRONT ET NAVIGATION SEULEMENT (périmètre fixé par Frédéric le 23/10)

> Aucun correctif ci-dessous ne touche le worker, la base ou Hektor. Tout est dans `apps/hektor-v1`.

| lot | correctifs | nature |
|---|---|---|
| **1** | **F0** — Affaires, Documents du cockpit, signatures et panneau Documents branchés sur le rechargement | rafraîchissement |
| **2** | **A1** ouvrir l'annonce créée (notre n° au clic) · **A2** ouvrir le contact créé (notre n° ≥ 20 M) | navigation |
| **3** | **F1** gestes d'affaire : recharger au clic et suivre leurs travaux à l'écran · **B1** archiver / désarchiver / statut / négociateur / activation · **B2** supprimer une recherche · **A3** recherche créée · **A4** mandants · **F6** registre après une annulation acceptée · **F8** après « Abandonner » · **F10** mandant retiré | rafraîchissement immédiat |
| **4** | **C1** n° de mandat · **C2** bannière « photos en attente » dans la fiche · **C3** Matterport · **F3** signatures · **F4** avis de valeur · **F5** cadastre / mandat généré · **F7** e-mail dans les Échanges · **F9** liste des utilisateurs | indicateur dans l'objet + relecture en fin de travail |
| **5** | **E** — retirer la modale, derrière un interrupteur, **en dernier** | retrait |

Hors périmètre, noté pour mémoire : **D** (la cloche, côté worker) · C2 « vraie solution » (photos envoyées par
le worker) · les échecs avalés en silence et le code mort du §8.5.

---

## 9. AUDIT GLOBAL DE LA NAVIGATION — avec essais (23/10, soir)

> Demande de Frédéric : *« refais un audit global de mon projet, fais des tests de navigation et propose-moi
> la meilleure optimisation possible »*. Front et navigation seulement.

### 9.1 Comment j'ai testé

| | |
|---|---|
| **essais à l'écran** | l'app lancée en local en **mode démonstration** (`hektor-mock`, port 5199 : données fictives, aucune connexion à la base) dans le navigateur intégré, en **largeur bureau (1440)** et en **largeur réduite** |
| **production** | `groupe-gti.vercel.app` ouverte **sans se connecter** (la connexion Google est à Frédéric) : poids et temps du premier chargement seulement |
| **base** | durée réelle de la relecture qui part à l'ouverture d'une fiche (30 derniers jours) |
| **code** | lecture ciblée pour expliquer chaque constat |
| ⚠ **non fait** | aucun temps de chargement mesuré sur les **vraies** listes ni sur les vraies fiches : il faut une session connectée. Je n'ai ouvert **aucune** fiche en production, parce que l'ouverture d'une fiche écrit un travail de relecture en base |

### 9.2 Ce que les essais ont prouvé

| # | essai | résultat | cause dans le code |
|---|---|---|---|
| **N1** | changer d'écran, ouvrir une fiche | ⛔ **l'adresse ne change jamais** (`http://localhost:5199/`) et **l'historique reste à 1** | aucun `pushState`, aucun `popstate` dans tout le front. Le seul lien profond est celui des e-mails de demande (`?open=request`) |
| **N2** | bouton **« retour »** du navigateur, fiche ouverte | ⛔ **« no back history »**. Dans un vrai navigateur, il **fait sortir de l'app**. Sur un **téléphone Android**, la touche retour la **ferme** | idem N1 |
| **N3** | **F5** sur l'écran Contacts | ⛔ **retour à l'Accueil**, fiche et position perdues | `useState<Screen>('accueil')` : rien n'est mémorisé |
| **N4** | recherche « Bellevue » sur Annonces → Contacts → retour sur Annonces | ⛔ **la recherche est perdue**, la liste revient entière | `openScreen` **remet à zéro** filtres, page et fiche à chaque changement de menu (`defaultFiltersForScreen`) |
| **N5** | la barre « Rechercher un bien, un contact, un mandat… » de l'**Accueil** | ⛔ **elle est décorative** : on ne peut rien y taper | `<input readOnly value="" …>` (App.tsx ~24136). **L'app n'a pas de recherche globale** |
| **N6** | fiche annonce → rubrique Contact → « Ouvrir la fiche » | ✅ la fiche contact s'ouvre **par-dessus** l'annonce, et la fermer ramène au bien (`openContactDirectory`) | — |
| **N7** | depuis cette fiche contact, ouvrir **un autre bien** | ⚠ le contact se ferme et l'autre bien **remplace** le premier : **impossible de revenir** à l'annonce de départ (un seul niveau, pas de pile) | `onOpenDossier` (~22158) : `setAnnonceContactId(null)` puis ouverture |
| **N8** | **Échap** sur une fiche ouverte | ⚠ rien ne se ferme | — |
| **N9** | ouvrir une fiche | ⚠ une relecture part chez Hektor : **29 s en médiane, 51 s pour les plus lentes** (671 en 30 jours). À la fin, **tout l'écran se recharge**, et le détail est chargé **deux fois** (il dépend aussi des listes) | effet du détail sur `[…, dataReloadKey, dossiers, mandats]` |
| **N10** | premier chargement de l'app (production) | ⚠ **un seul fichier** de 2,3 Mo de code (590 Ko compressés) + 1,6 Mo de style ; **0,8 s** ici, plus lent sur un téléphone en 4G | `App.tsx` : environ 44 000 lignes dans un seul bloc |
| **N11** | après une création ou un geste | voir §1 à §8 : on n'ouvre pas ce qu'on crée, et l'écran attend Hektor alors que la donnée est déjà chez nous | — |

### 9.3 Ce qui marche bien

La fiche annonce (« cockpit ») a son propre bouton **« Retour aux annonces »** et des rubriques claires. La
fiche contact s'ouvre **dans le contexte** de l'annonce (N6). Le menu bas sur mobile et le menu de gauche sur
bureau sont lisibles. L'agenda, le rapprochement et les modifications se mettent à jour tout de suite (§8.4).

---

## 10. LA MEILLEURE OPTIMISATION — ma proposition

**Le principe : chaque endroit de l'app a une ADRESSE.** C'est ce qui fait la différence entre « une page » et
« un logiciel normal » : retour, F5, lien partagé, onglet de plus, tout en découle.

| priorité | chantier | ce que l'utilisateur gagne | répare |
|---|---|---|---|
| **1** | **Une adresse par écran et par fiche**, du type `?ecran=annonces&fiche=10000009`, `?ecran=contacts&contact=20000007`. Chaque changement s'écrit dans l'historique du navigateur | ⭐ le bouton **retour** marche (y compris Android) ; **F5 garde la fiche ouverte** ; on peut **envoyer le lien** d'une fiche à un collègue ; une notification ou un e-mail peut ouvrir directement la bonne fiche ; on peut ouvrir une fiche **dans un autre onglet** | N1, N2, N3, N7 |
| **2** | **Chaque écran garde sa mémoire** : recherche, filtres, page et position quand on change de menu, et on retrouve tout en revenant | on ne refait plus sa recherche à chaque aller-retour | N4 |
| **3** | **Ouvrir ce qu'on crée, et refléter le geste au clic** (lots 1 à 3 du §8.6) | le geste se voit à la seconde ; on arrive sur l'objet créé | N11 |
| **4** | **Une vraie recherche globale** dans la barre de l'Accueil (et en haut de chaque écran) : numéro, nom, adresse, téléphone, n° de mandat → **un clic ouvre la fiche** | le geste le plus fréquent d'un agent (« retrouver un bien ou un client ») en une seule frappe | N5 |
| **5** | **Revenir en arrière entre objets** : annonce → contact → autre bien → retour… avec un **fil d'Ariane** (« Annonces › V1705 › M. MOREAU ») | on ne perd plus le bien de départ | N7 (le chantier 1 en fait l'essentiel) |
| **6** | **Indicateurs dans l'objet, puis retrait de la modale** (lots 4 et 5 du §8.6) | plus de fenêtre qui recouvre l'écran | §1 |
| **7** | **Finitions** : Échap ferme la fiche ; le détail n'est chargé **qu'une fois** ; une liste déjà vue s'affiche **tout de suite** puis se met à jour en fond | moins d'attente, plus de fluidité | N8, N9 |
| **8** | **Découper le gros fichier** pour que chaque écran ne charge que son code | ouverture plus rapide sur téléphone | N10 — en dernier : le gain est réel mais moins visible |

**Pourquoi des adresses en `?ecran=…` et pas `/annonces/123`** : il n'y a **pas de fichier de configuration
Vercel** dans le projet. Une adresse en `/annonces/123` renverrait une **erreur 404 après F5**. La forme `?…` marche
**sans rien changer au serveur** ni au déploiement.

**Comment, sans tout casser** : pas de nouvelle bibliothèque. Un petit module **lit** l'adresse au démarrage et
**écrit** l'adresse quand l'écran ou la fiche change, en s'appuyant sur les états qui existent déjà (`screen`,
`selectedDossierId`, `annonceContactId`…). **Derrière un interrupteur** : éteint, l'app se comporte comme
aujourd'hui.

### 10.1 Ce que ça pourrait casser ailleurs

- **Le lien profond des e-mails de demande** (`?open=request&app_dossier_id=…`) : il doit continuer de marcher,
  donc le module d'adresse doit le reconnaître **avant** le reste.
- **Le lien de récupération du mot de passe** (`#type=recovery`) : ne pas y toucher.
- **Le retour arrière d'Android** qui fermait l'app fermera désormais la fiche : c'est le comportement voulu,
  mais **à faire valider** par un utilisateur sur téléphone.
- **La mémoire des écrans (2)** : `openScreen` remet tout à zéro **exprès** aujourd'hui. Il faut vérifier si un
  écran (Suivi, tuiles de l'Accueil) **compte** sur cette remise à zéro pour afficher le bon filtre.
- **La session ⑧** modifie `App.tsx` en même temps : une seule tâche de code à la fois, à coordonner.

### 10.2 MESURES RÉELLES — production, session Chrome de Frédéric (23/10, 18:54 → 19:00)

> Lecture seule : je n'ai cliqué que sur les menus, plus une recherche. Un compteur posé dans la page a
> relevé chaque requête. **Aucune fiche n'a été ouverte volontairement**, mais le simple passage sur les
> menus a déclenché **3 relectures chez Hektor** (annonces 63339 et 63336, contact 10650798, toutes
> terminées sans erreur en 12 à 16 s). Ce sont des lectures, pas des écritures chez Hektor. Elles sont
> **l'objet du constat M1**.

**Temps par écran** (du clic à l'arrivée des données de la liste) :

| écran | données prêtes | requêtes | la plus lente |
|---|---|---|---|
| Annonces | **0,5 s** | 18 | `app_dossiers_current` 213 ms |
| Mandats (registre) | **0,5 s** | 17 | `app_registre_mandats_current` 223 ms |
| Accueil | **0,6 s** | 21 | `app_searches_to_complete` 414 ms |
| Suivi | **0,9 s** | 20 | `app_dossiers_current` 434 ms |
| Estimations | **1,4 s** | **34** | `app_dossiers_current` 386 ms |
| Agenda | **1,6 s** | 29 | `app_dossiers_current` 303 ms |
| Contacts | ⚠ **3,6 s** | 12 | ⚠ `app_contact_relations_current` **3 449 ms** (jusqu'à 4,2 s observé) |

**Ce que les mesures ont trouvé :**

| # | constat | preuve |
|---|---|---|
| **M1** | ⛔ **Afficher une liste sélectionne d'office sa première ligne**, et cette sélection suffit à **charger la fiche complète ET lancer une relecture chez Hektor**, sans que personne ne l'ouvre | `setSelectedDossierId(… rows[0] …)` (App.tsx ~14519) et `setSelectedContactId(… rows[0] …)` (~14322) ; la relecture part sur `selectedDossierId` (~14454) et `selectedContactId` (~14442), **pas sur l'ouverture**. Les 3 relectures du test le prouvent. ⚠ **Ça consomme le quota Hektor pour rien** : chaque relecture = annonce + photos + DPE + mandats + propriétaires. Le délai de 30 min évite les doublons (vérifié : 0 nouvelle relecture aux passages suivants) |
| **M2** | ⛔ **La fiche d'annonce attend le résumé des rendez-vous** (serveur Render) **avant de s'afficher en entier** : **9,3 s en moyenne, 20,6 s au pire** sur 16 appels | `loadDossierDetail` (api.ts ~5324) enchaîne Matterport, mandants, puis `/public/appointments/annonce/<n°>/summary` **en série**, avant de rendre la fiche. Ce résumé ne sert qu'à la rubrique RDV |
| **M3** | ⚠ **Le détail est rechargé en boucle** : **29 chargements de fiche** en quelques minutes **sans en ouvrir aucune** ; le résumé RDV de la même annonce **16 fois** | l'effet du détail dépend de `dossiers` et `mandats` : chaque rechargement de liste relance le détail (et M2 avec) — même sur l'Accueil, l'Agenda et le Suivi |
| **M4** | ⚠ **Contacts est l'écran le plus lent** (3,6 s), à cause d'**une seule requête** : `app_contact_relations_current` (3,4 s) | une seule requête lente : sa cause côté base n'a **pas été mesurée** (hors front) |
| **M5** | ⚠ chercher un bien par son **numéro de dossier** (V430063336) ne trouve rien s'il n'est pas dans la liste « actives » : il faut cliquer « Étendre aux archives, vendus et clos » | — c'est un argument de plus pour la recherche globale (chantier 4) |

**Ce que ça ajoute à la proposition du §10** (front seulement) :

| priorité | ajout | gain |
|---|---|---|
| **0** ⭐ | **Ne plus sélectionner d'office la première ligne** : on ne charge la fiche et on ne relit chez Hektor **qu'à l'ouverture réelle** (`detailOpen`) | moins de requêtes sur **tous** les écrans, et le **quota Hektor** n'est plus dépensé pour des fiches que personne ne regarde |
| **0 bis** ⭐ | **Afficher la fiche sans attendre le résumé RDV** : la fiche s'affiche tout de suite, la rubrique RDV se remplit quand le résumé arrive | ouverture d'une fiche : de **~9 s** à **moins d'une seconde** (estimation : les autres lectures du détail font 55 à 200 ms ; **non mesuré de bout en bout**) |
| **7 (renforcé)** | **Le détail ne se recharge que si SA fiche a changé**, pas à chaque rechargement de liste | fin des 29 chargements inutiles |

⚠ **Ce que M1 pourrait casser ailleurs** : des écrans **comptent peut-être sur la première ligne sélectionnée**
(un panneau latéral qui montre « la fiche en cours », le cockpit en grand écran). À vérifier écran par écran
**avant** de changer quoi que ce soit.

### 10.3 Ce qui reste à mesurer

Les listes sont mesurées (§10.2). Reste **l'ouverture d'une fiche, de bout en bout**, chronométrée à l'écran.
⚠ Ouvrir une fiche crée un travail de relecture chez Hektor : il faut l'accord de Frédéric. Et la cause de
la lenteur de `app_contact_relations_current` (M4) relève de la base, pas du front.

---

## 11. POINT 0 — RE-AUDIT DU 26/10 : « la première ligne ouverte d'office » (rien codé)

*Frédéric : « vas-y, mais j'ai besoin de bien comprendre avant chaque point ».*

**Le mécanisme, relu sur le code du 26/10** (`App.tsx`, après les commits ⑧ du 24-26/10) :

| où | ce que fait le code | conséquence |
|---|---|---|
| liste des annonces / mandats / estimations / suivi (l. 14521-14525) | à chaque chargement, si rien n'est sélectionné (ou si la sélection n'est plus dans la page), **sélectionne la 1re ligne** | la sélection déclenche (l. 14456-14464) une **relecture chez Hektor** (« read_through_open ») et (l. 14567-14601) le **chargement de la fiche complète** — sans qu'elle soit ouverte |
| liste des contacts (l. 14324-14328) | même chose avec le 1er contact | relecture du contact chez Hektor (l. 14444-14452) + chargement de sa fiche |
| registre (l. 14500-14503), mandat (l. 14505) | même chose | lecture légère chez nous (passerelles de diffusion) — **pas Hektor**, hors point 0 |

**Mesure en production (7 jours, `app_console_job`)** : 247 relectures d'annonce pour seulement **8 annonces** quand le
numéro est connu ; parmi les relectures « à l'ouverture » (`read_through_open`), **63299 ×41** et **63339 ×19** —
**63339 est celle qu'a sélectionnée d'office mon essai du 23/10** (preuve), 63299 est très probablement la tête de
liste de ces jours-là (liste triée par date de mise à jour). Côté contacts : 10650798 ×7 (même essai).

**Qui lit la sélection quand la fiche est FERMÉE ? (« ce que ça pourrait casser »)** — vérifié écran par écran :
- `AnnonceScreen` et la fiche des autres écrans : affichées **seulement si `detailOpen`** (l. 23645, 23830, 22856) ;
- `MandatsScreen` (mandats, estimations) et `SuiviMandatsScreenV2` : déclarent la prop `selectedDossier` mais **ne la
  lisent jamais** ;
- `ContactsScreen` (bureau et mobile) : fiche affichée **seulement sur clic** (état `detailOpen` local, l. 44062 / 44336) ;
- les modales de demande (l. 18029-18414) : n'utilisent la sélection **que si elle correspond** à la demande, sinon le
  mandat — inchangé ;
- **gardés tels quels** : la recherche directe d'un contact par son numéro (l. 14325, elle doit ouvrir ce contact) et
  le lien des e-mails `?open=request` (il pose lui-même la sélection, l. 14653-14655).

**Le correctif proposé** (front seulement, 2 endroits) : ne plus prendre la 1re ligne. On garde la sélection si elle
est toujours dans la liste (ou si la fiche est ouverte), sinon **rien n'est sélectionné** — la fiche, sa relecture
chez Hektor et son chargement ne partent **qu'au clic**. Derrière une constante (`SELECTION_D_OFFICE`) pour revenir
en arrière en une ligne.

**Ce que l'utilisateur verra** : rien de différent à l'écran (aucune fiche n'était affichée). Ce qui change : moins de
requêtes à chaque changement de menu, et **plus de relecture Hektor pour une fiche que personne ne regarde**.

**Contrôle prévu** : `npm run build` ; essai en mode démonstration (aucune relecture demandée en changeant de menu,
une relecture au clic sur une ligne) ; après déploiement, compter les `read_through_open` par jour.

### 11.1 ✅ POINT 0 CODÉ ET CONTRÔLÉ (26/10, « Vas-y mais contrôle le résultat »)

**Le code** (`App.tsx`) : constante `SELECTION_D_OFFICE = false` (avant `App()`), et une ligne à chacun des deux
endroits (liste des annonces/mandats/estimations/suivi ; liste des contacts) : la sélection est gardée si elle est
encore dans la liste (ou fiche ouverte), sinon **rien** — plus de 1re ligne. `true` = l'ancien comportement.

**Contrôles :**

| | résultat |
|---|---|
| `npm run build` | ✅ vert (l'avertissement « fichier > 500 Ko » existait déjà) |
| **témoin AVANT** (mode démonstration, ancien code) : Annonces → Estimations → Suivi → Contacts, aucune fiche ouverte | la ligne choisie d'office = **7801** sur les 3 écrans (lue dans les propriétés des écrans) — et 7801 est la **3e** ligne affichée |
| **APRÈS** : même parcours, + retour sur Annonces | **aucune** ligne choisie (`null`) sur tous les écrans |
| **témoin positif** : clic sur une ligne | la fiche s'ouvre — 2e ligne (5502 « T3 lumineux… Fauriel ») par clic de code, 3e ligne (7801 « Maison de caractère ») par **vrai clic de souris** ; « Retour aux annonces » garde la ligne surlignée |
| console | 4 erreurs 500 sur `/api/hektor-diffusion/broadcasts` : pas de serveur d'API en démonstration, la 1re **avant** le changement — sans rapport |

⚠ **Non éprouvé ici** :
- **les contacts** : la démonstration n'a **aucun** contact (liste vide) ; le code est le même patron, une ligne ;
- **le gain en production** : il se mesurera après déploiement, en comptant les relectures `read_through_open`
  par jour (référence : 63299 ×41 et 63339 ×19 sur les 7 jours avant le 26/10).

Hors point 0, laissé tel quel : la sélection d'office du **mandat** (l. 14505) et du **registre** (l. 14500) —
lecture légère chez nous (passerelles), pas Hektor. `StockScreen` (panneau « Fiche rapide ») lit la sélection, mais
l'écran `annonces` est **inatteignable** (`openScreen` le redirige vers `mandats`, l. 15045).
