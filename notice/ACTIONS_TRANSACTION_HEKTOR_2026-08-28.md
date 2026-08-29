# Les gestes de transaction chez Hektor — relevé sur écran, 28/08/2026

*Lu dans le navigateur de Frédéric, sur sa session admin, **sans cliquer sur quoi que ce soit**.
Fiche du bien **62774**. Aucune donnée touchée.*

---

## Pourquoi cette note

L'app sait **lire** les offres refusées et les compromis annulés — la statistique, le filtre et
les badges existent — mais elle ne sait **en poser aucun**. Pour les coder il fallait le nom exact
des appels, et deviner était exclu : **un mauvais nom n'écrit rien et ne dit rien**, exactement le
défaut corrigé le matin même sur la clôture de mandat.

**Deux tentatives ont échoué avant celle-ci**, et c'est instructif :

| | |
|---|---|
| chercher dans nos captures | le JavaScript capturé le 12/06 est celui de l'**en-tête** ; il ne connaît que `createOffre`, `createCompromis`, `addOffre` |
| demander les formulaires au serveur | ✅ fait, en lecture seule, **avec témoin** — et le témoin a montré que **Hektor ignore l'identifiant à l'ouverture** *(réponses identiques octet pour octet)*. Aucune commande d'annulation dans ces formulaires |

> **C'est Frédéric qui a trouvé la bonne méthode** : *« pourquoi ne pas utiliser ta session Hektor
> ouverte avec administrateur sur Chrome ? »*. Les boutons sont **sur l'écran**, et leur `onclick`
> porte le nom de la fonction. Une lecture du DOM, rien de plus.

---

## Ce qui a été relevé, tel quel

```js
offre_bien_change_status('refus',   '33027')   // REFUSER une offre
offre_bien_change_status('accepte', '33027')   // ACCEPTER une offre
delete_offre_suivi('33027')                    // supprimer une offre
launchPopinCompromis(62774)                    // ouvrir le compromis
launchPopinVente(62774)                        // ouvrir la vente
add_offre('62774')                             // ajouter une offre
```

### Les appels derrière ces boutons

| Geste | Mode Hektor | Paramètres |
|---|---|---|
| **refuser une offre** | `annonce-SuiviVente-updateOffre` | `id` *(l'offre)*, `type` = `refus` |
| **accepter une offre** | `annonce-SuiviVente-updateOffre` | `id`, `type` = `accepte` |
| **supprimer une offre** | `deleteOffre` | l'identifiant |
| **clore un compromis** | `annonce-SuiviVente-compromis-popinClotureCompromis` | ouvre une **popin** *(donc un formulaire derrière)* |
| **supprimer un compromis** | `deleteCompromis` | l'identifiant |
| **supprimer une vente** | `ventes-deleteVente` | l'identifiant |

---

## 🔴 UNE CORRECTION AU PROJET — la vente n'est pas ce qu'on croyait

Le projet affirme **trois fois** *« la vente : pas d'annulation possible »* — commits `cfe3483`
et `b8fc48e` du 25/06, et un commentaire dans `App.tsx`. Et j'ai répété cette phrase toute la
soirée du 28/08 pour justifier de ne pas éprouver la branche « Vendu ».

**C'est à moitié faux.** Hektor porte bien :

```js
annuleVente()        ->  mode  ventes-deleteVente
supprimerVente(id)   ->  confirmation "Voulez_vous_vraiment_supprimer_cette_vente"
                         puis  mode  ventes-deleteVente
```

**Une vente ne s'annule pas : elle se SUPPRIME.** C'est pour ça que `hektor_vente` ne porte aucune
colonne d'état — il n'y a rien à marquer, l'enregistrement disparaît. L'observation d'origine
était juste, sa conclusion trop large.

> **Conséquence directe** : la branche « Vendu » de C.4 **peut être éprouvée**. Une vente d'essai
> se retire *(`supprimerVente`)*. Ce n'est pas sans conséquence — la suppression est définitive —
> mais ce n'est plus le point de non-retour qui bloquait l'essai.

---

## Une contrainte trouvée en passant, et elle compte

Sur la même fiche, un bouton porte :

```js
$j.msgbox('Un compte administrateur ne peux pas saisir une offre.')
```

**Un compte administrateur ne peut pas saisir une offre chez Hektor.** À rapprocher du même
phénomène déjà connu sur les documents *(les blocs de signature invisibles en root admin, idUser 4)*
et de l'impersonation utilisée pour l'affectation du négociateur.

➡ **Le worker devra passer par un compte négociateur** pour ces gestes, comme il le fait déjà
ailleurs. À vérifier avant de coder.

---

## Ce que ça débloque

Les **trois gestes** que l'app ne savait pas faire sont désormais spécifiés :

1. **refuser une offre** — et c'est le plus sûr des trois : une offre est **une conversation**
   *(11 061 propositions, 9 988 acceptations, 1 096 refus)*, refuser **ajoute un événement** et
   n'écrase rien ;
2. **accepter une offre** — même mécanisme ;
3. **clore un compromis** — passe par une popin, dont le formulaire reste à relever.

Tous appartiennent à **C.4**, et tous sont des **branches** de `change_hektor_annonce_status`,
pas de nouveaux workers.

---

## Le compromis, relevé en entier — et c'est plus simple que la clôture de mandat

Second bien lu, **53372** *(compromis 50043 actif)*. La popin de clôture fait **1 819 caractères**
et ne contient **aucun champ** : c'est une simple confirmation.

> **« Annulation du compromis ! Êtes-vous sûr de vouloir annuler ce compromis ? »**

```js
annuleCompromis(idCompromis, fromContact)
    -> mode  annonce-SuiviVente-clotureCompromis
       parametres  idComp,  isCloture
```

**Ni motif, ni date, ni raison** — contrairement à la clôture de mandat qui en demande trois.
Un seul appel suffit.

### ⚠ CORRECTION DU 29/08 — `isCloture` ne distingue rien

*Cette note affirmait ici que `isCloture` séparait les deux issues du compromis —
`clore_compromis_vente` (il aboutit) et `annuleCompromis` (il tombe). **C'est faux, et
l'invention est de moi.** Relu dans `annuleCompromis` le 29/08 : la valeur est **toujours
`'1'`**, y compris pour annuler. Hektor n'a **qu'un seul geste**, et la popin qui le
déclenche s'intitule « Annulation du compromis ».*

*Le worker porte la correction depuis (`console_job_worker.js:13617`), et envoie aussi
`fromContact` — que la première version avait oublié. La note, elle, enseignait encore le
contraire : c'est réparé ici.*

## Modifier un compromis, en revanche, est hors de portée du worker

```js
launchPopinCompromis(idAnnonce, idCompromis)   // async, await import(... Modules/Compromis ...)
                                               // init, goToStep, presentPopin
```

C'est un **module ES chargé dynamiquement**, pas un formulaire postable. Cela **explique enfin**
pourquoi la lecture serveur du 28/08 rendait une coquille de « stepper » sans aucun champ, et
pourquoi passer `idCompromis` au mode `createCompromis` ne chargeait rien.

➡ **Annuler un compromis est simple. Le modifier ne l'est pas.** Ne pas confondre les deux.

## Ce qui reste à relever

- le **compte** à utiliser : l'admin est explicitement refusé pour *saisir* une offre. Les boutons
  **refuser** et **accepter**, eux, **sont bien présents** sur la fiche en session admin — donc
  l'interdiction semble porter sur la création seule. **À confirmer avant de coder.**

## Récapitulatif — tout ce qui est désormais spécifié

| Geste | Mode | Paramètres |
|---|---|---|
| refuser une offre | `annonce-SuiviVente-updateOffre` | `id`, `type='refus'` |
| accepter une offre | `annonce-SuiviVente-updateOffre` | `id`, `type='accepte'` |
| supprimer une offre | `deleteOffre` | l'identifiant |
| **annuler un compromis** | `annonce-SuiviVente-clotureCompromis` | `idComp`, `isCloture` |
| supprimer un compromis | `deleteCompromis` | l'identifiant |
| supprimer une vente | `ventes-deleteVente` | l'identifiant |
| *modifier un compromis* | *module ES `Modules/Compromis`* | **hors de portée du worker** |

---

*Méthode : `mcp__claude-in-chrome`, lecture du DOM et des fonctions globales sur la fiche 62774.
Aucun clic, aucune écriture. Voir aussi `Console/capture_transaction_actions.js` (lecture serveur)
et ses captures `Console/exports/transaction_actions_*`.*

---

# CE QUE HEKTOR REPOND — mesure du 29/08

*Question de Frederic : « je ne suis pas sur qu'Hektor, meme en cas de succes, nous envoie
autre chose ». Question juste : le detecteur strict pose la veille generalisait **une seule**
observation. Verifie dans le navigateur, sur les vrais appels.*

## Le temoin qu'il fallait poser d'abord

| appel | reponse |
|---|---|
| `mode` inexistant | **404**, corps vide |
| `mode` vide | **404**, corps vide |
| `annonce-SuiviVente-vente-deleteVente` | **404** — ce verbe **n'existe pas** |
| `ventes-deleteVente` | **200** + vide — le verbe **existe bien** |

> Sans ce temoin, un corps vide ne prouvait rien : il pouvait signaler un mode mal orthographie.
> Il confirme au passage que **les trois verbes du worker sont les bons**.

## L'offre — regle PROUVEE

| appel | reponse |
|---|---|
| `accepte` sur 33026 (reelle) | `"1"` |
| `refus` sur 33026 (reelle) | `"1"` |
| `accepte` sur 33027 (reelle) | `"1"` |
| **type invalide** | `"[]"` |
| **offre inexistante** | `"[]"` |

**Trois succes, et deux causes d'echec DIFFERENTES qui rendent toutes deux `"[]"`.** La regle
`"1"` = succes tient ; ce n'est plus une extrapolation.

## Le compromis et la vente — signature de succes INCONNUE

| appel | reponse |
|---|---|
| `clotureCompromis`, `idComp` bidon | **200 + corps vide** |
| `ventes-deleteVente`, `id` bidon | **200 + corps vide** |

Ces deux verbes repondent **vide quand ils echouent**. Rien ne dit qu'ils ne repondent pas
vide **quand ils reussissent** — aucun des deux n'a jamais ete execute pour de vrai.

**Le risque, en clair** : si le succes est vide lui aussi, le detecteur strict prend une
annulation REUSSIE pour un echec, **defait l'etat** et journalise une erreur.

## Pourquoi ce risque reste borne — verifie, pas suppose

Le geste ecrit `state` / `present_in_hektor` **directement sur `app_affaire_ledger`**
*(definition de `app_geste_affaire_optimistic` lue sur le serveur)*. Or ce registre est
reconstruit depuis Hektor a chaque run : `affaire_ledger.py:234` remet `present_in_hektor=1`
sur conflit, et l'etat est reflete par l'upsert.

> **Quelle que soit l'erreur — faux succes ou faux echec — la verite revient de Hektor au run
> suivant.** Aucune divergence durable n'est possible. La difference est ailleurs : un faux
> echec est **bruyant** (travail en erreur, visible) ; un faux succes est **muet**.

## Une lecture d'appoint : cherchee, pas trouvee

`compromis-getStepComrpomis` et `ventes-wizard-getStepVente` rendent le **meme formulaire
vide** (15 201 caracteres) pour un identifiant reel comme pour un identifiant bidon. Ils ne
discriminent pas. Il n'y a donc pas, cote console, de relecture simple qui prouverait l'effet.

> **C'ETAIT DEJA SU, et c'est Frederic qui me l'a rappele.** L'essai avec temoin du 28/08
> (en tete de cette note) avait etabli le meme fait : *« Hektor ignore l'identifiant a
> l'ouverture, reponses identiques octet pour octet »*. J'ai re-mesure le 29/08 ce que la
> note portait deja. **Cet essai n'etait pas un echec** : c'est lui qui a fait basculer vers
> la lecture du DOM, donc vers les trois verbes.
>
> Ce qu'il ne pouvait PAS donner, en revanche : il portait sur l'**ouverture des
> formulaires**, pas sur les **verbes d'action**. La signature de succes de
> `clotureCompromis` et de `deleteVente` reste donc entiere.

## Ce qui reste a faire

Le worker journalise desormais `reponse_hektor`. **La premiere execution reelle de chaque
geste livrera la signature manquante** — a condition de la lire. Une alternative plus sure
serait un compromis d'essai cree puis annule, mais c'est un acte sur Hektor : au choix de
Frederic.

---

# 🔴 L'ESSAI REEL DU 29/08 — le worker appelait le mauvais verbe

*Fait dans la session Chrome de Frederic, sur le bac a sable **62774** (« TEST C4 du 25-08 Villa
Bellecour », non diffusable, 0 portail). Un compromis d'essai cree, puis annule, en cliquant
dans l'interface. Demande par Frederic : « il faut proceder a des tests comme pour l'offre ».*

## Ce que l'interface fait vraiment

Le parcours d'annulation a **trois** temps, et non un :

```
   1. bouton « Annuler »   ->  clore_compromis_vente('50044')
   2. popin de confirmation « Annulation du compromis ! »   ->  Oui
   3. SECOND formulaire « Annuler un compromis de vente »
      (prix net vendeur, date, note)   ->  bouton « Cloturer »
```

Et l'appel emis au troisieme temps, **releve dans le reseau** :

```
   GET  xmlrpc.php?mode=annonce-SuiviVente-cloture&idCompromis=50044&notes=
```

## Or le worker envoyait ceci

```
   POST xmlrpc.php    mode=annonce-SuiviVente-clotureCompromis
                      idComp=...  isCloture=1  fromContact=false
```

**Mauvais mode, mauvais nom de parametre, mauvaise methode.** Le geste n'aurait jamais rien
annule. `clotureCompromis` existe bien (200, pas 404) — c'est vraisemblablement le chargeur de
la popin, pas l'action.

> **Pourquoi la lecture statique s'est trompee.** Le nom `annonce-SuiviVente-clotureCompromis`
> avait ete lu **dans le JavaScript** de `annuleCompromis`. Il y figure. Mais ce n'est pas
> celui que le navigateur emet au bout du parcours. **Lire le code ne remplace pas regarder
> passer l'appel.** C'est la lecon de cet essai, et elle vaut pour les deux autres gestes.

## Ce que l'essai confirme du correctif

Le compromis est passe a **« Cloture le 29/08/2026 »** : l'annulation marche. Et surtout —
avec l'ancien detecteur, le worker aurait appele un verbe sans effet, recu une reponse vide,
et **declare le geste reussi**. Le detecteur strict, lui, aurait leve une erreur. *La regle
« exiger la preuve du succes » a donc attrape une vraie panne, pas une panne imaginaire.*

## Ce qui reste inconnu, et c'est genant

| | |
|---|---|
| **echec** du vrai verbe *(id 99999999)* | **200 + corps vide** — mesure |
| **succes** du vrai verbe | **non capte** : l'enregistreur reseau a ete pose trop tard |

Si le succes est vide **lui aussi**, alors la reponse de ce verbe **ne porte aucune
information**, et le detecteur strict rejetterait chaque annulation reussie. L'indice penche
dans ce sens : apres l'appel, l'interface **recharge la fiche** (`chargeannonce_Accueil`) au
lieu de lire une reponse.

➡ **Conclusion de conception** : pour le compromis, il ne faut pas arbitrer sur la reponse
mais **verifier l'effet** en relisant la fiche. Reste a eprouver de la meme facon le verbe reel
de la **vente** — `ventes-deleteVente` n'a jamais ete vu passer, il vient lui aussi d'une
lecture statique.

## Trace laissee sur le bac a sable

**Compromis 50044 sur l'annonce 62774, cloture.** A retirer avec le reste des traces d'essai
en fin de chantier *(avec l'affaire 9 a 123 456 au lieu de 79 000)*.

---

# 🔴 SECOND VOLET — la vente, et DEUX TROUS dans le detecteur

*Meme session, meme bac a sable 62774. Une vente d'essai creee par l'interface, enregistreur
reseau arme cette fois. C'est lui qui a tout donne.*

## Ce que Hektor repond quand il REFUSE

L'enregistrement de la vente a produit, en HTTP **200** :

```
   "Vous ne pouvez pas creer un bien"      32 caracteres, repete 8 fois
   {"result":false}                        16 caracteres
```

**Et AUCUN des deux n'est reconnu par mon detecteur.** Verifie en executant la regex elle-meme
dans la page :

| chaine | reconnue comme refus ? |
|---|---|
| `Vous ne pouvez pas creer un bien` | **NON** — la regex dit `ne peu[xt] pas`, pas `ne pouvez pas` |
| `{"result":false}` | **NON** — la regex dit `"success":false`, pas `"result":false` |

Les deux sont **non vides**, donc ils passent aussi la liste des reponses vides.
➡ **Le worker les aurait comptes comme des SUCCES.** Deux faux succes, dans le detecteur cense
les empecher.

> **La lecon, et elle corrige la precedente.** J'avais durci la liste des reponses *vides*.
> Le vrai danger etait ailleurs : Hektor refuse en **HTTP 200 avec une phrase en francais**.
> C'est le **vocabulaire du refus** qu'il faut elargir, pas la liste des vides.

## Ce que la vente a revele d'autre

| | |
|---|---|
| la vente **a bien ete creee** *(id 23287)* | malgre les messages de refus, qui portaient sur autre chose |
| l'enregistrement offre **deux issues** | « Enregistrer & laisser actif » ou « **Enregistrer & archiver** » — a retenir pour la branche « Vendu » de C.4 |
| le bouton `supprimerVente(23287)` | **present en DOM mais masque (0x0)** pour le compte administrateur |

Ce masquage est **le meme phenomene** que les blocs de signature invisibles en root admin
*(idUser 4)*. Le chemin interface est donc ferme pour la suppression d'une vente.

## Ce qui reste a eprouver

- **la signature de succes** de `annonce-SuiviVente-cloture` *(compromis)* — l'echec vaut 200 +
  vide ; le succes n'a pas ete capte ;
- **le vrai verbe de la suppression d'une vente** : `ventes-deleteVente` n'a **jamais ete vu
  passer**. Il vient de la meme lecture statique que le verbe errone du compromis — il faut le
  tenir pour suspect tant qu'on ne l'a pas observe ;
- **l'hypothese de Frederic** : supprimer la vente fait-il revivre le compromis ? Non tranchee.

## Traces laissees sur le bac a sable 62774

```
   compromis 50044   cloture
   vente     23287   active  ->  le bien porte « BIEN VENDU 151 000 EUR »
```

A retirer en fin de chantier, avec l'affaire 9 (123 456 au lieu de 79 000).

---

# ⚖️ LE VERDICT — mesure du succes obtenue, et elle invalide mon correctif

*Frederic a ouvert lui-meme l'URL de suppression (le garde-fou de mon outil bloquait l'appel
depuis ma session). Il rapporte : **page blanche**. Puis j'ai relu la fiche.*

## La suppression a REUSSI, et elle a repondu VIDE

```
   GET  xmlrpc.php?mode=ventes-deleteVente&id=23287     ->  200, corps VIDE
```

Verifie sur la fiche apres coup :

| | |
|---|---|
| `supprimerVente(23287)` | **disparu du DOM** — la vente n'existe plus |
| « BIEN VENDU » | **absent** — le bien n'est plus vendu |
| badge | revenu a **COMPROMIS** |

**Le verbe `ventes-deleteVente` etait donc le bon** — contrairement a celui du compromis, qui
lui etait faux. La lecture statique avait vu juste une fois sur deux ; raison de plus pour
mesurer plutot que deduire.

## Ce que ca prouve, et c'est l'inverse de ce que j'avais code

```
   echec (id 99999999)  ->  200 + VIDE
   succes (id 23287)    ->  200 + VIDE
```

**Identiques.** La reponse de ce verbe **ne porte aucune information**.

> Mon detecteur strict rejette toute reponse vide. Il aurait donc pris **chaque suppression
> reussie** pour un echec, remis `present_in_hektor = true`, et journalise une erreur — alors
> que la vente etait bel et bien detruite chez Hektor. **Le faux echec, systematique.**

La question posee par Frederic — *« je ne suis pas sur qu'Hektor, meme en cas de succes, nous
envoie autre chose »* — avait donc exactement raison, et pour le bon geste.

## La regle qui en decoule, par famille de verbe

| geste | arbitre |
|---|---|
| **offre** *(refus / accepte)* | **la reponse** : `"1"` = succes, `"[]"` = echec. Mesure 3 fois + 2 causes d'echec |
| **compromis** *(annuler)* | **relire l'etat** — la reponse est vide a l'echec, et rien ne permet de croire qu'elle ne l'est pas au succes |
| **vente** *(supprimer)* | **relire l'etat** — demontre ci-dessus |

Et dans **tous** les cas, un refus explicite reste un echec : Hektor les rend en **HTTP 200
avec une phrase en francais** *(`Vous ne pouvez pas creer un bien`, `{"result":false}`)*.

## L'hypothese de Frederic — partiellement verifiee

*« supprimer la vente ne va-t-il pas annuler le compromis en meme temps ? »*

Le bien **retombe bien a l'etape compromis**. Mais le compromis 50044 reste **cloture** : la
suppression de la vente ne le ressuscite pas. Reserve honnete : 50044 avait ete cloture
**avant** la creation de la vente, donc l'essai ne dit pas ce qu'il adviendrait d'un compromis
**actif** dont on supprimerait la vente. A eprouver si le cas compte.

## Etat final du bac a sable 62774

```
   compromis 50044   cloture     (a retirer en fin de chantier)
   vente     23287   SUPPRIMEE   (plus rien a nettoyer)
```

---

# ✅ ESSAI EN SESSION NEGOCIATEUR — trois corrections a ce qui precede

*29/08, fin de journee. Frederic : « je pense que le probleme n'est pas l'acces negociateur
mais teste, on sera fixe ». Il avait raison sur les trois points.*

## ① `ajoutebien` n'a JAMAIS rien bloque — et le compromis avait bien ete cree

J'avais conclu que le compte admin ne pouvait pas creer de compromis, en lisant le refus
`Vous ne pouvez pas creer un bien` renvoye par le mode `ajoutebien`.

**Faux.** En supprimant le compromis 50044, un compromis **50045** est apparu : ma tentative
precedente **avait reussi**, elle etait simplement masquee par le bloc de 50044, qui n'affiche
qu'un compromis a la fois. `ajoutebien` est un appel annexe qui echoue sans consequence -- il
avait deja echoue 8 fois pendant la creation de la vente 23287, qui a pourtant abouti.

> **Mes propres mesures contredisaient ma conclusion, et je ne l'ai pas vu.** Le refus d'un
> appel annexe n'est pas le refus du geste.

## ② La vraie contrainte : UN SEUL COMPROMIS A LA FOIS

Sous negociateur, « Ajouter un compromis » rend en clair :

> **« Vous n'avez pas les droits pour creer un compromis lie a cette annonce. »**

Le meme refus qu'en admin, donc **ce n'est pas une affaire de compte** : tant qu'un compromis
existe sur l'annonce -- meme cloture -- on n'en cree pas d'autre. Le supprimer libere la place.

*Cette phrase est une TROISIEME formulation de refus, et ma regex ne la reconnaissait pas
davantage : j'avais ecrit `le droit` au singulier, Hektor ecrit « les droits ». Corrige.*

**Les comptes different quand meme, mais ailleurs** : le negociateur ne peut pas creer de
**vente** *(le statut VENDU disparait de la modale)* ; l'admin le peut. Ils sont complementaires.

## ③ 🔴 LA REPONSE DU COMPROMIS N'EST PAS MUETTE — je m'etais trompe

Annulation d'un compromis **reellement actif** (50045), enregistreur arme :

```
   POST  annonce-SuiviVente-clotureCompromis   ->  7214 car   <- le CHARGEUR du formulaire
   GET   annonce-SuiviVente-cloture            ->     4 car   <- l'ACTION
```

Et l'echec, mesure plus tot avec un identifiant inexistant : **0 caractere**.

| | |
|---|---|
| echec | **vide** |
| succes | **4 caracteres** *(valeur exacte non captee)* |

**Elles different.** Contrairement a la vente -- ou succes et echec rendent tous deux du vide --
la reponse du compromis **porte bien une information**. Ce que j'ai ecrit plus haut, et dans le
message du commit 779e2bf, est donc **inexact pour le compromis**.

*Le code, lui, reste bon* : il arbitre en relisant la fiche, ce qui marche dans les deux cas et
ne depend d'aucune supposition. Mais la raison ecrite etait fausse, et une raison fausse finit
toujours par egarer quelqu'un.

Au passage, ce releve **confirme le correctif du verbe** : `clotureCompromis` en POST est le
chargeur du formulaire *(7 214 caracteres de HTML)*, `cloture` en GET est l'action. L'ancien
worker appelait le chargeur.

## Une interaction statut / transaction, en prime

Supprimer le compromis a fait **redescendre l'annonce de « Sous compromis » a « Sous offre »**,
toute seule. A rapprocher de l'observation inverse du meme jour : cliquer « SOUS COMPROMIS »
change le statut **sans** creer de compromis.

➡ Chez Hektor, **la transaction commande le statut, le statut ne commande pas la transaction.**

## Bac a sable 62774 : propre

```
   compromis 50044   supprime
   compromis 50045   supprime
   vente     23287   supprimee
```

Il ne reste que l'affaire 9 (123 456 au lieu de 79 000), a retirer en fin de chantier.
