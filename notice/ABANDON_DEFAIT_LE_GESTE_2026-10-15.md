# « ABANDONNER CE GESTE » DEFAIT CE QUE L'APP AVAIT ECRIT — 15/10/2026

> **La question de Frédéric**, mot pour mot :
> *« comment dire a mon apps d'annuler le worker et annuler le changement dans l'apps
> c'est a dire remettre le montant comme hektor »*
>
> **Sa décision** : *« oui fais A »* — c'est-à-dire **« Abandonner » remet vraiment la
> valeur de Hektor**, au lieu de seulement masquer l'alerte. Pas de troisième bouton.

---

## 1. Le défaut, en une phrase

Depuis le chantier ③ *(12/10)*, l'app écrit **chez nous d'abord**. L'écran offre deux
boutons quand un geste a définitivement échoué — et **les deux font exactement la même
chose** : un `INSERT` dans `app_pending_resolution`, qui ne sert qu'à **faire taire
l'alerte**.

| le bouton | ce qu'il faisait avant le 15/10 |
|---|---|
| « J'ai refait » | masque l'alerte. Rien d'autre |
| « Abandonner ce geste » | masque l'alerte. Rien d'autre |

➡ **La valeur écrite par l'app restait en place pour toujours, alors que Hektor n'avait
jamais reçu le geste — et plus rien ne le disait.**

Les 5 fonctions « optimistes » concernées, et ce qu'elles posent chez nous :

| geste | la fiche `app_dossier_current` | le carnet `app_annonce_champ_app` |
|---|---|---|
| changer le statut | `statut_annonce`, `diffusable` | `statut`, `diffusable`, `clos_motif` |
| archiver | `archive` | `archive`, `archive_motif` |
| désarchiver | *(rien)* | `archive` |
| affecter un négociateur | `negociateur_email` | `negociateur_email` |
| les 4 gestes d'affaire | `statut_annonce` | `statut` |

---

## 2. ⭐⭐ Ce que le projet avait DÉJÀ tranché — et qu'on ne refait pas

**La matière du retour arrière était déjà là.** Les RPC optimistes posent l'état d'avant
dans la charge du travail — `statut_avant`, `diffusable_avant`, `archive_avant`,
`negociateur_avant` — et le commentaire de `app_geste_affaire_optimistic` le dit en clair :

> *« le travail EMPORTE l'état précédent, pour que le worker sache quoi restaurer »*

Et celui de `app_change_annonce_status_optimistic`, écrit le 12/10 :

> *« Personne ne les relit encore… elles sont posées maintenant pour que le second temps
> n'ait plus rien à changer ici. »*

**Le second temps, c'est aujourd'hui.** Il n'y avait rien à inventer.

### ⚠⚠ Et ce qu'on ne touche SURTOUT pas : les quatre gestes d'affaire

Pour l'offre, le compromis et la vente, **le worker restaure déjà**
*(`restaurerEtatAffaire` + `restaurerStatutRedescendu`, `console_job_worker.js:19523`)*, et
il le fait **exactement quand le filet de rejeu s'arrête** — donc **avant** que le bandeau
ne s'affiche. Y ajouter un second retour arrière serait un **double** retour arrière.

Le garde-fou de l'instant *(§ 3)* les écarte tout seul — le worker repose la valeur avec un
`ecrit_le` neuf — mais **la raison doit être écrite** : ce correctif ne vise que les gestes
d'**annonce**, les seuls dont personne ne défaisait l'écriture.

---

## 3. ⭐ Le garde-fou, et il est MESURÉ

**La question** : comment savoir quelles lignes du carnet appartiennent à *ce* travail, et
pas à un geste plus récent qui a réussi ?

**La réponse** : les deux colonnes valent `now()` par défaut, `now()` est **figé** pendant
une transaction, et la RPC écrit le carnet **et** crée le travail dans la **même**
transaction. Donc

```
app_annonce_champ_app.ecrit_le   =   app_console_job.requested_at
```

**à la microseconde.** Mesure du 15/10 sur les deux vrais travaux en erreur et leurs
21 couples possibles : **un seul couple par ligne de carnet tombe à 0,000 s** ; les autres
sont à **44 s, 124 s, 8 006 s, 473 236 s**.
➡ C'est un **identifiant**, pas une approximation — la règle du 14/10 : *« on croise sur
les identifiants, jamais sur les nombres »*.

### ⚠ Et ce garde-fou n'est pas décoratif : sans lui, on effaçait du vrai

| travail en erreur | le travail | la ligne de carnet | écart |
|---|---|---|---|
| **61672** | 13/10 **11:37** | 13/10 **11:51** | **+2 h 14** |
| **62963** | 14/10 **08:13** | 14/10 **08:16** | **+2 min** |

**Les deux lignes de carnet ont été écrites par un geste PLUS RÉCENT** — celui que Frédéric
a refait à la main, et qui a marché. Sans le garde-fou, « abandonner » aurait effacé une
valeur **légitime**. Avec lui, ces deux abandons ne touchent **RIEN** — et c'est la bonne
réponse.

### Le second garde-fou

On ne remet la fiche que si elle porte **encore** ce que ce geste y avait écrit. Si le run
de nuit, ou un autre geste, l'a déjà changée, **on n'y touche pas** — et le compte-rendu le
dit (`fiche_remise: 0`).

---

## 4. Pourquoi on EFFACE la ligne de carnet au lieu de la réécrire

`phase2/identite/contrat_autorite.py` porte la règle, arbitrée par Frédéric le 28/08 :

```
l'app a une valeur  ->  elle gagne
l'app n'a rien      ->  ON NE TOUCHE A RIEN
```

➡ **Une ligne absente veut dire « l'app n'a rien à dire », donc Hektor gagne** — c'est
exactement ce que Frédéric a demandé.

Y remettre l'ancienne valeur de Hektor serait la **revendiquer** comme une valeur de l'app,
et la **figerait** le jour de la coupure : c'est précisément **« LE GEL »** que le projet a
nommé le 03/09 et retiré le 16/09.

⚠ **Divergence assumée avec le worker** : `restaurerStatutRedescendu` **réécrit**
(`valeur_app = statut_avant, origine = 'redescente_annulee'`) au lieu d'effacer. Son cas est
différent — c'est une redescente que l'app a **calculée elle-même**, donc une valeur qu'elle
détient légitimement. Ici, le geste n'a **pas eu lieu** : l'app ne détient rien.

---

## 5. Ce que ça ne change pas

- **la sentinelle `data.travaux_en_erreur`** et sa clé `exclure_resolus` : elles lisent
  `app_pending_resolution`, qui reçoit sa ligne comme avant ;
- **le bandeau** *(`app_action_status`)* et la vue `app_en_attente_humain` : leur
  `NOT EXISTS` est inchangé, la ligne sort de la liste comme avant ;
- **les droits** : tout se passe **dans** `app_action_resolve`, **derrière** sa garde
  `app_console_can_request_job`. Personne ne gagne un pouvoir — celui qui peut abandonner un
  geste est celui qui pouvait le demander ;
- **« J'ai refait » n'est pas touché** : l'humain a fait le geste à la main, sa valeur est
  donc la bonne. On ne va pas la lui effacer ;
- **le carnet n'est relu par PERSONNE aujourd'hui** *(`CHAMPS_APP_ANNONCE` est vide, et le
  front ne le lit pas)* : le nettoyage n'a **aucun effet visible aujourd'hui**. Il compte
  pour **le jour de la coupure**, où le carnet devient la vérité — et c'est justement là
  qu'une valeur fausse ferait mal.

### ⚠ Les deux limites, dites franchement

1. **« Remettre comme Hektor » veut dire ici « remettre la valeur que NOTRE COPIE portait
   juste avant le geste ».** C'est la meilleure source disponible entre deux descentes, et
   c'est exactement celle que le worker utilise depuis le 01/09. Si Hektor a changé
   entre-temps, la descente du matin tranchera.
2. **Un travail sans état d'avant ne remet rien.** Mesure du 15/10 : le travail de **61672**
   *(13/10 11:37)* **n'a pas** la clé `statut_avant` — la ligne qui la pose est arrivée après
   lui. Dans ce cas on nettoie le carnet, **on ne touche pas à la fiche**, et le compte-rendu
   porte `valeur_avant: null`. **On ne devine pas.**

### La trace

Le compte-rendu de ce qui a été défait est rangé dans
`app_pending_resolution.payload_json->'defait'`. Et comme tout se passe dans **une seule
transaction** *(c'est une fonction plpgsql)*, **si l'écriture de la trace échoue, les
effacements sont annulés avec elle** — la règle du 13/10 *(« pour un geste irréversible, la
trace est une CONDITION, pas un effet de bord »)* est tenue **par construction**.

---

## 6. ⚠⚠ ET UN SECOND DÉFAUT TROUVÉ EN CHEMIN — *la moitié du correctif d'hier ne sert à rien*

Hier *(⑦-5 B)*, la vue `app_en_attente_humain` a appris à montrer les travaux que plus rien
ne rejouera : **« 5 tentatives épuisées OU plus de 3 heures »**.

**Mais les deux fonctions du bandeau sont restées à `>= 5` :**

| | la règle | 47824 *(1 tentative, 13 h)* |
|---|---|---|
| `app_en_attente_humain` *(la vue, corrigée hier)* | 5 **OU** > 3 h | ✅ **apparaît** |
| `app_action_status` *(le bandeau du bien)* | `>= 5` | ❌ **ne le liste pas** |
| `app_action_resolve` *(le clic)* | `>= 5` | ❌ **refuse en silence** |

➡ **Le travail sonne, il est visible dans le moniteur, et il n'existe nulle part où
cliquer.** Mesure du 15/10 : `resolve_accepte = false` pour **47824** et pour **61439**
*(apparu ce matin à 09:02)*.

⚠ **Et le refus était SILENCIEUX** : la RPC rend `{"resolved": false, "reason":
"rien_a_trancher"}`, et le front **jetait ce compte-rendu** — il cachait la ligne quand même.
Au rechargement suivant elle revenait, sans un mot.

### ✅ TRANCHÉ ET FAIT LE 15/10 — *Frédéric : « OUI ALIGNE LES 2 »*

`patch_aligner_seuil_trancher_2026-10-15.sql` *(+ INVERSE)* : les deux fonctions prennent la
**même** règle que la vue — « 5 tentatives **OU** plus de 3 heures ».

⚠ **Le prix, dit en clair** : un travail de 4 h avec 2 tentatives devient tranchable alors
que le filet de rejeu pourrait encore le reprendre *(sa fenêtre est de 24 h)*. Si l'humain
l'abandonne et que le filet réussit ensuite, Hektor recevra le geste **après** qu'on l'a
déclaré abandonné. La descente du matin remettra tout d'accord.
⭐ **Et le filet ne concerne que 9 types idempotents** : les deux travaux d'aujourd'hui
*(`sync_console_documents`)* n'en font pas partie — pour eux, **il n'y a rien à rejouer, donc
rien à perdre**.

### ⚠⚠ ET UN TROISIÈME MUR, que seule la mesure a trouvé

**Aligner les seuils n'aurait pas suffi.** `app_action_status` commence par

```sql
select * into d from app_dossier_current where app_dossier_id = ...;
if not found then raise exception 'dossier_not_found';
```

Or le bien de **47824** — **« Maison de village à rénover », VM8012** — est **VENDU** : depuis
le 20/05 il n'est plus dans `app_dossier_current` mais dans
`app_historical_annonce_index_current`. La fonction **levait une exception**, le front
l'avalait *(il le fait exprès : « un échec de lecture ne doit pas priver l'utilisateur de sa
fiche »)*, et **le bandeau ne s'affichait JAMAIS**. Le travail sonnait éternellement.

⭐ **C'est la même supposition fausse que le défaut 5a du 08/10** — *« le bien est dans
`app_dossier_current` »*, fausse pour **44 259 biens**. On la balaie ici **dans sa dernière
case** *(leçon 9 : une cause structurelle se balaie dans toute sa famille)*.

⚠ **On inclut les archives, délibérément** : une archive est en lecture seule pour ses
**champs**, mais trancher un geste abandonné **ne modifie pas le bien** — ça répond à une
**alerte**. L'exclure recréerait exactement le défaut qu'on répare.

---

## 6bis · OÙ SONT LES BOUTONS, ET QUAND ILS APPARAISSENT

**Les boutons ne sont PAS dans l'écran Santé Système.** Ils sont sur **la fiche du bien** —
c'est voulu : on tranche un geste là où on voit le bien, pas dans une liste de sondes.

| | où exactement |
|---|---|
| **cockpit** | onglet **« Le Bien »** *(App.tsx:28785)* — ⚠ **masqué** si la fiche est en lecture seule *(archive, brouillon, ou vendu/clos sans détail chargé)* |
| **fiche classique** | **au-dessus de la barre d'onglets** *(App.tsx:30394)* — **toujours affiché** |

Le chemin le plus court : **écran Santé → cliquer le bien cité par l'alerte** *(le lien posé
le 15/10, ⑦-5 A)* → la fiche s'ouvre → le bandeau rouge est en haut.

**Quand le bandeau apparaît**, depuis le 15/10 — il faut **les trois** :

1. le travail est en **erreur** ;
2. **5 tentatives épuisées OU plus de 3 heures** *(avant : 5 tentatives, point)* ;
3. moins de **30 jours** ;
4. et **personne ne l'a déjà tranché**.

**Mesure du 15/10, sur les 4 travaux en erreur :**

| bien | tentatives | âge | tranchable | où est le bien |
|---|---|---|---|---|
| **61672** | 5 | 47 h | ✅ | parc vivant |
| **62963** | 5 | 26 h | ✅ | parc vivant |
| **47824** | 1 | 13 h | ✅ *(règle des 3 h)* | **vendus/clos → repli** |
| **61439** | 1 | **1 h 30** | ⏳ **pas encore** — à partir de **12:02** | parc vivant |

---

## 7. Ce qui a été écrit

| fichier | quoi |
|---|---|
| `supabase/patch_abandon_defait_le_geste_2026-10-15.sql` | le correctif, **4 ancres**, sur la fonction **lue dans la base** |
| `…_INVERSE.sql` | le retour arrière, avec contrôle d'empreinte |
| `supabase/patch_aligner_seuil_trancher_2026-10-15.sql` | « 5 **ou** > 3 h » dans les 2 fonctions **+ le repli vendus/clos/archives** |
| `…_INVERSE.sql` | le retour arrière des deux |
| `apps/hektor-v1/src/lib/api.ts` | `resolveAction` **rend** son compte-rendu *(il était jeté)* |
| `apps/hektor-v1/src/App.tsx` | le bandeau **dit** ce que le clic a fait — et **ne cache plus une ligne qu'il n'a pas tranchée** |

**Les deux patchs SQL sont indépendants** *(leurs ancres ne se touchent pas)* : à coller dans
n'importe quel ordre — vérifié en les posant l'un après l'autre, les 4 + 3 ancres restent
uniques.

### ⚠⚠ VERSION 2 des deux patchs — *la version 1 a échoué chez Frédéric*

> `STOP : l'ancre du repli apparait 0 fois, attendu 1`

**Rien n'a été écrit** *(vérifié : les deux fonctions étaient à leurs empreintes d'origine,
sans aucun retour chariot — l'éditeur Supabase a tout annulé)*.

**La cause** : **coller du texte dans l'éditeur Supabase y met des CRLF.** L'ancre du repli
tient sur **deux lignes** : collée, elle porte un retour chariot que le corps de la fonction
*(stocké en LF)* n'a pas → **zéro correspondance**. Les ancres d'**une seule** ligne
marchaient — c'est pourquoi **une seule des trois** a cassé.

⚠ **Et la leçon était déjà écrite dans le projet, deux fois** *(08/10 puis 12/10 : « ça ne
touche pas que le md5, ça touche TOUTE ANCRE MULTILIGNE »)*. J'avais appliqué
`replace(…, chr(13), '')` à l'**empreinte** et l'avais oublié pour les **ancres**.

**Le remède** : on nettoie les retours chariot **des deux côtés** — le corps lu dans la base,
**chaque** ancre, et **chaque** texte inséré *(sinon le CRLF entre dans la fonction et c'est
l'INVERSE qui ne retrouverait plus ses ancres)*.

⚠⚠ **La vraie cause est plus profonde : mon épreuve ne reproduisait pas LE TRANSPORT.** Trois
épreuves vertes n'ont rien vu parce qu'elles passent par l'outil SQL, jamais par un
copier-coller Windows. **Donc j'éprouve maintenant le transport lui-même** :

```sql
EXECUTE replace(le_patch, chr(10), chr(13) || chr(10));   -- « comme si c'etait colle »
```

| | le cas | mesuré |
|---|---|---|
| 1 | l'ancre du repli, **en LF** *(comme je l'éprouvais)* | **1** occurrence |
| 2 | **la même, COLLÉE en CRLF** | **0** ← **l'erreur de Frédéric, reproduite** |
| 3 | collée + **les deux côtés nettoyés** | **1** ✅ |
| 4 | une ancre d'**une** ligne *(LF / CRLF)* | **1 / 1** — insensible, donc muette |
| 5 | **le vrai patch v2, exécuté en CRLF** | **posé sans erreur** ✅ |
| 6-8 | repli présent · seuil présent · **0 retour chariot** dans la fonction | ✅ |
| 9-13 | **patch ① en CRLF, puis son INVERSE en CRLF** | posé, 0 CR, **empreinte d'origine retrouvée** ✅ |

⚠ Un contrôle sur 8 est sorti rouge **à tort** : je cherchais `03:00:00` dans la fonction.
Une **vue** garde la forme normalisée `03:00:00`, une **fonction** garde le texte source
`interval '3 hours'` — vérifié dans les deux. Le patch était bon, mon attendu était faux.

**Empreintes d'avant** : `app_action_resolve` = `5590da3aff0e57512d8fb69c13abab2d` ·
`app_action_status` = `0c8a54d36ea621fbd4b5e7bc7b7da6a2`

### Les deux retours arrière sont ÉPROUVÉS, pas seulement écrits

| | `app_action_resolve` | `app_action_status` |
|---|---|---|
| origine | `5590da3a…` | `0c8a54d3…` |
| après patch | `723707b2…` / `2315de8f…` | `9d68752a…` |
| **après inverse** | **`5590da3a…`** ✅ | **`0c8a54d3…`** ✅ |

➡ **On retombe à l'octet près.** Et la ligne « après patch » prouve que le patch **a changé
quelque chose** — un inverse qui revient sur un patch qui ne faisait rien ne prouverait rien.

---

## 8. Les épreuves — **11 contrôles, sur la VRAIE base, en transaction annulée**

Scène montée sur le **bac à sable 62963**, identité empruntée *(`SET ROLE authenticated` +
`request.jwt.claims`)*, `ROLLBACK` à la fin. **Rien n'a été écrit.**

| | le cas | mesuré |
|---|---|---|
| A | abandon, carnet à l'instant du travail, état d'avant présent | `fiche=Actif carnet=0`, **2 champs défaits** ✅ |
| A | le détail | `clos_motif:0 statut:1` — seul `statut` a une colonne de fiche ✅ |
| A | la trace dans la résolution | `oui 2` ✅ |
| B | **le garde-fou de l'instant** *(carnet écrit 1 min plus tard)* | `carnet=2`, **0 défait** — on ne touche à rien ✅ |
| C | **« J'ai refait »** | `carnet=2`, **0 défait** ✅ |
| D | **sans état d'avant** | carnet nettoyé, **fiche INTACTE**, `fiche_remise=0` partout ✅ |
| E | **la fiche a déjà changé** *(elle dit « Vendu »)* | carnet nettoyé, **fiche non touchée** ✅ |
| F | **la production** | `47824=0 61439=0 61672=0 62963=0` — **aucun des 4 travaux n'a de ligne à défaire** ✅ |
| **G** | ⭐ **TÉMOIN INVERSE : le code d'AVANT, même scène que A** | `fiche=Sous compromis carnet=2`, pas de clé `defait` — **rien n'est défait** |
| G | et l'alerte se taisait **quand même** | `oui` — **c'est le défaut, montré** |

> **Le témoin inverse est ce qui donne du poids au reste** : avec l'ancien code, la même
> scène laisse la fiche fausse, le carnet plein, **et l'alerte éteinte**.

`npm run build` **vert** *(bundle `index-CaeOf3Z1.js`)*.

### Et 11 contrôles de plus pour l'alignement — *avant / après, sur les VRAIS travaux*

| | le cas | mesuré |
|---|---|---|
| **AVANT** | le bandeau du bien **vendu** 47824 | **`ERREUR dossier_not_found`** |
| **AVANT** | trancher 47824 | **`rien_a_trancher`** |
| AVANT | le bandeau du bien vivant 61672 | `abandonnes=1` |
| **APRÈS** | le bandeau du bien **vendu** 47824 | **`abandonnes=1`** ✅ |
| APRÈS | le bandeau de 61672 *(inchangé)* | `abandonnes=1` ✅ |
| APRÈS | **abandonner** 47824 | `resolved=true defaits=0` ✅ |
| APRÈS | 47824 **sort** du bandeau | `abandonnes=0` ✅ |
| APRÈS | **61439 n'a que 1 h 30** | `rien_a_trancher` ✅ — *la règle des 3 h n'ouvre pas tout* |
| APRÈS | « J'ai refait » sur 61672 | `resolved=true defaits=0` ✅ |
| APRÈS | sa fiche n'a pas bougé | `Sous offre` ✅ |
| APRÈS | son carnet est intact | `statut=Sous offre` ✅ |

> **Les trois lignes « AVANT » sont le témoin inverse** : elles montrent le défaut en
> fonctionnement, sur les vraies données, avant que le patch n'existe.

---

## 9. ⬜ Ce qui reste à Frédéric

1. **Coller les DEUX patchs** *(n'importe quel ordre)* :
   `patch_abandon_defait_le_geste_2026-10-15.sql` puis
   `patch_aligner_seuil_trancher_2026-10-15.sql`.
2. **Pousser** le front *(Vercel se déploie seul)*.
3. Sur **61672** et **62963** : **« J'ai refait »** — la mesure dit qu'il n'y a **rien à
   défaire** sur ces deux-là, et le geste **était passé** chez Hektor.
4. Sur **47824** *(« Maison de village à rénover »)* : **« Abandonner ce geste »** — c'est un
   envoi de documents qui a reçu du HTML au lieu de JSON ; **rien n'a été écrit chez nous**,
   donc rien à remettre.
5. **61439** : attendre **12:02** *(3 heures)*, puis il apparaîtra à son tour.

---

## 10 · ✅ CONTRÔLE DU 15/10 — *les deux patchs sont posés*

**Les cinq morceaux sont en base, et `0` caractère parasite** *(la version 2 a tenu le
collage)* :

| | |
|---|---|
| retour arrière sur « Abandonner » · sa trace | ✅ ✅ |
| seuil 3 h dans le **clic** · dans le **bandeau** | ✅ ✅ |
| repli **vendus / clos / archives** | ✅ |
| retours chariot laissés dans les 2 fonctions | **0** |

**Nouvelles empreintes** : `app_action_resolve` = `ad573c70facf20026fbe3043dc4d6ed3` ·
`app_action_status` = `9d68752afbbe48d99b2efec09e42faf8` *(exactement celle que l'épreuve
avait prédite)*.

**Et le résultat, lu avec l'identité de Frédéric :**

| bien | | le bandeau |
|---|---|---|
| **47824** *Maison de village à rénover* | **VENDU** → repli | **1 geste** ✅ *(avant : erreur, bandeau invisible)* |
| **61672** *Villa de PP de 1999* | parc vivant | 1 geste ✅ |
| **62963** *TEST C15 entrepôt* | parc vivant | 1 geste ✅ |
| **61439** *Beau T3 traversant* | 1 h 48 | **0** ⏳ *à partir de 12:02* |

➡ Et sur les **quatre**, `lignes_a_defaire = 0` : **rien à remettre**, confirmé une
troisième fois.

### ⚠⚠ Le contrôle a révélé un défaut DANS LE RETOUR ARRIÈRE — corrigé

Les deux patchs touchent **la même fonction**. L'inverse du patch ① exigeait l'empreinte
d'**avant les deux** : les deux posés, il **défaisait correctement sa part, puis refusait**.

> `STOP : on ne retombe PAS sur l'empreinte d'origine (2315de8fa9c52d6568f1c19904788adb)`

Et `2315de8f…` **est** exactement l'empreinte « seuil 3 h seul ». **Le travail était bon, le
juge trop strict.** Il refusait **sans rien casser** *(l'exception annule tout)* — mais il
bloquait.

⭐ **La règle qui en sort : un retour arrière ne juge que SA PROPRE part.** Il vérifie d'abord
qu'il ne reste **aucune trace** de ce qu'il devait retirer ; l'empreinte globale n'est exigée
que si l'autre patch n'est pas là, sinon il **dit** pourquoi elle diffère.

**6 contrôles de la chaîne complète** *(en transaction annulée)* : inverse ① avec ② posé →
**passe**, 0 trace, le seuil 3 h **est toujours là**, empreinte `2315de8f…` ; puis inverse ②
→ **`5590da3a…`, l'empreinte du départ**.
