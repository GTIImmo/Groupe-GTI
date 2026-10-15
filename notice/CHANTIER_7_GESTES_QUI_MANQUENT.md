# CHANTIER ⑦ — LES GESTES QUI MANQUENT

> **Note ouverte le 14/10/2026.** Le chantier n'est pas commencé : cette note **rassemble** ce qui
> s'y accumule, pour qu'on n'ait pas à le retrouver dans trois endroits le jour venu.
> *(Les items venaient de `CLAUDE.md` l. 115, 267 et 424.)*

**Ordre de Frédéric : ① ⑤ ④ ② puis ③ → ⑥ → ⑦ ⑧.**

---

## ⑦-1 · ARCHIVER ET DÉSARCHIVER UN CONTACT — *audité le 14/10, à la demande de Frédéric*

### La réponse : **l'app ne sait pas le faire**, et c'est établi par quatre chemins

| source | ce qu'elle dit |
|---|---|
| **la base** *(ce qui a réellement tourné)* | **9** types de gestes « contact » depuis mai : `refresh_console_contact_data` (477) · `update_hektor_contact_search` (24) · `update_hektor_contact` (23) · `create_hektor_mandant_contact` (17) · `create_hektor_contact` (16) · **`delete_hektor_contact` (13)** · `update_hektor_mandant_contact` (10) · `add_hektor_contact_search` (4) · `delete_hektor_contact_search` (3). **Aucun archivage.** |
| **le worker** | il sait archiver une **recherche** — `archiveHektorContactSearch()`, mode Hektor `contacts-contactProfile-modifDateArchiveCritere`. Pour la **fiche contact**, il **lit** `archive` *(l. 2202)* mais **ne l'écrit jamais**. |
| **l'écran** | **aucun bouton** « archiver » ni « désarchiver » sur une fiche contact. |
| **la liste des gestes du chantier ②** | elle porte « **supprimer un contact** » — **pas** « archiver ». |

*Et dans `git log`, tous les commits « archiver / désarchiver » concernent **les annonces**.*

### L'asymétrie, qui est le vrai sujet

| objet | archiver | désarchiver | supprimer |
|---|---|---|---|
| **annonce** | ✅ | ✅ | ✅ |
| **recherche** | ✅ | ❌ | ✅ |
| **contact** | ❌ | ❌ | ✅ *(13 fois)* |

> **Sur un contact, l'app ne connaît que le tout ou rien : on le supprime, ou on le garde.**
> Or **archiver** un contact est un geste courant — un acquéreur qui a acheté, un vendeur parti.

### ⚠ CE QU'IL FAUDRA TROUVER D'ABORD

**La commande Hektor pour archiver une FICHE CONTACT est INCONNUE.** Le worker connaît
`modifDateArchiveCritere` **pour une recherche** ; l'équivalent sur la fiche n'a jamais été
relevé.

➡ **Même méthode que « supprimer une photo »** *(audit du 25/09 : « les trouver d'abord »,
commande trouvée le 14/10 par un relevé en lecture seule)* : **un relevé, en lecture seule,
avant d'écrire la moindre ligne.**

---

## ⑦-2 · LE CAS GLADYS DURIEUX — *à régler en même temps* **(décision de Frédéric, 14/10)**

**Mesuré le 14/10** — c'est la **dernière** incohérence « fiche archivée + recherche active »
sur **64 054** fiches archivées.

| | |
|---|---|
| contact | **Gladys DURIEUX** · `10059959` · Groupe GTI Saint-Étienne · `accueil@gti-immobilier.fr` |
| sa **fiche** | **archivée**, mise à jour le **23/06/2026** |
| **mandante** de | **40608** — *« Villa d'architecte lumineuse avec piscine — 166 m² — Saint-Romain-Lachalm »* · **annonce ACTIVE** |
| **propriétaire** de | **58916** · annonce **active** |
| ses recherches | n° 0 archivée *(prix max 222 222)* · n° **1 ACTIVE** *(prix max **123 456**, « Saint-Étienne » saisi deux fois)* |

> ⚠ **Une cliente avec un mandat en cours a sa fiche contact archivée.**
> **Ce n'est pas un défaut technique : c'est une erreur de saisie métier.**

**Ce qui l'a protégée** : elle est éligible pour **deux** raisons —
`["active_annonce_relation", "active_search"]`. Sans son annonce active, elle serait tombée comme
les 35 autres *(voir `AUDIT_RECHERCHES_ORPHELINES_2026-10-14.md`)*.

⚠ **Et aujourd'hui, on ne peut pas la désarchiver depuis l'app** — il faut ouvrir Hektor. **C'est
exactement pourquoi ⑦-1 et ⑦-2 vont ensemble.**

*(Les prix 222 222 et 123 456 et les villes saisies deux fois ressemblent à un essai laissé sur
une vraie fiche. À confirmer avec l'agence.)*

---

## ⑦-5 · ✅ FAIT LE 15/10 — *« l'alerte est à un endroit, le bouton à un autre »*

*Frédéric : « mais dans le monitoring je n'ai pas de bouton pour relancer ou annuler ? »,
puis « FAIS LES 2 ».* **Deux trous, fermés ensemble.**

### B · Un travail que plus rien ne rejouera devient VISIBLE

**Le défaut** : l'écran Santé disait *« Travaux console en erreur : 3 »*, et Frédéric ne pouvait
en trancher que **deux**. Le bandeau exige **5 tentatives** — or le filet de rejeu
*(patch c4bis du 30/08)* ne rejoue que **9 types idempotents**, et `sync_console_documents` n'y
est pas, **délibérément** : *« sans vérification absolue, le rejeu transforme un succès en échec,
ou double une création »*.
➡ **Un travail non rejouable qui échoue était invisible ET éternel.**

**Le remède** *(`supabase/patch_bandeau_erreurs_definitives_2026-10-15.sql` + INVERSE)* :
la règle devient **« 5 tentatives épuisées OU plus de 3 heures »**. On ne touche **ni** au filet,
**ni** à la liste des types rejouables — on élargit seulement ce que le bandeau **montre**.

⚠ **Les 3 heures sont mesurées, pas choisies** : le filet attend 5, 10, 15 puis 20 minutes, soit
**50 minutes** pour épuiser les 5 tentatives. Passé 3 h *(marge ×3,6)*, un travail qui n'y est pas
ne le sera **jamais**.
⚠ **Ma première version disait 24 h** *(la constante du filet)*. **L'épreuve a montré qu'elle ne
changeait rien aujourd'hui** — le travail 47824 a 12 h. **J'aurais fait attendre jusqu'à 19:00
pour rien.**

**Éprouvé en lecture seule, sur la vraie base** : `47824` *(1 tentative, 12 h)* → **apparaît** ;
`62963` et `61672` *(5 tentatives)* → **inchangés**. **Exactement +1 ligne.**

### A · Les biens cités par une alerte deviennent CLIQUABLES

**Le défaut** : l'alerte nomme les biens *(« annonce 61672 | annonce 62963 »)*, mais il fallait
aller les chercher à la main pour trouver le bandeau qui porte les boutons.

**Le remède, entièrement côté front — rien en base** : les sondes joignent déjà un **aperçu** à
leur résultat *(le `sample` ajouté le 01/09, après la question de Frédéric « comment je le
retrouve ? »)*, et `details_json` **était déjà chargé** par l'écran. Un clic sur le bien ouvre sa
fiche, donc son bandeau.

⚠ **Le pont se fait au clic**, pas au chargement : la sonde rend un **numéro Hektor**, l'écran
ouvre par `app_dossier_id`. On n'interroge la base que pour la ligne sur laquelle on clique.
⚠ **La prop est facultative** : sans elle, l'écran se comporte exactement comme avant.

`npm run build` **vert**. ⬜ **À pousser par Frédéric** *(front → Vercel se déploie)*, et le patch
SQL **à coller**.

---

## ⑦-6 · ✅ FAIT LE 15/10 — *« ABANDONNER » DÉFAIT, au lieu de seulement faire taire*

*Frédéric : « comment dire a mon apps d'annuler le worker et annuler le changement dans
l'apps c'est a dire remettre le montant comme hektor », puis « oui fais A ».*

**Détail complet : `notice/ABANDON_DEFAIT_LE_GESTE_2026-10-15.md`.** En trois points :

**Le défaut** — depuis le chantier ③ l'app écrit *chez nous d'abord*, et les **deux** boutons
du bandeau faisaient la même chose : un `INSERT` dans `app_pending_resolution`, qui ne sert
qu'à **faire taire l'alerte**. La valeur écrite par l'app **restait en place pour toujours**
alors que Hektor n'avait jamais reçu le geste.

**Le remède** — « Abandonner » veut dire *« ce geste n'a pas eu lieu »* : la fiche reprend
l'état d'avant *(déjà posé dans la charge du travail par les RPC optimistes — « pour que le
worker sache quoi restaurer »)*, et **la ligne de carnet est EFFACÉE**, ce qui rend la parole
à Hektor *(contrat d'autorité : « l'app n'a rien → ON NE TOUCHE À RIEN »)*. « J'ai refait »
n'est pas touché.

⭐ **Le garde-fou est un IDENTIFIANT, pas une approximation** : la RPC écrit le carnet et crée
le travail dans la **même transaction**, donc `ecrit_le = requested_at` **à la microseconde**
*(mesure : un seul couple à 0,000 s sur 21 ; les autres à 44 s, 124 s, 8 006 s, 473 236 s)*.
⚠ **Et il n'est pas décoratif** : sur **61672** et **62963**, la ligne de carnet a été écrite
par un geste **plus récent** *(+2 h 14 et +2 min)* — sans lui, abandonner effaçait du vrai.
⚠⚠ **Les 4 gestes d'affaire sont hors de portée, exprès** : le worker les restaure **déjà**
*(`restaurerEtatAffaire`)*, au moment même où le filet de rejeu s'arrête. Un second retour
arrière serait un **double** retour arrière.

**11 contrôles verts sur la vraie base en transaction annulée, dont un TÉMOIN INVERSE** qui
montre l'ancien code laisser la fiche fausse, le carnet plein **et l'alerte éteinte**.

⚠⚠ **ET UN SECOND DÉFAUT TROUVÉ EN CHEMIN** : la vue corrigée hier *(⑦-5 B)* montre les
travaux de plus de 3 heures, **mais `app_action_status` et `app_action_resolve` sont restées
à `>= 5` tentatives**. Donc **47824** sonnait, était visible, et **n'avait aucun bouton** — le
clic était refusé **en silence** (`resolved: false`, que le front jetait).

✅ **ALIGNÉ LE 15/10** *(Frédéric : « OUI ALIGNE LES 2 »)* —
`patch_aligner_seuil_trancher_2026-10-15.sql` + INVERSE.
⚠ **Le prix, dit** : un travail de 4 h à 2 tentatives devient tranchable alors que le filet
pourrait encore le reprendre *(fenêtre 24 h)*. ⭐ Mais le filet ne couvre que **9 types
idempotents**, et les 2 travaux du jour n'en sont pas — **rien à rejouer, rien à perdre**.

⚠⚠ **ET UN TROISIÈME MUR, que seule la mesure a trouvé** : aligner les seuils **n'aurait pas
suffi**. `app_action_status` lève `dossier_not_found` si le bien n'est pas dans
`app_dossier_current` — et **47824 est VENDU** *(« Maison de village à rénover », VM8012)*,
donc dans l'index des vendus/clos depuis le 20/05. **Le front avalait l'erreur et le bandeau
ne s'affichait JAMAIS.** ⭐ Même supposition fausse que le défaut **5a du 08/10**, fausse pour
**44 259 biens** : balayée ici **dans sa dernière case**. Les **archives** sont incluses
exprès — trancher une alerte ne modifie pas le bien.

**11 contrôles avant/après sur les vrais travaux**, dont `ERREUR dossier_not_found` →
`abandonnes=1`, et **61439 (1 h 30) reste `rien_a_trancher`** — la règle des 3 h n'ouvre pas
tout. **Les deux retours arrière retombent à l'octet près.**

### Où sont les boutons *(question de Frédéric)*

**Pas dans l'écran Santé** : sur **la fiche du bien** — cockpit onglet **« Le Bien »**
*(masqué si la fiche est en lecture seule)*, et **au-dessus de la barre d'onglets** de la
fiche classique *(toujours)*. Chemin court : **Santé → cliquer le bien cité par l'alerte**
*(le lien de ⑦-5 A)*.

---

## ⑦-3 · CE QUI VIENT DU CHANTIER ③ *(décisions de Frédéric, 13 et 14/10)*

| | |
|---|---|
| **le crayon** de la date de clôture dans la **rubrique Mandat** | `setMandatClotureApp` n'a **qu'un seul appelant**, la modale de statut. Le crayon hors modale demande une vérification à l'œil. |
| **l'écran du journal des suppressions** | réservé aux admins ; **aucun écran ne le lit** aujourd'hui. |
| **réordonner / choisir la photo principale** | ⭐ `mode=ordonne_photos` est **désormais connu** *(relevé du 14/10)* — le plus dur est fait. |

---

## ⑦-4 · UN BANDEAU QUI MENT

L'index léger promet encore **« désarchiver »** à un bien **qui n'est pas archivé**.
*(Repéré pendant le chantier ③, 12/10.)*

---

## La règle qui vaut pour tout ce chantier

⚠ **Avant d'écrire un geste, trouver la commande Hektor par un RELEVÉ EN LECTURE SEULE.**
Le projet s'est fait avoir deux fois *(suppression de photo, archivage de recherche)*, et la
méthode du relevé a fonctionné les deux fois.
