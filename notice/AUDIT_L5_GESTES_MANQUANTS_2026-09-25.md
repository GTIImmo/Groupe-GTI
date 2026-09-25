# Audit `L5` — les gestes manquants : ce qui reste vraiment

*25/09/2026, après l'allumage de e3. Lecture seule : le worker, le front, la base.*

**Audit limité à `L5`** *(= `E.0-bis` dans la liste)*. Les autres lots ne sont pas mesurés ici.

## 1. Le chiffre du plan est périmé — et largement

Le plan annonce, en tête de `L5` :

> ⚠ **RENDRE MODIFIABLE CE QU'ON NE SAIT QUE CRÉER** *(mesure du 21/09 : 102 champs
> d'annonce, 40 de contact — créables, jamais corrigibles depuis l'app)*

**Cette mesure n'a laissé aucune note ; je l'ai donc refaite.** Résultat :

| | créables | modifiables | **créables mais PAS modifiables** |
|---|---|---|---|
| **annonce** | 136 | **179** | **0** |
| **contact** | 8 | 24 | **0** |

**Aucun champ n'est créable sans être corrigible.** C'est même l'inverse : **46 champs
d'annonce** et **16 champs de contact** sont modifiables sans être créables.

Le travail a été fait bien avant : `HEKTOR_WIZARD_UPDATE_GROUPS` — la modification par
groupes (secteur, intérieur, extérieur, terrain, équipements, diagnostics, copropriété,
construction récente, visite, mandat) — **existe depuis le 02/06/2026** (`a2e8160`).

⚠ **PIÈGE, ET JE SUIS TOMBÉ DEDANS EN LE MESURANT.** Les deux dictionnaires ne parlent pas
le même vocabulaire : `HEKTOR_WIZARD_FIELDS_BY_PROFILE` (création) emploie les noms Hektor
*(`NB_CHAMBRES`, `surfappart`)*, `HEKTOR_UPDATE_FIELDS_BY_PROFILE` emploie les noms de l'app
*(`bedroom_count`, `surface`)*. Comparés tels quels, ils n'ont **aucun** champ en commun et
donnent un écart de 136 — un chiffre du même ordre que le « 102 » du plan. **C'est
probablement l'origine de ce chiffre.** La bonne comparaison se fait contre
`HEKTOR_WIZARD_UPDATE_GROUPS`, qui est en vocabulaire Hektor.

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
vocabulaires. **Il reste trois gestes réels** *(mandat, photos, fusion)*, soit **6 à 10 jours**
au lieu des 2 à 3 semaines annoncées, plus le ménage des liens « Ouvrir Hektor ».

**Ordre proposé, du plus utile au moins :**
1. **les photos** — le geste le plus quotidien pour un négociateur, et le plus autonome ;
2. **le mandat existant** — dates et durée, les plus demandés ;
3. **la fusion de doublons** — après ton arbitrage : dans l'app, ou réservée à l'admin ?

⚠ **Et ceci vaut pour tout le plan** : le chiffre de `L5` était faux d'un facteur trois.
**Les autres chiffrages n'ont pas été revérifiés depuis leur écriture** — les prendre comme
des ordres de grandeur, pas comme des mesures.
