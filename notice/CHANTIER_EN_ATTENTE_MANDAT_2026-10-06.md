# CHANTIER EN ATTENTE — mandats : registre · fiche · édition du PDF

**Écrit le 05/10/2026 au soir pour la reprise du 06/10. Réécrit en fin de session après
relecture de tout l'échange.**

| | |
|---|---|
| l'audit complet | `notice/AUDIT_REGISTRE_MANDATS_2026-10-05.md` — 13 sections |
| l'audit des mandants | `notice/AUDIT_MANDANTS_REGISTRE_MANDATS_2026-10-04.md` |
| le précédent de 2026-08 | `notice/NOTE_CHAINE_DES_MANDATS_2026-08-25.md` — §5 et §6, **à relire** |
| la sentinelle | `phase2/checks/mandat_corps_recopie.py` |
| les sondes | `Console/sonde_*.js` — **diagnostic, jamais appelées par le run** |

---

# PARTIE 1 — CE QUI EST EN PRODUCTION. NE PAS LE REFAIRE.

| | mesure |
|---|---|
| les mandants du registre viennent de **notre registre des liens** | 24 451 / 24 487 · **607** lignes comblées, **31** restent vides |
| colonne `mandants_json` (nos **deux** identifiants par personne) | patch SQL collé, table **et** vue |
| notre liste est **prioritaire**, Hektor en repli | 23 640 lignes affichent désormais notre forme |
| `search_text` assaini | « BANO » ne ramène plus le bien de SOUVIGNET |
| `mandat_montant` masqué **au registre** | **454** lignes — ⚠ mais le front **ne lit pas** cette colonne |
| la sentinelle | corps recopié **91** · couples à deux mandats **31** · deux numéros le même jour **2** |
| le filet de colonne absente | `colonne_disponible()` + `adapter_registre_au_schema()` |
| la fiche mandat affiche les bons noms | commit `e3c1e2b` — **attend le push** pour être déployé |
| la régression du 05/10 | **corrigée** `3607d29` — voir Partie 5 |

⭐ **Et tout est autonome** : 0 appel Hektor dans `export_app_payload` /
`push_upgrade_to_supabase` / `registre_mandats_upsert`. Le critère se calcule sur le
miroir **local** ; Hektor éteint, le masquage fonctionne à l'identique.

### L'identité du registre est saine — 7 contrôles, 7 zéros

```
app_mandat : 26 835 · app_mandat_id nul 0 · en doublon 0 · couple (annonce,numero)
             en doublon 0 · numero vide 0 · plage de l'app envahie 0 ·
             present_in_hektor=0 -> 0 · lignes du registre absentes de app_mandat 0
2 072 mandats portent NOTRE numero sans celui de Hektor
```

### ⭐ La clé (annonce, numéro) a tenu, et c'est mesuré

Sur les cas où l'identifiant Hektor est partagé : **182 lignes du miroir → 182 de nos
lignes, aucune fusion**, et la bonne ligne gardée **31 fois sur 31**. Avec une clé sur
l'identifiant de Hektor, **91 mandats auraient disparu**.

---

# PARTIE 2 — LA CAUSE, ÉTABLIE. Ce n'est PAS un recyclage.

L'identifiant complet d'un mandat chez Hektor est **`<id>-<FAMILLE>`** — le projet l'avait
déjà écrit le **25/08** (`NOTE_CHAINE_DES_MANDATS` §6) :

> *« Hektor n'attend pas un numéro mais un couple `<id>-<FAMILLE>` — `648-PROTEXA` ou
> `9887-HEKTOR` — et une valeur amputée est ignorée sans erreur. »*

L'agence est passée aux mandats **PROTEXA en mars 2026**, et PROTEXA numérote **depuis 1** :
`10-PROTEXA` et `10-HEKTOR` sont **deux mandats différents**. Sur 449 identifiants nus
partagés, **446 portent les deux familles**. Les 454 lignes marquées sont **PROTEXA à 100 %**.

⛔ **Mais la lecture résout sur l'identifiant NU** :

```
getMandatById("10")          -> numero 16564, 2024, 82 000  (HEKTOR)
getMandatById("10-PROTEXA")  -> LE MEME
getMandatById("10-HEKTOR")   -> LE MEME
```

Le bloc mandat de la fiche annonce fait pareil : il renvoie **le montant et les mandants
du mandat HEKTOR** sous **le numéro et les dates du mandat PROTEXA**.

⭐ **La donnée existe chez eux** — ce sont ses dates de 2026 qui nous parviennent. C'est sa
**résolution** qui échoue. Le jour où ils corrigent, le montant revient au run suivant et
notre masque **se lève seul** (il se déclenche sur la collision d'identifiant nu).

### La preuve que le critère est le bon — 1 % contre 99 %

```
PROTEXA AVEC jumeau HEKTOR  (446 masques)  : montant == prix sur   1 des  88  (  1 %)
PROTEXA SANS jumeau       (1 216 epargnes) : montant == prix sur 522 des 526  ( 99 %)
```

Il ne sur-masque pas et ne sous-masque pas. Et il est **complet par construction** : la
série HEKTOR va de 1 à 79 720, la PROTEXA de 3 à 26 047 — un nouveau mandat PROTEXA
collisionne **forcément**, donc il sera marqué sans intervention.

---

# PARTIE 3 — DEMAIN, DANS L'ORDRE

## ⓿ Vérifier la nuit — 5 minutes, lecture seule

```bash
python phase2/checks/mandat_corps_recopie.py
```

| quoi | attendu |
|---|---|
| le **rattrapage documents** a drainé | 2 211 pending → 0, fin vers **04:10** (rythme mesuré ~5,8/min) |
| ⭐ **ma régression est bien réparée** | **0 erreur `refresh_console_data`** après 21h — c'est LA vérification du jour |
| le **quotidien** (05:00) et la **descente** (08:15) | 54 étapes, exit 0 |
| la sentinelle | 91 · 31 · 2 — si un chiffre **monte**, le défaut de Hektor s'aggrave |

## ① L'ÉPREUVE DE L'IDÉE DE FRÉDÉRIC — la porte est trouvée

**Ce qui a déjà été fait le 05/10 au soir, en lecture seule :**

```
session : les cookies du depot ont EXPIRE le 29/06 -> 403 sur les deux GET.
          Le worker garde une session FRAICHE par service :
             Console/sessions/storage_state_<kind>.json     (sync_light a 21:59)
          -> la sonde prend la plus recente en EVITANT celle du worker Documents.

mode=chargeannonce_MandatPrix&id=61811    HTTP 200,  84 294 car.
   -> un ONGLET : « Mandat N° 18466 » avec rel="49|0"
   -> 49 est l'IDENTIFIANT PROTEXA du mandat
   -> la page porte 71 000 (le prix) et 65 000, PAS le faux 95 000

mode=protexa-mandat&mandat=0&idann=61811  HTTP 200, 293 088 car.
   -> le formulaire de CREATION ; mandat=49 rend la MEME page. Ce n'est pas un lecteur.

⭐ les DEUX pages contiennent ASTIER -- le mandant que NOS LIENS donnent -- et PAS
  « LANGLADE » que le miroir porte. Une confirmation de plus que nos mandants sont justes.
```

**⭐⭐ LA PORTE DE LECTURE, trouvée dans le JS de la page :**

```js
function getThisInfoMandat(idMandat, idAnnonce, reloadHistory = false) {
  var dataSend = {
    mode: 'contacts-contactProfile-mandat-getInfoMandat',
    idMandat: idMandat,      // 49    <- lu dans rel="ID|0" de l'onglet
    idAnnonce: idAnnonce,    // 61811
    reloadHistory: reloadHistory
  };
  $j.ajax({ type: "POST", url: "xmlrpc.php", data: dataSend, ... })
}
```

**À FAIRE, dans cet ordre strict :**

1. **lire la fonction ENTIÈRE** dans la page déjà sauvegardée
   (`Console/exports/mandatprix_61811_mode_chargeannonce_MandatPrix.html`) — elle y est en
   clair, donc on confirme qu'elle ne fait que lire **sans toucher à Hektor** ;
2. puis, **avec l'accord de Frédéric**, l'appeler sur **UNE SEULE** annonce (61811 : affiche
   `95 000` pour un bien à `71 000`) et regarder si le vrai montant y est ;
3. si oui → **rattrapage console sur le modèle du chauffage** : un travail par annonce, sur
   **`WorkerAdmin` ou `WorkerActions`** — ⛔ **jamais** la file des documents. **Deux appels
   par annonce** : l'onglet pour l'identifiant PROTEXA, puis la lecture.

⛔⛔ **JAMAIS `mandat-postMandatVente` (qui enregistre) ni `mandat-supprime` (qui
supprime), ni les `step1`/`step2` du geste de génération** : ils créent un mandat et
**brûlent un numéro NON ANNULABLE** — c'est PROTEXA qui le fabrique, mention légale,
série cotée sans discontinuité.

## ② RENDRE LA MODALE DU REGISTRE AUTONOME — **la plus importante**

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

Trois endroits :
1. `editorFullContacts` ← `mandants_registre_json` d'abord, `proprietaires_json` en repli ;
2. `editorPartialContacts` ← `selectedDetail.mandants_json` (24 451 lignes l'ont) ;
3. `mandantsLibelle` (App.tsx ~4440) ← la **liste de contacts** avant `detail.mandants_texte`.

⚠ `VITE_RUBRIQUE_CONTACT_REGISTRE` vaut `'1'` par défaut — l'interrupteur est **allumé**.

## ③ MASQUER `mandat_montant` DANS LE DÉTAIL DU DOSSIER

Mon masquage porte sur `app_mandat_register_current.mandat_montant` — **que le front ne lit
pas**. Les deux usages réels lisent le **détail du dossier** :

```
App.tsx ~17978  detail.mandat_montant -> rubrique Mandat V3   (⚠ V3 est ALLUME)
App.tsx  ~4447  detail.mandat_montant -> dernier recours des HONORAIRES du PDF
```

**31 fiches** portent encore un montant faux, dont **5** sans aucun autre honoraire —
celles-là pourraient l'imprimer sur un document contractuel :

```
61811:18466  17/03  Actif       prix  71 000  ->  95 000
62049:18602  13/05  Sous offre  prix 160 000  ->  45 000
62567:18718  24/06  Actif       prix 275 000  ->  55 000
62001:18749  07/07  Actif       prix 665 000  -> 130 000
24113:18787  28/07  Actif       prix 128 787  ->  69 000
```

Le marqueur existe : `charger_corps_suspects()` dans `export_app_payload.py`. À appliquer
dans `build_trimmed_detail_payload` / `build_dossier_details`, qui disposent de
`hektor_annonce_id`.

⚠ **Fenêtre FERMÉE** : les 31 vont de **mars à juillet 2026**, rien après — depuis août
Hektor ne donne plus de montant du tout (363 des 454 étaient déjà vides). **Stock fixe,
pas hémorragie.** Statuts : 17 Actif · 9 Sous compromis · 3 Sous offre · 2 Estimation.

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

Un **montant de mandat n'est pas un honoraire** : repli douteux par nature, même sans ce bug.

## ⑤ VALIDER LE FRONT ET POUSSER

```bash
cd apps\hektor-v1 ; npm run build
cd C:\Hektor\Projet ; git push origin main
```

**19 commits.** ⚠ Le hook exige `GTI_ALLOW_PUSH=1`. Rien n'est sauvegardé hors de cette
machine, et parmi eux il y a **le correctif de la régression**. ⚠ **Ne pas stager**
`.gitignore` ni les deux `phase2/docs/RAPPORT_*.md` — ils sont réécrits par le run.

## ⑥ LE PUSH DU REGISTRE VERS SUPABASE *(différé du 05/10 au soir)*

```bash
.venv\Scripts\python.exe phase2\sync\registre_mandats_upsert.py
```

24 487 lignes, ~90 s, **UPSERT seul, aucune suppression** — faisable pendant que l'agence
travaille. Différé seulement pour ne pas charger Supabase pendant le drainage.

## ⑦ LE SIGNALEMENT À LA BOÎTE IMMO

> Vous exigez `<id>-<FAMILLE>` à l'écriture (formulaire d'offre : `648-PROTEXA`) et vous
> **l'ignorez à la lecture**. `getMandatById("10")`, `("10-PROTEXA")` et `("10-HEKTOR")`
> rendent **tous les trois** le mandat HEKTOR 16564 de 2024. Votre fiche annonce fait de
> même : elle renvoie **le montant et les mandants du mandat HEKTOR** sous **le numéro et
> les dates du mandat PROTEXA**. **454 mandats** concernés depuis mars 2026.
> Reproductible chez vous en cinq minutes.

**Et dans le même message, la demande d'export** « liste mandat » du **01/03/2026 à
aujourd'hui** : c'est la seule source qui ait jamais porté ces montants. Le lecteur existe
déjà (`phase2/sync/manual_mandat_corrections.py`, qui lit le fichier de **février**).
⚠ Il faudra l'autoriser à **corriger** un corps faux, pas seulement à **combler** un vide
(`if (mandats) return data` renonce dès qu'un mandat existe).

---

# PARTIE 4 — NE PAS CONFONDRE : LES DEUX GROUPES DE 31

```
groupe A : 31 lignes SANS MANDANT au registre
groupe B : 31 fiches dont le DETAIL porte un montant faux
en commun : 0        <- le meme chiffre par pure coincidence
```

**Le groupe A n'a rien à corriger :**

```
annees : 2011 (3) · 2012 (3) · 2013 (7) · 2014 (2) · 2016 (11) · 2017 (1) · 2021 (1)
statut : 29 « Clos » · 1 « Vendu » · 1 « Estimation »   ·   29 sur 31 archivees
avec un mandants_json quand meme : 0   -> PERSONNE ne les connait
la plus recente : 2021-05-04
```

⭐ Et **10 des 31 portent le même numéro `10249` du 15/03/2016** — annonces 36027 à 36036,
« PROGRAMME NEUF », « TYPE 2 DE 39M² »… **C'est un programme neuf : un seul mandat couvrant
dix lots**, et le mandant est chez le promoteur. C'est le cas légitime que la sentinelle
compte à part (117 identifiants).

**Les 39 annonces à plusieurs lignes au registre sont elles aussi légitimes** : 24
renouvellements (années différentes) + 13 dans l'année + **2** vrais doublons (deux numéros
émis le même jour par PROTEXA, à clôturer chez Hektor).

---

# PARTIE 5 — ⚠⚠ LA RÉGRESSION DU 05/10, à vérifier au réveil

```
TypeError: tuple indices must be integers or slices, not str
   charger_mandants_du_registre_des_liens -> ligne["ann"]
```

La fonction lisait les colonnes **par nom**, ce qui exige `row_factory = sqlite3.Row`.
`registre_mandats_upsert.py` le pose, mes contrôles aussi — **`push_single_annonce_to_supabase.py`
NON**. `refresh_console_data` a échoué **9 fois** entre 13:10 et 16:34 (annonces 63158,
61895, 63081, 63156) : une modification d'annonce n'était plus poussée en ~1 min, et **rien
ne le disait à l'écran**. C'est exactement le chemin de l'autonomie.

Corrigé `3607d29` par un **accès par position**, éprouvé dans la condition qui échouait
(58 594 annonces lues sans `row_factory`, résultat identique avec).

➡ **La leçon, écrite dans le code** : une fonction appelée par **plusieurs chemins** ne
suppose pas la forme des lignes. J'avais éprouvé trois fois — toujours par le chemin qui
pose `row_factory`.

---

# PARTIE 6 — CE QUI RESTE NOTÉ, SANS URGENCE

| | |
|---|---|
| **2 numéros brûlés** | 63073 (18883/18884, 18/09) · 63132 (18894/18895, 22/09) — la clôture se fait **chez Hektor** : un numéro émis ne disparaît pas d'un registre |
| **1 mandat du miroir sans annonce** | sur 94 lignes sans annonce, 93 sont des doublons de la vague du 27/08 ; le vrai manque est **1** |
| **le lien MARULAZ** | `mandants(idAnnonce: 48100)` connaît Sylvain MARULAZ (603108) et notre registre des liens ne l'a pas → ⭐ **piste : lire les mandants par cette API** plutôt que les déduire, ce qui comblerait les liens manquants |
| **687+ contacts** | le `display_name` porte la raison sociale à la place du nom (SCI, Indivision). **Ancien** : 5-7 % sur 2011-2014, 1 % depuis. Touche annuaire, recherche, documents. Mémoire `contacts-nom-famille-remplace-par-raison-sociale` |
| **les mandants cliquables** | `mandants_json` porte déjà les deux identifiants par personne — il ne reste que l'écran. Chantier séparé |
| ⛔ **les GESTES du mandat** | **2** gestes worker contre **9** pour l'annonce · **0** RPC optimiste · « Modifier le montant » / « Annuler » / « Résilier » ne font qu'un `INSERT` dans `app_diffusion_request`. **C'est le vrai retard d'autonomie du mandat** |
| **`app_mandat_mandant`** | une table mandat × contact serait la réponse de fond pour un historique fidèle. **Écartée** : 99,7 % des annonces n'ont qu'un mandat, les divergences valent 0,8 %. À ne rouvrir que si le besoin apparaît |
| **DÉDUIRE le montant du mandat à partir du prix** | **testée et écartée** : 80 % de justesse même quand le prix n'a pas bougé, et l'historique de prix ne démarre qu'au 05/06/2026 (303 lignes). Inacceptable pour une mention contractuelle. ⚠ **Écarter la DÉDUCTION n'écarte pas la RÉCUPÉRATION** — voir l'encadré ci-dessous |
| **les restes du run** | `busy_timeout` sur `pull_from_supabase.py` · le garde-fou d'ordonnancement descente / quotidien |

---

### ⚠⚠ NE PAS CONFONDRE « LE PRIX » ET « LE MONTANT DU MANDAT »

Ce sont **deux champs différents** sur la même ligne du registre, et une phrase mal
tournée de ma part le 05/10 a brouillé les deux.

```
prix            = le prix de l'ANNONCE   -> ON L'A DEJA, et c'est le DERNIER (206/206)
                  le suivi des baisses tourne : 303 evenements, 207 lignes avec historique
                  -> RIEN A RECUPERER

mandat_montant  = le montant du MANDAT   -> c'est LUI qui manque sur les 454
```

**Ce qui est écarté, c'est de DEVINER le second à partir du premier** (80 % de justesse).
**Aller chercher le vrai montant reste entièrement ouvert**, et c'est même la priorité ① :

| | |
|---|---|
| ⭐ **l'écran web de Hektor** (`getInfoMandat`) | la porte est **trouvée** — rattrapage console sur le modèle du chauffage. **La voie n°1** |
| **l'export « liste mandat »** mars → aujourd'hui | la vraie valeur, et le lecteur existe déjà |
| **leur correctif** | le montant revient seul au run suivant |

⚠ Et `app_mandat_mandant` n'avait **rien à voir avec le montant** : c'était une table pour
garder **quels mandants ont signé quel mandat**. Écartée parce que 99,7 % des annonces
n'ont qu'un seul mandat — le registre des liens suffit.

---

# PARTIE 7 — CE QUI EST VÉRIFIÉ ET N'A PAS BESOIN D'ÊTRE REVU

| | mesure |
|---|---|
| le **prix du listing** est bien celui de l'annonce | et c'est **le dernier** : 206 / 206 égaux à la dernière valeur de l'historique |
| la **fonction qui suit les prix** tourne | 303 événements du 05/06 au 04/10 · 207 lignes avec historique |
| les **doublons** dus aux identifiants Hektor | **résolus** : 0 doublon technique |
| le **bon mandat est lié** aux 454 | 436 / 454 ont `numéro == no_mandat de l'annonce` ; les 18 autres sont les annonces à plusieurs mandats |
| les **31** du groupe B ont tout bon au registre | mandant **31/31** · json **31/31** · id annonce **31/31** · date **31/31** · **prix 31/31** |
| le **worker ne passe pas par Render** | 0 occurrence — un `git push` ne coupe pas son drainage |
| les **4 services** sont des services **Windows locaux** | ils tournent depuis l'arbre de travail : un push ne les redémarre pas |
| une **session Hektor en parallèle** ne gêne pas le worker | mesuré : 0 erreur sur 578 running + 288 done pendant mes sondes |

---

# LES OUTILS ÉCRITS LE 05/10

⛔ **Aucun n'est appelé par le run.** Lecture seule, diagnostic.

| | |
|---|---|
| `Console/introspect_mandats_query.js` | l'introspection GraphQL — **coupée** chez Hektor |
| `Console/sonde_mandats_graphql.js` | trouve les champs par les messages d'erreur du serveur |
| `Console/sonde_mandants_annonce.js` | `mandants(idAnnonce)` — la requête **dédiée**, qui marche |
| `Console/comparer_mandants_api_vs_liens.js` | leur API contre notre registre : **5 cas contaminés sur 5**, elle confirme nos noms |
| `Console/sonde_getmandatbyid.js` | c'est elle qui a prouvé la cause |
| `Console/sonde_mandat_prix_web.js` | **l'épreuve ① de demain** — prend la session fraîche du worker |

⚠ Le jeton GraphQL valide est dans `Console/token_dump.json` (celui de
`storage_state.json` a expiré le 29/06). L'endpoint exige un en-tête `Authorization` — les
cookies ne suffisent pas. Les **cookies** web, eux, sont dans
`Console/sessions/storage_state_<kind>.json`, rafraîchis par chaque service.
