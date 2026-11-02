# LES COQUILLES D'OFFRE — ce qui est fait, et ⏰ CE QUI RESTE

**02/11/2026.** Frédéric : *« masque les 54 coquilles et fais une note pour pas
oublier dans le projet »*.

> ⏰ **LA PARTIE NON FAITE EST EN § 2. ELLE EST BLOQUÉE PAR UN AUTRE CHANTIER EN
> COURS, PAS PAR UNE DÉCISION.** Si cette note n'est lue qu'une fois, lire le § 2.

---

## 0. DE QUOI ON PARLE, EN UNE PHRASE

Hektor porte **54 offres sans aucune proposition** : ni montant, ni statut, ni
date. Elles existent chez lui (l'API répond `trouve: true`) mais il n'en sait
rien de plus que sa liste. Elles s'affichaient au registre des transactions
comme des offres, avec une date qui **glissait chaque nuit** — c'est ce que
Frédéric a vu sur VA30102 (deux offres datées du jour, sur un bien vendu en 2008).

**La définition exacte, et elle est unique** : *une offre dont la liste des
propositions est vide.* Chez Hektor le montant, le statut et la date d'une offre
vivent **dans** les propositions — donc « sans date », « sans montant » et « sans
statut » sont **un seul fait dit trois fois**.

⛔ **CE QUI N'EST PAS UNE COQUILLE : LES 14 OFFRES À `0000-00-00`.** Elles n'ont
pas de date non plus, mais ce sont de vraies offres — 2 propositions typées
chacune, un montant de **65 000 à 328 000 €**, 6 acceptées. **On ne les masque
pas**, et le prédicat les épargne délibérément (il regarde les propositions, pas
la date). Un témoin inverse le vérifie à chaque passage.

Tout l'audit : `notice/AUDIT_DATES_0000_COMPROMIS_ET_OFFRES_2026-11-02.md`.

---

## 1. ✅ CE QUI EST FAIT, ET PROUVÉ

**Le prédicat `app_affaire_est_coquille(kind, date, propositions_json)`** existe
en base, **déclaré et commenté**. ⭐ Une seule définition, appelée par chaque
porte — jamais recopiée (règle du projet : une exclusion recopiée dérive).

**La LISTE du registre ne les montre plus** : le filtre est posé dans
`app_registre_dossiers`. Mesure : **12 117 → 12 110 dossiers**, **31 107 →
31 053 lignes**. Les **7 dossiers qui disparaissent** sont ceux qui ne
contenaient **que** des coquilles ; les 42 autres gardent leur place et perdent
juste la ligne fantôme.

**8 contrôles verts, dont trois témoins inverses à zéro :**

```
coquilles reconnues                   54   (54 attendu)
offres a 0000 GARDEES                 14   (14 attendu)   <- temoin inverse
compromis / ventes touches             0                  <- temoin inverse
offres DATEES touchees                 0                  <- temoin inverse
filtre en place dans la fonction       1
parties toujours attachees            54
liens de classeur intacts         12 413
lignes du registre intactes       31 124   <- AUCUNE donnee supprimee
```

**Patch et retour arrière** : `supabase/patch_masquer_coquilles_offre_2026-11-02.sql`
et `..._INVERSE.sql`.

⭐ **Pourquoi un filtre d'affichage et pas une suppression** — trois raisons
mesurées, pas une préférence :

- elles **existent** chez Hektor : les ranger dans `app_affaire_supprimee`
  (« effacé chez Hektor ») serait un **mensonge** ;
- rien d'humain n'y est attaché (0 note, 0 condition, 0 champ saisi, 0 décision
  de carnet), **mais** il y a 54 parties, 40 relations de contact et ⚠ **1 lien
  de classeur** (ligne 3847, « à valider », posé par `apparier_classeur.py` le
  29/10). Un filtre ne casse rien de tout cela ; une suppression les aurait
  cassés ;
- et **masquer n'est pas masquer du vide** : ce sont **52 noms d'acquéreurs sur
  49 biens**, avec leur ville et leur ancienneté.

⚠ **Le patch pose par ANCRE sur la définition vivante**, après vérification de
son empreinte md5 et de l'unicité de l'ancre. Recopier les 6 251 caractères de
`app_registre_dossiers` aurait écrasé en silence toute retouche d'une autre
session.

---

## 2. ⏰⏰ CE QUI RESTE À FAIRE — LES DEUX FICHES

> **C'est la seule chose qui manque, et elle n'attend pas une décision : elle
> attend qu'un fichier se libère.**

Les écrans lisent `app_affaire_ledger` par **trois** portes. Une seule est
filtrée aujourd'hui :

```
LA LISTE du registre   app_registre_dossiers (SQL)              ✅ FILTREE
LA FICHE d'un dossier  api.ts loadDossierDeLaChaine(chaineId)   ⏰ A FAIRE
LA FICHE d'un bien     api.ts loadAffairesForDossier(dossierId) ⏰ A FAIRE
```

⛔ **POURQUOI JE NE L'AI PAS FAIT** : `apps/hektor-v1/src/lib/api.ts` porte des
**modifications non commitées d'une autre session** (elle travaille sur le
registre des transactions et les couples). Stager ce fichier aurait emporté son
travail en cours dans mon commit. La règle du projet — *stager fichier par
fichier* — ne protège pas d'un fichier **partagé** : là, il faut attendre.

⚠ **ET C'EST LA FICHE QUE FRÉDÉRIC A VUE.** Son signalement du 02/11 (« pourquoi
il y a 2 offres en date du 02/11 ») portait sur **VA30102**, un bien à deux
coquilles : c'est la fiche du dossier. **Tant que le § 2 n'est pas fait, le
symptôme qu'il a signalé reste visible là.** La date ne glisse plus (corrigée le
matin, commit `9eae26c`), mais les deux lignes vides sont toujours sur la fiche.

**LE GESTE, quand api.ts sera libre** — deux lectures, le même ajout :

```ts
// 02/11/2026 : on ne montre plus les coquilles d'offre -- une offre que Hektor
// porte SANS AUCUNE PROPOSITION. Meme predicat qu'en base
// (app_affaire_est_coquille) : si l'un bouge, l'autre doit bouger.
.not('app_affaire_id', 'in', ...)   // <- NON : voir ci-dessous
```

⭐ **La bonne forme est un filtre PostgREST sur les colonnes, pas une liste
d'identifiants** (une liste se périmerait à chaque run) :

```
.or('kind.neq.offre,date.not.is.null,propositions_json.neq.[]')
```

⚠ **À éprouver avant de la croire** : `propositions_json` est `jsonb`, et la
comparaison PostgREST d'un jsonb à `[]` n'est pas garantie. Si elle ne mord pas,
le repli propre est **une colonne générée** `est_coquille boolean` sur
`app_affaire_ledger`, alimentée par le prédicat, et un simple
`.eq('est_coquille', false)` — c'est la forme la plus lisible, et elle sert aussi
au front sans dupliquer la règle.

---

## 3. ⬜ LES QUESTIONS ENCORE OUVERTES, qui ne sont PAS ce chantier

Elles sont détaillées dans l'audit, § 4. Résumé pour ne rien perdre :

**a) Les 14 offres à `0000-00-00`** : on les garde visibles. Leur date n'existe
nulle part — ni dans la liste, ni dans le détail de l'API, ni dans le classeur.
Faut-il écrire quelque chose à la place du vide (« date inconnue ») ?

**b) ⛔⛔ L'ÉTAT DE 17 OFFRES EST DÉDUIT D'UN ORDRE SANS CLÉ DE TRI.** Trouvé le
02/11 en comparant l'API à la liste. Notre code prend le **type de la dernière
ligne** de l'historique ; cette règle suppose une date pour trier. Liste et
détail rendent le même historique de l'offre 1142 **dans un ordre inversé** →
« accepté » par l'une, « proposition » par l'autre. 14 offres à `0000` **et 3
offres tout à fait normales** dont les deux lignes sont horodatées à la même
seconde. La piste « l'id le plus petit est le plus récent » tient à **97 %** —
pas une clé. **Rien n'est codé**, et ça toucherait l'état affiché des 11 199
offres.

**c) Les compromis à `0000-00-00`** (204 au registre, 252 relations) : la date
est **gardée telle quelle**. La raison est mesurée — le compromis n'a pas été
signé (14,25 % des annulés contre 0,16 % des actifs). ⭐ La question avait été
**explicitement reportée le 20/10** et n'a jamais été tranchée.

**d) Les 15 compromis ACTIFS sans date** : les anormaux. Le § 2.7 existe, codé et
mesuré, **pas allumé** (`APP_CHAINAGE_SANS_DATE` vaut 1, pas 2).

**e) Les 7 compromis à `1990-01-01`** : jamais regardés de près.

**f) ⭐ Une offre à regarder par Frédéric** : la **20588** sur **VI054**,
150 000 €, proposée, au nom de **GERPHAGNON** (contact 95776). Il reconnaîtra
tout de suite si c'est réel.
