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

---

## 20. POINT 4 — RE-AUDIT DU 26/10 : « une vraie recherche globale » (rien codé)

*3b+3c laissé tel quel par Frédéric (« laisse et enchaîne »).*

**Ce qui existe (code + base, mesuré le 26/10)**
- La barre « Rechercher un bien, un contact, un mandat… » de l'Accueil est **décorative** : `<input readOnly value="">`
  (`App.tsx` ~24715, composant `HomeDashboardScreen`, rendu l. ~23228 et ~24119).
- Chaque écran a sa « Recherche rapide » (`App.tsx` ~23519), qui ne cherche **que dans sa liste**, et dans les annonces
  **seulement les actives** tant qu'on ne clique pas « Étendre aux archives, vendus et clos » (constat M5).
- Les recherches de liste existantes (`lib/api.ts`) : ≥ 3 caractères, `search_text ilike`, et pour un nombre aussi
  `numero_dossier`, `numero_mandat`, `code_postal` (annonces) ou `hektor_contact_id` / `hektor_target_id` (contacts).
- **Ce que porte `search_text`** : annonce = n° de dossier, titre, ville + CP, agence, négociateur — ⚠ **ni l'adresse,
  ni les mandants, ni le n° Hektor** ; contact = nom, téléphone, **e-mail** (29 773 / 29 902), négociateur, agence, rôle ;
  registre des mandats = n° de dossier, n° de mandat, titre, ville, négociateur, agence, **mandants**.

**Les 5 sources, et leur coût mesuré** (terme absent = pire cas, toute la table parcourue) :

| source | lignes | index | temps |
|---|---|---|---|
| annonces en cours (`app_dossiers_current`) | 13 512 | trigramme | 5,7 ms |
| vendues / closes (`app_historical_annonce_index_current`) | 8 955 | — | quelques ms |
| archives (`app_archive_annonce_index_current`) | 35 335 | trigramme | 7,0 ms |
| contacts (`app_contacts_current`) | 62 325 | trigramme | 5,2 ms |
| registre des mandats (`app_registre_mandats_current`) | 24 576 | ⚠ aucun (lecture complète) | 149 ms |

**Ouvrir un résultat : toutes les portes existent déjà** — annonce en cours : `openDossierDetailPage` ; vendue / close
/ archivée : `openLightweightDetailImport` (lecture seule, comme aujourd'hui) ; contact : `showContactInDirectory` ;
mandat : écran Mandats. Avec le point 1, chaque ouverture écrit son adresse → **Précédent** ramène où on était.

**Les droits** : les 5 lectures passent par les mêmes vues que les listes, donc par les mêmes règles d'accès : un
négociateur ne trouvera rien qu'il ne voie déjà dans ses listes.

### 20.0 DÉCISION DU 26/10 — 3b+3c reste EN LIGNE SANS ÊTRE ÉPROUVÉ sur ses gestes principaux

Frédéric : « on passe à 4, pas besoin de test ». **Non éprouvés en réel** : offre / statut → rubrique Affaires, refus
d'offre suivi, mandant lier / retirer, « Abandonner ce geste », archiver, affecter, acceptation d'annulation, création
d'utilisateur (aucune annonce d'essai avec mandat n'existe). Le risque est **d'affichage seulement** (front, aucune
écriture nouvelle) ; retour arrière = `L_ECRAN_SUIT_LE_CLIC = false`. ➡ Si une rubrique ne suit pas ou clignote dans
l'usage, c'est ici qu'il faut regarder en premier.

### 20.1 Ergonomie validée (26/10) et LES BLOCS DE RECHERCHE DES ÉCRANS

**Frédéric prend les 7 recommandations** : fenêtre au centre (la barre de l'Accueil ouvre la même), ordre des groupes
selon la saisie (téléphone / e-mail → contacts d'abord ; numéro → annonces et mandats d'abord), 5 par groupe +
« Voir tout », vendus / clos / archivés inclus d'office dans un groupe « lecture seule », la dernière recherche est
retrouvée, « / » ↑ ↓ Entrée Échap, loupe en haut sur téléphone ; champs : n° de dossier, de mandat, Hektor, adresse,
ville / CP, mandant, nom, téléphone, e-mail.

**Sa question** : « que fait-on des blocs de recherche actuels, qui cherchent d'abord dans l'index principal puis
proposent d'étendre ? Il faut que ce soit rapide avec le volume de tous les index. »

**Ce que fait l'écran Annonces aujourd'hui (code lu)** — `loadDossiersPage`, `lib/api.ts` ~5007 :
- la saisie part 400 ms après la dernière frappe, à partir de 3 caractères (`App.tsx` ~13815) ;
- elle cherche dans les **actives** seulement ; un bandeau « Recherche limitée » propose **« Étendre aux archives,
  vendus et clos »** — **à l'aveugle** : on ne sait pas s'il y a quelque chose à trouver avant de cliquer ;
- en mode étendu, l'écran lit **4 sources l'une APRÈS l'autre** (en cours, archives, vendus / clos, brouillons), chacune
  avec un **compte exact**, puis fusionne et trie dans le navigateur.
- côté base, **tout est déjà indexé** pour ça : 37 index « trigramme » sur les 4 sources d'annonces (texte, titre,
  dossier, mandat, ville, CP, négociateur, agence, **mandants**) et sur les contacts. ⚠ Seul le **registre des mandats
  n'en a aucun** (149 ms, lecture complète des 24 576 lignes).

**Proposition (front seul, pas de changement en base pour commencer)**
1. **Plus d'extension à l'aveugle** : pendant que la liste des actives s'affiche, l'écran **compte en parallèle** ce
   qu'il y aurait ailleurs (comptes seuls, sans lignes, sur index) et l'écrit : « Aussi : 2 vendues ou closes, 5 archivées
   — Afficher ». Rien trouvé ailleurs → pas de bouton. La liste principale n'attend pas ces comptes.
2. **0 résultat dans les actives** → l'écran étend **tout seul** et le dit (« Rien dans les actives — voici les vendues,
   closes et archivées »).
3. **Le mode étendu lit ses 4 sources EN MÊME TEMPS** au lieu de l'une après l'autre (mêmes requêtes, mêmes résultats).
4. La recherche globale fait **ses 5 lectures en même temps** ; chacune est bornée à 5 lignes.
- **Plus tard, seulement si la mesure le demande** (accord, patch à coller) : une seule fonction en base qui interroge
  les 5 sources en un aller-retour, et un index trigramme sur le registre des mandats.

**Ordres de grandeur** : côté base, 5 à 7 ms par source indexée, 149 ms pour le registre (mesuré) ; un aller-retour
navigateur → base ≈ 200 ms (mesuré le 23/10, §10.2). Gain attendu du point 3 : ~4 allers-retours enchaînés → ~1 seul
temps d'attente (**estimé, à mesurer au codage**).

### 20.2 ✅ POINT 4 CODÉ ET CONTRÔLÉ EN DÉMONSTRATION (26/10, « code le point 4 avec les 4 améliorations ») — ⚠ NON ÉPROUVÉ EN RÉEL

Interrupteurs : `RECHERCHE_GLOBALE` (App.tsx) et `LECTURES_SIMULTANEES` (lib/api.ts) — `false` = l'ancien comportement.
Fichiers : `RechercheGlobale.tsx` + `recherche-globale.css` (neufs), `App.tsx`, `lib/api.ts`, `layouts/MobileLayout.tsx`.

**Ce qui est fait**
1. **La recherche globale** (`rechercherPartout`, api.ts) : 5 lectures **en même temps**, 6 lignes chacune (5 montrées, la
   6e déclenche « Voir tout ») — annonces en cours (texte, mandants ; pour un nombre aussi n° de dossier, de mandat, CP,
   n° Hektor), vendues / closes et archives (mêmes filtres que la recherche étendue + mandants), contacts (nom,
   téléphone collé, e-mail ; n° pour un nombre), registre des mandats (texte **et adresse**). Une source en échec
   n'empêche pas les autres : elle est nommée.
2. **La fenêtre** : ouverte par la **loupe en tête du menu** (même picto par masque que les autres entrées, touche « / »
   rappelée), la **touche « / »** (pas pendant une saisie), la **barre de l'Accueil** (enfin active), et sur téléphone une
   **loupe dans la barre du haut** (fenêtre plein écran). ↑ ↓ Entrée Échap ; la dernière recherche est retrouvée.
   Ouvertures : annonce → sa fiche (Estimations si estimation) ; vendue / close / archivée → la fenêtre « Charger la fiche
   complète » existante ; contact → sa fiche ; mandat → écran Mandats filtré sur son numéro, ligne choisie.
3. **Écran Annonces** : `compterAnnoncesAilleurs` compte en parallèle (comptes seuls) ; le bouton devient « Aussi : 2
   vendues ou closes, 5 archivées — Afficher », il **disparaît** s'il n'y a rien ailleurs (« rien dans les vendues, closes
   ou archivées ») ; **0 résultat dans les actives** → extension automatique, une fois par saisie, annoncée « Rien dans les
   actives — … ».
4. **Recherche étendue** : ses 4 sources lues **en même temps** (`lireIndexLegerPourFusion`), même fusion.

**Design (demande de Frédéric en cours de route : « élever le niveau design »)** : charte bienvu — en-tête encre +
filet magenta (comme « Pilotage de l'annonce » et la fiche légère), Plus Jakarta Sans / Hanken Grotesk, vignettes photo
(grisées pour le passé), initiales des contacts en rose, pastilles d'état ok / warn / rose / neutre, mot tapé surligné en
magenta, barre de progression fine, touches dessinées, état vide qui présente le périmètre.

**Mesures en base (26/10, pire cas = terme absent ; terme numérique)** : annonces en cours 80 ms / 43 ms · archives
58 ms · contacts 26 ms · registre (texte + adresse, sans index) 196 ms. ⚠⚠ **L'adresse dans les annonces en cours
coûtait 1 515 ms** (pas d'index sur `adresse_privee_listing` → toute la table relue) : **retirée**, l'adresse est cherchée
dans le registre. Un index trigramme sur cette colonne la rendrait cherchable partout (patch à coller, accord).

**Contrôle en démonstration** (mode mock, bureau 1280 px avec le thème bienvu, puis largeur téléphone) : `npm run build`
vert ; « / » ouvre et met le curseur dans le champ ; « saint » → 2 annonces, 1 vendue, 3 mandats, groupes dans l'ordre ;
↓ puis Entrée ouvre la 2e annonce (`?ecran=annonces&annonce=5502`) ; **Précédent** revient à la liste ; la vendue ouvre
« Charger la fiche complète » ; le mandat 17125 ouvre Mandats avec « 17125 » dans la recherche ; « / » pendant une saisie
n'ouvre rien ; Échap ferme ; la barre de l'Accueil ouvre la fenêtre et retrouve « saint » ; 0 erreur JavaScript.
Défaut vu et corrigé : une image transitoire montrait les anciens résultats sous l'état vide après « Effacer ».
⚠ **Non vérifiable en démonstration** : les comptes « Aussi : … » et l'extension automatique (pas de base), les contacts
(aucun contact de démonstration). ➡ **À éprouver en réel après la mise en ligne** (lecture seule : chercher n'écrit rien).

### 20.3 L'ADRESSE — où elle est chez nous, ce qui la rend introuvable (mesuré le 26/10)

*Frédéric : « l'adresse des annonces et des contacts, même archivés, est déjà chez nous… rechercher par une adresse est
important dans notre métier. »*

| objet | adresses chez nous (Supabase) | cherchable aujourd'hui ? |
|---|---|---|
| annonces en cours | **10 787** / 13 512 (`app_dossier_current.adresse_detail`, quasi identique à `adresse_privee_listing` : 4 différences) | ❌ pas d'index → 1 515 ms |
| mandats du registre (toute leur histoire) | **24 347** / 24 576 (`app_mandat_register_current`) | ❌ ni index texte ni index adresse → 196 ms, lecture complète |
| ↳ dont des biens **archivés** | 17 164 / 35 335 archives | seulement par le registre |
| ↳ dont des biens **vendus / clos** | 6 420 / 8 955 | seulement par le registre |
| contacts | **32 685** / 62 325 (`app_contact_current.adresse`) | ❌ l'adresse **n'est pas** dans leur texte de recherche (116 cas par hasard) |
| archives et vendues **sans mandat** (~20 700) | ❌ pas dans les listes de Supabase (les index légers n'ont pas la colonne) ; ⚠ présentes dans la base locale du serveur (non mesuré) | ❌ |

**Le remède proposé (accord + patch à coller, aucune donnée modifiée, retour arrière = `DROP INDEX`)** : 3 index texte,
créés sans bloquer (`CONCURRENTLY`) — `app_dossier_current(adresse_detail)`, `app_mandat_register_current` (texte de
recherche + adresse), `app_contact_current(adresse)` ; puis 3 lignes de code pour chercher l'adresse dans ces trois
sources et l'**afficher** dans le résultat. Couverture : 10 787 annonces + 24 347 mandats (dont 23 584 biens vendus ou
archivés) + 32 685 contacts. Les ~20 700 archives / vendues sans mandat demandent d'ajouter l'adresse aux listes
construites la nuit : chantier à part.

### 20.4 Les index de l'adresse — le coût mesuré, le patch prêt (26/10) — ⛔ NON POSÉ

*Frédéric : « est-ce que cela risque de ralentir les recherches ? »* — Non : un index accélère la lecture. Il coûte
seulement à l'**écriture** des lignes de sa table. ⚠ Correction de mon propre propos : ce n'est **pas la descente**
(07:45, qui **lit** Supabase) qu'il faut surveiller, c'est le **run de nuit** qui **écrit** ces tables.

**Volumes écrits, 8 dernières nuits** (`logs/scheduled/quotidien_*.log`, « push upgrade » et « push contacts ») :
annonces en cours **2 à 52** lignes · registre des mandats **740-743** · contacts **8 à 4 030** ; durées stables
(push ~4 min 30-5 min, contacts ~35 s). Des volumes faibles : un index de plus n'y pèse presque rien.

**Le patch** : `supabase/patch_index_recherche_adresse_2026-10-26.sql` (+ `_INVERSE`, `_REPETITION`) — 4 index
trigramme créés **sans bloquer l'app** (`CONCURRENTLY`, donc **une ligne à la fois** dans l'éditeur), aucune donnée
touchée : adresse des annonces en cours (`adresse_detail`, qui couvre aussi les 15 sans `adresse_privee_listing`),
adresse **et** texte du registre, adresse des contacts.

**La répétition éprouvée AVANT la pose** (26/10) : 8 KO attendus (index absents ; sans index : annonces 27 ms sur la
table seule, registre 191 / 125 ms, **contacts 354 ms**) et **le témoin OK** (mandants déjà indexés, 9 ms) — le contrôle
sait distinguer les deux cas. ⚠ Le 1 515 ms du §20.2 venait de la **vue** `app_dossiers_current` (toutes ses colonnes
calculées pour chaque ligne avant le filtre), pas de la table seule.

**Ordre** : 1) Frédéric colle les 4 lignes, une à une, en journée (pas entre 04:00 et ~06:15) ; 2) il colle la
répétition → 9 OK ; 3) je remets l'adresse dans la recherche (annonces, registre, contacts) et je l'affiche dans le
résultat, je mesure par la vue, il pousse ; 4) je mesure la première nuit (durées du push).

### 20.5 ✅ POINT 4 ÉPROUVÉ EN PRODUCTION (26/10, en ligne `index-Czwx9zrT.js`, lecture seule, Chrome de Frédéric)

**0 travail créé** pendant l'essai (vérifié dans `app_console_job`) : aucune fiche ouverte, rien chez Hektor.

| essai | résultat |
|---|---|
| « / » ouvre la fenêtre, curseur dans le champ | ✅ |
| « moreau » (recherche globale) | ✅ 5 groupes ; les **5 lectures partent au même instant** (± 1 ms) |
| temps par source, recherche « chaude » (dupont / firminy / 42700) | annonces 277-329 ms · vendues 183-286 · archives 346-595 · contacts 330-630 · ⚠ **mandats 1 061-1 251 ms** |
| Annonces, « moreau » (rien dans les actives) | ✅ **extension automatique** : « Rien dans les actives — 13 résultats dans toutes les annonces hors estimations » |
| Annonces, « firminy » | ✅ « 45 résultats dans les actives + **Aussi : 1745 vendues ou closes, 6914 archivées, 15 en création — Afficher** » ; comptes 330-393 ms, en parallèle de la liste |
| clic « Afficher » (recherche étendue) | ✅ 4 sources lancées dans les 12 premières ms, bandeau étendu à **0,8 s** (8 719 résultats) |

**Corrigé dans la foulée (commit suivant)** :
1. ⚠ la fenêtre attendait la plus lente des 5 lectures (les mandats, ~1,1 s) : **chaque groupe s'affiche maintenant dès
   qu'il arrive** (`surGroupe`) — les annonces à ~0,3 s, les mandats ensuite ;
2. l'espace des milliers dans « Aussi : 1 745 … » ;
3. un caractère cassé **ancien** (`â†©`, commit `df5a585`) sur « Revenir au contexte », dans le bandeau touché ici.

**Vu, pas traité** : sous les règles d'accès, la base ignore l'index texte des contacts (lecture complète, ~190 ms en
base) ; le registre reste la source lente (~1,1 s par l'API) — l'index du patch §20.4 devrait l'aider, **à mesurer après
pose**. Le chargement de la liste Annonces lit 2 fois `app_dossiers_current` (déjà avant ce chantier, non mesuré plus avant).

### 20.6 ✅ LES 4 INDEX DE L'ADRESSE SONT POSÉS (26/10, 16:57-17:00, par Claude, accord de Frédéric : « je te laisse faire les SQL toi-même sur Supabase, tu as mon accord pour ce chantier »)

Avant la pose : 16:57 heure de Paris, 0 requête active, 0 travail en cours, 0 index déjà posé. Les 4 `CREATE INDEX
CONCURRENTLY` passés un par un, sans erreur. **Répétition : 9 OK sur 9.**

| | avant (sans index, en base) | après |
|---|---|---|
| adresse des annonces en cours | 27 ms | **0,2 ms** — index 1,1 Mo |
| adresse + texte du registre | 191 ms | **0,1 ms** — index 2,1 Mo et 12 Mo |
| adresse des contacts | 354 ms | **10 ms** — index 3,1 Mo |
| témoin (mandants, déjà indexé) | 9,4 ms | 9,1 ms |

**Par la VUE de l'app, avec les règles d'accès de Frédéric** (« victor hugo », planification comprise) : annonces avec
adresse **82 ms** (1 515 ms avant) · registre **142 ms** · contacts **8 ms** (190 ms avant : sous les règles d'accès la
base n'utilisait pas l'index texte ; avec l'OR sur l'adresse indexée, elle passe par les index).

**Code** : l'adresse revient dans la recherche des annonces en cours (`adresse_detail`), du registre (`adresse_detail` au
lieu de `adresse_privee_listing`, qui n'a pas d'index) et des contacts (`adresse`, sauf quand on tape un téléphone), et
**elle est affichée** en tête du détail de chaque résultat. Retour arrière : `_INVERSE.sql` (commentaire corrigé : il
faut d'abord retirer `adresse_detail` de `texteAnnonce`).

⏰ **À mesurer à la première nuit (27/10)** : durée du « push upgrade » (référence 4 min 05 à 4 min 59) et du « push
contacts » (référence 32 à 40 s), `logs/scheduled/quotidien_2026-10-27_*.log`.

### 20.7 La loupe du menu de gauche faisait défiler le menu (26/10, signalé par Frédéric)

**Mesuré dans son Chrome (fenêtre de 665 px de haut)** : 9 entrées de 50 px + écarts de 10 px → **536 px pour 463
disponibles** (73 px de trop). ⚠ **Sans la loupe, le menu débordait déjà de ~7 px** (8 × 50 + 7 × 10 = 470 > 463).

**Corrigé** : la loupe **quitte la liste** et va **dans la ligne du logo**, en petite pastille « loupe + / » au format du
bouton « replier » (bordure et fond magenta léger, plein magenta au survol) — **zéro hauteur ajoutée**. Pour les écrans
bas (≤ 760 px de haut, ≥ 1 025 px de large), marge sous le logo 14 → 6 px et écart entre entrées 10 → 8 px : 8 × 50 +
7 × 8 = 456 px pour ~471. Les grands écrans ne changent pas. Menu replié (82 px) : la pastille est masquée (« / » et la
barre de l'Accueil restent).
**Contrôle en démonstration avec le thème bienvu** (nouvelle config de lancement `hektor-mock-bienvu`, port 5198) à
1280 × 665 : menu 425 / 425 (plus d'ascenseur), pastille 53 × 28, clic → fenêtre ouverte, replié 471 / 471.

### 20.8 Le haut de l'écran sur téléphone (26/10, signalé par Frédéric : « tu n'as pas pensé à la version mobile ! »)

**Deux défauts, vus en démonstration avec le thème bienvu (390 × 700)** :
1. **De moi** : la barre du haut est une grille à **3 colonnes** (logo, titre, avatar). La loupe ajoutée au point 4 prenait
   la 3ᵉ place et **renvoyait l'avatar à la ligne**, par-dessus le menu. → 4ᵉ colonne quand la loupe est là
   (`has-search`, 44 px, tablette 48 / 52 px), loupe « vitrée » 44 × 44 (fond blanc 8 %, magenta au toucher) à côté de
   l'avatar magenta.
2. **Plus ancien** : le menu du haut était une grille « autant de colonnes de 46 px que possible » → **7** colonnes sur
   355 px ; la **8ᵉ entrée d'un admin (Santé)** passait à la ligne (menu 108 px de haut) et **recouvrait la recherche** de
   42 px. → une seule ligne (`grid-auto-flow: column`), entrées de 46 px minimum, et au-delà le menu **glisse sur le
   côté** (barre de défilement masquée ; la 8ᵉ entrée dépasse un peu pour inviter à glisser). Les comptes à 6 entrées ne
   changent pas.

**Contrôle** (mesures + image de la page) : 390 px → en-tête 68 px, loupe 280-324, avatar 334-378, menu 60 px sur une
ligne (défile 394 / 368), contenu à 142 px, **aucun chevauchement** ; 360 px → avatar à 348 px, rien ne déborde ;
tablette 768 px → 4 colonnes, menu en bas inchangé, la loupe ouvre la fenêtre.

### 20.9 ✅ Adresse, pastille et menu ÉPROUVÉS EN PRODUCTION (26/10, `index-vAI85dpc.js`, lecture seule, 0 travail créé)

*Décision de Frédéric : les deux recherches (loupe « partout » et champ « filtrer la liste » des écrans) restent avec
leurs libellés actuels — « laisse ».*

- **L'adresse est trouvée** : « victor hugo » → 5 annonces en cours (1ʳᵉ : « 119 Rue Victor Hugo · Firminy 42700 »),
  2 vendues / archivées, 5 contacts, 5 mandats ; « rue de la paix » → 5 annonces, 5 contacts, 5 mandats.
- **Temps, recherche « hugo »** (5 lectures lancées à la même milliseconde) : annonces 252 ms · vendues 210 · archives
  372 · contacts 375 · **registre 398 ms (1 061-1 251 ms avant son index)**. Tout est là en 0,4 s.
- **Menu de gauche à 665 px** : 471 / 471, plus d'ascenseur.
- ⚠ **Frédéric travaille menu REPLIÉ (82 px)** : dans ce mode la pastille est masquée → **aucune loupe visible** pour lui ;
  il lui reste « / » et la barre de l'Accueil. Question posée.

### 20.10 Le menu « trois traits » sur téléphone, et la loupe du menu replié (26/10, « oui, et soigne le design et la mise en page »)

**Téléphone (< 768 px)** — interrupteur `MENU_TIROIR` (`layouts/MobileLayout.tsx`), style `menu-tiroir.css` :
- la **barre d'icônes sous l'en-tête est remplacée** par un bouton **☰** (à gauche, vitré, 44 px, se change en ✕) ;
  l'écran commence **58 px plus haut** (84 px au lieu de 142) ;
- en-tête : **☰ | « bienvu » + titre de l'écran | loupe | avatar** (le symbole bienvu passe dans le panneau) ;
- **le panneau** glisse depuis la gauche (340 px, 88 % de l'écran au plus) : en-tête encre + filet magenta avec le logo
  bienvu et ✕ ; « Rechercher partout… » ; **Travail** (Accueil, Annonces, Estimations, Mandats, Contacts, Agenda) et
  **Pilotage** (Suivi, Santé selon les droits) — chaque vue avec **un picto dessiné**, son **nom en entier** et une
  ligne d'aide (« Le portefeuille de biens »…) ; la vue en cours en rose avec un filet magenta et « Ici » ; en pied :
  avatar, nom, agence, **Utilisateurs** et **Déconnexion**. Échap, le fond ou ✕ le ferment ; toucher une vue la
  ferme et ouvre la vue (l'adresse suit : `?ecran=contacts`).
- **Tablette (≥ 768 px)** : la barre du bas reste, le ☰ s'ajoute à côté du logo.
- ⚠ Non fait : le bouton **Précédent** du téléphone ne ferme pas le panneau (il navigue, comme avant) — l'ajouter
  demanderait une entrée d'historique en plus, à concilier avec les adresses du point 1.

**Bureau, menu replié (82 px)** : la loupe passe **sous le logo** (44 × 32) ; sur les écrans bas, les entrées du menu
replié passent de 50 à 46 px et leur écart de 8 à 6 px pour qu'il tienne.

**Contrôle en démonstration, thème bienvu** : 390 px → en-tête 44 / 204 / 44 / 44, barre d'icônes masquée, contenu à
84 px, panneau 340 px avec les 8 vues, curseur sur la vue en cours ; 360 px → titre 172 px, tout tient ; 768 px →
5 colonnes, barre du bas conservée, Échap ferme, « Contacts » ouvre `?ecran=contacts` et ferme le panneau ; bureau
1280 × 665 replié → loupe sous le logo, menu 416 / 416, la loupe ouvre la recherche ; déplié → 425 / 425.

### 20.11 La loupe du bureau revient EN TÊTE DU MENU (27/10, Frédéric : « je préférais la mise en page précédente mais optimisée »)

La pastille loupe + « / » dans la ligne du logo (20.9, 20.10) **ne lui plaît pas** : elle est **retirée**. La loupe
reprend sa place d'avant le 26/10, **en tête du menu**, mais en **champ compact** « 🔍 Rechercher  / » de **36 px** (au
lieu d'une entrée de 50 px + 6 de marge), gris discret, magenta au survol (`nav-search`, `recherche-globale.css`).
Menu replié : la loupe seule (50 × 36) dans la colonne des pictos, sans texte ni « / ». Téléphone et tablette inchangés.

**Pas d'ascenseur (exigence de Frédéric)** — deux paliers, rien ne change au-dessus de 760 px de haut :
- ≤ 760 px : écart logo/menu 24 → 12 px, entrées 46 → 42 px (46 replié), écarts 6 px ;
- ≤ 680 px : marges de la barre 24 → 14 px, entrées 38 px (déplié et replié), écarts 4 px, champ 34 px.

**Contrôle en démonstration, thème bienvu, 8 entrées (admin)** — débordement du menu, déplié / replié :
1080 → 0 / 0 · 761 → 0 / 0 · 681 → 0 / 0 · 650 → 0 / 0 · 600 → 0 / 0 · 560 → 0 / 0. ⚠ Avant le palier ≤ 680, 600 px
débordait de 30 / 40 px et 560 de 70 / 80 (le premier contrôle n'avait mesuré que 665 et 1080). 540 px déborde encore
de 16 px déplié (pas un écran de PC réel ; le défilement reste en secours). Le champ ouvre la recherche ; build OK.

### 20.12 Le menu latéral « Net » (27/10, piste A choisie par Frédéric)

Maquette : `maquettes/menu-lateral-bienvu-v1.html` (l'actuel + 3 pistes, déplié / replié, hauteurs 560-900, profils
admin / négociateur, tableau « rien ne se perd »). Frédéric a pris la **piste A · Net**. Code : interrupteur `MENU_NET`
(`App.tsx`, ne joue qu'avec bienvu allumé), styles `menu-lateral-net.css` chargé en dernier (`main.tsx`).

**Ce qui change (bureau seulement ; le téléphone et la tablette ont leur propre rendu)**
- Entrée active : voile magenta léger + fin trait magenta à gauche + picto rose. **Plus de dégradé ni de halo**, et
  **plus le trait blanc parasite** : c'était le `::after` de l'entrée active peint en blanc par `annonces-v2.css`.
- Lignes de 36 px ; deux groupes **« Travail »** (Accueil → Agenda) et **« Pilotage »** (Suivi, Santé — manager/admin).
- **Pictos posés par titre** : l'ancien rangement par `nth-child` décalait depuis que la loupe est un enfant du menu,
  et « Santé système » n'avait aucun picto (le ☰, pris pour un bouton de menu). Santé = cœur + pouls.
- Pied sur une ligne : avatar 32 px, nom, agence, cloche ; **un clic sur son nom** ouvre « Utilisateurs » (manager,
  admin) / « Se déconnecter » (Échap ou clic dehors referme). Le compteur de mes actions garde sa place à côté de
  la cloche (il reste coupé par `SUIVI_PASTILLE`).
- La fenêtre de la cloche s'ouvre **vers le haut** (elle s'ouvrait vers le bas, hors de l'écran) ; la barre laisse
  dépasser les fenêtres du pied (avant, elles étaient coupées au bord de la barre).
- Le trait magenta en dégradé collé au bas de la barre (`.side-rail::after`, `styles.css`) est retiré.
- Replié : **68 px** (colonne de la grille aussi, au lieu de 86), carrés de 40 px, séparateur entre les groupes,
  infobulle au survol, **la cloche reste visible** (elle était masquée), l'avatar ouvre le même menu.

**Contrôle en démonstration, thème bienvu, admin (8 entrées)** — débordement menu / barre, déplié et replié :
900 → 0 · 720 → 0 · 665 → 0 · 600 → 0 · 560 → 0 ; le pied reste dans l'écran à chaque hauteur. Clic sur « Contacts »
→ `?ecran=contacts`, entrée active suivie ; menu du nom ouvert / fermé par Échap ; cloche ouverte à 12 px du bord,
entière ; infobulle « Agenda » en replié. Build OK. ⚠ Non vu avec une vraie session (le mode démonstration n'a pas
« Se déconnecter ») ni par un négociateur réel.

---

## 21. POINT 5 — RE-AUDIT DU 26/10 : « revenir en arrière entre objets » (rien codé)

**Ce qui existe déjà (code lu + démonstration bienvu)**
- La fiche annonce (cockpit) a un **fil d'Ariane** : « **Annonces** › VA1988 · T3 lumineux… › *rubrique* »
  (`fa-ck-wb-crumb`, `App.tsx` ~31263) — « Annonces » ferme la fiche ; si la fiche a été ouverte **depuis une fiche
  contact**, elle rouvre ce contact (`dossierReturnContactId`, `closeDossierDetailPage` ~15676).
- Contact **par-dessus** l'annonce : l'adresse le dit (`?ecran=annonces&annonce=5502&contact=P-2001`, point 1).
- Depuis ce contact, ouvrir **un autre bien** (`onOpenDossier` ~22874) **ferme le contact et remplace** l'annonce de
  départ : à l'écran, **plus aucune trace** de l'annonce A ni du contact (constat N7). ⭐ Depuis le point 1, le bouton
  **Précédent** du navigateur, lui, ramène bien au contact puis à l'annonce A (chaque ouverture écrit son adresse).
- La fiche contact V2 a un en-tête « Fiche contact · *nom* » (~43040), sans chemin.

**Ce qui manque** : voir **où l'on est passé**, et y revenir **d'un clic** sans compter les « Précédent ».

**Proposition — le fil de navigation**
- Chaque fiche ouverte (annonce, contact) s'ajoute à un fil court (**les 5 dernières**) avec son libellé :
  « Annonces › VA1988 › Mme PETIT › VA2210 · Maison… ». Revenir en arrière raccourcit le fil.
- **Bureau** : il remplace le fil actuel du cockpit (« Annonces » reste le 1er segment) et s'ajoute en tête de la fiche
  contact ; chaque segment est cliquable et ramène **exactement** là (même mécanisme que Précédent : l'historique du
  navigateur, donc les deux restent d'accord).
- **Téléphone** : la place manque pour tout le fil → une pastille « ‹ VA1988 » (l'objet précédent) en haut de la fiche.
- Le fil est rangé **dans l'historique du navigateur** (`history.state`) : il survit à F5 et suit Précédent / Suivant.
- Interrupteur, comme les points précédents.

**Ce que ça pourrait casser** : le gestionnaire « Précédent » du point 1 (il doit continuer à restaurer écran + fiche) ;
le retour contextuel vers un contact (`dossierReturnContactId`, gardé) ; « Retour aux annonces » (gardé, 1er segment).
Non vérifiable en démonstration : la fiche contact n'a pas de données, donc le parcours « contact → autre bien » se
contrôlera en réel (lecture seule : ouvrir une fiche lance une relecture chez Hektor, à faire avec ton accord).

### 21.1 ✅ POINT 5 CODÉ ET CONTRÔLÉ EN DÉMONSTRATION (26/10, « code le point 5 et contrôle ») — ⚠ NON ÉPROUVÉ EN RÉEL

Interrupteur `FIL_NAVIGATION` (App.tsx). Style `fil-navigation.css`.

**Ce qui est fait**
- **Le fil** : chaque fiche ouverte (annonce ; contact, y compris **par-dessus** une annonce) s'ajoute (5 au plus) ;
  revenir à une fiche du fil le **raccourcit** ; un libellé qui arrive après l'ouverture complète l'entrée ; aucune fiche
  ouverte pendant 600 ms → le fil repart de zéro (sauf pendant le démarrage, pour survivre à F5). Gardé pour l'onglet
  (`sessionStorage`).
- **Bureau, fiche annonce** : les fiches précédentes s'insèrent dans le fil du cockpit, après « Annonces » (pictos
  maison / personne, nom complet en info-bulle) ; le fil s'arrête **à la fiche qu'il décrit** (sinon le cockpit sous un
  contact ouvert par-dessus répétait l'annonce).
- **Bureau, fiche contact** (V2 et ancienne) : un bandeau « Parcours » en tête, morceaux cliquables + la fiche en cours en
  rose.
- **Téléphone et tablette** : une pastille « ‹ fiche précédente » en bas à gauche (encre, chevron magenta).
- Cliquer un morceau rouvre **exactement** la fiche : une annonce (dans son écran), un contact **par-dessus son annonce**,
  ou un contact de l'annuaire.
- **Corrigé au passage (point 4)** : ouvrir une annonce depuis la recherche globale laissait le contact ouvert
  par-dessus l'annonce précédente → il se referme.

**Contrôle en démonstration (thème bienvu)**, adresse et fil relevés à chaque étape :
1. annonce A (VA1988) → fil « VA1988 » ; 2. contact par-dessus → « VA1988 › Contact P-2001 » (adresse `&contact=P-2001`) ;
3. annonce B par la recherche → « VA1988 › Contact P-2001 › VA1926 », cockpit « Annonces › VA1988 › Contact P-2001 ›
VA1926 · Grand T3… » ; 4. clic « Contact P-2001 » → retour à A **avec le contact par-dessus**, fil raccourci ;
5. **Précédent** → B, fil reconstruit ; 6. clic « VA1988 » → A, fil « VA1988 » ; 7. « Annonces » → fiche fermée, fil
vide ; **F5** sur B → fil « VA1988 › VA1926 » intact ; téléphone 390 px → pastille « ‹ VA1988 » (118 × 42, en bas à
gauche), la toucher ramène à A et la fait disparaître. 0 erreur JavaScript.
⚠ Non vérifiable en démonstration : la **fiche contact** (pas de données) — son bandeau « Parcours » et le chemin
« contact → autre bien » depuis sa liste de biens se contrôleront en réel (ouvrir une fiche lance une relecture chez
Hektor : avec l'accord de Frédéric).

---

## 22. POINT 6 — RE-AUDIT DU 26/10 : « indicateurs dans l'objet, puis retrait de la modale » (rien codé)

*Frédéric : « point 6, je pousse plus tard » (le point 5 n'est pas encore en ligne).*

**La fenêtre aujourd'hui (code relu)** : `HektorActionStatusPopup` (`App.tsx` ~9258), montée deux fois (téléphone
~23747, bureau ~24749). Elle montre les 8 derniers travaux de `hektorActionJobs` — et ce suivi charge **tous les
travaux en cours de tout le monde** (`loadActiveHektorActionJobs`, `api.ts` ~11268 : **aucun filtre sur l'auteur**) :
un admin voit donc surgir la fenêtre pour les gestes des négociateurs. Les 5 mécanismes qui dépendent du suivi (verrou
anti-double action, ligne en cours de suppression, préparation des fiches légères, photos et scan de la création,
`beforeunload`) **restent** ; seul l'affichage part. Piège n° 1 toujours là : l'effet `hektorActionLinkedDossiers`
(~14489) lit la liste **de la fenêtre** (`visibleHektorActionPopupJobs`) — à rebrancher sur `hektorActionJobs`.
Depuis le point 3a, le bouton « Ouvrir le détail » de la fenêtre est **redondant** (l'annonce créée s'ouvre seule).

**Ce que les gens déclenchent vraiment (base, 30 derniers jours, travaux lancés par un humain)** :

| travail | nombre | durée médiane / 90 % | ce que la fenêtre apporte |
|---|---|---|---|
| relecture à l'ouverture d'une fiche | 671 | 29 s / 51 s | rien (exclue de la fenêtre) |
| relecture d'un contact | 126 | 26 s / 56 s | rien (exclue) |
| **changer le statut / offre / compromis** | 36 + 13 | **60 s / 128 s** | « c'est parti / fini / refusé » |
| **envoyer une photo** | 23 | **7 min / 22 min** | la seule trace de l'envoi en cours |
| créer un contact | 10 | 15 s / 20 s | (3a ouvre déjà la fiche) |
| supprimer compromis / vente, réordonner, mandant, documents… | 2 à 11 chacun | 6 s à 56 s | « fini » |
| n° de mandat automatique, Matterport | **0** | — | — |

**Proposition (front seul, comme les points précédents)**
1. **Un indicateur dans la fiche** : sous l'en-tête de la fiche annonce (cockpit, téléphone) et de la fiche contact,
   une ligne discrète tant qu'un travail **sur cet objet** est en cours — « ⟳ Changement de statut en cours chez Hektor
   (≈ 1 min) », « ⟳ 3 photos en cours d'envoi » — qui devient « ✓ À jour chez Hektor » puis s'efface, ou **en rouge si
   Hektor refuse**, avec le message et ce qu'on peut faire (relire, voir le détail). Les photos choisies à la création
   gardent leur avertissement « ne fermez pas cet onglet » (et le `beforeunload`), mais **dans la fiche**.
2. **Un petit compteur d'activité** près de la cloche (bureau et téléphone) : « ⟳ 2 » quand **mes** actions sont en
   cours, rouge en cas d'échec ; un clic ouvre la liste de **mes** actions récentes (état, durée, échec et message).
   Pour l'admin : **ses** actions, pas celles des autres (l'écran Santé reste là pour tout voir).
3. **Retrait de la fenêtre** derrière un interrupteur, **en dernier**, une fois 1 et 2 en place ; le suivi des travaux
   et ses 5 dépendances ne bougent pas ; l'effet du piège n° 1 rebranché.

**Ce que ça pourrait casser** : les photos de la création (si le suivi était coupé avec l'affichage — il ne l'est
pas) ; l'admin ne verra plus surgir les gestes des autres (voulu ; Santé reste) ; **sans la fenêtre, un échec se voit
dans la fiche et dans le compteur** — il faut qu'ils soient bien visibles, c'est le cœur du point. Le rechargement
surprise des travaux sans auteur (balayage) n'aura plus d'explication à l'écran (déjà le cas, noté au §6).

### 22.1 Inventaire complet — TOUT ce qui affiche l'état d'un travail du worker (26/10, question de Frédéric : « mais toutes les fenêtres de suivi des workers ? »)

Balayage de tout le front (un auditeur, lecture seule ; vérifié sur deux points).

**Un seul suivi central** : le sondage de 5 s (`App.tsx` ~14296) qui nourrit `hektorActionJobs`. **Une seule fenêtre
générale** : `HektorActionStatusPopup`. Les autres « fenêtres » sont des **étapes d'un geste précis** :

| fenêtre | geste | ce qu'elle suit |
|---|---|---|
| « Charger la fiche complète » (`LightweightDetailImportModal`) | ouvrir un bien vendu, clos, archivé, brouillon | sa préparation — ⚠ **jamais « prête » pour un brouillon** (`prepare_brouillon_annonce_detail` absent du filtre `lightweightDetailJob`) |
| message « avis de valeur en cours de génération » | générer l'avis de valeur | **rien** (texte figé, travail non suivi) |
| signature après le PDF du mandat | générer le mandat | relit les documents 150 s (pas le travail) |
| fenêtre de recherche (création / modification) | créer / modifier une recherche | jusqu'à l'envoi seulement |

**États déjà affichés SUR PLACE** (ils restent) : lignes « En création… » des annonces, contacts et recherches ;
« Suppression en cours… » des recherches (point 3c) ; mandants « En création… » ; panneau Documents (« envoi à Hektor
en cours / a échoué », relu toutes les 8 s) ; panneau Photos (« gardée chez nous — envoi en cours / échoué ») ;
boutons « Envoi… / Demande… » (mandants, Matterport, n° de mandat) ; plan cadastral « en génération… » ; les 3
bandeaux de la fiche (modification d'annonce, de contact, gestes abandonnés — **lus à l'ouverture seulement**).

**Supervision** (reste) : écran Santé (120 s), cloche (120 s, bureau seulement).

**Code mort** : bandeau des travaux de `StockScreen` et ses cartes mobiles — rendus pour l'écran `'annonces'`, que
`openScreen` redirige vers `'mandats'` (vérifié, `App.tsx` ~24505).

**Trous trouvés** : (1) la fiche légère d'un **brouillon** ne passe jamais à « Ouvrir la fiche complète » ;
(2) des travaux **hors de la liste suivie** (`hektorActionJobTypes`) : préparation de brouillon, sortie de brouillon,
plan cadastral, avis de valeur, mandat PDF, visibilité / couverture / réordonner des photos — suivis seulement s'ils ont
été mémorisés pendant la session, et les photos et deux PDF ne le sont pas du tout ; (3) les 3 bandeaux de la fiche ne
se relisent pas tout seuls.

### 22.2 ✅ POINT 6 CODÉ ET CONTRÔLÉ EN DÉMONSTRATION (26/10, « Oui vas y ») — ⚠ NON ÉPROUVÉ EN RÉEL

**Ce qui est codé (front seul, aucune base, aucun worker)** — deux interrupteurs dans `App.tsx` :
`SUIVI_DANS_LA_FICHE = true` (le nouveau) et `FENETRE_SUIVI_ACTION = false` (l'ancienne fenêtre, gardée dans le code).

1. **La ligne d'état dans la fiche** (`IndicateurTravauxObjet`) — cockpit, fiche de base, fiche téléphone, les deux
   fiches contact. Par type : « ⟳ Changement de statut en cours chez Hektor (≈ 1 min) », « 2 envois de photos » ;
   les photos de la création y disent « ne fermez pas cet onglet » ; « ✓ À jour chez Hektor » 12 s puis s'efface ;
   **en rouge si Hektor refuse**, avec son message et un bouton « Compris » qui la range (mémorisé pour l'onglet,
   `sessionStorage gti_travaux_vus`). Les relectures automatiques (ouverture d'une fiche, documents) n'y paraissent pas.
2. **Le compteur de MES actions** (`CompteurMesTravaux`) à côté de la cloche : ⟳ n en cours, **rouge « ! n »** en
   cas de refus, ✓ sinon ; un clic ouvre la liste (8 max, `requested_by` = moi), chaque ligne ouvre l'objet ; Échap
   ou clic dehors ferme. **Barre repliée** : la cloche y est cachée exprès (`annonces-v2.css`), le compteur reste,
   en pastille sur l'avatar — un refus ne doit pas se cacher. **Téléphone** : pastille sur le ☰, et la section
   « Mes actions envoyées à Hektor » du menu passe **en tête** quand une action est en cours ou refusée (sinon en bas).
3. **La fenêtre « Suivi de l'action » est retirée** (les deux montages, derrière `FENETRE_SUIVI_ACTION`). Le suivi
   des travaux et ses 5 dépendances **ne bougent pas** ; le piège n° 1 est rebranché (`hektorActionLinkedDossiers`
   lit `hektorActionJobs`, plus la liste de la fenêtre).
4. **Les 3 trous du §22.1** : (1) `prepare_brouillon_annonce_detail` ajouté aux deux filtres de la fiche légère ;
   (2) 13 types ajoutés à `hektorActionJobTypes` (`api.ts`) — brouillon (préparer, activer), offre, compromis, vente,
   retrait de mandant, visibilité des photos, cadastre, avis de valeur, mandat PDF, relance et annulation de
   signature ; (3) les 3 bandeaux de la fiche se relisent à chaque relecture de l'app (`useRelectureRubriques`).

**Contrôle (mock bienvu, faux travaux posés par `window.__travauxDemo`, mock seulement)** — bureau 1280 px, barre
dépliée et repliée ; téléphone 390 px :
- ligne en cours + ligne rouge avec « Compris » dans la fiche, au bureau et au téléphone ; « Compris » → la ligne
  part, le compteur passe de « ! 1 » rouge à « ⟳ » ;
- panneau du compteur : 3 lignes aux bons états, un clic sur une ligne ouvre l'annonce et ferme le panneau ;
- téléphone : pastille rouge sur le ☰, section en tête du menu, aucun débordement horizontal (390 = 390) ;
- `npm run build` vert ; console : seulement les 500 du mock sans serveur (`/api/hektor-diffusion`), déjà là avant.

**Défauts trouvés au contrôle, corrigés** : le compteur **invisible barre repliée** (son conteneur y est caché ; et
une case de grille servait de repère à la pastille → `grid-area: auto`) ; un **double point** après le message de
Hektor ; « envoyé il y a NaN h » si la date manque ; un guillemet seul en bout de ligne (espaces insécables) ;
la section du menu sous la ligne de flottaison ; et **251 fins de ligne doublées** (`\r\r\n`) par mon script
d'insertion — remises au propre, 0 restante.

**Non vu, à dire** : quand le cockpit d'une annonce est ouvert, il couvre toute la barre — le compteur n'y est pas
cliquable, c'est la ligne de la fiche qui prend le relais (voulu). **Aucun essai réel** : il faut un vrai geste
(ex. un changement de statut) pour voir la ligne vivre sur un vrai travail — c'est une écriture chez Hektor, donc
avec l'accord de Frédéric. **Retour arrière** : `SUIVI_DANS_LA_FICHE = false` et `FENETRE_SUIVI_ACTION = true`.

### 22.3 POINT 6 bis — « c'est bien trop visible » : une PASTILLE pour le négociateur, les alertes à l'admin (27/10, décision de Frédéric)

**Sa demande** : *« les erreurs des workers uniquement visibles à partir de la vue Santé, que ce soit moi qui sois averti
en cas d'erreur. Les négociateurs doivent juste avoir une petite indication sur l'annonce ou le contact, discrète, qui
dit soit en attente, soit vert, soit rouge. Ensuite les admins ont accès au geste pour débloquer. »* Ses trois réponses :
bandeaux **réservés aux admins** ; alerte **cloche ET e-mail** ; pastille **dans la fiche seulement** (pas les listes).
C'est la suite de sa règle du 20/09 (bandeau d'annonce) : *« ce n'est pas l'utilisateur qui doit être prévenu […] lui ne
peut rien y faire »*.

**Audit avant de coder (mesures du 26/10 au soir)** : Santé montre déjà `console.jobs.errors` et `data.geste_abandonne`
avec « J'ai refait / Abandonner ce geste » ; l'e-mail existe déjà par le moniteur (`data.travaux_en_erreur`, critique,
toutes les 2 h, **seulement à la bascule** vers le rouge) ; mais l'avis d'échec du worker allait **au négociateur du
bien** (`resolveJobFailureRecipient`) — 9 avis en 30 jours, dont 6 pour Frédéric lui-même. 8 erreurs sur des gestes
humains en 30 jours.

**Front (`App.tsx`, `suivi-travaux.css`) — interrupteur `SUIVI_PASTILLE = true`** :
- `PastilleSuivi` : « Hektor · en attente » (point gris qui pulse) / « Hektor · à jour » (vert) / « Hektor · à vérifier »
  (rouge). Aucun message, aucun bouton ; le détail est dans la bulle (et « ne fermez pas cet onglet » si des photos de
  la création attendent). **Rouge** = ce que dit la base : saisie en conflit ou partielle (`app_annonce_edit_status`),
  geste abandonné non tranché (`app_action_status`, 5 essais ou 3 h), contact en conflit. **Gris** = travail en cours, ou
  en erreur mais encore rejoué (< 5 essais et < 3 h, même seuil), ou saisie en attente d'envoi. La base est relue à
  l'ouverture, à chaque relecture de l'app et **à chaque changement d'état d'un travail de l'objet**.
- Emplacements : cockpit **à droite du fil d'Ariane** (toujours visible) et la puce du pied du cockpit, qui disait
  « Hektor · à jour » **en dur** et dit maintenant l'état réel ; téléphone dans la rangée des statuts ; fiche contact V2
  sous le nom ; fiche de base et ancienne fiche contact sur une ligne fine à droite.
- La ligne d'état et le compteur de mes actions du §22.2 sont **coupés** (code gardé : `SUIVI_PASTILLE = false` les rend).
- Les 3 bandeaux (`AnnonceEditStatusBanner`, `ContactEditStatusBanner`, `GesteAbandonneBanner`) : **admin seulement**
  (ils ne lisent même plus la base pour un négociateur).

**Worker (`console_job_worker.js`) — interrupteur `CONSOLE_ALERTES_A_L_ADMIN` (actif par défaut, `0` = ancien
comportement)** : les 4 avis qui allaient au négociateur (échec d'un geste, création incomplète, conflit contact, conflit
recherche) passent par `posterAlerte` : **cloche de l'admin** (`GTI_ALERT_EMAIL`, même adresse que le moniteur, par
défaut Frédéric), le négociateur concerné **nommé** dans le message, et **un e-mail** par la clé de service Workspace
(jeton RS256 signé par `crypto`, aucune dépendance nouvelle) — seulement si l'avis est **nouveau** (l'index
`app_notif_unread_uq` écarte le doublon : un geste rejoué 5 fois sonne une fois), **plafond 10 e-mails / heure / service**.

**Contrôle** : démonstration (mock, vue négociateur forcée) — bureau : pastille grise en haut à droite du cockpit, puce
du pied qui suit, aucune ligne ni compteur ; rouge vérifié à l'œil ; téléphone 390 px : pastille dans les statuts, pas de
débordement ; erreur rejouée → gris. `npm run build` vert ; `node --check` du worker vert (le worker n'a pas été lancé).
**Le jeton Gmail s'obtient avec le vrai code** (extrait du worker, exécuté seul) : la clé et le droit `gmail.send`
répondent. ⚠ **Non éprouvé** : l'**envoi** d'un e-mail (il partirait vraiment) ; la **fiche contact** (le mock n'a pas de
contacts) ; le **rouge venu de la base** (le mock n'a pas de base) ; tout le worker tant que **les 4 services n'ont pas
redémarré** (accord de Frédéric, file vide : 0 pending ET 0 running).

**Mise en ligne (27/10, 00:07)** : Frédéric a poussé et redémarré les 4 services ; le bundle en ligne porte la pastille,
les 4 processus sont nés à 00:07:07-09 (après le commit 591ec16), journaux sans erreur. ⚠ Le redémarrage est tombé
**pendant le balayage des photos de minuit** : le travail `56cf6452` (annonce 40673, parti à 00:07:07) est resté
« running » — il serait passé en erreur à 00:37 et 40673 aurait été écartée **à vie** du balayage. **Remis en attente à
00:12:31 avec l'accord de Frédéric** (une ligne, gardée par `status='running'`) : repris et **fini à 00:12:43**. Le
balayage continue (569 en attente, ~9/min), 0 erreur depuis 23:00.

### 22.4 ⛔ CONTRÔLE DU 27/10 AU MATIN (« vérifie ton travail ») — LA CONNEXION ÉTAIT CASSÉE PAR LES POINTS 5, 6 ET 6 bis

**Le défaut, trouvé en ouvrant la vraie app sans être connecté** : page **blanche**, erreur React n° 300 (« Rendered
fewer hooks than expected »). Cause : les hooks ajoutés dans `App` par le **point 5** (fil : `filNavigation`,
`objetFilCourant`, 2 `useEffect`, `contexteFilNavigation` — 974e75d), le **point 6** (`travauxVus`, `contexteTravaux`,
1 `useEffect` — f6433e9) et le **point 6 bis** (`demoNegociateur` — b3058b0) étaient écrits **APRÈS** les deux `return`
de l'écran de connexion (`if (hasSupabaseEnv && !session && !bootLoading)`). Au démarrage `bootLoading` vaut vrai : tous
les hooks tournent ; puis, sans session, le `return` anticipé en saute 9 → React tombe. **Toute personne non connectée
(nouvel appareil, déconnexion, session expirée) avait une page blanche et ne pouvait plus se connecter.** Une personne
déjà connectée n'était pas touchée (aucun `return` anticipé). ⚠ Le mock ne pouvait pas le voir (il n'a pas d'écran de
connexion) : c'est la leçon « contrôler AUSSI la vraie app, déconnecté ».

**Le correctif** : le bloc (111 lignes, inchangé) est **remonté** juste au-dessus des deux `return`, avec une note
« tout hook de App se déclare AU-DESSUS ». Toutes les variables qu'il lit sont déclarées plus haut (vérifié une à une :
la plus basse, `isAdmin`, l. 19958) ; `allerAuFil` et `ouvrirCibleTravail` sont des déclarations de fonction (hissées).
Après le déplacement, **aucun hook** ne reste après le `return` de connexion (balayage jusqu'à la fin de `App`).

**Contrôle** : `npm run build` vert ; la version construite servie en local (`vite preview`, vraie base, bienvu allumé),
**déconnecté** : l'écran « Bon retour » s'affiche, **0 erreur React** (seulement les 401 attendus sans session).
**Témoin inverse** : à la même minute, la version en ligne (`index-B1mF2q6p.js`) reste blanche avec l'erreur n° 300.

**Le reste du contrôle du matin** :
- workers : les 4 services tournent depuis 00:07:07-09, **aucune erreur ni alerte** dans leurs journaux du 27/10 ; file
  vide, 0 erreur sur 12 h ; le balayage des photos a fini (963 travaux `done` depuis 23:00, dernier à 01:34) ;
- **aucune alerte n'a encore été posée** depuis le redémarrage (aucun échec) : l'**envoi réel** de l'e-mail reste non
  éprouvé ;
- **aucune fiche n'est rouge** en ce moment (un seul travail abandonné sur 30 jours : `refresh_console_contact_data`
  sans objet) : le rouge venu de la base reste non éprouvé en réel ;
- ⚠ **réserve sur ma propre note du §22.3** : « un geste rejoué 5 fois sonne une fois » n'est vrai que si le travail
  porte un `app_dossier_id` — l'index `app_notif_unread_uq` traite les `NULL` comme distincts. Un geste **sur un contact
  ou une recherche** (sans dossier) qui échoue 5 fois poserait **5 avis et 5 e-mails** (dans la limite de 10/h). Et
  l'alerte part dès le **1er échec**, même si un rejeu réussit ensuite. Mesure : 9 avis d'échec en 30 jours (5 sans
  dossier), 1 par travail — le bruit réel est faible. **Non corrigé, à décider.**
- ⚠ **réserve** : `app_action_status` compte **tous** les types de travail (les synchros de nuit aussi), alors que
  l'e-mail ne part que pour les gestes (`JOB_TYPES_A_NOTIFIER`) : une pastille peut passer au rouge sans e-mail — l'admin
  le voit alors dans Santé. Et pour un négociateur sur un bien qui n'est **pas à lui**, la fonction refuse
  (`forbidden_action_status`) : sa pastille ne montre pas ce rouge-là.

### 19.3 ⛔ LE TÉMOIN DE LA SUPPRESSION DE RECHERCHE EST ROUGE — 27/10 au matin

La recherche Firminy de 20000008 (index 1, critère 471880, « supprimée » le 26/10 à 12:45 par le travail `e43aff82`) est
**toujours `archive false / is_active true`** après la nuit : relue par le run des recherches à **02:48:21** le 27/10.
L'autre recherche du contact (index 0, Le Puy-en-Velay, appartement 123 500-136 500) est `archive true` — ⚠ elle l'était
**très probablement déjà avant** le geste : elle correspond au bien de l'essai 24113 (130 000, Le Puy), dont le compromis
du 22/10 a posé une relecture de raison `qualification_acquereur_archivee` (travail `12f0610b`). Non prouvé par une photo
d'avant le 26/10 : je ne peux pas exclure à 100 % que le geste ait visé la mauvaise (risque §19.2).

**Ce que ça dit** : `modifDateArchiveCritere` avec `dateArchive = 26-10-2026` n'a pas fait basculer `archive` en ~14 h.
Deux lectures restent possibles, et je ne tranche pas sans mesure : (a) Hektor archive **après** la date (le lendemain
ou plus tard) ; (b) le geste ne marche pas. ⚠ La date d'archivage programmée **ne nous parvient pas** (ni l'API ni notre
table ne la portent, mesure du 16/10), donc on ne peut constater que la bascule.
⏰ **Témoin à relire le 28/10 au matin** (après le run des recherches) ; s'il est encore actif, le geste « supprimer une
recherche » ne fait rien de visible chez Hektor → à auditer (`handleDeleteHektorContactSearch`).

### 19.4 ✅ TRANCHÉ LE 27/10 (fin de matinée) — LE GESTE A VISÉ LA MAUVAISE RECHERCHE. Le témoin du 28/10 est sans objet.

**Mesuré, en lecture seule, chez Hektor** (Chrome de Frédéric, compte admin, onglet Recherches de 605946 lu par
`contacts-contactProfile-recherche-changeTab`, aucune écriture) :

| chez Hektor | `data-search-id` | ce qu'elle est | auto-archivage |
|---|---|---|---|
| « Recherche 1 » | **471880** | **Le Puy-en-Velay**, appartement 123 500-136 500, créée le 22-10-2026, icône `icon-presentation-off` (archivée) | **26-10-2026** ← la date posée par `e43aff82` |
| « Recherche 2 » | **471894** | **Firminy** (la recherche à supprimer), sans icône | non lue (l'onglet ne détaille que la 1ʳᵉ) |

**Et le journal du travail le disait déjà** (`app_console_job_log`, étape `hektor_contact_search_list`) :
`count: 1, requested_index: 1, selected_idCritere: 471880` → l'entrée 1 n'existe pas → repli `|| list[0]`.

➡ **C'est le défaut DORMANT écrit le 31/08** (`AUDIT_RECHERCHES_ETAT_REEL_2026-08-31.md`, « La conséquence exacte ») :
la regex de `fetchHektorContactSearchList` ne rend que **le premier** numéro, alors que le HTML porte **les deux**
`data-search-id`, dans l'ordre. « Modifier ou supprimer la 2ᵉ recherche d'un contact agit sur la 1ʳᵉ. Sans erreur, sans
trace. » **Premier geste sur une 2ᵉ recherche, première morsure.**
➡ ⚠ **L'hypothèse du §19.2 est FAUSSE** : l'onglet ne liste pas « que les actives » — il liste **les deux** (l'archivée
d'abord). Le « tombé juste par chance » n'a pas eu lieu.

**Les dégâts** : nuls sur Firminy (jamais touchée, toujours active — c'est ce que voit le run). Sur Le Puy, déjà archivée :
sa date d'auto-archivage a été **écrasée** (création + 2 ans = 22-10-2028 attendu → 26-10-2026). Sans effet visible.
⭐ Et la réponse `desarchiveCritere: true` sur une recherche **archivée** colle au code de la page Hektor (relevé du 15/10) :
la page enchaînerait sur la bascule `archiveUnarchiveContactRecherche` — notre worker ne la fait pas, d'où Le Puy restée
archivée.

**Toujours vrai, et NON tranché par cette mesure** : poser la date du jour sur une recherche **active** l'archive-t-il, et
quand ? Les 4 gestes depuis juin ne le prouvent pas (le seul relu à 2 recherches, Gladys, portait un `idCritere`
explicite ; la bascule n'a jamais été datée). Et le worker rend « archived » **sans relire** (`handleDeleteHektorContactSearch`).

**NOTÉ, PAS TRAITÉ** — correctif connu depuis le 31/08 : lire `data-search-id` en premier (ancienne regex en repli,
journaliser les deux) ; refuser le repli `list[0]` quand l'index demandé n'existe pas ; relire l'état après le geste.
⚠ **Même chemin pour la MODIFICATION** (`handleUpdateHektorContactSearch` → `resolveContactSearchTargetCritereId`).
À décider par Frédéric.

**Complément du 27/10, après relecture des notes demandée par Frédéric :**
- ✅ **La MODIFICATION n'est PAS exposée** : elle est autonome depuis le 19/06 (Supabase-first) et la porte est fermée
  depuis **C.3 (24/08)** — `app_edit_search_optimistic` ne crée aucun travail (`push_search = null`) et cible par
  `(contact, search_index)` dans notre table. C'est pour ça que le risque du 31/08 a été **clos sans suite**
  (`LISTE_TACHES` l. 9246) — ⚠ mais cette clôture ne parlait **que de la modification**.
- ⛔ **L'ARCHIVAGE (bouton « Supprimer ») est le seul geste qui part encore chez Hektor** (décision du 20/08, confirmée le
  20/09 : « envoi sans retour ») — et **lui** passe toujours par le ciblage par rang scrapé. C'est lui qui a mordu.
- **Le registre des recherches existe** : `app_search_registry`, dans `phase2/phase2.sqlite` (77 255 lignes, jamais
  vidé, ancré sur la paire (contact, rang)) ; son numéro `app_search_id` est recopié dans `app_contact_search_current`
  chez Supabase. Pour 20000008 : **77235 = rang 0 = Le Puy**, **77251 = rang 1 = Firminy**. **Il ne porte PAS l'`idCritere`
  de Hektor** (l'API ne le donne pas, étude du 21/08) ; aucun écran ne l'affiche.
- ⚠ **Le correctif « la marque locale ne doit plus dépendre du succès du travail »** (audit d'autonomie du 21/09, §4,
  « à faire avec L4 ») **n'est pas fait** : notre `archive=true` local a été écrasé 13 s plus tard par la relecture du
  contact (`2eeaf07e`). C'est pour ça que l'écran remontre Firminy « Active ».
- Mesure d'aujourd'hui (compte admin seulement) : l'ordre des `data-search-id` chez Hektor = l'ordre de notre rang
  (471880 ↔ rang 0, 471894 ↔ rang 1). **Aucune note trouvée** d'un essai de `data-search-id` en contexte négociateur.

**ESSAI 1 — 27/10, lecture seule, 11 contacts (Chrome de Frédéric, compte admin) : notre rang = l'ordre de Hektor.**

| Hektor | nos rangs | Hektor (`data-search-id` dans l'ordre, icône d'archive) | regex du worker | 1ʳᵉ recherche (prix, communes) |
|---|---|---|---|---|
| 605946 | `Ao` | `Ao` 471880, 471894 | 471880 seul | ✅ |
| 36130 | `AAo` | `AAo` 6802, 6804, 470922 | 6802 seul | ✅ |
| 544653 | `AAoA` | `AAoA` 65490, 65491, 65493, 157849 | 65490 seul | ✅ |
| 409902 · 46798 · 76150 | `Ao` | `Ao` | le 1ᵉʳ seul | ✅ |
| 48853 · 604687 | `ooo` | `ooo` | le 1ᵉʳ seul | ✅ |
| 605131 | `ooooo` | `ooooo` 471571 … 471584 | 471571 seul | ✅ |
| 80422 · 84784 | `oo` | `oo` | le 1ᵉʳ seul | ✅ |

➡ **11 sur 11** : même nombre, même suite archivée/active, même 1ʳᵉ recherche (prix toujours ; communes quand Hektor en
affiche — « Non défini » sinon, et contrôlé dans notre liste pour 409902 et 48853). ➡ **La regex du worker ne rend que
le 1ᵉʳ numéro dans 11 cas sur 11** : tout geste d'archivage sur un rang ≥ 1 vise le rang 0, sans exception.
⚠ Limites : compte **admin** seulement (le worker agit en contexte **négociateur**) ; seul le détail de la 1ʳᵉ recherche
est lisible dans l'onglet ; 11 contacts, pas le parc. *(Corrigé par l'essai 2 : le détail de la recherche N se lit
avec `searchNum=N`, comme le fait `changeSearchTabLi` de la page.)*

**ESSAI 2 — 27/10, 13:15-13:16 UTC, ÉCRITURE chez Hektor avec l'accord de Frédéric (« Oui, tu as mon accord pour l'essai
d'écriture sur la recherche Firminy 471894 du contact d'essai 605946 »), Chrome de Frédéric, compte admin.**

| moment | geste | réponse de Hektor | relecture (`changeTab`, puis `searchNum=1` pour le détail) |
|---|---|---|---|
| avant | — | — | Recherche 1 = 471880 Le Puy, icône archivée ; Recherche 2 = 471894 Firminy, **sans icône (active)** |
| marche 1 | `modifDateArchiveCritere`, `idCritere=471894`, `dateArchive=27-10-2026` — **le geste exact du worker** | `200` `{"date":"27-10-2026","desarchiveCritere":true}` | date d'auto-archivage de 471894 = **27-10-2026** ✅ ; Firminy **toujours sans icône : ACTIVE** ❌ |
| marche 2 | `recherche-archiveUnarchiveContactRecherche`, `idCritere=471894`, `idContact=605946` — la bascule du menu ⋮ de la page | `200` « Succès: le contact a été archivé/désarchivé avec succès. » (texte générique) | Recherche 2 Firminy **icône archivée** ✅ ; Recherche 1 inchangée |

➡ **Mesuré : poser la date du jour n'archive pas une recherche active SUR LE MOMENT** ; c'est la bascule qui archive tout
de suite. ⚠ **CORRIGÉ le même jour (§19.5)** : j'en avais d'abord conclu « la date n'archive pas, le geste est faux ». La
relecture des 6 recherches qui n'ont JAMAIS reçu que la date (Le Puy 471880 + 5 autres) les montre **toutes archivées** :
la date archive bien, **en différé** (vraisemblablement la nuit). Le geste est donc juste ; **le seul défaut est le ciblage**.
⚠ La bascule est une **bascule** : la rejouer sur une recherche déjà archivée la **réactive**. Le correctif doit donc lire
l'icône avant (et après) le geste, jamais l'envoyer à l'aveugle.
➡ État chez Hektor après l'essai : 605946 a ses **deux recherches archivées** (Le Puy depuis avant le 26/10, Firminy depuis
13:16 UTC le 27/10). Le témoin du 28/10 devrait passer au vert à la prochaine relecture du contact.
➡ Le correctif : voir §19.5.

### 19.5 PLAN DU CORRECTIF DU WORKER — 27/10 après-midi (« OUI VAS Y » au plan ; **pièces 1-3 CODÉES, voir E** ; worker non redémarré)

**A. Mesures qui fondent le plan (journal `app_console_job_log` + relecture Hektor en lecture seule, compte admin).**

| geste du worker | date | contact Hektor | critère visé | état chez Hektor le 27/10 |
|---|---|---|---|---|
| supprimer (rang 0) | 12/06 | 414535 | 471249 | archivée |
| supprimer (rang 0) | 22/06 | 113412 | 17985 | archivée (2ᵉ recherche active, non visée) |
| supprimer (rang 0) | 18/09 | 605075 | 471682 | le contact n'a plus aucune recherche |
| qualification acquéreur | 18/09 | 605414 · 605429 | 471691 · 471697 | le contact n'a plus aucune recherche |
| qualification acquéreur | 22/10 | 605946 | 471880 Le Puy | archivée |
| qualification acquéreur | 23/10 | 605973 · 605975 · 605976 | 471886 · 471887 · 471888 | archivées toutes trois |
| qualification acquéreur | 23/10 | 605967 (= 20000012) | **non retrouvé** (« elle ne sera pas archivée ») | ⛔ **471882 Le Puy ACTIVE depuis 4 jours** |
| supprimer (**rang 1**) | 26/10 | 605946 | **471880 au lieu de 471894** | Firminy restée active → archivée à la main le 27/10 (essai 2) |

➡ **La date archive, en différé** : 6 sur 6 de celles qui l'ont reçue sont archivées, aucune exception mesurée. Et poser la
date sur une recherche **déjà archivée** ne la réactive pas (Le Puy, 26/10). C'est **plus sûr que la bascule**, qui réactive
si on la rejoue. ➡ **On garde le geste de la date.**
➡ **Le défaut est le ciblage, et il est RÉCENT** : la liste rendait 5, 9, 11, 22 numéros en juin-août, 2 le 18/09, **1 seul
le 26/10**. Hektor a changé son HTML entre le 18/09 et le 22/10 ; la regex n'attrape plus que le 1ᵉʳ. *(En juin, le compte
mêlait sans doute d'autres numéros que des recherches — `rel=` est très large ; le rang n'était donc déjà pas sûr.)*
➡ **Trois portes en dépendent**, pas une : `resolveContactSearchTargetCritereId` (supprimer, et modifier — porte fermée
depuis C.3) et `listerCriteresBestEffort` (qualification d'un acquéreur à la vente : avant / après la création). Avec 1 seul
numéro lu, un acquéreur qui a déjà une recherche voit sa recherche de qualification **introuvable, donc jamais archivée** —
c'est 605967.

**B. Le plan (4 pièces, toutes dans `Console/console_job_worker.js`).**

1. **Lire la liste par `data-search-id`** dans `fetchHektorContactSearchList` : un numéro par recherche, dans l'ordre,
   archivées comprises, avec l'état (`icon-presentation-off`). Rendre `{ index, idCritere, archivee }`. Garder l'ancienne
   regex **seulement** si `data-search-id` est absent, et le dire au journal (`source: "data-search-id" | "regex"`).
   *Contrôle : 11 contacts sur 11 de l'essai 1 + 605946 + 605967.*
2. **Refuser de deviner** dans `resolveContactSearchTargetCritereId` : plus de repli `|| list[0]`. Rang absent de la liste →
   **erreur** claire (« rang 1 demandé, 1 recherche lue chez Hektor ») : le travail échoue, rien n'est écrit chez Hektor.
   Même règle si la liste vient de l'ancienne regex et que le rang demandé est ≥ 1.
   *Contrôle de cohérence en plus : le nombre de recherches lu chez Hektor = celui de notre registre pour ce contact ; sinon
   erreur aussi.*
3. **Rendre le vrai état** dans `handleDeleteHektorContactSearch` : relire la liste après le geste et écrire au journal la
   date posée **sur le bon numéro** (`recentValueAutoarchivage<id>` via `searchNum`). Le travail dit « date posée, archivage
   attendu cette nuit », pas « archivée ». *Le témoin du lendemain reste la vraie preuve.*
4. **La qualification hérite seule** des pièces 1-2 (même fonction de liste) : avant/après redevient juste. Rien d'autre.

**C. Ce qui n'est PAS dans ce plan (à décider par Frédéric).**
- **La marque locale** (`archive=true` écrasé par la relecture du contact, audit du 21/09 §4) : avec l'archivage différé,
  la relecture faite 1 s après le geste **remet « active »** jusqu'au lendemain. C'est un chantier à part (Supabase + build).
- **La bascule** (archivage immédiat) : écartée, car elle réactive si on la rejoue.
- **605967 / 471882** : recherche de qualification encore active chez Hektor. L'archiver = une écriture chez Hektor → accord.
- **Contexte négociateur** : toutes les lectures sont en compte admin. Le worker lit en négociateur ; la pièce 1 doit donc
  être éprouvée **en réel** sur un travail d'essai (contact 605946, accord requis), pas seulement relue.

**E. ✅ PIÈCES 1 À 3 CODÉES le 27/10 (« Go : code les pièces 1 à 3 du §19.5 dans le worker, sans redémarrer ni pousser »).
⚠ NON COMMITÉ, worker NON redémarré : le code tourne encore à l'ancienne.**
- Pièce 1 : `lireRecherchesHektor` (`{ source, recherches: [{ index, idCritere, archivee }] }`) ; l'appel HTTP est sorti
  dans `fetchHektorContactSearchTabHtml(contactId, searchNum)` ; `fetchHektorContactSearchList` garde sa forme (la
  qualification n'a pas bougé) ; `lireDateAutoArchivageHektor` lit la date d'un rang.
- Pièce 2 : `cibleRechercheHektor` (refus + journal `source`, `nos_recherches`, `deja_archivee`) ; `compterNosRecherches`
  lit `app_contact_search_current` sous l'**identité** (archivées comprises, comme Hektor) ;
  `resolveContactSearchTargetCritereId` n'en est plus qu'une enveloppe (la modification en profite aussi).
  Un refus supplémentaire, non écrit au plan : **aucun rang demandé et plusieurs recherches** → échec (avant : rang 0).
- Pièce 3 : `relireArchivageRechercheBestEffort` (étape `hektor_contact_search_archive_relue`, `done`/`error`) ; le
  résultat du travail porte `archivage: fait | differe | non_verifie`, `search_index` et `relu` ; `status: "archived"`
  est gardé (rien ne le lit, on ne change pas un contrat en passant). Le message de `archiveHektorContactSearch` dit
  « Date d'auto-archivage posée (archivage en différé) ».
- **Éprouvé** : `node --check` ✅ ; **les deux fonctions de lecture copiées du fichier, exécutées dans l'onglet Hektor**
  (lecture seule, compte admin) sur les 11 contacts de l'essai 1 + 605967 : 12 listes justes (`AAo`, `AAoA`, `ooooo`…,
  605946 désormais `AA`), date lue au bon rang (605967 → 23-10-2027 ; valeur vide = Hektor n'affiche pas de date) ;
  **les refus et la relecture exécutés tels qu'extraits du fichier**, avec des listes simulées : 8 cas de ciblage
  (dont le 26/10 rejoué avec l'ancienne liste → **refusé**, « rang 1 demandé, 1 recherche lue ») + 5 cas de relecture
  (date posée, déjà archivée, autre date, numéro disparu, Hektor en panne) → tous conformes.
- **Pas éprouvé** : en **contexte négociateur** et par un vrai travail. À faire après redémarrage, sur 605946 (accord
  requis : écriture chez Hektor). Ses deux recherches sont archivées : un « supprimer » de rang 1 doit poser la date sur
  471894 et dire « déjà archivée ».

**D. Ce que ça pourrait casser ailleurs.** La pièce 2 transforme un mauvais geste silencieux en **échec visible** : un
contact dont la liste ne se lit pas verra son « supprimer » échouer au lieu de viser la 1ʳᵉ recherche. C'est voulu.
La pièce 1 touche la création (`listerCriteresBestEffort`) : si `data-search-id` venait à manquer, l'ancienne regex reprend,
comme aujourd'hui — pas pire qu'avant.


---

## 23. 6 bis — LES DEUX DÉCISIONS DU 27/10, ET POINT 7 — RE-AUDIT DU 27/10 (rien codé)

### 23.1 Les décisions de Frédéric sur les réserves du 6 bis (27/10)

> « 6bis 1 oui tu as raison 2. aussi pour la synchro de nuit. ensuite audit 7. 8 pour plus tard »

**D1 — l'e-mail ne part qu'à l'ABANDON du geste, plus au 1er échec.**
- **Mesuré.** `notifyJobFailureBestEffort` est appelé à **chaque** échec (`processOnce`, `console_job_worker.js`).
  - Seuls **10 types** sont rejoués, par `app_console_action_enqueue_due_retries`, jusqu'à 5 essais en ~50 min et dans les 24 h : statut, archiver, désarchiver, supprimer annonce/contact, négociateur, offre, compromis ×2, vente.
  - Tous les autres types sont **définitifs dès le 1er échec**, `update_hektor_annonce_fields` compris.
  - `job.attempt_count` est déjà le numéro de l'essai en cours : la prise fait +1 et rend `j.*`.
- **Ce que je ferais.** Prévenir seulement si le travail ne repartira pas :
  - refus d'état ;
  - OU type non rejoué ;
  - OU 5ᵉ essai ;
  - OU demande vieille de plus de 23 h.
- **Interrupteur.** `CONSOLE_ALERTE_A_L_ABANDON` : `0` rend l'ancien comportement.
- **Effet.**
  - Rien ne change pour les types définitifs : l'e-mail part au 1er échec, qui est le dernier.
  - Pour les 10 types rejoués, une panne guérie par le rejeu n'envoie plus d'e-mail.
  - Pour un contact ou une recherche, l'alerte ne peut plus partir 5 fois : une seule au plus.
- **Ce que ça pourrait casser.** La liste des 10 types existerait en **deux copies**, SQL et worker. C'est le même patron que `REJEU_MAX_TENTATIVES` (13/10).
  - Si un type **sort** de la liste SQL sans sortir du worker, son abandon n'envoie **pas** d'e-mail. Le moniteur (`geste_abandonne`, 3 h) et la pastille rouge restent.
  - L'autre sens est bénin : l'alerte part au 1er échec, comme avant.
- **Pour l'activer.** Redémarrer les 4 services, avec accord, 0 pending ET 0 running.

**D2 — la pastille ne rougit que pour un geste d'utilisateur, pas pour une synchro de nuit.**
- **Mesuré sur 30 jours** : sur 12 erreurs, 9 sont des synchros, à savoir `refresh_console_contact_data` ×6, `sync_console_documents` ×2 et `sync_hektor_photos` ×1.
  - La **pastille** rougit sur tout ce que rend `app_action_status`, quel que soit le type.
  - L'**e-mail**, lui, ne part que pour `JOB_TYPES_A_NOTIFIER`.
- **Ce que je ferais, dans le front seulement.** La pastille ne garde que les gestes de la liste qui prévient : **rouge ⇔ un e-mail est parti**.
  - Le **bandeau admin** de la fiche et l'écran **Santé** ne changent pas : l'admin continue de voir les synchros en échec.
  - **Aucune écriture en base.**
- **⚠ À trancher.** Les 4 gestes de transaction ne sont **pas** dans la liste qui prévient, et ce depuis leur naissance le 29/08 : offre, annuler le compromis, supprimer le compromis, supprimer la vente.
  - Leur échec ne prévient donc personne.
  - Je propose de les ajouter aux deux listes : il y a 0 échec en 90 jours, donc aucun bruit.
- **Nuance qui reste.** Pour un type **définitif**, l'e-mail part tout de suite, mais la pastille reste « en attente » jusqu'à 3 h avant de rougir.
  - C'est la règle `@seuil-3h` de `app_action_status`.
  - La corriger demanderait une écriture en base : c'est un sujet à part, pas proposé ici.

### 23.2 Point 7 — « Finitions » : ce que le code montre

**7a — Échap ne ferme rien (N8).**
- **Les fiches.**
  - annonce sur bureau, en grande fiche ou en cockpit ;
  - annonce sur téléphone (`mobile-detail-overlay`) ;
  - contact **par-dessus** l'annonce ;
  - contact seul, dans l'écran Contacts.
- **Les fenêtres.** Le front en a une quarantaine, sans balisage commun :
  - 15 `aria-modal` ;
  - 16 `role="dialog"` ;
  - 14 `modal-overlay` ;
  - et une dizaine de classes propres (`edit-overlay`, `estim-pdf-overlay`, `fcx-overlay`, …).
  - Plusieurs gèrent déjà Échap : le menu ☰, la recherche globale, l'édition en ligne (qui annule la saisie).
- **Ce que je ferais.**
  - Une seule écoute. Échap fait **exactement ce que fait le bouton Retour/Fermer de la fiche** : on marque ces boutons et on clique le plus haut. L'adresse, le fil et le retour vers le contact restent donc identiques.
  - Échap ne fait **rien** si le curseur est dans un champ.
  - Échap ne fait **rien** si une fenêtre est ouverte par-dessus. Dans le doute, rien.
  - Un Échap = un niveau : le contact posé sur une annonce se ferme d'abord.
- **Interrupteur.** `ECHAP_FERME_LA_FICHE`.
- **Ce que ça pourrait casser.**
  - Une fenêtre non recensée fermerait **aussi** la fiche. Le remède est l'inventaire complet au codage, composants compris, et la règle « dans le doute, rien ».
  - Une saisie non enregistrée hors fenêtre serait perdue, mais pas plus qu'avec le bouton Retour.

**7b — le détail rechargé en boucle (M3, N9).**
- **Mesuré dans le code.** L'effet du détail (`App.tsx` ~15285) dépend de `[selectedDossierId, session, dataReloadKey, dossiers, mandats]`.
  - Une relecture de l'app arrive après chaque geste, à la fin de chaque travail qui concerne l'écran, et à la fin de la relecture Hektor d'ouverture.
  - Elle relance le détail **3 fois** : la clé, puis la liste des annonces, puis celle des mandats.
  - Chaque chargement fait environ 5 requêtes **en série**, dont le détail de ~90 Ko.
  - ⚠ Et **fiche fermée** : `selectedDossierId` reste posé tant que le bien est dans la page. Chaque page, chaque filtre et chaque frappe dans la recherche de la liste rechargent donc une fiche que personne ne regarde. Ce cas a échappé au point 0, qui a supprimé la sélection d'office mais pas celle qui reste après la fermeture.
- **Ce que je ferais.**
  1. Remplacer `dossiers` / `mandats` par ce que l'effet utilise vraiment : « le bien est-il dans la liste » et « est-il léger (archive) ». On passe à **1 chargement par relecture au lieu de 3**.
  2. Ne charger que **fiche ouverte**, en ajoutant `detailOpen`. C'est cohérent avec le point 0 : « aucun écran ne lit la sélection fiche fermée ». Rouvrir une fiche la relit, ce qui est voulu.
- **Interrupteur.** `DETAIL_UNE_FOIS`.
- **Ce que ça pourrait casser.**
  - Un écran qui lirait le **détail** fiche fermée : je revérifie chaque lecteur de `selectedDossier` avant de coder.
  - Le lien profond du point 1 (`ficheDemandeeParAdresse`) : il charge à l'arrivée du numéro, sans attendre la liste, donc il ne bouge pas.
  - Le passage à une fiche légère quand la liste arrive : le booléen change, donc l'effet repart, comme aujourd'hui.
  - L'effet voisin (~15270), qui pose la fiche depuis la ligne de liste sans requête, reste tel quel.

**7c — une liste déjà vue s'affiche tout de suite.**
- **Mesuré dans le code.**
  - Une liste n'est **pas vidée** pendant son rechargement : ses lignes restent, avec « Mise à jour… ».
  - Mais `dossiers` est **une seule liste partagée** par Accueil, Annonces, Suivi, Estimations et Agenda (`mandats` aussi, entre Annonces et Mandats).
  - Donc Annonces → Suivi → Annonces pourrait montrer les lignes du **Suivi** sous le titre Annonces pendant 0,5 à 1,6 s. ⚠ **Non vu à l'écran** : le mock répond instantanément. À vérifier avec une latence simulée **avant** de coder.
- **Ce que je ferais.**
  - Une petite mémoire, en mémoire vive et pour l'onglet seulement, des dernières vues : écran, filtres, page et portée, 10 au plus.
  - En revenant sur une vue, ses lignes s'affichent tout de suite, puis la relecture part en fond comme aujourd'hui.
  - La mémoire est effacée à la déconnexion.
- **Interrupteur.** `LISTE_DEJA_VUE`.
- **Ce que ça pourrait casser.**
  - On montre une liste vieille de quelques minutes pendant ~1 s : un bien vendu entre-temps reste affiché le temps de la relecture, avec « Mise à jour… » visible.
  - Après un geste, la relecture remet la mémoire à jour.

**Ordre proposé : 7b, puis 7a, puis 7c.**
- 7b est le gain le plus net et le moins visible.
- Chacun a son interrupteur et son propre « vas-y ».

**Contrôle prévu.**
- mock bienvu, bureau ET téléphone ;
- un compteur provisoire des chargements de détail, retiré avant commit ;
- `npm run build` ;
- puis la vraie app ouverte **déconnectée**, pour vérifier que la connexion n'est pas cassée (§22.4).

**Point 8 (découper `App.tsx`) : remis à plus tard par Frédéric le 27/10.**

### 23.3 ✅ 6 bis (D1 + D2) ET 7b CODÉS ET CONTRÔLÉS (27/10, « Vas-y pour le 6 bis … puis le 7b ») — commit `1101fb3`

**La question de Frédéric avant le 7b : « retrouver d'abord la raison pour laquelle on a mis ces refresh ».**
- L'histoire, retrouvée par `git log -S` :
  - jusqu'au 21/05, l'effet du détail dépendait de `[selectedDossierId, session, dataReloadKey]` ;
  - `b0c582f` (21/05, « cache des annonces historiques ») a ajouté `dossiers`, `mandats` ;
  - `10bd1a2` (22/05) et `d07a540` (09/06, mobile) n'ont touché que la garde « fiche légère » et l'ont sortie des dépendances (par une ref).
- **La raison n'était pas de rafraîchir la fiche.** La ligne de liste dit si le bien est une **archive légère** (on ne charge pas son détail complet). L'effet devait donc repartir quand la liste arrive APRÈS le clic.
- Ce besoin est gardé à l'identique : l'effet suit le booléen `ficheLegereDansLaListe` au lieu des deux listes.
- Le rafraîchissement voulu reste `dataReloadKey`, c'est-à-dire après un geste, la fin d'un travail ou la relecture Hektor d'ouverture (point 3c).

**Ce qui est en place (3 interrupteurs, chacun `false`/`0` = l'ancien comportement) :**
- `CONSOLE_ALERTE_A_L_ABANDON` (worker) : l'alerte ne part que si `travailAbandonne()` répond oui.
  - Sinon, une ligne « Alerte retenue : le travail sera rejoué (essai n sur 5) » est écrite au journal du travail.
  - Les 4 gestes de transaction entrent dans `JOB_TYPES_A_NOTIFIER`, avec un libellé.
- `PASTILLE_GESTES_SEULEMENT` (front) : le rouge ne compte que les gestes de `GESTES_QUI_PREVIENNENT`.
  - C'est une **copie** de la liste du worker, donc rouge ⇔ e-mail.
  - Le bandeau admin et l'écran Santé ne changent pas.
- `DETAIL_UNE_FOIS` (front) :
  - les dépendances sont `[selectedDossierId, session, dataReloadKey, detailOpen, ficheLegereDansLaListe]` ;
  - fiche fermée, rien ne se charge.
  - J'ai revérifié le 27/10 que `MandatsScreen` (menu Annonces) et `SuiviMandatsScreenV2` reçoivent la fiche mais ne la lisent **jamais**.
  - Le registre (menu Mandats) a son propre `detailOpen` et son propre chargement (`editorDetailed`) : il n'est pas touché.

**Contrôles :**
- **L'essai du worker** (`node Console/test_alerte_a_l_abandon.js`) est vert à **14/14**, sur le code réel découpé :
  - type définitif ⇒ alerte au 1er échec ;
  - type rejoué ⇒ retenue aux essais 1 à 4, alerte au 5ᵉ ;
  - refus d'état ⇒ alerte ;
  - demande de plus de 23 h ⇒ alerte ;
  - copie identique à la liste lue en base ;
  - transactions présentes ;
  - `processOnce` passe par la règle.
  - ⭐ **Témoin inverse** : sur un worker abîmé (garde du refus d'état retirée et un type ôté de la liste), l'essai sort en **1** avec les 2 bons échecs.
- **Le 7b, mesuré dans la maquette** par un compteur provisoire (retiré avant le commit, `api.ts` intact). Même scénario, avec et sans l'interrupteur :

| scénario | `DETAIL_UNE_FOIS = true` | `false` (avant) |
|---|---|---|
| ouvrir une fiche | 1 | 1 |
| 3 relectures de l'app, fiche ouverte | **+3** | **+6** |
| fiche fermée : 3 relectures + 4 frappes dans la recherche | **+0** | **+1** |
| rouvrir une fiche | +1 (voulu : rouvrir relit) | — |

  - Contrôlé sur **téléphone** (fiche `mobile-detail-overlay`) **et bureau** (cockpit plein écran, 1 440 px). La fiche est complète, et la pastille « Hektor · à jour » est visible.
  - Les erreurs 500 de la console viennent de `/api/hektor-diffusion/broadcasts`, qui n'a pas de serveur en maquette. Elles sont sans rapport.
- `npm run build` vert.
- **La vraie app construite en local, ouverte DÉCONNECTÉE** (`hektor-dist-reel`, leçon du §22.4) affiche « Bon retour », sans erreur JavaScript.
  - Les deux 401 (`app_searches_to_complete`, `app_condition_catalogue`) existent **à l'identique en production** : ils sont antérieurs au correctif.

**Ce qui n'est PAS éprouvé :**
- un vrai échec de geste rejoué (e-mail retenu puis envoyé au 5ᵉ) ;
- une pastille rouge réelle ;
- le nombre de chargements en production, qui demande une session connectée.

**Pour que ce soit actif :**
- **Pousser.** Vercel déploie la pastille et le 7b.
- **Redémarrer les 4 services worker** pour D1, avec l'accord de Frédéric, **0 pending ET 0 running**. Tant qu'ils ne redémarrent pas, l'alerte part encore à chaque échec : c'est l'ancien comportement, sans risque.

⚠ **Coordination.**
- Le worker porte aussi les changements Youtrust / PDF de mandat de l'autre session, non commités. Ils sont restés hors du commit, qui a été indexé à partir de `HEAD` + mes seuls changements.
- Un redémarrage chargera **aussi** leur code non commité : il faut le dire à l'autre session avant.

**✅ EN LIGNE LE 27/10 (« REDEMARRE ET PUSH »).**
- **Front.** `1101fb3` et `8ff6e76` sont sur `origin/main`, et la production sert `index-L0oeshOf.js`.
  - Ce bundle contient la liste de la pastille, avec les 4 gestes de transaction.
  - Ouverte déconnectée, l'app affiche « Bon retour », sans autre erreur que les deux 401 antérieurs.
- **Worker.** Les 4 services ont démarré à **10:23:06-08** : c'est la ligne `"worker":` de chaque journal.
  - Le redémarrage n'a pas été fait par moi : sans élévation, mon `Restart-Service` de 10:24 a été refusé (« Impossible d'ouvrir le service »).
  - Le fichier du worker datait de **09:47:27**, avant le démarrage : le code de l'alerte à l'abandon est donc chargé.
  - La file était vide : aucun travail mis à jour depuis 10:10, puis 0 pending / 0 running à 10:24. Aucune erreur dans les 4 journaux depuis.
  - ⚠ **Ce démarrage a aussi chargé le code Youtrust / PDF de mandat NON COMMITÉ de l'autre session.** Il dort : `app_setting.signature_youtrust = off` (vérifié à 10:24), et ses deux branches ne jouent qu'interrupteur allumé.

### 23.4 Point 7a — Échap ferme la fiche : RE-AUDIT DU 27/10 (inventaire, essais en maquette ; rien codé)

**Inventaire du code** (script sur les 15 `.tsx` du front ; `role="dialog"`, `aria-modal`, `createPortal`, classes en
overlay / backdrop / modal / drawer, et chaque écoute d'Échap) — **~35 fenêtres**, sans balisage commun :

| famille | où | Échap aujourd'hui |
|---|---|---|
| 13 fenêtres de demande / action (`modal-overlay` + `modal-panel`) : baisse de prix, annulation, diffusion, statut, activer, import d'archive… | App (rendu de l'app) | ❌ rien |
| fenêtres d'agenda / e-mail (`createPortal` + `modal-overlay`) | GoogleAgenda*, ContactEmailComposerModal | ❌ rien |
| aperçu / éditeur PDF (`estim-pdf-overlay`, `estim-editor-modal`), cycle (`fcyc-modal`), tiroir de transaction (`transaction-detail-drawer`) | CockpitDetail, DossierDetailLayoutBase, MobileDossierDetail | ❌ rien |
| visionneuse photo (`bvv`, dialog) | BienvuViewer | ✅ se ferme (écoute la fenêtre, `preventDefault`) ; en plein écran, c'est le navigateur qui sort |
| recherche globale, rapprochement (stats), modification de contact | RechercheGlobale, RapprochementStats, ContactEditModalV2 | ✅ se ferment |
| menus : ☰ téléphone (`mtiroir`), compte (`rn-pop`, menu), cloche (`gti-notif-pop`, dialog), compteur de mes actions | MobileLayout, App, NotificationsBell | ✅ se ferment |
| édition en ligne d'un champ (cockpit, champs corrigeables) | CkInlineField, CkDescField, CorrigeableAnnonceField | ✅ **annule la saisie** — à ne pas casser |
| **les fiches** | voir ci-dessous | ❌ **rien (N8)** |

**Les fiches, et leur bouton de sortie** (mesuré en maquette, bureau 1 440 px ET téléphone) :

| fiche | conteneur | bouton qui la ferme aujourd'hui |
|---|---|---|
| annonce, bureau (cockpit) | ⚠ un `modal-overlay` plein écran — **la fiche elle-même est bâtie comme une fenêtre** | `fa-ck-rail-brand` : « Retour aux annonces », ou **« Retour au Cockpit »** quand une rubrique est ouverte (un niveau de plus) |
| annonce, téléphone | `mobile-detail-overlay` | `mobile-detail-close` « Fermer » |
| contact (sur une annonce, ou écran Contacts) | `fa-cx-overlay` (bienvu) / `fcx-overlay` | `fa-cx-back` / `fcx-back` — ⚠ **non testable en maquette** (0 contact ; le mandant 1001 met `contact=1001` dans l'adresse sans afficher de fiche) |
| registre (menu Mandats) | `modal-overlay` | `md-btn` « Retour » et « Fermer » (son propre `detailOpen`) |

**Ce que les essais ont trouvé :**
- ⚠ **Le tiroir ☰ du téléphone est TOUJOURS dans la page**, poussé hors écran (`translateX(-347px)`), avec `role="dialog"`
  même fermé. Une règle « une fenêtre est ouverte » naïve **désactiverait Échap pour toujours** sur ce rendu → il faut
  le critère « **visible DANS l'écran** » (rectangle qui coupe la fenêtre). *(Au passage : un `role="dialog"` sur un
  tiroir fermé est faux pour les lecteurs d'écran — noté, hors chantier.)*
- ✅ Avec ce critère, **rien n'est vu** sur une liste (Accueil, Annonces, Mandats, Contacts), et **chaque fenêtre ouverte est
  vue** : demande de baisse de prix, statut, visionneuse photo (téléphone) ; cloche et menu du compte (bureau, `role`
  + `aria-expanded`).
- ⚠ Sur le bureau, la fiche cockpit **et** le registre sont des `modal-overlay` : il faut **marquer les conteneurs de
  fiche** pour ne pas les prendre pour une fenêtre posée dessus.

**Ce que je ferais** — interrupteur `ECHAP_FERME_LA_FICHE` :
1. **Marquer**, sans rien changer à leur comportement, les ~6 conteneurs de fiche (`data-fiche`) et leur bouton de sortie
   (`data-fiche-retour`) : cockpit (rail), téléphone, contact ×2, registre.
2. **Une seule écoute** (dans `App`, **au-dessus des `return` de connexion** — §22.4). À Échap :
   - rien si la touche a déjà été traitée (`defaultPrevented` : visionneuse, recherche globale), si elle est répétée ou
     accompagnée d'une autre touche ;
   - rien si le curseur est dans un **champ** (`input`, `textarea`, `select`, éditable) : l'édition en ligne garde son Échap ;
   - rien si une **fenêtre visible dans l'écran** est ouverte et n'est pas une fiche (sélecteur large : dialog, menu,
     aria-modal, overlay, backdrop, drawer, lightbox, `-modal`) — **dans le doute, rien** ;
   - sinon : prendre la fiche **du dessus** (l'élément au centre de l'écran, `elementFromPoint`, et sa fiche ; à défaut la
     dernière visible) et **cliquer SON bouton de sortie**.
3. Conséquence voulue : **un Échap = un niveau**, exactement comme le bouton — rubrique → cockpit → liste ; contact posé
   sur une annonce → l'annonce ; et l'adresse, le fil (point 5) et le retour vers le contact (point 1) restent ceux du
   bouton, puisque c'est lui qui agit.

**Ce que ça pourrait casser ailleurs :**
- **une fenêtre que le sélecteur ne verrait pas** fermerait la fiche **dessous**, avec ce qui y était tapé. Remède : la
  liste des ~35 est passée en maquette une par une au codage ; celles qu'on ne peut pas ouvrir en maquette (fenêtres
  contact, agenda) sont couvertes par leur classe (`modal-overlay`) ; et **un menu interne sans rôle** (ex. le menu
  « actions » de la fiche contact, `contactActionsOpen`) est à **recenser au codage** et à ajouter ;
- **les fenêtres de demande / agenda ne se ferment PAS à Échap** (aujourd'hui non plus) : pendant qu'elles sont ouvertes,
  Échap ne fait rien. Les fermer aussi serait **un autre geste** (13 fenêtres, des saisies dedans) — **non proposé ici** ;
- **téléphone** : pas de touche Échap en pratique ; le bouton « retour » d'Android passe par l'adresse (point 1), inchangé ;
- la **fiche contact** ne peut pas être éprouvée en maquette : il faudra soit un contact de maquette, soit l'essai en réel.

**Contrôle prévu** : maquette bienvu bureau ET téléphone — chaque fiche se ferme ; rubrique → cockpit → liste ; Échap ne
fait rien avec une fenêtre de demande, la visionneuse, la cloche, le menu du compte, le ☰ ouvert ; Échap dans un champ du
cockpit annule la saisie **sans** fermer la fiche ; témoin inverse interrupteur éteint ; `npm run build` ; la vraie app
ouverte **déconnectée**.

### 23.5 ✅ POINT 7a CODÉ ET CONTRÔLÉ EN MAQUETTE (27/10, « Vas-y pour le 7a comme proposé ») — ⚠ fiche contact NON éprouvée

**Ce qui est en place** — interrupteur `ECHAP_FERME_LA_FICHE` (`false` = l'ancien comportement) :
- 6 fiches marquées `data-fiche` (annonce bureau, annonce téléphone, contact ×2, registre) et leur bouton de sortie
  `data-fiche-retour` (rail du cockpit, « Fermer » du téléphone, retour contact ×2, « Retour » du registre) —
  **attributs seulement**, aucun comportement changé ;
- une écoute dans `App`, **au-dessus des `return` de connexion** (l. ~14835 contre ~20786) : Échap clique le bouton de
  la fiche du dessus, sauf touche déjà traitée, touche combinée, champ, ou fenêtre visible dans l'écran par-dessus.

**Trois choses que les essais ont corrigées EN CODANT (elles n'étaient pas dans la proposition) :**
1. **`-modal` en fin de classe seulement** : `google-agenda-modal-layout` (mise en page de la rubrique Rendez-vous) passait
   pour une fenêtre → Échap ne faisait rien dans cette rubrique. Les vraies fenêtres finissent par `-modal`
   (`estim-editor-modal`, `fcyc-modal`…) ; `fa-cx-modal-scope` (enveloppe toujours présente de la fiche contact) est hors jeu.
2. **Le bouton de sortie n'a pas à être DANS l'écran** : sur une fiche qu'on a fait défiler, le rail du cockpit sort par le
   haut (mesuré à −193 px) et Échap ne faisait plus rien. « Affiché » suffit pour le bouton ; « dans l'écran » ne sert
   qu'aux fenêtres (le tiroir ☰ caché hors écran).
3. **Un champ qui se retire à Échap** (l'édition en ligne du cockpit) : quand l'événement arrive à la fenêtre, l'élément
   actif est déjà le corps de la page. La garde regarde donc AUSSI `event.target`, qui reste le champ. Reproduit par un
   champ retiré par un écouteur posé sur `#root` (là où React écoute) : la fiche **reste ouverte**.

**Contrôles en maquette bienvu :**

| essai | bureau 1 440 px | téléphone 375 px |
|---|---|---|
| liste seule + Échap | rien | rien (tiroir ☰ fermé hors écran : ignoré) |
| fiche + Échap | **fermée**, adresse `?ecran=annonces` | **fermée** |
| rubrique Le Bien / Publicité / Rendez-vous / Contact + Échap | **retour au cockpit** (×4), puis Échap → liste | — |
| fiche défilée, rail à −193 px + Échap | **fermée** | — |
| menu « Plus d'actions » ouvert + Échap | fiche **reste** | — |
| Rapprochement (fenêtre) + Échap | la fenêtre se ferme (son écoute), la fiche **reste** ; 2ᵉ Échap → liste | — |
| cloche ouverte + Échap | la cloche se ferme, la fiche **reste** | — |
| Échap dans un champ (même retiré) | fiche **reste** | — |
| demande « Baisse prix » ouverte + Échap | — | fiche **et** demande **restent** |
| visionneuse photo + Échap | — | la visionneuse se ferme, la fiche **reste** |
| ☰ ouvert sur la fiche + Échap | — | le tiroir se ferme, la fiche **reste** |
| registre (menu Mandats) + Échap | **fermée** | — |
| **témoin inverse** : interrupteur éteint, fiche + Échap | — | fiche **reste** (l'ancien comportement) |

`npm run build` vert. **Vraie app construite en local, ouverte DÉCONNECTÉE** : « Bon retour », le bundle porte
`data-fiche-retour`, seuls les deux 401 antérieurs.

**Ce qui n'est PAS éprouvé :**
- **la fiche contact** (sur une annonce, et dans l'écran Contacts) : la maquette n'a aucun contact. Le marquage est le même
  que les autres (conteneur + bouton de retour existant) ; à essayer en réel : contact posé sur une annonce + Échap →
  l'annonce ; 2ᵉ Échap → la liste ;
- l'édition en ligne réelle (les champs de la maquette sont en lecture seule) — couverte par la reproduction ci-dessus ;
- un clavier sur tablette.

### 23.6 Point 7c — « une liste déjà vue s'affiche tout de suite » : RE-AUDIT DU 27/10 (mesuré en maquette ralentie ; rien codé)

**Mise en ligne du 7a vérifiée (27/10, ~14:30).** `b3b0fb8` est dans `origin/main` ; le bundle de production
(`index-CA0qO0uU.js`) porte `data-fiche-retour` et la règle Échap ; l'app ouverte déconnectée affiche « Bon retour », avec
seulement les deux 401 connus.

**Audit limité aux listes de l'effet des listes** (`App.tsx` ~15297 : `dossiers`, `mandats`, `workItems` et leurs compteurs),
qui servent à Accueil, Annonces, Estimations, Mandats (registre), Suivi et Agenda. Seul le geste **lire** est concerné ;
créer / modifier / supprimer n'interviennent que par les retouches locales après un geste (voir « ce que ça pourrait
casser »). Les contacts sont traités à part, plus bas.

**Mesuré à l'écran** — maquette ralentie de 1,5 s par liste (délai temporaire marqué `TEMP-7C`, **retiré** ; `api.ts`
identique à HEAD) :

| passage | bureau (1440 px) | téléphone / tablette (800 px) |
|---|---|---|
| Annonces → Estimations | ⚠ « **3 estimations** · 1-3 / 3 » pendant 1,5 s (les lignes des annonces, voilées par « Chargement… »), puis 0 | « Chargement… », puis « Aucune ligne » |
| Annonces → Mandats | ⚠ « **3 mandats** » (les annonces) pendant 1,4 s, puis 2 | ⚠ « 3 / 3 », puis « 2 / 2 » |
| Mandats → Annonces | ⚠ « **2 annonces actives** », les 2 lignes du registre en grisé sous « Chargement… » | ⚠ « 2 / 2 » : les cartes du registre **affichées et cliquables, sans aucun signe de chargement**, 1,5 s |
| Estimations → Annonces | ⚠ « **0 annonces actives** » pendant 1,5 s | « Chargement… » pendant 1,5 s |
| Suivi → Annonces | juste **par chance** : la maquette a les mêmes 3 lignes des deux côtés | idem |

**Temps réels** (mesurés le 23/10, §2) : 0,5 s pour Annonces et le registre, 0,6 s Accueil, 0,9 s Suivi, 1,4 s
Estimations, 1,6 s Agenda. En production, la fenêtre fautive dure donc **0,5 à 1,6 s** à chaque changement d'écran.

**Le constat est confirmé.** Sur bureau, les **compteurs mentent** ; sur téléphone, les **lignes d'un autre écran** sont
montrées et cliquables. La cause : une seule liste `dossiers` / `mandats` / `workItems` (et leurs totaux) pour tous les
écrans, et l'effet des listes ne la vide pas au changement d'écran.

**Contacts : rien à faire.** Leur liste est à part (`contactsDirectory`, ~15124) et lue seulement par l'écran Contacts.
Elle garde ses lignes au retour, avec « Mise à jour… » ; avec la mémoire du point 2 (filtres, page), elle s'affiche
**déjà** tout de suite. Sa lenteur (3,6 s, M4) vient de la base.

**Ce que je ferais** — interrupteur `LISTE_DEJA_VUE`, dans l'effet des listes seulement :
1. **Au changement d'écran, jamais les lignes d'un autre écran.** Si la vue est en mémoire, on la montre (point 2) ;
   sinon, les trois listes et leurs compteurs sont **vidés** et l'écran affiche « Chargement… », comme Estimations →
   Annonces sur téléphone aujourd'hui.
   **Dans un même écran** (page, filtre, frappe), rien ne change : les lignes restent sous « Mise à jour… », sinon chaque
   frappe ferait clignoter « Chargement… ».
2. **Une mémoire des vues.**
   - La clé : écran + filtres + pages + portée.
   - 10 vues au plus, en mémoire vive, pour l'onglet seulement, vidée à la déconnexion.
   - Elle n'est écrite **que par les réponses du serveur**, jamais par les retouches locales.
   - En revenant sur une vue, ses lignes et ses compteurs s'affichent **tout de suite**, et la relecture part en fond comme
     aujourd'hui.
   - **Aucune requête en moins** : le gain est l'attente (0,5 à 1,6 s) à chaque retour sur un écran déjà vu.

**Ce que ça pourrait casser ailleurs** — les lecteurs de ces listes, recensés :
- **`jobConcernsThisScreen`** (~14671) décide si la fin d'un travail recharge l'écran, en regardant les lignes affichées.
  - Liste vidée : pendant 0,5 à 1,6 s, la fin du travail d'un **collègue** sur un bien du nouvel écran ne relancerait pas
    de relecture. Mais celle qui est en cours ramène l'état frais.
  - Aujourd'hui, pendant cette même fenêtre, il regarde les lignes de l'écran **précédent**.
  - Effet neutre.
- **`inferredUserNegotiatorContext`** (~20421) devine le négociateur d'après les lignes. C'est le **3ᵉ repli**, après le
  profil et l'identité Google.
  - Liste vidée, il vaut `null` pendant au plus 1,6 s, au moment d'un changement d'écran, quand aucun formulaire n'est
    en cours.
- **La fiche** : `openScreen` la ferme au changement d'écran. L'effet qui pose la fiche depuis la ligne (~15375) garde
  la fiche courante si elle n'est pas dans la liste. Le booléen du 7b relit la liste qui arrive. Neutre.
- **Les sélections** (`selectedMandatId`, `selectedRegisterRowId`) ne sont posées qu'à la réponse du serveur : pas de
  changement.
- **Les retouches après un geste** (`setMandats((current) => …)`, une quinzaine d'endroits) modifient la liste affichée,
  pas la mémoire.
  - Une vue rappelée montre donc l'état du serveur à son dernier passage pendant 0,5 à 1,6 s, puis la relecture la
    corrige.
  - ⚠ Un bien archivé ou supprimé depuis peut **réapparaître ce temps-là dans une autre vue** en mémoire. Sur bureau,
    c'est sous « Mise à jour… » ; ⚠ sur téléphone, **sans signe**, car ses listes n'ont pas d'indicateur « Mise à jour… »
    (seulement « Chargement… » quand elles sont vides). Ajouter cet indicateur n'est **pas** proposé ici : c'est à trancher.
- **La mémoire vive** : Suivi charge jusqu'à 1 000 mandats, donc 10 vues pèsent au pire quelques Mo.

**Retour arrière** : `LISTE_DEJA_VUE = false`, en une ligne.

**Contrôle prévu** :
- la même maquette ralentie, avec les 5 passages, sur bureau et téléphone ;
- un aller-retour dans un même écran (filtre, page) : pas de « Chargement… » ;
- le témoin inverse, interrupteur éteint ;
- `npm run build` ;
- la vraie app déconnectée.

### 23.7 ✅ POINT 7c CODÉ ET CONTRÔLÉ EN MAQUETTE (27/10, « Vas-y pour le 7c comme proposé (LISTE_DEJA_VUE), sans indicateur sur téléphone »)

**Ce qui est codé** (`App.tsx`, 65 lignes ajoutées, aucune retirée), derrière l'interrupteur `LISTE_DEJA_VUE`, posé entre
`DETAIL_UNE_FOIS` et `ECHAP_FERME_LA_FICHE` :
- **La clé d'une vue** : utilisateur, écran, filtres, les 3 pages et la portée. C'est tout ce qui fait partir la lecture,
  sauf la relecture (`dataReloadKey`). L'utilisateur est dans la clé : deux comptes dans le même onglet ne se mélangent pas.
- **En tête de l'effet des listes**, quand la clé change :
  - vue en mémoire → ses 3 listes et leurs 3 totaux sont posés tout de suite ;
  - sinon, si l'**écran** a changé → listes et totaux vidés ;
  - sinon (même écran) → rien, comme avant.
- **Chaque réponse du serveur** est retenue pour sa vue. Une vue n'est rappelée que si ses **trois** morceaux sont arrivés.
  On garde au plus 10 vues, la plus ancienne sort.
- **La déconnexion** vide la mémoire.
- **Pas d'indicateur ajouté sur téléphone**, comme décidé.

**Contrôlé en maquette ralentie** (1,5 s par liste ; délai `TEMP-7C` retiré, `api.ts` identique à HEAD) :

| passage | bureau (1440 px) | téléphone (375 px) |
|---|---|---|
| 1ʳᵉ visite d'Annonces, de Mandats, d'Estimations | compteurs à **0** sous « Chargement… », puis les bons | « Chargement… », puis les bonnes lignes |
| Annonces → Mandats → Annonces (retour) | « **3 annonces actives** » tout de suite (avant : « 2 ») | « **3 / 3** » en 60 ms (avant : les 2 cartes du registre) |
| Mandats (retour) | « **2 mandats** » tout de suite (avant : « 3 ») | « **2 / 2** » en 160 ms |
| Annonces → Estimations | « **0 estimations** » (avant : « 3 estimations ») | « Chargement… », puis « Aucune ligne » |
| frappe « Fauriel » dans la recherche d'Annonces | — | les 3 lignes **restent** jusqu'à la réponse (1 / 1), **pas** de « Chargement… » |
| **témoin inverse** (interrupteur éteint) | — | le défaut revient : « 3 / 3 » sous Mandats, puis « 2 / 2 » sous Annonces |

`npm run build` vert. **Vraie app construite en local, ouverte DÉCONNECTÉE** : « Bon retour », seulement les deux 401
antérieurs.

**⚠ Constaté au contrôle, NON corrigé** (hors du périmètre accordé) — sur bureau, Annonces et Estimations ont un **voile**.
- Il couvre la liste à **chaque relecture** : `listing-loading-banner`, `App.tsx` ~26475. Avec bienvu, il est en
  `position: absolute; inset: 0`, blanc à 72 %, avec « Chargement… » (`bienvu.css:284`, refonte du 19/10). Sans bienvu,
  c'était une fine barre collante.
- Une vue rappelée y arrive donc **juste** (bons compteurs, bonnes lignes), mais **voilée et non cliquable** pendant la
  relecture (0,5 s en production pour Annonces).
- Le registre (Mandats) n'a pas ce voile : ses lignes sont utilisables tout de suite.
- Ne voiler que la liste **vide** rendrait le gain visible sur bureau. C'est une décision de dessin : **à trancher par
  Frédéric**.

**Ce qui n'est PAS éprouvé :** les temps réels en production. La maquette répond en 1,5 s fixes ; la production en
0,5 à 1,6 s selon l'écran (§2).

### 23.8 Le voile « Chargement… » du bureau : ne le montrer que sur une liste vide — AUDIT DU 27/10 (rien codé)

**Demande de Frédéric (27/10)** : « Audite le voile du bureau : ne le montrer que quand la liste est vide, explique-moi avant de
coder. »

⚠ **Mise en ligne du 7c : PAS ENCORE.** `origin/main` est à `e453f13`. La branche locale a 2 commits d'avance :
`299087a` (7c) et `df4b5be` (l'autre session). Le bundle de production est toujours `index-CA0qO0uU.js`.

**Le voile — ce que montre le code :**
- **Un seul endroit le pose** : `MandatsScreen` (`App.tsx` ~26474-26475), c'est-à-dire le tableau du **bureau** pour
  Annonces **et** Estimations.
  - Dès que `props.loading` est vrai, il ajoute la carte `listing-loading-banner` (le symbole animé « Chargement… ») et
    la classe `is-refreshing` (hauteur mini de 260 px).
  - Avec bienvu, `bienvu.css:284` en fait un **voile** : `position: absolute; inset: 0`, blanc à 72 %, au-dessus des
    lignes, qui **ne sont plus cliquables**.
- **Ce qui existe déjà à côté, et resterait :**
  - un « Mise a jour... » discret dans l'en-tête de la liste (~26443), à côté du compteur ;
  - l'état « éteint » des lignes pendant une relecture (`is-refreshing-row`, opacité 0,46 : `styles.css:4996`, depuis mai).
- **Les autres listes n'ont pas ce voile :**
  - le registre (Mandats) n'a que « Mise a jour... » ;
  - les contacts posent le symbole **au-dessus** des lignes, qui restent cliquables (`av-loading`, ~46052) ;
  - le téléphone n'a « Chargement… » que sur une liste vide.

**⭐ C'est une décision écrite de Frédéric.** Lot 5 bienvu, 19/10 :
- La première version (`044b8e6`) gardait les lignes « lisibles, un peu éteintes, jamais effacées » avec une barre fine
  et un squelette.
- Il l'a refusée : « c'est moche, je pensais un logo qui tourne comme la connexion jusqu'au chargement des résultats ».
  D'où `b66b58b`, le voile au symbole.
- La demande d'aujourd'hui la **restreint** :
  - le symbole reste pour **toute vraie attente** : premier chargement, écran pas encore vu (le 7c vide la liste), filtre
    qui ne rend rien ;
  - il disparaît quand des lignes sont déjà là.

**Ce que je ferais** — interrupteur `VOILE_SI_LISTE_VIDE`, une seule condition à ~26474-26475 :
- le voile et `is-refreshing` ne s'affichent que si la liste **affichée** (`visibleMandats`) est **vide** ;
- quand des lignes sont là, elles restent **cliquables**, éteintes comme avant le 19/10, sous le « Mise a jour... » de
  l'en-tête ;
- **seulement avec bienvu** : sans bienvu (barre fine collante, qui ne cache rien), rien ne change.

**Ce que ça pourrait casser ailleurs :**
- **La décision du 19/10** : elle est restreinte, pas défaite. Le symbole tourne toujours tant qu'il n'y a **rien** à
  montrer.
- **Changer de page** : pendant la relecture (0,5 s), l'en-tête dit déjà « Page 2 » alors que les lignes **éteintes**
  sont encore celles de la page 1. Aujourd'hui le voile les cache.
  - Un clic à ce moment ouvre le bien cliqué, par son numéro, donc le bon bien.
  - C'est déjà le cas du registre et du téléphone.
- **Frappe dans la recherche** : les lignes de la recherche précédente restent éteintes jusqu'à la réponse, comme au
  registre.
- **Un bien rappelé par la mémoire du 7c**, vendu ou archivé depuis, reste visible **éteint** pendant la relecture. C'est
  l'extinction qui le signale, d'où la proposition de la **garder**.
- **Le 7a (Échap)** cherche les fenêtres par `[class*="overlay"]`, `[class*="backdrop"]`, etc. `listing-loading-banner`
  n'en fait pas partie : le voile n'a jamais bloqué Échap. Aucun changement.
- **Les contacts** (symbole au-dessus des lignes, qui restent cliquables) ne sont **pas** touchés.

**Retour arrière** : `VOILE_SI_LISTE_VIDE = false`, en une ligne.

**Contrôle prévu** — maquette ralentie, sur bureau :
- retour sur Annonces (lignes en mémoire) : pas de voile, lignes éteintes et **cliquables**, « Mise a jour... » visible ;
- première visite et Estimations vide : le symbole ;
- changement de page et frappe ;
- le témoin inverse ;
- `npm run build` ;
- la vraie app déconnectée.
