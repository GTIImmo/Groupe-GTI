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
Au rechargement suivant elle revenait, sans un mot. **C'est corrigé** *(§ 7)*, mais
**l'alignement des deux fonctions sur la règle des 3 heures reste à trancher par Frédéric** :
ce n'est pas un détail technique, c'est un **choix** — il rendrait tranchables des travaux
qu'un filet pourrait encore rejouer.

---

## 7. Ce qui a été écrit

| fichier | quoi |
|---|---|
| `supabase/patch_abandon_defait_le_geste_2026-10-15.sql` | le correctif, **4 ancres**, sur la fonction **lue dans la base** |
| `…_INVERSE.sql` | le retour arrière, avec contrôle d'empreinte |
| `apps/hektor-v1/src/lib/api.ts` | `resolveAction` **rend** son compte-rendu *(il était jeté)* |
| `apps/hektor-v1/src/App.tsx` | le bandeau **dit** ce que le clic a fait — et **ne cache plus une ligne qu'il n'a pas tranchée** |

**Empreinte d'avant** : `5590da3aff0e57512d8fb69c13abab2d`

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

---

## 9. ⬜ Ce qui reste à Frédéric

1. **Coller** `patch_abandon_defait_le_geste_2026-10-15.sql` dans Supabase.
2. **Pousser** le front *(Vercel se déploie seul)*.
3. **Cliquer « J'ai refait »** sur **61672** et **62963** — la mesure dit qu'il n'y a **rien
   à défaire** sur ces deux-là, et « J'ai refait » est le bon bouton : le geste **était
   passé** chez Hektor.
4. **Trancher la question du § 6** : aligne-t-on `app_action_status` et `app_action_resolve`
   sur « 5 tentatives **OU** plus de 3 heures », comme la vue d'hier ?
