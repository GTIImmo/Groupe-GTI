# PROMPT DE REPRISE V2 — LE CHANTIER CLASSEUR, AVEC LE RAPPORT ET LE PATCH DE L'AUTRE SESSION

> **Écrit le 19/11/2026 vers 00:30**, à la demande de Frédéric, pour une session neuve
> (Opus 5.5 en version Max). Il remplace, comme document de tête,
> `notice/PROMPT_REPRISE_CHANTIER_CLASSEUR_2026-11-18.md` (le « V1 »), **qui reste à lire** :
> le V2 ne recopie pas ses sections stables, il les désigne.
>
> ⛔ **La source de vérité reste `notice/PLAN_CHANTIER_CLASSEUR_2026-10-28.md`.**
> Ce document est une porte d'entrée, pas une décision.
>
> ⛔ **Tout l'état chiffré ci-dessous a été MESURÉ en lecture seule le 19/11 vers 00:00**,
> chez Supabase et dans le dépôt. Aucune écriture n'a été faite pour l'écrire.

---

## 0. CE QUE FRÉDÉRIC DEMANDE, DANS SES MOTS

> *« Peux-tu me faire un prompt encore pour reprendre le chantier de la même manière que
> tout à l'heure mais cette fois avec toutes les notes etc… artefact et le rapport de
> l'autre chat et le patch proposé. Après avoir fait son propre calcul il utilisera le
> rapport pour comparer et encore affiner le patch, puis il me fait une explication claire.
> Ensuite il faut reprendre les autres étapes jusqu'à la fin. »*

Et sa demande d'origine, du 18/11, qui n'a pas changé :

> *« D'abord faire un audit de la situation actuelle de ma base, data serveur et apps au
> sujet de ce chantier, ensuite un audit par lui-même entre le Sheet et mon registre des
> transactions pour qu'il me donne son verdict. Il doit être capable, avec ma data, le Sheet
> et le classeur modelo, de trouver pour chaque ligne du Sheet son dossier de transactions,
> donc trouver nos erreurs et finir le rapatriement. »*

Et son avertissement, à prendre au mot :

> *« Attention au geste, consulte le projet, nous avons rencontré beaucoup de problèmes avec
> certaines écritures. »*

**L'ordre des quatre temps est explicite, et il ne s'inverse pas** : ton calcul d'abord,
la comparaison ensuite, l'affinage du patch après, l'explication enfin. Puis les étapes
suivantes.

---

## 1. ⛔ CE QUI NE SE DISCUTE PAS

- **Accord explicite de Frédéric, OBLIGATOIRE et à chaque fois**, avant : toute écriture en
  base de production · toute écriture chez Hektor (créer, modifier, supprimer) · tout run ou
  rattrapage · tout redémarrage de service · tout déploiement · tout geste irréversible.
  Lecture, mesure et audit : tu enchaînes sans demander.
- **Écrire uniquement en français.** Même les petites phrases.
- **Pas de tableaux** dans les messages qui lui sont adressés. Phrases et listes courtes.
- **L'identité d'un administrateur ne s'écrit JAMAIS sur un document** produit par l'app.
- **Ne rien écraser** : additif et chirurgical, jamais de remplacement massif.
- **Stager fichier par fichier.** Jamais `git add .` (des dizaines de fichiers non suivis
  traînent dans le dépôt). **Relire le stage juste avant le commit**, et **relire la liste à
  pousser juste avant le push**.
- **`git commit -m` n'existe plus** : tout message de commit passe par un fichier et `-F`.
- **Ne jamais décider seul un périmètre.** Ce qu'il signale est un symptôme, jamais la limite
  du sujet — mais l'élargir est SA décision.
- **Jamais `tail -f` sur un journal du run.** **Ne jamais lancer le worker pour l'inspecter.**
- Une autre session peut travailler en parallèle : **relire `git log` avant d'écrire.**

---

## 2. L'ORDRE DE LECTURE — les sept pièces, et ce que chacune apporte

**À lire dans cet ordre, avant le premier calcul :**

1. **`notice/PLAN_CHANTIER_CLASSEUR_2026-10-28.md`** — la source de vérité (≈ 361 Ko ; ne
   jamais lire en entier, ouvrir par section). La règle du chantier et les sept gardes y
   vivent.
2. **`notice/PROMPT_REPRISE_CHANTIER_CLASSEUR_2026-11-18.md`** (le V1, 576 lignes) — ses
   sections **1, 3, 5, 6, 10 et 11** ne sont PAS recopiées ici et restent la référence : les
   règles, l'accord circulaire, **les sept lecteurs qu'une transaction sans numéro Hektor
   réveille**, ses 14 arbitrages avec ses mots, les adresses et **18 pièges déjà payés**.
3. **`notice/AUDIT_INDEPENDANT_CLASSEUR_2026-11-18.md`** — le rapport de l'autre session
   (341 lignes). ⚠ **À n'ouvrir qu'APRÈS ton propre calcul** (voir § 5), et avec les trois
   réserves du § 7 en tête.
4. **`notice/AUDIT_INDEPENDANT_CLASSEUR_VERDICTS_2026-11-18.csv`** — 350 lignes jugées, une
   par ligne du Sheet : verdict, décision de chaque lien, transaction à rattacher, preuve,
   raison, conséquences, question pour Frédéric. Séparateur `;`, en-tête avec BOM.
5. **`notice/AUDIT_INDEPENDANT_CLASSEUR_OPERATIONS_GEL_2026-11-18.csv`** — les 141 opérations
   du patch, une par ligne (`operation;id_unique;ligne_classeur;role;de;vers;genre_cible;…`).
6. **`supabase/patch_correction_gel_audit_independant_2026-11-18.sql`** (+ `_INVERSE`,
   `_REPETITION`) — le patch **DORMANT**. Voir § 8.
7. **La page d'arbitrage de Frédéric** : `https://claude.ai/artifact/PRXmPfRhMSX77Cm9F5WcL7`.
   Ses choix vivent dans la base de cette page, **collection `reponses2`**, un document par
   question. Ils sont reproduits au § 6 avec leur état réel, mais **les relire à la source** :
   il peut en avoir ajouté.

**Les notes qui comptent aussi** (ouvrir à la demande, pas d'office) :
`notice/AUDIT_COMPROMIS_CLOTURES_MALGRE_LA_VENTE_2026-11-18.md` ·
`notice/LECONS_DE_METHODE.md` (31 leçons, **numéros à ne jamais renuméroter**) ·
`CLAUDE.md` (la porte d'entrée du dépôt) ·
et la mémoire projet : `C:\Users\admin\.claude\projects\C--Hektor\memory\`, en particulier
`audit-independant-classeur-18-11.md`, `chantier-classeur-la-regle-historique-et-les-7-gardes.md`,
`accord-circulaire-quand-on-a-deja-pose-la-source.md`,
`apparieur-v2-second-appariement-du-classeur.md`.

⚠ **Le CLAUDE.md annonce de faux horaires de nuit** : il dit le run à 05:00 et la descente à
07:45. La vérité mesurée est **04:00** (tâche `GTI Quotidien`) et **06:45** (`GTI Descente`).
Non corrigé au 19/11 : ne pas calculer une fenêtre sur le CLAUDE.md.

---

## 3. ⛔⛔⛔ LE PIÈGE N° 1 — L'ACCORD CIRCULAIRE

**Nous avons déjà posé 15 211 valeurs du classeur dans la base.** Comparer le Sheet à notre
registre aujourd'hui mesure donc, pour une large part, **un accord que nous avons fabriqué
nous-mêmes**. C'est arrivé le 17/11 : **874 des 897 « accords » étaient circulaires.**

**Les quatre règles d'indépendance, à tenir pendant tout ton calcul :**

1. Ne jamais lire le gel (`app_classeur_lien`) **pour choisir** — seulement après, pour
   comparer.
2. **Aucune valeur posée par nous ne sert de preuve** : les colonnes `*_app`
   (`honoraires_entree_app`, `honoraires_sortie_app`, `charge_commission_app`,
   `date_annulation_app`, `motif_annulation_app`, `numero_facture_app`, `vente_reglee_app`,
   `numero_mandat_app`), les notes et conditions d'origine « classeur », la répartition
   `classeur_reconstitue`, le carnet des mandats « classeur », les avis.
3. **Les 190 transactions créées depuis le Sheet sont retirées des candidats** (colonne
   `transaction_origine = 'classeur'`) : elles sont circulaires par construction.
4. La date d'une offre est **sa première proposition** (`propositions_json`), pas sa colonne
   `date`. Un refus ou une acceptation datés **à partir du 11/11/2026** sont NOS gestes et ne
   prouvent rien.

**Le témoin d'AVANT existe** : les 11 sauvegardes datées en base. Elles disent ce que la base
portait avant nos poses.

---

## 4. L'ÉTAT MESURÉ — 19/11/2026, vers 00:00, en lecture seule

```
LE SHEET            4 794 lignes dans notre table des lignes (le Sheet en porte 4 795 :
                    une ligne est nee depuis -- regle n° 1 : rien a reprendre dessus)
L'APPARIEMENT       4 703 lignes liees (98,1 %) . 91 sans aucun lien
LE GEL              12 787 liens . 0 transaction prise par deux lignes . 0 paire en double
                    277 liens « a valider » = 104 LIGNES seulement, toutes de l'etage 9
                    9 liens casses, benins (Hektor ne porte plus la transaction, nous si)
LE REGISTRE         31 356 transactions, chez Supabase ET en local (les deux d'accord)
                    190 creees depuis le Sheet (etaient 195 : 5 doublons retires le 18/11)
RESTE A POSER       207 lignes non posees . 36 lignes qu'il a tranchees dont rien n'est pose
                    . les 13 arbitrages du § 6 . C6, C10, AA, U/X, AC/AE/AK . les signes
                    non decodes de la colonne F
```

**Deux faits d'architecture à ne pas confondre, et ils ont coûté cher :**

- ⛔⛔ **`app_affaire_ledger` : le LOCAL est le maître**, Supabase la copie. Le push de 04:00
  est **« delete-never »** : il renvoie toutes les lignes locales par upsert, sans jamais
  supprimer. Une transaction retirée **d'un seul côté remonte** — et **sans sa marque**, car
  `transaction_origine` figure dans `COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS`
  (`phase2/sync/affaire_ledger.py`). Une ligne de la plage app (≥ 1 000 000) sans numéro
  Hektor et sans marque est attrapée par le filet `poserNumerosManquants` du worker, qui lui
  collerait le numéro d'une offre Hektor existante. ➡ **Une transaction de la plage app se
  retire DES DEUX CÔTÉS, dans la même fenêtre**, ou par le journal
  `app_affaire_supprimee`, que le run applique AVANT de pousser.
- ⭐⭐ **`app_classeur_lien` (le gel) : c'est l'inverse. SUPABASE est le maître**, le local
  n'est qu'une copie **refaite à chaque descente** (`phase2/sync/pull_from_supabase.py`
  découvre les tables par l'OpenAPI ; il refuse d'écrire dans une table qu'il n'a pas créée).
  Le gel local portait 12 792 liens contre 12 787 en haut le 18/11 à 23:49 : **c'est l'état
  de la veille, pas une remontée qui menace.** Et **aucun run de nuit, aucune tâche planifiée
  n'écrit dans le gel** → **aucune fenêtre ne se ferme à 04:00 pour le patch du § 8.**

---

## 5. ⭐⭐⭐ LA MISSION — quatre temps, dans cet ordre

### Temps 1 — ton propre calcul, SANS le rapport de l'autre session

Refais l'audit **par toi-même**, avec les quatre règles du § 3. N'ouvre ni le rapport, ni le
CSV des verdicts, ni le patch tant que ton propre résultat n'est pas arrêté et écrit.

Ce que tu dois produire, par ligne du Sheet : **le dossier et les transactions que TU
désignes**, avec la preuve qui te fait conclure, et un degré de certitude.

**Les familles de preuve admises** — toutes venues de Hektor, de MODELO ou de la ligne
elle-même :

```
lien     l'annonce que L'AGENCE a nommee : lien d'administration (id=), et surtout
         ⭐ la REFERENCE NETTY (VM.../VA..., colonne B ou lien CRM) = le NUMERO DE
         DOSSIER HEKTOR -> l'annonce. C'est le pont le plus fort : 646 lignes.
mandat   le numero du Sheet porte par une transaction, ou le registre des mandats
modelo   le numero du Sheet dans MODELO -> sa reference produit -> l'annonce
acq      un NOM DE FAMILLE d'acquereur (les prenoms ne comptent pas)
vend     un NOM DE FAMILLE de vendeur (mandants, registre, MODELO)
dates    ⭐⭐ LA PREUVE INTERNE, celle qui tranche : une transaction du bon genre
         AU JOUR PRES
prix     a 1 % pres . ville
```

⚠ **Les liens « neosphere » et « rodacom » (3 800 lignes) portent un identifiant ÉTRANGER** :
ils ne désignent rien chez nous. Ne pas les prendre pour des liens.

⛔⛔ **UN RATIO ENTRE DEUX SOURCES NE VAUT RIEN TANT QU'ON N'A PAS VÉRIFIÉ QUE LES DEUX
NOMBRES PARLENT DU MÊME BIEN.** Deux fiches d'arbitrage du 18/11 étaient fausses pour cette
seule raison, et c'est Frédéric qui l'a vu les deux fois : un « 81,7 % » divisait les
honoraires d'un bien par le prix d'un autre (la ligne 3938 pointe sur **deux annonces**,
9769 et 39836) ; un « 72 % » faisait pareil (le vrai taux est 4,7 %, rien d'anormal).
➡ **Avant tout ratio, afficher les DEUX montants ET l'annonce de chacun.** Un taux aberrant
est d'abord le symptôme d'un appariement faux, pas d'une valeur fausse.

⭐ Un seul signal faible — un nom de famille seul, ou un numéro de mandat seul — **ne suffit
pas**. C'est le motif de la plupart des liens faux du gel.

### Temps 2 — la comparaison avec le rapport de l'autre session

Alors seulement, ouvre le rapport, le CSV des verdicts et le CSV des opérations. Compare
**ton** résultat au sien, ligne par ligne, et classe :

- **vous êtes d'accord** → le lien est solide, deux chemins indépendants y mènent ;
- **vous divergez** → c'est le vrai gisement. Dis **lequel des deux a la meilleure preuve**,
  et pourquoi. N'adopte pas son verdict parce qu'il est écrit.
- **il a jugé, tu n'as rien** (ou l'inverse) → dis-le, ne comble pas le trou par politesse.

⛔ **Ne prends pas son rapport pour une mesure.** Il a été écrit par une session qui pouvait
se tromper, et trois trous y ont déjà été trouvés (§ 7). Deux audits indépendants qui
convergent valent une preuve ; un audit recopié n'en vaut aucune.

### Temps 3 — affiner le patch

Reprends `supabase/patch_correction_gel_audit_independant_2026-11-18.sql` et produis-en une
version affinée, **toujours dormante** : les trois corrections du § 8 y sont obligatoires, et
tes propres divergences du temps 2 s'y ajoutent ou s'en retirent.

⛔ **Les lignes marquées INCERTAIN ne se touchent pas** : elles attendent sa réponse.
⛔ **Les 18 lignes du patch qui portent une question ouverte** (il le dit lui-même) : soit tu
les sors du patch, soit il y répond d'abord. On ne tranche pas à sa place.

### Temps 4 — l'explication claire

Puis, et seulement puis, **une explication en français simple** : ce que tu as trouvé par
toi-même, où tu rejoins l'autre session, où tu la contredis et pourquoi, ce que le patch
affiné fait exactement, ce que ça pourrait casser ailleurs, comment on revient en arrière,
et comment on vérifiera. Pas de tableaux. Et **demander son accord** avant le moindre
`insert`, `update` ou `delete`.

---

## 6. ⭐⭐ LE REGISTRE DE SES 13 ARBITRAGES, ET LEUR ÉTAT RÉEL

**Ce registre n'existait pas, et son absence est la cause de cinq oublis.** Ses réponses
vivent dans la base d'une page web, le travail vit dans des fichiers et des patchs, et rien
ne reliait les deux : chaque session prenait un bout du sujet et le faisait bien, sans que
personne tienne la liste. **Le voici. Il se tient à jour à chaque geste.**

Relevé dans `reponses2` le 19/11 vers 00:10, et confronté au rapport, au CSV et à la base.

**✅ TENU — le patch fait exactement ce qu'il a décidé (1)**

- `L173-TR42PT5H-lien` → **« deplacer-27195 »**. Le patch retire le lien vers 27196 et pose
  le compromis **27195** sur la ligne 173. Verdict du juge : faux, confiance certaine.
  *(bien 53398 : l'offre 27196 et le compromis 27195 étaient croisés entre deux acheteurs)*

**✅ SON DOUTE CONFIRMÉ par un audit qui ne le connaissait pas (2)**

- `L3938-61OW86CS-commission` → **« ecarter »**, avec son mot : *« et donne moi le dossier et
  annonce chez nous rattaché »*. Verdict : **partiel**, et le patch **retire le lien** du
  compromis 4496.
- `L3991-NEFHS7JI-commission` → **« annulee-donc-non »**, avec son mot : *« Il y a une erreur
  sur l'annonce c'est pas le bon bien »* · et `L3991-NEFHS7JI-date` → **« doute-appariement »**.
  Verdict : **faux**. Le patch retire 26395 et 26397, et range la ligne parmi les sept qui
  perdent tout lien.

**⚠⚠ À MOITIÉ FAIT — sa décision dit deux gestes, le patch n'en fait qu'un (2)**

- `L3464-1ESJE28Q-lien` → **« defaire-et-creer »**. Le patch **défait** (12952, 12953) et
  **ne crée rien**.
- `L3579-8Q3LHGZ4-lien` → **« defaire-et-creer »**. Le patch **défait** (8321, 8322) et
  **ne crée rien**.
  ➡ L'audit les classe parmi les sept lignes qui restent sans aucun lien, *« faute d'affaire
  chez nous »*. Ce n'est pas un désaccord de fond : il n'existe chez nous aucune transaction
  à rattacher. Mais **créer reste entièrement à faire**, et c'est un geste d'une autre nature
  (comme C5). ⛔ Jouer le patch seul laisse ces deux lignes **orphelines au lieu de réparées**.

**⬜ NON JUGÉES par l'audit, mais PAS contredites (3)**

- `L1401-74IL9C8F-date` → **« poser »** · `L1135-QH6672TZ-date` → **« poser »** ·
  `L17-Y8O4NJSY-commission` → **« poser »**.
  Absentes du rapport, du CSV et du patch — et c'est **légitime** : mesuré en base, leurs
  liens portent **6 à 8 familles de preuve**, confiance « sûre », étages 1 et 2. Elles
  n'étaient pas dans le lot suspect. Le patch les laisse intactes, et `Y8O4NJSY` n'est pas
  dans la liste des commissions dont la pose doit être retirée.
- ⛔⛔ **MAIS LE BLOCAGE DES DEUX DATES D'OFFRE TIENT, et il n'a pas été levé :**
  - **aucune colonne n'existe** pour accueillir une date d'offre venue du classeur. La seule
    cible serait `date`, que le run relit chez Hektor chaque nuit et à qui la protection est
    **nommément refusée** (`R2_JUGES_SUR_LE_REGISTRE`, `phase2/sync/affaire_ledger.py`) ;
  - ⭐⭐ **et le journal de l'offre porte LUI-MÊME la mauvaise année** — mesuré par
    `app_dossier_jour_date_transaction(kind, date, propositions_json::jsonb, affaire_id)` :
    l'offre **23488** rend `2002-01-31`, l'offre **24448** rend `2020-08-07`. **La faute est
    CHEZ HEKTOR**, donc aucun des cinq lecteurs alignés le 12/11 ne la corrigera, et poser
    chez nous ne rendrait rien de visible.
  ➡ **Décision à lui demander : créer une colonne dédiée, ou corriger chez Hektor ?**

**⬜ PAS ABORDÉES DU TOUT par le rapport (5)**

- `REGLE-transaction-cible` → **« toutes »** (poser sur **toutes** les transactions de la
  chaîne). ⛔ **Cette règle contredit un script déjà joué** :
  `phase2/checks/c2_generer_commissions_2026-11-17.py` pose sur **la transaction LA PLUS
  AVANCÉE** (vente > compromis > offre), et **66 lignes sont déjà posées ainsi** : 14 sur une
  vente, 8 sur un compromis, 44 sur une offre. Sa règle triple le périmètre **et change
  l'existant**. ➡ **À lui demander : repasse-t-on sur les 66, ou « toutes » ne vaut-il que
  pour la suite ?**
- `OFF4281-36794-reparer` → **« reparer »**. Une **écriture chez Hektor** sur l'offre 4281.
  Rien n'est fait, rien n'est préparé. ⛔ Accord obligatoire, et lire d'abord
  `offre-acceptee-hektor-refuse-en-silence` : **modifier une offre acceptée, Hektor la refuse
  en silence.**
- `REFUS5-classeur-contredit` → **« auditer »**, répondu à 14:19:50. Le script
  `phase2/checks/c_refus_11_11_contre_le_classeur_2026-11-18.py` existe, mais il a été écrit
  à **11:19, soit AVANT sa réponse** : l'audit n'a donc **pas** été refait à sa demande.
  ➡ **À reprendre.**
- `CP8-clotures-malgre-vente` → **« plus-tard »**. Rangé par lui, pas un oubli. Son audit
  existe : `notice/AUDIT_COMPROMIS_CLOTURES_MALGRE_LA_VENTE_2026-11-18.md`.

---

## 7. LE RAPPORT DE L'AUTRE SESSION — ce qu'il vaut, et ses trois trous

### Ce qui est solide, et vérifié indépendamment le 19/11

La méthode est juste (appariement sans le gel, quatre règles d'indépendance), le volume est
réel (350 lignes jugées, 107 contre-expertises, 4 renversements), et **ses comptes tombent
juste** : 55 retraits et 109 ajouts comptés dans le fichier, la garde « 12 787 liens » exacte,
**0 transaction prise par deux lignes aujourd'hui** (son contrôle global ne plantera donc pas
pour une cause étrangère), **0 doublon** dans ses deux listes, et **les deux listes de
retraits sont rigoureusement identiques** (même empreinte). L'inverse juge sa part, la
répétition est en lecture seule.

**Ses quatre familles d'erreurs du gel sont vraies et utiles :**

1. des liens faux par **un seul signal faible** (un nom, ou un numéro de mandat seul) ;
2. ⭐⭐ des affaires **CROISÉES entre acheteurs successifs d'un même bien** — sur un bien
   revendu ou repris après annulation, le gel a donné à une ligne l'offre de l'acheteur
   **suivant** (11 paires nommées) ;
3. ⛔ **25 des 190 transactions créées par C5 copient une transaction Hektor** du même bien,
   du même genre, au jour près — même cause que les 5 doublons du 18/11 : la colonne `date`
   abîmée par les gestes de masse du 11-12/11 ;
4. des valeurs (C2, C3, C4) **posées sur la transaction d'une autre affaire** via un lien faux.

Et la cinquième, qui n'est pas une erreur d'appariement mais un effet de bord : **la nuit du
17 au 18/11 a coupé 136 transactions créées de leur dossier** (le chaînage est une déduction
refaite chaque nuit ; une offre refusée ou un compromis annulé ouvre sa propre chaîne) → **255
lignes ont désormais plusieurs étiquettes possibles**, ce qui bloque l'étape 5.2. Remède
possible : `phase2/sync/rattachements_manuels.csv` (lu si `APP_CHAINAGE_RATTACHEMENT_MANUEL=1`)
— ⛔ **mais ce fichier est une décision : on n'y ajoute JAMAIS une ligne sans lui.**

### ⛔ Les trois trous, mesurés le 19/11

1. ⛔ **Le rapport renvoie SIX FOIS à un « § 5 ter » qui n'existe pas dans le document.**
   C'est là qu'il annonce **les 33 questions**, les valeurs mal posées une par une (20
   transactions Hektor et 11 créées par C5) et la mesure du run, des workers et de l'app.
   ➡ **Réclamer ces pièces, ou les refaire.** Le fichier était **modifié et non commité** au
   19/11 00:20 (trois commits le portent déjà : `96ec780`, `42a44b8`, `260340a`) : l'autre
   session était peut-être en train de les écrire.
2. ⚠ **Le patch touche 87 lignes du Sheet, dont 18 portent une question ouverte.** Le jouer
   tel quel tranche à la place de Frédéric sur ces 18.
3. ⚠ **Ses chiffres se sont corrigés en cours de route** — « 10 copies C5 retirables » devenu
   11, « 2 des 15 tenues par des lignes incertaines, pas non jugées », « 190 et non 195 »,
   « 207 non posées et non 202 ». Ce n'est pas une faute, c'est un document vivant : **ne
   jamais citer un de ses chiffres sans le remesurer.**

---

## 8. LE PATCH — ce qu'il fait, et les TROIS corrections à y porter

**Ce qu'il fait** : il ne touche **que le gel**. Une garde (le gel doit porter exactement
12 787 liens, et chacun des 55 liens à retirer doit exister), une **sauvegarde datée fermée
dès sa naissance** (`app_classeur_lien_avant_audit_independant_20261118`, avec `revoke` sur
`public`, `anon` **et** `authenticated` — le `revoke from public` seul ne ferme pas
`authenticated`), **55 retraits**, **109 ajouts**, puis le contrôle **dans la même
transaction** : le compte attendu (12 841), l'exclusivité que la base ne garantit pas, le
genre de chaque cible, la taille de la sauvegarde, et **le témoin inverse** (les liens non
visés sont identiques).

**Ce qu'il ne fait pas, volontairement** : il ne touche ni les transactions (les copies de C5
ne se retirent qu'après, quand plus aucun lien ne les vise), ni les valeurs posées par
C2/C3/C4/C8/C9 sur une mauvaise transaction, ni Hektor, ni les 8 lignes incertaines.

⛔⛔ **IL PORTE SON `commit;` : il ne se joue JAMAIS « à blanc ».** Un patch avec `commit;`
joué pour voir **se commite**. C'est arrivé le 13/11.

### ⛔ Correction 1 — il détourne deux colonnes de mesure. À corriger avant de jouer.

Mesuré en base : `etage` (text) porte aujourd'hui un **libellé court et normalisé** — « 1
mandat seul » (8 255 liens), « 2 mandat + acquéreur » (2 836), « 9 sans mandat (acquéreur +
vendeur) » (245), « 0 creee par C5 depuis cette ligne » (190)… — et `preuves` (smallint)
porte le **NOMBRE de familles de preuve**, de 2 à 8.

Le patch met, dans ses 109 ajouts :
- dans `etage`, **une phrase de 160 à 173 caractères, tronquée en milieu de mot** (« qui doit
  passer à 474 », « Arrivé chez nous aprè », « et ses 195 ») ;
- dans `preuves`, **0** — or 0 veut déjà dire autre chose : « créée par C5, aucune preuve ».

**Conséquences** : 109 liens que l'audit déclare « sûrs » seraient comptés comme **sans
preuve**, et tout regroupement par étage deviendrait illisible (109 étages uniques).

⭐ **La cause est intéressante et se répétera** : le patch produit une chose **nouvelle** — un
lien dont la preuve est une **phrase rédigée par un juge**. La table du gel a été dessinée
pour un apparieur automatique et **n'a pas de case pour ça**. Au lieu de dire « il manque une
case », la phrase a été mise dans la case la plus proche. *Un chemin provisoire n'est pas une
place définitive.*

**Le remède, sans risque** : un libellé court et constant dans `etage` (par exemple
« audit independant 18/11 »), le **compte réel** de familles de preuve dans `preuves`, et la
phrase **laissée dans le CSV des opérations**, où elle est déjà et complète. Ou, si la phrase
doit vivre en base, **une colonne pour elle**.

### ⚠ Correction 2 — les 18 lignes à question sortent du patch, ou il y répond d'abord.

### ⚠ Correction 3 — ce qui suit le patch doit être enchaîné, pas abandonné à mi-chemin.

Après le patch, **le lien dit la vérité mais la valeur dit encore le faux** : les valeurs
posées par C2/C3/C4/C9 via les **31 liens qui partent** restent sur la mauvaise transaction.
L'ordre proposé est bon — **ne pas s'arrêter entre les deux**.

### L'ordre des gestes, chacun avec son accord

```
1. le patch du gel, AFFINE (55 retraits, 109 ajouts, les 3 corrections ci-dessus)
2. les valeurs posees via les 31 liens qui partent -> a reposer au bon endroit
3. les 11 copies de C5 qui ne sont plus visees par aucun lien -> retirer DES DEUX
   COTES (Supabase ET local, meme fenetre, ou par app_affaire_supprimee)
4. un 4e tour de jugement pour les 15 copies C5 encore tenues par une ligne
5. creer les transactions manquantes de 1ESJE28Q et 8Q3LHGZ4 (sa decision
   « defaire-et-creer », moitie non faite)
6. le seuil de la sentinelle `data.classeur_ligne_sans_lien` : 92 -> la mesure du jour
   (monitoring/check_gti_health.py, vers la l. 817). Son propre commentaire l'exige :
   « le seuil suit la MESURE du jour, et il est relu a chaque fois qu'on touche au gel ».
   ⚠ C'est une modification de code : elle demande son « vas-y » a part.
7. les 36 lignes qu'il a tranchees et dont RIEN n'est pose . les 207 non posees
8. les 91 lignes sans lien (60 apres le patch) et les 277 « a valider »
```

---

## 9. LES ÉTAPES SUIVANTES — ce qu'il veut enchaîner « jusqu'à la fin »

### ÉTAPE 4 — la porte, et les vagues de reprise

L'écriture passe par **`app_modifier_affaire_optimistic`**, qui **exige** : un utilisateur
connecté admin ou gestionnaire (`is_app_manager_or_admin()` lit `auth.uid()`), un numéro
Hektor, et une transaction **encore présente chez Hektor**. Elle corrige notre registre à
l'instant et pose un travail `change_hektor_annonce_status`.

⛔ **Une « porte sans écran » appelée par un script n'a pas d'utilisateur.** **Qui signe le
geste est à trancher avec lui avant d'écrire 4.1.**

⚠ Et **ce que la reprise enverrait réellement chez Hektor reste à mesurer** : commission,
charge, facture, règlement et annulation **n'ont pas de case chez lui**.

⛔ **La réserve du 13/11 tient** : 14 chaînes du classeur sont **entièrement mortes** chez
Hektor. Une reprise qui exige « présente chez Hektor » ne les touchera jamais.

### ÉTAPE 5 — la bascule

- **5.1 reste à Frédéric** : les Apps Script du Sheet.
- **5.2 (écrire notre identifiant de dossier dans `affair_uuid`)** bute sur **255 lignes qui
  ont plusieurs étiquettes possibles** (§ 7, la scission du 17-18/11), en plus de la réserve
  du 13/11. Deux options à lui soumettre : rattacher à la main les 136 transactions coupées
  (via `phase2/sync/rattachements_manuels.csv`, **sa décision**), ou laisser et **choisir l'étiquette à
  l'export**.

---

## 10. LES ADRESSES — contrôlées une par une le 19/11

**Documents** — `notice/PLAN_CHANTIER_CLASSEUR_2026-10-28.md` ·
`notice/PROMPT_REPRISE_CHANTIER_CLASSEUR_2026-11-18.md` ·
`notice/AUDIT_INDEPENDANT_CLASSEUR_2026-11-18.md` ·
`notice/AUDIT_INDEPENDANT_CLASSEUR_VERDICTS_2026-11-18.csv` ·
`notice/AUDIT_INDEPENDANT_CLASSEUR_OPERATIONS_GEL_2026-11-18.csv` ·
`notice/AUDIT_COMPROMIS_CLOTURES_MALGRE_LA_VENTE_2026-11-18.md` ·
`notice/LECONS_DE_METHODE.md` · `CLAUDE.md`.

**Patchs** — `supabase/patch_correction_gel_audit_independant_2026-11-18.sql` (+ `_INVERSE`,
`_REPETITION`) · `supabase/patch_retirer_doublons_offres_classeur_2026-11-18.sql` (+ `_INVERSE`,
`_REPETITION`) · `supabase/patch_b2_b3_sentinelles_2026-11-17.sql` (les deux vues et la
sentinelle).

**Scripts** — `phase2/checks/apparier_v2.py` (et `_socle`, `_dossier`, `_inventaire`,
`_rapport`, `_tableau`) · `phase2/checks/c2_generer_commissions_2026-11-17.py` ·
`phase2/checks/c_refus_11_11_contre_le_classeur_2026-11-18.py` ·
`phase2/checks/retirer_doublons_classeur_du_local_2026-11-18.py` (le patron d'un geste local :
à blanc par défaut, témoin positif, sauvegarde et retrait dans une seule transaction) ·
`phase2/sync/affaire_ledger.py` (le push, `COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS`,
`R2_JUGES_SUR_LE_REGISTRE`, `appliquer_les_suppressions`) ·
`phase2/sync/pull_from_supabase.py` (la descente) · `monitoring/check_gti_health.py`.

**Tables et vues** — `app_classeur_lien` (le gel) · `app_classeur_ligne_id` (les lignes du
Sheet) · `app_affaire_ledger` (le registre) · `app_affaire_note` · `app_affaire_supprimee`
(le journal des suppressions) · `app_v_classeur_ligne_sans_lien` ·
`app_v_classeur_lien_casse` · `app_dossier_jour_date_transaction(text, text, jsonb, bigint)`.

**La page d'arbitrage** — `https://claude.ai/artifact/PRXmPfRhMSX77Cm9F5WcL7`, collection
`reponses2`.

**Écrire en production** — si le connecteur Supabase tombe, le chemin de secours est
`Console/apply_sql_patch.js` **par le POOLER**.

---

## 11. ⛔ LES PIÈGES, EN PLUS DES 18 DU V1

- ⛔⛔ **Un patch qui porte son `commit;` se commite même « à blanc ».**
- ⛔⛔ **Un compte d'IDENTIFIANTS n'est pas un compte de LIGNES.** Le 18/11 : 41 clés pour
  43 lignes, et une décision perdue.
- ⛔⛔ **Réparer un geste de masse laisse une CICATRICE** : 661 dates déplacées les 11-12/11
  ont fabriqué 5 doublons le 16/11.
- ⛔ **Un zéro ne se croit pas sans témoin positif**, et **une lecture ratée n'est jamais un
  vert**.
- ⛔ **Une table de gel sans clé primaire fait sauter des lignes à la descente.**
- ⚠⚠ **Une mesure LOCALE avant la descente porte l'état de LA VEILLE** (la descente est à
  06:45 ; le gel local avait 5 liens de retard le 18/11 à 23:49).
- ⚠ **Un bien vendu, clos ou archivé n'est plus dans `app_dossier_current`** : zéro ligne
  n'est pas une anomalie.
- ⚠ **`etat_au_classeur` n'est PAS une colonne** : c'est une clé du `payload_json` d'un
  travail, que personne ne lit. Et **`origine` n'est pas dans le ledger**, elle est dans
  `app_affaire_note`.
- ⚠ **Le mur de Hektor** : un quota de VOLUME, 13 000 à 17 000 requêtes par période, et la
  règle de Frédéric est de rester **40 % en dessous**. La nuit en consomme déjà ~4 500.
- ⚠ **Les renvois `l. N` se décalent en silence.** Après toute édition du plan ou de la
  liste : `python phase2/checks/verifier_renvois_liste.py --reparer`, puis **relancer sans
  `--reparer`**.
- ⚠ **Un heredoc Bash casse** sur un document long truffé d'apostrophes : passer par l'outil
  d'écriture.

---

## 12. LA MÉTHODE, À CHAQUE PAS

1. **AUDITER** — le code et la base d'abord, les notes ensuite. En cas de désaccord, **le
   code gagne**, puis le plan, puis les notes.
2. **EXPLIQUER** simplement : ce que j'ai trouvé, ce que je vais faire, ce que ça touche,
   **ce que ça pourrait casser ailleurs**, comment on revient en arrière, comment on
   vérifiera.
3. **ATTENDRE SON « VAS-Y »** pour tout ce qui écrit.
4. **CODER** en additif, derrière un interrupteur quand c'est possible.
5. **CONTRÔLER** — et **dire aussi ce qui a raté**. Un contrôle qui agrège perd ce qui sert à
   agir : donner les identifiants, pas seulement les nombres. Et **un témoin positif** est
   obligatoire : sans lui, un zéro ne prouve rien.
6. **METTRE À JOUR LE PLAN** (la case cochée AVEC sa mesure), **ce registre des arbitrages
   (§ 6)**, et la mémoire projet.

⭐ **Une tâche n'est cochée que si son ÉNONCÉ est couvert.** Une mesure approximative vaut une
mesure fausse.

⭐⭐⭐ **Et la leçon de la journée du 18/11, qui vaut pour toi aussi** : les fautes ne sont pas
dans le raisonnement difficile — elles sont **au bord du travail**. Où l'on pose, ce qu'on
n'a pas écrit, ce qu'on n'a pas bouclé. Plus le lot est gros, plus l'attention part dans le
volume et déserte le rangement. **Garde dix minutes pour le bord.**
