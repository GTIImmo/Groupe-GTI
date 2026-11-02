# A9 — LA CHARGE EXISTE : ELLE EST DANS LE DÉTAIL DE L'ANNONCE

**03/11/2026.** Audit demandé par Frédéric : *« explique-moi encore, après avoir
refait un audit de mes notes, de mes codes etc. »* — après qu'il m'a dit, la
veille : *« cette information doit bien être quelque part dans mon projet,
vérifie les données récupérées par un appel id annonce dans le détail bloc
mandat »*. **Il avait raison.**

⛔⛔ **CETTE NOTE CORRIGE `A8_AUDIT_CHARGE_DE_COMMISSION_2026-11-02.md` SUR UN
POINT MAJEUR, ET SE CORRIGE ELLE-MÊME SUR UN AUTRE.**

**LECTURE SEULE DE BOUT EN BOUT.** Miroir ouvert en `mode=ro`, 12 appels de
lecture à Hektor, aucune écriture nulle part.

---

## § 0. LES QUATRE PHRASES À RETENIR

```
1. LA CHARGE EXISTE CHEZ NOUS, EN CLAIR, ET ELLE DESCEND CHAQUE NUIT :
     data/hektor.sqlite -> hektor_annonce_detail -> honoraires_json
     [{"id": "31", "taux": "5000", "charge": "vendeur"}]
   14 302 annonces · 11 030 « vendeur » · 3 258 « acheteur » · 0 vide.

2. A8 A CONCLU « IL N'Y A RIEN » PARCE QU'IL A CHERCHE SUR TROIS OBJETS
   (hektor_mandat, hektor_compromis, hektor_vente) ET PAS SUR L'ANNONCE.
   Mesure : le mot « honoraires_json » n'apparait PAS une fois dans A8.

3. A8 AVAIT RAISON, ET MOI TORT, SUR honorairesEntree / honorairesSortie :
   ce ne sont PAS « honoraires vendeur / acquereur » au sens de qui paie.
   J'ai affirme le contraire le 02/11 au soir. PREUVE DE MON ERREUR ci-dessous.

4. DEUX PORTES OUVRENT SUR « VENDEUR » EN DUR, ET AUCUNE NE LIT LA VALEUR DE
   HEKTOR -- dont UNE QUE A8 N'AVAIT PAS VUE : l'editeur du PDF de mandat.
```

---

## § 1. CE QUI ÉTAIT DÉJÀ ÉCRIT — et que l'audit confirme

**A8, le 02/11 à 16:48** (commits `4cbb1c3` et `b4e0045`) a trouvé **la cause
racine du vide**, et elle tient :

```
L'ecran de la modale de statut ouvre sur « Vendeur » (useState('vendeur')),
et la RPC n'est appelee QUE `if (statusChangeCommissionTouchee)`.
=> ouvrir, voir « Vendeur » -- qui est juste -- et envoyer : RIEN N'EST ECRIT.
PREUVE PAR LA DONNEE : 8 lignes de charge dans toute la base, 8 « acquereur »,
0 « vendeur ». Le seul cas qui OBLIGE a toucher le select est le seul qui existe.
```

**Et la mesure du 14/10** (commit `b957636`), déjà au dossier : *sur 25 lignes où
le classeur dit « Acquéreur », 13 sont rangées côté vendeur chez Hektor.* C'était
déjà la preuve que la charge ne se déduit pas des montants.

⚠ **Les notes du domaine, balayées** : `A8`, `A4`, `A4bis`, `A5`,
`DECISIONS_REPARTITION_HONORAIRES_HISTORIQUE_2026-10-29`,
`LES_38_COLONNES_CONSOLIDE_2026-10-28`, `MECANISME_REGISTRE_TRANSACTIONS_2026-10-28`,
`SPEC_CHARGE_HONORAIRES_MANDAT_2026-11-02`, `DECISIONS_CHAMP_PAR_CHAMP_CLASSEUR_2026-11-02`.
**Aucune ne mentionne `honoraires_json`.** Le champ n'était pas caché : il
n'était pas cherché là.

---

## § 2. ⛔ CE QUE A8 A MANQUÉ, ET POURQUOI

A8 a déballé les `raw_json` de **trois** objets et a conclu, à juste titre pour
ces trois-là, qu'aucun ne porte la charge :

```
hektor_mandat      17 cles -> aucune charge
hektor_compromis   16 cles -> des MONTANTS, jamais qui paie
hektor_vente       19 cles -> idem
```

⭐ **Mais la charge n'est ni sur le mandat, ni sur le compromis, ni sur la
vente : elle est sur l'ANNONCE**, dans son bloc `honoraires`. C'est la quatrième
porte, celle que la question de Frédéric désignait.

```
MESURE (02-03/11) :
  61 459 lignes de detail, 14 302 portent un bloc honoraires
  valeurs : « vendeur » 62 571 lignes · « acheteur » 19 352 · AUCUNE vide
  les 3 cles sont toujours la : id, taux, charge
  par annonce : 11 030 vendeur · 3 258 acheteur · 14 se contredisent
⚠ Hektor dit « acheteur » la ou notre vocabulaire dit « acquereur ».
```

**Témoin croisé, dans les deux sens** : 8 314 mandats présents à la fois dans
`honoraires_json` et dans l'export Modelo → **93,5 % d'accord** (7 777 / 8 314).
Les deux sources ont été établies sans l'autre.

⛔ **Donc la conclusion ④ de A8 — *« le rattrapage : le classeur est la seule
source (955 lignes) »* — est fausse.** La source est chez nous, elle est 15 fois
plus large, et elle se met à jour toute seule.

---

## § 3. ⛔⛔ CE QUE CET AUDIT CORRIGE CHEZ MOI

Le 02/11 au soir, j'ai expliqué à Frédéric que `honoraires_entree` /
`honoraires_sortie` étaient « honoraires vendeur » et « honoraires acquéreur »,
donc que la charge s'en déduisait peut-être. **Je me fondais sur les libellés du
front** (`App.tsx:30778` « Honoraires acquéreur », `30780` « Honoraires vendeur
(agence) »). **A8 disait l'inverse : le partage entre deux agences.**

**C'est A8 qui a raison, et la mesure le prouve** — croisement complet, sans
échantillon, des compromis avec la charge que Hektor annonce sur leur annonce :

```
charge dite par Hektor   verdict arithmetique du compromis        lignes
  acquereur              « le prix inclut les honoraires »            81
  acquereur              non mesurable / autre                         9
  vendeur                « le prix inclut les honoraires »         4 307
  vendeur                autre                                        56

honoraires_sortie rempli :  acquereur 8  ·  vendeur 9
```

⭐⭐ **81 des 90 compromis à charge ACQUÉREUR donnent le MÊME profil
arithmétique que les 4 307 à charge vendeur.** Donc `prix_net_vendeur` est
calculé par Hektor comme *prix − honoraires* **quelle que soit la charge** : le
témoin qui avait tranché l'export Modelo **ne discrimine rien ici**. Et
`honoraires_sortie` est rempli presque autant d'un côté que de l'autre.

```
PAR DENOMBREMENT, et c'est imparable :
  honoraires_sortie renseigne   79 fois sur 31 124
  or Hektor dit « acquereur » pour 3 258 annonces
  -> il manquerait plus de 3 000 valeurs. La colonne NE PEUT PAS porter l'info.
  par nature : offre 11 206 (entree 0, sortie 33) · compromis 10 642 (10 605/26)
               vente 9 276 (9 255/20)
```

⚠ **Et cela désigne un défaut d'étiquette** : `App.tsx:30778` affiche
« Honoraires acquéreur » en prenant `honoraires_sortie_app` (la nôtre) **puis
`honoraires_sortie` en repli** — c'est-à-dire une colonne de Hektor qui ne veut
pas dire cela. ⬜ À corriger : le repli est trompeur.

---

## § 4. ⬜ LES TROIS DÉFAUTS NEUFS, TROUVÉS PAR CET AUDIT

### A — L'éditeur du PDF de mandat ouvre sur « Mandant », EN DUR

```
App.tsx:4571    honorairesCharge: 'mandant',
App.tsx:5791    le select « Charge des honoraires » : Acquereur / Mandant
App.tsx:4677    const chargeAcquereur = payload.honoraires.charge === 'acquereur'
                -> LE PDF COCHE UNE CASE SELON CETTE VALEUR
```

C'est **le jumeau exact du défaut qu'A8 a trouvé sur la modale de statut**, sur
une autre porte, et A8 ne l'a pas vu. La valeur de Hektor existe pour ce bien :
elle n'est **jamais lue**. Pour les 3 258 annonces à charge acquéreur, le PDF
coche donc « Mandant » si le négociateur ne corrige pas **un document signé par
le client**.

⭐ **L'impact réel est aujourd'hui faible, et il faut le dire** : `18` PDF de
mandat générés en tout, du **29/06 au 24/07/2026**, aucun depuis. Le défaut ne
mord presque pas — **mais il mordra dès qu'on utilisera cette porte**, et c'est
précisément la porte que le chantier de la charge veut ouvrir.

### B — Le repli du PDF sur `honoraires_json` lit les MAUVAISES CLÉS

```
App.tsx:4543
  valueFromJsonList(detail.honoraires_json, ['montant_ttc','montant','honoraires','value'])
  les VRAIES cles du bloc sont : id · taux · charge
  -> ce repli ne peut JAMAIS rien trouver. Le montant vit dans `taux`.
```

⭐ Et `backend/app/services/rapprochement_email.py:129` le savait déjà : *« dans
`honoraires_json`, `taux` est un MONTANT en € (pas un %) »*. Le backend a la
bonne clé, le front ne l'a pas.

### C — Le registre des mandats ne reçoit rien

```
app_mandat_register_current : 70 colonnes, AUCUNE de charge
  (mandat_montant porte LE PRIX : mandat 18569, prix 70 000 = montant 70 000)
mandat_charge_honoraires_app : posee le 02/11, VIDE -- c'est la saisie humaine
```

La valeur arrive chaque nuit dans le miroir et **s'arrête là**. Aucun worker,
aucune synchro, aucun écran ne la remonte.

---

## § 5. ⚠ LES TROUS, NOMMÉS — et ce qui n'est PAS mesuré

```
⛔ QUELLE ANNONCE FAIT FOI POUR UN MANDAT : NON TRANCHE.
   par hektor_annonce.no_mandat   10 188 mandats  8 421 vendeur · 1 767 acquereur
   par le lien du registre         8 571 mandats  8 467 vendeur ·   104 acquereur
   Les liens sont COHERENTS (93,4 % identiques, 6,6 % se recoupent, ZERO cas
   disjoint sur 18 167) : l'ecart vient du PERIMETRE. Sans cette decision, un
   rattrapage ecrirait la charge d'une annonce voisine.

⬜ 116 MANDATS DE 2026 SANS CHARGE, et l'API ne l'a pas : mesure en trois temps
   (miroir 'null' · reponse brute conservee 'null' · APPEL EN DIRECT le 02/11
   soir : 11 null, TEMOIN POSITIF 61398 qui rend bien la donnee). Ce n'est donc
   ni notre lecture ni la fraicheur : la valeur n'a pas ete saisie chez Hektor.
   Statuts : 3 Actif (dont un EXCLUSIF a 192 400 €), 2 sous compromis, 1 Vendu,
   3 Clos, 2 Estimation. -> anomalie de SAISIE a l'agence, rien a coder.

⬜ LE TROU 2012-2014 : 5 143 mandats, aucune source. NON EXPLIQUE.
⬜ 2 258 annonces portent un verdict mais AUCUN no_mandat.
⬜ 30 mandats dont les annonces se contredisent · 537 desaccords Hektor/Modelo.
⬜ NON MESURE : ce que dit honoraires_json des 25 lignes du classeur de la
   mesure du 14/10. Ce serait un TROISIEME temoin, et il arbitrerait le classeur.
⬜ NON MESURE : si honoraires_json existe aussi pour les LOCATIONS, et ce que
   « charge » y signifie (le vocabulaire locatif est different).
```

---

## § 6. CE QUE JE PROPOSE — rien n'est codé, aucun « go » demandé ici

```
① LIRE CE QUI EXISTE DEJA, avant d'ecrire quoi que ce soit :
     une colonne mandat_charge_honoraires_hektor au registre des mandats,
     alimentee par l'exporteur depuis honoraires_json, A COTE de la saisie
     humaine (mandat_charge_honoraires_app). Precedence a l'ecran : la saisie
     d'abord, Hektor en repli. C'est le patron DEJA EPROUVE de la date de
     cloture (13/10), et il protege le carnet du push de nuit.

② CORRIGER LES DEUX DEFAUTS D'OUVERTURE (A8 et defaut A ci-dessus) : les deux
   portes doivent s'ouvrir sur LA VALEUR DU BIEN, pas sur une constante.
   ⭐ Le defaut A est le plus urgent des deux sur le FOND (un PDF signe par le
     client) et le moins urgent sur le VOLUME (18 PDF, aucun depuis juillet).

③ CORRIGER LA CLE DU REPLI (defaut B) : `taux`, pas `montant_ttc`.
④ CORRIGER L'ETIQUETTE « Honoraires acquereur » (§ 3) : retirer le repli sur
   honoraires_sortie, qui ne veut pas dire cela.
⑤ LE RATTRAPAGE HISTORIQUE : Hektor pour 2018->2026, l'export Modelo pour
   2015->2017 (voir DECISIONS_CHAMP_PAR_CHAMP_CLASSEUR § 3 sexies), chaque
   ligne portant SA SOURCE. ⛔ APRES la decision sur l'annonce qui fait foi.
```

⛔ **ET LA LEÇON, qui est celle d'A8 retournée contre lui** : *une réserve
d'audit non traitée devient le bug.* Ici, c'est **un audit qui a conclu à
l'absence sans avoir balayé les quatre objets**. La règle du projet le disait
déjà : *un audit balaie les objets ET les gestes* — et « annonce » est un objet
du tableau. Voir [[un-zero-ne-se-croit-pas-sans-temoin-positif]] : **A8 a cru un
zéro**, et le témoin positif existait à une table de là.
