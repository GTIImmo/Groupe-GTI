# Audit — les champs « Vendeurs » et « N° de mandat » de la modale « Changer le statut »

*06/11/2026. Lecture seule : rien n'a été écrit en base, chez Hektor ni dans le code. Question de Frédéric (06/11) :
« il n'est pas utile de mettre le champ vendeurs ; vérifie aussi le numéro de mandat, je pense qu'il ne faut pas y
toucher, donc mieux vaut le cacher ». Audit limité à ces deux champs de la modale (offre, compromis, vente) ; les autres
objets ne sont pas mesurés ici.*

Sources lues : `App.tsx` (`handleChangeHektorAnnonceStatus`, le grand préremplissage, l'héritage de la vente),
`lib/api.ts` (`createChangeHektorAnnonceStatusJob`), `Console/console_job_worker.js`
(`normalizeStatusTransactionPayload`, `submitHektorTransactionStatus`, `submitHektorAssistantTransaction`),
`supabase/patch_photo_saisie_affaire_2026-09-16.sql` (le carnet). Mesures : `app_console_job` (175 travaux
`change_hektor_annonce_status` depuis le 21/05), leurs journaux `hektor_transaction`, `app_affaire_ledger` (2025+).

## 1. Le champ « Vendeurs » (mandants)

**Ce qu'il fait.** Il MONTRE les vendeurs que le registre connaît pour l'affaire (préremplissage, drapeau « affirmés »
faux) et n'ENVOIE rien tant qu'on n'y touche pas (`mandantContactIds` seulement si `statusChangeMandantsAffirmes`).
Si on y touche, la liste part et REMPLACE celle de Hektor (règle du 16/09 : « null = on ne pose rien, Hektor garde les
siens ; tableau = l'app affirme »).

**Ce que Hektor fait sans lui (registre, depuis 2025).**
- Compromis : **699 sur 699** portent leurs vendeurs ; ventes : **640 sur 642**. Hektor les déduit lui-même du mandat
  (mesure du 16/09 : le compromis 50084, créé SANS vendeur, est revenu avec ses trois).
- Offres : **0 sur 707**. Le formulaire d'offre de Hektor n'a pas de vendeurs : le champ y est donc toujours vide, et
  y toucher n'aurait de sens que pour le carnet.

**Usage réel.** 9 envois en tout depuis le 16/09, **tous des essais** (24933 le 16/09, 24113 le 23/10, par
Frédéric pour éprouver le geste). **Aucun usage réel.** ⛔ *Correction du 06/11 :* 24113 (VA6482, mandat 18787) **n'est
PAS un bien d'essai**, ce sont de vrais clients (Frédéric, 03/11) ; il a seulement servi de banc aux essais du 22-23/10.

**Risque du champ.** Une liste tapée incomplète REMPLACE la bonne liste de Hektor (le code le dit : « une liste
incomplète ferait pire que mieux »).

**Conclusion.** Le champ n'apporte rien et porte un risque. **Le cacher ne change rien à ce qui part** : sans geste, la
liste n'est jamais envoyée — c'est exactement le chemin pris par 100 % des transactions réelles. Les vendeurs se
corrigent sur la fiche du bien / du mandat, pas au moment d'une transaction.

## 2. Le champ « N° de mandat »

**Ce qu'il fait.** Il est PRÉREMPLI avec un numéro de mandat (« 18787 ») : en modification depuis le carnet de l'affaire
(`carnet.numero_mandat`), à la vente depuis le compromis repris (`c.numero_mandat`). La charge l'envoie toujours
(`selected_mandat`), qu'on y ait touché ou non. La base le recopie dans le carnet (`app_affaire_champ_app`,
champ `numero_mandat`) — et le carnet resert au préremplissage suivant : la boucle s'entretient.

**Ce que le worker en fait.**
- **Compromis et vente** (l'assistant de Hektor, `submitHektorAssistantTransaction`) : le champ n'est **lu nulle
  part**. Le worker « reposte ce que Hektor a rendu » : le mandat vient du formulaire de Hektor. **Le champ ne sert à
  rien.**
- **Offre** (`submitHektorTransactionStatus`) : `selectedMandat = payload.selected_mandat || <la valeur cachée de
  Hektor>`. Le champ de l'app PASSE DEVANT celle de Hektor. Or Hektor attend sa propre forme (`553-PROTEXA`,
  `10261-HEKTOR`) et le code le dit depuis le 25/08 : « une valeur amputée est ignorée SANS ERREUR — l'offre part alors
  sans mandat ».

**La mesure, journal par journal (22 offres envoyées).**
- champ VIDE → le worker envoie la valeur de Hektor : `553-PROTEXA` (24113), `10261-HEKTOR` (24933) ;
- champ REMPLI → il envoie le numéro seul : `11939`, `18787`, `18426` — **11 offres** ;
- sur 150 transactions, **92 ont envoyé un numéro seul, 0 la forme de Hektor**.

**Ce que Hektor en a gardé (registre).** Sur 24933, les offres créées du 01 au 03/09 avec « 11939 » sont TOUTES
revenues **sans mandat** (`mandat_origine = deduit_unique` : c'est notre registre qui le devine) ; celle du 04/09,
créée avec « 10261-HEKTOR », porte le sien (`hektor`). Même partage sur 24113 le 23/10 (`deduit_periode` contre
`hektor`). ⚠ Ce sont des essais (24113 est un vrai bien client qui a servi de banc) ; sur le parc, les offres de 2025+ n'ont leur mandat de Hektor que pour 291 sur
707 (395 déduits) — cette faiblesse vient surtout des offres saisies chez Hektor, pas de l'app (22 offres seulement
sont parties de l'app).

**Conclusion.** Le champ est inutile au compromis et à la vente, et **nuisible à l'offre** : prérempli, il remplace la
bonne valeur de Hektor par une valeur qu'il ignore, et l'offre part sans mandat. Personne ne peut d'ailleurs y taper la
bonne forme (l'identifiant interne de Hektor n'est affiché nulle part).

⚠ **LE CACHER NE SUFFIT PAS** : caché, il resterait prérempli et continuerait de partir. Il faut aussi que la modale
n'envoie plus `selected_mandat` (ou seulement si quelqu'un l'a touché, ce qui n'arrivera plus une fois caché). C'est
une modification de `handleChangeHektorAnnonceStatus` — un des 61 morceaux « derrière » — donc HORS du chantier
visuel : elle demande son propre « vas-y ».

**Ce que ça pourrait casser ailleurs.**
- La clôture (« Clos ») : n'utilise pas ce champ (`setMandatClotureApp` prend `statusChangeTarget.numero_mandat`) ; la
  clôture chez Hektor est débranchée depuis le 28/08 (12 travaux « Clos », 12 avec le champ vide). Rien ne change.
- Le carnet : il ne recevra plus de `numero_mandat` venu de la modale ; le registre garde celui de Hektor (ou sa
  déduction). L'affichage de la liste des affaires lit le carnet PUIS le registre : il montrera celui du registre.
- Les biens à plusieurs mandats (1,2 % du parc) : Hektor propose alors une liste ; le worker ne sait pas lire un
  `<select>` (`htmlInputValue`), il retombe sur le champ caché `selectedMandatId`. Aujourd'hui, le champ de l'app n'y
  aidait pas davantage (même numéro seul, ignoré). Pas de régression ; cas à part.
- Les essais : `test_boutons_modale_point5`, `test_heritage_compromis_offre`, `test_offre_regularisation` ne portent
  pas sur ce champ ; l'outil d'empreintes signalera `handleChangeHektorAnnonceStatus` changé — à lire, puis reposer.

## 3. Proposition

1. **Vendeurs** : retirer le champ de la nouvelle modale. Écran seulement ; rien de ce qui part ne change.
2. **N° de mandat** : retirer le champ de la nouvelle modale **et** ne plus envoyer `selected_mandat` depuis la modale
   (une ligne dans `handleChangeHektorAnnonceStatus`, qui vaut aussi pour l'ancienne modale). Le worker envoie alors
   la valeur de Hektor, comme pour les offres réussies.
3. Contrôle : l'envoi réel prévu sur 62774 (une offre) doit revenir **avec son mandat de Hektor**
   (`forme_mandat = <id>-<FAMILLE>` au journal, `mandat_origine = hektor` au registre après la nuit) — c'est le témoin
   positif.
4. Retour arrière : remettre la ligne ; réafficher les champs.

## 4. Fait le 06/11 (« Oui, vas-y » de Frédéric)

- **Vue** (`ModaleStatutV2.tsx`) : les champs « Vendeurs » et « N° de mandat » sont retirés (offre : 4 champs,
  compromis : 5, vente : 2 ; « Les personnes » = l'acquéreur et les deux notaires). Vu à l'écran en démonstration.
- **Envoi** (`App.tsx`, `handleChangeHektorAnnonceStatus`) : `selectedMandat: ''` — la modale n'envoie plus de numéro
  de mandat, la nouvelle comme l'ancienne. Le worker reposte la valeur de Hektor.
- **Outil de preuve** (`test_statut_v2_empreintes.cjs`) : les noms retirés sont DÉCLARÉS (liste `RETIRES`, avec ce
  renvoi) et attendus absents ; tout geste ou condition qui les porte est attendu absent ; leur retour serait un écart.
  Le contrôle a signalé EXACTEMENT un écart, `handleChangeHektorAnnonceStatus` — la ligne décidée — puis la
  référence a été reposée (sommet `8c321a4`). Essais de la modale verts ; `npm run build` vert.
- ✅ **Le témoin positif est FAIT le 06/11 à 16:40** (poussé par Frédéric, paquet servi `index-Cgh_zedy.js` vérifié :
  `selectedMandat:""`, interrupteur `"true"`). Cible : **61398** (mandants « TEST GTI Delphine », Actif, diffusable 0,
  mandat 18420) — 62774 est clos depuis le 21/10, et 24113 est un VRAI client. Offre de 170 000 €, 06/11, 10 jours,
  acquéreur d'essai ESSAI 8 CINQ (605976), envoyée depuis la NOUVELLE modale avec l'accord de Frédéric. Travail
  `ac20049d-0717-4f4f-9c6e-184cb7d3e2ae` : `done`, `verifie: true`, 0 erreur. Charge : `selected_mandat` **vide**.
  Journal `hektor_transaction` : **`forme_mandat_selectionne = 3-PROTEXA`** (la valeur de Hektor, plus un numéro seul),
  et la réponse de Hektor porte l'offre **33132** avec **`id_mandat: 3`, `type_mandat: PROTEXA`** → l'offre est née
  AVEC son mandat. Preuve « deux portes » (fiche + API) verte. À 16:40, avant la nuit : `hektor_mandat_id` vide,
  `mandat_origine` vide, `numero_mandat` 18420 (le registre n'était pas encore relu).
- ✅ **Lu après la nuit, le 07/11** (registre relu à 05:24:27) : l'offre 33132 porte **`mandat_origine = hektor`**,
  **`hektor_mandat_id = 3`**, `numero_mandat` 18420, `present_in_hektor` vrai, 170 000 €, 10 jours, état `proposed`.
  Le témoin positif est complet de bout en bout : l'offre partie de la modale est née chez Hektor AVEC son mandat, et
  notre registre le reconnaît comme venant de Hektor (plus une déduction).
- ⚠ Le bien d'essai 61398 est maintenant « Sous offre » chez Hektor, avec l'offre 33132 en cours ; la refuser pour le
  remettre « Actif » serait un autre geste chez Hektor, non fait (décision de Frédéric).
- ⚠ L'ancienne modale (interrupteur éteint) affiche toujours la case « N° de mandat », mais sa valeur ne part plus.
