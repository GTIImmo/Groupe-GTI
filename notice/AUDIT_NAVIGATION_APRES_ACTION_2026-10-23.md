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

### 11.2 Contrôle en production (26/10, ~09:10)

- ✅ **Déployé** : le code publié (`assets/index-dFQW02Qi.js`, en ligne vers 09:04) porte la nouvelle forme
  `…rows.some(…)?bt:null` — identique à la construction locale ; l'ancienne finissait par `…?bt:De.rows[0]?.app_dossier_id??null`.
- ⏳ **Comportement réel pas encore prouvé** : l'extension Chrome ne répondait pas (pas d'essai dans la session de
  Frédéric). En base, 2 relectures « à l'ouverture » ce matin, **toutes deux sur 63339** (07:32 et 09:01:15), donc
  **avant** la mise en ligne (~09:04) — le même schéma que l'ancien code (63339 en tête de liste).
- ⚠ Une application déjà ouverte dans un onglet **garde l'ancien code** tant qu'on ne recharge pas la page (F5).
- **Le juge** : plus aucune relecture `read_through_open` sans fiche réellement ouverte ; à mesurer sur une journée
  ouvrée (référence avant : 63299 ×41, 63339 ×19 en 7 jours).
- ✅ **PROUVÉ EN RÉEL le 26/10 vers 09:20** (journaux de l'API Supabase, `edge_logs`, heures de Paris) — l'extension
  Chrome de cette session étant tombée, Frédéric a fait les gestes et j'ai lu le résultat :

  | minute | listes d'annonces chargées | appels de relecture Hektor |
  |---|---|---|
  | 09:01 (ancien code) | 113 | **3** (→ la relecture de 63339) |
  | 09:05 (nouveau code) | 86 | **0** |
  | 09:09 | 90 | **0** |
  | 09:10 | 40 | **0** |

  Et `app_console_job` : **0 relecture** de 09:05 à 09:19. ⚠ Les **contacts** n'ont pas été visités dans la fenêtre :
  non prouvé en réel pour eux (même ligne de code).

## 12. POINT 0 bis — RE-AUDIT DU 26/10 : « la fiche attend le résumé des RDV » (rien codé)

**Le mécanisme** (`lib/api.ts`, `loadDossierDetail`, l. 5306-5404) : la fiche attend, **l'une après l'autre**,
5 lectures avant d'être rendue : le bien (Supabase) → son détail (Supabase) → Matterport → les mandants (registre)
→ **le résumé des RDV** (serveur Render, `/public/appointments/annonce/<n°>/summary`). Mesure du 23/10 dans la
session de Frédéric : **9,3 s en moyenne, 20,6 s au pire** pour ce seul résumé ; les autres lectures 55 à 200 ms.
Aujourd'hui sans jeton, le serveur répond « non autorisé » en 0,2-0,5 s : la lenteur est dans le **calcul** du
résumé (~6 allers-retours Render ↔ Supabase), pas dans le réseau.

⚠ **Le résumé n'est pas une simple lecture** (`backend/app/services/appointment_service.py`,
`get_internal_annonce_summary`, l. 707) : s'il manque, il **crée** le lien public de RDV du bien
(`_ensure_link_for_annonce`, POST) et peut **compléter** ses coordonnées (`_maybe_enrich_link_contacts`, PATCH).
Le point 0 bis ne change **pas** qu'il soit appelé à l'ouverture d'une fiche — seulement qu'on ne l'attende plus.
(Le point 0 a déjà supprimé les appels pour les fiches que personne n'ouvrait.)

**Qui lit le résumé** (5 endroits, tous dans la fiche ouverte) :

| endroit | ce qu'il lit | si le résumé arrive 9 s plus tard |
|---|---|---|
| rubrique RDV (l. 36397-36401) | lien public, demandes, historique | le lien retombe déjà sur le n° de l'annonce s'il manque (l. 8485-8496) ; la liste se remplit à l'arrivée |
| filtre des visites du cycle (l. 29415) | demandes | se remplit à l'arrivée |
| ⚠ **onglet Reporting** (l. 32504) | demandes → **compte-rendu au vendeur** | ⚠ un compte-rendu préparé **avant** l'arrivée sortirait **sans les visites** → il faut le dire à l'écran et bloquer l'envoi tant que le résumé n'est pas là |
| onglet Synthèse (l. 32565) | demandes | se remplit à l'arrivée |
| agenda de la fiche (l. 35483) | e-mail / n° du négociateur | repli déjà prévu sur le négociateur du bien |

**Les autres appelants de `loadDossierDetail`** : l'éditeur d'avis de valeur (l. 15263), la relecture après une
modification (l. 23658, 23849), l'éditeur de la fiche estimation (l. 25319). **On ne les change pas** : ils gardent
le chargement complet.

**Le correctif proposé** (front seulement) :
1. `loadDossierDetail` reçoit une option « sans le résumé RDV » ; **par défaut, rien ne change** pour personne.
2. La fiche ouverte (l. 14594) s'en sert : elle s'affiche dès que le bien, son détail, Matterport et les mandants
   sont là (~0,5 s estimé, **non mesuré de bout en bout**).
3. Le résumé est demandé **juste après**, à part ; à son arrivée, il est fusionné dans la fiche — **seulement si
   c'est toujours la même annonce**, et gardé d'un rechargement à l'autre (pas de clignotement).
4. **Reporting** : tant que le résumé n'est pas arrivé, un message « rendez-vous en cours de chargement » et
   l'envoi du compte-rendu attend ; s'il échoue, on le dit (au lieu d'envoyer sans les visites).
5. Derrière une constante `RESUME_RDV_EN_DIFFERE` (`false` = l'ancien comportement).

**Contrôle prévu** : `npm run build` ; essai en démonstration (la fiche s'ouvre, la rubrique RDV se remplit) ;
puis en production, chronométrer l'ouverture d'une fiche (⚠ ouvrir une fiche lance une relecture chez Hektor —
c'est le geste normal d'un négociateur).

### 12.1 Quel système de RDV ? Déjà noté ? (26/10, question de Frédéric)

**Le résumé qui bloque la fiche appartient au RDV PUBLIC DE LA VITRINE** (`backend/app/services/appointment_service.py`,
page `gtiimmo.github.io/vitrine/rdv/index.html?ref=…`, QR codes) — **pas** à Google. Le projet a trois systèmes
(`notice/AUDIT_VITRINE_ET_RDV_2026-09-25.md`, mémoire `vitrine-et-rdv-publics-liens-hektor`) :

| système | dans la fiche | bloque la fiche ? |
|---|---|---|
| 1. la vitrine (catalogue exporté chaque nuit sur GitHub) | — | non |
| 2. **le RDV public de la vitrine** | rubrique RDV (lien public, demandes, historique) + Reporting + Synthèse | ⛔ **oui : c'est le résumé de 9 s** |
| 3. l'agenda Google (RDV depuis les rapprochements) | `GoogleAgendaAnnonceSection` | **non** : chargé par sa propre section ; il emprunte seulement l'e-mail du négociateur au résumé, avec repli sur celui du bien |

**Déjà noté ?** Oui pour le système, non pour la lenteur :
- **Liste, section 11bis** (25/09) : 4 points ouverts, **aucun fait** (① liens au jeton — ⛔ *« ne pas faire tel quel, le
  jeton n'est pas stable »* (07/10) ; ② le service relit le bien par le n° Hektor ; ③ fiche visite PDF produite par
  Hektor ; ④ un lien d'agenda vers un contact supprimé). Et déjà le 07/10 : *« 0 demande enregistrée par cette page
  depuis le 29/04 »*.
- **La lenteur qui bloque la fiche** n'était notée nulle part avant mon audit du 23/10 (M2).

**Mesuré le 26/10** : `app_appointment_request` = **0 ligne, depuis toujours** ; liens publics **2 284** (54 en
30 jours, créés surtout par l'étape de nuit `backfill appointment public links`) ; liens d'agenda Google **11**, le
dernier le 15/06. ➡ **La fiche attend 9 s une liste de demandes qui est TOUJOURS VIDE.** Seule partie utile du
résumé aujourd'hui : le jeton du lien public (et la rubrique retombe déjà sur le n° de l'annonce s'il manque).

**Conséquence pour 0 bis** : le risque du Reporting est **théorique aujourd'hui** (0 demande), mais la garde reste
utile le jour où une demande arrive. ⚠ Le résumé peut **créer** un lien public (et donc un nouveau jeton) à
l'ouverture d'une fiche — lien avec le point ① de 11bis (jetons instables) ; 0 bis ne change **pas** quand il est appelé.

**Noté, hors sujet (ne pas traiter ici)** : 0 demande depuis 6 mois — la page de RDV de la vitrine **fonctionne-t-elle
encore** ? Non mesuré.

### 12.2 ✅ POINT 0 bis CODÉ ET CONTRÔLÉ EN DÉMONSTRATION (26/10)

**Le code** :
- `lib/api.ts` : le résumé sort dans `loadAnnonceAppointmentSummary` et `appointmentSummaryFields` (même fusion
  qu'avant) ; `loadDossierDetail(id, { sansResumeRdv })` — **par défaut rien ne change** (avis de valeur, relecture
  après modification, éditeur d'estimation gardent le chargement complet).
- `App.tsx` : constante `RESUME_RDV_EN_DIFFERE = true` ; la fiche ouverte charge sans le résumé ; le résumé est
  demandé à part (fiche **ouverte**, **non légère** seulement) ; fusion dans `detail` **seulement pour la même
  annonce** ; `appointment_resume_etat` = chargement / prêt / échec.
- **Reporting protégé aux DEUX endroits** — ⚠ et c'est le contrôle qui l'a trouvé : en production le cockpit est
  allumé (`APP_COCKPIT_V2_ENABLED = "true"` dans le code publié), donc le Reporting affiché est celui de
  `CockpitDetail`, **pas** celui de `DossierDetailLayoutBase` que j'avais d'abord protégé seul (mémoire
  « vérifier QUEL composant s'affiche »). Les deux sont protégés.

**Contrôles** (`npm run build` vert, avec la vérification des types ; démonstration ouverte sous `essai.localhost`
pour que l'app appelle vraiment le serveur RDV, et réponse du résumé **simulée à 5 s** dans la page) :

| essai | résultat |
|---|---|
| ouvrir une fiche | **affichée en entier à 1 s** (capture) pendant que le résumé est « en chargement » |
| arrivée du résumé (5 s) | état « prêt », jeton et demande fusionnés dans la fiche |
| Reporting **pendant** le chargement | « Aperçu / PDF » et « Envoyer au propriétaire » **BLOQUÉS**, message « Rendez-vous en cours de chargement… », compteur « … » |
| Reporting **après** | boutons actifs, compteur « 1 » |
| résumé **en échec** (500 simulé) | avertissement « les rendez-vous de la vitrine n'ont pas pu être chargés… », boutons actifs |
| **changer de fiche** pendant le chargement | la fiche affichée porte **son** jeton (`JETON-15` pour l'annonce 15) ; la réponse de la 1re fiche est jetée |
| console | seules erreurs : les passerelles de diffusion (pas de serveur d'API en démonstration) et la panne simulée |

⚠ **Non éprouvé** : l'interrupteur à `false` (c'est l'ancien chemin, inchangé) ; une fiche « légère » d'archive ; le
**temps réel en production** — à chronométrer après déploiement (référence : résumé 9,3 s en moyenne le 23/10).

### 12.3 ✅ POINT 0 bis EN PRODUCTION (26/10) — mesuré sur les ouvertures de Frédéric

En ligne à **10:05:36** (code publié `index-DBtnx4qq.js`, porte `appointment_resume_etat`). Frédéric a rechargé
puis ouvert des fiches ; journaux de l'API Supabase (`edge_logs`), heures de Paris :

| fiche | clic (relecture demandée) | fiche complète (détail, Matterport, mandants lus) | résumé RDV terminé (lectures faites par Render) |
|---|---|---|---|
| 63304 | 10:05:51,0 | 10:05:51,6 → **0,6 s** | 10:05:53,8 → 2,8 s |
| 63200 | 10:06:14,8 | 10:06:15,2 → **0,4 s** | 10:06:17,5 → 2,7 s |

➡ La fiche n'attend plus le résumé : elle a ses données en **0,4 à 0,6 s** ; le résumé arrive ~2,2 s plus tard.
Ce matin le serveur Render était **chaud** (2,7 s au lieu des 9,3 s en moyenne du 23/10) : le gain réel varie donc
de ~2 s à ~9 s (et plus quand Render se réveille). ⚠ Mesure côté serveur (heure des lectures), pas le temps
d'affichage à l'écran ; l'affichage suit les lectures.

Vu au passage : un **2e résumé** pour 63200 à 10:06:22-23 — probablement une réouverture de la même fiche (ou le
renouvellement du jeton de session, dont l'effet dépend) ; sans conséquence (le lien existe déjà, il n'est pas recréé).
Et les relectures Hektor n'ont été demandées **qu'à l'ouverture** des fiches (10:05:51, 10:06:26) — le point 0 tient.

---

## 13. POINT 1 — RE-AUDIT DU 26/10 : « une adresse par écran et par fiche » (rien codé)

**Aujourd'hui** (`App.tsx`) : l'écran est un état mémoire, `useState<Screen>('accueil')` (l. 12890) ; la fiche
ouverte aussi (`detailOpen` + `selectedDossierId`, le contact par-dessus une annonce `annonceContactId`, la fiche
contact de l'écran Contacts = un état **local** de `ContactsScreen`). **Aucun** `pushState` ni `popstate` : l'adresse
ne bouge jamais → retour du navigateur = sortie de l'app (fermeture sur Android), F5 = Accueil, pas de lien partageable.

**Ce qui lit DÉJÀ l'adresse (à ne pas casser)** :
| adresse | où | règle |
|---|---|---|
| `?open=request&app_dossier_id=…&role=…&request_type=…` (e-mails de demande) | l. 14670-14711, `buildAppRequestUrl` l. 8540 | elle passe **en premier**, puis efface ses paramètres |
| `#type=recovery` (mot de passe) | l. 13687, 18585 | le module ne touche **jamais** au `#` |
| `/rdv/annonce/<jeton>` (lien public RDV) | `buildAppointmentAnnonceUrl` l. 8479 ; serveur `_compose_public_url` | ⚠ voir « trouvé au passage » |

**L'hébergement** : pas de `vercel.json`. Mesuré : `groupe-gti.vercel.app/?ecran=contacts` → **200** ;
`/annonces/123` → **404**. ➡ des adresses en **`?…`** (F5 marche sans toucher au déploiement), pas en `/…`.

**Les deux portes qui existent déjà** et que l'adresse réutiliserait (aucune nouvelle logique d'ouverture) :
`openDossierDetailPage(id)` (l. 15156) pour une annonce, `showContactInDirectory(id)` (l. 14882) pour un contact.

**Ce que ça pourrait casser** :
- ⚠ **la connexion Google ramène à l'accueil** (`redirectTo` = l'origine, l. 14771 / `supabase.ts` l. 47) : un lien
  ouvert **déconnecté** perdrait sa cible → la garder le temps de la connexion (stockage de session) et la rejouer ;
- ⚠ **la fiche contact de l'écran Contacts est un état local** (`ContactsScreen`, bureau l. 44062 et mobile l. 44336) :
  il faut qu'elle **prévienne** l'app quand elle s'ouvre / se ferme (une prop de plus) — sinon l'adresse l'ignore ;
- ⚠ **les noms internes trompent** : l'écran interne `mandats` est le menu « Annonces », `registre` est le menu
  « Mandats » (mémoire `ecran-mandats-est-le-menu-annonces`) → l'adresse porte les noms **du menu**, traduits ;
- les droits : un lien vers une fiche qu'on n'a pas le droit de voir n'ouvre rien (la base filtre déjà) → afficher
  « fiche introuvable ou non accessible » au lieu d'une fiche vide ; `suivi` / `sante` refusés restent redirigés (l. 19315) ;
- ⚠ **un bien vendu / clos / archivé n'est plus dans `app_dossier_current`** (mémoire) : son adresse ne pourra pas
  l'ouvrir directement en 1re version → le dire, pas le cacher ;
- la session ⑧ modifie aussi `App.tsx` : une seule tâche de code à la fois, à coordonner.

**Trouvé au passage, NOTÉ, PAS TRAITÉ** : le **lien public de RDV** affiché dans la fiche pointe sur
`<adresse de l'app>/rdv/annonce/…` — côté écran (`VITE_APPOINTMENT_PUBLIC_BASE_URL` **absente** du code publié → repli
sur `groupe-gti.vercel.app`) comme côté serveur (`app_base_url` + `/rdv/annonce/`, valeur Render non mesurée). Or
`groupe-gti.vercel.app/rdv/annonce/abc` → **404**. Ce lien semble **mort** ; à rapprocher de la vitrine (§12.1, 11bis).

### 13.1 ✅ POINT 1 CODÉ ET CONTRÔLÉ EN DÉMONSTRATION (26/10, « VAS Y POUR LE POINT 1 »)

**Principe tenu** (demande de Frédéric : « améliorer, pas casser » ma navigation) : **aucun bouton de l'app ne change**
(menu, « Retour aux annonces », retour contextuel vers le contact, contact par-dessus l'annonce). L'adresse s'écrit
**derrière** eux et se relit par les **deux portes existantes**.

**Le code** (`App.tsx`) : interrupteur `ADRESSE_DANS_LA_BARRE = true` ; noms du **menu** (`ECRAN_VERS_ADRESSE` /
`ADRESSE_VERS_ECRAN`) ; l'adresse **déduite** de l'état (`adresseVoulue`) → `pushState` ; pendant une restauration
(démarrage, précédent/suivant) → `replaceState` (pas de fausse étape) ; lecture au démarrage **après** le lien
`?open=request` et une fois connecté ; `popstate` ; une entrée sans adresse = l'accueil ; mémo de l'adresse le temps de
la connexion (`sessionStorage`, onglet seul) ; fiche introuvable par l'adresse → message et retour à la liste ;
`ContactsScreen` et `MobileContactCards` préviennent l'app (ouverture / fermeture) et acceptent d'être fermées ; le
mobile accepte aussi `openContactId`.

**Contrôles** (`npm run build` vert avec les types ; mode démonstration, bureau 1440 et téléphone 375) :

| essai | résultat |
|---|---|
| arrivée | `?ecran=accueil`, **remplace** l'entrée (historique 1) |
| menu Annonces → fiche | `?ecran=annonces` puis `?ecran=annonces&annonce=7801` (2 étapes) |
| menu Contacts puis **précédent ×3, suivant ×2** | fiche 7801 → liste → accueil → liste → fiche ; **historique constant (4)**, aucune fausse étape |
| **F5** sur la fiche | la fiche 7801 se rouvre |
| contact par-dessus la fiche | `…&contact=P-7801` ; précédent l'enlève, suivant le remet (⚠ voir « non éprouvé ») |
| bouton **« Retour aux annonces »** (le tien) | ferme comme avant ; l'adresse suit (`?ecran=annonces`) ; « précédent » rouvre la fiche |
| lien vers une fiche **inexistante** (`annonce=999999`) | message « Fiche introuvable ou non accessible… », retour à la liste, sans étape ajoutée |
| lien des **e-mails de demande** (`?open=request…`) | la modale de Pauline s'ouvre toujours (VM7801), puis l'adresse prend le relais |
| **téléphone** : Annonces → « Voir le détail » → **retour** | `annonce=32621` puis retour aux cartes **sans quitter l'app** |

⚠ **Non éprouvé en démonstration** : l'**écran Contacts** (la démonstration n'a **aucun** contact) et l'**affichage**
du contact par-dessus l'annonce (le contact d'essai `P-7801` n'existe pas : l'adresse suit, la fiche ne s'affiche
pas) ; la **connexion Google** (pas de connexion en démonstration) ; la touche retour d'un **vrai** Android. → à
éprouver en production avec Frédéric.

### 13.2 ✅ POINT 1 PROUVÉ EN PRODUCTION (26/10, en ligne à 11:16:30, `index-DgY4J4V_.js`)

Frédéric a joué les **6 essais réels** et les déclare **tous bons** : (1) annonces — précédent / suivant ; (2) F5 et lien
dans un nouvel onglet ; (3) écran Contacts — ouverture, précédent / suivant, F5 ; (4) contact par-dessus une annonce,
ses boutons inchangés ; (5) lien ouvert en navigation privée → connexion Google → arrivée **sur la fiche** ; (6) touche
retour d'Android → la fiche se ferme, l'app reste ouverte. Les réserves du §13.1 (contacts, connexion, Android) sont levées.

---

## 14. POINT 2 — RE-AUDIT DU 26/10 : « chaque écran garde sa mémoire » (rien codé)

**Aujourd'hui** : **un seul** jeu de filtres pour toute l'app (`filters`, l. 12915 ; ~25 critères : recherche, statut,
archive, négociateur, agence, mandat, diffusion…) et des pages par liste (`dossierPage`, `mandatPage`, `contactPage`,
`workItemPage`). **Chaque changement d'écran passe par `openScreen`** (l. 15075), qui **remet tout à zéro** : filtres
par défaut de l'écran (`defaultFiltersForScreen`, l. 6750), pages à 1, élargissement aux archives annulé, raccourcis de
chiffres effacés. Constat N4 du 23/10 : « Bellevue » sur Annonces → Contacts → Annonces = **recherche perdue**. Et depuis
le point 1, **« précédent » vers une liste** passe aussi par `openScreen` → la recherche est perdue au retour.

**Les deux sortes d'entrées sur un écran** (c'est ce qui commande la conception) :

| entrée | où | ce qu'on attend |
|---|---|---|
| **le menu** (bureau l. 23189-23196, téléphone `onNavigate`) et **précédent / suivant** | `openScreen` | **retrouver** sa recherche |
| **les raccourcis** : tuiles chiffrées de l'Accueil (l. 24442), « Voir toutes », « Détail », « Ouvrir le suivi Pauline », « Registre des mandats », « Contrôle contacts » (l. 24458-24524) ; chiffres cliquables (`openMandatDrilldown`, `openRegisterDrilldown`) ; recherche d'un contact par son numéro (`showContactInDirectory`) ; lien des e-mails | `openScreen` ou leurs propres réglages | une **vue précise** : la tuile « Portefeuille actif 3 » doit montrer **3**, pas la recherche d'il y a dix minutes |

**Ce que ça pourrait casser** :
- ⚠ une **tuile de l'Accueil** qui ouvrirait un écran avec une vieille recherche → un chiffre qui ment → les raccourcis
  doivent **garder la vue par défaut**, comme aujourd'hui ;
- ⚠ la **recherche d'un contact par son numéro** (retour depuis une annonce, lien d'adresse) pose une recherche
  technique (`query = numéro`) : il ne faut **pas** la mémoriser comme « la recherche de l'utilisateur » ;
- ⚠ le **Suivi** a un filtre posé à l'ouverture (`pending_or_in_progress`, l. 15083) et les raccourcis chiffrés ont
  un **titre** (`mandatDrilldownLabel`…) : mémoriser le filtre **sans** son titre afficherait une liste filtrée sans
  dire pourquoi → mémoriser les deux ensemble ;
- une recherche mémorisée **oubliée** fait croire à des données manquantes → elle reste **visible** : les filtres actifs
  s'affichent déjà en étiquettes (l. 23811) et le bouton « Réinitialiser » existe ;
- `Estimations` et `Annonces` partagent aujourd'hui le même jeu de filtres → une mémoire **par écran** les sépare.

**Hors point 2** (noté) : la **position dans la page** (le défilement) — à part, après ; les filtres **dans l'adresse**
(lien d'une recherche) — possible plus tard, pas maintenant.

### 14.1 ✅ POINT 2 CODÉ ET CONTRÔLÉ EN DÉMONSTRATION (26/10, choix « A » de Frédéric)

**Le code** (`App.tsx`) : interrupteur `MEMOIRE_DES_ECRANS = true` ; une mémoire **par écran** (recherche et filtres,
élargissement aux archives, pages, titre et filtre d'un raccourci, filtre du Suivi), rangée **au départ** de l'écran
quel que soit le chemin, gardée pour l'onglet (`sessionStorage`) et effacée au **vrai** passage connecté → déconnecté
(pas au démarrage, sinon F5 la perdrait). `openScreen(écran, { vueParDefaut })` : le **menu** et **précédent/suivant**
rendent la mémoire ; les **deux accueils** (bureau et téléphone) passent `ouvrirEcranParDefaut` (vue précise, comme
avant). Les autres raccourcis (chiffres cliquables, recherche d'un contact par son numéro, lien des e-mails) posaient
déjà leur propre vue sans `openScreen` : inchangés. La recherche technique d'un contact par son numéro n'est **pas**
mémorisée. Au passage (point 1) : l'adresse qui rouvre une fiche passe par `openScreen` → la liste **derrière** la fiche
retrouve aussi sa mémoire.

⚠ **Trouvé par le contrôle, et corrigé** : les étiquettes de filtres actifs ne s'affichent **que panneau ouvert**
(l. 23897) — un filtre mémorisé aurait été invisible. Le bouton dit désormais **« Filtres (N) »**, N = ce qui **diffère
de la vue par défaut** de l'écran (le panneau, lui, compte aussi « Archive : Actives » et « Statut : Actif / offre /
compromis » — un compteur à 2 en permanence aurait menti).

**Contrôles** (`npm run build` vert avec les types ; démonstration, bureau) :

| essai | résultat |
|---|---|
| Annonces : « Bellevue » → menu Contacts → menu Annonces | **« Bellevue » retrouvée**, 1 ligne |
| précédent ×2, suivant ×2 | « Bellevue » retrouvée à chaque passage sur Annonces |
| **F5** sur la liste | « Bellevue » retrouvée |
| raccourci « Détail » de l'Accueil | Annonces en **vue par défaut** (3 lignes, sans recherche) |
| Annonces « Fauriel », Estimations « Bellevue », allers-retours | chaque écran garde **la sienne** |
| « Réinitialiser » sur Estimations | vide Estimations seulement ; Annonces garde « Fauriel » |
| bouton Filtres | « Filtres (1) » avec « Fauriel » ; « Filtres » sur les vues par défaut (Annonces, Estimations, Mandats) |
| console | aucune erreur |

⚠ **Non éprouvé en démonstration** : l'écran Contacts (aucun contact) ; une vraie déconnexion (pas de connexion en
démonstration) ; le format téléphone. → essais réels avec Frédéric.

### 14.2 ✅ POINT 2 PROUVÉ EN PRODUCTION (26/10, en ligne à 11:45:17, `index-DaNalipJ.js`)

Frédéric : **les 5 essais réels sont bons** (Annonces, Contacts, raccourci de l'Accueil en vue par défaut, téléphone,
déconnexion). ⚠ Un premier « souci » (« Bellevue » perdue) venait de l'**ancien code** : journaux de l'API, la liste
redemandée **sans** « Bellevue » à 11:45:14 — **3 s avant** la mise en ligne (11:45:17) ; après rechargement, la liste
est redemandée **avec** « Bellevue » (11:46:27). Leçon : après un déploiement, l'onglet ouvert garde l'ancien code
tant qu'on ne recharge pas — vérifier l'heure de l'essai contre l'heure de mise en ligne avant de chercher un défaut.

---

## 15. POINT 3 — RE-AUDIT DU 26/10 : « ouvrir ce qu'on crée, refléter le geste au clic » (rien codé)

Le point 3 regroupe les **lots 1 à 3 du §8.6** (11 correctifs). Revérifié sur le code du 26/10 (après les commits ⑧) :

| constat | re-vérifié le 26/10 | où |
|---|---|---|
| **A1** créer une annonce : la fenêtre se ferme, **rien ne s'ouvre** | ✅ toujours vrai | `handleCreateDraftAnnonce`, l. 16523 |
| … alors que **notre numéro est connu au clic** | ✅ `payload_json.app_dossier_id` = 10000001, 10000006, 10000009 | `app_console_job` |
| **A2** créer un contact : rien ne s'ouvre | ✅ toujours vrai (5 hôtes : annuaire bureau et mobile, fiche annonce ×2, agenda) | `HektorContactIdentityForm`, l. 38997 |
| … notre numéro au clic | ✅ `payload_json.app_identite` = 20000010 … 20000015 | `app_console_job` |
| **F0** la rubrique **Affaires** du cockpit ne se relit qu'au **changement de fiche** ; le cockpit ne reçoit **aucun** signal de rechargement | ✅ toujours vrai | `CockpitDetail`, effet l. 29051-29092 sur `[ckDossierIdPourRegistre]` |
| **F1** gestes d'affaire (refuser / accepter une offre, annuler / supprimer un compromis ou une vente) : modale fermée, **rien ne se recharge**, travail **non suivi** | ✅ toujours vrai | `handleGesteHektor`, l. 17862-17863 |
| **B1** archiver, désarchiver, statut, négociateur : le travail est suivi, mais l'écran ne se recharge **qu'à sa fin** (~1 min) alors que la base est à jour **au clic** (RPC `*_optimistic`) | ✅ toujours vrai | l. 16633, 15219, 17011, 17929 |
| A3, A4, B2, F6, F8, F10 | repris de l'audit du 23/10 — **à revérifier au moment de les coder** | §5, §8 |

**Proposé : le découper en TROIS sous-lots, expliqués et contrôlés un par un.**

| sous-lot | contenu | ce que l'utilisateur verra | ce que ça pourrait casser |
|---|---|---|---|
| **3a — ouvrir ce qu'on crée** | A1 (annonce → sa fiche, par notre numéro) · A2 (contact → sa fiche, par notre numéro) | après « Créer », la fiche de l'objet créé **s'ouvre** et la liste le montre | ⚠ un contact créé **depuis l'agenda** (saisie d'un RDV) ne doit **pas** faire changer d'écran : on reste dans le RDV ; ⚠ la file des **photos de la création** se rattache à son dossier par le travail suivi — ouvrir la fiche ne doit rien y changer (à éprouver) |
| **3b — les rubriques se relisent** | F0 : Affaires, Documents du cockpit, signatures, panneau Documents branchés sur le signal de rechargement | une offre, un compromis, un document généré apparaissent **sans rouvrir la fiche** | ⚠ un rechargement ne doit **ni vider la rubrique** (clignotement) **ni effacer une saisie en cours** (note, condition) → garder l'affichage pendant la relecture ; ⚠ le signal part souvent (fin de chaque travail) |
| **3c — refléter le geste au clic** | F1 · B1 · B2 · A3 · A4 · F6 · F8 · F10 | l'écran change **à la seconde du clic**, plus une minute après | si Hektor **refuse**, le worker remet l'ancien état en base : l'écran le reflètera **à la fin du travail** (le rechargement existe) — il faut que F1 suive son travail pour ça |

**Recommandé : 3a d'abord** (le cœur de la demande initiale, et le numéro est déjà là), puis 3b, puis 3c. Tout est
**front seul**, derrière un interrupteur par sous-lot, et n'écrit rien chez Hektor.

### 15.1 SOUS-LOT 3a CODÉ (26/10, « code le sous-lot 3a ») — ⚠ NON ÉPROUVÉ À L'ÉCRAN

**Le code** (`App.tsx`) : interrupteur `OUVRIR_CE_QU_ON_CREE = true` ; `numeroCreeDansLeTravail(job, clé)`.
- **A1** (`handleCreateDraftAnnonce`) : après « Créer », relecture de la liste et `openDossierDetailPage(notre n°)`.
  Vérifié avant de coder : la création passe par `app_create_annonce_job_optimistic` (création provisoire allumée,
  `PROVISIONAL_CREATION_ENABLED = true`), qui écrit la ligne dans `app_dossier_current` **dans la transaction du clic** ;
  la fiche lit `app_dossiers_current`, qui montre bien 10000006 et 10000009 (statut Estimation). La file des photos et
  du scan suit le **travail** (`rememberHektorActionJob`), pas la fiche : inchangée.
- **A2** (`surTravailDeLAnnuaire`) : branché **seulement** sur l'annuaire (bureau `ContactsScreen`, téléphone
  `MobileContactCards`) → `showContactInDirectory(notre n° ≥ 20 M)`. Les deux créations **depuis un RDV**
  (`GoogleAgendaGlobalEventModal`, `GoogleAgendaAnnonceSection`) ne passent **pas** ici : on reste dans le RDV.

**Contrôles** : `npm run build` vert avec les types. ⚠ **La démonstration ne peut pas créer** (« Supabase is not
configured ») : le parcours n'est **pas** éprouvé. ⚠ Et la modale « Suivi de l'action » s'affiche toujours à la
création (son retrait est le point 6) : elle se superposera à la fiche ouverte.

➡ **Seul juge : une création réelle** — elle écrit chez Hektor, donc **avec l'accord de Frédéric** et sur un essai
qu'il choisit (contact d'essai à supprimer ensuite, par exemple).

### 15.2 ✅ A2 PROUVÉ EN PRODUCTION (26/10, 12:10, essai fait par Claude dans le Chrome de Frédéric, à sa demande)

En ligne à **12:07:08** (`index-ieQDEkZX.js`). Annuaire → « Nouveau contact » → compte **« FRANCK GERPHAGNON – Compte
formation »**, Propriétaire, **M. ESSAI 3A / A SUPPRIMER**, mobile fictif **06 99 99 03 26**, **sans e-mail** (aucun
e-mail RGPD possible), étape 2 « Terminer » (aucune annonce reliée) → « Créer le contact ».

| | résultat |
|---|---|
| clic | 12:10:46 |
| ~2 s après | l'adresse passe à `?ecran=contacts&contact=20000016` et **la fiche du contact créé est ouverte** (capture : « M. A SUPPRIMER ESSAI 3A », mobile 0699990326) |
| base | `app_console_job` : `app_identite` **20000016**, contact **présent dans `app_contact_current`** au clic |
| Hektor | travail `done` à 12:10:55, contact Hektor **605997** |

⚠ La modale « Suivi de l'action » s'affiche **par-dessus** la fiche ouverte (attendu ; son retrait = point 6).
⚠ Un 1er essai avec le mobile 06 00 00 00 00 a déclenché « Doublon possible » (2 contacts réels le portent) :
**annulé avant création** (vérifié : aucun travail créé), refait avec un numéro unique.
⚠ La fiche affiche « Négociateur : Non affecté — Compte formation » : comportement existant de la création, noté.

✅ **Contact d'essai SUPPRIMÉ par Frédéric** (26/10, travail `delete_hektor_contact` `done` à 13:01:09) : Hektor
  **605997** supprimé (`hektor_delete_sent: true`, relu ensuite **introuvable** : `after_found: false`), et 0 ligne
  restante dans `app_contact_current` pour 20000016 / 605997.
⬜ **A1 (annonce) non éprouvé** : créer une annonce écrit un brouillon chez Hektor — essai à décider par Frédéric.

---

## 16. SOUS-LOT 3b — RE-AUDIT DU 26/10 : « les rubriques se relisent » (rien codé)

**Les rubriques qui ne se relisent qu'au CHANGEMENT DE FICHE** (revérifié sur le code du 26/10) :

| rubrique | où | aujourd'hui |
|---|---|---|
| **Affaires** (offres, compromis, ventes, carnet, répartition, conditions, note, notaires) — bureau | `CockpitDetail`, effet l. 29088 sur `[ckDossierIdPourRegistre]` | relue au changement de fiche ; ⚠ elle se **vide** d'abord (`setCkRegistreAffaires(null)`) |
| **Affaires** — téléphone | `MobileDossierDetail`, l. 37051 sur `[mobDossierId]` | idem |
| **Documents du cockpit** | `CockpitDetail`, l. 29229 sur `[dossier?.app_dossier_id]` | idem |
| **Suivi des signatures** | `MandatSignatureTracker`, l. 11047 sur `[dossier.app_dossier_id]` | idem |
| **Panneau Documents** | `ConsoleDocumentsPanel`, l. 11151 | relu au changement de fiche ; sonde toutes les 8 s **seulement** s'il a lui-même un document « en cours » |

**Le signal de rechargement** (`dataReloadKey`) part : à la **fin d'un travail suivi** qui concerne l'écran
(+600 ms, `jobConcernsThisScreen`, l. 14041) ; après une **modification** d'annonce / contact / recherche ; 25, 55 et
90 s après le retour d'une recherche ; après une **création** (3a) ; après une **date de clôture**. Il ne relit
aujourd'hui que la liste, la fiche, le contact et les dates de clôture.

**Ce que 3b corrige** : brancher ces cinq rubriques sur ce signal. Concrètement :
- une **offre, un compromis, une vente créés** par la fenêtre « statut » (travail **suivi**, l. 17929 + 59) apparaissent
  dans Affaires **à la fin du travail**, sans rouvrir la fiche ;
- les **documents** et l'**état des signatures** se relisent à chaque signal.

**Ce que 3b NE corrige PAS** (le dire pour ne pas promettre trop) :
- les **gestes sur une affaire existante** (refuser / accepter une offre, annuler / supprimer un compromis ou une
  vente) : leur travail **n'est pas suivi** → pas de signal → c'est **3c** (recharger au clic) ;
- l'**avis de valeur généré** (`generate_estimation_pdf`) : non suivi → point 6 (indicateurs) ;
- le délai : la mise à jour arrive **à la fin du travail Hektor** (~1 min), pas au clic → c'est **3c**.

**Ce que ça pourrait casser** :
- ⚠ **le clignotement** : l'effet Affaires vide la rubrique avant de relire → au rechargement, on **garde l'affichage**
  et on ne vide qu'au **changement de fiche** ;
- **une saisie en cours** : la carte `CkAffaires` (l. 27514-27645) est un **pur affichage** (aucun champ, aucun état
  local) ; les modifications d'affaire passent par des fenêtres à part → rien à perdre. Le panneau Documents garde
  son état « en cours » (téléversement) : il relira **sans** l'effacer (il le fait déjà toutes les 8 s) ;
- **la charge** : 6 lectures Supabase pour la seule fiche ouverte, à chaque signal (pas Hektor) ;
- (constat, pas touché) dans `CockpitDetail`, des effets sont déclarés **après** un `return` anticipé (l. 29225) —
  écart à la règle des hooks React, existant.

Interrupteur proposé : `RUBRIQUES_SE_RELISENT`. Front seul, rien chez Hektor.

---

## 17. 3b + 3c ENSEMBLE — « l'écran suit le clic » (re-audit du 26/10, rien codé)

*Frédéric : « pourquoi il n'y a pas un comportement en temps réel, puisque tout est écrit chez nous sauf quelques
gestes ? »* → Réponse : l'écran a gardé le réflexe « Hektor d'abord » (attendre la fin du travail) alors que la base est
passée « chez nous d'abord » (chantier ③, 14/10). Le **vrai temps réel** (voir les gestes des AUTRES) est un chantier à
part, déjà étudié le 10/10 (`AUDIT_RELECTURES_OUVERTURE_2026-10-09.md` §6 : faisable par signaux Broadcast, pas
nécessaire tout de suite). Décision du 26/10 : **3b et 3c ensemble**.

**Le principe** : après chaque geste, **relire tout de suite** (la donnée est déjà chez nous), rubriques comprises (3b),
puis **encore une fois à la fin du travail Hektor** (filet : si Hektor refuse, le worker remet l'ancien état en base).

| geste | écrit chez nous au clic ? | aujourd'hui (revérifié) | proposé |
|---|---|---|---|
| **refuser / accepter une offre, annuler / supprimer un compromis ou une vente** (F1) | ✅ `app_geste_affaire_optimistic` | la fenêtre se ferme, **rien ne bouge** ; travail **non suivi** (`handleGesteHektor`, l. 17862) | relire au clic **et suivre le travail** (relire à sa fin) |
| **changer le statut, créer offre / compromis / vente** (B1, F2) | ✅ `app_change_annonce_status_optimistic` | liste à la fin (~55 s), **Affaires jamais** | au clic + à la fin, Affaires comprises |
| **archiver / désarchiver** une annonce (B1) | ✅ `app_archive_…` / `app_restore_annonce_optimistic` | à la fin (~1 min) | au clic + à la fin |
| **affecter un négociateur** (B1) | ✅ `app_assign_negotiator_optimistic` | à la fin | au clic + à la fin |
| **créer une recherche** (A3) | ✅ (écrite avec le travail, `ContactSearchModal` l. 80) | invisible jusqu'au retour de Hektor : la création **n'émet pas** `hektor:search-updated` (seule la modification le fait, l. 73) | émettre le même signal à la création |
| **supprimer une recherche** (B2) | ⛔ **non** : travail seul (`app_console_create_delete_contact_search_job`) | disparaît au retour de Hektor | afficher « suppression en cours » au clic, retirer à la fin — **pas** de retrait optimiste (si Hektor refuse, elle doit rester) |
| **lier / retirer un mandant** (A4, F10) | ✅ `app_link_mandant_optimistic` / `app_unlink_…` | le bloc des mandants ne se relit qu'au changement d'annonce (l. 3336, 3630 : `onJobCreated` seul) | brancher le bloc sur le signal, relire au clic |
| **« Abandonner ce geste »** (F8) | ✅ valeurs **remises en base** | la fiche **affiche encore les valeurs abandonnées** (`GesteAbandonneBanner`, l. 35660-35676 : message seul) | relire la fiche au clic |
| **accepter une demande d'annulation** (F6) | ✅ date de clôture écrite au clic | registre relu à la fin du travail « Clos » | relire au clic (⚠ circuit **dormant** : 0 demande depuis le 02/06) |
| **activer un brouillon** | ⛔ non optimiste | à la fin | **inchangé** |

**3b (rubriques relues)** : Affaires (bureau + téléphone), Documents du cockpit, signatures, panneau Documents, **et le
bloc des mandants** → branchés sur le signal, **sans se vider** pendant la relecture (§16).

**Ce que ça pourrait casser** :
- **F1 suivi** : suivre ces travaux fera apparaître la modale « Suivi de l'action » pour ces gestes aussi (comme pour les
  autres, jusqu'au point 6). C'est ce qui permet de voir un **refus de Hektor** (état remis) à la fin du travail ;
- **plus de relectures** : une de plus par geste (liste + fiche ouverte), dans notre base seulement ;
- **un geste refusé par Hektor** s'affichera d'abord comme réussi (au clic), puis reviendra à la fin du travail. C'est
  déjà la règle de la base (« chez nous d'abord, Hektor confirme ») — l'écran la rend visible ;
- la suppression de recherche **n'est pas** rendue optimiste : seulement un état « en cours ».

Front seul, rien chez Hektor, interrupteur `L_ECRAN_SUIT_LE_CLIC`.

---

## 18. LE TABLEAU COMPLET — TOUS LES GESTES D'ÉCRITURE DE L'APP (26/10, relevé dans le code)

*Frédéric : « il manque beaucoup de gestes, tu as listé que ceux qui changent ? »* — oui : le §17 ne listait que les
gestes que 3b + 3c touchent. Règle du 21/09 : **balayer TOUS les objets et TOUS les gestes**.

**Méthode** : relevé automatique de **toutes** les fonctions de `lib/api.ts` qui écrivent (appel `rpc`, `insert / update /
delete`, ou appel serveur `POST / PATCH / DELETE`) — **99 fonctions**, appelées à **169 endroits** des écrans — puis, pour
chaque appel, ce que l'écran fait juste après (relecture, mise à jour locale, suivi du travail, signal, rien), et
**vérification à la main** des « rien » douteux (agenda, rapprochement, fenêtre statut). **10 fonctions ne sont
appelées par aucun écran** (code mort, en bas). Légende : ✅ déjà instantané · 🔧 **3b+3c** · ⏳ attend vraiment Hektor →
**point 6** (indicateur dans l'objet) · ⛔ hors navigation.

| objet | geste | écrit chez nous au clic ? | l'écran aujourd'hui | verdict |
|---|---|---|---|---|
| **annonce** | créer | ✅ | ✅ **ouvre la fiche (3a, 26/10)** | ✅ |
| | modifier (formulaire, édition dans la fiche, « Reporter dans la fiche ») | ✅ | signal `hektor:annonce-updated` / mise à jour locale | ✅ |
| | modifier depuis l'éditeur d'estimation (`save`, l. 5177) | ✅ | ❔ aucun signal relevé | 🔧 à vérifier au codage |
| | changer le statut, créer offre / compromis / vente | ✅ | liste à la fin du travail, **rubrique Affaires jamais** | 🔧 |
| | archiver | ✅ | à la fin du travail | 🔧 |
| | désarchiver | ✅ | rouvre la fiche, liste à la fin | 🔧 |
| | affecter un négociateur | ✅ | à la fin du travail | 🔧 |
| | supprimer | — | retrait local immédiat | ✅ |
| | activer un brouillon | ⛔ non | à la fin du travail | ⏳ inchangé |
| | préparer la fiche d'une archive / d'un historique / d'un brouillon | — | état « préparation » en ligne | ✅ |
| | relire depuis Hektor (ouverture d'une fiche) | — | silencieux (point 0) | ✅ |
| | Diffusable, Validé, passerelles | appel **direct** Hektor | mise à jour à la réponse | ✅ |
| | numéro de mandat automatique (PROTEXA) | ⛔ vient de Hektor | à la fin du travail | ⏳ point 6 (C1) |
| | Matterport (en ligne, hors ligne, archiver, réactiver) | ⛔ non | à la fin du travail | ⏳ point 6 (C3) |
| | date de clôture du mandat | ✅ | relecture immédiate | ✅ |
| **transaction** | refuser / accepter une offre, annuler / supprimer un compromis ou une vente | ✅ | **rien ne bouge**, travail non suivi | 🔧 |
| | conditions, note, commission, répartition (écrites avec la fenêtre statut) | ✅ | **Affaires jamais relue** | 🔧 |
| | trancher un écart du carnet / fermer un écart de personne (R4) | ✅ | aucune relecture relevée | ⛔ **chantier ⑧ de l'autre session** — à coordonner, pas touché |
| **contact** | créer (annuaire) | ✅ | ✅ **ouvre la fiche (3a, prouvé 26/10)** | ✅ |
| | créer pendant la saisie d'un RDV | ✅ | reste dans le RDV | ✅ voulu |
| | modifier, archiver / réactiver, supprimer | ✅ | signal / mise à jour locale | ✅ |
| | trancher un contact « en attente » (`resolveContactPending`) | ✅ | **aucune relecture** | 🔧 |
| | envoyer un e-mail (Gmail) | ⛔ Gmail | l'onglet Échanges ne se relit pas | ⏳ point 6 (F7) |
| **recherche** | créer | ✅ | **invisible jusqu'au retour de Hektor** | 🔧 |
| | modifier | ✅ | signal + relectures à 25 / 55 / 90 s | ✅ |
| | supprimer | ⛔ travail seul | disparaît au retour de Hektor | 🔧 état « suppression en cours » |
| **mandant / relation** | lier, retirer, créer, modifier le contact mandant | ✅ | bloc des mandants relu au changement d'annonce seulement | 🔧 |
| **documents** | préparer, téléverser, supprimer | — | le panneau suit et relit (8 s) | ✅ |
| | marquer signé à la main | ✅ | relecture | ✅ |
| | relancer / annuler une signature | — | travail suivi, **état des signatures non relu** | 🔧 relu (3b) + ⏳ point 6 (F3) |
| | générer l'avis de valeur PDF | ⛔ worker | aucune relecture des documents | ⏳ point 6 (F4) |
| | générer le mandat PDF, le plan cadastral | ⛔ worker | l'éditeur sonde / relecture | ✅ (+ 3b relit Documents) |
| **photos** | ajouter, supprimer, couverture, réordonner, masquer / afficher, synchroniser | ✅ ou travail suivi | le panneau relit (9, 22, 25 s…) | ✅ |
| **RDV / agenda** | créer, modifier, supprimer (planning, fiche annonce, fiche contact, rapprochement) | Google | relecture du planning | ✅ |
| **rapprochement** | proposer, écarter, rétablir, relances, e-mail | ✅ | mise à jour locale immédiate | ✅ (⚠ « Rétablir » avale ses erreurs, §8.5) |
| **demandes** | créer, corriger, refuser ; accepter une diffusion ou une baisse | ✅ | relecture / mise à jour | ✅ |
| | accepter une **annulation** | ✅ date | registre relu à la fin du travail « Clos » | 🔧 (circuit dormant) |
| **geste abandonné** | « J'ai refait » / « Abandonner ce geste » | ✅ valeurs remises | message seul, **fiche non relue** | 🔧 |
| | trancher une annonce « en attente » (`resolveAnnoncePending`) | ✅ | **aucune relecture** | 🔧 |
| **estimation** | sources (DVF, cadastre, DPE…), brouillon de scan, textes (rédacteur) | ✅ | relecture / mise à jour locale | ✅ |
| **notifications, alertes** | marquer lu, Résolu / Pris en charge | ✅ | mise à jour locale | ✅ |
| **utilisateurs** | créer | serveur | **liste non relue** | 🔧 (F9, une ligne) |
| | modifier, envoyer la réinitialisation du mot de passe | serveur | relecture / rien à montrer | ✅ |

**Code mort — 10 fonctions d'écriture qu'aucun écran n'appelle** : `editAffaireOptimistic`, `setDossierDiffusable`,
`createAnnonceProvisional`, `seedDefaultDiffusionTargetsOnHektor`, `createSyncConsoleDocumentsJob`,
`createLinkHektorMandantJob`, `createHektorContactSearchJob`, `createUpdateHektorContactSearchJob`,
`createUpdateHektorContactJob`, `createUpdateHektorAnnonceFieldsJob` (remplacées par leurs versions « optimistes »).

**Bilan** : sur ~45 gestes, **~27 déjà instantanés**, **14 relèvent de 3b+3c** (dont 4 que le §17 ne listait pas :
conditions / note / commission / répartition, contact « en attente », annonce « en attente », création d'utilisateur),
**5 attendent vraiment Hektor** (point 6), **1 appartient au chantier ⑧** (écarts R4).

---

## 19. ✅ 3b + 3c CODÉS ET CONTRÔLÉS EN DÉMONSTRATION (26/10, « Ok pour 3b et 3c ») — ⚠ NON ÉPROUVÉS EN RÉEL

Front seul (`App.tsx`, `ContactSearchModal.tsx`), rien en base, rien chez Hektor. Interrupteur **`L_ECRAN_SUIT_LE_CLIC`**
(`false` = l'ancien comportement, en une ligne).

**La mécanique (3 pièces)**
- `relireApresLeGeste()` (dans l'app) : relit tout de suite (`dataReloadKey`), puisque la donnée est déjà chez nous. La
  relecture de **fin de travail** (+600 ms, existante) reste le filet : si Hektor refuse, le worker remet l'ancien état
  et l'écran le montre.
- `signalerGeste()` (composants enfants : mandants, geste abandonné, « en attente » tranché) : émet
  `hektor:geste-fait`, que l'app écoute comme les signaux annonce / contact / recherche. Pas de props à tirer.
- **3b** : chaque relecture de l'app est relayée aux rubriques par `hektor:relire-rubriques` (hook
  `useRelectureRubriques`). Les rubriques **ne se vident qu'au changement de fiche** (mémoire de la dernière fiche
  lue) : une relecture de la même fiche garde l'affichage jusqu'à la réponse, et une relecture ratée garde ce qui
  est affiché.

**Les rubriques branchées (3b)** : Affaires du cockpit (registre + carnet, répartition, conditions, notes ; les noms de
notaires déjà lus sont gardés le temps de les relire), Documents du cockpit, Affaires du téléphone, état des
signatures (`MandatSignatureTracker`), panneau Documents (relu **en silence**, sans « chargement »), mandants en
création (`MandantsEnCreation` — ⚠ il n'est rendu que dans l'ancienne fiche `DossierDetailLayoutBase` ; dans le
cockpit de production, les mandants viennent de la fiche elle-même, relue par la même relecture).

**Les gestes (3c)** — les 14 du §18 :

| geste | ce qui est fait |
|---|---|
| changer le statut / créer offre-compromis-vente + commission, conditions, note, répartition | relit à la fin de la saisie (tout est écrit), Affaires comprises |
| refuser / accepter une offre, annuler / supprimer un compromis ou une vente (F1) | relit au clic **et le travail est enfin suivi** (`job_id` de la RPC → `loadConsoleJobsByIds` → suivi) ⚠ la fenêtre « Suivi de l'action » apparaîtra donc aussi pour ces gestes (jusqu'au point 6) |
| archiver, désarchiver, affecter un négociateur | relit au clic (en plus de la fin du travail) |
| créer une recherche | émet `hektor:search-updated` comme la modification → la ligne « en création » se voit tout de suite |
| supprimer une recherche | **pas** de retrait optimiste : « Suppression en cours… » reste sur la ligne **tant que le travail vit** (sondage 5 s du seul travail), puis relecture. Les deux fiches contact (ancienne et V2 ; la V2 n'avait qu'une icône → texte ajouté) |
| lier, retirer, créer, modifier un mandant | `signalerGeste()` après le travail |
| « Abandonner ce geste » / « J'ai refait » (bandeau) | `signalerGeste()` : la fiche ne montre plus les valeurs abandonnées. Le message « Remis comme Hektor : … » reste affiché |
| trancher un contact / une annonce « en attente » | `signalerGeste()` |
| accepter une demande d'annulation (F6) | relit dès que la date est posée chez nous |
| créer un utilisateur | la liste des utilisateurs se relit |
| corriger un champ depuis l'éditeur (estimation / mandat, l. ~5177) | ⛔ **volontairement inchangé** : la valeur est déjà mise à jour sur place (`onSaved`), et relire la fiche ferait lever à l'éditeur ouvert son bandeau « la fiche a changé » (`draftStale`) pour la correction qu'on vient de faire |

**Contrôle hors ligne** : `npm run build` vert. **Démonstration** (mode mock, fiche 32621, cockpit 1440 px puis
téléphone 375 px), par lecture de l'état React :
- 1 signal `hektor:geste-fait` → **1** `hektor:relire-rubriques` → le compteur du cockpit passe **0 → 1**, celui des
  signatures **0 → 1**, celui de la fiche téléphone **0 → 1** ;
- **aucun clignotement** : longueur du texte de la fiche échantillonnée toutes les 15 ms pendant 2 s (105-107
  échantillons) — Affaires 1 541 / 1 541, Mandat 2 774 / 2 774, téléphone 3 156 / 3 156 ;
- aucune erreur JavaScript (les seules erreurs sont les 500 de `/api/...`, absent en démonstration, déjà là avant).
⚠ **Limite honnête** : la démonstration n'a pas de base — ses Affaires sont vides, donc l'absence de clignotement y
est prouvée sur une rubrique sans lignes ; et aucun geste réel n'a pu partir (les RPC n'existent pas en démonstration).

**Ce qui reste : l'essai réel** (à faire avec Frédéric, sur une fiche qu'il choisit) — voir la liste donnée en fin de
session.

### 19.1 ESSAIS RÉELS (26/10, 12:44-12:52, faits par Claude dans le Chrome de Frédéric, à sa demande : « fais-le toi-même »)

En ligne : `index-BFoQ-fUF.js` (contient `hektor:relire-rubriques` et `hektor:geste-fait`, vérifié).

| essai | cible | résultat |
|---|---|---|
| **créer une recherche** | contact d'essai 20000008 (« Creation ESSAI 8A B2 », Hektor 605946), Maison, Firminy, 120-250 k€ | ✅ **visible « En création… » ~2 s après le clic, sans recharger** (avant : ~1 min). Travail `ecf9d13b` done en 13 s, resynchro `fc1f9f7b` done 13 s plus tard ; la ligne est passée **d'elle-même** à « Active · Firminy 42700 » 0,6 s après |
| **supprimer cette recherche** | même contact, index 1 | ⚠ l'état « Suppression en cours… » **n'a pas pu être capturé** (mes lectures de la page ont expiré à 45 s). Travail `e43aff82` done en 11 s, résultat `status: archived, idCritere 471880` — ⛔ **MAIS HEKTOR NE L'A PAS ARCHIVÉE** : le détail du contact relu par Hektor à 12:45:55 (13 s après) porte toujours la recherche Firminy en `archive: "0"`, donc notre base la garde active (local et Supabase, contrôlé à 12:47:46). Le worker (`handleDeleteHektorContactSearch`, l. 19636) **ne vérifie pas** l'archivage : il renvoie « archived » sur la seule réponse (`desarchiveCritere: true`). **Hors 3b/3c — défaut du geste lui-même, NOTÉ, PAS TRAITÉ.** À revoir après la nuit (si un délai de Hektor, la recherche passera inactive au run) |
| **créer puis refuser une offre** | 62965 « TEST C13 … à supprimer » (62774 est close : hors `app_dossier_current`) | ⛔ **NON FAIT, volontairement** : l'annonce n'a pas de mandat et la fenêtre dit « N° de mandat : attribué automatiquement si vide » → envoyer l'offre aurait fait **attribuer un vrai numéro de mandat** à une annonce d'essai (irréversible). Fenêtre fermée sans envoi (0 travail, vérifié) |
| **lier puis retirer un mandant** | 62965 | ⛔ **NON FAIT** : « Rattacher un mandant existant » ne cherche que les contacts **du négociateur de l'annonce** (gonzalez) ; aucun contact d'essai n'est à lui (20000009 → « Aucun contact trouvé pour ce négociateur »). Annulé sans envoi |

**Vu en passant** :
- ⚠ la fenêtre « Suivi de l'action » a titré la suppression de recherche **« Création d'une annonce »** (job `e43aff82`), alors que l'étiquette du type existe (`api.ts:3111`, « Suppression d'une recherche acquereur »). Cause non mesurée ; la fenêtre doit disparaître au point 6 ;
- ✅ le bouton **Précédent** du navigateur a rouvert la fiche 62965 (point 1, encore bon).

**Reste à éprouver en réel** : la rubrique Affaires après une offre (il faut une annonce d'essai **avec mandat**), le refus d'offre suivi, le mandant, « Abandonner ce geste ». ➡ À Frédéric de désigner une annonce d'essai avec mandat et un contact d'essai du bon négociateur — ou de faire ces gestes lui-même sur un vrai dossier.

### 19.2 ⚠ CORRECTION (26/10, question de Frédéric : « ton worker est-il en erreur ? supprimer veut dire archiver »)

**Le worker n'est pas en erreur** : 4 services `Running`, 95 travaux en 24 h dont 1 seul en erreur (relecture du contact
d'essai 20000016, supprimé ce matin — attendu). Le travail `e43aff82` est `done`, son journal est complet.

**Mon « Hektor ne l'a pas archivée » (§19.1) était PRÉMATURÉ.** C'était déjà écrit : *supprimer = archiver en posant une
date* (plan, tâche 4bis du 21/08 ; mémoire « feature recherche contact ») — `modifDateArchiveCritere` avec
`dateArchive` = aujourd'hui. Ce geste **programme** l'archivage ; rien ne dit qu'il bascule `archive` à la seconde.
Les deux suppressions passées qu'on peut relire ont bien fini archivées (414535 du 12/06 → `archive 1` ; 113412 du
22/06 → la recherche visée `archive 1`, l'autre `0`). **Quand** la bascule a lieu n'a jamais été mesuré.
⏰ **Témoin : la recherche Firminy de 20000008 (critère 471880) doit être `archive 1` après la nuit** (run des
recherches de 03:00). Si elle l'est, le geste marche, avec un délai.

**Ce qui reste vrai, et deux choses nouvelles (NOTÉES, pas traitées) :**
1. **3c** : « Suppression en cours… » s'efface à la fin du travail (~11 s), mais la recherche reste « Active » à l'écran
   jusqu'à la bascule chez Hektor. L'écran dit donc moins que la vérité ; à reprendre au point 6 (indicateur).
2. ⚠⚠ **Risque de VISER LA MAUVAISE RECHERCHE** (`resolveContactSearchTargetCritereId`, worker) : l'onglet Hektor lu
   (`recherche-changeTab`) n'a listé **qu'1 critère** alors que le contact en a 2 (1 archivée + 1 active) → il semble ne
   lister que les **actives**, alors que notre `search_index` compte **aussi les archivées**. Et si l'index n'est pas
   trouvé, le worker prend **la première** (`|| list[0]`). Ici c'est tombé juste par chance (une seule active). Avec
   [0 archivée, 1 active A, 2 active B] : supprimer A (index 1) viserait B, supprimer B (index 2) viserait A.
   *(« 9 actives précédées d'une archivée » au 21/08 ; « 163 contacts actifs portent des recherches archivées » au
   21/10.)* **Probable, pas prouvé** : il faudrait lire l'onglet d'un contact à 2 actives + 1 archivée. **Même
   mécanisme pour la MODIFICATION** si elle passe par l'index — non vérifié.
3. La fenêtre de suivi a titré ce travail « Création d'une annonce » — cause non mesurée.
