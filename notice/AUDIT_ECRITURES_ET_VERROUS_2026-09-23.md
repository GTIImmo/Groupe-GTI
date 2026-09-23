# Audit des écritures — qui écrit quoi, et qui efface qui

*23/09/2026, pendant le run. Question posée : « est-ce qu'on se trompe sur certaines
écritures ? » Traduite en question mesurable : **y a-t-il des endroits où deux mains
écrivent la même chose, et où l'une efface l'autre ?***

---

## Ce qui va bien — et c'est l'essentiel

**Les bannettes sont vides.** `app_contact_pending` 0 · `app_search_pending` 0 ·
`app_annonce_pending` 0, aucun conflit. Aucune saisie ne traîne.

**Les deux protections sont symétriques.** Le push des contacts saute les lignes en cours
d'édition *(15 références à `dirty`)*, et le push des annonces fait de même
*(`fetch_dirty_annonce_ids`, `tier2-dirty-skip`)*. Ce que l'app écrit n'est pas écrasé par
le run — **ni pour les contacts, ni pour les annonces**.

**Le front n'écrit presque rien en direct** : trois tables seulement
*(`app_diffusion_request`, `app_diffusion_target`, `app_diffusion_request_event`)*. Tout le
reste passe par des RPC, donc par une règle écrite.

**Sept tables reçoivent plusieurs mains**, et toutes sont des cas connus et voulus :
`app_console_job` *(le front enfile, le worker consomme)*, `app_contact_current` et
`app_contact_search_current` *(le serveur reconstruit, le worker corrige — protégé par les
bannettes)*, `app_dossier_current` *(même mécanique côté annonce)*.

---

## ⛔ CE QUI NE VA PAS — un garde-fou fantôme

```
phase2/.descente.lock     TESTE par 3 scripts
                          CREE par personne
                          n'a jamais existe sur le disque
```

**Trois scripts s'arrêtent si ce fichier existe** — `magasin_affaire_app`,
`magasin_annonce_app`, `migrer_registre_recherche`. Il n'existe jamais. **Leur garde ne se
déclenche donc jamais**, et ils écrivent pendant la descente.

C'est **exactement la forme du défaut C-4** trouvé ce matin : un garde-fou écrit, présent
dans le code, et qui ne protège rien. Deuxième fois en une journée.

> Le vrai verrou existe et fonctionne : `pull_from_supabase.lock`, posé par `VerrouUnique`
> après l'incident du 22/08 *(deux descentes simultanées, ~2 800 requêtes, l'instance
> Supabase a cédé jusqu'au redémarrage)*. Il est honoré par `pull_from_supabase`,
> `comparer_doublures`, `annonces_app_seule`, `magasin_mandat_app` et `sync_active_searches`.
>
> **Deux scripts frères — `magasin_mandat_app` et `magasin_affaire_app` — utilisent deux
> verrous différents.** L'un le vrai, l'autre le fantôme.

> **FAIT le 23/09.** Les trois scripts visent désormais `pull_from_supabase.lock`. Une
> ligne chacun — **l'intention était juste, le nom de fichier ne l'était pas** : leur
> propre commentaire dit *« la descente tient ce verrou ~21 minutes »*.
>
> ⚠ **Vérifié avant de toucher** : `magasin_annonce_app` est l'**étape 3 de la descente
> elle-même**. Les étapes 1 et 2 prennent le verrou **chacune à son tour et le relâchent**,
> donc l'étape 3 ne se bloque pas sur son propre run.
>
> **10 contrôles** (`phase2/checks/test_un_seul_verrou.py`). Il ne vérifie pas qu'un verrou
> existe — il vérifie que **tout le monde regarde le même**, et que c'est bien celui que
> quelqu'un **crée**. Éprouvé en échec sur la version d'avant.
>
> *(Sa première forme s'accusait elle-même : son propre texte contient le nom qu'elle
> traque. Quatrième contrôle faux de la journée, attrapé tout de suite.)*

---

## ⚠ CE QUI NE VA PAS NON PLUS — le read-through n'attend personne

```
37 travaux en status=error, le plus vieux du 27/08
   19  Hektor injoignable   (TimeoutError WinError 10060)  -- externe
    4  database is locked                                  -- a nous
   14  causes metier                                       -- a trier
```

**Les 4 verrous tombent à 07:51, 07:58, 15:36 et 15:38.** Les deux premiers sont
**pendant la descente de 07:30**.

Le rafraîchissement déclenché par un clic *(`refresh_single_annonce`,
`refresh_contact_inproc`)* **ne regarde aucun verrou**. Il attend ses 30 secondes de
`busy_timeout`, puis meurt. L'utilisateur a cliqué sur une fiche et a vu une donnée
périmée — **sans que rien ne le lui dise**.

⚠ Ce n'est **pas** une perte de saisie : un rafraîchissement est une LECTURE, et le run de
nuit la refait. Mais c'est un écran qui ment sans le dire.

**Correctif possible** : que le read-through cède au verrou lourd, comme
`sync_active_searches` le fait déjà *(`ceder_au_verrou`)*. Ou, plus simple, qu'un échec de
rafraîchissement **se voie à l'écran** au lieu de finir dans une table que personne ne lit.

---

## ⚠ ET UNE HABITUDE À TRANCHER

**37 travaux en erreur dorment depuis un mois.** Personne ne les regarde, personne ne les
rejoue, personne ne les efface. Les 19 « Hektor injoignable » sont sans conséquence ; les
14 autres portent des causes métier — *« aucun champ annonce modifiable fourni »*,
*« hektor_offre_id required »*, un mandant jamais rattaché — **et ceux-là étaient des gestes
d'utilisateur qui n'ont pas abouti**.

### Les 37, triées une par une le 23/09 — **ce sont TOUTES des essais**

| | |
|---|---|
| 19 | Hektor injoignable — externe, se répare seul |
| 4 | verrou SQLite — dont 2 pendant la descente *(voir plus haut)* |
| **10** | sur **`TEST C15 agence Firminy - a supprimer`**, **`TEST C4 Villa Bellecour`** et **`[Sans titre] EM28412`** *(l'annonce 24933, essais déjà connus)* |
| 4 | sans annonce rattachée — création de brouillon, statut d'offre, recherche : même période d'essais |

➡ **Pas un seul geste client perdu.** Le plus alarmant à lire — trois échecs d'affilée sur
un mandant qu'on n'arrivait pas à rattacher — portait sur une annonce nommée
*« à supprimer »*.

**Mais personne ne le savait**, et c'est ça le vrai sujet : **37 erreurs mortes garantissent
que la 38ᵉ, la vraie, passera inaperçue.**

> **Recommandation** : purger les 37, et écrire que la file doit rester à zéro. Une file
> qu'on laisse grossir cesse d'être une file : elle devient un décor.

⚠ **Et deux annonces d'essai sont encore `Actif`, non archivées**, un mois après — dont une
qui s'appelle littéralement *« TEST C15 agence Firminy - a supprimer »*.

---

## L'ALERTE MANQUANTE — corrigée le 23/09

`GTI Recherches Actives` n'était pas dans la liste des tâches qui alertent. Son échec du
**19/09** *(OAuth Hektor en timeout)* n'a donc prévenu personne. **Troisième fois le même
trou** — après la sauvegarde (19/08) et la descente (08/09), et découvert de la même
façon : parce que Frédéric a demandé à vérifier.

> **FAIT.** Elle est `critical`. C'est le **seul** mécanisme qui capte les recherches
> modifiées dans Hektor ; une nuit ratée se répare seule, **trois nuits en silence font
> dériver les recherches**.

⚠ **`GTI Relances Email` a été laissée de côté DÉLIBÉRÉMENT.** Elle tourne **toutes les
heures** et lance `relance_worker` **sans `--allow-auto-send`** : l'envoi automatique est
bloqué par décision. L'alerter serait du bruit horaire pour un mécanisme éteint — et le
bruit finit par faire ignorer les vraies alertes. *Le jour où l'envoi sera rallumé, il
faudra une sonde de **données** (des relances dues qui ne partent pas), pas l'échec d'une
exécution.*

---

## LES 2 ORPHELINS — réglés, et ils n'étaient pas ce que je croyais

Je les avais attribués à mon accident du 22/09. **Faux.** Leurs deux recherches **existent
sur le serveur** et ont été revues le 23/09 à 12:52. Mais leurs contacts sont **archivés**
et **hors périmètre** : elles ne sont donc légitimement pas dans Supabase.

C'étaient des lignes d'état du moteur, laissées derrière quand le contact a quitté
l'annuaire. **Supprimées** — elles se reconstruiraient seules si le contact revenait.

## Six avertissements que personne ne lit

La sonde en produit **six**, et **aucun ne part** *(seuls les `critical` déclenchent un
envoi)*. Deux méritent un œil : **90 notifications sans destinataire** *(seuil 20)* et
**4 Go dans `.tmp`** — sur le volume unique qui porte aussi le code, les bases et les
sauvegardes.

---

## CE QUE JE N'AI PAS BALAYÉ

- Les **écritures locales** dans `phase2.sqlite` par plusieurs scripts du même run
  *(l'ordre du pipeline les sérialise, mais je ne l'ai pas prouvé table par table)*.
- Le **contrat d'autorité par CHAMP** *(`contrat_autorite.py`)* : je n'ai pas vérifié que
  la liste des champs « app » est cohérente entre le serveur, le worker et le front.
- Les **148 copies `__sb`** : j'ai vérifié en septembre qu'on n'y écrit pas ; je ne l'ai
  pas re-mesuré aujourd'hui.
