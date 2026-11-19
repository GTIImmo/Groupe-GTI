# PROMPT DE REPRISE V2 — LE CHANTIER CLASSEUR, AVEC LE RAPPORT ET LE PATCH DE L'AUTRE SESSION

> **Écrit le 19/11/2026 vers 00:30**, à la demande de Frédéric, pour une session neuve
> (Opus 5.5 en version Max). Il remplace, comme document de tête,
> `notice/PROMPT_REPRISE_CHANTIER_CLASSEUR_2026-11-18.md` (le « V1 »), **qui reste à lire** :
> le V2 ne recopie pas ses sections stables, il les désigne.
>
> ⛔ **La source de vérité reste `notice/PLAN_CHANTIER_CLASSEUR_2026-10-28.md`.**
> Ce document est une porte d'entrée, pas une décision.
>
> ⛔⛔⛔ **QUI TIENT LE CHANTIER, ET CE QUE L'AUTRE SESSION A FAIT — à lire avant tout le reste.**
> **Le chantier classeur est tenu par la conversation qui a écrit ce dossier**, et c'est d'elle
> que tu prends la suite : l'état mesuré, les règles, le registre des arbitrages, les gardes et
> les pièges ci-dessous viennent de là. **Une autre session, en parallèle, a produit DEUX
> PIÈCES et rien de plus : un RAPPORT d'audit et un PATCH PROPOSÉ.** Ces deux pièces sont
> précieuses — le rapport a trouvé de vraies erreurs, le patch est bien construit — mais ce
> sont **des pièces versées au chantier, pas la conduite du chantier**. Elles se vérifient,
> elles ne se recopient pas : **le patch n'a JAMAIS été joué**, trois trous ont été trouvés
> dans le rapport (§ 7), et son auteur n'a traité ni la règle « toutes », ni l'offre 4281, ni
> l'audit REFUS5, ni la moitié « créer » de deux arbitrages (§ 6).
>
> ⛔ **Tout l'état chiffré ci-dessous a été MESURÉ en lecture seule le 19/11 vers 00:00**,
> chez Supabase et dans le dépôt. Aucune écriture n'a été faite pour l'écrire.

---

## 0 bis. ⭐⭐⭐ LE PROMPT À COLLER DANS LA CONVERSATION NEUVE

> Le texte ci-dessous est **le prompt lui-même**, prêt à copier. Le reste du document est
> ce qu'il demande de lire.

```
Tu reprends le chantier classeur du projet Hektor (depot C:\Hektor\Projet) : le
rapatriement d'un classeur Google Sheet de 4 795 lignes d'affaires historiques vers notre
registre des transactions.

C'EST CE CHANTIER-LA QUE TU REPRENDS, celui conduit par la conversation qui a ecrit le
dossier ci-dessous. Une AUTRE session, en parallele, a seulement produit DEUX PIECES : un
RAPPORT d'audit et un PATCH PROPOSE, jamais joue. Elles se verifient, elles ne se recopient
pas : trois trous y ont deja ete trouves, et cinq de mes decisions n'y sont pas traitees.

AVANT TOUT : lis notice/PROMPT_REPRISE_CHANTIER_CLASSEUR_V2_2026-11-19.md EN ENTIER. Il
porte l'etat mesure, les regles, mes 13 arbitrages et leur etat reel, le rapport d'une
autre session, le patch qu'elle propose, et les erreurs deja trouvees dedans. Puis lis les
pieces qu'il designe a son § 2, dans l'ordre.

TA MISSION, EN QUATRE TEMPS -- ET L'ORDRE NE S'INVERSE PAS :

1. TON PROPRE CALCUL. Refais l'audit par toi-meme : pour chaque ligne du Sheet, trouve son
   dossier et ses transactions chez nous, avec ta preuve et ton degre de certitude. N'ouvre
   NI le rapport de l'autre session, NI son CSV de verdicts, NI son patch, tant que ton
   resultat n'est pas arrete et ecrit. Tiens les quatre regles d'independance du § 3 : ne
   jamais lire le gel pour CHOISIR ; aucune valeur posee par nous ne sert de preuve ; les
   190 transactions creees depuis le Sheet sont hors candidats ; la date d'une offre est sa
   PREMIERE PROPOSITION, et nos gestes du 11/11/2026 ne prouvent rien.

2. LA COMPARAISON. Alors seulement, ouvre son rapport et compare ligne par ligne : ou vous
   etes d'accord, ou vous divergez, et surtout LEQUEL DES DEUX a la meilleure preuve.
   N'adopte pas son verdict parce qu'il est ecrit : trois trous y ont deja ete trouves.
   Deux audits independants qui convergent valent une preuve ; un audit recopie n'en vaut
   aucune.

3. AFFINE LE PATCH. Produis une version affinee du patch de correction du gel, TOUJOURS
   DORMANTE. Les trois corrections du § 8 sont obligatoires -- la premiere est qu'il
   detourne deux colonnes de mesure. Ne touche pas les lignes incertaines, et sors du patch
   les 18 lignes qui portent une question ouverte : on ne tranche pas a ma place.

4. EXPLIQUE-MOI CLAIREMENT, en francais et sans tableaux : ce que tu as trouve seul, ou tu
   rejoins l'autre session, ou tu la contredis et POURQUOI, ce que le patch affine fait
   exactement, ce que ca pourrait casser ailleurs, comment on revient en arriere, et
   comment on verifiera.

PUIS ON ENCHAINE JUSQU'A LA FIN : les 8 gestes du § 8 dans l'ordre, les 5 arbitrages non
traites du § 6 (la regle « toutes », l'offre 4281 chez Hektor, l'audit REFUS5, les deux
transactions a creer), puis l'etape 4 et l'etape 5.

CE QUI NE SE DISCUTE JAMAIS :
- MON ACCORD EXPLICITE AVANT : toute ecriture en base de production, toute ecriture chez
  Hektor, tout run ou rattrapage, tout redemarrage de service, tout deploiement, tout geste
  irreversible. Lecture, mesure, audit : enchaine sans me demander.
- Ecris UNIQUEMENT en francais. PAS DE TABLEAUX dans tes messages.
- Ne rien ecraser : additif et chirurgical, jamais de remplacement massif.
- Stage FICHIER PAR FICHIER, jamais `git add .`. Relis le stage juste avant le commit, et la
  liste a pousser juste avant le push. `git commit -m` n'existe plus : passe par un fichier
  et `-F`.
- Ne decide JAMAIS seul un perimetre. Ce que je signale est un symptome, pas la limite du
  sujet -- mais l'elargir est MA decision.
- Un RATIO entre deux sources ne vaut rien tant que tu n'as pas verifie que les deux nombres
  parlent du MEME bien. Deux fiches etaient fausses pour cette seule raison.
- Un patch qui porte son `commit;` SE COMMITE, meme joue « pour voir ».
- Jamais `tail -f` sur un journal du run. Ne jamais lancer le worker pour l'inspecter.
- Une autre session travaille parfois en parallele : relis `git log` avant d'ecrire.

LA METHODE, A CHAQUE PAS : auditer (en cas de desaccord LE CODE GAGNE, puis le plan, puis
les notes) -> m'expliquer, avec « ce que ca pourrait casser ailleurs » -> attendre mon
« vas-y » -> coder en additif -> controler avec un TEMOIN POSITIF, et me dire aussi ce qui a
rate -> mettre a jour le plan, le registre des arbitrages du § 6, et la memoire projet.

Et la lecon de la journee du 18/11, qui vaut pour toi aussi : les fautes ne sont pas dans le
raisonnement difficile, elles sont AU BORD du travail -- ou l'on pose, ce qu'on n'a pas
ecrit, ce qu'on n'a pas boucle. Garde dix minutes pour le bord.
```

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

**⭐ ÉTAT APRÈS L'AUDIT V2 ET LE PATCH AFFINÉ — 19/11 vers 02:30** *(rien n'est joué ; `reponses2`
relue à 00:50 : toujours 13 documents, aucun ajout)* — `notice/AUDIT_INDEPENDANT_V2_2026-11-19.md` :

- `L173-TR42PT5H-lien` « deplacer-27195 » → **le patch affiné le fait** (ajoute 27195, retire 27196 ;
  27196 va à 739a0db1). Mon calcul indépendant donne la même chose.
- `L3938-61OW86CS` « ecarter » → **le patch affiné retire 4496** ; mon calcul met la ligne sur
  l'annonce 39836, offre 19130 (STRIPOLLI / STRIPPOLI : une faute de frappe).
- `L3991-NEFHS7JI` (×2) → **le patch affiné retire 26395 et 26397** ; mon calcul trouve son bien :
  l'annonce **55001** (mandat 3576), SANS transaction chez nous — la vente AKSU est sur le lot voisin
  54999 (ligne 82TBULHC).
- `L3464-1ESJE28Q` et `L3579-8Q3LHGZ4` « defaire-et-creer » → le patch affiné **défait** ; mon calcul
  confirme les biens 9194 et 46472, sans transaction. ⛔ **Créer reste à faire** (geste 5).
- `L17-Y8O4NJSY`, `L1401-74IL9C8F`, `L1135-QH6672TZ` « poser » → hors du gel ; mon calcul confirme
  les trois appariements (Y8O4NJSY : 3661/3660/3662 ; 74IL9C8F : l'offre à 7 305 jours, « 2002 pour
  2022 ») ; ⛔ le blocage des deux dates d'offre tient.
- `REGLE-transaction-cible` « toutes », `OFF4281`, `REFUS5`, `CP8` → **inchangés, non traités**.

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

---

## 13. ⭐⭐⭐ LES DONNÉES, EN DUR — pour n'avoir rien à redécouvrir

> Tout ce qui suit a été **extrait et recompté le 19/11/2026 vers 01:00** du patch, du CSV
> des verdicts et de la base, par la session qui tient ce chantier. **Ce sont des données,
> pas des conclusions** : elles servent à partir vite, et chacune se remesure avant un geste.

### A. Les comptes, mesurés chez Supabase le 19/11 vers 00:00

```
lignes du Sheet connues (app_classeur_ligne_id)        4 794
lignes liees                                           4 703      (98,1 %)
lignes sans aucun lien                                    91
liens du gel (app_classeur_lien)                      12 787
liens « a valider »                                      277      = 104 LIGNES
liens casses (vue app_v_classeur_lien_casse)               9      benins
transactions du registre (app_affaire_ledger)         31 356      local ET Supabase
transactions creees depuis le Sheet                      190      transaction_origine='classeur'
transactions prises par DEUX lignes                        0      l'exclusivite tient
paires (ligne, transaction) en double                      0
```

### B. Les étages du gel, et ce que portent `etage` et `preuves` AUJOURD'HUI

⛔ C'est la mesure qui fonde la **correction 1 du § 8**. `etage` est un libellé court et
normalisé, `preuves` un compte de 2 à 8 — sauf pour les 190 liens de C5, à 0.

```
1 mandat seul                                 8 255 liens   preuves 2 a 8
2 mandat + acquereur                          2 836         preuves 2 a 8
3 mandat + date                                 731         preuves 3 a 7
9 sans mandat (acquereur + vendeur)             245         preuves 2 a 6
0 creee par C5 depuis cette ligne               190         preuves 0  <- le seul 0
v2 additif (13/11) : >= 3 familles              177         preuves 3 a 6
4 mandat + avancement                           117         preuves 2 a 7
0 mandat de recherche + acquereur                69         preuves 3 a 7
9 ... + acquereur unique dans tout le registre   54         preuves 5 a 7
9 ... + exclusivite                              32         preuves 2 a 6
5 mandat + vendeur                               21         preuves 3 a 7
et une dizaine d'etages plus rares (10, 6, v2, exclusivites)
```

### C. Les 55 liens que le patch RETIRE — `ligne:transaction`

```
045ecde7:28558          08GV8OMZ:6341           1D7EIYKW:27512          1ESJE28Q:12952
1ESJE28Q:12953          3308P0UX:4480           3S4ZWOFK:1001580        3W10AEIK:4747
427UDDSF:3648           427UDDSF:3650           45225170:30712          45225170:1001361
5a956cad:30776          61OW86CS:4496           739a0db1:27195          739a0db1:1001520
774aa002:11138          87QOXR64:1001534        8Q3LHGZ4:8321           8Q3LHGZ4:8322
8RWTD0YX:4385           8RWTD0YX:1001477        9UO5NUN6:11958          9WQ204HP:1001532
A07EC3DH:1001563        CITFQGOB:16378          DAMOO7OU:23995          E9GL6MUS:11415
EGR8KXOL:6554           FLPUUSY3:1876           KT0601S6:24291          NEFHS7JI:26395
NEFHS7JI:26397          OXQSBZ9V:17427          OXQSBZ9V:17430          Q602VZJX:6555
QJQ9M4OF:17366          R0JRVFDC:1001542        RX6J289Y:16377          SBH4QWDW:23050
TR42PT5H:27196          TRJ5Y59U:1001561        UTLG66LE:1001482        V3FO5NDA:19131
V3FO5NDA:19133          VEP1DVQ4:7780           VMWFLLW4:1001540        WJ3KA32F:10730
Y51UMZHY:19277          a8aaeb2b:998            a8aaeb2b:1000           ea6a28a7:14033
f1aedc01:28967          fa06e4e5:28930          fa06e4e5:1001553
```

### D. Les 109 liens que le patch AJOUTE — `ligne:transaction:rôle`

```
0GV2LNV2:4747:offre             1eec6575:30825:offre            2SCBZXMH:7780:offre
2U5QPKRC:17769:compromis        2U5QPKRC:17770:vente            3S4ZWOFK:11958:offre
3W10AEIK:4748:offre             427UDDSF:3649:offre             4G2UHO35:19819:offre
515RUEN3:17428:compromis        515RUEN3:17430:offre            58I5AO17:7908:compromis
58I5AO17:7909:offre             58I5AO17:7910:vente             5H70KQZA:14224:compromis
5H70KQZA:14227:offre            5H70KQZA:14228:vente            5a956cad:30684:offre
5e4c8881:30820:offre            6FQO29C8:19131:compromis        6FQO29C8:19133:vente
70740f2f:30824:offre            72GQRHVB:6391:compromis         72GQRHVB:6392:offre
72GQRHVB:6393:vente             739a0db1:27196:offre            7IHI7YTJ:4234:compromis
7IHI7YTJ:4235:offre             7IHI7YTJ:4236:vente             7JXLR3JQ:7115:compromis
7JXLR3JQ:7117:offre             87QOXR64:17427:compromis        8ATXF2EZ:19152:compromis
8ATXF2EZ:19153:offre            8ATXF2EZ:19154:vente            8RWTD0YX:4387:offre
91IHSGNC:4781:compromis         91IHSGNC:4782:offre             91IHSGNC:4783:vente
9706WM9J:23931:offre            9Q0FHAKK:3647:compromis         9Q0FHAKK:3648:offre
9Q0FHAKK:3650:vente             9UO5NUN6:11959:offre            9WQ204HP:4480:compromis
A07EC3DH:1876:offre             CS38OO8R:27984:compromis        CS38OO8R:27986:offre
CS38OO8R:27987:vente            D9MMB7OU:17366:offre            DAMOO7OU:23996:offre
DHXRAK9O:9370:compromis         DHXRAK9O:9371:offre             DHXRAK9O:9372:vente
E9GL6MUS:11414:offre            EGR8KXOL:6555:compromis         EJN79TJ1:27712:compromis
EJN79TJ1:27713:offre            EJN79TJ1:27714:vente            ESMCO1NC:6588:compromis
ESMCO1NC:6589:offre             ESMCO1NC:6590:vente             FLPUUSY3:1877:offre
H6CTRVR6:11415:offre            I3TFR2KG:24618:compromis        I3TFR2KG:24619:offre
I3TFR2KG:24620:vente            J6RGX0CQ:4928:compromis         J6RGX0CQ:4929:offre
J6RGX0CQ:4930:vente             JL8GV7RQ:15169:compromis        JL8GV7RQ:15170:vente
KAYC29B7:27170:offre            LUX9SDIL:14119:compromis        LUX9SDIL:14120:offre
LUX9SDIL:14121:vente            MDOXOBIC:2163:compromis         MDOXOBIC:2164:offre
MDOXOBIC:2165:vente             MQ6H8TVQ:26695:compromis        MQ6H8TVQ:26696:offre
MQ6H8TVQ:26698:vente            O1099YC0:6341:offre             O8BY6AC8:1000105:offre
O8BY6AC8:1000141:compromis      OXQSBZ9V:17431:offre            PPIM4947:24291:offre
Q602VZJX:6554:compromis         QXDW8EQA:1027:compromis         QXDW8EQA:1028:offre
QXDW8EQA:1029:vente             R0JRVFDC:16377:compromis        RX6J289Y:16378:compromis
S8BKB6FL:4412:compromis         S8BKB6FL:4413:offre             S8BKB6FL:4414:vente
TR42PT5H:27195:compromis        TRJ5Y59U:23995:offre            UTLG66LE:5055:offre
VEP1DVQ4:7781:offre             VMWFLLW4:23050:compromis        Z6P7KE5R:1337:offre
ZZ5WKMWM:11206:offre            a2abd36c:30827:compromis        b43e76f5:30826:offre
b884cbd4:30821:offre            c6233284:30801:offre            f90b0418:19050:offre
fa06e4e5:28931:offre
```

### E. Les 350 verdicts de l'autre session, par catégorie

```
JUSTE                       190
RIEN_CHEZ_NOUS               51
A_RATTACHER                  38
PARTIEL                      37
JUSTE_SANS_PREUVE_FORTE      12
FAUX                         12
INCERTAIN                     8
HORS_JEU                      2
```

Lecture : `JUSTE` et `JUSTE_SANS_PREUVE_FORTE` = le gel avait raison · `PARTIEL` = une partie
des liens de la ligne est fausse · `FAUX` = tous · `A_RATTACHER` = ligne sans lien dont la
transaction existe chez nous · `RIEN_CHEZ_NOUS` = ligne sans lien et sans transaction à
rattacher · `INCERTAIN` = sa réponse manque · `HORS_JEU` = ligne écartée du chantier.

### F. ⭐⭐⭐ LES 32 QUESTIONS ECRITES POUR FRÉDÉRIC — le « § 5 ter » que le rapport annonçait sans l'écrire

⛔ **Aucune de ces lignes ne se pose, ne se déplace ni ne se corrige avant sa réponse.**
Extraites de la colonne `question_pour_frederic` du CSV des verdicts, le 19/11 à 01:00.
⭐ **32 questions sont écrites ; la 33e, annoncée par le rapport, est MUETTE** — `SHN6RKDI`
est marquée incertaine sans question rédigée (voir G). 32 + 1 = les « 33 questions » promises.

- **`TA5QUCD4`** *(juste)* — L'offre du Sheet au 19/07/2018 est-elle une faute de saisie ? Hektor porte l'offre DUPARANT au 11/12/2018, 145 jours plus tard.
- **`Y9A2L3X4`** *(juste)* — Le compromis GERPHAGNON/JOINAUX a-t-il été signé le 20/06/2019 (Sheet) ou le 17/07/2019 (Hektor) ?
- **`V3FO5NDA`** *(partiel)* — Hektor porte pour BAUDOIN-PETIPAS / TROUILLER (Chenereilles) un compromis du 08/12/2023 et un acte du 04/06/2024 (80 000 €, honoraires 6 000), postérieurs à l'annulation du 23/06/2023 : cette vente manque-t-elle au Sheet (une nouvelle ligne prendrait 19131 et 19133) ?
- **`1D7EIYKW`** *(partiel)* — GANDON-BERAUD ont-ils signé un compromis le 17/02/2021 (annulé ensuite), après l'annulation du 20/11/2020 ? Si oui, c'est une seconde tentative absente du Sheet ; si c'est la même tentative, le compromis 27512 peut rester sur cette ligne.
- **`HUY49KEC`** *(juste sans preuve forte)* — Pour ce lot vendu à CANIVET, le compromis du 16/11/2018 a-t-il existé, ou est-ce une date de remplissage (toutes les dates du Sheet sont au 16/11) ? Faut-il le créer ?
- **`O6R10ZQA`** *(incertain)* — O6R10ZQA (annulée le 21/09/2021) et T2GZOY5O (annulée le 21/11/2021) sont la même affaire PAOLONE : laquelle garde l'offre 20075 et le compromis 20073, et quelle date d'annulation est la bonne ?
- **`5QE9107L`** *(incertain)* — Le compromis 20088 (DEBARD, 50 000 EUR dont 5 000 d'honoraires, jamais daté) est-il celui de la 1re offre (55 000 du 20/02/2021, annulée le 21/06/2021) ou celui de la 2e (50 000 du 20/07/2021, ligne ZW7MKTWH, annulée le 21/11/2021) ?
- **`E9GL6MUS`** *(partiel)* — Valérie FIGARI (offre Hektor 11414 du 06/04/2021 à 295 000) est-elle la co-acquéreuse de SOUBEYRAND ?
- **`ea6a28a7`** *(faux)* — La transaction 14033 (compromis annule sans date, 140 500 EUR dont 9 500 d'honoraires, aux noms COLAS / SOLEILHAC) est-elle la trace de l'offre DONNADIEU / KOSINSKI du 04/06/2025, ou un premier compromis du dossier COLAS saisi au prix affiche puis refait a 130 000 EUR ?
- **`c0a73edd`** *(juste)* — Le dossier Hektor 28614-28616 (annonce 59136, D2025-0399, honoraires a la charge du vendeur, porte par aucune ligne) est-il un doublon de la vente 28611-28613, ou un second lot vendu par M. JUQUET a la SCI La Felolie ?
- **`d1cb8dd7`** *(juste)* — Pour le rôle offre, gardes-tu l'offre refaite au nom des MADER (28833, datée du 15/04) ou la première saisie (28832, du 09/04, au nom d'Héloïse MADERE), qui porte la date du classeur ?
- **`2dfa6ef3`** *(juste)* — En cas de renegociation, le role offre doit-il tenir l'offre acceptee (30692, prix du Sheet) ou la premiere offre (30656, date du Sheet) ?
- **`5a956cad`** *(partiel)* — Pour une offre renégociée, le rôle offre doit-il viser l'offre d'origine 30684 du 21/09/2026 (date du Sheet) ou l'offre acceptée 30776 du 27/10/2026 (prix du Sheet) ?
- **`9Q0FHAKK`** *(a rattacher)* — POTTIER Dominique et SOUCHON Christine forment-ils le même ménage acquéreur ? Hektor met SOUCHON sur le compromis à 460 000 et sur la vente, le Sheet met POTTIER.
- **`EJN79TJ1`** *(a rattacher)* — L'acquéreur MACHADO du Sheet est-il le ménage « NERONDE Arthur » de Hektor ?
- **`QXDW8EQA`** *(a rattacher)* — TARDY (Sheet) est-il lié à la SARL VEYRARD DEVELOPPEMENT ou à STEFANELLI Léa, les acquéreurs chez Hektor ?
- **`I3TFR2KG`** *(a rattacher)* — COTE Jean-Claude (Hektor) est-il le représentant de la SCI MADEVA (Sheet) ?
- **`91IHSGNC`** *(a rattacher)* — La vente 4783 nomme GRANGÉ Denis au lieu des DELAVAUD : est-ce une simple erreur de contact chez Hektor ?
- **`2U5QPKRC`** *(a rattacher)* — MARLEE (Sheet) et OBERLIN Christian (Hektor, transactions 17769/17770) forment-ils le même ménage d'acquéreurs ?
- **`MQ6H8TVQ`** *(a rattacher)* — Le Sheet nomme MITTELETTE acquereur de la vente HDHILI du 06/07/2018 ; Hektor porte KABAB Julian (offre) et ODDOU Thibaut (compromis, vente), et MITTELETTE (SCI BEAST) a signe le meme 27/12/2017 un compromis annule sur un autre bien (26558, vendeur DUPORT) : le nom d'acquereur du Sheet est-il une erreur de saisie ?
- **`JZ9693S0`** *(rien chez nous)* — La ligne 3489 (mandat 92560, sans nom ni date, facture GGTI00002792 / avoir AVR00000465) est-elle un residu ou un avoir a laisser hors du registre ?
- **`D9MMB7OU`** *(a rattacher)* — Hektor met ROBERT Joel sur l'offre, le compromis et la vente ; le Sheet met AFFONSO (commentaire « Guetat/Anfosso ») sur la vente : est-ce le même ménage ?
- **`YRUF0S9H`** *(incertain)* — YRUF0S9H (annulée le 22/04/2022, refus de prêt) et 3308P0UX (annulée le 22/05/2022, renonciation) sont-elles la même affaire VIALLARD saisie deux fois ? Si oui, laquelle garde l'offre 4483 ?
- **`4G2UHO35`** *(a rattacher)* — Le compromis annule 19814 (17/02/2020, 69 000, hon 5 980 = commission de cette ligne, acte prevu 17/05/2020), range sous le contact CHEVALLET cree en mai 2020 et porte par aucune ligne, est-il le compromis de BROCHIER (affaire annulee le 20/05/2020 pour financement) ?
- **`ZZ5WKMWM`** *(a rattacher)* — L'offre sans nom 11206 (02/12/2019, 280 000 €) est-elle bien celle de PLA BOUARD ? Le compromis sans date 11205 (280 000 €, honoraires 15 800, étiqueté KERROUM) semble aussi être le leur, mais la ligne n'affirme aucun compromis.
- **`Z6P7KE5R`** *(a rattacher)* — Le Sheet n'a pas de date de compromis (compromis prévu le 21/02, reporté puis annulé). Faut-il aussi rattacher 1335 (compromis THEVENON annulé, sans date, 38500 €, hon 3500) comme compromis de cette ligne ?
- **`3308P0UX`** *(partiel)* — VIALLARD est saisie deux fois au Sheet avec la même offre du 02/02/2022 : 3308P0UX (annulée 22/05/2022, renonciation acq) et YRUF0S9H (annulée 22/04/2022, refus prêt). Laquelle garde l'offre 4483, l'autre restant sans lien ?
- **`87QOXR64`** *(partiel)* — Au Sheet, RIGAUD est annulée le 22/01/2022 mais a un compromis du 11/02/2022. L'annulation est-elle plutôt du 22/02/2022, juste avant le compromis LECOMPTE du 24/02/2022 ?
- **`T2GZOY5O`** *(incertain)* — PAOLONE est saisie deux fois au Sheet (T2GZOY5O annulée le 21/11/2021, O6R10ZQA annulée le 21/09/2021, tout le reste identique) : laquelle garde l'offre 20075 et le compromis 20073, et quelle date d'annulation est la bonne ?
- **`ZW7MKTWH`** *(incertain)* — Le compromis 20088 (DEBARD, 50 000 EUR dont 5 000 d'honoraires, jamais daté) suit-il la 2e offre (50 000 le 20/07/2021, ligne ZW7MKTWH, annulée le 21/11/2021) ou la 1re (55 000 le 20/02/2021, ligne 5QE9107L, annulée le 21/06/2021) ?
- **`RGCEC677`** *(incertain)* — Le compromis annulé et jamais daté 4542 (108 000 €, honoraires de 8 000 €) de la ferme de Cunlhat a-t-il été préparé pour les MEJEAN/MARIAGE (offre de 110 000 € du 07/03/2021, annulée le 01/08/2021 pour un problème de parcelle) ou pour FAU-PIETTE (offre de 108 000 € de septembre 2021, annulée le 21/11/2021) ?
- **`XC761R8Z`** *(incertain)* — Le compromis annulé 4496 de la maison VAN DIJK à Cunlhat (155 000 EUR dont 9 800 d'honoraires, jamais daté) a-t-il été préparé pour l'affaire BISCH (offre de 155 000 le 14/04/2021, annulée le 21/05/2021) ? Si non, il ne revient à aucune ligne.

### G. Les 8 lignes INCERTAINES — intouchables tant qu'il n'a pas répondu

```
5QE9107L      O6R10ZQA      RGCEC677      SHN6RKDI
T2GZOY5O      XC761R8Z      YRUF0S9H      ZW7MKTWH
```
⚠ `SHN6RKDI` est marquée incertaine **sans question écrite** : la formuler avant de lui
soumettre (le compromis 26613 était-il préparé pour MOSNIER ?).

### H. Les 11 paires d'affaires CROISÉES entre acheteurs successifs d'un même bien

La famille d'erreurs la plus instructive : sur un bien revendu ou repris après annulation, le
gel a donné à une ligne la transaction de l'acheteur **suivant**.

```
TR42PT5H <-> 739a0db1   bien 53398 : offre 27196 et compromis 27195 croises
3W10AEIK  -> 0GV2LNV2   l'offre 4747 tombe au jour pres pour 0GV2LNV2
E9GL6MUS  -> H6CTRVR6   l'offre 11415 tombe au jour pres pour H6CTRVR6
VEP1DVQ4 <-> 2SCBZXMH   offres 7780 / 7781
DAMOO7OU  -> TRJ5Y59U   offre 23995
FLPUUSY3  -> A07EC3DH   offre 1876
9UO5NUN6  -> 3S4ZWOFK   offre 11958
427UDDSF  -> 9Q0FHAKK   offre 3648 et vente 3650
OXQSBZ9V  -> 515RUEN3   offre 17430 et compromis 17427
RX6J289Y <-> CITFQGOB / R0JRVFDC   compromis 16377 / 16378
Q602VZJX <-> EGR8KXOL   compromis 6554 / 6555
```

### I. Les copies de C5 nommées — créées alors que Hektor portait déjà la vraie

```
1001520 (copie de 27196) . 1001482 (5055) . 1001480 (20075) . 1001536 (20073)
1001540 (23050) . 1001561 (23995) . 1001563 (1876) . 1001580 (11958)
1001534 (17427) . 1001542 (16377) . 1001553 (« n'a jamais existe »)
```
⛔ **Elles ne se retirent qu'APRÈS le patch du gel**, quand plus aucun lien ne les vise, et
**DES DEUX CÔTÉS** (Supabase et local) ou par `app_affaire_supprimee`. Sur les 25 copies
repérées, 11 seraient retirables après le patch ; 15 restent tenues par des lignes non encore
jugées ou incertaines (un 4e tour).

### J. Ce que la relecture du patch a VALIDÉ, chiffre par chiffre (19/11)

```
55 retraits comptes dans le fichier                           = 55 annonces . OK
109 ajouts comptes dans le fichier                            = 109 annonces . OK
les deux listes de retraits (garde et DELETE)                 MEME EMPREINTE . OK
doublons dans la liste des retraits                           0 . OK
doublons dans la liste des ajouts                             0 . OK
garde « le gel porte 12 787 liens »                           vraie le 19/11 00:00 . OK
controle d'exclusivite global                                 deja vrai aujourd'hui (0) . OK
l'INVERSE juge sa part (0 ecart, 12 787 liens)                OK
la REPETITION est en lecture seule                            OK
types des colonnes visees (preuves smallint, etage text)      l'INSERT passera . OK
```
⛔ **Donc le patch TOURNERA.** Sa faute n'est pas qu'il casse : c'est **où il écrit**
(correction 1 du § 8).
