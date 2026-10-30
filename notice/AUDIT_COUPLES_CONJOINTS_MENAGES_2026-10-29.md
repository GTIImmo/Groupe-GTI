# AUDIT APPROFONDI — LES COUPLES, CONJOINTS ET MÉNAGES *(29/10/2026)*

> **Demande de Frédéric (29/10)** : *« Le couple conjoint dans les contacts est une partie très compliquée que nous avons commencé à
> travailler mais pas entièrement maîtrisée ; donc il faut d'abord réaliser un audit approfondi de tout mon projet, mes codes et notes à
> ce sujet, ensuite analyse et fais-moi un rapport. »*
>
> **Lecture seule.** Rien codé, rien écrit en base, **0 appel à Hektor**. Sources : toutes les notes (`notice/`, racine, mémoire, notes
> supprimées, messages de commit), l'écran (`apps/hektor-v1`), le worker et les scripts (`Console/`, `backend/`), la synchro et le SQL
> (`phase2/`, `hektor_pipeline/`, `supabase/`), et des mesures du jour dans le cloud et les deux bases locales.
> Suite de l'audit 8g (`notice/CHANTIER_8_GARDE_CHEZ_NOUS_2026-10-21.md`, section 8g).
> Aucun nom de personne réelle : les contacts sont cités par leur numéro.

---

## 1. EN UNE PAGE

- **Chez Hektor, un couple, ce sont DEUX fiches** qui partagent un numéro de ménage (`refCouple`). La première (« la porteuse ») porte
  le nom et se désigne elle-même ; la seconde est **presque toujours vide** (civilité « Mr./Mme », ni nom ni prénom). Le vrai bloc
  conjoint (`nom_m2`, `prenom_m2`, `email_m2`, `telephone_m2`, `adresse_m2`) vit **dans le formulaire web de Hektor, pas dans son API**.
- **Ce que nous savons faire aujourd'hui — et qui marche** : lire le ménage chaque nuit, traduire le lien dans nos numéros, **masquer la
  fiche vide** quand sa porteuse est connue (« une personne, une ligne », Frédéric, 11/09), **fusionner le ménage** en une ligne sur la
  fiche d'un bien, écarter les fiches vides des mandants du registre et de la signature.
- **Ce que nous ne savons PAS faire** : **créer** un couple qui marche sans Hektor, **modifier** un conjoint, **voir** le conjoint,
  **supprimer / archiver / retirer** un ménage entier. Le chemin « créer un couple » de l'écran existe mais **n'a jamais servi**
  (0 sur 26 créations) et **n'a jamais été mesuré** — et le conjoint saisi **n'est gardé nulle part chez nous**.
- **Le sujet a une date de péremption** (Frédéric, 25/09) : la seule façon de savoir quelle paire fabriquer nous-mêmes, c'est de regarder
  ce que Hektor fabrique **tant qu'il vit**.
- **Trois défauts réels sont trouvés en plus** (section 5), dont un qui touche les documents de mandat.

---

## 2. COMMENT ÇA MARCHE AUJOURD'HUI, DE BOUT EN BOUT

**La nuit (le seul chemin qui vit vraiment)** :
1. Le run lit les contacts de Hektor (`phase1 sync_raw`, `contact details delta`) ; `normalize_source.py:1166-1169` écrit
   `hektor_contact.hektor_couple_contact_id` depuis `refCouple` (« 0 » = aucun). ⚠ **Un lien vide n'efface jamais l'ancien**
   (`normalize_source.py:1138-1145`, choix écrit : « un couple défait chez Hektor… rare »).
2. `build_contacts_layer.py` traduit le lien dans **notre** série (`identite_app()`, l. 444 et 517) et calcule `couple_role`
   (l. 96-131, 781-835) :
   - une fiche est « de ménage » si elle n'a **ni nom ni prénom**, **un lien**, et que ce lien désigne **une autre** fiche ;
   - `menage_resolu` si la porteuse a prénom + nom ; `menage_orphelin` sinon ; toute autre fiche : vide. **Aucun rôle « porteuse »**
     (décision écrite l. 125-127) ;
   - nom affiché : la fiche résolue prend « civilité + prénom nom de la porteuse » ; l'orpheline « Contact <numéro> ».
3. Le push envoie `hektor_couple_contact_id` et `couple_role` ; `app_contact_id_propager` remplit `app_couple_contact_id` dans le cloud
   (`patch_26bis_couples_entretien_2026-09-21.sql:76-87`) — en SQL exprès, pour ne pas changer les 200 000 empreintes du push (21/09).
4. Sentinelle `data.couples_non_traduits` (`monitoring/check_gti_health.py:592-605`), seuil absolu 3 000, niveau warning.

**L'écran (lecture)** :
- Annuaire, recherche globale, sélecteur de contacts : filtre `SANS_FICHE_DE_MENAGE` (`api.ts:200`, utilisé l. 3524, 5440, 10155) —
  la résolue disparaît, l'orpheline reste visible.
- Fiche d'un bien (rubrique Contact) : fusion par `couple:<refCouple>` (`App.tsx:7148`), nom fusionné par `mergeCoupleContactName`
  (`App.tsx:7206-7222`, « M. et Mme NOM »), rôle « mandants mariés ».
- Registre des mandats : `export_app_payload.py:1964-2145` marque les fiches vides `"muet": true` et les retire du texte ;
  `App.tsx:7419-7422` les ignore.
- Signature Youtrust (26/10) : on n'invente jamais de prénom ; une fiche de couple sans prénom donne un refus clair « à éclater en deux
  signataires » (`console_job_worker.js:6240-6253`, 6427) ; D22 de Frédéric : *« il faut ajouter par défaut le conjoint »*.

**L'écran (création)** — **une seule porte** : `HektorContactIdentityForm` (`App.tsx:40610`), ouverte depuis l'annuaire (ordinateur et
téléphone) et les deux modales « Nouveau contact » de l'agenda. Menu « Structure » → `couple` → bloc « Conjoint » de 7 champs (nom exigé,
prénom, e-mail, téléphone, adresse, CP, ville). `api.ts:10205-10211` envoie `spouse_*` + `person_type` à `app_create_contact_optimistic`.
Le worker (`console_job_worker.js:18274-18298`, 18406-18409) transforme `couple` en `statut = "2"`, ouvre le formulaire `contact_couple`
et remplit `nom_m2`, `prenom_m2`, `email_m2[]`, `telephone_m2[]`, `adresse_m2`, `villeprivee`, `codeprivee` (18501-18517). **C'est Hektor
qui fabrique (ou non) la seconde fiche.**

---

## 3. LA GRILLE DES GESTES *(règle du 21/09)* — audit limité au ménage ; les autres objets ne sont pas mesurés ici

**Contact en couple**
- **Créer** : porte unique (annuaire + agenda) ; **jamais servi** (26 créations depuis le 29/05, toutes `personne_seule`, 23 charges
  avec des clés `spouse_*` vides) ; ce que Hektor fabrique : **non mesuré** ; conjoint gardé chez nous : **non** (ni
  `app_create_contact_optimistic`, ni la naissance complète 8a `patch_8a_contact_nait_complet_2026-10-21.sql:64-83`, ni le compte rendu
  du travail — seulement `app_console_job.payload_json`) ; la seconde fiche reçoit un numéro chez nous : **non** (un seul `nextval`).
- **Modifier** : **impossible** de modifier, ajouter ou retirer un conjoint (`isCouplePerson` n'existe qu'en création, `App.tsx:40713` ;
  le menu Structure est masqué en édition, 41508 ; les champs conjoint partent vides, 40061-40078 et 43824-43841). Chez Hektor le
  conjoint est **préservé** (le worker relit le formulaire et ne touche pas `_m2` hors statut 2, 19172-19187). ⚠ Risque non mesuré : le
  filtre de groupe de `extractHektorFormValues` (10436-10453) pourrait ne pas renvoyer les champs `_m2`.
- **Supprimer / archiver** : **un seul numéro** (`console_job_worker.js:21455-21600`, 19437-19472 ; `api.ts:10328`, 10356). La seconde
  fiche n'est jamais regardée. Ce que Hektor fait de son côté (cascade ?) : **non mesuré**. Chez nous, la fiche vide d'une porteuse
  supprimée devient `menage_orphelin` et **réapparaît** dans l'annuaire en « Contact <n> ».
- **Lire / remonter** : la nuit, voir section 2 ✅.

**Relation (mandant, propriétaire, acquéreur)**
- **Créer un mandant en couple** : **impossible** — `createHektorMandantContact` force `statut=1` (`console_job_worker.js:20778`), à la
  création d'annonce comme pour un mandant ajouté ; `api.ts:10402` n'a ni `person_type` ni conjoint.
- **Modifier un mandant** : une seule fiche (la plus complète du ménage fusionné, `App.tsx:3738`).
- **Retirer un mandant** : un seul numéro détaché (`App.tsx:3610`, 3641) ; les autres fiches du ménage **restent liées au bien**.
- **Acquéreurs d'une transaction** : plusieurs acquéreurs, dédoublonnés par numéro (« un couple n'a pas toujours le même »,
  `App.tsx:29565`) ; table des parties : `fiche_sans_nom` = nom vide, **sans lien vers la porteuse**
  (`patch_table_des_parties_2026-10-26.sql:26,75`).

**Document / signature** : voir défaut n° 1 (section 5).
**Annonce, recherche, mandat (hors relation), RDV / visite** : non concernés par le ménage — sauf les **invités d'un RDV** tirés d'un
bien (`api.ts:9970`), qui incluent les fiches vides et les comptent dans la limite de 24.

---

## 4. LES MESURES DU JOUR *(29/10, cloud et bases locales, lecture seule)*

**Le miroir local** (`data/hektor.sqlite`, tout le parc Hektor) : 356 716 contacts ; **264 418** avec un numéro de ménage ;
**139 890** porteuses (se désignent elles-mêmes). Ménages : à 1 fiche **47 399**, à 2 **105 567**, à 3 **1 947**, à 4 **11** ;
**14 069** ménages dont la porteuse a disparu.

**Le cloud** (`app_contact_current`, le périmètre de l'app : **62 357** contacts) :
- `couple_role` : vide **47 844** · `menage_resolu` **12 115** (toutes vides, liées à une porteuse nommée) · `menage_orphelin`
  **2 398** (toutes vides).
- Forme des ménages vus du cloud : 2 fiches dont 1 nommée **11 831** · 2 fiches toutes deux nommées **1 379** (de vrais couples à deux
  noms) · 1 seule fiche nommée **11 108** · 1 seule fiche vide **2 682**.
- Civilités : vide **27 060** · « Mr./Mme » **21 393** · M. 12 406 · Mme. 1 004 · ⚠ **et une famille de civilités de couple que personne
  n'a documentée** : `M_Mme` **327**, `Mme_M` **8**, `Mme_Mme` **5**, `M_M` **2** (342 fiches).
- Fiches vides **sans aucun lien de ménage** : **1 396** — ni masquées, ni résolues.
- Liens non traduits (`app_v_couples_non_traduits`) : **2 756** (stable depuis le 21/09 : 2 752).
- ⭐ **Les 2 398 orphelines** : leur porteuse est **absente du miroir local, 2 398 sur 2 398** (vérifié numéro par numéro). Le nom est
  **perdu pour de bon** chez nous — ce n'est pas un défaut de traduction.

**L'impact sur les biens vivants** (`app_dossier_current`, liens propriétaires présents, non retirés) : **12 717** biens, **22 785** liens.
**6 298 biens** (≈ la moitié) ont au moins une fiche vide de ménage parmi leurs propriétaires (**5 446** liens vers une résolue,
**1 509** vers une orpheline, sur **1 333** biens). ⭐ Mais **seuls 5 biens vivants n'ont AUCUN propriétaire nommé** — la fiche vide
accompagne presque toujours sa porteuse ou un co-propriétaire nommé.

---

## 5. LES DÉFAUTS TROUVÉS *(du plus grave au moins grave)* — à vérifier à l'écran avant toute correction

1. **Le document de mandat fait de la fiche vide un mandant.** `buildMandatDocumentMandants` (`App.tsx:4413-4427`) déplie les
   `members` d'un couple **sans filtrer** les fiches vides : la fiche « Mr./Mme » devient un mandant à part, sans nom, avec les
   coordonnées de la porteuse par repli. Déjà vu le 26/10 dans l'éditeur (`notice/PROPOSITION_FENETRE_ENVOI_SIGNATURE_2026-10-26.md:86`),
   **jamais corrigé**. Touche aussi la signature (une case de signature pour une fiche vide).
2. **Le conjoint saisi à la création serait jeté en silence** dans deux cas : si la charge porte une clé `statut` / `status` d'une
   valeur inconnue (elle passe **avant** `person_type`, `console_job_worker.js:18406-18409`, et le statut retombe sur « 1 ») ; et à
   toute création de **mandant** (statut forcé à 1). Aucun refus, aucune ligne de journal.
3. **La fiche vide revient quand on supprime ou retire la porteuse** : supprimer, archiver, retirer un mandant n'agissent que sur un
   numéro ; la fiche vide devient orpheline (annuaire, « Contact <n> ») ou reste liée seule au bien.
4. **La ville du conjoint partirait en texte seul** (`villeprivee`, `codeprivee`), sans identifiant de commune — or Hektor ignore une
   ville en texte seul (leçon du 22/10). Et que `villeprivee` soit bien la ville du conjoint **n'est pas mesuré** (côté annonce, ce nom
   désigne la commune du bien).
5. **La civilité « Mr./Mme » n'existe pas dans l'écran** : le formulaire ne propose que M., Mme., Mlle. (`App.tsx:41172-41174`), et
   `contactCivilityToken` (`App.tsx:7199-7203`) ne reconnaît ni « Mr./Mme » ni `M_Mme` — le nom fusionné peut ne pas donner
   « M. et Mme NOM » (à voir à l'écran).
6. **Chaque modification de contact renvoie `person_type: personne_seule` et `contact_kind: acquereur`** (`api.ts:10221-10222`). Sans
   effet sur le ménage chez Hektor ; ⚠ mais une **personne morale** modifiée est traitée en statut 1 (branche `sociale`, l. 18481, non
   prise) — hors sujet couples, noté.
7. **Petits défauts de cohérence** : `affaireAcquereursNoms` (`App.tsx:29660`) ne filtre pas la fiche vide, `ckNomsParties` (29648) si ;
   `loadContactById` ouvre une fiche vide en « Mr./Mme » sans renvoi vers sa porteuse ; statistiques et invités de RDV sans le filtre ;
   **trois détections différentes** de « la fiche vide » (couche : ni nom ni prénom + lien ; registre : une expression sur le nom ;
   parties : nom vide) qui peuvent diverger.
8. **Le lien traduit ne se corrige jamais** : l'entretien ne remplit que `app_couple_contact_id IS NULL`
   (`patch_26bis_couples_entretien_2026-09-21.sql:82`) alors que la pose utilisait `IS DISTINCT FROM`. Et **`app_couple_contact_id`
   n'est lu par AUCUN code** (vérifié par recherche dans tout le dépôt) : écrit chaque nuit pour rien aujourd'hui.
9. **`menage_orphelin` est mal nommé** : il vaut aussi pour une porteuse présente mais sans prénom + nom (une société) ; la sentinelle
   dit « détecter une hausse » mais son seuil est absolu, et en warning (aucun e-mail).

---

## 6. CE QUI MANQUERAIT LE JOUR DE LA COUPURE

- Personne ne fabriquerait plus la seconde fiche ni le numéro de ménage : **aucune fonction de création ne pose de lien**.
- Le conjoint saisi resterait dans la charge d'un travail qui n'existe plus ; `couple_role` resterait vide pour tout contact né dans
  l'app (il n'est calculé que la nuit, depuis Hektor) ; la fusion à l'écran ne jouerait plus pour les nouveaux ménages.
- La nuit repartirait d'un miroir figé, et la règle « le vide ne gagne pas » garderait les anciens liens indéfiniment.
- Il n'existe aucun geste « ménage » : modifier le conjoint, séparer un couple, supprimer / archiver les deux, éclater en deux
  signataires.

---

## 7. LES DÉCISIONS DÉJÀ PRISES — NE PAS RELANCER

- **« Une personne, une ligne »** (11/09, Frédéric : *« sur les listings de recherche il faut qu'il n'y ait qu'une fiche si l'autre est
  vide »*) ; les orphelines restent visibles ; la proposition de recopier le nom de la porteuse sur la fiche vide a été **rejetée**.
- **Ne jamais écrire `nom` / `prenom` sur la fiche vide** (la nuit y verrait une divergence) — passer par une colonne à part.
- Le lien de ménage est posé **dans notre série, côté cloud** (21/09).
- **C.9-couple a une date de péremption** (25/09) — la mesure doit se faire tant que Hektor vit.
- Toute écriture chez Hektor exige un « go » explicite ; la cible d'essai est **choisie par Frédéric**.
- **Point D reporté** (22/10) : les champs sans colonne chez nous, dont le bloc conjoint.
- **D22** (26/10) : le conjoint est ajouté **d'office** comme signataire ; on n'invente jamais de prénom.
- *« Les couples sont un autre point du dev »* (Frédéric, cité au code `api.ts:277`, 02/10) — c'est ce point-ci.

---

## 8. LES NOTES QUI SE CONTREDISENT *(à remettre d'aplomb)*

- **La mémoire `contacts-muets-fiches-de-couple.md` est périmée sur 3 points** : elle dit le lien en numéro d'app « pas posé » (il l'est
  depuis ca5fde2, 21/09), l'arbitrage « non tranché » (Frédéric a tranché le 11/09), et l'écran « reste à faire » (fait par f89b500 le
  même jour). → corrigée avec ce rapport.
- **26bis-COUPLES** : coché ✅ au journal (25/09) et rangé en L2 au plan, mais la case de la liste reste `[ ]` (l. 8825) tout en
  écrivant « déjà fait » (l. 554).
- **C.9-couple** : CLAUDE.md le range en « étape 3, hors code » ; la note du chantier 8 en fait **8g** de l'étape 2.
- **Des chiffres qui ne parlent pas de la même chose** : 13 989 fiches en 404 / 13 998 orphelines / 14 080 liens / 14 069 ménages ;
  264 272 → 264 372 → 264 418 fiches à numéro de ménage (le parc grossit) ; 2 752 / 2 756 / 2 758 non traduits ; 301 / 303 / 309
  fiches de couple pour la signature (trois bases différentes). Les chiffres 40 157 / 37 404 / 2 753 du plan n'existent nulle part
  dans le code.

---

## 9. CE QUI RESTE À DÉCIDER — par Frédéric

1. **La mesure d'une heure** (8g option A), tant que Hektor vit : un couple d'essai créé depuis l'app (noms fictifs), les deux sondes
   (`phase2/checks/sonde_paire_de_menage.py`, `Console/sonde_conjoint.js`), puis la suppression de l'essai **en vérifiant que la seconde
   fiche part aussi**. Elle répondrait d'un coup à : une fiche ou deux ? quel sens ? quels champs ? `villeprivee` est-il la ville du
   conjoint ? la civilité « Mr./Mme » est-elle posée ? la suppression descend-elle en cascade ?
   ⚠ La sonde `sonde_conjoint.js` a deux défauts à corriger avant (elle ignore `<textarea>` et `<select>` ; chemin de Chrome mal écrit).
2. **Où vit le conjoint chez nous** (question posée le 07/10 et le 26/10, jamais tranchée) : **A** une vraie seconde fiche née chez nous,
   liée par `app_couple_contact_id` (le modèle de Hektor, que tout notre code sait déjà lire) ; **B** un bloc conjoint sur la fiche
   porteuse (le modèle du formulaire) ; **C** les deux.
3. **Les défauts de la section 5** : lesquels corriger, dans quel ordre — le n° 1 (document de mandat) est le seul qui touche un
   document signé.
4. **Les 342 fiches aux civilités `M_Mme`, `Mme_M`, `Mme_Mme`, `M_M`** et les **1 396 fiches vides sans aucun lien** : à regarder
   (non mesuré d'où elles viennent).

**Ma recommandation, dans l'ordre** : (1) la mesure d'une heure — rien d'autre ne peut se décider proprement sans elle, et elle périme ;
(2) le défaut n° 1 du document de mandat, qui ne dépend pas de la mesure ; (3) le choix A / B / C du conjoint, à la lumière de la mesure ;
(4) le reste de la section 5, en un chantier « ménage » à part, avec sa propre grille de gestes.

---

## 10. POURQUOI HEKTOR FAIT COMME ÇA — VU DANS SON ÉCRAN *(30/10, Frédéric : « il faut bien comprendre avant de corriger »)*

**Lecture seule**, dans le Chrome de Frédéric (sa session), ~15 lectures espacées de 1,5 s : la page d'un contact, le formulaire
d'édition (`contacts-ihmChargeGroupe`, `consultMode=editer`, le même que lit le worker) et le formulaire **vierge** de création d'un
couple (`addManuelContactFromOtherObject`, `statut=contact_couple` — il AFFICHE le formulaire, il ne crée rien ; seul `insertManuel…`
crée). **Rien n'a été enregistré.** Les valeurs ont été comparées dans le navigateur sans être affichées : aucun nom n'est sorti.

### 10.1 Le modèle de Hektor : UN FOYER, DEUX MEMBRES, DEUX FICHES
- **Le formulaire d'un couple a deux blocs** : le membre 1 (`nom`, `prenom`, téléphones, e-mails, adresse, naissance) et le **membre 2**
  (`nom_m2`, `prenom_m2`, `telephone_m2[]`, `email_m2[]`, `dateenr_m2`, `adresse_m2`, `villeprivee` + **`idVilleprivee`** + `codeprivee` +
  **`idCodeprivee`**, `pays_m2`, `dateNaissance_m2`, `lieuNaissance_m2`, `lang_m2`, `commentaires_m2` — 25 champs).
  ⇒ **`villeprivee` EST bien la ville du conjoint** (réserve du §5 n° 4 levée), et elle a son **identifiant de commune**.
- **La civilité d'un couple dit sa composition** : la liste ne propose que `M_Mme` (« M./Mme », **choisie par défaut** dans le formulaire
  vierge), `M_M` (« M./M. »), `Mme_Mme` (« Mme./Mme. »), `Mme_M` (« Mme./M. »), et « Non défini ». **« Mr./Mme » n'est plus dans la
  liste** : c'est l'ancien libellé, resté dans les données (la fiche 1078 montre « Non défini » ET `M_Mme` marqués à la fois).
- ⭐⭐ **LA SECONDE FICHE EST LE MIROIR EXACT DU BLOC « MEMBRE 2 » DE LA PREMIÈRE.** Comparé champ par champ sur trois ménages — deux
  récents (603324 → 603325, 603330 → 603331, créés dans Hektor en mai 2026) et un ancien (1078 → 1079, 2023) : `nom_m2` = `nom` de la
  seconde, `prenom_m2` = `prenom`, `telephone_m2` = téléphone, `email_m2` = e-mail, `adresse_m2` = adresse, `dateNaissance_m2` =
  naissance — **ÉGAL partout où c'est rempli**, « vide des deux côtés » ailleurs. La seconde fiche n'a pas elle-même de bloc membre 2.
- ⭐⭐ **D'OÙ VIENNENT LES 133 343 FICHES « MUETTES »** : ce sont les secondes fiches de ménages dont **personne n'a jamais rempli le
  membre 2**. Sur 1078 / 1079, seul le nom du conjoint avait été saisi → la seconde fiche a un nom et **pas de prénom**, exactement.
  Ce n'est ni un doublon ni un défaut : c'est **la place du conjoint, vide parce qu'on ne l'a jamais saisi**.
- **La page du contact** affiche le foyer comme UN contact : « M./MME NOM » en titre, « M./Mme NOM Prénom1 / Prénom2 » dans le fil
  d'Ariane.
- Une fiche « personne seule » (141053) **n'a pas** de bloc membre 2 dans son formulaire.

### 10.2 Le changement de février 2026 *(mesuré dans le miroir, par mois de création)*
- **Jusqu'en janvier 2026** : les couples naissent en « Mr./Mme » (215 à 394 par mois), la seconde fiche presque toujours vide.
- **Depuis février 2026** : **0** « Mr./Mme » ; les couples naissent en `M_Mme` / `Mme_M` / `Mme_Mme` / `M_M` (33 à 145 par mois).
  Sur **394** ménages de ce type à deux fiches, **369 ont les deux fiches nommées** (prénom + nom) et **370 ont des numéros
  consécutifs** (603324 / 603325…). ⇒ Hektor (ou l'agence, en saisissant enfin le conjoint) a changé de pratique : **le second membre
  est maintenant rempli et devient une vraie fiche**.
- Hypothèse, NON prouvée (il faudrait la documentation de Hektor) : la seconde fiche a été **rétro-créée en masse** pour tout le parc
  ancien (mesure du 11/09 : identifiants 400 000 à 599 999, date recopiée de la porteuse), puis le formulaire « deux membres » est devenu
  la norme à la création.

### 10.3 Ce que ça change pour notre code *(constaté, rien corrigé)*
- **Notre chemin de création envoie DÉJÀ la bonne forme** (statut 2 → formulaire `contact_couple`, bloc `nom_m2`…), c'est-à-dire ce que
  fait l'écran de Hektor. Il est donc **probable** que Hektor fabrique les deux fiches comme pour 603324 / 603325 — **non prouvé** tant que
  l'essai n'est pas fait.
- ⚠ **Mais trois écarts avec le formulaire de Hektor** (nouveaux défauts, à ajouter au §5) :
  - **La civilité** : le worker pose `civilite` = la valeur de notre écran (« M. », « Mme. » ou vide, `console_job_worker.js:18487`),
    toujours présente dans la charge → elle **écrase** le `M_Mme` par défaut du formulaire avec une valeur **absente de la liste**
    d'un couple. Effet chez Hektor : non mesuré (« Non défini » probable).
  - **La ville du conjoint** part sans `idVilleprivee` / `idCodeprivee` → très probablement ignorée (§5 n° 4 confirmé sur la forme).
  - **Le bloc membre 2 a 25 champs**, notre écran en envoie 7 (pas de naissance, lieu, pays, langue, commentaires du conjoint).
- ⚠ **Notre lecture des couples récents est fausse en un point** : la règle « fiche de ménage = sans nom ni prénom » ne voit pas les
  couples modernes (deux fiches nommées) — c'est voulu (« une personne, une ligne » ne masque que la fiche vide), mais ces deux personnes
  ne sont **reliées nulle part à l'écran** hors de la fiche d'un bien (pas de rôle « porteuse », `app_couple_contact_id` lu par aucun code).
- **Non mesuré** (il faudrait écrire chez Hektor) : modifier la seconde fiche met-elle à jour le membre 2 de la première ? Laquelle fait
  foi ? Supprimer la première supprime-t-elle la seconde ?

### 10.4 Pourquoi un CRM immobilier range un couple ainsi *(connaissance générale, pas une mesure)*
- **L'unité commerciale est le FOYER** : un couple cherche, visite, achète ou vend ensemble ; une recherche, un rapprochement, un mandat
  appartiennent au foyer. D'où **une page « M./Mme NOM »** et un seul interlocuteur dans les listes.
- **L'unité juridique et de communication est la PERSONNE** : chacun a son téléphone, son e-mail, sa date de naissance, ses consentements
  (RGPD), et **chacun signe**. Pour un mandat de vente du **logement de la famille**, le Code civil (art. 215, al. 3) exige l'accord des
  deux époux même si un seul est propriétaire ; un bien commun ou en indivision se signe par tous. ⇒ il faut **une identité complète par
  signataire** : c'est exactement la décision D22 du 26/10 (« ajouter par défaut le conjoint »).
- **Deux façons de faire existent dans les CRM** : (a) une seule fiche avec un bloc « conjoint » (simple, mais le conjoint n'est pas
  un vrai contact : pas d'e-mail propre, pas de signature propre) ; (b) deux fiches liées par un numéro de foyer (chaque personne est un
  vrai contact). **Hektor fait les deux à la fois** : le bloc membre 2 dans le formulaire du foyer, et la seconde fiche qui en est le
  miroir. C'est ce qui rend le sujet compliqué : **deux endroits pour une même personne**.
