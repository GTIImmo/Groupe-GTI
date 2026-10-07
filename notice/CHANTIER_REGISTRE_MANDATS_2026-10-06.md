# CHANTIER — le registre des mandats *(note de memoire, 06/10/2026)*

> **A quoi sert cette note** : la session du 05 et du 06/10 a produit beaucoup de
> mesures et **cinq corrections de mes propres affirmations**. Tout ce qui suit est
> MESURE. Les chiffres que j'ai annonces puis retires sont nommes, pour qu'on ne les
> ressorte pas.
>
> ~~**Rien n'est lance.** Le LOT 0 attend le « vas-y » de Frederic.~~

---

## ⭐ ETAT AU 06/10 AU SOIR — QUATRE LOTS FAITS ET EPROUVES

```
4ec2e2d  LOT 1  la fiche annonce reprend ses MANDANTS chez nous
87364c1  LOT 2  le registre dit le PRIX la ou il ecrivait un montant -- MASQUE RETIRE
6e76d17  LOT 2b sans prix ET corps emprunte -> on ne dit rien (1 regression rattrapee)
308fb70  LOT 3  app_mandat perd `montant` -- LE CODE SEUL, les 2 ALTER TABLE restent
037d956  LOT 4  la fiche annonce cesse d'afficher un montant emprunte
```

## ✅ 07/10 — TOUT EST EN LIGNE, ET TROIS PIEGES PAYES AU PASSAGE

```
ETAT FINAL MESURE A 09:56
   registre               24 494 lignes · montant <> prix 0 · historique <> prix 0
   fiches actives         13 904 lignes · barre qui pend 0 · 0 doublon
   index archive          35 317 · barre 0      index historique  8 937 · barre 0
   temoin 63198           la fiche dit « Emmanuel MILAGRO » (plus de barre)
```

**LES QUATRE COMMANDES, DANS L'ORDRE REELLEMENT PASSE** *(Frederic a inverse les
deux dernieres ; mesure apres coup : AUCUN degat, le registre est reste a 24 494
et a 0 ecart, parce que le push ne remplace que les 736 lignes qu'il reecrit)*

```
refresh_views.py                                  33 725 barres retirees en local
registre_mandats_upsert.py                        pose 24 494 lignes en 68 s,
                                                  AUCUNE suppression
push_upgrade_to_supabase.py --all-local-current   8 946 fiches, baseline false
```

**⛔ PIEGE 1 — UN PUSH QUI REUSSIT EN N'ENVOYANT RIEN.** Lance sans drapeau, il
a repondu `exit 0` et un bilan d'apparence normale avec `"details_upserted": 0`
et `"baseline_adopted": true` : faute de repere de fraicheur exploitable il
ADOPTE LA LIGNE DE BASE et saute les fiches. Les deux index, eux, passent (ils
comparent des empreintes). Le drapeau qui force est `--all-local-current` ;
`--full-rebuild` force aussi mais VIDE le registre -- a ne pas utiliser.

**⛔ PIEGE 2 — `--rebuild-register-only` N'ETAIT PAS LE BON OUTIL.** Elle vide la
table avant de la refaire, et son propre en-tete l'interdit en journee. Le bon
existe depuis le 30/09 et je l'avais manque : `registre_mandats_upsert.py`,
UPSERT seul, le registre n'est JAMAIS vide.

**⛔ PIEGE 3 — J'AI COMPARE LA MAUVAISE TABLE, POUR LA TROISIEME FOIS DE LA
JOURNEE.** Le cloud affichait 13 904 fiches et j'ai cru a une anomalie parce que
`app_dossiers_current` en compte 13 463. Ce sont DEUX PERIMETRES DIFFERENTS : le
push lit `app_view_generale WHERE ANNONCES_SCOPE_WHERE`, qui rend exactement
13 904 avec la meme repartition (Estimation 12 955, Actif 813, compromis 85,
offre 51). Le cloud est JUSTE.
   ⭐ ET CELA A REVELE UN TROU REEL : le cloud lui manquait 441 annonces de son
     PROPRE perimetre, que le push incrementiel de la nuit n'avait jamais
     portees. `--all-local-current` les a comblees. A SURVEILLER : si l'ecart
     revient, c'est le detecteur de fraicheur du push qu'il faut regarder.

---

**CE QUE LES MESURES ONT CORRIGE DANS MES PROPRES CHIFFRES** *(la 6e et la 7e fois)*

```
« 456 mandants empruntes »         -> 87. J'avais compte les entrees qui PORTENT
                                      un mandant, pas celles qui portent le nom
                                      d'un AUTRE. Sur 457 couples suspects, 370
                                      designent LA MEME personne, ecrite autrement,
                                      et le texte de Hektor y est PLUS RICHE
                                      (adresse, parfois un co-mandant).
                                      PROUVE PAR UNE 3e SOURCE : le bloc
                                      `proprietaires` DE L'ANNONCE confirme notre
                                      nom 86 fois sur 86, celui de `mandats[]` 0.

« etendre le masque »             -> REFUSE PAR FREDERIC, et il avait raison :
                                      « un masque, ce n'est pas une rustine ? »
                                      Si. On a mis LA VRAIE VALEUR a la place.
```

**LES REGLES RETENUES, et pourquoi elles DIFFERENT d'un ecran a l'autre**

```
LE REGISTRE   colonne de NOMS SEULS -> notre liste gagne, rien n'est perdu
LA FICHE      texte qui porte AUSSI l'adresse -> on ne remplace QUE si nos noms
              n'ont AUCUN nom en commun avec celui de Hektor
LE MONTANT    mandat COURANT + un prix -> le prix du bien
              mandat ANCIEN, ou pas de prix -> on EFFACE (un prix d'aujourd'hui
              ne dit rien d'un mandat signe autrefois)
```

**CE QUI RESTE, ET C'EST POUR FREDERIC**

```
⬜ les 2 ALTER TABLE du LOT 3 : local + supabase/patch_app_mandat_sans_montant_2026-10-06.sql
   l'outil a refuse l'ALTER TABLE en production (« irreversible »). Repete sur
   copie de 5,9 Go : 1,35 s, 0 ligne perdue, 3 index intacts, quick_check ok.
   Filet : notice/filet_montants_app_mandat_2026-10-06.json (26 839 triplets).
⬜ pousser les 5 commits
⬜ rien n'est a l'ecran avant le run de nuit (ou la prochaine sauvegarde d'une fiche)
```

**LES CONTROLES, tous eprouves A L'ENVERS** *(ils echouent sur la version d'avant)*

```
phase2/checks/fiche_annonce_mandants.py        mandants + montants de la fiche
phase2/checks/registre_montant_est_le_prix.py  les 3 chemins du registre
phase2/checks/chemin_immediat_paquet.py        non-regression du chemin immediat
```

---

## 0. CE QUI EST DEJA FAIT ET DEPLOYE

```
e060bb5  (pousse le 06/10, Vercel deploye, applique par le run de la nuit suivante)
   view_generale.py  mandat_montant : COALESCE(src.prix formate, m.montant)
                     mandants_texte : COALESCE(proprietaires_resume, m.mandants_texte)
   App.tsx:4447      mandat_montant RETIRE de la chaine des HONORAIRES
```

**Pourquoi le 3e n'etait pas optionnel** : en remplissant `mandat_montant`, les deux
premiers auraient fait passer de **87 a 3 310** le nombre de PDF imprimant le prix du
bien dans la case « honoraires d'agence ».

**Eprouve** : SQL prepare par SQLite sans erreur · 4 temoins basculent du faux au juste
(61693 `140 000 -> 365 000` THEVENOT -> TOUBI · 61811 `95 000 -> 71 000` · 39707
`62 000 -> 112 500` · 62055 `69 500 -> 139 500` GRANGE -> MIQUEL, **confirme par l'API
de Hektor elle-meme**) · mandants : 24 244 changent, **97 conservees par le COALESCE,
0 perdue** · honoraires : 87 -> 0 · `npm run build` OK.

⚠ **C'est une marche, pas la destination** : le `COALESCE` vers le bloc proprietaires
de Hektor disparaitra au profit de nos relations (LOT 1).

---

## 1. LA CAUSE RACINE, ETABLIE

### a) Les corps empruntes — ce n'est PAS notre code

Le referentiel mandats de Hektor est **gele au n° 18339 / 30-01-2026**. Ses **trois**
routes s'arretent ensemble (`ListMandat`, `MandatById`, `MandatsByIdAnnonce`) --
documente le 21/07 dans `sync_raw.py` et `refresh_single_annonce.py`, **verifie par
appels reels** (n° 18299 encore servi, n° 18549 vide).

Au-dela de ce numero, deux cas, mesures sur 454 lignes :

```
363  Hektor ne trouve AUCUN enregistrement
     -> pas de montant (champ STOCKE), mais il DERIVE encore les mandants des
        proprietaires de l'annonce -> noms justes, montant VIDE
 88  l'identifiant nu tombe sur un VIEUX mandat (les ids PROTEXA repartent de 1,
     453 des 469 collisionnent) -> Hektor sert le CORPS ENTIER du vieux mandat :
     montant ET mandants d'un AUTRE bien
```

**Un seul appel, sur l'ID ANNONCE** : `GET /Api/Annonce/AnnonceById/?id=<idAnnonce>`,
dont la reponse porte 21 blocs. **Nous n'appelons jamais rien avec un id de mandat.**
La resolution fautive se fait **chez Hektor, avant l'envoi** -- prouve quatre fois :
l'archive brute `raw_api_response` contient deja le mauvais corps ; le miroir le
reproduit a l'identique (454/454) ; le bloc `proprietaires` de la MEME reponse nomme
quelqu'un d'autre (88 cas) ; et `mandat_infofi.prix` de la MEME reponse donne le vrai prix.

⭐ **Hektor se contredit lui-meme** : annonce 61693, un seul document ->
`mandats[]` dit « THEVENOT / 140 000 », `mandat_infofi.prix` dit 365 000,
`proprietaires[]` dit « TOUBI ».

### b) Les mandants manquants — ca, c'est NOTRE code

```sql
-- LE REGISTRE DES ANNONCES (view_generale)
mandants_texte : COALESCE( m.mandants_texte , det.proprietaires_resume )
                                              ^^^ UN RECOURS, et il sauve 255 lignes
```
```python
# LE REGISTRE DES MANDATS (mandat_ledger._poser)
_texte(courante.get("mandants")) or _texte(_du_plat("mandants_texte"))
#       ^^^ le bloc mandats         ^^^ LE MEME bloc, forme plate
#       DEUX recours, et les DEUX puisent au MEME bloc. AUCUN vers les proprietaires.
```

**Chronologie de la faute** : le 21/07 on retire `MandatById` (le gros trou : il
ECRASAIT numero, type, dates et montant par ceux d'un homonyme -- **310 des 392
mandats recents y etaient exposes**). Le 29/09 on cree `app_mandat`, et son commit dit
juste : *« Le registre lit le detail. LA TABLE DOIT LIRE LA MEME CHOSE. »* -- **mais la
VALEUR du registre ne vient pas de la source seule, elle passe par le COALESCE de la
vue.** La table a copie la SOURCE, pas la RECETTE. D'ou 255 lignes plus pauvres.

⭐ **Les deux symptomes de Frederic -- des noms faux et des noms manquants -- sont les
deux faces d'un seul `COALESCE` : mal ordonne dans la vue, absent dans app_mandat.**

---

## 2. LE PERIMETRE REEL — DEUX POPULATIONS, PAS UN TOTAL

⚠ **« 715 lignes suspectes » est une formule FAUSSE, et c'est moi qui l'ai employee.**
« Suspect » ne vaut que pour les 457. Les 258 ne sont pas suspectes : elles sont VIDES.
Ce sont deux problemes de gravite differente, et il ne faut pas les additionner.

### A — 457 lignes : UN NOM FAUX S'AFFICHE  ⛔ le cas grave
Elles ONT un texte de mandant, mais c'est celui d'un **autre bien**. Toutes de 2026,
toutes au-dela du n° 18339.
```
ann 59559  n° 18476  mars 2026   affiche : « Michel NUNEZ21 rue Francis garnier »
ann 24113  n° 18787  juil. 2026  affiche : « M. QUETANT Laurent78 bis rue de Coullons »
ann 61740  n° 18445  mars 2026   affiche : « Isabelle HUMBERT2 chemin du presbytere »
```
**Un nom de personne etrangere sur un document de mandat.** Reparables par nos
relations : **457 sur 457**.

### B — 258 lignes : AUCUN NOM NE S'AFFICHE  ⚠ genant, pas dangereux
L'entree de Hektor est **vide**. Pas de faux : du rien. Toutes anciennes (2012-2020),
et **presque toutes des SOCIETES**.
```
ann 1053   n° 3653  2012   (vide)      ann 38002  n° 2406  2017   (vide)
ann 38569  n° 7948  2014   (vide)      ann 38631  n° 7540  2014   (vide)
```

⭐⭐ **ET LE CORRECTIF SOCIETES EXISTE DEJA — c'est le registre des relations lui-meme.**
Rappel de Frederic, 06/10. Nos relations viennent du bloc `proprietaires`, qui NOMME la
societe. Aucun traitement particulier n'est necessaire :
```
ann 1053   -> « M. SCI JCL »            ann 38569  -> « MAISON EN FRANCE »
ann 38002  -> « SCAM »                  ann 38631  -> « PORTE | M. Service Tutelaire ARHM »
```
Reparables : **228 sur 258**, 30 restent inconnues.

### Et ce qui reste EXCLU, par decision
```
2 073  LOCATION / INCONNUE, origine=annonce   -> decision de Frederic du 26/08
   29  LOCATION/GESTION/INCONNUE origine=detail -> a trancher
```

⚠ **Correction de Frederic, 06/10** : j'annoncais « 2 320 trous a combler ». **Faux** --
ce sont des LOCATIONS et des natures inconnues lues sur l'index, deja ecartees.

```
BILAN : 457 + 228 = 685 lignes reparables · 30 restent vides
```

---

## 3. ⭐ CE QUI MARCHE DEJA, ET QU'IL NE FAUT PAS « REPARER »

```
les 39 annonces a PLUSIEURS mandats :
   29  mandants DIFFERENTS par mandat   ->  DEJA JUSTE
   10  le meme mandant                  ->  NORMAL (renouvellement)
    0  aucun mandant
```

**`_poser()` lit `courante.get("mandants")`** -- l'entree de CE mandat dans
`mandats_json`, pas les proprietaires du bien. `app_view_generale.mandats_json` porte
l'historique complet : 13 cles par entree (id, numero, type, debut, fin, cloture,
montant, mandants, note, avenants, CartePro, duree_irrevocabilite, taciteReconduction),
et **37 des 39 ont leurs propres mandants par entree**.

Le registre des ANNONCES, lui, n'a pas le probleme : sur les 39, il montre **le plus
recent 36 fois**, **0 numero etranger, 0 melange de date, 39/39 mandants coherents avec
le mandat affiche**.

⚠ **Et j'avais invente un « trieur » pour un probleme qui n'existe pas.** Le risque
« tous les proprietaires du bien » n'existe QUE sur l'intersection :
**48 lignes sur 715** (une ligne en recours, sur une annonce a plusieurs mandats).

### ⛔ LE TRIEUR EST ABANDONNE — l'audit du 06/10 le condamne

L'idee etait : le texte des AUTRES mandats du bien dit quels noms ne sont pas les
notres, donc on les ECARTE. **Mesure sur les 48 :**

```
 1 nom  : 23 lignes   -> RIEN A TRIER, aucun risque de surplus
 2 noms : 17
 3 noms :  4
 4 noms :  3
 5 noms :  1
         -> 25 lignes a 2 noms ou plus = le seul vrai sujet
```

⚠⚠ **ET MA PREMIERE RAISON DE LE REFUSER ETAIT FAUSSE.** J'avais ecrit : *« sur
l'annonce 8377, ecarter FERNANDEZ laisserait "Contact 10348368", un nom muet »*.
**Je lisais la liste BRUTE, pas l'affichage** : `texte_des_mandants()` filtre les noms
muets depuis le 04/10.
```
ann 8377   liste BRUTE   : ['Julien FERNANDEZ', 'Contact 10348368']
           ce qui S'AFFICHE : « Julien FERNANDEZ »
```

### ⛔ LA VRAIE RAISON DU REFUS, et elle est de principe

```
sur les 39 annonces a plusieurs mandats, 10 portent LE MEME mandant sur TOUS :
   ann 61800   n° 18497 -> SERVAT Patrick     n° 18837 -> SERVAT Patrick
```

**Une personne peut etre mandante de DEUX mandats du meme bien** -- elle a renouvele.
Donc « ecarter ce que l'autre mandat nomme » est **faux en principe** : sur l'annonce
8377, l'autre mandat nomme FERNANDEZ et notre liste affichee EST FERNANDEZ. Le trieur
la viderait.

⚠ **Et un contre-exemple qui confirme** : annonce 62055, les DEUX textes de Hektor sont
faux (MOREAUX et GRANGE), nos relations disent MIQUEL, **et l'API de Hektor confirme
MIQUEL**. Un trieur base sur ses textes aurait suivi le faux.

### Ce qu'on fait sur les 48 : RIEN de special

**Et je retire aussi ma proposition de « marquer la ligne comme mandants DU BIEN ».**
Elle supposait un defaut qui n'en est pas un.

```
apres filtrage des muets, sur les 48 :
   25 lignes affichent UN seul nom
   23 lignes en affichent plusieurs
```

⭐ **Et plusieurs mandants n'est PAS une anomalie : c'est le cas de 47,5 % du registre.**
```
24 491 lignes :  UN mandant 12 823 (52,4 %)  ·  PLUSIEURS 11 637 (47,5 %)
```
Un couple, une fratrie, une indivision. `62055 -> MIQUEL | MIQUEL` est un couple
confirme par l'API ; `30911 -> Muriel | Cecile | patricia | Eric Andriollo` une famille.

➡ **Le recours standard suffit. Aucun traitement particulier pour les 48.**

---

## 4. POURQUOI `app_relation` ET PAS LE BLOC DE L'ANNONCE

**Argument decisif, et c'est celui de Frederic, pas le mien :**

```
le bloc « proprietaires » de l'annonce :  100,0 % d'identifiants HEKTOR (17 297/17 297)
app_relation.app_contact_id            :  100,0 % d'identifiants A NOUS (132 697/132 697)
```

Lire le bloc directement **reintroduirait les identifiants de Hektor** -- exactement le
bug corrige le 30/09 par `93cc01b` -- **et defairait le geste « retirer un mandant »**
(en service depuis le 03/10, `retire_le` + `retire_par`).

⚠ **Mon argument de couverture etait faible et je le retire** : le bloc couvre 98,0 %
des annonces du registre, nos relations 99,9 %. L'ecart est de 459, dont **451 =
annonces dont NOUS n'avons aucun detail** (toutes archivees ; le detail d'une archive
n'est rapatrie qu'a la demande). **Hektor n'oublie pas les proprietaires des biens
vendus** : il les sert encore sur 98 %.

⭐ Et `app_relation` **n'est pas une autre source** : c'est le bloc `proprietaires`,
extrait par `build_contacts_layer.py`, **conserve** (delete-never) et dote de nos
numeros. 132 697 liens contre 50 236 dans le cloud -- *82 386 liens qu'un bien vendu
emportait*.

⭐ **Et le registre des mandats est le plus avance du projet sur l'identite** :
`mandants_json` porte **les deux numeros** (`{"app_contact_id": 10002776,
"hektor_contact_id": "5509", "nom": "..."}`), alors que les trois index d'annonce et
`app_dossiers_current` ne portent **AUCUNE** colonne de contact.

---

## 5. LE PLAN, PAR LOTS

### LOT 0 — le filet, AVANT tout *(code NEUF, ne touche a rien)*
```
0a  un controle qui lance le VRAI push_single_annonce_to_supabase.py sur une annonce
    temoin, a chaque changement de export_app_payload.py
    -> aurait EMPECHE la panne du 05/10 (9 h de silence, 13 echecs, aucune alerte)
    -> lecon `eprouver-c-est-executer-le-code` : ma fonction avait ete « prouvee »
       trois fois, toujours par le chemin qui pose row_factory
0b  une sentinelle : alerte des 2 echecs consecutifs de refresh_console_data
0c  brancher les 3 sentinelles mandat ECRITES ET JAMAIS LANCEES
    (mandat_corps_recopie · mandat_disparu · registre_depuis_app_mandat : 0 occurrence
     dans le pipeline)
```
C'est aussi le **n° 2 et le n° 1** de la note de la session « Biens invisibles ».

### ⚠ LOT 0 — ETAT AU 06/10, ET UNE DETTE LAISSEE SCIEMMENT

```
0a  ✅ FAIT  phase2/checks/chemin_immediat_paquet.py   (113596c)
    eprouve DANS LES DEUX SENS : vert sur le code sain (4 temoins sur 4),
    ROUGE sur le bug du 05/10 remis en memoire (« TypeError: tuple indices
    must be integers or slices, not str », le message exact).
    ⛔ IL N'EST BRANCHE PAR RIEN. A lancer a la main avant tout changement de
      export_app_payload.py / push_upgrade_to_supabase.py.

0b  ⛔ PAS FAIT, et la sentinelle EXISTAIT DEJA :
       "key": "data.travaux_en_erreur" · table app_console_job
       "params": {"status": "eq.error"} · absolute · max 0 · CRITICAL
    POURQUOI ELLE N'A PAS SONNE LE 05/10 -- la deduplication porte sur l'ETAT,
    pas sur le NOMBRE :
       newly_critical = [r for r in criticals
                         if previous_status.get(r.status_key) != "critical"]
       03/10  1 erreur -> la cle devient critical -> UNE alerte part
       05/10  13 erreurs NEUVES, meme cle -> newly_critical VIDE -> SILENCE
    ⭐ Un critical qui RESTE critical ne realerte jamais, meme si le probleme
      grossit treize fois.
    Le compte precedent est pourtant lisible (_previous_sentinel_count).
    ⚠ MAIS le corriger touche la deduplication de TOUTES les sentinelles, et le
      moniteur tourne toutes les 2 h -> risque de spam. Il faut un garde-fou, et
      c'est une decision sur le systeme d'alerte entier. Arbitrage de Frederic
      du 06/10 : on ne le fait pas maintenant.

0c  ⛔ PAS FAIT (brancher les 3 sentinelles orphelines = editer le run de nuit)

⛔⛔ LA DETTE, A CONNAITRE : TANT QUE LA FILE N'EST PAS VIDE, L'ALERTE SUR LES
   TRAVAUX EST ETEINTE -- pour TOUT, pas seulement le mandat. Elle l'est depuis
   le 01/10. 15 travaux en erreur, par cause reelle :
      12  le bug du 05/10 (TypeError)  -- cause CORRIGEE par 3607d29
           annonces 63158 (x7) · 63156 (x2) · 61895 · 63099 · 63081
       2  « database is locked »        -- annonces 63208 (05/10 06:44), 63158 (01/10)
       1  « Retrait du mandant NON PROUVE pour le contact 603953 » -- le contact
          de TEST, le meme qui pollue les mandants de l'annonce 24113
```

#### Et le diagnostic des 2 « database is locked », mesure le 06/10

```
⛔ CE N'EST PAS UN busy_timeout MANQUANT : il est deja la, timeout=30 (ligne 669),
  avec un commentaire qui documente deja cette panne.

CE QUI TENAIT LE VERROU le 05/10 a 06:44 -- une CHAINE de courtes ecritures :
   06:43:35 -> 06:44:28   registre des liens (app_relation)   53 s
   06:44:28  entretien compromis · 06:44:32 entretien ventes
   06:44:35  redescente des lectures · 06:44:38 registre depuis console
   06:44:39  repartition de commission
   -> chaque etape relache et la suivante reprend. `executescript` a besoin d'une
      fenetre EXCLUSIVE : il ne l'a jamais eue. Allonger les 30 s ne sauverait rien.

⭐ LA VRAIE CAUSE EST EN AMONT : ensure_schema() prend un verrou d'ecriture a
  CHAQUE appel -- 2 465 fois mesurees -- alors qu'il n'a rien a creer. Son script
  (339 lignes, 12 CREATE TABLE IF NOT EXISTS, 14 CREATE INDEX IF NOT EXISTS) coute
  0,000 s quand tout existe, MAIS il contient un INSERT OR REPLACE : il ecrit donc
  toujours.

CORRECTIF IDENTIFIE, NON FAIT (arbitrage du 06/10) :
  ensure_schema(con, seulement_si_manquant=True) sur le SEUL chemin immediat
  -> un controle en LECTURE ; si les 12 tables et 14 index sont la, aucun verrou.
  ⚠ fonction PARTAGEE, 5 appelants -> un PARAMETRE, jamais un changement par defaut.
  ⚠ et les 2 lignes de donnees de reference ne seraient plus reposees a chaque
    retour de fiche (le run de nuit les repose par bootstrap_phase2.py:314).
```

### LOT 1 — les mandants du registre des mandats
```
OU  phase2/sync/mandat_ledger.py , _poser()
  ①  SON entree a des mandants ET le corps n'est pas suspect -> on garde  (24 022)
  ②  SINON, et SEULEMENT si nature = VENTE -> NOS relations
         457 corps empruntes  -> 457 reparees
         258 vides (societes) -> 228 reparees, le correctif societes EST deja la
  ③  si nos relations ne savent pas -> VIDE + sortie en LISTE                 (30)
  ⚠ LOCATION / GESTION / INCONNUE : on ne touche a rien (decision du 26/08)
  ⛔ PAS DE TRIEUR, et AUCUN traitement special pour les 48 : refuse par principe
     (une personne peut etre mandante de DEUX mandats du meme bien -- 10 cas sur 39).
     Les noms muets sont deja filtres, et plusieurs mandants est le cas de 47,5 %
     du registre. Le recours standard suffit.
  ⭐ ET ON PRIORISE : les 457 d'abord (un nom FAUX s'affiche aujourd'hui),
     les 258 ensuite (un vide, pas un mensonge).

⚠ DEPLACEMENT DANS LE RUN : aujourd'hui l. 839 app_mandat PUIS l. 922 app_relation
  -> deplacer app_mandat APRES app_relation.
  VERIFIE : rien entre les deux ne lit app_mandat (relation_ledger ne le cite que
            dans ses commentaires). Sans effet de bord.
```

### LOT 2 — le montant et le prix
```
2a  le FRONT lit le prix dans l'index de l'annonce (actif -> archive -> historique)
    mesure : 24 313 / 24 491 trouves = LA COUVERTURE ACTUELLE, 1 seule divergence
    100 % des 24 452 annonces du registre sont dans au moins un index, 0 orpheline
    ⭐ l'ecran fait .select('*') -> aucune requete ne casse
2b  l'export cesse de poser montant et prix dans le registre
2c  les colonnes tombent, local puis Supabase, avec re-GRANT
⛔ JAMAIS 2c avant 2a : un select= nommant une colonne absente fait echouer TOUTE
   la requete en PostgREST (mesure du 06/10)
```

### LOT 3 — la derniere porte ou NOUS utilisons l'identifiant
```
normalize_source.py , upsert_mandats()
   relation_items[mandat_id]  ->  relation_items[(annonce, numero)]
le code le prescrit lui-meme. Sa « limite connue » visait 1 cas en juillet :
il y a 483 identifiants partages aujourd'hui, et 19 lignes dans la zone a risque.
```

### LOT 4 — les archives sans detail
```
452 annonces du registre sans AUCUN detail -- toutes ARCHIVEES
371 lignes sans date de mandat (origine='annonce')
⚠ PAR PETITS LOTS : c'est ce geste qui a fait bannir l'IP
   (memoire `rattrapage-documents-bannissement-ip`)
```

### L'ORDRE
```
LOT 0 -> LOT 1 -> LOT 2a -> LOT 3 -> LOT 2b -> LOT 2c -> LOT 4
```
**LOT 1 avant LOT 2** : tant que `app_mandat` porte de faux mandants, faire lire la vue
depuis lui deplacerait le defaut au lieu de le corriger.

---

## 6. CE QUI RESTE DEHORS

```
⬜  40 lignes dont personne ne connait les mandants
⬜   2 annonces sur 39 ou une entree n'a pas ses mandants
⬜   1 cas HUMAIN : mandat n° 17842 de l'annonce 41629 -- deux CHARBONNIER, deux
    montants (59 000 / 53 000), meme date. Le registre a pris Annette / 53 000,
    rien ne prouve que c'est le bon.
⬜  2 numeros brules chez Hektor : 63073, 63132
⬜  UN CONTACT DE TEST dans les mandants de l'annonce 24113 : « Mme. CLAUDE
    TESTCLAUDE » (603953, l'essai L4-b du 21/09). Ce n'est pas un defaut de mandat :
    c'est un contact d'essai a nettoyer, comme les annonces 63146 et 63147.
⬜  le defaut de Hektor continue : ~60 lignes/mois. MAIS depuis septembre elles
    arrivent en montant VIDE, plus jamais emprunte (41 % en mars -> 0 % en septembre),
    et apres le LOT 1 elles recoivent leurs mandants seules, sans intervention.
⬜  DETTE notee : le cote annonce ne porte AUCUN numero de contact. Pour des mandants
    cliquables depuis la fiche annonce, il faudra y poser l'equivalent de mandants_json.
```

---

## 7. LES CINQ CHIFFRES QUE J'AI ANNONCES PUIS RETIRES

> A ne pas ressortir.

```
« 2 320 trous a combler »        -> des LOCATIONS, deja ecartees. Le perimetre est 715.
« 35 fusions de mandat »         -> mesure sur hektor_mandat qui ACCUMULE. La source
                                    du registre n'en porte que 4, dont 1 douteux.
« 87 % puis 94 % de collision »  -> calcule sur la colonne `famille`, qui est une
                                    HEURISTIQUE sur le libelle de type, pas une lecture.
                                    Refait sur les dates : 453 / 469 = 97 %.
« le numero est par agence »     -> vrai AVANT ~2015 seulement. Au-dessus de 18 000 :
                                    0 doublon de numero.
« famille est un artefact »      -> FAUX. Elle capte une vraie signature de systeme :
                                    HEKTOR = codes SIMPLE/EXCLUSIF/ACCORD,
                                    PROTEXA = phrases francaises. Et la bascule VENTE
                                    est datee : HEKTOR s'arrete 2026-02, PROTEXA
                                    demarre 2026-01.
```

⚠ **Et la lecon de methode, payee trois fois en deux jours** : *mesurer sur la BONNE
source*. `hektor_mandat` accumule, `mandats_json` dit le present, la colonne `famille`
devine. Trois fois j'ai conclu sur la mauvaise.
