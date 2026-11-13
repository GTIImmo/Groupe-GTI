# Étape 3 — l'assistant qui agit : audit (13/11/2026)

> Plan : `notice/PLAN_DEV_ACCUEIL_ASSISTANT_IA_2026-10-29.md`, étape 3. Cadrage d'origine : `notice/SPEC_ETAPE0_ASSISTANT_IA_2026-10-29.md` §4, §5, §5 bis (le catalogue des écritures et les vagues A, B, C, validées le 29/10 : « Oui, il me va »).
> Ouvert sur « ENCHAÎNE » de Frédéric le 13/11, après le report du témoin commercial (« AUCUN ON FERA PLUS TARD »).
> ⚠ Audit **sans rien écrire** : ni code, ni base, ni Hektor.

## 1. Le verdict

L'assistant sait lire (étape 2). Pour qu'il **agisse**, il manque une seule pièce de fond : **la carte de validation**. Tout le reste existe déjà : les gestes sont ceux de l'écran (mêmes fonctions de la base, appelées avec le jeton de la personne), l'e-mail et l'agenda ont leurs routes et leurs gardes.

Le principe, décidé le 29/10 et inchangé : **le modèle ne fait jamais rien lui-même.** Il PROPOSE une action ; notre serveur la garde de côté ; la personne voit une carte (« Créer une relance jeudi 10 h pour M. X — Valider / Annuler ») ; **au clic**, notre serveur exécute la même fonction que l'écran, avec le jeton de la personne. Un refus ou une carte ignorée = rien n'est écrit.

## 2. Les mesures

**Les fonctions d'écriture de l'écran** (base, mesuré le 13/11) : 22 relevées pour les vagues A et B. Toutes fermées aux non-connectés.
- **16 contrôlent l'appelant** : contacts (créer, modifier, archiver, supprimer), recherches (créer, modifier, supprimer), notes et conditions de transaction, mandants (créer, rattacher, détacher), annonce (modifier, statut), mandat (clôture, numéro automatique).
- ⚠ **6 ne contrôlent TOUJOURS PAS l'appelant** (déjà relevées le 29/10 ; Frédéric : « Non, plus tard » pour les corriger pour tout le monde) :
  `app_create_relance_for_contact`, `app_relance_set_status` (les relances), `app_set_bien_statut`, `app_record_proposition` (bien ↔ recherche, proposition), `app_update_mandant_contact_optimistic`, `app_create_annonce_job_optimistic`.
  → Règle du 29/10 pour l'agent : **le serveur vérifie d'abord le droit** par une lecture avec le jeton (le contact, la relance, le bien sont-ils lisibles par la personne ?), puis appelle la fonction. Et `p_negociateur_email` / `p_nego` sont posés PAR LE SERVEUR (l'e-mail de la personne), jamais par le modèle.

**E-mail** : route `POST /google-workspace/gmail/send` (déjà utilisée par l'écran), garde `assert_gmail_subject_allowed` (un commercial n'envoie que depuis sa propre adresse). ⚠ L'envoi à blanc est le défaut (`dryRun`) ; l'interrupteur `EMAIL_REAL_SEND_ENABLED` existe (`settings.py:141`) — **sa valeur sur Render n'est pas mesurée** (je ne lis pas la configuration de Render).
Décision du 29/10 : envoi réel **en interne d'abord** (« Oui, en interne ») → il faut une garde « destinataires @gti-immobilier.fr seulement » pendant les essais.

**Agenda** : routes `POST | PATCH | DELETE /google-workspace/calendar/events`, garde `assert_calendar_subject_allowed`, rattachement métier existant.

**Bon de visite** : ⚠ il n'existe QU'À L'ÉCRAN (HTML construit dans le navigateur). Pas de PDF côté serveur. Chemin proposé le 29/10 : un travail du worker comme le document de mandat (Playwright). C'est le morceau le plus lourd de la vague A.

**Le journal** : `app_agent_run.status` accepte déjà `proposed / accepted / rejected / error` — le cycle d'une carte. Mais il ne doit garder **aucun texte** (règle de l'étape 1) : la charge de l'action (destinataire, texte d'un e-mail…) ne peut pas y vivre. → il faut **une table des actions proposées** (qui, quel geste, quels paramètres, état, expiration), lisible par la personne seule (+ admin). C'est une écriture de base : accord nécessaire.

**L'écran** : l'étape 4 (l'écran façon ChatGPT) n'est pas faite. Sans elle, une carte ne peut être validée que par l'API — c'est ainsi que je prouverais l'étape 3 (comme les 30 questions de l'étape 2).

## 3. Le tableau objets × gestes (étape 3 : la colonne « faire », vague A)

| | créer | modifier | supprimer / archiver | statut |
|---|---|---|---|---|
| relance | ⚠ fonction sans contrôle | — | — | ⚠ fait / reporté : fonction sans contrôle |
| recherche | ✅ contrôle | ✅ | ✅ (supprimer) | — |
| contact | ✅ | ✅ | ✅ archiver ; supprimer = manager/admin | — |
| bien ↔ recherche | ⚠ proposition sans contrôle | — | — | ⚠ visite / écarté : sans contrôle |
| note de transaction | ✅ | — | — | — |
| rendez-vous | ✅ route + garde | ✅ | ✅ | — |
| e-mail | ✅ route + garde (à blanc par défaut) | — | — | — |
| bon de visite | ⚠ PDF serveur à construire | — | — | — |

Vague B (annonce, mandants, mandat et avenant, signature, demandes, Matterport, cadastre, estimation) et vague C (statuts, transactions, archivage, suppression — manager/admin) : **non mesurées en détail ici**, catalogue du 29/10 (spec §5, §5 bis).

## 4. Ce que je propose

Avancer **par petits lots**, chacun prouvé en réel avant le suivant :
1. **Lot 1 — le mécanisme de la carte** + un seul geste simple : **les relances** (créer, faite, reportée). La table des actions proposées (base, avec inverse et répétition), la fonction « proposer », les routes « valider » et « refuser », le journal. Le droit vérifié par le serveur (les relances ont une fonction sans contrôle).
2. **Lot 2** — recherches, contacts, notes de transaction (fonctions qui contrôlent déjà).
3. **Lot 3** — rendez-vous et e-mails, **destinataires internes seulement** pendant les essais.
4. **Lot 4** — le bon de visite en PDF (worker).
5. Puis vague B, puis C.

**Ce que ça touche** : le backend (nouveaux fichiers, comme aux étapes 1-2), une table neuve en base. Rien dans Hektor tant qu'un geste ne passe pas par le worker (les relances n'y vont pas ; contacts et recherches, si).
**Retour arrière** : l'interrupteur de l'assistant, et l'inverse de la table.
**Ce que ça pourrait casser ailleurs** : rien de l'écran (mêmes fonctions, appelées comme lui) ; le risque est un geste exécuté sans que la personne l'ait voulu → c'est exactement ce que la carte empêche (exécution seulement au clic, une fois, avant expiration, par la personne qui l'a demandée).

## 5. Les questions pour Frédéric

1. **L'ordre** : lot 1 = le mécanisme de la carte + les relances, d'accord ?
2. **L'écran** : on prouve les cartes par l'API (comme les 30 questions), et l'écran vient à l'étape 4 ; ou on fait l'écran juste après le lot 1, pour que tu cliques toi-même ?

## 6. Lot 1 codé le 13/11 (« Oui enchaîne »), en local, rien en ligne

**Le périmètre** (catalogue complet, §5, validé par « Oui enchaîne ») : la carte de validation + les demandes à la direction + les relances.

**La base** — `supabase/patch_assistant_ia_etape3_cartes_2026-11-13.sql` (+ `_INVERSE`, `_REPETITION`) : la table `app_assistant_action` (une carte : qui, quel geste, paramètres, résumé, état, résultat, expiration à 30 min). Écrite par le serveur seul ; lue par la personne et par l'admin (même règle que les conversations). **Répétition jouée à blanc : 8 OK, 0 KO** (dont « deux clics : une seule exécution »), rien laissé en base. ⏳ **Pas posée** : accord nécessaire.

**Le code** :
- `assistant_gestes.py` (neuf) : 3 gestes, chacun en deux temps — **préparer** (vérifie, résume, range la carte) et **exécuter** (au clic seulement, re-vérifié, avec le jeton).
  - `demande_direction` : diffusion, baisse_prix, annulation_mandat — les conditions de l'écran (numéro de mandat ; validation = oui pour la baisse et l'annulation ; pas encore validé pour la diffusion ; une seule demande en cours par type ; prix normalisé), le **même texte** que l'écran, la demande + son événement « envoyée », écrits avec le jeton (la règle d'écriture de la base s'applique).
  - `creer_relance`, `statut_relance` (fait, reporté de 3 jours) : contact ou relance relus avec le jeton AVANT d'appeler les fonctions sans contrôle ; l'e-mail du négociateur posé par le serveur ; l'état relu après l'écriture.
- Le modèle n'a que des fonctions `proposer_…` : **aucune** ne fait un geste. Chaque carte part dans le flux (`{"type": "carte", id, geste, resume}`).
- Routes : `POST /assistant/actions/{id}/valider`, `POST /assistant/actions/{id}/refuser`, `GET /assistant/conversations/{id}/actions`. Le clic : la carte doit être à la personne (même l'admin ne valide pas à la place d'un autre), le geste ouvert à son rôle, encore « proposée » et pas expirée — une mise à jour conditionnelle, donc **un seul clic passe**.
- Consignes : la section « Agir » (ne jamais dire que c'est fait, une carte par geste, vérifier d'abord).
- `relances` et `demandes` gagnent leur colonne `id` (pour viser une relance ou une demande).
- Essais : **36 nouveaux verts** (`test_assistant_gestes.py`), et 59 + 71 + GED 28 + 80 toujours verts.

**⚠ Trouvé en passant (NON traité)** : un négociateur **ne peut pas corriger** une demande renvoyée, même à l'écran. La règle d'écriture de `app_diffusion_request` réserve la mise à jour à la direction (`is_app_manager_or_admin`) ; l'écran envoie la correction sans vérifier qu'une ligne a bougé. Le bouton « Corriger » d'un commercial ne fait donc probablement rien (à confirmer par un essai réel). « Corriger » n'est pas offert à l'assistant.

**Pour mettre en service** (chaque geste avec son accord) : poser le patch, pousser le code, puis prouver en réel : une relance créée puis marquée faite sur un contact d'essai ; une demande de baisse de prix sur un bien d'essai (62774 ou celui qu'il choisit), que Pauline / lui pourra refuser ensuite.

**✅ POSÉ ET EN LIGNE le 13/11** (son « Vas y ») :
- Table posée à ~11:14 : « PATCH PASSÉ » ; contrôlée à part : vide, 1 règle de lecture, l'écran lit mais n'écrit pas, la clé publique ne lit rien, le serveur écrit.
- Code en ligne à 11:16 (`7dcb6d4`, `/health` le rend) ; les 4 routes répondent 401 sans jeton.
- Contrôle en réel (lecture seule) : « Quelles relances sont en retard ? » → les 3 relances de franck…, exact ; **0 carte proposée** (aucun geste demandé) — l'assistant ne propose pas de lui-même un geste qu'on ne lui demande pas.
- ⏳ **Pas encore éprouvé** : une carte proposée puis validée en réel. Il faut une cible choisie par Frédéric (un contact d'essai pour une relance ; un bien VIVANT, mandat validé, pour une demande — le 62774 est clos).

