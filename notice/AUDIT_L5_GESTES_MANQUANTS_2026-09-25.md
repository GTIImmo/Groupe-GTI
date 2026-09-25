# Audit `L5` — les gestes manquants : ce qui reste vraiment

*25/09/2026, après l'allumage de e3. Lecture seule : le worker, le front, la base.*

**Audit limité à `L5`** *(= `E.0-bis` dans la liste)*. Les autres lots ne sont pas mesurés ici.

## 1. Le chiffre du plan est périmé — et largement

Le plan annonce, en tête de `L5` :

> ⚠ **RENDRE MODIFIABLE CE QU'ON NE SAIT QUE CRÉER** *(mesure du 21/09 : 102 champs
> d'annonce, 40 de contact — créables, jamais corrigibles depuis l'app)*

**Cette mesure n'a laissé aucune note ; je l'ai donc refaite.**

⚠ **MA PREMIÈRE MESURE ÉTAIT FAUSSE, et Frédéric l'a vue** *(« je ne comprends pas comment
il peut y avoir plus de champs modifiables que créables »)*. Elle comparait une liste
**partielle** de création à la liste **complète** de modification : la création a **deux**
listes — `HEKTOR_WIZARD_COMMON_FIELDS` *(les champs communs à tous les biens : adresse,
prix, honoraires, taxes)* et `HEKTOR_WIZARD_FIELDS_BY_PROFILE` *(les champs propres au type
de bien)*. **Je n'avais pris que la seconde**, d'où l'absurdité : on aurait pu modifier une
adresse sans pouvoir la créer.

**La mesure refaite, listes complètes :**

| | annonce |
|---|---|
| champs **créables** | 42 communs + 136 par type = **178** |
| champs **modifiables** | 179 par groupes + 3 chauffage = **182** |
| **en commun** | **173** |
| créables mais pas modifiables | **5** — tous couverts, voir ci-dessous |
| modifiables mais pas créables | 9 — **des doublons de nom, pas des champs** |

**Les 5, vérifiés un par un :**

| champ | verdict |
|---|---|
| `titre`, `corps` *(la description)* | **modifiables** — chemin propre `principal_text` (l. 9642) |
| `NEGOCIATEUR` | **modifiable** — handler dédié `handleAssignHektorAnnonceNegotiator` |
| `diffusable` | **figé exprès** : le code le force à 0 (étape 7) et ignore toute autre valeur |
| `idpays` | le pays, posé à « France » par défaut, jamais modifié |

**Les 9 « modifiables mais pas créables » sont des doublons de nommage** : Hektor appelle le
même champ `ANNEE_CONS` à la création et `ANNEE_CONSTRUCTION` à la modification. Idem
`SDB`/`NB_SDB`, `SE`/`NB_SE`, `WC`/`NB_WC`, `DPE`/`dpe_cons`, `GES`/`dpe_ges`,
`ETAT_EXTERIEUR`/`etat_exterieur`, `ETAT_INTERIEUR`/`etat_interieur`, `SDE`/`NB_SE`.

**Côté contact** : 8 champs à la création, 24 à la modification, **0 créable sans être
corrigible**.

➡ **AUCUN champ n'est créable sans être corrigible, ni pour l'annonce ni pour le contact.**

Le travail a été fait bien avant : `HEKTOR_WIZARD_UPDATE_GROUPS` — la modification par
groupes (secteur, intérieur, extérieur, terrain, équipements, diagnostics, copropriété,
construction récente, visite, mandat) — **existe depuis le 02/06/2026** (`a2e8160`).

⚠ **DEUX PIÈGES, ET JE SUIS TOMBÉ DANS LES DEUX.**

**① Deux vocabulaires.** `HEKTOR_WIZARD_FIELDS_BY_PROFILE` (création) emploie les noms Hektor
*(`NB_CHAMBRES`, `surfappart`)*, `HEKTOR_UPDATE_FIELDS_BY_PROFILE` les noms de l'app
*(`bedroom_count`, `surface`)*. Comparés tels quels, ils n'ont **aucun** champ commun et
donnent un écart de 136 — l'ordre de grandeur du « 102 » du plan. **C'est probablement
l'origine de ce chiffre.** La bonne comparaison se fait contre `HEKTOR_WIZARD_UPDATE_GROUPS`,
qui est en vocabulaire Hektor.

**② Une liste sur deux.** La création se lit dans **deux** listes, pas une. N'en prendre
qu'une fait apparaître comme « non créables » l'adresse, le prix et les honoraires.

➡ **La leçon, et elle vaut pour tout audit de ce projet** : avant de comparer deux listes,
vérifier qu'elles sont **complètes** et qu'elles parlent **la même langue**. Ici, le même
piège a produit deux fois un chiffre faux — dont celui qui figure dans le plan depuis le 21/09.

**Les 3 seuls champs hors des groupes** — `formatChauff`, `typeChauff`, `energieChauff` —
ne sont pas un manque : le chauffage a **son propre chemin** (`applyHektorChauffage`,
appelé à chaque modification, l. 9651).

## 2. Ce qui reste vraiment dans L5

| geste | état mesuré | chiffrage du plan |
|---|---|---|
| **modifier un mandat existant** *(dates, durée, avenant qui prolonge)* | **manquant** — le worker ne sait que **générer** le document (`handleGenerateMandatDocument`) et **créer** avec numéro auto (`handleCreateHektorMandatAutoNumber`) | 2-3 j |
| **photos : supprimer, réordonner, choisir la principale** | **manquant** — on sait seulement **ajouter** (`handleUploadHektorPhoto`) et **synchroniser** (`handleSyncHektorPhotos`) | 2-3 j |
| **fusionner des doublons de contacts** | **manquant** — aucun handler ; le bouton ouvre Hektor | 2-4 j, **ou réservé à l'admin : à trancher par Frédéric** |
| **supprimer une annonce** | ⭐ **DÉJÀ FAIT** — `handleDeleteHektorAnnonce` existe et le front l'appelle (`delete_hektor_annonce`, `api.ts:9547`) | — |
| **reprise des brouillons** | à mesurer — on sait **créer** un brouillon, pas le reprendre | — |
| **retirer les liens « Ouvrir Hektor »** | **38 occurrences** dans `App.tsx` — dernier geste du lot, quand tout le reste est couvert | — |
| **`C.13` clôture du mandat** | non mesuré ici | — |

## 3. Conclusion

**`L5` est beaucoup plus petit qu'annoncé.** Son gros morceau — les 102 + 40 champs — n'existe
pas : il était déjà fait, et le chiffre venait vraisemblablement d'une comparaison entre deux
listes incomplètes, écrites dans deux vocabulaires différents. **Il reste trois gestes réels** *(mandat, photos, fusion)*, soit **6 à 10 jours**
au lieu des 2 à 3 semaines annoncées, plus le ménage des liens « Ouvrir Hektor ».

**Ordre proposé, du plus utile au moins :**
1. **les photos** — le geste le plus quotidien pour un négociateur, et le plus autonome ;
2. **le mandat existant** — dates et durée, les plus demandés ;
3. **la fusion de doublons** — après ton arbitrage : dans l'app, ou réservée à l'admin ?

⚠ **Et ceci vaut pour tout le plan** : le chiffre de `L5` était faux d'un facteur trois.
**Les autres chiffrages n'ont pas été revérifiés depuis leur écriture** — les prendre comme
des ordres de grandeur, pas comme des mesures.
