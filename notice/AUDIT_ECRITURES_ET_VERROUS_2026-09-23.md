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

**Correctif** : les trois scripts doivent tester `pull_from_supabase.lock`, comme leurs
frères. Une ligne chacun.

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

La question n'est pas technique : **veut-on une file d'erreurs qu'on relit, ou pas ?** Si
non, il faut les purger et le dire. Si oui, il faut quelqu'un pour les lire.

---

## CE QUE JE N'AI PAS BALAYÉ

- Les **écritures locales** dans `phase2.sqlite` par plusieurs scripts du même run
  *(l'ordre du pipeline les sérialise, mais je ne l'ai pas prouvé table par table)*.
- Le **contrat d'autorité par CHAMP** *(`contrat_autorite.py`)* : je n'ai pas vérifié que
  la liste des champs « app » est cohérente entre le serveur, le worker et le front.
- Les **148 copies `__sb`** : j'ai vérifié en septembre qu'on n'y écrit pas ; je ne l'ai
  pas re-mesuré aujourd'hui.
