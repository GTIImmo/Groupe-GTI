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

**✅ PREMIÈRE CARTE PROUVÉE EN RÉEL le 13/11 à 11:19-11:20** (son « Vas y », contact d'essai M. AVOIR TEST4, n° 10354488, sa session Chrome) :
1. « Crée une relance pour M. AVOIR TEST4… pour le 20 novembre » → **une carte** (« Créer une relance pour M. AVOIR TEST4 le 20/11/2026 : … ») et l'assistant dit « j'ai préparé la carte, valide-la » — pas « c'est fait ». **Vérifié en base AVANT le clic : aucune relance créée**, la carte « proposée ».
2. **Clic « Valider »** → relance **n° 20** créée (à faire, 20/11, attribuée à frederic.gerphagnon@ — l'e-mail posé par le serveur). **Second clic → 409 « Cette carte a déjà été validée »**, rien refait.
3. « Reporte la relance 20 » → carte → **« Annuler »** → carte refusée ; un clic « Valider » ensuite → 409 « Cette carte a été refusée ». **La relance n'a pas bougé** (toujours à faire au 20/11).
4. « Marque la relance 20 comme faite » → carte → **« Valider »** → relance 20 **faite** (relue après l'écriture).
5. Le journal des cartes : 3 lignes — exécutée, refusée, exécutée — avec qui, quoi, les heures de proposition, de décision et d'exécution.
⚠ La relance n° 20 reste en base (faite) sur le contact d'essai : c'est la trace de l'essai.
⏳ Pas encore éprouvé en réel : une demande à la direction (il faut un bien vivant à mandat validé, choisi par lui).

## 7. Audit du lot 2 (13/11, sur « Lot2 ») — rien codé

**Le périmètre** (catalogue §5) : rapprochements, recherches, contacts, notes, notifications.

**Mesuré en base** : propositions de biens **15 en tout** (4 en 90 jours ; e-mail 13, visite 1, rdv 1) ; statuts bien ↔ acquéreur : proposé 11, écarté 2 ; notes de transaction 9 ; notifications lues en 30 jours : 36 (2 101 non lues). → des gestes qui existent mais servent peu : l'assistant peut les rendre faciles.

**Les écritures de l'écran, lues** :
- **Proposer un bien à un acquéreur** : `app_record_proposition(recherche, bien, canal, note, nego…)` — ⚠ SANS contrôle de l'appelant. Elle écrit la proposition, le statut bien ↔ acquéreur (« proposé », ou « visite » pour les canaux visite / virtuelle) ET pose une relance de suivi s'il n'y en a pas déjà une.
- **Écarter / rétablir un bien pour une recherche** : `app_set_bien_statut(recherche, bien, statut, motif, nego)` — ⚠ SANS contrôle. Statuts : jamais_vu (efface), propose, visite, ecarte, offre.
- **Marquer une notification lue** : `app_mark_notification_read(id)` — ⚠ SANS contrôle : n'importe qui peut marquer lue celle d'un autre.
- **Note de transaction** : `app_affaire_note_ecrire(affaire, texte)` — contrôle l'appelant ; à l'écran, par la modale des transactions (direction).
- **Modifier un contact** : `app_edit_contact_optimistic(contact, champs, délai)` — contrôle l'appelant (`forbidden_update_contact`), accepte une modification PARTIELLE (seuls les champs donnés), écrit chez nous tout de suite, puis Hektor après le délai (travail `update_hektor_contact`). L'écran envoie toujours le formulaire complet. ⚠ La correction du téléphone qui s'AJOUTAIT chez Hektor est réglée depuis le 05/11 (interrupteur `contact_coordonnees_remplacer`).
- **Archiver / réactiver un contact** : `app_console_archiver_contact_optimistic` — contrôle, phrase de refus en français ; archive aussi ses recherches.
- **Archiver une recherche** (« supprimer » à l'écran) : `app_console_create_delete_contact_search_job` — contrôle.
- **Créer un contact**, **créer / modifier une recherche** : formulaires longs (identité complète, doublons ; critères, villes, types, budgets) — à part.
- **E-mail de rapprochement** : route `/emails/rapprochement/send`, à blanc par défaut — c'est un e-mail : il va avec le lot 3.

**Ce que je propose** :
- **2a — chez nous seulement** (aucun envoi à Hektor) : proposer un bien à un acquéreur (téléphone, visite, rendez-vous, e-mail déjà envoyé), écarter / rétablir un bien, marquer MES notifications lues (une, ou toutes celles d'un type), écrire une note de transaction (direction). Pour les 3 fonctions sans contrôle : la recherche, le bien et la notification relus avec le jeton AVANT ; le négociateur posé par le serveur ; une notification ne se marque que si elle est à la personne.
- **2b — vers Hektor** : modifier les coordonnées d'un contact (téléphone, e-mail, adresse, commentaire), archiver / réactiver un contact, archiver une recherche. ⚠ L'écran envoie toujours le formulaire complet ; l'assistant n'enverrait QUE les champs changés (la fonction de la base l'accepte) — chemin jamais emprunté à l'écran : **essai réel sur un contact d'essai obligatoire** avant de l'ouvrir.
- **2c — plus tard** : créer un contact, créer / modifier une recherche (formulaires longs, à reprendre champ par champ).

## 8. Lot 2 codé le 13/11 (« Les deux » = 2a et 2b), en local, rien en ligne

**2a — chez nous seulement** :
- `bien_propose` : bien proposé PAR TÉLÉPHONE à une recherche (`app_record_proposition`, canal `telephone` seulement — l'e-mail et la visite s'enregistrent après leur envoi / leur rendez-vous, lot 3). Le bien passe « proposé » et une relance de suivi est posée (c'est la fonction de la base qui le fait).
- `statut_bien` : écarter (avec motif) ou rétablir (= « jamais vu », comme l'écran).
- `notifications_lues` : des numéros, un type, ou toutes — **seulement les siennes**, relues au clic (un numéro de collègue glissé dans la carte n'est pas marqué : témoin vert).
- `note_transaction` : **direction seulement** (comme l'écran ; double verrou) ; la carte montre l'ANCIENNE note, parce que la fonction de la base la REMPLACE.
- Les trois fonctions sans contrôle (proposition, statut, notification) : l'objet est relu avec le jeton avant, le négociateur posé par le serveur.

**2b — vers Hektor** :
- `modifier_contact` : téléphone, e-mail, commentaire — **seuls les champs qui changent partent** (la fonction de la base l'accepte ; l'écran, lui, envoie toujours la fiche entière : chemin à éprouver sur un contact d'essai). La carte montre avant → après. ⛔ Pas l'adresse ni la ville (identifiants de commune, leçon du 22/10).
- `archiver_contact` : archiver (prévient que ses recherches actives partent avec) ou réactiver (prévient que ses recherches ne reviennent pas).
- `archiver_recherche` : le rang de la recherche est relu au clic (le défaut « la 2e vise la 1re » est corrigé et éprouvé depuis le 29/10).

**Objets** : `notifications` gagne sa colonne `id`. **Consignes** : la liste des gestes ouverts, et ce qu'il ne peut pas encore faire.
**Essais** : `test_assistant_gestes.py` **60 verts** (dont les témoins inverses : notification d'un collègue, note invisible jamais lue avant sa transaction, commercial sans la note) ; 59 + 71 ; GED 28 + 80.

**Pour la preuve réelle (avec son accord)** : sur le contact d'essai M. AVOIR TEST4 — modifier son téléphone puis le remettre (vérifier chez Hektor qu'il REMPLACE et n'ajoute pas), archiver puis réactiver ; une recherche d'essai à archiver ; proposer / écarter un bien d'essai ; marquer une de ses notifications lue.

## 9. La preuve réelle du lot 2 (13/11, 12:15-12:43, son « Vas y »), contact d'essai M. AVOIR TEST4

**En ligne à 12:14** (`ec64384`). Tout passe par la conversation et les cartes, avec sa session.

**2a — chez nous, prouvé** :
- « Note que l'annonce 63330 a été proposée par téléphone à M. AVOIR TEST4… » → carte → validée : proposition enregistrée (téléphone, note « essai assistant », négociateur = Frédéric), le bien « proposé », et **la relance de suivi n° 21** posée par la base (à faire au 18/11).
- « Écarte l'annonce 63330, motif : essai terminé » → carte → validée : statut « écarté » avec son motif.
- « Marque comme lue ma notification 11370698 » → carte → validée : lue.

**2b — vers Hektor** :
- **Archiver la recherche** du contact d'essai → fait chez Hektor en 11 s, relu : cadenas ouvert → fermé.
- **Archiver puis réactiver la fiche** → les deux faits chez Hektor (10 s et 14 s), « Modification archivage ok ». ⚠ La carte d'archivage annonçait encore « 1 recherche active » alors qu'elle venait d'être archivée : le compteur de la fiche n'était pas encore relu (sans conséquence ici).
- ⛔ **Le téléphone a ÉCHOUÉ d'abord** : travail `update_hektor_contact` en erreur « Nom contact requis » (12:28, puis une 2e tentative automatique à 12:34). **Cause** : le worker exige le NOM à chaque modification (`normalizeHektorContactPayload`, `requireName`), même inchangé ; l'écran l'envoie toujours, l'assistant ne l'envoyait pas. C'était le risque noté à l'audit (« chemin jamais emprunté »). **Effets** : la fiche chez nous portait le nouveau numéro, pas Hektor ; 2 notifications d'échec (et leurs e-mails d'alerte admin).
- **Réparé à 12:42** avec sa session, par la fonction de l'écran : le nom ACTUEL (« TEST4 », inchangé) ajouté à la modification en attente (la base fusionne, remet le compteur à zéro). **Nouvel envoi à 12:43 : fait en 11 s**, « coordonnées remplacées ». **Relu depuis Hektor** : téléphone 06 00 00 00 01 seul (pas de 2e ligne), prénom, civilité, e-mail inchangés, plus rien en attente.
- **Corrigé dans le code (en local, `assistant_gestes.py`)** : chaque modification envoie aussi le nom actuel ; un contact sans nom → rien n'est lancé. Témoin ajouté : **61 essais verts**.

**Le correctif est en ligne** : `fa868f9` a été poussé par l'autre session avec ses propres commits (`05904b9`, 14:33). `/health` rendait `05904b9`, qui le contient.

**Remplacer un numéro existant — PROUVÉ le 13/11 (son « Vas y »)** :
- « Mets le téléphone 06 00 00 00 02 sur la fiche de M. AVOIR TEST4 (contact 10354488), à la place de l'actuel. » → carte « téléphone : « 06 00 00 00 01 » → « 06 00 00 00 02 » » → validée à 15:29:01. Retour : `champs = [last_name, phone]` (**le nom part bien**).
- Envoi en attente : `push_fields = {phone, last_name: TEST4}`, départ à +10 min.
- Travail `update_hektor_contact` 211ca381 : posé à 15:40:00, **fait en 18 s**, `status: updated`, `coordonnees: remplacees`, `telephone: 06 00 00 00 02`, `telephone_secondaire: null`.
- Relecture depuis Hektor (travail f0ae139c, `synced`, 15:40:41) : `phone_primary = 06 00 00 00 02`, `phone_secondary` vide, e-mail inchangé, rien en attente. **Remplacé, pas ajouté.**

➡ **Le lot 2 est prouvé en entier.** ⚠ Traces d'essai laissées sur le contact d'essai : relance n° 21 (à faire), recherche archivée, téléphone 06 00 00 00 02.

## 10. Audit du lot 3 (13/11, sur « Enchaine ») — rien codé

**Périmètre** (catalogue §5) : agenda et visites, espace client, e-mails, bon de visite. Lecture du code (écran, serveur, base) et mesure en base. ⚠ Audit limité à ces gestes ; les autres objets ne sont pas mesurés ici.

**Mesuré en base — des gestes qui dorment** :
- Rendez-vous créés par l'app : 16 en tout, **0 en 90 jours** (le dernier le 19/06). Suppressions 5, modification 1. 6 comptes Google reliés.
- Disponibilités lues (freebusy) : 21 en 90 jours.
- E-mail libre (Gmail) : 70 envois réels en tout, **2 en 90 jours** (le dernier le 12/10).
- E-mails de rapprochement / estimation (`app_email_envoi`) : 84, presque tous de juin-juillet ; le dernier le 12/10.
- Espace client : **3 demandes de visite** en tout (juin-juillet), **0 message**. Demandes de RDV publiques : 0.
- Propositions de biens : 16 (lot 2).

**Ce que fait l'écran, geste par geste** :
- **Rendez-vous** (créer / modifier / supprimer) : route du serveur `/google-workspace/calendar/events`. Le serveur écrit dans **Google Agenda** par délégation de domaine, puis garde le lien dans `app_google_calendar_event_link` (clé de service ; suppression douce). Garde côté serveur (`assert_calendar_subject_allowed`) : un commercial n'écrit que dans SON agenda ; admin et manager dans celui de n'importe qui. ⚠ L'écran envoie **toujours** `sendUpdates: all` : Google envoie **de vraies invitations** à tous les invités, acquéreurs compris, **sans aucun interrupteur**. Pas d'écriture chez Hektor.
- **Visite** : le RDV de visite, une fois créé, pose « visite » sur le bien pour la recherche (`app_set_bien_statut`) ; supprimer le RDV remet « jamais vu » (⚠ efface aussi un « proposé » d'avant).
- **Espace client** : la demande du client crée la ligne, une notification et deux e-mails. Le négociateur **confirme ou propose des créneaux sur une page à lien** (`/visite/{jeton}`, sans connexion, 21 jours), **pas dans l'app** ; confirmer crée le RDV Google avec le client invité. Pas d'annulation. Ces pages suivent l'interrupteur `EMAIL_REAL_SEND_ENABLED`.
- **E-mail libre** : route `/google-workspace/gmail/send`, depuis la boîte de la personne, modèles et jusqu'à 10 pièces jointes. ⚠ **Réel par défaut** (`dryRun = False`), **hors interrupteur, sans désinscription, sans plafond**.
- **E-mails de rapprochement et d'estimation** : routes `/emails/…/send`, à blanc par défaut ; réel seulement si `dry_run = false` **et** `EMAIL_REAL_SEND_ENABLED`, désinscription respectée, plafond du jour (80), journal `app_email_envoi`. L'estimation pose aussi un travail `generate_estimation_pdf` (archivé chez Hektor).
- **Bon de visite** : une page HTML construite à l'écran, imprimée par le navigateur. **Pas de PDF, rien n'est enregistré.**

**Trouvé en passant — défauts qui existent déjà, NON corrigés (à lui de dire)** :
1. Rapprochement et estimation : l'**expéditeur** (`sender_email`) vient du navigateur et **n'est pas contrôlé** — tout compte connecté peut envoyer « au nom » d'un autre négociateur (vérifié : `emails.py:218-230`).
2. Pièces jointes de l'e-mail libre : téléchargées depuis **n'importe quelle adresse** par le serveur, sans liste d'hôtes autorisés.
3. Supprimer un RDV de visite remet le bien à « jamais vu », même s'il avait été proposé avant.
⚠ Non mesuré : la valeur actuelle de `EMAIL_REAL_SEND_ENABLED` sur Render.

**Ce que je propose** :
- **3a — l'agenda, dans SON agenda, sans invitation extérieure** : lire son agenda (« qu'est-ce que j'ai jeudi ? », créneaux libres) ; créer / déplacer / supprimer un RDV relié à un bien et un contact, **invitations coupées** (`sendUpdates: none`) ; un RDV de visite pose « visite » comme l'écran. Jamais l'agenda d'un collègue.
- **3b — les e-mails, en interne d'abord** : un e-mail libre **seulement vers une adresse @gti-immobilier.fr** (le serveur refuse le reste) ; le rapprochement **à blanc seulement** (l'assistant montre le texte qui partirait, rien ne part).
- **3c — plus tard** : envoyer vers un client (invitation, e-mail, rapprochement réel), confirmer un créneau de l'espace client, et le bon de visite en PDF (à construire côté serveur).

## 11. Lot 3 codé le 13/11 (« A et b » = 3a et 3b), en local, rien en ligne

**3a — l'agenda Google DE LA PERSONNE, sans invitation** :
- `lire_mon_agenda` (lecture, sans carte) : tout son agenda Google entre deux dates (31 jours au plus) — heure, titre, lieu, nombre d'invités (et d'extérieurs), et `rdv_app` pour ceux posés par l'app. ⛔ Aucune adresse ne part au modèle (ni la sienne, ni celles des invités). Lecture ajoutée au service Google (`list_calendar_events`, portée `calendar.events` déjà accordée) ; ⚠ sans ligne au journal Google : sa contrainte ne connaît pas la lecture et le journal avale ses refus en silence.
- `creer_rdv` : dans SON agenda (garde de l'écran : compte Google relié), **aucun invité, aucune notification** (`sendUpdates: none`), relié à l'app comme à l'écran (bien, contact, recherche ; marqué « assistant ») ; une visite liée à une recherche met le bien « visite » (= l'écran). La carte signale un créneau déjà pris. Créneau passé ou date sans heure : refusé.
- `deplacer_rdv` / `supprimer_rdv` : seulement un RDV **posé par l'app**, **dans son agenda**, **sans aucun invité** (re-vérifié au clic : un invité ajouté depuis l'écran entre-temps → refusé). Sans notification.
- ⚠ **Choix à valider par lui** : supprimer un RDV de visite **ne remet pas** le bien à « jamais vu » (l'écran le fait, et efface ainsi un « proposé » d'avant : défaut n° 3) ; la carte le dit.

**3b — les e-mails EN INTERNE** :
- `email_interne` : depuis SA boîte (garde de l'écran), **seulement vers des adresses @gti-immobilier.fr** (vérifié à la carte ET au clic : une carte trafiquée vers l'extérieur est refusée au clic), sans pièce jointe, 10 destinataires et 3 000 caractères au plus — **la carte montre le texte en entier**.
- `apercu_rapprochement` (lecture, sans carte) : le texte de l'e-mail de rapprochement qui partirait ; **rien n'est envoyé ni enregistré**, chaque bien est lu avec le jeton, les adresses e-mail sont masquées.

**Au passage** :
- La date donnée à l'assistant porte le **jour de la semaine**, à l'heure de Paris (« vendredi 13/11/2026 ») : « jeudi », « demain » ne se devinent plus.
- ⛔ **Correctif de l'étape 2** : la lecture `agenda` envoyait au modèle l'adresse de l'agenda — donc parfois **celle de la personne**, contre la règle de l'étape 1. Remplacée par « le tien » (un collègue garde la sienne) ; chaque RDV porte aussi son `rdv_app`.

**Essais** : `test_assistant_gestes.py` **101 verts** (dont les témoins : agenda d'un collègue, RDV avec invités, invité ajouté avant le clic, faux domaine, carte trafiquée, aucune adresse vers le modèle) ; `test_assistant_ia.py` 59 ; `test_assistant_lecteur.py` 73 ; GED 28 + 80. L'application entière se charge.

**Pour la preuve réelle (avec son accord)** : dans SON agenda — créer un RDV d'essai, le déplacer, le supprimer ; un e-mail interne à lui-même ; un aperçu de rapprochement (contact d'essai AVOIR TEST4, annonce 63330).

## 12. La preuve réelle du lot 3 (13/11, 16:14-16:30, son « Oui, vas-y »)

**En ligne à 16:14** (`eab475d`). Conversation avec sa session ; écrit dans SON agenda Google.

- **Lire l'agenda** : « lundi prochain » → aucun RDV ; ⭐ témoin positif « du 2 au 13 novembre » → **12 RDV**, les vrais de son agenda (titres et heures justes).
- **Créer** : « ESSAI ASSISTANT - à supprimer », lundi 16/11 07:00-07:15 → carte juste ; **avant le clic, rien** (0 lien, 0 création au journal Google) ; validée → créé chez Google, journal `calendar.event.create` avec `send_updates: none` et **0 invité**, lien app `2f70c06f…` (source « assistant »).
- **Déplacer** à 07:30 → carte « 07:00 → 07:30–07:45, personne n'est prévenu » → validée → **relu depuis Google** : 07:30-07:45, aucun invité.
- **Supprimer** → validée → **relu depuis Google** : il n'y est plus ; **second clic refusé (409)**.
- **E-mail vers l'extérieur** (jean.dupont@gmail.com) : l'assistant refuse de lui-même, **aucune carte**.
- **Aperçu du rapprochement** (AVOIR TEST4, annonce 63330) : le texte rendu, adresses masquées, rien envoyé.

**Deux défauts trouvés par la preuve, corrigés en local (104 essais verts)** :
1. ⛔ **L'aperçu envoyait au modèle les LIENS de l'e-mail** (« Voir ce bien », « Affiner », « Se désinscrire ») : ils portent une **clé d'accès à l'espace du client** (`/espace/<jeton>`, sans connexion, ~1 an). Une fois, pour le contact d'essai 10354488 seulement. → les liens sont remplacés par « [lien] ».
2. **« Envoie-moi un e-mail » était impossible** sans écrire son adresse dans la question — donc chez OpenAI, contre la règle de l'étape 1. → destinataire « moi » : la carte dit « toi », l'adresse est posée par le serveur au clic.

**Correctifs en ligne à 16:28** (`e2f5861`, son « Oui, vas-y » ; seul ce commit poussé, celui de la GED au-dessus laissé à son auteur) :
- **Aperçu refait** sur AVOIR TEST4 / 63330 : « Voir ce bien », « Affinez », « Se désinscrire » → `[lien]` ; plus aucun `/espace/` dans ce que voit le modèle.
- **E-mail interne « à moi »** : carte « e-mail interne à toi » (son adresse n'apparaît pas) ; **avant le clic, 0 envoi** au journal Google ; validée → envoyé (journal `gmail.send` : réel, de sa boîte à sa boîte, domaine gti-immobilier.fr, 1 destinataire, 0 pièce jointe, `related_entity_type: assistant`, message Gmail `1a1d5878b108077b`). ⚠ La réception dans sa boîte n'est pas vue par moi (Gmail a accepté l'envoi).

➡ **Le lot 3 (3a + 3b) est prouvé en entier.** Restent hors de l'assistant (lot 3c) : tout envoi vers un client, l'espace client, le bon de visite en PDF. Les 3 défauts existants de l'écran (§10) restent à sa décision.
