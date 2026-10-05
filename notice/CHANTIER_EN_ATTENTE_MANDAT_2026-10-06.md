# CHANTIER EN ATTENTE — registre des mandats · fiche mandat · édition du PDF

**Écrit le 05/10/2026 au soir, pour la reprise du 06/10.**
Audit complet : `notice/AUDIT_REGISTRE_MANDATS_2026-10-05.md` (13 sections).
Sentinelle : `phase2/checks/mandat_corps_recopie.py`.

---

## CE QUI EST DÉJÀ EN PRODUCTION — ne pas le refaire

| | mesure |
|---|---|
| les mandants du registre viennent de **notre registre des liens** | 24 451 / 24 487 · **607** lignes comblées, 31 restent vides |
| le montant d'un autre mandat n'est plus affiché **au registre** | **454** lignes masquées (91 montraient un chiffre) |
| la recherche ne remonte plus un nom étranger | « BANO » ne ramène plus le bien de SOUVIGNET |
| la sentinelle veille | 3 gardes : corps recopié **91** · couples à deux mandats **31** · deux numéros le même jour **2** |
| le filet de colonne absente | `colonne_disponible()` + `adapter_registre_au_schema()` |
| l'identité du registre | 7 contrôles, 7 zéros · 2 072 mandats portent notre numéro sans celui de Hektor |

⭐ **Et tout cela est autonome** : 0 appel Hektor dans `export_app_payload` /
`push_upgrade` / `registre_mandats_upsert`. Le critère se calcule sur le miroir local.

---

## LA CAUSE, ÉTABLIE — ce n'est pas un recyclage

L'identifiant complet d'un mandat chez Hektor est **`<id>-<FAMILLE>`** — le projet
l'avait déjà écrit le 25/08 (`notice/NOTE_CHAINE_DES_MANDATS_2026-08-25.md` §6) :

> *« Hektor n'attend pas un numéro mais un couple `<id>-<FAMILLE>` — `648-PROTEXA` ou
> `9887-HEKTOR` — et une valeur amputée est ignorée sans erreur. »*

L'agence est passée aux mandats **PROTEXA** en mars 2026, et PROTEXA numérote depuis 1.
`10-PROTEXA` et `10-HEKTOR` sont **deux mandats différents** : sur 449 identifiants nus
partagés, **446 portent les deux familles**.

⛔ **Mais la lecture résout sur l'identifiant NU.** Vérifié :
`getMandatById("10")`, `("10-PROTEXA")` et `("10-HEKTOR")` rendent **tous les trois** le
mandat HEKTOR 16564 de 2024. Le bloc mandat de la fiche annonce fait pareil : il renvoie
**le montant et les mandants du mandat HEKTOR** sous **le numéro et les dates du mandat
PROTEXA**.

⭐ Donc **la donnée existe chez eux** — ce sont ses dates de 2026 qui nous parviennent.
C'est sa **résolution** qui échoue. Le jour où ils corrigent, le montant revient au run
suivant et notre masque se lève seul.

---

# ⬜ CE QUI RESTE À FAIRE — par ordre

## ① L'ÉPREUVE : l'écran web porte-t-il le vrai montant ?

```bash
node Console/sonde_mandat_prix_web.js 61811
```

Deux GET que le worker connaît déjà (`chargeannonce_MandatPrix`, `protexa-mandat`),
**en lecture seule**.

⛔⛔ **JAMAIS les POST qui suivent** dans le geste du worker (`step1`, `step2`) : ils
**créent** un mandat et **brûlent un numéro non annulable** (c'est PROTEXA qui le
fabrique, mention légale, série cotée sans discontinuité).

Le cas témoin : annonce **61811**, qui affiche `95 000` pour un bien à `71 000`.

- **si le vrai montant y est** → rattrapage console sur le modèle du chauffage, un
  travail par annonce, sur `WorkerAdmin` ou `WorkerActions` (**pas** la file des
  documents), et les 454 se remplissent avec la **vraie** valeur, sans La Boîte Immo ;
- **sinon** → il ne reste que l'export « liste mandat » de mars à aujourd'hui.

### ⭐ L'ÉPREUVE A ÉTÉ TENTÉE LE 05/10 AU SOIR — et elle a trouvé la porte

**Ce qui marche :**

```
session : les cookies du depot ont EXPIRE le 29/06 -> 403 sur les deux GET.
          Le worker garde une session FRAICHE par service :
          Console/sessions/storage_state_<kind>.json  (sync_light a 21:59)
          -> la sonde prend la plus recente en EVITANT celle du worker Documents.

mode=chargeannonce_MandatPrix&id=61811   HTTP 200,  84 294 car.
mode=protexa-mandat&mandat=0&idann=61811 HTTP 200, 293 088 car.
```

**Ce que les deux pages donnent — et ne donnent pas :**

| | |
|---|---|
| `chargeannonce_MandatPrix` | un **onglet de navigation** : `Mandat N° 18466` avec `rel="49|0"` → **49 est l'identifiant PROTEXA du mandat**. La page porte `71 000` (le prix) et `65 000`, **PAS** le faux `95 000` |
| `protexa-mandat` | le **formulaire de création** (`numeroMandatProtexa` vide). `mandat=49` rend la même page que `mandat=0` : ce n'est pas un lecteur |
| ⭐ les deux | contiennent **ASTIER** — le mandant que **nos liens** donnent — et **pas** « LANGLADE » que le miroir porte. **Une confirmation de plus que nos mandants sont justes** |

**⭐⭐ LA PORTE DE LECTURE, trouvée dans le JS de la page :**

```js
function getThisInfoMandat(idMandat, idAnnonce, reloadHistory = false) {
  var dataSend = {
    mode: 'contacts-contactProfile-mandat-getInfoMandat',
    idMandat: idMandat,      // 49   <- l'identifiant PROTEXA, lu dans rel="ID|0"
    idAnnonce: idAnnonce,    // 61811
    reloadHistory: reloadHistory
  };
  $j.ajax({ type: "POST", url: "xmlrpc.php", data: dataSend, ... })
}
```

⚠⚠ **C'EST UN POST, ET JE NE L'AI PAS DÉCLENCHÉ.** Son nom dit `getInfoMandat`, donc
c'est très probablement une lecture — mais « très probablement » ne suffit pas : la même
page cite **`mandat-postMandatVente`** (qui enregistre) et **`mandat-supprime`** (qui
supprime). Un mauvais appel dans cette famille écrit ou détruit un mandat.

**DONC DEMAIN, DANS CET ORDRE :**

1. **lire d'abord** la suite de `getThisInfoMandat` dans la page sauvegardée
   (`Console/exports/mandatprix_61811_mode_chargeannonce_MandatPrix.html`) pour confirmer
   qu'il n'écrit rien — la fonction entière y est ;
2. puis, **avec ton accord**, l'appeler sur **une seule** annonce et regarder si le vrai
   montant y est ;
3. si oui → rattrapage console sur le modèle du chauffage, **sur `WorkerAdmin` ou
   `WorkerActions`**, jamais la file des documents. L'identifiant PROTEXA se lit dans le
   `rel="ID|0"` de l'onglet, donc **deux appels par annonce** : l'onglet puis la lecture.

⛔ **Et JAMAIS `mandat-postMandatVente` ni `mandat-supprime`.**

## ② RENDRE LA MODALE DU REGISTRE AUTONOME — *la plus importante*

Le motif existe et fonctionne **sur la fiche annonce** depuis le 02/10 :

```js
// App.tsx ~17872 -- NOTRE REGISTRE D'ABORD, le detail Hektor en repli
const duRegistre = detail.mandants_registre_json
if (duRegistre !== null && duRegistre !== undefined) {
  return buildDetailContactsFromRegistre(duRegistre, 'detail-contact')
}
return buildDetailContactsFromProprietaires(detail.proprietaires_json, 'detail-contact')
```

**La modale du registre ne l'a jamais reçu :**

```
editorFullContacts    (~23542) <- proprietaires_json de HEKTOR      12 700 / 13 467
editorPartialContacts (~23557) <- proprietaires_json du registre          0 / 24 487
```

⛔ **Conséquence : sur 97 % des lignes du registre (23 742 sans détail de dossier), le
`MandatDocumentEditor` reçoit ZÉRO contact** et retombe sur `detail.mandants_texte` — le
texte **brut de Hektor**, intact dans le payload. Sur une ligne contaminée, le document
imprimerait **BANO au lieu de SOUVIGNET**.

À faire, trois endroits :
1. `editorFullContacts` ← `mandants_registre_json` d'abord, `proprietaires_json` en repli ;
2. `editorPartialContacts` ← `selectedDetail.mandants_json` (24 451 lignes l'ont) ;
3. `mandantsLibelle` (App.tsx ~4440) ← la **liste de contacts** avant `detail.mandants_texte`.

## ③ MASQUER `mandat_montant` DANS LE DÉTAIL DU DOSSIER

Mon masquage porte sur `app_mandat_register_current.mandat_montant` — **que le front ne
lit pas**. Les deux usages réels lisent le **détail du dossier** :

```
App.tsx ~17978  detail.mandat_montant -> rubrique Mandat V3   (V3 est ALLUMÉ)
App.tsx ~4447   detail.mandat_montant -> dernier recours des HONORAIRES du PDF
```

**31 fiches** portent encore un montant faux, dont **5** sans aucun autre honoraire —
celles-là pourraient l'imprimer sur un document contractuel :

```
61811:18466  17/03  Actif       prix  71 000  -> montant affiche  95 000
62049:18602  13/05  Sous offre  prix 160 000  -> montant affiche  45 000
62567:18718  24/06  Actif       prix 275 000  -> montant affiche  55 000
62001:18749  07/07  Actif       prix 665 000  -> montant affiche 130 000
24113:18787  28/07  Actif       prix 128 787  -> montant affiche  69 000
```

Le marqueur existe : `charger_corps_suspects()` dans `export_app_payload.py`. Il suffit
de l'appliquer dans `build_trimmed_detail_payload` / `build_dossier_details`, qui
disposent de `hektor_annonce_id`.

⚠ **Fenêtre fermée** : les 31 vont de **mars à juillet 2026**, rien après — depuis août
Hektor ne donne plus de montant du tout (363 des 454 étaient déjà vides). C'est un
**stock fixe**, pas une hémorragie.

## ④ RETIRER `detail.mandat_montant` DE LA CHAÎNE DES HONORAIRES

```js
const rawHonoraires = firstNonEmpty(
  rawDetailProp(detail, 'mandat_infofi', 'HONORAIRES'),
  rawDetailProp(detail, 'mandat_infofi', 'HONORAIRES_ACQUEREUR'),
  valueFromJsonList(detail.honoraires_json, [...]),
  detail.honoraires_resume,
  detail.mandat_montant,          // <-- A RETIRER
)
```

Un **montant de mandat n'est pas un honoraire** : repli douteux par nature, même sans ce
bug.

## ⑤ POUSSER LES 18 COMMITS

```bash
cd C:\Hektor\Projet ; git push origin main
```

⚠ Le hook exige `GTI_ALLOW_PUSH=1`. Parmi les 18 : **le correctif de la régression du
05/10** (voir plus bas). ⚠ Ne pas stager `.gitignore` ni les deux
`phase2/docs/RAPPORT_*.md` — ils sont réécrits par le run.

## ⑥ LE PUSH DU REGISTRE VERS SUPABASE *(différé du 05/10 au soir)*

```bash
.venv\Scripts\python.exe phase2\sync\registre_mandats_upsert.py
```

24 487 lignes, ~90 s, **UPSERT seul, aucune suppression** — faisable pendant que l'agence
travaille. Différé seulement pour ne pas charger Supabase pendant le drainage des
documents.

## ⑦ LE SIGNALEMENT À LA BOÎTE IMMO

> Vous exigez `<id>-<FAMILLE>` à l'écriture (formulaire d'offre : `648-PROTEXA`) et vous
> **l'ignorez à la lecture**. `getMandatById("10")`, `("10-PROTEXA")` et `("10-HEKTOR")`
> rendent **tous les trois** le mandat HEKTOR 16564 de 2024. Votre fiche annonce fait de
> même : elle renvoie **le montant et les mandants du mandat HEKTOR** sous **le numéro et
> les dates du mandat PROTEXA**. **454 mandats** concernés depuis mars 2026.

---

# ⚠⚠ LA RÉGRESSION DU 05/10 — à vérifier au réveil

J'avais cassé le **chemin immédiat du worker** pendant neuf heures :

```
TypeError: tuple indices must be integers or slices, not str
   charger_mandants_du_registre_des_liens -> ligne["ann"]
```

La fonction lisait les colonnes **par nom**, ce qui exige `row_factory = sqlite3.Row`.
`registre_mandats_upsert.py` le pose, mes contrôles aussi — **`push_single_annonce_to_supabase.py`
NON**. `refresh_console_data` a échoué **9 fois** entre 13:10 et 16:34 : une modification
d'annonce n'était plus poussée en ~1 min, et **rien ne le disait à l'écran**.

Corrigé (`3607d29`) par un **accès par position**, éprouvé dans la condition qui
échouait. **À vérifier demain : 0 nouvelle erreur `refresh_console_data` après 21h.**

➡ La leçon : **une fonction appelée par plusieurs chemins ne suppose pas la forme des
lignes.** J'avais éprouvé trois fois — toujours par le chemin qui pose `row_factory`.

---

# CE QUI RESTE NOTÉ, SANS URGENCE

- **2 numéros brûlés le même jour** à clôturer chez Hektor : 63073 (18883/18884, 18/09) ·
  63132 (18894/18895, 22/09). Un numéro émis ne disparaît pas d'un registre : la clôture
  se fait chez eux.
- **1 mandat du miroir sans annonce** (sur 94 lignes, 93 sont des doublons de la vague du
  27/08).
- **le lien MARULAZ** : `mandants(idAnnonce: 48100)` de Hektor connaît Sylvain MARULAZ
  (603108) comme mandant, et notre registre des liens ne l'a pas. Piste : lire les
  mandants par cette API plutôt que les déduire.
- **687+ contacts** dont le `display_name` porte la raison sociale à la place du nom de
  famille (SCI, Indivision). Phénomène **ancien** (5-7 % sur 2011-2014, 1 % depuis).
  Touche l'annuaire, la recherche, les documents. Voir mémoire
  `contacts-nom-famille-remplace-par-raison-sociale`.
- `busy_timeout` sur `pull_from_supabase.py` · le garde-fou d'ordonnancement
  descente / quotidien.

---

# LES OUTILS DE DIAGNOSTIC ÉCRITS LE 05/10

⛔ **Aucun n'est appelé par le run** — ce sont des sondes, en lecture seule.

| | |
|---|---|
| `Console/introspect_mandats_query.js` | l'introspection GraphQL (coupée chez Hektor) |
| `Console/sonde_mandats_graphql.js` | trouve les champs par les messages d'erreur du serveur |
| `Console/sonde_mandants_annonce.js` | `mandants(idAnnonce)` — la requête **dédiée**, qui marche |
| `Console/comparer_mandants_api_vs_liens.js` | leur API contre notre registre : **5 cas contaminés sur 5**, elle confirme nos noms |
| `Console/sonde_getmandatbyid.js` | `getMandatById` — c'est elle qui a prouvé la cause |
| `Console/sonde_mandat_prix_web.js` | **l'épreuve ① de demain** |

⚠ Le jeton valide est dans `Console/token_dump.json` (celui de `storage_state.json` a
expiré le 29/06). L'endpoint exige un en-tête `Authorization` — les cookies ne suffisent
pas.
