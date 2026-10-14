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
