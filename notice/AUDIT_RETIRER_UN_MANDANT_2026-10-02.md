# AUDIT — RETIRER UN MANDANT D'UN BIEN

**02/10/2026** · demandé par Frédéric · `L5` / `E.0-bis`
**Version 2** — après observation directe de Hektor (session Chrome d'Emmanuelle PEREIRA).

> **Énoncé** : *« faire le worker désassocier un mandant, donc retirer aussi sa relation,
> vérifier que Hektor accepte. Ensuite il faut que cette écriture soit immédiatement dans
> l'app et le serveur. Cela doit interagir sur le registre des relations. **RÈGLE : si un
> numéro de mandat a été généré, impossible de retirer des mandants.** Dans tous les autres
> cas, bien prévenir l'utilisateur avant la validation du worker. »*
> **Et** : *« il faut être sur un accès NÉGOCIATEUR dans Hektor, pas admin — c'est ce qui
> fait du 403. »*

⚠ **Audit limité au geste « retirer un mandant d'un bien ».** Les autres objets (annonce,
recherche, transaction, document, RDV) ne sont pas mesurés.

---

## 1. ✅ HEKTOR ACCEPTE — et voici l'appel exact

**Observé en direct le 02/10**, bien `63112` (mandat 18886, Firminy, négociateur
Emmanuelle PEREIRA — *son propre bien*).

⚠ **Le menu n'est PAS sur la ligne du mandat, il est sur la ligne du MANDANT**, dans le
bloc « Mandant » en tête de l'onglet Mandat :

```
Mandant
NOM                   INFORMATION      DATE         COORDONNEES              ⋮
M. GENEVRIER PASCAL   Bien achete le   21-09-2026   06xx xx xx xx            ⋮
                                                                             │
   ┌─────────────────────────┐                                               │
   │ Voir la fiche du contact│ ◄─────────────────────────────────────────────┘
   │ Envoyer un Email        │
   │ Poser un rendez-vous    │
   │ Détacher le contact     │  ◄── LE GESTE
   └─────────────────────────┘
```

**L'appel, lu dans le `onclick` puis dans le corps de la fonction — rien n'a été exécuté :**

```js
degroupproprioForAnnonce(id, idann, fromAnnonce = false)

$j.ajax({ url: 'xmlrpc.php',
          data: { mode: 'degroupproprio', id: <idContact>, idann: <idAnnonce> } })
```

⭐ **Symétrie parfaite avec le rattachement que le worker fait déjà** — mêmes paramètres :

```
RATTACHER   mode=selectnouveauproprio_sup   &id=<contact>&idann=<annonce>   (worker:14926)
DETACHER    mode=degroupproprio             &id=<contact>&idann=<annonce>   (observé 02/10)
```

### ⚠ Hektor ne demande AUCUNE confirmation

```
degroupproprioForAnnonce : confirm() -> ABSENT
```

Un clic, le contact est détaché. **C'est donc à notre app de prévenir** — l'exigence de
Frédéric n'est pas un confort, elle comble un manque réel de Hektor.

---

## 2. ✅ LES DROITS — la réponse au 403, et elle existe déjà

**Prouvé à l'écran sur trois biens :**

| bien | négociateur | résultat |
|---|---|---|
| 63175 Riotord | Nadege PEYRARD | *« Vous n'avez pas le droit de modifier ce bien »* · **pas de menu** |
| 63205 Saint-Étienne | Mélanie LEGRAND | idem · **pas de menu** · page en lecture seule |
| **63112 Firminy** | **Emmanuelle PEREIRA** *(la session)* | **page complète, menu présent** |

➡ **Les droits sont par NÉGOCIATEUR, pas par agence.** Un admin ne suffit pas, et un
négociateur ne peut pas agir sur le bien d'un autre.

### ⭐ Le worker sait déjà faire — `handleLinkHektorMandant` l'applique

```js
const dossier = await loadDossier(job);
await ensureHektorExecutionContext(job, dossier, payload, {
  preferRequester: true,      // d'abord le negociateur QUI DEMANDE
  preferDossierOwner: true,   // sinon le proprietaire DU DOSSIER
  required: true              // ⛔ pas de contexte -> PAS D'ECRITURE
});
```

Et la bascule elle-même **nomme le 403 exactement** :

```js
async function switchHektorUserContextWithPlaywright(idUser) {
  page.goto(`${ADMIN_URL}?call=authenticate&mode=autologin&idUser=<negociateur>`)
  if (loginResponse.status() === 403) throw `Hektor 403 on context switch autologin idUser`
  if (adminResponse.status()  === 403) throw `Hektor 403 after context switch autologin idUser`
  // puis CONFIRME la bascule en relisant localStorage.impersonate
}
```

➡ **Le nouveau geste doit recopier cette ligne, à l'identique.** C'est la seule précaution
à prendre, et elle est déjà écrite et éprouvée.

---

## 3. ✅ LA RÈGLE DE FRÉDÉRIC EST LA BONNE — mesurée

> *« Si un numéro de mandat a été généré, impossible de retirer des mandants. »*

**Elle est meilleure que celle que j'avais proposée (« si le mandat est signé »)**, pour
trois raisons :

1. **Elle est mesurable aujourd'hui** — `numero_mandat` existe. L'état « signé », lui,
   **n'existe nulle part** dans la base (0 colonne sur `app_mandat`, 0 sur
   `app_console_document` ; il vit chez ImmoSign, côté Hektor).
2. **Elle se trompe du bon côté** — un mandat peut avoir un numéro sans être signé, donc
   elle bloque *plus* de cas. Une règle de sécurité doit refuser par défaut.
3. **Elle ne demande aucun rapprochement par le nom.** `app_mandat.mandants_texte` est une
   phrase d'affichage (*« Guy BOURGIN gérant SARL RESIDENCE AMPERE16 avenue Jean FAURE »* —
   nom et numéro collés) : s'y fier serait **deviner**.

### Ce qu'elle laisse ouvert — mesuré sur deux sources indépendantes

```
biens vivants                                13 462
avec un numero de mandat  -> BLOQUES            715   ( 5,3 %)
sans numero  -> RETRAIT POSSIBLE             12 747   (94,7 %)

(meme resultat par app_mandat et par app_dossiers_current.numero_mandat)
tous les mandats de app_mandat ont un numero : 0 sans
```

⚠ **Et une question à part, qui mérite d'être posée** : que 94,7 % des biens vivants
n'aient aucun numéro de mandat chez nous n'est pas anodin. Ce n'est pas le sujet du jour,
mais ce n'est pas normal non plus.

---

## 4. ⚠ OÙ POSER LE BOUTON — et le vrai piège

**La rubrique demandée** : cockpit, `App.tsx:24947`

```js
{ key: 'contact', label: 'Contact', sub: 'Mandants · syndic · notaires', ... }
```

Le bouton va **sur la ligne de chaque mandant**, à côté de ce qui existe déjà :

```
App.tsx:3379   <button>Rattacher un mandant existant</button>
App.tsx:3123   MandantsEnCreation -- l'etiquette provisoire « En creation… »
```

### ⛔ LE PIÈGE : la rubrique ne lit pas le registre

```js
App.tsx:17596   buildDetailContactsFromProprietaires(detail.proprietaires_json, ...)
```

**Le front lit bien NOTRE base** (`app_dossier_detail_current` dans Supabase) — il
n'appelle jamais Hektor. Mais le champ qu'il lit est **la copie du détail Hektor**,
rafraîchie par le run — **pas `app_relation`, notre registre**.

➡ **Conséquence directe : écrire `retire_le` dans le registre ne ferait PAS disparaître le
mandant de cette rubrique.** Les deux écrans ne lisent pas la même chose :

| écran | source | `retire_le` le fait-il disparaître ? |
|---|---|---|
| fiche CONTACT → ses annonces | `app_contact_relations_current` *(le registre)* | ✅ oui, la vue filtre dessus |
| **fiche ANNONCE → rubrique Contact** | `proprietaires_json` *(copie Hektor)* | ⛔ **non** |

**Il faut donc un calque optimiste de RETRAIT**, pendant exact de `MandantsEnCreation` :
masquer la ligne dès le clic, jusqu'à ce que Hektor confirme et que le détail redescende.

---

## 5. LA PLACE DE `retire_le`

Les colonnes existent depuis le 30/09, pour la décision : *« le retrait part chez Hektor et
la ligne reste chez nous, datée »*. Le travail du 02/10 (`78b61b3`) fait que le serveur
**adopte** le retrait depuis la doublure, sans quoi le push de la nuit l'effacerait.

⛔ **Mais il est INCOMPLET pour ce geste** : il **pose** un retrait et ne le **retire
jamais**. Or il faut pouvoir l'annuler — **si Hektor refuse**, le calque optimiste doit
revenir en arrière. Ce complément s'écrit **avec** le geste, pas avant.

⚠ Et il exige une étape de run **non encore posée** (`pull_from_supabase --table
app_relation` avant le push) : sans elle, la doublure a 23 h de retard.

---

## 6. LA CHAÎNE COMPLÈTE

```
① LE FRONT       bouton sur la ligne du mandant, dans la rubrique « Contact »
                 · GRISE si le bien a un numero de mandat      <- la regle de Frederic
                 · AVERTISSEMENT explicite avant validation    <- Hektor n'en fait aucun
② UNE RPC        pose le travail + le calque optimiste de retrait
                 -> la ligne disparait A LA SECONDE
③ LE WORKER      ensureHektorExecutionContext(..., required: true)   <- LE 403
                 puis mode=degroupproprio&id=<contact>&idann=<annonce>
                 puis CONFIRME ou ANNULE le calque
④ LE SERVEUR     adopte retire_le depuis la doublure           ✅ FAIT (78b61b3)
                 ⚠ exige l'etape de doublure avant le push     ⛔ PAS POSEE
⑤ LE REGISTRE    app_relation garde la trace, datee et nominative
```

⭐ **L'ordre est celui, éprouvé le 30/09, de « créer un contact et le rattacher » : LE
TRAVAIL D'ABORD** — c'est lui qui porte les garde-fous ; s'il refuse, rien ne s'écrit.

---

## 7. CE QUI RESTE À DÉCIDER OU À ÉPROUVER

```
⬜ EPROUVER LE RETRAIT EN REEL     sur un bien d'essai, avec accord explicite
   (observe mais JAMAIS execute -- c'est une ecriture chez Hektor)
⬜ Hektor refuse-t-il de lui-meme si le mandat est signe ? inconnu
⬜ que fait degroupproprio quand le contact est mandant de PLUSIEURS biens ?
⬜ le 3e parametre `fromAnnonce` : son role exact n'est pas etabli
⬜ l'etape de doublure dans le run (prerequis de ④)
```

## 8. CE QUI N'A PAS ÉTÉ MESURÉ

- le comportement réel de `degroupproprio` *(jamais exécuté)*
- `metadata_json` de `app_console_document` *(pourrait porter un état de signature)*
- les autres objets du tableau des gestes *(hors périmètre, annoncé en tête)*
