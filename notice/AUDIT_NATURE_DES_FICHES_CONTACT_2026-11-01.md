# AUDIT — LA NATURE DE CHAQUE FICHE CONTACT, DU SERVEUR À L'APP

**01/11/2026 · chantier ⑧ · couples.** Demande de Frédéric : « une logique aussi pour le serveur à l'app », puis « oui » à la
logique des sept natures, avec deux questions : les 28 473 couples ont-ils une deuxième fiche, faut-il en créer ; et ce qu'on fait
de chaque famille.

> ⛔ LECTURE SEULE. Rien n'est codé, rien n'est écrit en base ni chez Hektor. Audit limité aux CONTACTS (lire / afficher /
> envoyer). Les gestes créer / modifier / archiver / supprimer ne sont pas changés par cette proposition ; « compléter le
> conjoint » (décision 3) reste hors périmètre.
> Sources : `AUDIT_COUPLES_ANCIENS_AFFICHAGE_2026-11-01.md` §4 bis à §10 (les règles), `COUPLES_ERGONOMIE_ET_ECRITURE_PROPOSITION_2026-10-30.md`
> §21-23 (P1, P2, P3). Script de mesure : `natures.py` (scratchpad, lecture seule, aucun nom affiché).

---

## 1. LES CHIFFRES — LES 356 762 FICHES DU SERVEUR

Trois nombres par nature : serveur (archivées comprises) · actives · dans l'app.

**Famille 1 — les vrais contacts (210 269)**

1. **Personne seule** : 181 290 · 68 623 · 39 891. Dont 113 894 mises « en couple » par l'import de Hektor sans signe (§10 de l'audit des couples anciens).
2. **Couple** (un agent l'a écrit : « Mr./Mme », code 2026, deux prénoms, ou conjoint avec prénom) : 28 473 · 11 302 · 4 788.
3. **Conjoint** (deuxième fiche avec prénom) : 506 · 451 · 67.

**Famille 2 — les cases créées par Hektor (146 493)**

4. **Conjoint sans prénom** (nom de famille recopié) : 13 150 · 12 033 · 1 540.
5. **Case conjoint vide** : 96 889 · 53 287 · 12 111.
6. **Case vide orpheline** (13 989 places dont la première a disparu + 22 459 fiches vides sans lien + 6) : 36 454 · 26 863 · 3 777.

**Famille 3 — les doublons (se comptent à part)** : 12 950 personnes en 27 810 fiches, **14 860 en trop** ; **1 102 en trop dans l'app**.

Total : 356 762 · 172 559 · **62 174 dans l'app** (règle d'envoi actuelle : bien actif, recherche active ou partie d'une transaction).

## 2. LES 28 473 COUPLES ONT-ILS UNE DEUXIÈME FICHE ?

- a. **deuxième fiche avec prénom** (vrai conjoint) : 422 · actifs 395 · app 307 ;
- b. **deuxième fiche au nom recopié, sans prénom** : 13 135 · 5 023 · 2 443 ;
- c. **deuxième fiche vide** : 11 298 · 3 654 · 1 652 ;
- d. **lien de couple Hektor mais aucune deuxième fiche** : 1 142 · 409 · 135 ;
- e. **aucun lien de couple chez Hektor** (l'agent l'a écrit, Hektor ne le sait pas) : 2 476 · 1 821 · 251.

**12 206 couples ont les deux prénoms écrits sur la première fiche** (« Paul et Anne ») : le prénom du conjoint est connu.

**Faut-il créer les deuxièmes fiches qui manquent ? CONSEIL : NON, pas en masse.**
- Pour **b et c (24 433)**, la case **existe déjà** : quand un agent complète le conjoint, on **remplit cette case** (modification
  chez Hektor d'une fiche existante), on n'en crée pas une autre. Sinon on fabrique un doublon.
- Pour **d et e (3 618, dont 2 230 actifs)**, créer une fiche vide reproduirait exactement ce que l'import de Hektor a fait de mal.
  La fiche se crée **quand on connaît la personne**, par le geste « compléter le conjoint » ; la création d'une paire existe déjà
  en base depuis le 31/10 (`app_contact_creer_conjoint`, pièces A-B-C). ⚠ Pour e, il faudra poser le lien chez Hektor sur une
  fiche EXISTANTE : non éprouvé, et « Transformer en couple » a déjà fait disparaître une fiche le 30/10.
- **Ce qu'on peut faire sans rien créer** : afficher « Couple · conjoint à compléter », et **pré-remplir le prénom** du conjoint
  pour les 12 206 couples qui l'ont écrit. Un clic de l'agent suffit ensuite.
- Une création en masse chez Hektor coûterait aussi le quota (~1 req/s, plafond de la nuit), sans valeur tant que le conjoint
  n'est pas nommé.

## 2 bis. LES CAS d ET e, FICHE PAR FICHE *(question de Frédéric : « les id pointent sur rien ? »)*

**Rappel du mécanisme** : chaque fiche Hektor a une case `refCouple`. Sur la fiche principale d'un foyer, elle contient **son propre
numéro** (« je suis le chef du foyer ») ; sur la deuxième fiche, **le numéro de la principale** (« je suis son conjoint »). Rien
d'autre ne relie les deux.

**Cas d — 1 142 couples (409 actifs) : la principale dit « je suis chef de foyer », mais personne ne dit « je suis son conjoint ».**
Vérifié dans la fiche brute de Hektor : `refCouple` = son propre numéro pour les 1 142. Le numéro ne pointe donc pas « sur rien »,
il pointe **sur elle-même** ; c'est la deuxième fiche qui a disparu ou perdu son lien. Une fiche vide détachée créée **à la même
seconde** existe pour 100 d'entre eux (probablement leur case perdue), plusieurs candidates pour 445, aucune pour 597. Toutes
créées avant mars 2026 (une seule après). Civilité : « Mr./Mme » 722, vide 303, « M. » 112 ; deux prénoms écrits : 706.

**Cas e — 2 475 couples : aucun lien du tout (`refCouple` vide chez Hektor).** Seul ce qu'un agent a écrit dit « couple » :
« Mr./Mme » 1 569, deux prénoms 978.
- **602 n'existent plus chez Hektor** : ce sont des fiches supprimées dont nous gardons le nom parce qu'une annonce ou une offre les
  cite (agence vide, réponse 404). Rien à compléter chez Hektor.
- **1 873 sont de vraies fiches sans lien** (1 218 actives), surtout à Issoire, Courpière, Tence, Craponne-sur-Arzon : les agences
  importées avec le réglage « foyer pour les couples seulement », qui a manqué une partie des couples.

**Ce qu'on fait** :
- **À l'écran, aucune différence** : les 3 617 s'affichent « Couple · conjoint à compléter », comme les couples à case vide, avec le
  prénom proposé quand il est écrit (706 + 978).
- **On ne crée rien d'avance**, et on ne raccroche pas les 100 cases probables : elles sont vides, les relier n'apporterait rien.
- **La différence n'existe que pour le geste « compléter le conjoint »** (plus tard) :
  - d : créer une deuxième fiche dont `refCouple` = le numéro de la principale — c'est exactement le modèle de Hektor, la
    principale est déjà prête ;
  - e : il faut EN PLUS poser `refCouple` sur la principale existante — **non éprouvé**, à essayer d'abord sur une fiche d'essai
    (« Transformer en couple » a fait disparaître une fiche le 30/10) ;
  - les 602 supprimées chez Hektor : affichage seulement, pas de geste.

## 3. CE QUI EXISTE DÉJÀ (code lu)

- **La nuit** (`phase2/contacts/build_contacts_layer.py`) :
  - `couple_role` (l. 136) : `menage_resolu` (case vide dont la première est connue), `menage_orphelin` (première disparue), sinon vide ;
  - `display_name` (l. 158) : une case vide emprunte l'identité de sa première (« Mr./Mme DURAND ») ; une case orpheline ou une
    fiche vide sans lien devient « Contact <numéro> » ;
  - l'envoi (l. ~1800) : raisons `active_annonce_relation`, `active_search`, et `console_transaction_party`.
- **P2, posé le 01/11** (`conjoints_des_couples.py`) : `couple_json` sur la première, `couple_role = 'conjoint'` pour une seconde
  NOMMÉE (y compris celles au nom recopié), qui devient envoyée. ⏰ première nuit le 02/11.
- **L'écran** (`apps/hektor-v1/src/lib/api.ts`) : `SANS_FICHE_DE_MENAGE` (l. 200) masque `menage_resolu` dans l'annuaire (l. 3524),
  la recherche générale (l. 5440) et le choix d'un mandant (l. 10258). ⭐ **Les mandants d'un bien ne passent PAS par ce filtre**
  (`loadAnnonceMandants`, l. ~10160 : lecture par les liens, puis les fiches) : masquer une fiche de l'annuaire ne la retire pas
  d'un bien.
- **Qui lit `display_name`** : le worker (22 endroits), l'espace client, les rendez-vous, l'administration (`backend/app/services`).

## 4. CE QU'ON FAIT DE CHAQUE FAMILLE — LA PROPOSITION

Principe : **la nuit calcule une nature pour chaque fiche, une seule fois, au serveur ; l'app lit la nature au lieu de deviner.**
Rien n'est supprimé, rien n'est écrit chez Hektor. `couple_role` et `display_name` **ne changent pas** (trop de lecteurs) : la
nature s'AJOUTE.

**Famille 1 — les vrais contacts**
- **Personne seule** : nature `personne`. Le lien de couple posé par l'import est **ignoré**. Affichée normalement. Civilité
  corrigée par le classeur quand Hektor a perdu « Madame » (19 290 actives) — dans une colonne à nous, jamais dans `civilite`.
- **Couple** : nature `couple`. Annuaire : une tuile « Couple · Paul et Anne » (P3). Fiche : « conjoint à compléter » en orange
  si le conjoint manque (réponse de Frédéric du 31/10 : orange sur la fiche seulement). Prénom du conjoint pré-rempli quand il est écrit.
- **Conjoint** : nature `conjoint`. Pas de ligne à part dans l'annuaire (il est dans la tuile du couple) ; trouvé par la recherche
  et le choix d'un mandant ; l'ouvrir ouvre le couple sur son onglet (P3).

**Famille 2 — les cases de Hektor**
- **Conjoint sans prénom** : nature `case_nom_recopie`. Jamais une ligne d'annuaire. Dans le couple : « conjoint à compléter ».
  Sur un bien (1 540 dans l'app) : « Conjoint de DURAND (prénom inconnu) ».
- **Case conjoint vide** : nature `case_vide`. Déjà masquée de l'annuaire (`menage_resolu`). Sur un bien (12 111 dans l'app) :
  « Conjoint de DURAND (non renseigné) » au lieu de « Mr./Mme DURAND ».
- **Case vide orpheline** : nature `case_orpheline`. **Nouveau** : retirée de l'annuaire, de la recherche et du choix d'un mandant
  (aujourd'hui « Contact 1000… », 3 777 dans l'app). Sur un bien : « Conjoint non identifié ». Elle reste sur le bien (vérifié §3).
- Pour toute la famille 2 : envoyée vers l'app **seulement si elle est liée à un bien** (déjà le cas) ; et le jour de la coupure,
  **elle n'est pas reprise** dans notre registre maître sauf si elle est liée à un acte.

**Famille 3 — les doublons**
- Aucun changement automatique. Le drapeau « Doublon » existe déjà. Une liste de revue pour un admin viendra dans un chantier à part
  (les 1 102 fiches en trop de l'app d'abord) : la fiche choisie reste, l'autre est masquée de l'annuaire avec « doublon de… » et
  garde ses biens, recherches et mandats.

## 5. CE QUE ÇA POURRAIT CASSER AILLEURS

1. **La nouvelle colonne doit exister chez Supabase AVANT la nuit**, sinon le push échoue (même piège que P2). Écriture en
   production : **accord de Frédéric**.
2. **Une clé neuve dans la charge du push peut être jetée** (mémoire « nouvelle clé dans la charge peut être JETÉE ») : le push
   doit nommer la colonne, à éprouver hors ligne.
3. **La première nuit, les 62 174 fiches de l'app repartent toutes une fois** : envoi plus lourd, à mesurer (P2 en ajoute déjà ~26 000).
4. **`couple_role` garde ses trois lecteurs** (filtre de l'écran, P2, la fonction de la paire en base) : la nature ne le remplace pas.
5. **`display_name` ne change pas** : les libellés « Conjoint de… » sont composés à l'écran à partir de la nature. Le worker,
   l'espace client et les rendez-vous ne voient rien.
6. **Masquer les orphelines** de la recherche et du choix d'un mandant : un agent qui cherchait « Contact 1000… » ne la trouvera
   plus. Elle reste visible sur son bien.
7. **La civilité corrigée** vient du classeur (données personnelles) : il est chargé une fois dans une table du serveur, jamais
   dans git ni dans Supabase ; seule la civilité dérivée part vers l'app.
8. **Le téléphone** a un rendu séparé (`MobileLayout`) : chaque libellé est à vérifier aussi sur téléphone.

## 6. L'ORDRE, LE RETOUR ARRIÈRE, LA VÉRIFICATION

- **N1** — la nuit calcule la nature et la civilité corrigée, **au serveur seulement** (essai à blanc, les chiffres du §1 doivent
  ressortir). Additif, aucun lecteur.
- **N2** — colonne chez Supabase (accord) + envoi derrière un interrupteur dans `.env`.
- **N3** — l'écran (P3 + libellés de la famille 2 + « Mme »), derrière un interrupteur, ordinateur ET téléphone.
- **N4** — les doublons, chantier à part.
- **Retour arrière** : éteindre les interrupteurs ; la colonne peut rester (personne ne la lit) ou être retirée par un patch inverse.
- **Vérification** : les comptes du §1 après la nuit ; témoin inverse : aucune fiche sans nom ne reçoit `personne` ou `couple`,
  et aucune fiche nommée ne reçoit une nature de la famille 2.

## 7. NON MESURÉ

- Le comportement de Hektor quand on pose un lien de couple sur une fiche EXISTANTE (cas e).
- La part de faux positifs dans « deux prénoms écrits » (un nom composé avec « et » ?) : un échantillon lu par une personne le dirait.
- Le poids exact de la première nuit (N2).
