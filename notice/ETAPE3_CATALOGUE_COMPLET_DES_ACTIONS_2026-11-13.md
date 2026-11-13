# Étape 3 — le catalogue COMPLET des actions possibles de l'assistant (13/11/2026)

> Demande de Frédéric le 13/11 : « AUDIT MON PROJET POUR PROPOSER DES CHOSES PERTINENTES ET QUE TA LISTE SOIT LA PLUS COMPLÈTE POSSIBLE, EXEMPLE LES DEMANDES À LA DIRECTION POUR VALIDATION, BAISSE DE PRIX, ANNULATION OU LA MISE EN LIGNE D'UN BIEN SI DIFFUSABLE ETC. »
> Complète `notice/ETAPE3_AGENT_QUI_AGIT_AUDIT_2026-11-13.md` (le mécanisme de la carte) et la spec du 29/10 (§5, §5 bis).
> **Méthode** : trois balayages en lecture seule — (1) chaque geste de l'écran (`App.tsx`, `api.ts` et les 20 écrans annexes), avec sa garde de rôle et ses conditions métier ; (2) les 57 types de travaux du worker et toutes les routes du serveur ; (3) **ce qui est réellement utilisé**, mesuré en base (`app_console_job` sur 90 jours, `app_diffusion_request`, états des biens). Rien n'a été écrit.
> **Règle de toujours** : l'assistant ne fait JAMAIS un geste que l'écran ne permet pas au rôle de la personne, et chaque geste passe par une carte « Valider / Annuler ».

Rôles : **[TOUS]** = tout compte actif · **[CONTACTS]** = admin, manager, commercial · **[DIR]** = manager ou admin · **[ADMIN]** = admin seul.

## 1. Les demandes à la direction — l'exemple de Frédéric

Le circuit existe en entier à l'écran (`app_diffusion_request` + ses événements), **mais il dort** : 9 demandes en tout, toutes des essais de mai-juin (4 annulations et 4 baisses acceptées les 13-14/05, 1 diffusion en attente depuis le 02/06).

| Geste | Qui | Conditions de l'écran | Ce que fait le clic |
|---|---|---|---|
| **Demander la validation / mise en diffusion** d'un bien | [TOUS] | mandat avec numéro ; mandat PAS encore validé ; une seule demande en cours par type | crée la demande + l'événement |
| **Demander une baisse de prix** (nouveau prix) | [TOUS] | mandat validé ; prix numérique ; ⚠ le prix ne se modifie JAMAIS en direct (l'écran renvoie vers cette demande) | idem |
| **Demander l'annulation du mandat** | [TOUS] | mandat validé ; c'est LA porte de clôture du registre | idem |
| **Corriger une demande renvoyée** | [TOUS] | demande « à corriger » ou refusée | repasse « en attente » |
| **Traiter : accepter une validation** | [DIR] | — | Hektor : validation = oui, diffusable, portails par défaut ; e-mail de décision au négociateur |
| **Traiter : accepter une baisse** | [DIR] | le prix chez Hektor doit déjà être le nouveau (`price-drop-check`) | puis diffuser sur toutes les passerelles (au choix) ; e-mail de décision |
| **Traiter : accepter une annulation** | [DIR] | date de clôture | décoche diffusable + validation, statut « Clos » chez Hektor, clôture du mandat ; e-mail |
| **Refuser une demande** (motif obligatoire) | [DIR] | — | suivi à J+2 ; e-mail de décision |

**Pertinent pour l'assistant** : c'est là qu'il apporte le plus, parce que le circuit est complet mais personne ne s'en sert. Le négociateur dit « baisse le 63289 à 185 000 » → l'assistant vérifie les conditions (mandat validé, pas de demande en cours), prépare la demande avec un commentaire, carte, clic. Pauline demande « qu'est-ce qui m'attend ? » → la liste des demandes, avec pour chacune le résumé du bien (prix, ancienneté, visites, rapprochements) qui l'aide à trancher, puis « accepte la baisse du 63289 » → carte (vague direction).

## 2. Mettre en ligne et diffuser

Mesuré le 13/11 sur les biens **Actifs** (574) : **249 ne sont pas diffusables**, **259 ne sont sur aucun portail**, **234 sont « à contrôler »** (validation non faite).

| Geste | Qui | Conditions | Ce que fait le clic |
|---|---|---|---|
| Choisir les portails et appliquer | [TOUS] (un commercial : ses biens) | mandat validé ; un commercial ne force jamais « diffusable » | portails chez Hektor + état chez nous |
| Cocher / décocher un portail | [TOUS] | numéro de mandat ; bien diffusable | idem, un portail |
| Basculer « Validation » oui/non | [DIR] | bien en cours | chez Hektor |
| Basculer « Diffusable » oui/non | [DIR] | bien en cours | chez Hektor |

**Pertinent** : « mes biens actifs qui ne sont sur aucun portail » → pour chacun, la bonne suite : demande de validation (mandat pas validé), choix des portails (validé), ou rien (estimation). Pour la direction : « les biens à contrôler depuis plus de 7 jours ».

## 3. Les autres gestes, famille par famille

**Annonces**
- Créer une annonce ou une estimation (brouillon) [CONTACTS] — 21 en 90 j.
- Modifier les champs du bien [TOUS, ses biens] (prix exclu : demande de baisse) — 26 en 90 j.
- Activer un brouillon (le mettre en ligne) [TOUS, ses biens] — 1.
- Rédiger la description par IA (le rédacteur existe déjà).
- Changer le statut (offre, compromis, vendu, clos) [DIR] — 166.
- Archiver [DIR] — 4 · désarchiver [TOUS] — 7 · supprimer [DIR] — 14 · réaffecter le négociateur [DIR] — 3.

**Photos** [TOUS] : synchroniser, couverture, masquer / afficher, réordonner (9), supprimer. ⚠ Ajouter une photo demande un FICHIER (plus tard).

**Documents** [TOUS] : préparer / ouvrir, supprimer. Déposer = un FICHIER (plus tard). Plan cadastral (4 en 90 j), avis de valeur PDF (3).

**Mandat**
- Numéro automatique [TOUS] (non annulable) — 2.
- Document de mandat ou **avenant** (nouveau prix) [TOUS] ; avenant seulement si mandat actif et validé — 2.
- Signature Youtrust : envoyer (4), relancer un signataire (2), annuler (2) ; ImmoSign : relancer, annuler ; « signé à la main ».
- Clôture : par la demande d'annulation (§1) ; corriger une date de clôture [DIR].
- ⛔ Modifier ou prolonger un mandat : fermé par décision (⑦-7).

**Mandants** [TOUS] : rattacher (5), créer (2), modifier (5, ⚠ fonction sans contrôle), retirer (3).

**Transactions** [DIR] : offre / compromis / vente avec leurs champs (1 253 changements d'état d'offre en 90 j), accepter / refuser une offre, annuler un compromis (27), supprimer un compromis (19) ou une vente (15) ; commission, répartition, conditions, note. Trancher un écart [ADMIN].

**Contacts** [CONTACTS] : créer (37), modifier (15), archiver / réactiver (5), ajouter un conjoint (1) ; supprimer [DIR] (39).

**Recherches** [CONTACTS] : créer (4), modifier, archiver (4).

**Rapprochements** [TOUS] : proposer un bien (e-mail, téléphone, visite), écarter / rétablir (⚠ fonctions sans contrôle), **envoyer l'e-mail de rapprochement** (garde-fous : désinscription, plafond du jour, envoi réel derrière `EMAIL_REAL_SEND_ENABLED`).

**Relances** [TOUS] : créer, faite, reportée (⚠ fonctions sans contrôle).

**Agenda** [TOUS] (l'agenda d'un collègue : [DIR]) : créer / modifier / supprimer un RDV (visite, estimation, mandat, compromis, relance…), avec invitations ; la visite pose le statut « visite » du bien. Bon de visite : impression à l'écran seulement.

**E-mails** [TOUS] : e-mail libre avec modèles et pièces jointes (documents, photos) ; e-mail d'estimation ; e-mail de rapprochement.

**Espace client et visites publiques** : le client écrit, demande une visite, modifie sa recherche → cloche + e-mail au négociateur ; le négociateur confirme un créneau ou en propose d'autres (pages `/visite/…`). **Pertinent** : « qui m'a écrit depuis son espace ? », « confirme la visite de M. X jeudi 10 h ».

**Partenaires** [CONTACTS] : syndic / diagnostiqueur d'un bien, créer un partenaire, métier, apporteur / courtier, interlocuteurs d'une étude. « Demander un document au syndic » n'est aujourd'hui qu'un brouillon d'e-mail (rien n'est envoyé par l'app).

**Notifications** [TOUS] : marquer lu / tout lu (2 101 non lues en base).

**Santé** [ADMIN] : prendre en charge / résoudre une alerte, « j'ai refait » / abandonner un geste.

**Matterport** : en ligne, privé, archiver, réactiver — ⚠ API hors service depuis le 03/11 (passe par la console).

**⛔ Exclus** : la gestion des utilisateurs (décision du 29/10, question 5) ; le registre des utilisateurs.

## 4. Ce que l'assistant peut proposer de lui-même (force de proposition)

Situations mesurées le 13/11, qui deviennent des cartes « je te propose de… » :
- **26 offres en attente de réponse** → « accepter / refuser / relancer l'acquéreur ».
- **26 actes prévus dans les 30 jours** → « préparer le rendez-vous de signature, prévenir le notaire ».
- **59 biens vivants à mandat échu** (en vente, sous offre ou sous compromis) → « demander une prolongation par avenant » ou « demander l'annulation ».
- **249 biens actifs non diffusables, 259 sur aucun portail** → « demande de validation » ou « choisir les portails ».
- **2 438 nouveaux rapprochements en 7 jours** → « envoyer le rapprochement aux 5 meilleurs acquéreurs ».
- **3 535 acquéreurs actifs sans mise à jour depuis 90 jours** → « une relance téléphonique », « l'e-mail de rapprochement ».
- **2 101 notifications non lues** → les trier, résumer, marquer lues.
- Demandes de visite et messages de l'espace client en attente → confirmer un créneau, répondre.
- Échecs de gestes (`job_echec`) → expliquer, proposer de refaire.
- Pour la direction : demandes en attente, biens « à contrôler » depuis longtemps, gestes abandonnés.
Tout cela nourrit aussi **le point du jour** (étape 5), qui n'existe pas encore : les sources sont listées (notifications, relances à faire, demandes de visite, demandes de RDV, travaux en erreur, sondes du moniteur).

## 5. L'ordre proposé (à valider)

1. **Lot 1** : la carte de validation + **les demandes à la direction** (créer, corriger) + **les relances**. Gestes simples, chez nous seulement, aucun appel à Hektor : le meilleur terrain pour éprouver la carte.
2. **Lot 2** : rapprochements (proposer, écarter, e-mail de rapprochement à blanc puis en interne), recherches, contacts, notes, notifications.
3. **Lot 3** : agenda et visites (RDV + statut visite + espace client), e-mails libres (en interne d'abord), bon de visite PDF.
4. **Lot 4** : annonce (champs, activer un brouillon, photos sans fichier, rédacteur), mandat (numéro, document, avenant), signature (relancer, annuler), diffusion (portails).
5. **Lot 5 — direction [DIR]** : traiter les demandes (accepter / refuser, avec les vérifications Hektor), validation et diffusable, statuts et transactions, archivage.
6. **Plus tard** : tout ce qui demande un fichier (photos, documents), Matterport, suppressions définitives.
