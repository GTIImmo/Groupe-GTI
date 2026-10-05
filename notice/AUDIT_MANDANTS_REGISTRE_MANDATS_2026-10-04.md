# Les mandants manquants du registre des mandats — audit + plan

**04/10/2026.** Signalé par Frédéric : des lignes du registre des mandats n'affichent
aucun mandant, alors que la fiche annonce et le registre des relations les ont.

---

## LE FAIT, MESURÉ

```
24 487 lignes au registre
   638 sans mandant
       ├─ 607  que NOTRE registre des relations connaît   <- le défaut
       └─  31  que personne ne connaît                    <- normal, à laisser vide

le registre des relations couvre 24 451 des 24 487 lignes  (99,9 %)
```

⚠ **Ce ne sont PAS surtout des annonces actives** : 635 des 638 n'ont plus de fiche
dans l'app (vendues, archivées). Par ancienneté : 4 récentes (≥ 62000), 8 entre
55000 et 62000, 137 entre 40000 et 55000, **489 anciennes**.

---

## LA CAUSE — une colonne orpheline, PAS une mauvaise lignée

⭐ **Le registre des mandats EST autonome, et je m'étais trompé en disant l'inverse.**
`app_mandat` est notre table durable : 26 835 mandats, plage d'identifiants propre,
doublure, 2 sentinelles, et le worker y écrit à la naissance d'un mandat. Le registre
en est la projection.

**Le défaut porte sur UNE colonne sur 25** :

```
app_mandat : 25 colonnes
   qui nomment une personne :  1   (mandants_texte, un TEXTE)
   identifiants de contact   :  AUCUN
```

`mandants_texte` est la seule colonne restée un texte recopié de Hektor, sans
identifiant et sans chemin pour se remplir depuis chez nous :

```sql
-- view_generale.py:338
COALESCE( NULLIF(TRIM(m.mandants_texte),'') , NULLIF(TRIM(det.proprietaires_resume),'') )
-- deux sources, toutes deux Hektor.  « app_relation » : 0 occurrence dans ce fichier.
```

Quand Hektor ne fournit plus ce texte (bien vendu, archivé, fiche mandat incomplète),
**rien ne prend le relais** — alors que le registre des relations a justement été créé
pour garder ces liens-là (les 82 386 liens qu'un bien vendu emportait).

---

## ⚠ CE QUE LA MESURE A CHANGÉ AU PLAN

**Le multiple est la règle, pas l'exception :**

```
1 seul mandant   4 600  (19 %)      3 à 4      4 887  (20 %)
2               11 884  (49 %)      5 et plus  3 077  (13 %)
                              -> 81 % ont PLUSIEURS mandants
```

**Et le repli naïf écrirait du bruit** — mesuré sur les 607 :

```
1 241 personnes brutes  ->  974 après dédoublonnage     -22 % (267 doublons)
exemple : « M. SCI JCL | Mr./Mme SCI JCL »  = la même entité deux fois
```

C'est le problème connu des **fiches de couple** : Hektor crée une seconde fiche pour
le ménage, notre registre porte les deux à juste titre, mais on ne les affiche pas
deux fois.

Répartition après nettoyage : 308 à 1 mandant · 266 à 2 · 12 à 3 · 12 à 4 · 5 à 5 ·
3 à 6 · 1 à 7.

---

## LE PLAN

### L'endroit — un seul, et il sert les deux chemins

`build_mandat_register_rows()` dans **`phase2/sync/export_app_payload.py`**.

⭐ Il alimente **le push de nuit** (`push_upgrade_to_supabase.py`, run l. 1159) **ET**
**le push par annonce** (`push_single_annonce_to_supabase.py`, déclenché par le worker
en ~1 min). Une correction, les deux bénéfices.

⛔ **NE PAS corriger dans `mandat_ledger.py` (run l. 839)** : il s'exécute AVANT le
rafraîchissement des relations (l. 922) et lirait **les liens de la veille**. L'ordre
du run est le piège principal de ce chantier.

### Deux colonnes, deux rôles

| colonne | rôle |
|---|---|
| `mandants_json` *(neuve)* | la **liste** — un objet par personne avec **nos deux numéros**. C'est elle qui permettra les fiches cliquables (chantier suivant). |
| `mandants_texte` *(existante)* | rempli **en dernier recours**, dérivé de la liste, pour le listing compact et `search_text`. |

Le patron existe déjà dans ces deux tables : `versions_json`, `avenants_json`,
`register_history_json`, `register_avenants_json`. On ne crée pas une forme nouvelle.

### Les règles à tenir

- ⛔ **jamais d'écrasement** : si Hektor ou le détail ont fourni le texte, on ne touche
  à rien — les 23 849 lignes remplies doivent rester **identiques**.
- **dédoublonnage** sur le nom nu (sans civilité, sans accents, sans casse).
- **les liens retirés sont exclus** (`retire_le IS NULL`) — cohérent avec le geste
  « retirer un mandant » posé le 03/10.
- `search_text` se recalcule : ces 607 mandats deviendront **trouvables par le nom du
  mandant**, ce qu'ils ne sont pas aujourd'hui.

### L'ordre des gestes

1. **patch SQL** : la colonne `mandants_json` (Frédéric le colle).
2. **le code** dans `export_app_payload.py`.
3. **contrôle à blanc** : 607 comblées · **0 des 23 849 modifiée** · échantillon relu.
4. **une garde** dans `phase2/checks/relation_disparue.py` : « lignes du registre sans
   mandant alors que les relations savent » — **607 aujourd'hui, devra valoir 0**.

---

## CE QUE CE CORRECTIF NE FAIT PAS

⛔ Les mandants resteront **affichés**, pas **cliquables** : `mandants_json` portera les
numéros, mais l'écran du registre devra être repris pour en faire des liens. Chantier
séparé.

⛔ Et il ne touche en rien les **gestes** du mandat, qui restent le vrai retard :

```
                         fiche ANNONCE        fiche MANDAT
gestes du worker              9                   2  (PDF · numéro)
RPC optimistes               17 (app)             0
champs possédés par l'app   189 cartographiés     1 champ, 2 lignes
« Modifier le montant »     geste optimiste       ouvre une DEMANDE à un humain
```

Les boutons « Modifier le montant », « Annuler le mandat », « Résilier avant
l'échéance » font un `INSERT` dans `app_diffusion_request` — **aucun ne crée de travail
worker, aucun ne touche Hektor**.

---

## DEUX FAITS ÉTABLIS EN CHEMIN

- ⭐ **Le mandat a bien ses deux identités**, comme les autres objets :
  `app_mandat_id` (26 835/26 835) et `hektor_mandat_id` (24 763). Les 2 072 sans
  numéro Hektor portent quand même le nôtre — c'est l'autonomie qui fonctionne.
- ⛔ **Il n'existe PAS de numéro de mandat provisoire**, et c'est **volontaire** : le
  numéro est une mention légale (série « cotée sans discontinuité »), PROTEXA le
  fabrique, et le front confirme avant car **c'est non annulable**. C'est la seule
  place où l'utilisateur attend vraiment.
- ⚠ **`origine = 'app'` : 0 mandat.** Le mécanisme de naissance dans l'app est en
  service depuis le 30/09 et **n'a jamais servi**. Tout ce qui précède sur ce chemin
  est lu dans le code, **pas observé**.

---

# CE QUI A ETE FAIT — 05/10/2026

Les quatre gestes du plan sont poses. **Le patch SQL reste a coller** ; tant qu'il
ne l'est pas, le code se retire tout seul (voir le filet plus bas).

## ① Le patch SQL — `supabase/patch_mandants_json_registre_mandats_2026-10-05.sql`

La colonne `mandants_json` (`text`, comme toutes ses sœurs) **et la vue**
`app_registre_mandats_current`, qui enumere ses colonnes : sans le second ordre
la colonne existerait et resterait invisible au front — le bug se deplacerait.
Elle est ajoutee **en fin de liste** : `CREATE OR REPLACE VIEW` n'accepte que
cela, et cela preserve les droits (un `DROP` les perdrait).

## ② Le code — `export_app_payload.py`

Une seule source (`build_mandat_register_rows`), donc **les trois chemins** en
profitent : push de nuit, push par annonce (~1 min) et `registre_mandats_upsert`.

⚠ **Trois pieges que seule la mesure a montres** :

| ce que le code naif aurait fait | ce que la mesure a dit |
|---|---|
| lire **tous** les liens | le registre des liens porte **3 roles** : mandant 74 200 · proprietaire 58 479 · **acquereur_compromis 4**. Un acquereur serait devenu mandant. → liste blanche `{mandant, proprietaire}`, et les ecartes sont **comptes** sur stderr |
| joindre le contact par `hektor_contact_id` | **0 nom** sur 20 000. `app_contact_current.hektor_contact_id` porte **notre** identifiant (serie 10 000 001+) — la substitution d'identite du build. Par `app_contact_id` : **20 000 / 20 000** |
| afficher tous les noms | **11 857 liens vivants** pointent une fiche **muette** (« Contact 10309272 ») — 199 sur les 607. Un nom affiche sur cinq. → ecartes du **texte**, gardes dans le **JSON** avec leurs identifiants. Et les jeter **ne coute rien** : 0 ligne redevient vide, 196 perdent un nom sur plusieurs, le conjoint est nomme |

## ③ Le controle a blanc — **vert**

Le registre est construit **deux fois avec le meme code**, une fois le repli
neutralise (= l'ancien comportement exact), une fois tel quel, puis compare :

```
lignes au registre          :  24487
COMBLEES                    :    607   (attendu 607)      ✔
DEJA REMPLIES MODIFIEES     :      0   (doit valoir 0)    ✔
encore vides apres coup     :     31   (attendu 31)       ✔
lignes avec mandants_json   :  24451
```

`search_text` inclut deja `mandants_texte` : ces 607 mandats deviennent
**trouvables par le nom du mandant** sans une ligne de code en plus.

## ④ La garde — `phase2/checks/relation_disparue.py`

```
   -- le registre des mandats sait-il ce que les liens savent ? --
   lignes sans mandant           : 638 au total
      dont les liens les savent  : 607   (doit valoir 0)
```

⚠ **Les deux CAST ne sont pas decoratifs** : `hektor_annonce_id` est un `INTEGER`
au registre et un `TEXT` dans les liens. Sans eux la jointure est muette et la
garde **rend 0 en mentant** (mesure : 0 sans cast, 607 avec). Meme famille que
l'affinite qui a coute 79 minutes le 03/10.

## ⑤ EN PLUS DU PLAN — le filet qui empeche la nuit de tomber

PostgREST refuse **tout le lot** des qu'une colonne lui est inconnue (PGRST204).
Le code etant sur le disque **avant** que le patch soit colle, le push du
registre serait tombe **en entier** cette nuit. `colonne_disponible()` (la sœur
de `table_available()`, deja dans le fichier) et `adapter_registre_au_schema()`
retirent la colonne absente **et le disent** sur stderr. Eprouve contre le cloud
reel ce matin :

```
colonne mandants_texte (existe)  : True
colonne mandants_json  (absente) : False
[registre des mandats] colonnes absentes du cloud, RETIREES de ce push :
    mandants_json  -- le patch SQL n'est pas encore passe.
```

➡ **Le registre ne peut plus tomber a cause de ce chantier, patch ou pas.**
