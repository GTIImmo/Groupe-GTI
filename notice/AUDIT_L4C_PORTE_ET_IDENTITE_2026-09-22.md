# Audit avant `L4-c` — la porte avant la bascule

*22/09/2026. Demandé par Frédéric : « audite et explique-moi avant, respecte le plan de dev ».
Trois explorations : la base (moi), l'API + l'espace acquéreur, le worker + le front.*

> **CONCLUSION EN UNE LIGNE : `L4-c` n'est pas la prochaine étape. Fermer la porte l'est.**

---

## 1. Ce qu'on cherchait

Basculer l'identité du contact de `hektor_contact_id` vers `app_contact_id`. Question :
qu'est-ce qui casse ? Méthode : classer chaque endroit en **A** *(parle à Hektor — garde le
numéro Hektor)*, **B** *(relie nos données — doit prendre le nôtre)*, **C** *(affiche ou trace)*.

---

## 2. ⛔ LE RÉSULTAT QUI COMMANDE TOUT : neuf sortants ne passent pas par la porte

La porte est `cibleHektorContact()` *(`console_job_worker.js:1888`, posée le 21/09)*. Elle est
franchie par **7 sites**. **Neuf autres envoient un numéro à Hektor sans elle** :

| ligne | endroit | ce qui part | garde-fou |
|---|---|---|---|
| 11290 · 11337 · 11474 | assistant compromis / vente | `acquereurs[]`, `idProspect` | **aucun** |
| 11666 | changement de statut de transaction | `acquereurs[]` | **aucun** |
| 13391 · 13393 | qualification des acquéreurs | `idContact`, `idProspect` | **aucun** |
| 13431 · 13433 | archivage des recherches de qualification | `idCritere`, `Referer` | **aucun** |
| 14282 · 14321 | numéro de mandat (`protexa-valideStep4`) | `idMandants` | **partiel** |
| 18452 | création d'annonce, mandants existants | `selectnouveauproprio_sup` | **partiel** |

**VÉRIFIÉ À LA MAIN, les deux plus lourds :**

⛔ **`console_job_worker.js:13390` — la traduction est calculée PUIS JETÉE.**
```js
const { context } = await ensureContactSearchExecution(job, { hektor_contact_id: q.contactId });
const avant   = await listerCriteresBestEffort(q.contactId);      // <- le numéro BRUT
await createHektorContactSearchCriteria(job, q.contactId, ...);   // <- le numéro BRUT
```
`ensureContactSearchExecution` **rend** le numéro traduit ; on ne déstructure que `context`.

⚠ **`console_job_worker.js:14130` — le filtre ÉCARTE au lieu de traduire.**
```js
if (/^\d+$/.test(id) && Number(id) >= PLAGE_NUMEROS_APP) continue;
```
Le commentaire que j'ai écrit le 21/09 dit : *« le contact rejoindra la liste dès qu'il aura son
vrai numéro »*. **Rien ne le fait rejoindre.** Un mandant né dans l'app disparaît du mandat, en
silence, définitivement.

**CE N'EST PAS UN PROBLÈME DE `L4-c`, C'EST UN PROBLÈME DE `C.9`.** Ces sites-là sont
exactement ceux qu'une annonce créée depuis l'app emprunte : mandants, acquéreurs, mandat.
Ils sont inoffensifs aujourd'hui *(2 contacts nés dans l'app, aucun mandant, aucun acquéreur)*
et deviennent nuisibles **le jour où C.9 existe**.

---

## 3. Les comptes, couche par couche

```
                     A (Hektor)   B (nos donnees)   C (affichage)
API + espace              3             87               16
front                   ~35            ~60              ~21
worker            7 portes + 9 sortants non traduits
serveur (phase2)   50 (lisent le miroir)   le reste passe par identite_app()
```

**L'API est presque entièrement tournée vers nous** : 3 endroits sur 106 parlent à Hektor.

⚠ **`app_contact_id` n'apparaît NI dans le worker (0), NI dans le front (0).** La bascule
n'a donc **aucun point d'appui** dans le code applicatif : tout y est écrit sur
`hektor_contact_id`. C'est ce que disait déjà `patch_c2b_identite_contacts_2026-08-25.sql:78`
— *« PERSONNE NE LIT ENCORE app_contact_id »*.

---

## 4. Les trois dépendances HORS BASE — qu'aucune mesure SQL ne pouvait montrer

| | quoi | mesuré |
|---|---|---|
| **jetons signés** | le numéro est gravé dans `{"c": …}`, TTL **60 jours**, déjà parti dans des emails vers les acquéreurs — irrattrapable | **2 envois** |
| **JSON d'agenda** | figé dans `metadata_json->attendee_contacts`, interrogé par contenance — une colonne se migre, pas ça | **9 liens** |
| **lien « Ouvrir Hektor »** | `App.tsx:7920` fabrique l'URL Hektor avec le numéro, **hors de tout job** — la porte ne peut pas le protéger | 4 appels |

➡ L'exposition des jetons **grandira avec l'usage de l'espace acquéreur**. C'est un argument
pour basculer **tôt**, pas tard.

---

## 5. Les empreintes : la condition est REMPLIE

Trois vérifications indépendantes *(moi, l'exploration API, l'exploration worker)* :
**`build_contacts_layer.py` est le seul endroit du dépôt qui fabrique `contact_search_key` et
`relation_key`.** L'API les fait voyager telles quelles ; le worker **les relit depuis
Supabase** (l. 16711) au lieu de les recalculer.

⚠ **Une TROISIÈME empreinte trouvée** : `duplicate_group_id`, même fichier l. 1241, calculée
elle aussi sur des numéros de contact. **0 ligne** dans les deux tables de doublons : sans
effet aujourd'hui.

---

## 6. Les lignes humaines : moins qu'annoncé

```
app_notification           1 254 lignes, 1 106 sur une empreinte
                           ⚠ AUCUNE colonne de contact -- que l'empreinte
app_email_envoi               82, dont 24 sur empreinte
app_proposition               11    doublure 11/11
app_relance_rapprochement     10    doublure 10/10
app_bien_acquereur_statut      7    doublure  7/7
app_espace_visite_request      3    doublure  3/3
```

**Six tables sur sept portent déjà la doublure, remplie.** Et comme l'empreinte est **figée**
par `app_search_registry` et redonnée à chaque run, si le registre suit le contact
*(changement d'une ligne)*, **l'empreinte ne bouge pas** — donc ces lignes n'ont rien à
repointer. ⚠ **À PROUVER par la répétition sur copie, pas à supposer.**

---

## 7. L'ordre qui en découle

| | | |
|---|---|---|
| **L4-b′ — FERMER LA PORTE** | les 9 sortants passent par `cibleHektorContact` ; le filtre des mandants **traduit** au lieu d'écarter ; la traduction de `13390` cesse d'être jetée | **~1 j** |
| **L4-c — la bascule** | répétition sur copie, puis passage réel | ~2 j |
| **C.9 — la création d'annonce** | elle emprunte les sites de L4-b′ : elle vient après | |

**Pourquoi la porte d'abord** : elle est utile **tout de suite** *(elle protège C.9)*, elle est
**petite**, elle ne touche pas aux données, et elle est le **préalable technique** de la
bascule — un sortant non traduit enverrait un numéro d'app à Hektor le jour où l'identité
change.

---

## 7bis. ⛔⛔ LES DEUX SÉRIES SE CHEVAUCHENT — trouvé le 22/09 en codant `L4-c`

**J'allais rendre le registre des recherches « tolérant »** : qu'il retrouve sa ligne sous
l'ancien numéro **ou** sous le nouveau. Une mesure faite avant d'écrire l'a arrêté net.

```
contacts                                   356 137
plus grand numero HEKTOR                   605 461
plus grand numero APP (doublure)           356 137

NUMEROS PRESENTS DANS LES DEUX SERIES      194 687
   dont les deux numeros du MEME contact         4
   donc AMBIGUS : un numero, DEUX contacts  194 683
```

**194 683 numéros désignent un contact dans une série et un AUTRE contact dans l'autre.**
Plus de la moitié du parc. Un lecteur « tolérant » aurait rendu la mauvaise fiche 194 683
fois — sans erreur, sans trace, et avec des données parfaitement valides.

➡ **CONSÉQUENCE DE FOND : la bascule ne peut pas être progressive.** Pendant une période
mixte, un numéro seul **ne dit pas à quelle série il appartient**. Aucune tolérance n'est
possible : soit tout bascule d'un coup, soit les numéros deviennent auto-descriptifs.

### La sortie, et elle est déjà dans la doctrine du projet

Le 21/09 on a choisi que **la plage de l'app commence à 10 000 000** — pour les contacts nés
dans l'app, pour les annonces, pour les recherches. La doublure `app_contact_id` est
**antérieure à cette convention** et la viole : elle vit de 1 à 356 137, en plein dans la
série de Hektor.

**Déplacer la doublure dans la plage de l'app** *(`app_contact_id + 10 000 000`)* rend chaque
numéro **auto-descriptif** : `< 10 000 000` = Hektor, `>= 10 000 000` = nous. L'ambiguïté
disparaît, et une transition progressive redevient possible.

**Et ça ne coûtera JAMAIS moins cher qu'aujourd'hui**, parce que rien ne lit encore la
doublure *(0 occurrence dans le worker, 0 dans le front)* :

```
Supabase   relations 81 297 · contacts 61 975 · rapprochements 49 624
           recherches 11 382 · emails 24 · propositions 11      = 204 313 lignes
local      app_contact 356 137 · app_search_registry 77 070
```

C'est un décalage arithmétique sur une colonne que personne ne lit : mécanique, vérifiable,
et réversible par une soustraction.

➡ **`L4-c` gagne donc une étape ZÉRO : déplacer la doublure, avant tout le reste.**

---

## 8. Ce qui reste NON MESURÉ, et qui se dit

- Le **RDV / visite** n'a pas été balayé comme objet propre *(il apparaît par ricochet dans les
  liens d'agenda)*.
- `app_contact_consent` : `hektor_contact_id` y est porté mais la clé est `(email, canal)` —
  rattachement ou trace, non tranché.
- **Douze endroits ambigus** relevés par les explorations, dont trois qui comptent : le
  garde-fou `isdigit()` qui ne distinguera plus rien après bascule, le nom
  `hektor_contact_id` qui est un **paramètre public de l'API**, et les sentinelles
  `hektor_contact_id: ''` / `'invite'` / une adresse email qui montrent que le champ n'est
  pas toujours un numéro.
