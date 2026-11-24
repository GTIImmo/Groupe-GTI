# Recrutement — les e-mails dans l'app : audit de l'existant et proposition

> Demande de Frédéric (24/11/2026) : « fais un audit de mon app, qui pose déjà tous les accès Google, Gmail et
> agenda, et des fonctionnalités ; ensuite propose-moi une idée d'intégration dans l'app des e-mails envoyés, avec
> aperçu, modification, etc., tout ce qu'il y a de mieux ; et il faut pouvoir sélectionner plusieurs candidats dans
> le listing pour leur envoyer des e-mails en même temps ». **Audit en lecture seule, rien n'est codé.**
> Chantier : `notice/CHANTIER_RECRUTEMENT_ANNUAIRE_MANDATAIRES_2026-11-20.md` (R7.1 ; décision D5). Modèle de texte
> au fond validé : `notice/RECRUTEMENT_MODELE_EMAIL_PREMIER_CONTACT_2026-11-24.md`.

## 1. L'audit — ce que l'app sait DÉJÀ faire (lu dans le code le 24/11)

**L'accès Google** (`backend/app/services/google_workspace_service.py`) :
- une **clé de service Workspace à délégation complète** (aucun mot de passe) : le serveur agit AU NOM d'une boîte
  du domaine. Droits posés au départ : `gmail.send`, `calendar.freebusy`, `calendar.events`, `gmail.readonly` ;
  décrits mais pas posés d'office : `contacts.readonly`, `gmail.metadata` ;
- **la règle de l'expéditeur** (`supabase_admin.assert_gmail_subject_allowed`) : une adresse du domaine seulement ;
  admin et manager peuvent écrire depuis une boîte du domaine, un commercial seulement depuis la sienne (liée) ;
- **chaque geste est journalisé** dans `app_google_workspace_action_log`.

**Gmail** (`backend/app/routers/google_workspace.py`) :
- `POST /google-workspace/gmail/send` : destinataires, copie, copie cachée, objet, texte ET HTML, nom affiché,
  adresse de réponse, **jusqu'à 10 pièces jointes** (8 Mo chacune), mode « à blanc », et le lien à une fiche
  (`relatedEntityType` / `relatedEntityId`) ;
- les pièces « depuis l'ordinateur » : dépôt contrôlé par le serveur, lien de 15 min, ménage après 2 jours ;
- `GET /gmail/contact-messages`, `/gmail/message`, `/gmail/attachment` : **lire les échanges** avec une adresse
  (la carte « fil Gmail » d'un contact, `ContactEmailThreadCard`).

**L'agenda** : créer, modifier, supprimer un rendez-vous avec invitations (`/calendar/events`), lire les
disponibilités (`/calendar/availability`, freebusy), et le lien rendez-vous ↔ fiche (`google_calendar_event_link`).

**Les e-mails « métier » déjà faits** (`backend/app/routers/emails.py`, `services/rapprochement_email.py`,
`email_tracking.py`, `email_tokens.py`) :
- un **habillage HTML GTI** (en-tête, pied, boutons) et un **APERÇU** rendu sans envoi (`/emails/.../preview`) ;
- des **liens signés** publics : ouverture (`/r/o/…png`), avis, téléchargement, et **une page de désinscription**
  (`/r/u/{jeton}`), avec l'en-tête `List-Unsubscribe` et un **filtre des désinscrits AVANT chaque envoi** ;
- un suivi (ouvertures, clics) et un score chaud / tiède / froid ;
- la **prise de rendez-vous publique** (`/public/appointments`).

**Dans l'écran** (`App.tsx`) : `ContactEmailComposerModal` — modèles, expéditeur, copie, objet, texte, pièces
jointes (documents, photos, ordinateur) ; **texte brut, sans aperçu, une personne à la fois**. Utilisée par 3 écrans.

**Ce qui manque pour le recrutement** : aucun lien « candidat » côté Gmail ni agenda ; pas d'envoi groupé ; pas
d'aperçu dans la fenêtre ; l'écran Recrutement n'ouvre que la messagerie de l'utilisateur (`mailto:`).

## 2. La proposition — « Écrire » depuis le recrutement

**Principe** : on RÉUTILISE tout (la clé, l'envoi, le journal, l'habillage, les jetons signés, la page de
désinscription, l'agenda). Le neuf se limite à l'écran, aux modèles du recrutement et à un petit lien
« candidat » côté serveur.

**A. Écrire à UN candidat** (depuis sa fiche) — une fenêtre en trois temps : *Écrire · Aperçu · Envoyé*.
- **Modèle** au choix : Premier contact (le texte validé), Relance, Proposer un rendez-vous, Message libre. Les
  cases se remplissent seules depuis la fiche : prénom, agence la plus proche, **source exacte** et lien de sa fiche.
- **Modifiable** : objet et texte, avec les cases visibles ; un « réinitialiser le modèle ».
- **Le bloc d'information RGPD est AJOUTÉ SEUL** aux fiches collectées, et ne peut pas être retiré (il peut être
  replié à l'écran). Le lien « Ne plus me contacter » aussi.
- **Aperçu** exactement tel qu'elle le recevra (habillage GTI), en largeur bureau ou téléphone.
- **De** : la boîte de l'administrateur connecté (sa signature), ou une adresse « recrutement » si Frédéric en
  crée une. **Pièces jointes** : la plaquette GTI en un clic, ou un fichier.
- **Envoyer** : par la clé Workspace (rien ne part sans le clic). Puis, tout seul : le **fil** note l'e-mail (objet
  + extrait), l'étape passe à « Contactée », et la case **« informée »** se coche (l'e-mail portait l'information).

**B. Écrire à PLUSIEURS candidats** (depuis la liste) — les cases existent déjà.
- Une **barre d'action** apparaît : « 12 choisis — Écrire à 12 candidats ».
- **Un e-mail PAR personne** (jamais une liste de destinataires visible, jamais de copie cachée groupée) : chacun
  reçoit SON prénom, SA source, SON lien de désinscription.
- **Avant d'envoyer, l'écran dit qui sera écarté** et pourquoi : sans e-mail, sur la liste « ne plus contacter »,
  opposé à la prospection au registre (écarté d'office), déjà écrit il y a moins de 30 jours (à cocher).
- **Aperçu par destinataire** : flèches ‹ 3 / 12 ›, et la possibilité de retoucher UN message sans toucher aux autres.
- **Envoi en file douce** : un e-mail toutes les quelques secondes, **plafond par jour** (proposé : 40), barre
  d'avancement, résultat par personne (envoyé / refusé), et chaque fil mis à jour.

**C. Les réponses et la désinscription**
- **Désinscription** : la page publique existante `/r/u/…` (variante « recrutement ») → un clic « Ne plus me
  contacter » pose la personne sur la liste « ne plus contacter » (le même geste que « Retirer », `qui = elle-même`),
  et aucune collecte ne la remettra.
- **Réponses** : le serveur lit déjà les échanges avec une adresse (`gmail.readonly`) — la fiche affiche « a
  répondu le … » et le fil Gmail, comme pour un contact. **Pas de pixel d'ouverture** pour le recrutement
  (prospection : prudence CNIL ; la réponse est le seul vrai signal).

**C bis. Où se voient les échanges** (question de Frédéric, 24/11) — **dans la fiche du candidat**, bloc « Le fil des
échanges » (planche 4) :
- **ce qui est envoyé DEPUIS l'app** est gardé en base (objet, texte tel qu'envoyé, pièces, date, expéditeur) : « voir
  l'e-mail tel qu'envoyé », visible de tous les administrateurs, quel que soit celui qui a écrit ;
- **les réponses, et tout échange fait directement dans Gmail**, sont LUES EN DIRECT à l'ouverture de la fiche : le
  serveur cherche dans la boîte qui a écrit `from:/to:/cc:` l'adresse du candidat (les 20 à 25 derniers messages,
  la route `/gmail/contact-messages` qui sert déjà aux contacts). Rien de ces réponses n'est recopié en base :
  Gmail reste l'archive (minimisation) ;
- et bien sûr dans Gmail lui-même : « Envoyés » de l'expéditeur, et la réponse arrive dans sa boîte de réception.
- ✅ **DÉCIDÉ par Frédéric le 24/11 : TOUTES LES BOÎTES.** La fiche cherche l'adresse du candidat dans toutes les
  boîtes Gmail de l'équipe (les comptes actifs de l'app, du domaine), pour ne rien manquer si quelqu'un d'autre a
  échangé avec lui. Visible des administrateurs seuls (la rubrique l'est). Ce que ça demande, à tenir au code :
  - **une recherche par boîte** : faite en arrière-plan à l'ouverture de la fiche, gardée quelques minutes en mémoire
    (pas une salve d'appels Google à chaque clic), et chaque message dit **de quelle boîte** il vient ;
  - **seulement les messages échangés avec CETTE adresse** (`from:/to:/cc:`), jamais le reste d'une boîte ;
  - **l'équipe doit en être informée** : la lecture d'une boîte professionnelle par l'employeur se limite au
    professionnel et se dit (règle de la CNIL) — une ligne dans la charte ou une note à l'équipe, à faire par Frédéric.

**D. Le rendez-vous** : « Planifier un rendez-vous » crée l'événement dans l'agenda Google de l'administrateur,
avec la personne invitée (elle reçoit l'invitation), lié à sa fiche ; le fil le note ; option « proposer 3
créneaux libres » (lecture des disponibilités, déjà là).

**E. Les modèles** se gèrent dans l'app (admins) : nom, objet, texte avec cases ; le « Premier contact » est la
version validée le 24/11.

## 3. Ce que ça touche (et ce que ça pourrait casser ailleurs)

- **Base** : un petit patch — la table des modèles du recrutement, l'envoi tracé par candidat, et une fonction
  « désinscription » appelable par le serveur. ⛔ Accord avant de poser.
- **Serveur (Render)** : une route « recrutement » qui fabrique et envoie CHAQUE message (aperçu = même code à
  blanc), en appelant l'envoi Gmail existant ; une variante de la page de désinscription. ⚠ **Le backend est
  partagé avec tout l'app** : du code AJOUTÉ seulement, les routes existantes ne bougent pas ; déploiement = push.
- **Écran** : la fenêtre « Écrire » dans `RecrutementScreen.tsx` (pas de retouche de la fenêtre des contacts,
  utilisée par 3 écrans) ; la barre d'action de la liste.
- **Risque principal** : la **délivrabilité** (un envoi groupé depuis une boîte du domaine peut être classé
  indésirable) → plafond par jour, file douce, désinscription en un clic, en-tête `List-Unsubscribe`.

## 4. En plusieurs temps (chacun utile seul)

1. **E1** — écrire à UN candidat : modèle, cases, aperçu, envoi Workspace, fil + étape + « informée ».
2. **E2** — la sélection multiple et l'envoi groupé (écartés, aperçu par destinataire, file douce, plafond).
3. **E3** — la désinscription en un clic et les réponses dans la fiche.
4. **E4** — le rendez-vous dans l'agenda (invitation, créneaux libres).

## La maquette (24/11, à valider)

https://claude.ai/artifact/EBmocyoc2sRduq9cEg18vP — 4 planches, données fictives ; copie rangée dans
`notice/maquettes_recrutement/emails/` :
1. **Écrire à un candidat** — modèle, cases remplies depuis la fiche (rose) ou à compléter (ambre), bloc RGPD
   verrouillé, pièce jointe, aperçu « tel qu'elle le recevra » en bureau ou téléphone ;
2. **Écrire à plusieurs** — 9 recevront / 3 écartés et pourquoi, aperçu par destinataire (‹ 3 / 9 ›), envoi doux ;
3. **L'envoi, un par un** — avancement, résultat par personne, « Arrêter l'envoi », un refus ne bloque pas les autres ;
4. **Après** — le fil (e-mail envoyé, réponse lue dans Gmail, étape), « Planifier dans mon agenda », et la page
   publique « Ne plus me contacter » sur téléphone (avant / après le clic).

## 4 bis. ✅ E1 CODÉ le 24/11 (« Oui, code l'étape 1 »)

- `apps/hektor-v1/src/lib/recrutementEmail.ts` (neuf) : 4 modèles (premier contact = le texte validé ; relance ;
  rendez-vous ; libre), cases `{prenom}` `{agence_proche}` `{expediteur}` remplies depuis la fiche, passages
  `[À COMPLÉTER]` qui BLOQUENT l'envoi, le bloc RGPD (texte validé) ajouté seul tant qu'elle n'est pas informée
  (sinon la ligne « Ne plus me contacter »), le HTML exact, la lecture de l'expéditeur et des réglages, l'envoi par la
  route Gmail EXISTANTE (`relatedEntityType: recrutement`, journal du serveur inchangé).
- `RecrutementScreen.tsx` : la fenêtre « Écrire » (planche 1) ; après l'envoi, le fil note « E-mail envoyé : <objet> »
  avec « voir l'e-mail tel qu'envoyé », l'étape passe à « Contactée », la case « informée » se coche. Une personne
  OPPOSÉE au registre : envoi refusé (proposé, accepté avec la maquette).
- **Rien de neuf côté serveur ni en base.**
- **Trois réglages en base** (`app_setting`, écriture en production = accord) :
  - `recrutement_envoi_email` = `on` → le bouton « Envoyer » part par Gmail ; **absent → la fenêtre ouvre la
    messagerie de l'administrateur avec le texte prêt (et copié)** : utile dès aujourd'hui, sans rien allumer ;
  - `recrutement_email_adresse_postale` et `recrutement_email_contact_donnees` : sans eux, le bloc RGPD est
    incomplet et l'envoi reste bloqué (message clair dans la fenêtre).
- Éprouvé en local (données fictives) : remplissage, blocage tant qu'un passage reste à compléter, aperçu (bureau et
  téléphone), envoi simulé, fil + étape + « informée », téléphone 375 px sans débordement ; build vert.
  ⚠ L'aperçu dans un cadre totalement isolé ne s'affichait pas : cadre « même origine, sans aucun script ».

- ✅ **EN LIGNE le 24/11 à 16:00** (poussé par Frédéric avec `GTI_ALLOW_PUSH=1`, GitHub = `c78a8a4`). Vu en réel, en
  lecture seule (rien envoyé) : la fenêtre s'ouvre, l'expéditeur est lu, mode « Ouvrir ma messagerie ».
  ⚠ **CORRECTION de ce que j'avais dit** : les deux adresses du bloc RGPD (postale, contact pour les données) sont
  nécessaires dans LES DEUX modes — sans elles, le bloc porte « [ADRESSE POSTALE DE GTI] » et l'envoi reste
  bloqué, même par la messagerie. Rien ne part donc avant ces deux réglages (vérifié dans l'aperçu réel).

- ✅ **Les deux adresses du bloc RGPD sont POSÉES le 24/11 (~16:10)**, données par Frédéric : `recrutement_email_adresse_postale`
  = « 22 rue Jean Jaurès, 42700 Firminy », `recrutement_email_contact_donnees` = « accueil@gti-immobilier.fr ».
  La fenêtre peut donc ouvrir la messagerie avec un texte complet (une fois « [CE QUE GTI PROPOSE] » rempli).
  `recrutement_envoi_email` (l'envoi direct par Gmail) reste ÉTEINT : à allumer seulement sur sa demande.

## 4 ter. ✅ E2 CODÉ le 24/11 (écrire à plusieurs + l'envoi un par un — planches 2 et 3)

- Liste : une **barre d'action** dès qu'un candidat est coché (« Écrire à N candidats », « Tout décocher »).
- Fenêtre : recevront / écartés et POURQUOI (pas d'e-mail ; opposé au registre, d'office ; déjà écrit il y a moins de
  30 jours, avec « Lui écrire quand même ») ; modèle et texte communs, cases remplies pour chacun ; aperçu ‹ i / N › ;
  « Retoucher ce message seulement » ; plafond de 40 par jour (compte du jour lu en base) ; au-delà : « à refaire demain ».
- Envoi : un toutes les 5 s, statut par personne, « Arrêter l'envoi » ; un refus ne bloque pas les autres ; chaque envoi
  noté dans le fil, étape « Contactée », « informée ». ⚠ L'envoi tourne DANS la fenêtre (elle doit rester ouverte) :
  la maquette disait « vous pouvez fermer », ce qui demanderait une file côté serveur, non faite.
- Base : `supabase/patch_recrutement_envoi_groupe_2026-11-24*.sql` (rec_candidats + 3 clés, rec_emails_du_jour),
  répétition 7/7 verte, **PAS posé** (accord). Sans lui, la fenêtre bloque l'envoi (« compte du jour illisible »).
- Il faut aussi l'envoi direct allumé (`recrutement_envoi_email`) : plusieurs e-mails personnalisés ne passent pas par
  une messagerie.
- Éprouvé en local : 5 cochés → 3 recevront / 2 écartés ; envoi simulé de 3 à 5 s d'écart ; « déjà écrit
  aujourd'hui » + « Lui écrire quand même » ; sélection vidée après ; étape « Contacté » ; build vert.

## 5. ⏸ Ce que Frédéric décide

1. **L'adresse d'envoi** : la boîte de l'administrateur connecté, ou une adresse « recrutement@ » à créer.
2. **Le plafond par jour** (proposé : 40) et le délai minimum entre deux e-mails à la même personne (30 jours).
3. **Les personnes opposées à la prospection au registre** : écartées d'office (proposé).
4. **Ses 4 cases** du modèle validé (expéditeur, « ce que GTI propose », adresse postale, adresse de contact).
5. **La maquette** : à valider avant toute ligne de code (règle des écrans du projet).
