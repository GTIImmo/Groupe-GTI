# A8 — AUDIT DE LA CHARGE DE COMMISSION : POURQUOI IL N'Y A RIEN

**02/11/2026.** Demande de Frédéric : *« STOP AVANT, il y a un chantier : il faut
auditer mon projet et ma data avec notes et codes et historique pour savoir
pourquoi il n'y a rien sur la charge de la commission de vente, puisque cela est
important dans les calculs financiers. Nous avons déjà abordé le sujet mais il
va falloir avoir clairement l'information aussi bien sur les mandats de vente
que sur les transactions qui normalement récupèrent la charge saisie sur le
mandat de vente mais qui peuvent changer. »*

**LECTURE SEULE DE BOUT EN BOUT.** Rien écrit en base, ni chez Hektor, ni au
classeur. Aucun appel à l'API Hektor, aucun login Google.

---

## § 0. LA RÉPONSE, EN HAUT DE PAGE

```
⛔⛔ LA CAUSE RACINE : LA VALEUR JUSTE DANS 99,8 % DES CAS EST LA SEULE QUI NE
    S'ENREGISTRE JAMAIS.

    L'ecran ouvre sur « Vendeur » (useState('vendeur')), et la RPC n'est
    appelee que `if (statusChangeCommissionTouchee)`. Le drapeau ne se leve
    QUE si on TOUCHE quelque chose. Donc : ouvrir la modale, voir « Vendeur »
    -- qui est juste -- et envoyer => RIEN N'EST ECRIT.

    LA DONNEE LE PROUVE SANS DISCUSSION :
        8 lignes portent une charge dans toute la base
        8 a « acquereur »   ·   0 a « vendeur »
    Le seul cas qui OBLIGE a toucher le select est le seul qui existe en base.

⛔ ET LE MANDAT N'EN GARDE RIEN DU TOUT. La charge y est saisie, imprimee sur
   le PDF, puis JETEE : aucune colonne de charge sur un mandat dans toute la
   base de production. Donc la phrase « les transactions recuperent la charge
   saisie sur le mandat » decrit quelque chose QUI N'EXISTE PAS.

⭐ LA BONNE NOUVELLE : la plomberie est saine. Les valeurs d'essai du 16/10
   sont TOUJOURS LA 17 jours plus tard -- la classe A resiste au run de nuit.
   Ce n'est pas un probleme de conservation, c'est une PORTE QUI NE S'OUVRE PAS.
```

---

## § 1. HEKTOR NE PORTE LA CHARGE NULLE PART — mesuré, pas supposé

Déballé le 02/11 sur les `raw_json` du miroir (400 charges brutes par objet) :

```
hektor_mandat      17 cles : CartePro · avenants · cloture · dateEnregistrement
                   · debut · duree_irrevocabilite · fin · id · linked_product_ref
                   · mandants · manual_import · montant · note · numero
                   · product_recap · taciteReconduction · type
                   >>> AUCUNE charge, AUCUN honoraire, AUCUN taux

hektor_compromis   16 cles : acquereurs · annonce · dateEnd · dateSignatureActe
                   · dateStart · honorairesEntree · honorairesSortie · id
                   · mandants · mandat · note · partAdmin · prixNetVendeur
                   · prixPublique · sequestre · status
                   >>> des MONTANTS, jamais QUI PAIE

hektor_vente       19 cles : commissionAgence · honoraires · honorairesEntree
                   · honorairesHT · honorairesSortie · partAdmin
                   · retro_honoraires · retro_idContact · retro_idUser
                   · retro_nom · retro_qualite · prix · date · ...
                   >>> idem : des MONTANTS, jamais QUI PAIE
```

⛔ **Et elle ne se déduit pas de ses chiffres.** Mesure du 14/10, inscrite au
commit `b957636` : *sur 25 lignes où le classeur dit « Acquéreur », **13 sont
rangées côté vendeur chez Hektor**.* Un tirage à pile ou face ferait mieux que
de deviner.

⭐ Deux clefs valent d'être connues, car elles ressemblent à la charge sans en
être :
```
honorairesEntree / honorairesSortie   le partage ENTRE DEUX AGENCES, pas qui paie.
                                      honorairesSortie = 0.00 dans 395/400 :
                                      nous sommes presque toujours les deux cotes.
annonce.partage = 1 dans 387/400      une clef « partage » existe sur l'annonce.
                                      ⬜ NON MESUREE : piste pour les 16 ecarts
                                      a facteur 2 du classeur (A7 § lot 2).
```

---

## § 2. CHEZ NOUS, LE MÉCANISME EST COMPLET — construit le 16/10

L'historique git le dit, commit par commit :

```
16/10  b957636  Classeur, lot 1a : la commission et sa charge des l'offre
                (3 colonnes de classe A)
16/10  f1ee9f0  Lot 1b : la RPC qui ecrit la commission -- et la correction
                de Frederic
16/10  bfb1e09  Lot 1c : la commission se saisit des l'offre, et se reprend
                au compromis
16/10  eb46977  L'essai de commission est pose, et son temoin attend demain
16/10  cabb5f4  Audit du chainage de la commission : le conflit redoute est
                quasi impossible
2?/10  5c7c970  feat(8) V : ... la charge et le nom du notaire SE REPRENNENT
```

Ce qui existe, vérifié dans le code et dans la base :

```
✅ 3 colonnes de classe A sur app_affaire_ledger :
     honoraires_entree_app · honoraires_sortie_app · charge_commission_app
✅ une CONTRAINTE : 'vendeur' | 'acquereur', NULL permis
     (eprouvee : un « Vendeur » majuscule a ete REFUSE le 16/10)
✅ une RPC ecrireAffaireCommission (api.ts:2031), dont le UPDATE porte
     WHERE app_affaire_id = cible -- ecrire sur l'offre NE PEUT PAS bouger le
     compromis, c'est la requete elle-meme qui le garantit
✅ l'ecran « Charge de la commission » (Vendeur / Acquereur) AUX TROIS ETAPES
     (App.tsx:22403)
✅ les 3 colonnes dans affaireLedgerSelect (api.ts:1622) -- sans ca elles
     existent en base et l'ecran ne les voit jamais, SANS AUCUNE ERREUR
     (le projet s'est fait prendre deux fois le 13/10)
✅ la REPRISE offre -> compromis -> vente (App.tsx:17749-17762)
✅ la PROTECTION contre le run de nuit : les colonnes sont dans
     COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS et hors du ON CONFLICT DO UPDATE SET
```

⭐⭐ **ET LA PROTECTION MARCHE, c'est prouvé par le temps.** Les valeurs posées
le 16/10 sur l'offre d'essai 1001339 (`honoraires_entree_app` 1234,
`honoraires_sortie_app` 500, `charge_commission_app` acquereur) sont **encore
en base le 02/11**, après 17 runs de nuit. Le problème n'est **pas** la
conservation.

---

## § 3. ⛔⛔ LA CAUSE RACINE, LIGNE PAR LIGNE

### L'état initial est la bonne valeur

```
App.tsx:14003   const [statusChangeChargeCommission, setStatusChangeChargeCommission]
                  = useState('vendeur')
```
Le select affiche donc « Vendeur » dès l'ouverture — et c'est **juste dans
93,6 % des cas** (classeur : 894 Vendeur contre 61 Acquéreur).

### Mais l'écriture est conditionnée à un drapeau

```
App.tsx:19211   if (statusChangeCommissionTouchee) {
                  ... await ecrireAffaireCommission(...)
                }
```

### Et le drapeau ne se lève que si l'on TOUCHE

```
App.tsx:22390   on tape dans « Honoraires vendeur »       -> drapeau leve
App.tsx:22405   on CHANGE le select de la charge          -> drapeau leve
App.tsx:17759   reprise depuis une offre qui porte une commission -> leve
App.tsx:17753   reprise de la seule charge, A LA CREATION, si l'offre en a une
App.tsx:17941   fermeture de la modale                    -> remis a false
```

### Le résultat, et le cercle vicieux

```
① le negociateur ouvre la modale
② il lit « Charge de la commission : Vendeur » -- c'est la bonne valeur
③ il n'a AUCUNE raison d'y toucher
④ il envoie
⑤ => statusChangeCommissionTouchee est FAUX, la RPC n'est jamais appelee,
     RIEN N'EST ECRIT
```

⭐⭐ **Et la reprise ne peut pas sauver la situation**, parce qu'elle part d'une
**offre qui porte déjà une charge** (`if (... chargeOffre ...)`). Si l'offre est
vide — et elle l'est, par ⑤ — il n'y a rien à reprendre au compromis, donc rien
à reprendre à la vente. **La chaîne ne démarre jamais.**

### LE TÉMOIN QUI CLOT LE DIAGNOSTIC

```
toute la base de production, app_affaire_ledger (31 124 lignes) :
    charge_commission_app renseignee      8
    dont « acquereur »                    8
    dont « vendeur »                      0      <<<<<<
```

« Acquéreur » est **le seul choix qui oblige à toucher le select**. C'est le seul
qu'on trouve en base. Si la cause était autre (une panne de la RPC, un écrasement
par le run, un droit manquant), on verrait **zéro des deux** ou **les deux**.

---

## § 4. ET CE N'EST PAS PROPRE À LA CHARGE — TOUTE LA CLASSE A EST VIDE

```
app_affaire_ledger, 31 124 lignes, mesure du 02/11 sur SUPABASE :
    taux_honoraires          7      <- classe A, les 7 sont des essais
    notaire_id               0      <- classe A, JAMAIS AUCUNE VALEUR
    charge_commission_app    8      <- classe A, les 8 sont des essais
    honoraires_entree_app    4
    honoraires_sortie_app    6
  pour comparer, ce qui vient de HEKTOR :
    taux_honoraire_entree   18 537
    honoraires_entree       19 908
    unites_entree_percent   18 537
```

⚠⚠ **Et c'était déjà écrit le 16/10**, dans
`phase2/checks/essai_commission_offre_2026-10-16.py` :

> « CE MÉCANISME N'AVAIT JAMAIS PORTÉ UNE VALEUR. Mesure du 16/10 : les deux
> colonnes de classe A qui existaient (`taux_honoraires`, `notaire_id`) sont
> VIDES PARTOUT — 0 en production, 0 en local. »

**Dix-sept jours plus tard, `notaire_id` est toujours à 0.** La réserve a été
écrite, jamais traitée.

⭐ Deuxième chiffre qui éclaire : **341 transactions seulement sont nées dans
l'app** sur 31 124 (1,1 %). Les 30 783 autres viennent de Hektor par le run de
nuit, et **le run n'a aucune charge à écrire** (§ 1). Donc même une porte
réparée ne remplirait que l'avenir, jamais le passé.

---

## § 5. LE MANDAT — LA CHARGE EST IMPRIMÉE, PUIS JETÉE

### Ce qui existe

```
App.tsx:4056   honorairesCharge: 'acquereur' | 'mandant' | ''
App.tsx:5735   un menu « Charge des honoraires » (Acquereur / Mandant)
App.tsx:4595   il part dans le payload du document : honoraires.charge
App.tsx:4803   et il coche la case du PDF :
               « La totalite des honoraires sera a la charge du :
                 [ ] MANDANT   [ ] ACQUEREUR »
App.tsx:5435   il est meme OBLIGATOIRE pour valider l'onglet « prix »
```

### ⛔ Ce qui n'existe pas

```
AUCUNE colonne de charge sur un mandat, dans TOUTE la base de production.
Verifie sur information_schema le 02/11 : les seules colonnes qui parlent de
charge sont
    app_affaire_ledger.charge_commission_app     (la TRANSACTION)
    app_dossier_current.commerce_charges         (les charges d'un COMMERCE,
                                                  rien a voir)
```

Donc : **à chaque mandat signé dans l'app, la charge est choisie, imprimée sur
le contrat, et perdue.** Elle ne survit nulle part.

### ⚠⚠ ET PIRE : LES DEUX DÉFAUTS SONT OPPOSÉS

```
App.tsx:4560   le MANDAT      honorairesCharge: rawHonoraires ? 'acquereur' : ''
                              -> « acquereur » des qu'il y a des honoraires
App.tsx:14003  la TRANSACTION useState('vendeur')
                              -> « vendeur » a l'ouverture
```

**La même app propose deux valeurs par défaut CONTRAIRES pour la même notion.**
Et celle du mandat n'est pas un choix : personne ne l'a dit, le code l'écrit.
Sur le classeur, la réalité est 93,6 % Vendeur — donc **le défaut du mandat est
faux dans 9 cas sur 10**.

### ⭐ MAIS LA PLACE EXISTE DÉJÀ, et c'est une bonne nouvelle

```
TABLE app_mandat_champ_app  (le CARNET du mandat, en cle/valeur)
  hektor_annonce_id · numero_mandat · champ · valeur_app · hektor_mandat_id
  · origine · ecrit_le · ecrit_par

ce qu'elle porte aujourd'hui :
  champ                 lignes  mandats  du           au           origine
  mandat_date_cloture        4        4  28/08/2026   23/10/2026   cloture_app
```

**Un seul champ, quatre lignes.** Poser la charge du mandat, c'est donc
`champ = 'charge_commission'` dans une table qui existe — **pas une colonne à
créer, pas une migration**.

---

## § 6. « LES TRANSACTIONS RÉCUPÈRENT LA CHARGE DU MANDAT » — ÇA N'EXISTE PAS

Sa phrase décrit le comportement attendu. Voici le comportement réel :

```
ATTENDU   mandat (saisie) --> offre --> compromis --> vente
                         ^^^^^^^^^^
                         ce maillon N'EXISTE PAS

REEL      mandat (saisie) --> PDF --> poubelle
          offre --> compromis --> vente       (ce maillon existe et MARCHE)
```

⭐ **Le second maillon est prouvé**, sur la chaîne d'essai 1001393 (annonce
24113) : la charge « acquereur » est présente sur l'offre **1001393**, le
compromis **1001394** et la vente **1001395** (= Hektor 23358, la vente d'essai).
La reprise fonctionne ; il lui manque seulement son point de départ.

Et « mais qui peuvent changer » est déjà respecté par la forme du code : la
reprise ne s'applique **qu'à la création** et **jamais par-dessus un choix**
(`if (!courante && chargeOffre && !statusChangeCommissionTouchee)`). Une charge
qui change en cours de route est donc déjà prévue.

---

## § 7. LES 8 LIGNES, UNE PAR UNE — ce sont toutes des essais

```
aff        kind       annonce  hektor   entree  sortie  charge      vu le
1001339    offre        24933   33050     1234     500  acquereur   05/09
1001378    offre        24113   33110     8000    5000  acquereur   24/10
1001381    offre        24113   33112     7000    6000  acquereur   24/10
1001384    offre        24113   33114     6500    5000  acquereur   24/10
1001390    offre        24113   33115        -    5000  acquereur   24/10
1001393    offre        24113   33116        -    5000  acquereur   24/10
1001394    compromis    24113   50137        -       -  acquereur   24/10
1001395    vente        24113   23358        -       -  acquereur   24/10
```

`24933` est le bien d'essai de la console (dit au commit `eb46977`), `24113`
celui du registre des transactions. **Aucune vraie affaire du portefeuille ne
porte de charge.**

---

## § 8. ET L'ÉCRAN MONTRE UNE CASE VIDE, CODE EN DUR

```
App.tsx:33731
  honoraires: honFai ? { fai: honFai, charge: '', taux: '', part: '',
                         rendement: '' } : undefined
```

La fiche d'affaire prévoit un emplacement « charge », un « taux », une
« part » et un « rendement » — **tous les quatre écrits vides**. L'écran
réserve donc la place sans jamais la remplir, même pour les 8 lignes qui ont
une valeur.

---

## § 9. LA SEULE SOURCE HISTORIQUE RESTE LE CLASSEUR

```
colonne Q « Charge Commission » : 955 lignes sur 4 780
    Vendeur      894   (93,6 %)
    Acquereur     61   ( 6,4 %)
deux valeurs, aucune autre, aucune faute de casse.
```

⚠ **Et une correction au passage** : le commit du 16/10 écrit « défaut Vendeur
(99,8 % des cas) ». Le classeur dit **93,6 %**. Les 61 « Acquéreur » ne sont pas
une poignée d'exceptions : c'est un cas sur seize.

---

## § 10. CE QUE JE RECOMMANDE — et rien n'est fait sans son go

```
① ⛔ REPARER LA PORTE (le plus urgent, et le plus petit)
   Ecrire la charge MEME SI PERSONNE N'Y A TOUCHE, puisque l'ecran a affiche
   une valeur et que l'utilisateur l'a validee en envoyant.
   Deux formes possibles, a trancher :
     a. lever le drapeau a l'OUVERTURE de la modale (une ligne)
     b. sortir la charge du drapeau : l'ecrire toujours, et garder le drapeau
        pour les seuls honoraires
   ⚠ a eprouver sur le bien d'essai AVANT toute vraie affaire, et verifier
     qu'ouvrir-puis-envoyer n'ECRASE pas une charge deja posee.

② ⭐ UNIFIER LE DEFAUT : « vendeur » des deux cotes. Le mandat ecrit
   « acquereur » par defaut, ce qui est faux 9 fois sur 10.

③ ⭐ PERSISTER LA CHARGE DU MANDAT dans app_mandat_champ_app
   (champ = 'charge_commission'), puis la reprendre sur la premiere offre de la
   chaine. C'est le maillon manquant qu'il decrit, et la table existe deja.

④ ⬜ LE RATTRAPAGE DU PASSE : seul le classeur sait (955 lignes). Il n'y a
   aucune autre source -- ni Hektor, ni nous. C'est la decision du lot 2 de la
   revue champ par champ, et elle reste ouverte.

⑤ ⬜ TRAITER LA RESERVE DU 16/10 restee ouverte : notaire_id est a 0 depuis
   sa creation. Meme famille, meme cause probable.

⑥ ⬜ REMPLIR LES 4 CASES VIDES de la fiche (charge, taux, part, rendement).
```

---

## § 11. PROVENANCE DES CHIFFRES

```
Hektor         data/hektor.sqlite, raw_json deballes (400 par objet), 02/11
notre base     SUPABASE EN DIRECT (projet dwaqxfrinihnychuoptk), 02/11 --
               et le miroir local donne EXACTEMENT les memes chiffres
               (31 124 lignes, 8 charges), donc la redescente n'est pas en cause
le code        apps/hektor-v1/src/App.tsx et src/lib/api.ts, lus ce jour
l'historique   git log -S sur « charge_commission_app » et « honorairesCharge »
les notes      notice/A4bis, A4, A5, A7 · phase2/checks/essai_commission_offre_2026-10-16.py
               · phase2/sync/affaire_ledger.py
le classeur    cache local du 01/11 18:47 (4 780 lignes, 38 colonnes), sans
               appel reseau
```
