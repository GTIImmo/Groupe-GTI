# « Modifier chez Hektor » sur une offre ACCEPTÉE — Hektor refuse, et il le fait en silence

*Mesuré le 13/10/2026, en lecture seule. Point de départ : échec signalé par Frédéric —
offre 33094 de l'annonce 61672, montant à corriger de 16 000 vers 160 000.*

---

## LE FAIT

**Hektor refuse d'ouvrir le formulaire d'une offre dont l'état est `accepted`. Son refus est
un `HTTP 200` avec un CORPS VIDE — zéro octet, aucun message.**

Une offre `proposed` ou `refused` s'ouvre normalement.

| état de l'offre | ouverture `init=1` avec `idOffre` | mesuré sur |
|---|---|---|
| `accepted` | **200 · 0 octet** | 9 offres sur 9 |
| `proposed` | 200 · ~230 000 octets | 2 sur 2 |
| `refused` | 200 · ~230 000 octets | 1 sur 1 |

12 offres réelles, 12 fois la même règle. Aucun contre-exemple.

### L'appel mesuré

```
POST /admin/xmlrpc.php
    mode=annonce-SuiviVente-offre-createOffre
    idAnnonce=<annonce>
    init=1
    idOffre=<offre>
```

C'est exactement l'appel de `submitHektorTransactionStatus`
*(`Console/console_job_worker.js:12449`)*. Aucun `actionContainer[]` → **aucune écriture**.
Scripts : `Console/capture_transaction_actions.js` pour la forme d'origine (28/08).

### Deux témoins qui écartent les fausses pistes

- **Ce n'est pas le nom du paramètre.** Sur une offre `proposed` (33050 / 24933),
  `idOffre` rend **1 193 caractères de plus** que l'ouverture nue : il est donc **lu**, et il
  **pré-remplit**. `id_offre` — la forme employée par la capture du 28/08 — est, lui,
  **ignoré** : réponse identique **octet pour octet** à l'ouverture sans aucun identifiant
  (même md5). ➡ `idOffre` est le bon nom. La note du 28/08 qui concluait « Hektor ignore
  l'identifiant à l'ouverture » **mesurait le mauvais champ**.
- **Ce n'est pas le compromis derrière l'offre.** 61672 n'a **aucun** compromis
  (`compromis_state` vide) et répond quand même vide.

---

## CE QUE ÇA CASSE AUJOURD'HUI

1. **Le bouton « Modifier chez Hektor » est proposé sur une offre acceptée alors qu'il ne peut
   pas aboutir.** Il n'a aucune condition d'état *(`App.tsx:20238`)*.
   **144 offres vivantes sur 185 sont `accepted`, soit 78 %** — sur 144 biens distincts.
2. **Le worker transforme un refus d'état en jargon.** `parseHektorJson` lève
   *« Reponse Hektor JSON invalide init Sous offre: »* — rien après les deux-points. Et cette
   phrase part telle quelle dans la notification du négociateur
   *(`app_notification`, type `job_echec`)*.
3. **Ça contredit une décision écrite.** `TRANSACTIONS_REPRISES.offre = new Set()`
   *(`console_job_worker.js:10893`)* porte l'arbitrage du 07/09 : *« on n'interdit RIEN
   d'avance : on envoie, et si Hektor refuse on montre sa réponse »*. Ici Hektor refuse et
   **sa réponse est vide** : il n'y a rien à montrer. Le cas « refus muet » n'avait pas été
   prévu.
4. **Le filet rejoue pour rien.** `change_hektor_annonce_status` est rejouable 5 fois
   *(`app_console_action_enqueue_due_retries`)*. Un refus d'état ne guérit pas en 24 h :
   5 tentatives, 5 échecs, 5 bruits.

### Ce qui a bien marché

- **Rien n'a été écrit chez Hektor** : l'arrêt a lieu avant l'enregistrement. C'est la
  protection voulue — enregistrer sur une offre existante avec un formulaire vide aurait
  **effacé** séquestre et prix net vendeur *(`console_job_worker.js:12437`)*.
- **L'échec n'est pas silencieux** : notification créée, travail en erreur, visible
  *(chantier ④)*.
- **Chez nous d'abord a tenu** : `app_affaire_champ_app` garde `montant = 160000` avec
  `valeur_hektor_au_moment = 16000` et `valeur_hektor_relue` vide → **non confirmé**, pas
  faussement validé.

---

## POURQUOI LE 08/09 AVAIT « MARCHÉ »

Le seul succès de reprise d'offre *(job `01f5a4dc`, offre 33050)* portait sur une offre
**`proposed`**. Les 10 envois d'offre antérieurs ont tous `init_error = true` dans
`result_json` — **10 sur 10** : cette ouverture renvoie **toujours** `error: true`, même
quand elle rend le formulaire. Le worker le tolère depuis le début. Ce qu'il ne tolère pas,
c'est **le vide**.

➡ La preuve du 08/09 ne couvrait donc **pas** le cas majoritaire. Le relevé de l'offre
champ par champ était d'ailleurs resté **ouvert** dans la liste (§ 3.2d, *« offre ⚠ AUTRE
MÉTHODE… il faut une session négociateur »*).

---

## LA TRACE QUI EXISTAIT DÉJÀ, ET QUI N'AVAIT PAS SERVI

`notice/ACTIONS_TRANSACTION_HEKTOR_2026-08-28.md`, mesure du 29/08 :

> | `clotureCompromis`, `idComp` bidon | **200 + corps vide** |
> | `ventes-deleteVente`, `id` bidon | **200 + corps vide** |
>
> *« Ces deux verbes répondent **vide quand ils échouent**. »*

**`200 + corps vide` est la signature documentée du refus chez Hektor.** Elle était connue
depuis le 29/08 pour deux verbes ; elle vaut aussi pour l'ouverture d'une offre acceptée.
Elle n'avait pas été reportée sur ce chemin-là.

À comparer avec le compromis, où Hektor refuse **en clair** : *« Désolé, un compromis clôturé
ne peut pas être modifié »* *(`Modules/GenericPopinStepperManager.js`, essai du 03/09)*.
**Même nature de refus, deux politesses différentes.**

---

## ET UNE OFFRE NON ACCEPTÉE, ALORS ? — mesuré le 13/10, et c'est OUI

**`idOffre` PRÉ-REMPLIT le formulaire, et l'enregistrement d'une offre `proposed` est
PROUVÉ** — a posteriori, 35 jours après, par Hektor lui-même.

Les valeurs lues dans les formulaires rendus *(même appel, lecture seule)* :

| offre | état | avec `idOffre` | sans identifiant | registre *(= Hektor, relu chaque nuit)* |
|---|---|---|---|---|
| **33050** / 24933 | `proposed` | `montantOffre=167000` · `nbJoursValidite=33` | `180000` · `10` *(défauts du bien)* | **167 000** |
| **33073** / 11832 | `refused` | `montantOffre=168000` | `175000` *(défaut)* | **168 000** |

➡ **La reprise du 08/09 a bel et bien modifié l'offre 33050.** Le travail avait conclu
*« MODIFIÉ mais NON VÉRIFIÉ — la relecture ne l'a pas retrouvé »* ; elle est **vérifiée
maintenant** : le formulaire de Hektor porte **167 000**, exactement le montant envoyé ce
jour-là, et **33 jours** de validité, qui ne sont pas le défaut du bien (10). Aucune écriture
locale n'a pu maquiller ce chiffre : `app_affaire_champ_app` n'a que les 5 lignes de la
**création** du 04/09, aucune du 08/09, et `affaire_ledger.py:782` remet `montant` depuis
Hektor **à chaque run**.

### Donc, règle d'exploitation

```
proposed   MODIFIABLE          ouverture + pre-remplissage + enregistrement PROUVES
refused    MODIFIABLE a priori ouverture + pre-remplissage prouves ; enregistrement JAMAIS essaye
accepted   PAS MODIFIABLE      Hektor n'ouvre meme pas le formulaire
```

**➡ L'ORDRE DES GESTES COMPTE : corriger le montant D'ABORD, accepter ENSUITE.** Une fois
acceptée, l'offre est figée chez Hektor.

### ⚠ UN PIÈGE DANS LE PRÉ-REMPLISSAGE

`dateOffre` revient à **la date du jour** (`13-10-2026`) dans les deux cas, **pas** la date
réelle de l'offre (04/09 pour 33050, 22/09 pour 33073). Le pré-remplissage **ne restaure pas
la date**. Une reprise qui ne poserait pas explicitement `transaction_date` **écraserait la
date de l'offre par celle du jour**. Le 08/09 l'avait posée (`2026-09-04`) et la date a tenu
— mais c'est la charge de l'app qui l'a sauvée, pas le formulaire.

### L'état, lui, ne passe PAS par ce formulaire

Aucun témoin d'état *(refus/accepté)* dans le rendu. Le changement d'état est un geste
séparé, `updateOffre` avec `type=accepte|refus` *(relevé du 28/08)* — et l'app l'a déjà, avec
ses boutons « Accepter l'offre » et « Refuser l'offre ». Le souhait du 07/09 *(« modifier une
offre refusée, la passer en valide, changer le montant et l'état »)* est donc **deux gestes
que l'app possède tous les deux**, dans cet ordre.

---

## CE QUI RESTE NON MESURÉ — à ne pas conclure à sa place

- **Hektor lui-même sait-il modifier une offre acceptée depuis son écran ?** Si son interface
  le refuse aussi, la règle est de Hektor et l'app doit simplement la dire. **Un clic dans
  Hektor tranche.**
- **Une offre `refused` s'OUVRE et se PRÉ-REMPLIT — mais l'enregistrement passe-t-il ?** Non
  mesuré : le vérifier demande une écriture. Structurellement c'est le même chemin que
  `proposed`, qui est prouvé — mais « structurellement pareil » n'est pas une mesure.
- **Le contexte négociateur.** Toutes ces mesures sont en session **admin** : le serveur rend
  bien le formulaire, c'est l'enregistrement que l'admin se voit refuser *(« un compte
  administrateur ne peut pas saisir une offre »)*. La corrélation état → vide est donc établie
  en admin ; rien n'indique qu'elle diffère en négociateur, mais ce n'est pas prouvé.
- **Y a-t-il un verbe pour re-passer une offre acceptée en proposée ?** `updateOffre` ne
  connaît que `type=accepte` et `type=refus` *(relevé du 28/08)*. Aucun retour à `proposed`
  n'est connu.

---

## LES SORTIES POSSIBLES — aucune n'est choisie

| | ce que ça fait | ce que ça coûte |
|---|---|---|
| **A** | **Dire la vérité à l'écran** : éteindre « Modifier chez Hektor » quand l'offre est `accepted`, avec la raison en clair, comme le fait déjà le verrou compromis/vente *(`App.tsx:20204`)* | front seul · ne répare pas le besoin |
| **B** | **Traduire le vide** côté worker : *« Hektor refuse de rouvrir une offre acceptée »* au lieu du jargon, et **ne pas rejouer** un refus d'état | worker · un redémarrage des 4 services |
| **C** | **Le chemin métier** : refuser l'offre → corriger le montant → l'accepter de nouveau. Les trois verbes existent *(`updateOffre`)* | change l'historique d'état de l'offre chez Hektor · l'enregistrement sur une offre refusée n'est **pas** prouvé |
| **D** | **Garder la correction chez nous** sans l'envoyer : le montant vit dans notre registre, marqué non confirmé | divergence assumée avec Hektor |

**A et B vont ensemble** : l'un empêche le geste impossible, l'autre explique celui qui part
quand même. **C et D sont des décisions de Frédéric**, pas des correctifs.

---

# ✅ A + B SONT CODÉS — « go A+B » de Frédéric, 13/10

**2 fichiers, 158 lignes ajoutées, 11 retirées. Aucune écriture en base, aucun appel à
Hektor, aucun service redémarré, rien de déployé.**

## A · le front — `apps/hektor-v1/src/App.tsx`

- `offreAccepteeFigeeChezHektor(affaire)` : vrai **seulement** si `kind = 'offre'` **et**
  `state = 'accepted'`. L'état se lit sur **l'affaire que la modale affiche**, jamais sur
  `dossier.offre_state` *(ce dernier n'est rempli que par le run de nuit et peut désigner
  l'offre précédente — incident du 02/09)*.
- « Modifier chez Hektor » est **éteint** dans ce cas, avec l'infobulle qui dit pourquoi.
- Un **bandeau en clair** l'explique et donne le remède — doctrine 2.2c : *« un bouton gris
  et muet est pire que pas de bouton »*.
- ⚠ **Le remède se tait quand il n'est pas applicable** : si l'offre est verrouillée par son
  dossier *(un compromis ou une vente derrière elle)*, « Refuser l'offre » est **caché** —
  le bandeau renvoie alors au message précédent au lieu de conseiller un geste introuvable.

## B · le worker — `Console/console_job_worker.js`

- **Le refus muet devient une phrase**, au point exact de l'échec (avant `parseHektorJson`) :

  > `[REFUS D'ETAT] Hektor refuse de rouvrir offre 33094 (etat « accepted ») : il repond 200
  > avec un corps VIDE, sans aucun message. Une offre ACCEPTEE n'est plus modifiable chez lui
  > (mesure du 13/10) ; une offre proposee ou refusee s'ouvre. Pour corriger le montant d'une
  > offre acceptee : la refuser, corriger, puis l'accepter de nouveau. Rien n'a ete envoye
  > chez Hektor.`

- **Plus de rejeu pour un refus d'état** : la marque `[REFUS D'ETAT]` voyage dans le message,
  `processOnce` la lit, `finishJob` porte alors `attempt_count` au maximum. **C'est le
  mécanisme que le projet avait déjà choisi** — la boucle 0 de la même fonction SQL écarte
  les travaux dépassés exactement comme ça : *« ils sortent donc d'eux-mêmes de la condition
  ci-dessous »*.
- ⚠ **Deux copies d'une constante** : `max_tentatives` vit dans la fonction SQL, 
  `REJEU_MAX_TENTATIVES` dans le worker. Si l'une monte sans l'autre, **la panne est
  bénigne** : le travail redevient rejouable, c'est-à-dire le comportement d'avant.

## L'épreuve — `Console/test_offre_acceptee_figee.js`, 33 sur 33

Il **découpe le vrai code des deux sources et le fait tourner** avec de faux appels. Ni
Hektor, ni Supabase, aucun fichier écrit. Les témoins inverses sont dedans :

- **B2** un corps **non vide** ne lève rien → le chemin des 10 envois tolérés (`error: true`)
  est **intact** ;
- **B6c** une panne ordinaire *(timeout)* **garde** son rejeu ;
- **A2 → A7** offre **refusée**, **proposée**, **état inconnu**, **compromis**, **vente** :
  tous restent **libres**. On ne bride que le cas mesuré.

⚠ **Piège payé au passage** : `console_job_worker.js` est en **CRLF**, `App.tsx` en **LF**.
La première version du test cherchait `"\n  }"` et ne trouvait **rien**. Le test normalise
pour découper.

`npm run build` *(donc `tsc -b`)* : **vert**.

## ⛔ CE QUI RESTE, ET QUI DEMANDE SON ACCORD

```
1 REDEMARRER LES 4 SERVICES WORKER   -- sans ca, B n'est PAS actif
2 DEPLOYER LE FRONT (push vers main) -- sans ca, A n'est PAS a l'ecran
3 LE TRAVAIL d9ed984e porte encore 3 rejeux inutiles. Tant que B n'est pas
  redemarre, ils partiront. Le neutraliser = une ecriture en production.
4 NON VERIFIE A L'ECRAN : la preuve visuelle demande le deploiement.
```

**Et deux trouvailles sorties du lot, NON traitées** *(elles ne sont pas dans le périmètre
« A+B »)* :

- **le marqueur d'offre manquant** : `MARQUEURS_TRANSACTION`
  *(`console_job_worker.js`)* ne connaît que `vente` et `compromis`. Aucune modification
  d'offre n'a jamais pu être vérifiée par la machine — c'est pour ça que le trou est resté
  invisible 36 jours ;
- **le bandeau ne dit pas si « Modifier » doit aussi disparaître** quand l'offre est
  verrouillée par son dossier. C'est un périmètre : la décision est à Frédéric.
