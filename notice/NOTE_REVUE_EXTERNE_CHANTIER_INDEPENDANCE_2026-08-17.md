# Revue externe du chantier « indépendance Hektor » — découvertes et corrections

**Date : 2026-08-17. Revue faite depuis une session tierce, sur le code réel + git + la session « Calque optimiste contact V2 » (880 messages).**
**Complète (ne remplace pas) `AUDIT_GLOBAL_ET_METHODE_INDEPENDANCE_2026-08-08.md`.**
**Règle respectée : aucun code écrit, aucun fichier du projet modifié.**

---

## Résumé

Le chantier est bien mené et la méthode Strangler Fig est le bon choix. Cette note ne conteste rien
de fond : elle apporte **4 découvertes nouvelles** (B, D, E, I), **2 précisions qui changent la mise en
œuvre** (C, G) et **1 point de code résiduel** (A).

| # | Découverte | Nature | Urgence |
|---|---|---|---|
| A | Asymétrie résiduelle sur le chemin `annonceContact` | code | faible |
| B | Le doc d'audit n'est ni versionné ni sauvegardé | process | **haute** |
| C | Le « dirty-skip » recouvre **deux** mécanismes distincts | précision 1b | haute |
| D | `delete_searches_except_dirty` = la machine à orphelins | technique | **haute** |
| E | Le lot 2×/jour retarde la diffusion portails de 12 h | métier | haute |
| F | L'import entrant est un artefact de transition | cadrage | — |
| G | L'ordre « arrêter read-through + calque avant la Phase A » est risqué | correction | haute |
| H | Le surrogate contact (0d) rend la moitié de 2b gratuite | optimisation | — |
| I | Les « points en attente » sont **4**, pas 3 (photos) | cadrage | moyenne |
| J | Les seuils de monitoring doivent suivre le rythme 2×/jour | exploitation | moyenne |

---

## A. Correctif contact V2 — une asymétrie est restée

Le correctif `310ee99` est en place et correct : `App.tsx:12350` dépend bien de `dataReloadKey`.

**Mais l'audit de généralisation a conclu « `annonceContact` était le seul vrai cas » et a fermé le
sujet, alors qu'il reste une seconde asymétrie sur ce même chemin.**

- Source « listing » : un effet de reset (`App.tsx:12356-12359`) vide relations et recherches **au
  changement de contact**, précisément pour éviter la « recherche fantôme » (les recherches du
  contact précédent affichées pendant le chargement du suivant). Le commentaire du code le dit.
- Source « annonce » : **aucun équivalent.** `setAnnonceContactRelations` / `setAnnonceContactSearches`
  ne sont vidés que si l'`id` est vide (`App.tsx:12339`).

**Exposition réelle** : limitée. Fermer la fiche remet `annonceContactId` à `null`, ce qui déclenche
le reset. Le défaut ne se manifeste que sur un passage **direct** du contact A au contact B sans
fermeture intermédiaire — chemin que je n'ai pas pu confirmer comme atteignable dans l'UI actuelle.

**Conclusion** : ce n'est pas un bug avéré, c'est une asymétrie de traitement entre deux sources qui
doivent rester jumelles. Le même oubli de retrofit que celui qui a causé le bug d'origine.

---

## B. ⚠️ Le document d'audit n'est ni versionné ni sauvegardé

`.git/info/exclude:35` contient le motif `AUDIT_*.md`.

Conséquence : `notice/AUDIT_GLOBAL_ET_METHODE_INDEPENDANCE_2026-08-08.md` (16 Ko, la synthèse de tout
le chantier) est **non suivi par git ET exclu**. Il n'existe que sur le disque du serveur — celui-là
même dont le §5bis démontre qu'il n'a aucune sauvegarde automatique.

Autres constats git : 17 notes de `notice/` non suivies, **92 entrées** au total dans le working tree
du dépôt (scripts de debug, notes, maquettes).

**Recommandation** : ajouter une exception (`!notice/AUDIT_*.md`) ou renommer le fichier en `NOTE_*`,
puis le commiter. Coût : deux minutes. Sans ça, un incident disque efface 700 messages de raisonnement
en même temps que la base qu'ils décrivent.

*(La présente note est volontairement préfixée `NOTE_` pour échapper au motif d'exclusion.)*

---

## C. Précision sur 1b : le « dirty-skip » recouvre DEUX mécanismes

L'audit dit « le mécanisme existe déjà pour naissance/matrimonial, on l'étend, on ne casse rien ».
C'est exact, mais imprécis : il y a **deux** protections dans
[`push_contacts_to_supabase.py`](../phase2/sync/push_contacts_to_supabase.py), et elles n'ont pas du
tout la même portée.

**① Protection temporaire, par ligne** — `fetch_dirty_contact_ids`, `fetch_dirty_search_pairs`
Protège une ligne **pendant que l'édition fait son aller-retour** vers Hektor. Dès que le pending est
consommé, la protection tombe et Hektor redevient maître.
Le code est explicite (l. 446-449) : un pending **en conflit** est *exclu* du dirty pour que le
read-through rafraîchisse — commentaire d'origine : *« Hektor gagne »*.

**② Protection permanente, par champ** — `fetch_app_owned_contact_fields`
Ne couvre que **naissance / lieu de naissance / situation matrimoniale**. Hektor ne les renvoie
jamais ; le pipeline relit la valeur Supabase et la **réinjecte**. C'est une vraie propriété.

**Donc 1b se formule précisément ainsi** : *faire passer les champs du contrat d'autorité (0c) du
mécanisme ① au mécanisme ②.* Aujourd'hui le prix, la surface, le DPE, l'adresse sont en ①, c'est-à-dire
protégés le temps du trajet puis relâchés — la valeur fait toujours l'aller-retour par Hektor.

C'est aussi la ligne 446-449 qu'il faudra retirer : c'est l'autorité de Hektor rendue explicite.

---

## D. ⚠️ `delete_searches_except_dirty` : le mécanisme qui fabrique les orphelins

Le §5ter attribue l'instabilité de `contact_search_key` au fait que « modifier une recherche change
son hash ». C'est vrai mais incomplet, et l'ampleur réelle est plus grande.

`delete_searches_except_dirty` **supprime toutes les recherches d'un contact puis les réinsère à
chaque passage**, sauf celles marquées dirty. Combiné à une clé dérivée du contenu
(`build_contacts_layer.py:826`) et à un `search_index` positionnel, chaque cycle delete+réinsert peut
reforger des clés différentes — pas seulement lors d'une édition.

**Trois conséquences pour le plan :**

1. **1b est insuffisant sans 0b.** Protéger les champs ne sert à rien si la ligne entière est
   supprimée puis recréée sous une autre clé primaire.
2. Le motif delete-puis-réinsert est exactement celui du bug de fenêtre déjà rencontré côté
   read-through. Il est ici **systématique et nocturne**.
3. La correction de 0b doit viser le **mécanisme de reconstruction**, pas seulement la fonction de
   hachage : tant qu'on reconstruit par delete+insert, toute clé dérivée du contenu se retrouvera
   instable.

---

## E. ⚠️ Conséquence métier non traitée : le lot 2×/jour retarde la diffusion

Point absent de l'audit. Tant que la diffusion portails passe par Hektor (prise 3, remplacée en
Phase 5 seulement), regrouper le sortant en deux passages quotidiens signifie qu'une **baisse de prix
ou un changement de statut met jusqu'à 12 h à atteindre LeBonCoin / SeLoger**.

C'est acceptable pour la plupart des champs. Ça ne l'est pas pour le prix, le statut et les photos —
ce sont précisément ceux qu'un négociateur annonce à son client comme immédiats.

**Trois options** : (a) garder prix / statut / photos en push immédiat hors du lot, (b) accepter le
délai, (c) accélérer la prise diffusion. **(a) est recommandée** : coût faible, et elle supprime le
seul irritant visible de la Phase 3 — celle où les négociateurs jugent l'app.

---

## F. Cadrage : l'import entrant est un artefact de transition

Pendant la cohabitation il y a **deux** flux 2×/jour, et ils ne doivent pas avoir la même autorité :

| Sens | Rôle | Durée de vie |
|---|---|---|
| App → Hektor | la « migration globale » annoncée aux négociateurs | jusqu'à la coupure |
| Hektor → App | l'import tiers, **parce que les négociateurs y saisissent encore** | s'éteint quand ils basculent |

L'import entrant n'est pas une brique permanente de l'architecture cible : il se vide de lui-même à
mesure que les portefeuilles basculent, jusqu'à ne plus contenir que les retours des 4 points en
attente. **C'est le test d'autonomie réelle** : tant qu'un gros import quotidien reste nécessaire,
c'est que Hektor produit encore de la donnée.

---

## G. Correction d'ordre : ne pas arrêter le read-through avant la bascule

Instruction donnée en session : *« avant la Phase A il faut arrêter les workers calque optimiste et
read-through »*. L'intention est juste, l'ordre est risqué.

- **Le read-through ne doit pas être arrêté, mais rétrogradé.** Il fait deux choses : rafraîchir
  (utile tant que les négociateurs sont dans Hektor) et **faire autorité** (reconstruire, écraser).
  C'est l'autorité qu'il faut retirer, pas la fonction. Un flux tiers a le droit de **remplir**,
  jamais d'écraser ce que l'app possède.
- **Le calque optimiste ne se retire pas avant — il tombe après, tout seul.** Overlay, `base_snapshot`
  et gestion de conflit n'existent que pour survivre à un read-through qui pouvait écraser. Une fois
  l'autorité retirée, cette machinerie devient du poids mort. C'est un **nettoyage**, pas un préalable.

**Ordre sûr** : rétrograder le read-through → simplifier le calque (réactivité) → basculer les
négociateurs → allumer le lot 2×/jour.

Argument supplémentaire pour faire la réactivité **avant** la bascule : l'app doit être à son meilleur
le jour où on la présente. Une app instantanée emporte l'adhésion ; une app qui attend la perd.

---

## H. Le surrogate contact (0d) rend la moitié de 2b gratuite

Si les contacts reçoivent un `app_contact_id` (option (b) déjà envisagée en Phase 0), un contact créé
dans l'app **possède une identité définitive dès la première seconde**. Plus besoin de jeton
provisoire ni de réconciliation pour `create_hektor_contact` / `create_hektor_mandant_contact` :
l'ID Hektor devient une simple référence ajoutée plus tard.

Illustration de l'imbrication des phases : une décision d'identité en Phase 0 supprime du travail en
Phase 2. Argument de poids pour trancher (b) plutôt que (a).

**Rappel de périmètre pour 2b** — restent à rendre optimistes ([`console_job_worker.js:28`](../Console/console_job_worker.js:28)) :
`create_hektor_contact`, `create_hektor_mandant_contact`, `add_hektor_contact_search`,
`link_hektor_mandant`, plus le cycle de vie `change_hektor_annonce_status`, `archive_hektor_annonce`,
`restore_hektor_annonce`, `assign_hektor_annonce_negotiator`. Seul
`create_hektor_draft_annonce` est déjà couvert (`app_annonce_provisional`).

Noter aussi que 2b est un **échafaudage temporaire** : après la coupure, l'app minte les identités et
le mécanisme provisoire perd sa raison d'être. À construire à peu de frais, en réutilisant le patron
existant et son balayage automatique — pas en réinventant une mécanique par entité.

---

## I. Les « points en attente » sont quatre, pas trois

Le récit habituel cite trois prises : numéro de mandat, signature, diffusion. **Les photos sont la
quatrième**, et c'est la seule dépendance *binaire*.

`app_console_photo` ne stocke que des **URLs du CDN Hektor** (`url_preview` / `url_hd`,
`source: "hektor_console"`). Aucun fichier n'est rapatrié — contrairement aux documents, qui sont bien
écrits en premier dans `C:\Hektor\HektorConsoleDocuments`.

Tant que ce n'est pas fait, l'autonomie est **cosmétique** : Hektor s'éteint, les annonces s'affichent
sans images. La Phase 4 n'est pas une phase de confort, c'est un prérequis de la coupure.

---

## J. Exploitation : adapter les seuils de monitoring au rythme 2×/jour

Un worker qui ne tourne plus que deux fois par jour déclenchera les alertes de fraîcheur calibrées
sur un rythme continu. Le cas s'est déjà produit en session (*« Worker sans succès depuis 2846 min,
seuil 1680 »*), et le commit `dcbf82f` a adapté un seuil de cron pour cette raison.

À traiter **en même temps** que l'allumage du lot, pas après : sinon les premières semaines de la
Phase 3 — celles où la confiance se construit — seront noyées sous les fausses alertes.

---

## Priorités suggérées

1. **B** — sortir le doc d'audit de l'exclusion et le commiter (deux minutes, protège tout le reste).
2. **0a** — sauvegarder le mapping d'identité (~200 Ko/nuit), indépendant de toute décision.
3. **D + 0b** — corriger la clé des recherches **et** le mécanisme de reconstruction, ensemble.
4. **C + 0c** — écrire le contrat d'autorité, puis migrer ses champs du mécanisme ① au ②.
5. **E** — trancher le sort du prix / statut / photos dans le lot 2×/jour, avant la bascule.
