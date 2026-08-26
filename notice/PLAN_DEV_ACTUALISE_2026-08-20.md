# Plan de développement actualisé — 20/08/2026

Remplace le plan du 18/08. Établi après quatre audits mesurés :
identifiants (19/08), workers (20/08), diffusion (20/08), contacts et modales (20/08).

---

## CE QUI EST FAIT

| | | Commit |
|---|---|---|
| Un dossier ne perd jamais son numéro | on marque `absent_depuis`, on ne supprime plus | `dc45c62` |
| Le correctif anti-fantôme couvre 21 tables au lieu de 5 | ~600 annonces abîmées depuis juin | `aa8a374` |
| **Les identifiants d'annonce sont alignés** | 13 215 / 13 215, vérifié après un run complet | `99e262f` |
| Pipeline et surveillance fiabilisés | chauffage non bloquant, sauvegarde surveillée, 4 sentinelles en critique | 5 commits |

---

## ⛔ AVANT DE COMMENCER UN CHANTIER — à relire, sans exception

**Cette liste existe parce que le 20/08 j'ai oublié trois fois un point déjà documenté.**
Un plan ne protège de rien s'il n'est pas relu avant chaque geste.

| | À relire | Pourquoi |
|---|---|---|
| **1** | **Ce document en entier** — pas seulement la tâche visée | les pièges sont dans les sections voisines |
| **2** | Les **notes citées** par le chantier concerné | elles contiennent les décisions déjà prises |
| **3** | `ls notice/*.md` **et la racine**, par mot-clé | ~158 notes ; celles qui comptent ne sont pas toujours dans `notice/` |
| **4** | **L'historique git** : `git log --all --diff-filter=D -- 'notice/*'` | 12 notes supprimées le 19/08 portent encore de la doctrine active |
| **5** | La **mémoire projet** de l'assistant | la réponse y était déjà, deux fois, le 20/08 |

**Trois questions à se poser avant d'affirmer qu'une chose est cassée :**

1. **Est-ce documenté ?** Dans ce projet, ce qui ressemble à une négligence est presque toujours
   une décision écrite quelque part.
2. **Est-ce mesuré ?** Une détection `ILIKE` mal écrite m'a fait affirmer l'inverse de la vérité
   sur `app_edit_search_optimistic`. **Mesurer, puis conclure.**
3. **Qu'est-ce que j'oublie ?** Lister les cas voisins : si on traite « la recherche modifiée »,
   a-t-on traité « la recherche supprimée » ? Si on traite les annonces, et les contacts ?
   les affaires ? les recherches ?

---

## LES TÂCHES, DANS L'ORDRE

*Ordre **validé par Frédéric le 21/08/2026**, après l'audit de la data locale
(`notice/AUDIT_DATA_LOCALE_ET_SYNCHRO_2026-08-21.md`). Il remplace la liste plate précédente.*

### ⛔ LA MÉTHODE — arrêtée le 21/08, sans exception

Avant **chaque étape** et **avant tout code**, quatre phrases :

```
   ce que ca fait  ·  ce que ca touche  ·  comment on revient en arriere  ·  comment on verifie
```

Frédéric valide, **puis** on code. Jamais l'inverse. *« Je ne veux pas d'ambiguïté. »*

### 📚 LES NOTES QUI FONT AUTORITÉ — rattachées le 24/08

*L'audit du 24/08 a trouvé que **19 des 21 notes les plus récentes n'étaient citées nulle part
dans ce plan**. C'est ce qui m'a fait réinventer, cinq jours plus tard, un travail déjà fait.
Ce qui suit répare la cause, pas le symptôme.*

| Note | Ce qu'elle tranche | Lue par |
|---|---|---|
| `METHODE_DE_TRAVAIL_2026-08-20` | **le contrat de travail** : lire, mesurer, expliquer, faire valider, prouver | **avant chaque tâche** |
| `A1_CHAMPS_PROPRIETE_APP_2026-08-19` | **189 champs** que l'app possède · la règle « l'import n'a pas le droit de réécrire » · le mécanisme « c'est une soustraction » · **3 arbitrages en attente** | **C.4** |
| `ETUDE_WORKERS_EXISTANT_ET_FAISABILITE_2026-08-20` | les 4 familles · **16 workers** sont le gisement réel · **7 sur 34 marchent déjà sans Hektor** · **3 seulement** dépendent vraiment de lui | **C.4** |
| `PLAN_DEV_MANDAT_CLOTURE.md` | **cadrage validé le 30/07, dev non commencé** · les déclencheurs · les motifs Hektor · la clôture cible par **ID interne** · « échu ≠ clos » | **C.13** |
| `ETUDE_OU_EN_SOMMES_NOUS_2026-08-25` | **E.0** · les deux circuits chronométrés · ce que l'app sait déjà écrire dans Hektor · les 4 manques | **E.0, C.4** |
| `NOTE_CHAINE_DES_MANDATS_2026-08-25` | la chaîne des mandats de bout en bout · `mandat_source_id` **est** `hektor_mandat_id` · pourquoi le registre se défie de `hektor_mandat` · **342 identifiants partagés entre annonces** → toujours interroger par le **couple** | **C.4, C.5** |
| `AUDIT_IDENTITE_CONTACTS_2026-08-20` | l'état des lieux du 20/08 · **son verrou est levé**, voir la relecture ci-dessous | **C.2** |
| `RELECTURE_IDENTITE_CONTACTS_2026-08-24` | **C.2a, fait** · 4 tables portent 95 % · 3 fonctions à basculer, pas 11 · `hektor_contact_id` **est la clé primaire** | **C.2b, C.9** |
| `AUDIT_DATA_LOCALE_ET_SYNCHRO_2026-08-21` | le sens unique · le régime de chaque table · les 3 trous | **B, C.6, C.7** |
| `AUDIT_ET_PLAN_REALISTE_2026-08-22` | l'état mesuré des 5 supports · les durées | **le calendrier** |
| `AUDIT_SESSION_ET_PLAN_2026-08-24` | cet audit · la duplication · l'ordre corrigé | |
| `ETUDE_HISTORIQUE_RECHERCHES_ACQUEREUR_2026-08-21` | pourquoi les recherches sont autonomes depuis le 19/06 | **C.3** |
| `ETUDE_ORIGINE_CLE_RECHERCHE_2026-08-21` | un seul fabricant de nom · la doublure | *fait* |
| `VISION_GLOBALE_DEV_INDEPENDANCE_2026-08-18` | la vision d'ensemble | |
| `NOTE_PLAN_SAUVEGARDE_2026-08-18` | les 4 niveaux · pourquoi le niveau 3 est désactivé | **0.1, D** |

> **Règle** : une tâche qui cite une note **la lit avant de commencer**. Une note qui n'est
> citée nulle part est une note perdue.

---

### 🛤 LES TROIS PISTES — posées par Frédéric le 24/08 au soir

*Ce qui suit **affine** la section des trois étapes ci-dessous. Les étapes racontaient l'histoire ;
elles laissaient croire que le code attendait une décision d'organisation. **C'est faux.** Trois
choses avancent indépendamment, et il ne faut jamais les confondre :*

```
   PISTE 1 -- LE CODE EST PRET       C.2b C.12 C.6 C.5 C.7 C.8 C.9 C.4 C.11
                                     puis E.0 : que ne sait pas faire l'app ?
                                     -> se construit MAINTENANT, dormant
                                     -> ne depend de PERSONNE

   PISTE 2 -- LES GENS BOUGENT       quand ils veulent, un par un
                                     jamais les deux systemes pour LA MEME personne
                                     -> depend de Frederic seul

   PISTE 3 -- ON COUPE LES WORKERS   quand A.1 / A.2 / A.3 sont faits
                                     -> depend de contrats exterieurs
```

#### Ce que ça change, concrètement

**On construit tout, dormant, et le jour J n'est plus qu'un paramétrage.** C'est le patron déjà
utilisé quatre fois ici — `VITE_APP_COCKPIT_V2_ENABLED`, `VITE_APP_CONTACT_V2_ENABLED`,
`VITE_APP_MANDAT_V3_ENABLED`, `APP_BROUILLON_BUCKET_ENABLED` — et c'est la méthode de la
doublure, qui a marché trois fois : `app_dossier`, `app_affaire_ledger`, `app_search_registry`.

> ⚠ **La condition, mesurée le 24/08** : ces quatre drapeaux ont été posés les 17/07, 23/07,
> 26/07 et 22/06 — **aucun n'a jamais été allumé en production**. 29 à 38 jours de sommeil.
> **Construire dormant est facile ; c'est l'allumage qui ne se fait pas.**
>
> Et le journal des doublures dit `app seule = 45`, **plat trois jours sur trois** — parce que
> personne n'utilise l'app. **Tout ce qu'on sait de « l'app comme auteur » est mesuré sur une app
> que personne n'exerce.** L'antidote est de Frédéric : **il passe sur l'app pendant qu'eux restent
> dans Hektor**. Ça rend les mesures vraies, et ça éprouve C.1' avec son seul travail en jeu.

#### Le modèle, dans les mots de Frédéric — et ce qui existe en face

```
        L'APP ecrit
             |
             +--> Supabase --(la DESCENTE)--> LE SERVEUR      [FAIT le 22/08, B.1]
             |
             +--> worker --------------------> HEKTOR

        HEKTOR --(import de nuit)--> LE MIROIR --> LE SERVEUR  [depuis toujours]
```

> *« Le miroir de Hektor devient une **source d'information** ».* C'est le nom exact de **C.7**.
> Aujourd'hui le miroir n'est pas *une* source, il est **la** source — le serveur se reconstruit
> depuis lui chaque nuit. C.7 le fait passer de **vérité** à **témoignage**.

**Les deux sortes d'écart ont déjà chacune leur instrument :**

| L'écart | Ce que c'est | L'instrument | Depuis |
|---|---|---|---|
| **conflit de worker** | l'envoi vers Hektor a été bloqué ou a échoué | `app_*_pending.conflict` · 8 sondes · bandeau + boutons | **24/08** *(C.1')* |
| **conflit de miroir** | le miroir dit autre chose que ce que l'app détient | les 10 doublures + le journal de 07:30 | **22/08** *(B.2/B.4)* |

> **Mais détecter n'est pas résoudre.** Les doublures voient l'écart, elles ne le tranchent pas —
> et chaque nuit le serveur se reconstruit depuis le miroir, donc **Hektor regagne par défaut**.
> Pas parce qu'on l'a décidé : **parce qu'il est seul dans la pièce**. C.7 est l'endroit où
> l'écart se résout ; C.6 fournit le *quoi* à réconcilier.

#### La réserve sur « pas les deux en même temps »

Ça se lit **par personne**, pas par système. Si l'un passe sur l'app pendant que l'autre reste
dans Hektor, **les deux systèmes sont vivants** à l'échelle de l'agence. Ce qui rend ça tenable,
c'est que les dossiers sont en **portefeuilles** *(mesuré le 24/08 : Sylvie 2 181 · Marion 1 878 ·
Groupe GTI 1 702 · Nicolas 1 522 · Christèle 1 330 · Arnaud 1 122…)*.

Le risque ne porte donc pas sur le volume : il porte sur les **dossiers partagés** — un acquéreur
suivi par deux négociateurs, un mandat en co-listing. **C'est exactement ce que le journal des
doublures verra chaque matin.**

---

### 🗝 LES TROIS ÉTAPES — posées par Frédéric le 24/08

*Ce n'est pas un détail d'organisation : **c'est ce qui décide de la moitié du travail
technique**. Le plan précédent supposait que l'app et Hektor seraient utilisés en même temps.
Ils ne le seront pas.*

```
   ETAPE 1  (aujourd'hui)   tout se fait dans HEKTOR
                            les negociateurs n'ont pas acces a l'app, sauf Frederic

   ETAPE 2                  les negociateurs utilisent L'APP
                            et il leur est INTERDIT d'ouvrir Hektor en meme temps

   ETAPE 3                  la coupure
```

#### Ce que l'étape 2 supprime

Il y a **trois** façons pour l'app et Hektor de diverger :

| | | À l'étape 2 |
|---|---|---|
| **①** | l'envoi n'est jamais parti | **reste** |
| **②** | l'envoi a raté *(Hektor injoignable, session morte, refus)* | **reste** |
| **③** | quelqu'un a modifié dans Hektor entre-temps | **disparaît** |

**Le cas ③ disparaît, et avec lui tout l'arbitrage** — la règle de priorité, la tolérance de
comparaison, la notification de conflit. C'était la moitié de l'ancienne tâche C.1.

Mieux : si personne ne touche à Hektor, le run de nuit ne rapporte plus *les modifications de
quelqu'un d'autre*. Il rapporte **ce que l'app vient d'y écrire**. Le va-et-vient devient une
**confirmation**, plus une compétition.

#### Ce qu'elle ne supprime PAS — et c'est le vrai danger

```
   l'envoi echoue  ->  la protection tombe  ->  le run de nuit ECRASE la saisie
```

**Démontré sur le contact 602197, le 24/08.** Un négociateur affine une recherche à 120 000 €.
L'envoi est bloqué. Le travail est marqué `done`. La ligne de protection disparaît. Le run
suivant rapporte la valeur de Hektor. **Les trois supports disent aujourd'hui `prix_min = 0` —
la saisie n'existe nulle part.** Et personne n'a rien modifié dans Hektor.

> ⚠ **La doublure ne protège pas de ça.** Elle copie ce que Supabase contient. Si Supabase est
> écrasé, elle copie l'écrasement. Elle donne au serveur une **copie fidèle**, pas une
> **mémoire**.

#### Les trois garde-fous d'aujourd'hui ne se ressemblent pas

*Relevé dans `console_job_worker.js` le 24/08 — ils ont été écrits à des moments différents.*

| | **Recherche** | **Contact** | **Annonce** |
|---|---|---|---|
| Compare | **le contenu** *(empreinte villes/types/critères)* | une **date** | une **date** |
| Relit avant | **oui**, read-through complet | non | non |
| Si la relecture échoue | **bloque** | **écrit quand même** | **écrit quand même** |
| Prévient le négociateur | **oui** | **oui** | **non** |
| Sans photo | aucun garde-fou | aucun garde-fou | aucun garde-fou |
| Après blocage | `done` · **jamais repris** | `done` · **jamais repris** | `done` · **jamais repris** |

**Les trois savent détecter. Aucun ne sait retenir.** C'est le seul défaut qui compte, et c'est
le seul que l'étape 2 ne corrige pas.

*(Le « best-effort » du contact et de l'annonce mérite d'être nommé : ligne 11421,
« si la relecture API échoue, on écrit ». Le moment où l'on est le moins sûr est celui où l'on
protège le moins.)*

---

### 📍 LE TABLEAU DE BORD — posé le 22/08 après l'audit

*Le plan disait QUOI faire, jamais COMBIEN DE TEMPS ni QUI BLOQUE QUI.*

#### Le chemin critique — et il n'est pas technique

```
   A.1 PORTAILS  +  A.2 SIGNATURE   ------------------------->  LA COUPURE
   semaines a mois, ne depend pas de moi, A ZERO

   PISTE 1, le code       C.2b C.6 C.7 C.12 [FAITS] -> C.4 -> C.9 -> C.13
                          (C.5 ANNULEE le 25/08 au soir : retour arriere)
                          -> C.11 -> E.0 [FAIT le 25/08]
                                                     4 a 6 semaines
                          SE CONSTRUIT MAINTENANT, dormant. N'attend personne.

   PISTE 2, les gens      quand ils veulent, un par un.   Frederic seul.
   PISTE 3, la coupure    quand A.1/A.2/A.3 sont faits.   A ZERO.

   Fait a ce jour : 0.1 0.2 0.4 0.5 0.6 0.7 0.8 | B.1 B.2 B.4 B.5
                    C.1' C.2a C.2b C.3 C.6 C.7 C.12
```

> **Aucun travail technique ne permet de couper Hektor tant que A.1 et A.2 ne sont pas faits.**
> Tes annonces passent par **son** abonnement portails, tes mandats se signent avec **son**
> contrat. Chaque semaine de retard sur A s'ajoute **intégralement** à la date de coupure.

> **Corrigé le 24/08** : la colonne « sans Hektor » était une contrainte de la panne du 22,
> pas une règle. Hektor répond en 0,23 s. Ce qui commande désormais l'ordre, c'est **avant** ou
> **pendant** l'étape 2 — voir la section des trois étapes.

#### Ce qui peut avancer SANS Hektor *(section de la panne du 22/08, conservée pour mémoire)*

| | Tâche | Durée |
|---|---|---|
| **0.4 → 0.7** | Les quatre gestes de sécurité du bloc 0 | **1 h** |
| **D.1a** | Mesurer le vrai périmètre du rapatriement des documents | **1 h** |
| ✅ **C.2a** | Identité des contacts — la relecture | **FAIT le 24/08** |
| **C.6** | La table « ce que l'app détient » pour l'annonce | **1 à 2 jours** |

#### Ce qui exige Hektor vivant

| | Tâche | Durée | Sur quoi repose l'estimation |
|---|---|---|---|
| **C.1** | La règle de comparaison | **3 à 5 j** | le garde-fou existe ; c'est le verdict qu'on inverse |
| **C.3** | L'exception recherches | **1 à 2 j** | la doublure existe déjà |
| **C.2b** | Identité des contacts — le code | **3 à 5 j** *(revu par C.2a)* | 4 tables, 3 fonctions. **Sans le changement de clé primaire**, qui est un second chantier |
| **C.4** | Les workers, un par un | **2 à 3 sem.** | 35 types de travaux |
| **C.7** | Le serveur lit sa base | **2 à 3 j** | collée à C.1 |
| **C.9** | La création part de l'app | **1 à 2 sem.** | après C.7 |

> ⚠ **Ces durées sont des FOURCHETTES, et c'est volontaire.** Trois fois cette semaine j'ai
> donné un chiffre précis là où la donnée ne portait qu'un ordre de grandeur — « ~270
> recherches invisibles » *(réalité : environ 5)*, « 20 000 rapprochements disparus »
> *(réalité : zéro — j'avais comparé une estimation à un comptage)*, « ~2,7 Go » *(réalité :
> 4,32)*. **Un chiffre qui entre dans une décision se mesure, il ne s'estime pas.**

#### Une dette signalée, pas mise au plan

`App.tsx` fait **37 204 lignes** — les trois quarts du front dans un seul fichier. Ça marche,
et le découper serait un chantier sans valeur métier. Mais **C.9 va beaucoup y toucher**, et
c'est le genre de dette qui se paie au pire moment. À savoir, pas à traiter maintenant.

---

### LE BUT, redit par Frédéric le 21/08

> *« Je veux que mon app et mon serveur fonctionnent comme une vraie solution métier, sauf que
> dans un premier temps les données rafraîchies proviennent d'une API avec Hektor, et que chaque
> modification doit lui être envoyée pour qu'il reste à jour — mandat, pub, etc. »*

C'est le chantier 3, mot pour mot : **écrire chez soi d'abord, envoyer ensuite, confirmer au
retour.** Deux précisions à ne jamais perdre de vue :

- **Les recherches sont la seule exception** — décision de Frédéric du 20/08 : elles ne remontent
  plus à Hektor, parce que la modale n'exprime que 7 critères sur 12 et que les renvoyer les
  appauvrit. *Décision prise, geste pas encore fait.*
- **On lit par une API, on n'écrit PAS par une API.** L'écriture passe par un robot qui remplit le
  formulaire web avec les cookies d'un négociateur. C'est la vraie fragilité de « Hektor reste à
  jour », et elle disparaîtra avec Hektor — elle ne se corrigera pas.

---

### ✅ CE QUI EST FAIT

| | Tâche | |
|---|---|---|
| ✅ | Avertissement d'échec des workers | `48e475a` |
| ✅ **1** | ~~**Rattacher l'irremplaçable**~~ — 15 lignes déplacées, 0 perdue — propositions, relances, retours acquéreur, envois | 15 lignes, **0 ambiguïté** |
| **1bis** | *(cas des recherches SUPPRIMÉES chez Hektor : 31 clés, 681 rapprochements — **rien d'irremplaçable dessous**)* | traité par la tâche 2 |
| ✅ **2** | ~~**Supprimer le recalculable**~~ — 13 339 lignes — 1 373 rapprochements + 11 966 lignes d'historique | après le 1 |
| ✅ **2bis** | ~~**Poser le balayage nocturne**~~ — `app_sweep_search_orphans`, 07:00 | sinon la fuite reprend dès le lendemain |
| ✅ **2ter** | ~~**Sentinelle**~~ sur les orphelins NON rattachables | attendu 0 |
| ✅ **2quater** | ~~**Le balayage tient un carnet**~~ — `app_sweep_search_orphans_log` | une réparation qui ne dit pas ce qu'elle répare ne se surveille pas |
| ✅ **3** | ~~Le numéro Hektor d'**annonce** a le droit d'être vide~~ + sa sentinelle | |
| ✅ **4** | ~~**Identité des transactions**~~ **20/08** — 28 980 affaires numérotées par l'app, clé basculée | **confirmé par lecture** : le worker envoie `idOffre=""` — il ne sait que créer |
| ✅ **4bis** | ~~MESURER : supprimée ou archivée ?~~ **ARCHIVÉE, toujours.** Hektor ne sait pas supprimer une recherche (`console_job_worker.js:11878-11890`) | ⇒ **le rang ne glisse jamais.** Les « 184 contacts à risque » n'existent pas |
| ✅ **4bis-A** | ~~**Les recherches archivées ne sont plus supprimées de Supabase**~~ — 6 777 récupérées | **C'ÉTAIT LA FUITE.** Règle *delete-never* |
| ✅ **4bis-B** | ~~**Le verrou du moteur de rapprochement**~~ — il ne score que les actives | **posé AVANT les données** |
| ✅ **4ter** | ~~Un numéro propre pour la recherche, en doublure~~ — `app_search_id` + `app_search_registry` | table à part, car le run complet **vide** la couche |
| ✅ **4quater** | ~~**Observer** la doublure~~ — **close le 21/08** | le cas limite a été provoqué et vérifié en direct |
| ✅ **4quinquies** | ~~**FIGER le nom de la recherche**~~ — 76 841 noms figés, 0 doublon | **L'empreinte n'est PAS touchée** — c'était la condition posée |
| ✅ **4sexies** | ~~**SENTINELLE « une recherche ne disparaît jamais »**~~ **21/08** — `app_search_count_high_water` + cron + sonde, seuil 0 | **entendue sonner**, puis restaurée. Ferme le risque de position introduit par 4quinquies |

---

### BLOC 0 — PROTÉGER L'EXISTANT · *cette semaine, quelques heures*

| | Tâche | Pourquoi maintenant |
|---|---|---|
| ✅ **0.1** | ~~**Mettre `app_search_registry` et `app_affaire_ledger` dans la sauvegarde de nuit**~~ **FAITE le 22/08** | vérifié **en décompressant l'archive**, pas en lisant ce que le script affiche : 76 841 et 28 981 lignes dedans |
| ✅ **0.2** | ~~**Écrire la règle : le miroir ne se supprime jamais**~~ **FAITE le 22/08** — règle 5 du plan + en tête de `backup_critical.py` | formulation corrigée sur objection de Frédéric : **une mise à jour n'a jamais besoin d'une suppression**, elle écrase en place |
| ⏳ **0.3** | **Finir 19-R1** — le rattrapage acquéreurs, ≈ 4 h 35 | à cocher quand le journal rend `termine OK` |
| ✅ **0.4** | ~~**Fermer l'accès public à `app_dossiers_current`**~~ **FAIT le 24/08** — 13 210 annonces, 10 510 adresses privées et 12 488 noms de mandants cessent d'être lisibles avec la clé publique | **c'était pire que la lecture** : `anon` avait aussi INSERT, UPDATE, DELETE et TRUNCATE. `revoke all`, pas `revoke select`. Vérifié : HTTP 401 |
| ✅ **0.5** | ~~**Fermer les 5 vues de surveillance et `app_search_count_high_water`**~~ **FAIT le 24/08** — `anon` **et** `authenticated` retirés, RLS activée sur la table | n'importe qui pouvait **effacer** cette table : aucune RLS et TRUNCATE accordé. Le trou était de moi |
| ✅ **0.6** | ~~**Supprimer `tmp_etape12_avant`**~~ **FAIT le 24/08** | |
| ✅ **0.7** | ~~**Auditer les fonctions appelables sans être connecté**~~ **FAIT le 24/08** — **85 SECURITY DEFINER, 81 ouvertes à la clé publique. 33 vérifient leur appelant, 48 non** | **la bonne nouvelle** : les 33 qui vérifient sont exactement celles qui font des dégâts — **toutes** les `app_console_create_*_job` *(supprimer une annonce, un contact, une recherche)*. Un visiteur ne pouvait pas déclencher de suppression |
| | **12 fonctions de maintenance fermées** — balayages, recalculs, mises en file, alertes, `claim_next_job` | un visiteur pouvait appeler `app_bulk_recompute_chunk` en boucle et **charger l'instance à volonté** — ce qui l'a fait redémarrer le 21/08, mais involontairement. Vérifié : 401 à la clé publique, le worker passe toujours, **0 échec cron**, 21 sondes OK |
| ⚠ | **DETTE ASSUMÉE** — 36 fonctions sans contrôle interne restent appelables sans être connecté | ce sont surtout des **lectures** que le front appelle. Les caractériser demande de lire 36 corps de fonction. **Connu, pas ignoré** |
| ✅ **0.8** | ~~**Le correctif d'une ligne, sur les trois fonctions**~~ **FAIT le 24/08** — `and p.conflict = false` ajouté à la suppression qui annulait la protection | **prouvé par un essai contrôlé** : une ligne en conflit **survit** désormais au passage de la mise en file, une ligne sans conflit est toujours nettoyée. Motif vérifié et non deviné — la migration lève une exception si elle ne trouve pas, si elle s'applique deux fois, ou si le compte n'est pas 3 |
| | **QUAND LE FAIRE : MAINTENANT, et précisément parce que rien n'est en jeu** | **0 ligne en attente, 0 en conflit sur les trois tables aujourd'hui.** Le rayon d'action est donc **nul**. Attendre l'étape 2, ce serait poser le correctif au moment où les négociateurs en dépendent — l'inverse de la prudence. Et d'ici là on aura des **semaines de preuve** que rien ne s'accumule |
| | **Ce qu'il faut surveiller ensuite** — le nombre de lignes en conflit sur les trois tables | il était fatalement à zéro *(elles étaient effacées)*. S'il monte, **c'est une information, pas une panne** : ce sont des saisies qu'on perdait sans le savoir. La règle des 24 h borne l'accumulation — **rien ne peut geler indéfiniment** |

---

### BLOC A — OUVRIR LES DOSSIERS LONGS · *cette semaine, en parallèle de tout le reste*

> **La correction d'ordonnancement la plus importante du plan.** Ces deux dossiers étaient rangés
> en 29 et 30, à la toute fin. Or leur délai **ne dépend pas de nous**. Les commencer après vingt
> tâches techniques, c'est ajouter leur durée *après* tout le reste. Ouverts maintenant, ils se
> déroulent pendant qu'on code.

| | Tâche | |
|---|---|---|
| ⏳ **A.1** | **Portails** — engager la sortie en nom propre, et la reprise des ~350 annonces en ligne *(ex-29)* | délai non maîtrisé. La partie commerciale peut démarrer tout de suite ; le flux de diffusion se construit en parallèle |
| ⏳ **A.2** | **Signature** — ton propre contrat *(ex-30, Yousign)* | ImmoSign appartient à l'abonnement Hektor : le jeton est lu dans une iframe. À la coupure, la signature s'arrête |
| ⏳ **A.3** | **Registre de mandats en propre** *(ex-31)* | obligation légale ; aujourd'hui adossé à Hektor |

**Tant que A.1 et A.2 ne sont pas faits, on ne peut pas couper** — même si toutes les données
étaient déjà chez toi.

---

### BLOC B — LE SERVEUR APPREND DE L'APP · *le morceau qui manquait*

> **Ce bloc n'existait pas dans le plan.** L'audit du 21/08 a montré que **rien ne remonte
> jamais** de Supabase vers le serveur : sur les 11 scripts qui touchent les deux, aucun n'écrit
> une valeur venue de Supabase dans une table locale. Le plan supposait cette moitié acquise.

| | Tâche | Risque |
|---|---|---|
| ✅ **B.1** | ~~**La descente de ce que Hektor ignore**~~ **FAITE le 22/08** — `phase2/sync/pull_from_supabase.py` — **110 tables, 1 337 162 lignes**, 0 en échec. La base locale passe de 2,26 à 3,76 Go | **le serveur apprend de Supabase pour la première fois.** Rapprochements, documents, registre de mandats, DVF, estimations, notifications : tout cela n'existait qu'en ligne, sans aucune copie ni sauvegarde |
| | **Ce qui a été construit** — découverte des tables par la spec OpenAPI *(aucune liste à tenir, donc rien à oublier)* · garde-fou : le script refuse d'écrire dans une table qu'il n'a pas créée *(les 10 exclues sont les bonnes)* · `SupabaseReader` n'a qu'une méthode `get` : **il ne peut pas écrire en ligne** | |
| | **Les trois freins**, posés après l'incident — **copier puis renommer** avec comptage avant bascule · **frein** entre les requêtes et tables triées légère→lourde · **verrou** contre deux descentes simultanées | ils ont servi dès le premier run réel : une copie amputée de 4 lignes a été **refusée** avant de remplacer la bonne |
| | ⚠ **INCIDENT du 21 au 22/08** — deux descentes lancées en une heure, ~2 800 requêtes sans frein : l'API de données a rendu HTTP 522 pendant ~20 min et l'instance a redémarré. Nuit, personne au travail, **aucune donnée perdue**. Compte rendu complet dans `AUDIT_DATA_LOCALE_ET_SYNCHRO_2026-08-21.md` | la même leçon que le rattrapage des documents chez Hektor, que je n'avais pas transposée |
| ✅ **B.2** | ~~**La descente des fiches, en doublure**~~ **FAITE le 22/08** — **10 doublures, 174 720 lignes**. Total : **120 tables, 1 511 882 lignes**, base locale à 3,90 Go | **aucun arbitrage** : la table dérivée garde la version Hektor, la doublure `__sb` porte celle de l'app. Elles cohabitent, personne ne tranche |
| | **La règle n'a plus d'exception** — *un nom qui se heurte →* `<nom>__sb`, toujours. L'ancienne « le nom existe en local → on ne touche pas » m'obligeait à juger qui était le maître, **et je me suis trompé 2 fois sur 10** | découvert sur demande de vérification de Frédéric |
| | ⚠ **Ce que cette vérification a trouvé** — `app_diffusion_request` (**9**) et `app_diffusion_request_event` (**29**) sont créées par le **front seul** ; la table locale du même nom est une **coquille vide**. Mon garde-fou les prenait pour des tables natives et les laissait **sans aucune copie locale**. Et `app_diffusion_target` (42 local / 13 en ligne) est **deux vies parallèles** : le local écrit par un script **manuel**, absent du run de nuit ; l'en-ligne par le front | |
| | **L'annonce était déjà faite par B.1** — `app_dossier_current` et `app_dossier_detail_current` n'entraient pas en collision de nom, donc elles étaient déjà descendues, à côté de `app_view_generale`. B.2 se réduisait au contact | |
| | **Vérifié en 14 contrôles** — intégrité SQLite · les 14 tables natives **inchangées à la ligne près** · 0 résidu · 0 copie en cours · 0 script du projet ne lit ou n'écrit une table descendue · reconstruction d'un contact en 5 s · sauvegarde et 20 sentinelles inchangées · **et le CONTENU comparé valeur par valeur** : 225 + 550 valeurs relues chez Supabase, **0 écart** | les comptes ne prouvent pas le contenu |
| ⏳ **B.3** | **Le déclencheur** — le worker appelle la descente pour la fiche qu'il vient de traiter *(idée de Frédéric, 21/08)* | **en attente de ce que dira le journal.** La doublure ne se rafraîchit qu'à la descente : une modification faite à 9 h n'apparaît qu'à 7 h 30 le lendemain. Suffisant pour **observer**, pas pour **arbitrer**. Si la colonne « app seule » reste plate pendant trois semaines, B.3 est inutile ; si elle grimpe, il se justifie **avec un chiffre** |
| | ❗ **LE CRITÈRE NE PEUT PAS BOUGER — corrigé le 26/08.** Le relevé de la descente montre de quoi la colonne « app seule = 45 » est faite : `app_diffusion_request` **9** + `app_diffusion_request_event` **29** + `app_diffusion_target` **7**. **Que des demandes de diffusion** — les seuls objets que Hektor ne connaît pas. Les trois essais du 25/08 *(un contact modifié, un contact créé, un mandant créé et rattaché)* **ne l'ont pas bougée d'un point**, et c'est normal : tout est passé par Hektor et en est revenu | |
| | ➡ **Donc attendre trois semaines ne prouverait rien.** Cette colonne ne montera que le jour où l'app possédera des objets que Hektor ignore — c'est-à-dire **après 26bis et C.9**. **La décision sur B.3 dépend de 26bis, pas du calendrier** | |
| ✅ **B.4** | ~~**Le serveur dit-il la même chose que Supabase ?**~~ **FAITE le 22/08** — `phase2/checks/comparer_doublures.py` + `app_doublure_journal` + **2 sondes** (`data.doublure_journal`, `data.recherche_divergente`) | **un journal, pas une alarme globale.** Un seuil sur « les deux diffèrent » sonnerait toujours pour rien : Supabase ne porte qu'un sous-ensemble. Une sentinelle qui sonne toujours ne protège de rien |
| | **Premier relevé** — `app_affaire_ledger__sb` 28 981 d'accord, **0 écart** · `app_diffusion_target__sb` **6 / 36 / 7** *(les deux vies parallèles, enfin chiffrées)* · **45 lignes** connues de l'app SEULE | |
| | **L'alarme est étroite et elle a du sens** — les recherches présentes **des deux côtés** dont les critères diffèrent. Une seule ligne = un négociateur a affiné une recherche que Hektor n'a jamais reçue. **0 sur 10 762** | **entendue sonner** : `prix_max` modifié dans la doublure → CRITICAL 1 ; restauré → OK 0 |
| ✅ **B.5** | ~~**La tâche planifiée**~~ **FAITE le 22/08** — `GTI Descente`, **07:30**, descente puis relevé. S4U, limite 2 h, rattrapage si manquée | après le run de 05:30 *(qui pousse la journée)* et après la sauvegarde de 07:00 *(qui fait l'instantané)*. **Les 6 tâches GTI sont désormais en S4U** : elles tournent sans session ouverte |

**B.1 a rendu un service double.** Ce million de lignes n'avait **aucune copie ni sauvegarde
hors de Supabase**. Il est desormais dans `phase2.sqlite`, donc couvert par l'instantane
**hebdomadaire** (niveau 2 de `backup_critical.py`).

> **A trancher plus tard** : `phase2.sqlite` passe de 2,26 a **3,76 Go**, donc l'instantane
> hebdomadaire grossit d'autant. Et le rafraichissement des vues du run de 05:30 est passe de
> **37 a 56 secondes** -- mesure sur le run du 22/08. Modeste, mais reel : a surveiller si la
> base continue de grandir.

### Les trois incidents du 21-22/08, et le garde-fou que chacun a produit

Aucune donnée perdue dans les trois cas. Mais chacun a révélé un manque, et c'est ce qui rend
le bloc B solide aujourd'hui — pas la relecture du code.

| Incident | Cause | Ce qu'il a produit |
|---|---|---|
| **Supabase saturée jusqu'au redémarrage** | 2 descentes lancées en 1 h, ~2 800 requêtes sans frein | le **frein** entre requêtes, les tables **légères d'abord**, et le **verrou** |
| **Le rattrapage de l'autre session tué** à 7 500 | mes écritures concurrentes dans `phase2.sqlite` — les `CREATE INDEX` du relevé, hors verrou | `busy_timeout` **30 s** *(autre session)* + le **verrou étendu aux deux étapes** |
| **Un verrou désarmé sur un run vivant** | `Stop-ScheduledTask` tue le PowerShell parent, **pas le python enfant** : il devient orphelin et va au bout. J'ai retiré un verrou qui protégeait un run en cours | le verrou **vérifie que son processus est vivant** *(OpenProcess, jamais `os.kill` sous Windows — il tuerait le processus)* |

**Trois défauts trouvés en testant, pas en relisant** : la copie tronquée prise pour une fin de
table *(elle remplaçait la bonne, en silence)*, le `--dry-run` du relevé qui écrivait quand même
*(il pose les index)*, et la comparaison sans index qui tournait **dix minutes** au lieu de 26 s.

> **Deux leçons de méthode, valables au-delà de ce bloc :**
> **① Arrêter la tâche planifiée n'arrête pas le travail.** Pour couper, il faut tuer le python.
> **② Un message d'erreur qui accuse le mauvais coupable coûte une heure.** Le coupe-circuit
> criait « bannissement d'IP » sur une panne locale ; mon verrou disait « une descente tourne »
> quand c'était le relevé. Les deux sont corrigés.

**Pourquoi la descente et pas la double écriture** *(question de Frédéric, tranchée le 21/08)* :
une double livraison ne couvre que ce qui passe par un worker — **5 % des lignes** — elle exige
que chaque fonction future **pense** à s'y brancher, et elle place le risque **dans le chemin
d'écriture du négociateur**. La descente couvre tout, ne demande rien à l'app, et si elle échoue
personne n'est bloqué. Et surtout : après la coupure, l'app écrira toujours dans Supabase — **le
serveur devra de toute façon apprendre de Supabase.** La descente n'est pas une rustine, c'est la
moitié manquante de l'architecture finale.

---

### BLOC C — L'APP DEVIENT L'AUTEUR · *réduit le 24/08 par la stratégie en trois étapes*

> **Quatre morceaux ont été supprimés** et le plus gros divisé par deux. Ce n'est pas un
> renoncement : l'interdiction d'ouvrir Hektor à l'étape 2 les rend **sans objet**.

#### À FAIRE AVANT L'ÉTAPE 2 — *pendant que les négociateurs sont encore dans Hektor*

| | Tâche | Durée | Pourquoi maintenant |
|---|---|---|---|
| ✅ **C.3** | ~~**Fermer la porte sortante des recherches**~~ **FAIT le 24/08** — `push_search` devient `null` dans les **deux** fonctions d'édition *(négociateur **et** espace client)*. La ligne d'attente devient un **registre** : elle survit, elle protège, elle ne part jamais | **le mécanisme le prévoyait déjà** — la boucle d'enfilage exige `push_search is not null`, et aucune suppression n'atteint une telle ligne. Pas de table neuve, pas de cron touché. **Vérifié** : survit à 2 passages, 0 travail créé |
| | **L'alarme a été adaptée en même temps** — les recherches du registre sortent de `data.recherche_divergente` | sans quoi elle passerait en CRITICAL dès le premier affinage, **alors que la divergence est désormais voulue**. Une sentinelle qui sonne quand tout va bien cesse d'être lue |
| ⚠ | **Ce que ça change pour tes clients** — un acquéreur qui affine sa recherche dans son espace croira peut-être que son négociateur la verra dans Hektor. **Ce n'est plus le cas** | 28 envois en 90 jours : l'effet est nul aujourd'hui, il compte pour l'étape 2 |
| ✅ **C.1'** | ~~**« UNE SAISIE NE SE PERD JAMAIS »**~~ **FAIT le 24/08** — la purge des 24 h retirée des 3 fonctions · la sortie de conflit *(`app_pending_resolution` + `app_annonce_pending_resolve`)* · les 3 marqueurs du worker cessent d'avaler leur échec · 4 sondes ajoutées · le bandeau distingue les deux causes et permet de clore | **FAIT** | **Deux des trois gestes existaient déjà** — la saisie était gardée, et la reprise était écrite *(5 tentatives, délai croissant)*. Le défaut réel tenait en **une ligne** : la purge des 24 h. **L'avertissement avait une durée de vie d'un jour**, et n'était visible que de qui rouvrait cette fiche précise |
| ✅ **C.2a** | **Identité des contacts — la relecture** — `RELECTURE_IDENTITE_CONTACTS_2026-08-24` | **FAIT le 24/08** | **Le verrou du 20/08 est levé** : un seul fabricant de nom de recherche, local, et il consulte le registre — **0 fonction Supabase sur 27 n'en fabrique**. Ajouter une colonne ne peut plus déplacer une clé. Et le périmètre est plus petit qu'annoncé : **4 tables sur 18 portent 95 % des 202 404 lignes**, 6 sont vides |

> ⚠ **Ce que ça change pour la surveillance** : la sonde ne mesure plus une perte déjà
> consommée, mais **du travail en attente de décision**. Elle reste rouge tant qu'un humain
> n'a pas tranché — c'est voulu, c'est l'objet même de la tâche.
>
> ℹ **Reste ouvert, et ça porte un numéro : C.12** — **les contacts seulement**. Les
> recherches n'en ont pas besoin : **C.3 a fermé la porte**, elles ne peuvent plus produire
> de conflit *(vérifié)*. Les annonces ont leur bouton depuis C.1'.
> *Écrit d'abord ici en simple commentaire, ça se serait perdu — et j'avais dit « contact ET
> recherche ». Frédéric a relevé les deux le jour même : une chose qui n'est pas une TÂCHE
> n'existe pas, et un périmètre qu'on n'a pas mesuré est toujours trop large.*

#### C.1' — la règle qui remplace l'arbitrage

Trois gestes, et **aucun n'est de l'arbitrage** :

| | |
|---|---|
| **a** | Une saisie dont l'envoi a échoué **n'est jamais écrasée** par le run. Aujourd'hui la protection est une ligne **temporaire** qui disparaît ; elle doit devenir **durable** |
| **b** | L'échec est **visible**. Aujourd'hui le travail est marqué `done` et personne ne sait |
| **c** | Et il **se reprend**. Aujourd'hui il ne repart jamais |

> C'est le patron qui a déjà marché **trois fois** dans ce projet : `app_dossier` qui marque
> `absent_depuis` au lieu de supprimer, `app_affaire_ledger` en *delete-never*,
> `app_search_registry` qui survit à la reconstruction.
> **Ne jamais laisser le passager effacer le durable.**

#### À CONSTRUIRE MAINTENANT, DORMANT — *(ex-« pendant l'étape 2 », corrigé le 24/08)*

*Aucune de ces tâches n'attend que les négociateurs bougent. Chacune se construit et se livre
**éteinte** ; seul son **interrupteur** attend — voir le tableau plus bas.*

| | Tâche | Durée |
|---|---|---|
| ✅ **C.2b** | ~~**Identité des contacts — le code**~~ **FAIT le 25/08** — `app_contact` locale (355 687 numéros, patron d'`app_dossier`) · `app_contact_id` sur **19 tables** Supabase · **144 985 lignes remplies** · sonde · branché dans le run de nuit | **FAIT** | **0 incohérence** : aucune ligne ne porte un numéro différent de sa fiche contact, et **0 numéro ne sert à deux contacts**. La clé primaire n'est **pas** touchée, et **personne ne lit encore la colonne** — c'est une doublure |
| | ⚠ **Ce que le chantier a révélé, absent du plan** : *le registre doit se **maintenir**, pas seulement se créer*. Le jour même, **15 contacts créés la veille** étaient déjà dans Supabase et pas encore en local. Le script est devenu incrémental et tourne chaque nuit | |
| | ℹ **35 vrais orphelins** trouvés dans `app_search_count_high_water` — des compteurs qui pointent un contact qui n'existe plus. **Exactement ce que C.2a annonçait** : sans clé étrangère, les orphelins existent sans que rien ne le signale. *Signalé, pas corrigé* | |
| ✅ **C.12** | ~~**La sortie de conflit — contacts**~~ **FAIT le 25/08** — `app_contact_edit_status` + `app_contact_pending_resolve` · bandeau à deux causes posé dans **les DEUX versions** de la fiche | **FAIT** | Un défaut trouvé **par l'essai, avant mise en service** : la trace lisait le numéro sur la ligne d'attente, que seule une ligne déjà rattrapée porte. Elle le résout désormais **à la source** |
| | ✅ **Les recherches n'en ont PAS besoin** — *vu par Frédéric, vérifié de bout en bout*. C.3 a fermé la porte : aucun travail créé, aucun `push_job_id`, donc **aucun conflit possible**. Le bouton aurait été mort-né | |
| | ℹ **Nom du paramètre** : `target_hektor_contact_id`, pas `target_contact_id`. Le renommage des 11 fonctions ambiguës reste **rayé**, mais pour des fonctions **neuves** le nom clair ne coûte rien. *On arrête d'en créer des ambiguës* | |
| ✅ **C.6** | ~~**Le domicile de l'annonce**~~ **FAIT le 25/08** — table `app_annonce_champ_app`, clé/valeur, **jamais reconstruite** · branchée en 3/3 de la descente · sous sauvegarde critique | **FAIT** | Le plan annonçait *36 champs calculés à l'export* : c'est **13**, presque tous techniques. Et le paquet de détail est un blob de 134 clés dont **l'app n'en écrit que 7** |
| | ❗ **Le vrai problème n'était pas la conservation mais l'ÉCRITURE** : `view_generale.py` fait `DROP TABLE` puis `CREATE TABLE AS` — une valeur écrite par l'app **ne survivrait pas à 05:30**. Cette table est le seul endroit où elle survit | |
| | ℹ **Résultat mesuré : 0 divergence sur ~581 000 comparaisons.** Mais **quatre faux écarts** ont dû être éliminés d'abord — `NULL` vs `0.0` *(7 143 !)*, entier `0` vs texte `'0'` *(23, piège GLOB)*, la date sentinelle `0000-00-00`, et **un jour de décalage** *(89)*. C'est ce dernier qui dicte le placement : les deux côtés doivent être de la même heure | |
| ⏳ **C.4** | **Les workers — 16, et non 35** *(mesuré : `ETUDE_WORKERS_EXISTANT_ET_FAISABILITE_2026-08-20`)*. Familles B1+B2. Statut + affaire *(le plus riche)* · archiver/désarchiver · créer contact et mandant · **affectation du négociateur EN DERNIER** *(impersonation)* | **7 sur 34 marchent déjà sans Hektor.** Et **3 seulement** en dépendent vraiment — numéro de mandat, relance et annulation de signature — soit **exactement A.1 et A.2** |
| | ❗ **LE MANDAT D'UNE TRANSACTION** *(enquête du 25/08, `NOTE_CHAINE_DES_MANDATS_2026-08-25`)*. **a)** Quand le négociateur changera un statut **depuis l'app**, celle-ci doit **transmettre le numéro de mandat de la fiche** — pas laisser le worker chercher. ⚠ **Et la valeur doit être ENTIÈRE** : Hektor attend `<id>-<FAMILLE>` *(`648-PROTEXA`)*, jamais le numéro seul — c'est ce qui a fait annuler C.5. Tant que Hektor vit, **le worker recopie sa valeur** ; le formulaire n'a rien à envoyer. *La modale actuelle est **réservée aux admins** : `isAdmin ? openStatusChangeModal : undefined`* | |
| | ⚠ **b)** **Si un négociateur crée un nouveau mandat et que la fiche Hektor ne bascule pas tout de suite**, le numéro de la fiche pointerait encore l'**ancien**. Ce n'est pas théorique : le même défaut a été corrigé le 28/07 sur les dates *(VA6482 — numéro neuf + date de fin échue → annonce bloquée en « échu »)* | |
| | ℹ **C.4 n'est PAS l'ouverture des droits** *(corrigé le 25/08)*. Elle rend l'app capable de faire ces gestes **sans Hektor** — c'est un chantier de **coupure**, pas de permission. Les droits sont un sujet à part : **bloc F** | |
| | **C'est ICI que se répondent les 3 arbitrages de A1** — `statut_annonce`/`archive`, `negociateur_email`, les champs de mandat | **pas avant** : la carte de A1 dit « si l'app sait écrire un champ », et **c'est précisément ce que cette tâche change**. Trancher plus tôt serait figer une carte sur un état qui va bouger *(décision de Frédéric, 24/08)* |
| ❌ **C.5** | ~~Registre d'affaires et mandat des transactions~~ — **ANNULÉE le 25/08 au soir, le jour même.** Le worker **recopie de nouveau** la valeur de Hektor. *Le registre d'affaires, lui, reste acquis (tâche 4 du 20/08).* | **RETOUR ARRIÈRE** | **La moitié était déjà faite** : `app_affaire_ledger` porte `app_affaire_id` et `app_dossier_id` depuis le 20/08. Vérifié **avant** de refaire |
| | ❗ **POURQUOI ELLE A ÉTÉ ANNULÉE.** Hektor n'identifie pas un mandat par un nombre : son formulaire attend **`<id>-<FAMILLE>`** — `648-PROTEXA`, `9887-HEKTOR` — parce qu'il tient **deux registres parallèles**. C.5 envoyait `648` : aucune option ne correspond, Hektor range « mandat non renseigné », **sans erreur**. Constaté en vraie grandeur : l'offre **33026** est chez Hektor **sans mandat**, alors que toutes les offres créées depuis septembre 2025 en portent un | |
| | ℹ **Ce qui marchait avant, et pourquoi.** Le worker **recopiait** la valeur de Hektor, lue dans l'`<input>` caché `selectedMandatId`. *(Le plan et l'audit du 20/08 nommaient `id_mandat` : c'est un `<select>`, que `htmlInputValue` ne sait pas lire. Le constat de fond — « le worker dépend du HTML » — était juste ; le champ nommé, non.)* | |
| | ✅ **POURQUOI LE RETOUR ARRIÈRE PLUTÔT QU'UN CORRECTIF** *(arbitrage de Frédéric, 25/08)*. **① Ce worker meurt avec Hektor** — le rendre autonome de Hektor est sans objet. **② Le gain de C.5 était nul, et c'est mesuré** : Hektor pré-sélectionne le mandat courant, et la fiche de l'app désigne le même courant **24 fois sur 24**. **③ Règle du plan** : les workers sont **maintenus, pas refondus** | |
| | 🔎 **Ce qui reste acquis** : la valeur composite, les **deux familles** de registre *(`SIMPLE`/`EXCLUSIF`/`ACCORD` → HEKTOR ; libellé français → PROTEXA, vérifié 10/10)*, et le **livrable A0** de la clôture, jamais produit en juillet. Versé dans **C.13** | |
| ❌ **C.8** | ~~Le **calque** disparaît · la **barrière**~~ **DISSOUTE le 25/08, après mesure** — ses deux moitiés n'étaient pas des tâches | |
| | **2.5, le calque** : `app_edit_annonce_optimistic` **écrit déjà dans la fiche** (`app_dossier_current` + son détail) et garde une photo d'avant dans la file. Le « calque » n'est pas un objet à supprimer : c'est le **statut provisoire** de ce que l'app écrit. Il cesse d'être provisoire **quand le contrat de C.7 cesse d'être vide** — **c'est une bascule d'interrupteur, pas un développement**. Et le faire maintenant, contrat vide, retirerait l'affichage instantané **sans** donner l'autorité à l'app : une régression | |
| | **2.6, la barrière** : **aucun travail n'échoue faute de numéro Hektor** — 456 travaux sans numéro, **0 en erreur**, et ce sont des travaux qui n'en ont pas besoin *(363 rafraîchissements de contact, 26 créations de brouillon)*. Le cas naît avec **C.9** : la barrière y est **fondue** | |
| ⏳ **C.16** | **LES CONTACTS NE SONT JAMAIS REBALAYÉS ENTIÈREMENT — et 611 « contacts » n'existent pas** *(trouvé le 26/08)* | ⚠ **à chiffrer** |
| | ❗ **LE RUN DES CONTACTS EST EN DELTA, PAS EN BALAYAGE.** Contrairement aux annonces *(balayage complet chaque nuit, 2 847 pages)*, les contacts ne sont revus que s'ils ont bougé. **Le listing complet n'a pas été rebalayé depuis mai** : 284 269 contacts ont pour dernière vue `2026-05`. **Conséquence : si Hektor archive ou supprime un contact, nous ne l'apprenons pas** | |
| | ℹ **L'écart mesuré** : Hektor déclare **348 053** contacts *(169 448 actifs + 178 605 archivés)*, notre miroir en a **355 712** — **+7 659** | |
| | ✅ **ESSAI A (26/08), échantillon stratifié de 300 contacts interrogés un par un** : **actifs 120/120 existent — 0 supprimé** · **archivés 117/120, soit 2,5 % absents** *(≈ 4 600 sur 184 100)* · **sans indicateur d'archivage : 0/60, soit 100 % absents** | |
| | 🔴 **LES 611 « SANS INDICATEUR » NE SONT PAS DES CONTACTS SUPPRIMÉS — CE N'EN ONT JAMAIS ÉTÉ.** Leur charge brute est un talon : `raw_json = {"id": "56974"}`. Ce sont des **RÉFÉRENCES ORPHELINES** : une annonce, une offre ou un mandat de Hektor cite un identifiant de contact, nous en gardons le nom et la typologie — et `ContactById` répond **404**. **C'est une incohérence dans les données de Hektor, que le miroir a fidèlement recopiée** | |
| | ℹ **Ce n'est pas de la déduplication** : sur 11 absents testés, **2 seulement** appartiennent à un groupe de doublons — alors que le parc en compte 37 144 groupes / 80 992 membres | |
| | ✅ **Écarté avec preuve** : doublons d'identifiant *(355 712 lignes = 355 712 identifiants distincts, en texte comme en entier)* · périmètre d'agence *(la somme par agence égale exactement le total)* · filtre `type` *(`type=0` rend le total, et les types se chevauchent — un contact peut être propriétaire ET acquéreur)* | |
| | ⚠ **CORRECTION D'UNE ERREUR À MOI** : j'avais expliqué les 7 659 par « des contacts supprimés que nous accumulons, faute de mécanisme de suppression ». **Faux sur deux points** — la règle « on ne supprime jamais » date du **22/08**, elle ne peut pas expliquer un écart antérieur ; et les actifs ne montrent **aucune** suppression. Frédéric a refusé cette explication, il avait raison | |
| ⏳ **C.15** | **LE RUN NE VOIT QU'UN TYPE D'OFFRE SUR SIX — 4 165 ANNONCES N'ENTRENT JAMAIS** *(trouvé le 26/08)* · `sync_raw.py` appelle `ListAnnonces` **sans le paramètre `offre`**, et Hektor rend alors **uniquement les ventes** | 🔴 **LE PLUS GROS TROU CONNU** |
| | ❗ **MESURÉ, PAR TROIS CHEMINS INDÉPENDANTS QUI DONNENT LE MÊME CHIFFRE** : *(a)* GraphQL 61 076 − REST 56 911 = **4 165** · *(b)* somme des totaux par type : 927 actives + 3 238 archivées = **4 165** · *(c)* `hektor_annonce.offre_type` vaut **0 sur les 56 910 lignes, sans exception** — aucune autre n'est jamais entrée | |
| | | **actives · archivées · total** |
| | `0` vente — *tout ce que le run voit aujourd'hui* | 22 424 · 34 487 · **56 911** |
| | `2` location | 621 · 2 248 · 2 869 |
| | `10` vente immo pro | 251 · 782 · 1 033 |
| | `11` location immo pro | 54 · 208 · 262 |
| | `6` neuf · `8` saisonnier | 1 · 0 · 1 |
| | **INVISIBLES** | **927 · 3 238 · 4 165** |
| | ✅ **DÉCISION DE FRÉDÉRIC, 26/08** : le **SERVEUR** reçoit **tous** les types *(61 076)* — il devient réellement le maître. **SUPABASE, LE FRONT ET LES WORKERS** ne reçoivent que **`0` + `10` + `6`** *(57 945, soit +1 034)*. Les locations *(3 131)* restent au serveur et **n'apparaissent pas dans l'app** | |
| | ❗ **ET LES QUATRE INDEX SUPABASE — point relevé par Frédéric, 26/08.** Ce n'est pas « un seau » : les quatre index sont **tous dérivés de `app_view_generale`**, donc **ajouter les types au serveur les ferait partir automatiquement vers Supabase**, locations comprises | |
| | | **la carte du routage** |
| | `app_dossier_current` *(actives)* — `ANNONCES_SCOPE_WHERE` | `archive='0'` ET statut ∈ (`Actif`, `Sous offre`, `Sous compromis`, `Estimation`) |
| | `app_archive_annonce_index_current` | `archive='1'` |
| | `app_historical_annonce_index_current` | `archive='0'` ET statut ∈ (`Vendu`, `Clos`) |
| | `app_brouillon_annonce_index_current` | `archive='0'` ET id ∈ brouillons *(`hektor_annonce_draft_state`)* |
| | ✅ **LA COLONNE EXISTE DÉJÀ** : `app_view_generale.offre_type` vient de `ann.offre_type` *(`view_generale.py:273`)* et vaut **`0` sur les 56 910 lignes**. Le filtre `offre_type IN ('0','10','6')` peut donc être posé **sans rien ajouter à la vue** | |
| | 🔑 **D'OÙ L'ORDRE À RESPECTER, ET IL EST GRATUIT** : poser le filtre **AVANT** d'ouvrir le run. Aujourd'hui `offre_type` vaut 0 partout, donc **le filtre est totalement inerte** — il ne change pas une ligne. Une fois posé, on ouvre le robinet : **il n'existe alors aucun instant où une location peut fuir vers Supabase**. Faire l'inverse, c'est publier 3 131 locations puis courir après | |
| | ⚠ `ANNONCES_SCOPE_WHERE` sert **aussi aux compteurs** *(total_dossiers, total_sans_mandat, total_bloques, total_valides_diffusion…)* : le filtre s'y applique donc d'un seul geste, mais il faut vérifier que c'est bien voulu partout | |
| | ⚠ **PIÈGE À NE PAS RATER** : `reconcile_active_annonce_scope` calcule `known_ids − active_annonce_ids` et **SUPPRIME** la différence *(état, liens contacts, détail brut)*. Si le balayage couvre les six types mais que la réconciliation compare à un seul, **elle effacera les 4 165 à chaque run**. La réconciliation doit être **scopée par type d'offre** | |
| | ✅ **LA SÉQUENCE, EN QUATRE TEMPS — arrêtée avec Frédéric le 26/08. Ne pas intervertir.** | |
| | ✅ **①-a FAIT le 26/08 — LA RÉCONCILIATION TRACE CE QU'ELLE SUPPRIME.** Elle renvoyait déjà la liste des annonces effacées, **et l'appelant l'ignorait** : aucun journal, aucun compteur — **personne ne pouvait dire combien d'annonces disparaissaient chaque nuit, ni lesquelles**. C'est ce silence qui a laissé vivre le défaut. Désormais : table `sync_annonce_scope_purge_log` *(miroir)* + deux lignes au journal du run. **Comportement strictement inchangé**, éprouvé sur banc isolé — **7 attendus sur 7** *(mêmes lignes supprimées, variante `archived` intacte, retour identique, trace écrite, second passage sans effet)* | |
| | ✅ **①-a bis FAIT le 26/08 — DEUX REFUS, ET UN DANGER FERMÉ.** Avec `--max-pages`, le balayage s'arrête tôt et `active_annonce_ids` ne contient qu'une poignée d'annonces : la comparaison portait alors sur presque tout le parc. **Une simple commande de test aurait effacé l'état, les liens contacts et le détail brut de ~22 300 annonces, en silence.** Désormais : refus si le balayage est partiel *(`--max-pages`)*, et refus si le listing rend moins de **50 %** de ce qu'on connaît *(incident Hektor en cours de balayage)* | |
| | ℹ **Le run de nuit ne passe jamais `--max-pages`** *(défaut 0 = sans limite)* : son comportement est **strictement inchangé**. Éprouvé sur banc isolé — balayage partiel → 0 suppression · balayage tronqué → 0 suppression · balayage normal → mêmes 3 suppressions qu'avant, trace écrite | |
| | ⏳ **①-b — à décider APRÈS avoir le chiffre** : vérifier chaque disparition par un appel `AnnonceById` avant d'effacer, et distinguer « archivée » *(légitime)* de « disparue ». **Sans le volume réel, tout correctif serait posé à l'aveugle** — trois par nuit ne se traite pas comme trois cents | |
| | **① Scoper la réconciliation par type d'offre** — `reconcile_active_annonce_scope` compare `known_ids` au balayage. Tant qu'elle compare six types à un seul balayage, **elle efface les 4 165 à chaque run**. *Vérif : provoquer un balayage partiel et constater **0 suppression**.* | **le préalable absolu** |
| | ✅ **② FAIT le 26/08 — LE FILTRE EST POSÉ, ET IL EST INERTE.** `FILTRE_OFFRE_APP` défini **une seule fois** dans `export_app_payload.py`, appliqué aux **quatre** points : `ANNONCES_SCOPE_WHERE` *(actives + tous les compteurs)* et les trois index *(archives, historiques, brouillons)*, par un marqueur `__FILTRE_OFFRE_APP__` substitué après la définition des requêtes | |
| | ✅ **L'INERTIE EST VÉRIFIÉE, attendu écrit avant** : actives **13 575 → 13 575** · archives **34 487 → 34 487** · historiques **8 800 → 8 800** · brouillons **0 → 0**. Et sur les **56 913** lignes de `app_view_generale`, le filtre en retient **56 913** — **0 exclue**. Il ne peut rien casser aujourd'hui | |
| | ⚠ **Un raté rattrapé en chemin** : j'avais laissé le marqueur `__FILTRE_OFFRE_APP__` dans les trois requêtes **sans rien pour le remplacer** — le SQL aurait été invalide au premier appel. Vu et corrigé avant tout commit, mais c'est exactement le genre d'oubli que seule la vérification attrape | |
| | **② Poser le filtre `offre_type IN ('0','10','6')`** sur les 4 index **et** sur `ANNONCES_SCOPE_WHERE` *(qui sert aussi aux compteurs)*. **Inerte aujourd'hui** : tout vaut 0. *Vérif : après application, les comptes Supabase doivent être **identiques au caractère près** — c'est la preuve de l'inertie.* | gratuit, zéro risque |
| | ✅ **③ FAIT le 26/08 — LA PHOTO D'AVANT EST PRISE, et c'est un outil, pas un relevé.** `phase2/checks/photo_avant_c15.py` : **lecture seule**, il mesure les trois supports d'un coup *(miroir, serveur, Supabase)*, l'enregistre, et **compare automatiquement à la photo précédente** en affichant les écarts. Il se rejoue après chaque palier d'ouverture | |
| | | **les repères du 26/08, avant toute ouverture** |
| | miroir | annonces **56 910** *(offre_type = 0 sur 100 %)* · mandats **24 130** · offres **10 992** · compromis **10 455** · ventes **7 537** · contacts **355 712** |
| | serveur | `app_dossier` **56 913** · `app_view_generale` **56 913** · `app_contact` **355 712** · ledger **28 984** · recherches **76 899** |
| | index | actives **13 575** · archives **34 487** · historiques **8 800** |
| | registre | avec mandat **23 854** · sans mandat **33 059** |
| | statuts | Clos 33 989 · Estimation 12 718 · Vendu 9 095 · Actif 923 · Sous compromis 94 · Sous offre 41 |
| | Supabase | `app_dossier_current` **13 210** · archives **34 487** · historiques **8 800** · brouillons **412** · registre mandats **23 817** · contacts **57 559** |
| | **③ Mesurer l'aval AVANT d'ouvrir** — relever les compteurs de `app_view_generale`, du registre des mandats, des rapprochements et des statistiques. **Tous ont été calculés jusqu'ici sur un parc amputé** ; sans photo d'avant, on ne saura pas distinguer un effet voulu d'une régression. | la photo d'avant |
| | **④ Ouvrir le run, un type à la fois** — commencer par **`offre=6` : UNE seule annonce**, le canari parfait. Puis `10` *(1 033)*, puis `2` et `11` *(serveur seul, 3 131)*. Surveiller le **frein de débit** à chaque palier : notre IP a déjà été bannie une fois. | progressif |
| | ℹ **Ce que ça explique** : les 3 annonces cherchées par Frédéric *(62815, 62823, 62825)* sont des **ventes immo pro**. Elles ne sont pas « tombées » du miroir — elles n'auraient jamais dû y entrer, et n'y sont entrées que par le canal brouillon avant d'être effacées par cette même réconciliation | |
| | ⚠ **À VÉRIFIER AVANT DE CODER** : le volume de détails à rapatrier au premier run *(+927 `AnnonceById` actives)* et le **frein de débit** *(notre IP a déjà été bannie une fois)* · l'effet sur `app_view_generale`, le registre, les rapprochements et les statistiques, **tous calculés jusqu'ici sur un parc amputé** · le sort d'un contact rattaché à une location, absente de Supabase | |
| | ❗ **QUATRE AUTRES ÉCARTS, RELEVÉS LE 26/08 SUR TOUS LES ENDPOINTS DU RUN** — Frédéric : *« as-tu vérifié entièrement mon projet ? »*. Non, je ne l'avais pas fait. Le contrôle complet donne : **mandats +2 279** *(Hektor 26 409 / miroir 24 130)* · **ventes +1 674** *(9 211 / 7 537)* · **offres +116** · **compromis +116** *(le même chiffre des deux côtés — cause commune probable)* | |
| | ➡ **Hypothèse à remesurer APRÈS C.15** : ce sont vraisemblablement les mandats et les ventes des **4 165 annonces absentes** — le mandat arrive par le détail de l'annonce *(`AnnonceById.mandats`)*, donc une annonce absente emporte son mandat. Si les écarts se referment après correction, l'hypothèse était bonne. **Un mandat manquant sur un registre légal n'est pas une nuance d'affichage** | |
| | ℹ **L'agence 20 « Gestion site »** est déclarée par Hektor et **absente de notre miroir** *(nous en avons 19 sur 20)*. Petit, mais net | |
| | ✅ **Écarté avec preuve, sur les annonces** : ce n'est **pas** un problème de périmètre d'agence — la somme par agence égale exactement le total. Le seul filtre en cause est `offre` | |
| | 📌 **Comment ça a été trouvé** : Frédéric a refusé deux fois ma conclusion *(« c'est impossible »)*. La réponse était dans **`notice/Hektor API v2 - Documentation`**, que je n'avais pas ouverte : *« `offre` : 0 vente, 2 location, 6 neuf, 8 saisonnier, 10 vente immo pro, 11 location immo pro »*. J'avais sondé `offredem` — le nom du champ **dans la réponse** — au lieu de `offre`, le paramètre de la **requête**. Même piège que `mandat` / `id_mandat` le matin même | |
| ⏳ **26bis** | **DONNER UN CORPS À L'ANNONCE CÔTÉ SERVEUR** — *décrite depuis le 21/08 dans « LE TROU DE STOCKAGE », **sans jamais avoir de numéro de tâche**. Numérotée le 25/08 pour qu'elle cesse d'être invisible* · **(1)** ✅ **FAITE le 26/08** · **(2)** observer *(en cours)* · **(3)** basculer, collée à C.9 | ⚡ |
| | ✅ **26bis-(1)** — `phase2/identite/annonces_app_seule.py` · table `app_annonce_app_seule` *(accumule, `absent_depuis`, jamais de suppression)* · **branchée dans le run après le contrat d'autorité** · **sous sauvegarde critique**. Relit Supabase **en direct et paginé** *(la copie locale a 22 h de retard à 05:30 — même raison que C.7 ; et PostgREST plafonne à 1 000 lignes : 13 210 annonces lues, pas 1 000)* | |
| | ℹ **SEUL `--recenser` EST BRANCHÉ, PAS `--injecter`.** Poser ces lignes dans `app_view_generale` changerait ce que le push envoie vers Supabase, avec **84 colonnes vides sur 130** : c'est l'étape (3), elle se décide champ par champ. **Ici on observe** | |
| | ✅ **Éprouvé** : essai contrôlé avec une annonce fabriquée n'existant que côté app → **posée dans `app_view_generale` avec `hektor_annonce_id` VIDE** *(tout l'objet)* · deuxième injection → **0 doublon** · nettoyage complet. Et **aujourd'hui : 0 annonce dans ce cas**, l'étape est donc inerte | |
| | ❗ **La seule tâche du plan qui devient IMPOSSIBLE si on la remet à plus tard** : le remplissage initial vient du miroir, donc il exige que **Hektor vive encore**. Mesure du 25/08 : `app_dossier` = **56 899 lignes mais 10 colonnes** *(identité pure)*, `app_annonce_champ_app` = **0 ligne**. Le contact et la recherche, eux, ont leur corps *(355 687 et 76 889 lignes)* | |
| | ⚠ **ORDRE IMPÉRATIF** : *« la création app-first écrit dans Supabase. **Sans 26bis, une annonce créée dans l'app n'existe QUE là.** Ce serait creuser le trou pendant qu'on le rebouche. »* Et **l'interrupteur `CHAMPS_APP_ANNONCE` ne peut s'allumer qu'après** — sans corps local, une valeur écrite par l'app n'a nulle part où survivre | |
| | ❌ **CONSTAT DU 26/08 MATIN — RETIRÉ LE MÊME JOUR, IL ÉTAIT FAUX.** J'avais écrit que le lien bien ↔ mandant n'existait que dans le miroir. **C'est faux** : il vit dans `app_contact_relation_current` — **165 474 lignes sur le serveur, 77 376 dans Supabase** — avec `hektor_annonce_id` **et** `app_dossier_id`, le rôle, le numéro de mandat. Vérifié sur notre mandant d'essai : contact 605030 · annonce 62774 · `app_dossier_id` 3828957 · rôle `mandant` | |
| | ⚠ **L'ERREUR DE MÉTHODE, à ne pas refaire** : j'ai conclu à une absence après **trois recherches par nom** (`sync_annonce_contact_link`, `app_annonce_contact_link`, `app_contact_annonce_link`) au lieu de faire l'inventaire des tables. **Une recherche qui échoue ne prouve pas une absence** | |
| | ✅ **CE QUE L'INVENTAIRE A ÉTABLI, LUI** — et le trou en sort **plus précis** : le contact possède **tout** *(`app_contact` identité · `app_contact_current` corps 34 col · `app_contact_relation_current` liens — tous en `CREATE IF NOT EXISTS` + upsert)*. L'annonce possède son identité *(`app_dossier`)* mais **PAS son corps** : `app_view_generale` est en **`DROP TABLE` + `CREATE TABLE AS` inconditionnel, chaque nuit, depuis le miroir** | |
| | ❌ **ET CETTE PHRASE-LÀ AUSSI ÉTAIT FAUSSE — retirée le 26/08.** J'avais écrit que le `DROP` de 05:30 effacerait les 56 913 lignes. **Non** : le miroir **GÈLE, il ne disparaît pas** *(c'est écrit dans l'en-tête de C.6)*. Le fichier reste, la reconstruction reproduit le même contenu. Les annonces existantes gardent leur corps, figé | |
| | ✅ **LE TROU RÉEL, ENFIN CERNÉ.** La machinerie est déjà complète pour les annonces EXISTANTES : le miroir gelé les redonne, et `appliquer_contrat.py` (C.7) **ré-applique chaque nuit ce que l'app détient**, relu dans Supabase. Il ne manque que l'interrupteur `CHAMPS_APP_ANNONCE`. **Ce qui manque vraiment, c'est autre chose** : une annonce **NÉE DANS L'APP** n'a aucune ligne dans le miroir → aucune ligne dans `app_view_generale` → **le serveur ne la connaît pas du tout**. Et C.7 ne sait que *mettre à jour* des lignes existantes, pas en *créer* | |
| | ➡ **Donc 26bis n'est pas « donner un corps à l'annonce »** *(elle en a un)* **mais « rendre le serveur capable de tenir une annonce que le miroir ignore »**. C'est exactement ce que le plan disait depuis le 21/08 : *« sans 26bis, une annonce créée dans l'app n'existe QUE dans Supabase »*. Plus petit, plus net — et toujours à faire avant C.9 | |
| ⏳ **C.9** | La **création** part de l'app *(ex-23,24,25)* | **1 à 2 sem.** — après C.7 |
| | ℹ *Le patron « naître sans numéro Hektor » est **déjà dans le schéma** — `app_dossier.id` autoincrement + `hektor_annonce_id` **nullable** + UNIQUE. Il n'a jamais servi (0 ligne sur 56 894) : la création optimiste est derrière un drapeau éteint. C'est ici qu'il s'exerce pour la première fois* | |
| ⏳ **C.13** | **LA CLÔTURE DE MANDAT DANS L'APP** — *cadrage **déjà validé** le 30/07, dev non commencé* · `PLAN_DEV_MANDAT_CLOTURE.md` · drapeau `VITE_APP_MANDAT_CLOTURE_ENABLED` (éteint) | **à chiffrer** |
| | ❗ **ENQUÊTE DU 25/08 — le cadrage était incomplet, et sa portée est de 91 %.** Le formulaire de clôture a **deux visages** : avec plusieurs mandats il affiche un `<select>` ; **avec un seul, AUCUNE option** — tout est dans un `<input>` caché `selectedMandatId` *(valeur **et** attribut `data`)*. Le worker ne sait lire que des `<option>` : il **refuse de clôturer** sur **694 annonces actives sur 759**. Et sur les **98 clôtures réelles du parc, 74 portent sur une annonce à mandat unique** | |
| | ℹ **Pourquoi personne ne l'a vu** : tout le cadrage du 30/07 a été relevé sur **l'annonce 24113**, l'une des rares à deux mandats *(ses mandats 9887/553 sont les exemples du document)*. Et son sous-lot **A0** — *« verrouiller le format exact, en lecture seule, sans coder »* — **n'a jamais été produit** ; A1 a été codé le même jour | |
| | ✅ **A0 EST FAIT (25/08)**, lu dans le JavaScript de Hektor : `mandatFrom = '#selectedMandatId'` **par défaut**, la liste ne prime que si elle existe ; `idMandat = .val()` · `typeMandat = .attr('data')` ∈ `mandat` \| `protexaMandat`. ⚠ **Faux ami** : `typeMandat` est la **famille de registre**, PAS le type juridique — et le code laisse `payload.type_mandat` passer **avant** Hektor : piège armé | |
| | ⚠ **Asymétrie à refermer** : la branche « l'app fournit l'identifiant » **fabrique** une cible sans vérifier que Hektor la propose ; l'autre branche, elle, refuse. **La clôture est IRRÉVERSIBLE côté Hektor** | |
| | ❗ **Ce chantier existait et n'était cité NULLE PART dans ce plan** — 20ᵉ note orpheline, trouvée le 25/08 en cherchant autre chose. Les déclencheurs, les motifs Hektor et les arbitrages sont **verrouillés depuis le 30/07** | |
| | ✅ **Sa source est désormais prouvée** : le formulaire Hektor cible le mandat par son **ID INTERNE**, et la mesure du 25/08 établit que `mandat_source_id` **EST** `hektor_mandat_id` — **23 814 / 23 814**. Le registre peut donc remplacer la liste déroulante de Hektor le jour où elle disparaît | |
| | ℹ **Rappel de l'arbitrage** : un mandat **échu reste « en cours »**, il n'est PAS clos automatiquement — seule une **alerte négo** part. C'est pourquoi **22 749 mandats sont échus et non clos, et 85 seulement portent une date de clôture** : ce n'est pas un défaut, c'est la règle | |
| ✅ **C.14** | ~~**Le titre français côté serveur, et le calque lu par l'en-tête**~~ **FAIT le 25/08** — `view_generale` préfère l'entrée **française** au lieu de `$[0]` *(qui prenait le premier bloc quelle que soit sa langue)* · `optimisticOverlayValue()` branché sur l'en-tête **et** le fil d'Ariane | **FAIT** |
| | ℹ **Portée re-mesurée le 25/08 au soir** *(mon chiffre de l'après-midi, « 3 annonces », était approximatif)* : sur **13 475 annonces actives**, **701** avaient un `texte_principal_titre` faux *(686 vides)* — et **1 seule** avait son titre **visible** affecté. Les 701 comptent quand même : le front lit `texte_principal_titre` **en premier** pour le titre de la rubrique « Le Bien » et l'en-tête du bloc descriptif | |
| | ⏳ **C.14-bis, petit, non urgent** : le front a **son propre repli** avec le même défaut — `api.ts:4097` prend `textBlocks.find(item => item.html \|\| item.text)`, **le premier bloc quelle que soit sa langue**. Ne se déclenche que si le champ arrive vide, donc rare après C.14 — mais faux quand il sert | |
| | Le calque (`app_optimistic_overlay`) **contient bien** le champ modifié, titre compris — vérifié en base. La **rubrique** le lit et affiche la nouvelle valeur. Mais `App.tsx:22527` fait `const heroTitle = dossier.titre_bien || …` : **l'en-tête, le fil d'Ariane et le bandeau lisent la colonne en direct**. Résultat : *la fiche se contredit elle-même* — nouveau titre dans la rubrique, ancien titre partout ailleurs | |
| | ℹ **Ce n'est pas une régression du calque** : c'est un composant **jamais raccordé**. Le cockpit V2 est arrivé après *(17/07)* et son en-tête lit la donnée comme le faisait l'ancienne fiche. La note `calque-cles-hektor-vs-front` porte déjà la trace du chantier « overlay-first », branché écran par écran | |
| ⏳ **C.11** | Ménage des tables mortes *(ex-19)* | |
| ✅ **E.0** | ~~**AUDIT : que ne peut-on PAS faire dans l'app ?**~~ **FAIT le 25/08** — `ETUDE_OU_EN_SOMMES_NOUS_2026-08-25` | **FAIT** | **31 types de travaux éprouvés, 0 erreur sur 54 737.** Quatre manques, et **un seul est du code** |
| | ❌ **CONCLUSION CORRIGÉE LE 25/08 PAR FRÉDÉRIC.** J'avais écrit que le bridage admin *(passer une offre, un compromis, une vente)* était le manque qui sépare de l'étape 2. **C'est FAUX : ce bridage est VOULU.** Le négociateur ne décide pas seul — il fait une **demande de validation** à l'admin. Le circuit existe et il est éprouvé : `demande_diffusion` · `demande_baisse_prix` · `demande_annulation_mandat`, **9 demandes, 8 acceptées et traitées** | |
| | ✅ **Ce qui reste avant l'étape 2 n'est donc PAS du code** : créer la dizaine de comptes manquants *(5 actifs, dont 2 commerciaux)*, éprouver la création de mandat, et **s'en servir soi-même une semaine** | |
| | ℹ Et trois manques qui **ne sont pas du code** : **5 comptes actifs** dont 2 commerciaux pour une douzaine de négociateurs · la création de mandat **éprouvée une seule fois** · et l'usage réel par Frédéric, sans lequel tout est mesuré sur une app que personne n'exerce | |


#### 🔌 LES INTERRUPTEURS — « construit » ne veut jamais dire « actif »

| Tâche | Constructible maintenant | Ce qui attend |
|---|---|---|
| **C.2b** · **C.11** · **C.12** | oui, entièrement | **rien** — additif |
| **C.6** | oui, en doublure | qui **lit** la table |
| **C.8** | oui | le calque, côté front |
| **C.9** | oui, derrière drapeau | le drapeau |
| **C.7** | oui, **contrat vide** | ⬇ **la liste des champs app** |
| **C.4** | oui, worker par worker | ⬇ **la liste des champs app** *(les 3 arbitrages)* |

**Il n'y a donc qu'UN interrupteur de fond, et deux tâches le partagent.**

#### 🗝 LA LISTE DES CHAMPS APP — le seul vrai interrupteur

*Elle existe déjà. Elle fait trois lignes. Elle marche.*

```
   phase2/sync/push_contacts_to_supabase.py:476
   APP_OWNED_CONTACT_FIELDS = ("birth_date", "birth_place", "marital_status")
```

Le commentaire du code dit pourquoi ce sont ceux-là : *« Hektor ne les renvoie **jamais**, seule
l'app les écrit »*. **Il n'y a rien à arbitrer : Hektor n'a rien à dire.**

**À quoi elle sert.** Aujourd'hui, tout ce que l'app écrit doit faire l'aller-retour par Hektor
pour survivre — `app → worker → Hektor → import de nuit → retour`. Si un maillon casse, l'import
ramène la valeur de Hektor et **la saisie est remplacée**. La liste, c'est ce qui permet à une
valeur de **survivre sans l'aller-retour**.

| | Hektor connaît le champ ? | Faut-il décider ? |
|---|---|---|
| **les 3 qui marchent déjà** | **non** | non — personne à contredire |
| **les 189 de la carte A1** | **oui** | **oui, pour 3 d'entre eux** |
| **côté ANNONCE** | — | ⚠ **aucune liste n'existe** *(vérifié le 24/08)* |

> ❗ **Le point qui change la nature des 3 arbitrages.** Le jour de la coupure, Hektor n'existe
> plus : **il n'y a plus rien à arbitrer, l'app gagne tout.** Donc `statut_annonce`,
> `negociateur_email` et les champs de mandat ne sont **pas** trois décisions de fond sur le
> métier. Ce sont **trois réglages de transition**, réversibles, qui ne valent que pendant la
> cohabitation — et qu'on peut laisser à « Hektor gagne » aussi longtemps qu'on veut.

#### SUPPRIMÉ le 24/08 — rendu sans objet par l'étape 2

| | | |
|---|---|---|
| ~~**C.1**~~ | ~~la règle d'arbitrage, ses 3 cas d'écart, sa tolérance de comparaison~~ | le cas ③ disparaît |
| ~~**la notification de conflit**~~ | ~~unifier les 3 objets~~ | il n'y aura plus de conflit à notifier |
| ~~**C.10**~~ | ~~corriger le modèle « au moins » de la modale recherche~~ | **une fois la porte fermée (C.3), l'app n'a plus à exprimer ce que Hektor comprend** |
| ~~**5a**~~ | ~~renommer seul les 11 paramètres ambigus~~ | **RAYÉE le 20/08** — Postgres refuse le rename, l'appel se fait par NOM |

---

### BLOC D — RAPATRIER LES FICHIERS · *irréversible*

| | Tâche | |
|---|---|---|
| ⏳ **D.1a** | **MESURER d'abord** — combien de `cloud_available` n'ont pas de fichier local ? | **1 heure.** L'audit du 22/08 a montré que la tâche est bien plus petite qu'annoncée |
| ⏳ **D.1** | **Documents** — ~~40 493~~ **à redimensionner** : 44 512 indexés, dont **22 491 déjà `local_only`** et 22 021 `cloud_available` ; et **46 359 fichiers, 65,6 Go déjà sur le disque** — donc une part du cloud est déjà là | ⚠ avec le frein anti-bannissement, et **sans JAMAIS rejouer les annonces déjà en échec** |
| ⏳ **D.2** | **Photos** — 1 397 | ⚠️ |

---

### BLOC E — COUPER

| | Tâche | |
|---|---|---|
| | → **E.0 est passée en PISTE 1** *(24/08)* — si l'on construit tout maintenant, il faut savoir **maintenant** ce que l'app ne sait pas faire, sinon on bâtit six semaines et on découvre le trou à la fin | |
| ⏳ **E.1** | **19-R2 — RATTRAPAGE, LA VEILLE DE LA BASCULE** | ⚠️ **dernière occasion.** Après, plus personne ne crée de recherche dans Hektor |
| ⏳ **E.2** | **BASCULE DES NÉGOCIATEURS SUR L'APP** *(ex-19bis)* | **décision d'organisation** — c'est elle qui débloque tout le bloc recherches |
| ⏳ **E.3** | Les workers deviennent invisibles *(ex-26)* | une fois l'avertissement éprouvé |
| ⏳ **E.4** | Le jour J — le distributeur démarre à 100 000 · le serveur remplit **les deux cases** · le numéro est **imposé** · on éteint l'aspirateur *(ex-32→35)* | |

---

### BLOC F — APRÈS LA COUPURE · *rien d'urgent, mais à ne pas perdre*

| | Tâche | |
|---|---|---|
| ⏳ **F.1** | **UTILISATEURS, RÔLES ET DROITS** — revoir qui peut faire quoi | *après la coupure, décision de Frédéric le 25/08* |
| | **Aujourd'hui le modèle est délibérément serré** : trois profils *(admin, commercial, administratif)*, et le négociateur **demande** au lieu de décider — baisse de prix, diffusion, annulation de mandat. **C'est un contrôle voulu, pas une limite technique** | |
| | Ce qu'il faudra reprendre alors : le périmètre de chaque rôle, ce qui reste soumis à validation, et ce qui peut s'ouvrir | |

---

### CE QU'IL NE FAUT PAS OUBLIER

*Liste tenue à jour. Ce qui n'est dans aucun bloc et qui se perdrait autrement.*

- **Les 4 services Windows et les 33 workers** : ils deviennent inutiles au jour J. Décider quand
  on les éteint, et dans quel ordre.
- **Le monitoring doit survivre à la coupure** — 20 sentinelles, dont plusieurs interrogent des
  objets liés à Hektor. À relire une par une avant E.4.
- **Deux alertes ouvertes** : `data.notif_orphelines` 57 *(seuil 20)*, `data.notif_non_lues` 851
  *(seuil 300)*.
- **Une recherche de test** sur le contact 603953 *(Maison · Firminy · 180 000 €)*, que ni l'app
  ni l'interface Hektor n'ont laissé retirer — l'agence du contact est 12, pas 1.
- **L'espace client tourne sur Render** : vérifier qu'il ne dépend de rien de Hektor.
- **Le premier remplissage de C.6** doit se faire **pendant que Hektor vit** : c'est le miroir qui
  alimente.

---

## LE BLOB DE DETAIL — faux obstacle, leve le 21/08

Le contrat d'autorite du 17/08 reclamait *« un inventaire exhaustif des ~130 cles du blob avant
d'ecrire quoi que ce soit dessus »*. **Cet inventaire est sans objet** : la question n'etait pas
« que contient le blob » mais « qui l'ecrit ».

**Une seule fonction ecrit dans le blob** : `app_edit_annonce_optimistic`. Et elle n'y touche
que **7 cles** :

```
   surface . nb_pieces . nb_chambres . surface_terrain_detail
   latitude_detail . longitude_detail . garage_box_detail
```

Elle range en plus ce que le negociateur vient de saisir dans un **compartiment dedie**,
`app_optimistic_overlay`. **Le paquet a deja un tiroir reserve a l'app.**

Les 127 autres cles sont une photocopie de Hektor : l'app les lit, les affiche, s'en sert pour
le rapprochement -- elle n'en ecrit aucune.

> **Ce qui reste a faire est minuscule** : proteger ces 7 cles de la reecriture de nuit, avec le
> mecanisme qui existe deja (celui qui protege naissance / lieu / situation matrimoniale cote
> contact). Ce n'est pas un chantier a part : ca rentre dans « Hektor confirme, il n'ecrase plus ».

**Ce qui reste valide de la mise en garde du 17/08** : ne PAS declarer « tout le descriptif est a
l'app ». Le blob transporte de la diffusion, des affaires, des mandats et des photos bien
vivants -- une regle en bloc les aurait geles.

---

## LE TROU DE STOCKAGE DES ANNONCES — decouvert et tranche le 21/08

> ### ⚠ DIAGNOSTIC CORRIGÉ LE 21/08 AU SOIR — lire ceci d'abord
>
> **Tout ce qui suit reposait sur une affirmation fausse.** L'audit de la data locale
> (`notice/AUDIT_DATA_LOCALE_ET_SYNCHRO_2026-08-21.md`) a ouvert la base au lieu de lire le
> nom des fichiers :
>
> ```
>    ce que cette section affirme   « le serveur ne detient pas les annonces »
>    ce que la base contient        app_view_generale : 56 890 lignes, 130 COLONNES
>                                   refaite chaque nuit en 37 SECONDES
>                                   132 des 168 champs sont deja des colonnes locales
> ```
>
> `view_generale.py` n'est pas une vue : c'est un `DROP TABLE` suivi d'un
> `CREATE TABLE AS`. **Le serveur détient déjà les annonces**, et il les gardera après la
> coupure — le miroir gèle, il ne disparaît pas.
>
> **Le vrai problème n'est donc pas la conservation, c'est l'écriture** : la table étant jetée et
> refaite chaque nuit, une valeur écrite par l'app n'y survivrait pas jusqu'à 05:30. Il faut une
> table à côté, jamais reconstruite — patron `app_search_registry`. **C'est la tâche C.6, et
> elle est beaucoup plus petite que ce que décrit la suite de cette section.**
>
> La suite est conservée telle quelle : elle porte des mesures justes (le partage 59/134, le
> calendrier, les trois gestes) et le raisonnement qui a mené à l'erreur.

**Constat, mesure a l'appui.** Cote annonces, le serveur local **ne detient pas les donnees** :

```
   app_dossier  (local)  =  10 colonnes seulement
      id . hektor_annonce_id . hektor_mandat_id . numero_dossier
      numero_mandat . commercial_id . commercial_nom . dates . absent_depuis
```

Le contenu vit **uniquement dans le miroir de Hektor** (`data/hektor.sqlite`, 34 tables,
464 952 reponses API brutes). `view_generale.py` recompose a la volee **une ligne a plat
d'environ 200 champs**, qui part ensuite vers Supabase, coupee en deux :

| | |
|---|---|
| **59 champs** | colonnes de `app_dossier_current` -- chercher, filtrer, trier |
| **134 champs** | le paquet `app_dossier_detail_current` -- afficher |

Le partage est decide par deux listes explicites dans le code. **Rien n'est opaque** : les
134 cles sont nommees et calculees une par une. *(C'est pourquoi l'« inventaire des 130 cles »
reclame par le contrat d'autorite du 17/08 est sans objet -- voir plus bas.)*

> **Le probleme** : le jour ou Hektor s'eteint, le miroir cesse d'etre alimente. Or c'est lui
> qui fabrique la ligne a plat. **Le serveur local n'aurait plus de quoi la recalculer.**

*(Le contact et la recherche n'ont PAS ce trou : le local a ses propres tables --
355 641 contacts, 76 839 recherches.)*

### La decision (Frederic, 21/08) : option ②

**Le serveur local recoit ses propres tables d'annonces** et reste le maitre, comme pour les
contacts et les recherches. Supabase garde son role : le sous-ensemble utile, en ligne.

**Consequence de calendrier, non negociable** : le remplissage initial doit se faire **pendant
que Hektor vit encore**, puisque c'est le miroir qui alimente. Apres la coupure il serait trop
tard. -> tache **26bis**.

### Les trois gestes, et OU ils sont dans la liste

```
   26bis-(1)  CREER + REMPLIR   juste apres la bascule du numero de recherche
   26bis-(2)  OBSERVER          en parallele, personne ne lit
   ------------------------------------------------------------------
   26bis-(3)  BASCULER          juste apres la tache 9 -- COLLEE au contrat d'autorite
```

**Pourquoi ce n'est plus a la fin (corrige le 21/08).** Je l'avais rangee avec le rapatriement
des documents et des photos, dans la famille « sortir de chez Hektor avant la coupure ».
**Fausse ressemblance** :

- **Ce n'est PAS irreversible.** Documents et photos, oui. Une table locale, on la jette.
- **Elle demande une longue observation.** La poser tard, c'est repousser la coupure d'autant.
- **(3) va avec 6-9.** Les laisser a vingt taches d'ecart, c'est se condamner a faire l'un sans
  l'autre : le contrat aurait un arbitrage sans endroit ou l'ecrire.
- **Et surtout** : la creation app-first (23-25) ecrit dans Supabase. Sans 26bis, une annonce
  creee dans l'app n'existe QUE la, et le serveur ne l'apprend que si Hektor la confirme.
  **Ce serait creuser le trou pendant qu'on le rebouche.**

**Une seule reserve, assumee** : (2) attend la bascule du numero de recherche, pour ne pas avoir
deux doublures a surveiller en meme temps. C'est une affaire de jours. Six chiffres a lire chaque
matin au lieu de trois, ca cesse d'etre une surveillance et ca devient une corvee -- et une
sentinelle qu'on ne lit plus ne protege de rien.

### (3) EXIGE le contrat d'autorite -- trouve par Frederic le 21/08

L'app n'ecrit QUE dans Supabase (aucune porte d'entree vers le serveur, et il ne faut pas en
creer). Donc une table locale alimentee seulement par le miroir **apprendrait les modifications
uniquement par Hektor** -- et seulement si Hektor les a recues. **Une saisie en conflit, ou dont
l'envoi a echoue, n'arriverait JAMAIS dans la base locale.**

Le serveur doit donc **venir lire dans Supabase ce que l'app a ecrit**. Ce mecanisme existe deja,
pour trois champs de contact : `fetch_app_owned_contact_fields` relit dans Supabase ce que Hektor
ne connait pas, et le reinjecte. **Meme geste, a etendre.**

```
   la nuit :
        ce que dit HEKTOR (le miroir)  +  ce que dit L'APP (relu dans Supabase)
              -> arbitre selon le CONTRAT D'AUTORITE du 17/08
              -> ecrit dans LA BASE LOCALE
              -> envoye vers Supabase
```

> **La table locale devient l'endroit ou l'arbitrage a lieu.** Aujourd'hui il n'y a pas d'endroit :
> c'est pour cela que Hektor gagne par defaut -- il est seul dans la piece.

**Consequence sur l'ordre** : les taches **6-9** et **26bis** ne sont plus independantes.
`26bis sans le contrat` = une base qui oublie les saisies.
`le contrat sans 26bis` = un arbitrage sans endroit ou se faire.

### Ce que 26bis debloque en plus

Apres la coupure, une annonce **creee dans l'app** puis archivee n'aura jamais existe dans le
miroir : son detail ne serait nulle part. La consultation des archives doit donc changer de
source -- et 26bis est ce qui le permet.

---

## LE BLOC RECHERCHES — ce que les audits du 20/08 au soir ont changé

**Trois choses que je croyais et qui sont fausses**, vérifiées dans le code, pas déduites :

| Ce qui était écrit | Ce que la lecture montre |
|---|---|
| L'étiquette sert à détecter qu'une recherche a changé chez Hektor | **Non.** La détection vient de la **redemande de la fiche** (run 03:00, sans filtre de date) et de la comparaison de contenu `stable_payload_hash`. L'étiquette n'est que le **nom de rangement** de la ligne |
| Il faut reprendre ≈ 493 000 lignes | **Non.** **Un seul endroit fabrique l'étiquette** : `build_contacts_layer.py:827` |
| Le renommage seul est sans risque | **Non.** Postgres refuse le rename, l'appel se fait par NOM, la compilation ne voit rien |

**La preuve que le numéro suffit est dans le projet lui-même.** Dans le *même* script d'envoi,
deux tables voisines :

| Table | Rangée sous | Quand Hektor modifie |
|---|---|---|
| `app_contact_current` | `hektor_contact_id` — **un numéro** | ligne **mise à jour sur place** ✅ |
| `app_contact_search_current` | l'étiquette — **un haché de contenu** | ligne **supprimée puis recréée** ❌ |

Les modifications de contact faites dans Hektor remontent parfaitement. **Le mécanisme
fonctionne déjà avec un numéro stable — il n'est pas appliqué aux recherches, voilà tout.**

### Le fond, formule par Frederic le 20/08 au soir : **il y a DEJA deux haches**

Preuve dans `phase2.sqlite`, table `app_contact_supabase_push_state` :

```
   UNE RECHERCHE
   nom de la ligne : 001697ad4134b105219d5549       <- un hache (la cle)
   empreinte       : 742548023fb03575338def20...    <- un AUTRE hache

   UN CONTACT
   nom de la ligne : 100030                         <- un NUMERO
   empreinte       : 03dd0f0f5e96c4c031bec5b88...   <- un hache
```

**L'empreinte de contenu existe deja sur les 3 962 recherches.** Elle est calculee et
stockee a chaque run. **Et elle n'est jamais consultee** : le nom ayant change en meme temps
que le contenu, la ligne d'avant est introuvable et l'empreinte connue reste rangee sous un
nom mort.

> **Deux haches sur chaque recherche. Le premier fait mal le travail du second.
> Le second, qui le ferait bien, n'est jamais lu.**

**Ce que le chantier fait, exactement :**

```
   AVANT   nom : 001697ad4134b105219d5549     empreinte : 742548...
   APRES   nom : 412                          empreinte : 742548...
                  ^                                        ^
             on remplace CA                      on ne touche pas a CA
```

Le run de nuit retrouve alors la ligne d'avant, compare les deux empreintes, voit que le
contenu a bouge, **et met a jour au lieu de detruire**.

> **On ne construit rien. On enleve un doublon qui bloque un mecanisme deja present.**

Le detail de la boucle : `push_contacts_to_supabase.py:206-211`
`known_hashes.get(row_key(row)) != stable_payload_hash(row)` -- le nom sert a retrouver ce
qu'on savait, l'empreinte sert a comparer. Deux metiers, une seule ligne de code.

**La méthode retenue est celle de Frédéric (20/08) : la doublure.**

```
   poser le numero A COTE, sans rien lui confier
        -> l'etiquette continue de commander, rien ne casse
   observer pendant des semaines : tombe-t-il toujours juste ?
        -> une sentinelle repond, pas une supposition
   basculer seulement une fois qu'il a fait ses preuves
```

> C'est l'inverse de ce que j'avais proposé — basculer puis vérifier. **Et c'est ce qu'on
> aurait dû faire pour les annonces** : `app_dossier_id` a dérivé de mars à juin sans que
> personne le voie, précisément parce que personne ne l'observait.

**Tâche 4bis — RÉPONDUE le 21/08.** **Hektor ne sait pas supprimer une recherche.**
Le worker, même pour un « Supprimer » demandé depuis l'app, appelle
`archiveHektorContactSearch` → `mode=contacts-contactProfile-modifDateArchiveCritere` avec une
`dateArchive` : il **pose une date**, il n'efface rien (`console_job_worker.js:11878-11890`, `:11918`).

> **Donc le rang ne glisse jamais, et `(contact + rang)` est une poignée stable.**
> Confirmé par les données : 72 872 archivées en local occupant des rangs jusqu'à 15, et
> seulement **9** recherches actives précédées d'une archivée. Capturer l'`idCritere` n'est
> plus un préalable — ça reste un confort.

⚠️ **Mais l'archivage détache quand même**, pour une raison de **périmètre**, pas de rang :
le local garde les archivées, **Supabase ne garde que les actives**. Une recherche archivée
disparaît donc de Supabase, et ce qui pointait sur sa clé devient orphelin. C'est ce rythme
que mesure le carnet du balayage (`app_sweep_search_orphans_log`, posé le 21/08).

*(Correction : les « 31 recherches supprimées chez Hektor » notées le 20/08 étaient selon toute
vraisemblance des recherches **archivées**.)*

### Le nom figé épingle une POSITION — conséquence relevée le 21/08

Objection de Frédéric sur « la tâche 22 est déclassée ». **Elle portait juste.**

Ce qui a été vérifié et tient : **un seul endroit du projet fabrique un nom de recherche**,
`build_contacts_layer.py:828`, et le registre lui reprend la main à la ligne 1235. Le front, le
worker et les fonctions Postgres n'en fabriquent aucun *(vérifié le 21/08)*. Donc oui : plus
personne ne peut recalculer un nom et ne plus rien retrouver.

**Mais figer le nom déplace le risque, il ne le supprime pas :**

```
   AVANT   le nom designait UN CONTENU   -> le contenu change, le nom change, la ligne s'orpheline
   APRES   le nom designe UNE POSITION   -> la position glisse, le nom se recolle sur la MAUVAISE
                                            recherche -- et SANS BRUIT
```

Le second est plus rare mais **plus grave** : l'orphelinage se voit *(le balayage le compte)*, la
mauvaise attache ne se voit pas. Et ce sont précisément les **4 portes** qui relisent les rangs
chez Hektor. **La tâche 22 reprend donc un rôle de stabilité — un autre que celui qu'elle perd.**

**Ce qui a été mesuré**, sur l'ordre dans lequel Hektor rend les recherches :

```
   9 contacts seulement melent archivee(s) et active(s)
      8  toutes les archivees AVANT les actives   -> ajout en FIN de liste
      0  toutes les archivees APRES les actives   -> insertion en tete
      1  entrelacee  (archivee / active / archivee)
```

L'entrelacée n'est pas un contre-exemple : c'est exactement ce que produit un ajout en fin de
liste quand on archive après coup. **Zéro contre-exemple — mais 9 contacts, ce n'est pas une
preuve.** À dire ainsi, et pas autrement.

**D'où la tâche 4sexies**, qui remplace l'observation par un fait vérifiable : *le nombre de
recherches d'un contact ne peut que croître.* Toute diminution signale un glissement.

**Posée le 21/08** — `patch_sentinelle_recherche_disparue_2026-08-21.sql`. Le repère ne redescend jamais *(`greatest`)* : sinon le relevé du lendemain effacerait l'anomalie de la veille. **Vérifiée en la faisant sonner**, pas seulement en la voyant à 0.

---

## LE CHANTIER D'IDENTITÉ — trois objets, un seul dessin

**Le dessin, valable pour les trois :**

```
   case 1 : un numero A TOI        <- la cle, remplie des la creation, jamais remplacee
   case 2 : le numero de Hektor    <- simple reference, vide en attendant son retour
```

**Arbitrage Frédéric (20/08) : pas de solution mixte.** Un objet ne peut pas avoir une case pour
les anciens et deux pour les nouveaux. **Tout le parc bascule d'un coup, ou rien.**

**Deuxième arbitrage : on double ET on bascule dans la foulée.** Jamais de numéro « secondaire »
généré mais inutilisé — c'est ce qui a laissé `app_dossier_id` dériver de mars à juin sans que
personne le voie. *Ce qui est utilisé est ce qui est vérifié.*

### L'ordre, établi par l'audit des points d'appel (20/08)

| Ordre | Objet | Volume | Points d'appel ambigus | Risque |
|---|---|---|---|---|
| **1** | **Transactions** | ≈ 29 100 | **0 sur 12** — jamais envoyés au worker | **le plus faible** |
| — | *Annonces* | *341 394* | *3 sur 56, dont 2 `null`* | *fait le 19/08* |
| **2** | **Contacts** | ≈ 186 500 | **3 réels**, ≈ 10 fonctions à relire | **le plus élevé** |
| **3** | **Recherches** *(3 961)* | ≈ 1 300 rapprochements à rebrancher | clé = **hachage du contenu**, elle bouge seule | **cas à part — voir le dossier ci-dessous** |

> **Pourquoi les contacts sont les plus risqués** : ils n'ont qu'une seule colonne, donc **aucune
> couche n'a jamais eu a faire la distinction**. Mesure du 20/08 :
>
> | | Front | Fonctions de la base | Worker |
> |---|---|---|---|
> | Annonces | 53 explicites / 56 | explicites | lit un champ nomme |
> | **Contacts** | **3 ambigus**, ~10 fonctions | **6 fonctions ambigues** | lit un champ nomme |
> | Transactions | 12 / 12 explicites | jamais envoyees | ne les connait pas |
>
> Les six fonctions concernees : `app_console_create_update_contact_job`,
> `..._delete_contact_job`, `..._contact_search_job`, `..._update_contact_search_job`,
> `..._delete_contact_search_job`, `..._update_mandant_contact_job` — toutes ecrivent
> `hektor_contact_id` a partir de `target_contact_id`.

### La méthode, par objet — jamais deux à la fois

```
   0. AUDIT COMPLET DES POINTS D'APPEL, sur les TROIS couches -- prealable absolu.
      Partout ou un identifiant part vers un worker, il doit etre lu dans la
      colonne NOMMEE, jamais dans "la cle".
        a) le front        : modales, api.ts, App.tsx
        b) les fonctions de la base : les 14 app_console_create_*_job
        c) le worker       : il lit deja un champ nomme -> a confirmer, pas a modifier
      Puis renommer ce qui est ambigu : input.contactId -> input.hektorContactId.
      Aucun effet fonctionnel aujourd'hui, verifie par la compilation.
   1. ajouter la case (Supabase + local, parent et tables enfants)
   2. renumeroter le stock  : table de correspondance conservee, essai a blanc
                              qui annule tout, transaction unique, verification chiffree
   3. basculer la cle DANS LA FOULEE : les jointures lisent la nouvelle case,
      ET LA CASE HEKTOR DEVIENT FACULTATIVE -> c'est CE geste qui autorise
      la creation depuis l'app. Il est impossible avant l'etape 3, puisque
      la case Hektor est encore la cle.
   4. poser la sentinelle   : doublons = 0, orphelins = 0, ecart local/Supabase = 0
   5. le worker NE CHANGE PAS : il lit toujours le champ nomme hektor_*_id
```

**Preuve avant la masse** : basculer un seul objet, le modifier depuis l'app, vérifier que le
worker aboutit et que Hektor a bien reçu. Dix annonces avaient servi de test le 19/08 avant les
12 162 — aucun orphelin créé.

**Garde-fou pendant la transition** : la RPC de création de travail **refuse** de créer un travail
Hektor si la case Hektor est vide — elle le met en attente. Un travail ne peut donc pas partir
avec un mauvais numéro : il ne part pas du tout.

---

## LE DOSSIER RECHERCHES — enquête du 20/08, à lire avant d'y toucher

**Trois facettes distinctes**, identifiées par `RAPPORT_ANALYSE_SYNC_HEKTOR_SUPABASE_2026-06-19.md` :

| | Facette | État |
|---|---|---|
| **A** | **Clé instable** — `contact_search_key` hache le **contenu éditable** | ❌ jamais corrigée |
| **B** | **Écrasement** — l'édition renvoie TOUTE la recherche depuis une copie peut-être périmée | ❌ jamais corrigée |
| **C** | **Angle mort `date_maj`** — éditer une recherche dans Hektor ne bump pas la date du contact | ✅ **corrigée le 20/06** |

**C a été corrigée par un run dédié** : `scheduled/run_recherches_actives.ps1` ->
`sync_active_searches.py`, **03:00 chaque nuit**, ~3 590 contacts, sans filtre `date_maj`.

> **Le noeud : la correction de C amplifie A.**
> Avant le 20/06, une édition faite dans Hektor était invisible -> la clé ne bougeait pas.
> Depuis, elle est détectée -> **la clé bouge** -> l'historique se détache.
> **Orphelins : 327 le 19/06 -> 1 332 le 20/08. Multiplié par quatre en deux mois.**

**Ce n'est PAS voulu — vérifié le 20/08 :**

- **6 clés du projet sur 7 hachent une identité** (relation, registre, contact, dossier, doublons).
  La recherche est **la seule** à hacher du contenu.
- **Deux consommateurs s'en protègent déjà en production** : `app_email_envoi.search_index`
  (migration du 17/06 : *« la contact_search_key change à l'édition »*) et
  `espace_client._load_search_for_envoi` (3 niveaux, *« on ne s'y fie qu'en tout dernier recours »*).
  **Le contrat de fait est déjà : ne pas se fier à cette clé.**
- **Personne ne dépend de son instabilité.** Le rapprochement est le seul à ne pas se protéger.

**Pourquoi ça n'a jamais été corrigé** : le correctif proposé en juin était `hash(contact_id, index)`.
Il est **mauvais** — l'`index` est la **position**, qui bouge à chaque suppression et n'est pas
alignée entre l'API et le grattage Console. **La bonne réponse est un identifiant propre à l'app.**

**Gravité** : le moteur de rapprochement est **app-only par décision métier**
(`NOTE_MOTEUR_RAPPROCHEMENT_ACQUEREUR_2026-06-14.md`). Ce qui se détache — propositions, retours
acquéreur, relances, emails — **n'existe nulle part ailleurs**. Hektor ne peut rien reconstruire.

**Vérifié en direct le 20/08**, contact 604020 : édition à 14:36 -> clé inchangée, 41
rapprochements recalculés ; retour de Hektor à 14:48:07 -> **nouvelle clé**, les 41 deviennent
orphelins. Et **aucune des 4 fonctions** qui suppriment des rapprochements ne nettoie par absence.

### Ce qui pend sous la clé — mesuré le 20/08, SEPT tables

| Table | Total | Orphelins | Recalculable ? |
|---|---|---|---|
| Historique de score | 450 046 | **11 966** | ✅ oui |
| Rapprochements | 47 547 | **1 373** | ✅ oui |
| **Notifications** | 843 | **13** | ❌ **non** |
| **Propositions** | 11 | **6 — 55 %** | ❌ **non** |
| **Relances** | 10 | **5 — 50 %** | ❌ **non** |
| **Envois d'email** | 82 | **2** | ❌ **non** |
| **Retours acquéreur** | 7 | **2 — 29 %** | ❌ **non** |

> ⛔ **NE PAS « nettoyer les orphelins » d'un bloc.** Plus de la moitié des propositions et des
> relances sont détachées : ce sont des traces d'actions réelles, **app-only**, que Hektor n'a
> jamais eues. Les supprimer les détruirait définitivement.

**Deux gestes distincts, dans cet ordre :**

1. **REBRANCHER l'irremplaçable** — propositions, relances, retours acquéreur, envois,
   notifications — par *(contact + search_index)*, **exactement comme le fait déjà
   `espace_client._load_search_for_envoi`**. ~28 lignes aujourd'hui, mais 50 % des propositions.
2. **NETTOYER le recalculable** — rapprochements et historique de score, 13 339 lignes, sans risque.
3. **CLÉ PROPRE**, pour que ça ne recommence pas.

**Rebrancher AVANT de nettoyer.** Dans l'autre sens, on détruit ce qu'on voulait sauver.

> **L'espace client ne changera pas de comportement** : il ne s'appuie déjà plus sur la clé
> (résolution à 3 niveaux). C'est le seul consommateur déjà immunisé.

### Les recherches deviennent-elles indépendantes en coupant le run de 03:00 ?

**Presque — il y a TROIS portes entrantes, pas une :**

| | Porte | Fréquence |
|---|---|---|
| **1** | Run dédié `sync_active_searches` | 03:00 |
| **2** | Run quotidien — `push_contacts_to_supabase` **supprime puis réécrit** les recherches d'un contact | 05:30 |
| **3** | **Read-through** — `refresh_console_contact_data` appelle le **même code** avec `--contact-id` | à chaque ouverture de fiche |

**Et une porte sortante** : les 3 travaux `*_hektor_contact_search`.

Couper les quatre rend les recherches entièrement app-owned — **et la clé cesse alors de bouger
toute seule, donc le problème A disparaît sans être corrigé**. Mais il faut d'abord :

- **corriger le modèle « au moins »** : la modale n'expose que des minimums, le worker sait envoyer
  20 critères. Ce que l'app ne sait pas exprimer sera perdu (cf. mémoire projet) ;
- **mesurer combien de recherches Hektor portent des critères invisibles dans l'app** ;
- **rebrancher l'irremplaçable** (point 1 ci-dessus) avant de couper quoi que ce soit.

**Ne pas ajouter de garde-fou sur la suppression** — décision Frédéric du 18/08 : il ferait échouer
les cas où le repli `list[0]` tombe juste.

### Le trou des NOUVELLES recherches — mesuré le 21/08

Les trois portes ci-dessus font entrer les **modifications**. Aucune ne fait entrer une
**première** recherche :

```
   les recherches ne sont PAS dans le listing -- uniquement dans ContactById
   creer une recherche ne bouge PAS la date_maj du contact
   le run de 03:00 ne relit que les contacts dont l'app connait deja une recherche active
   -> un contact qui gagne sa PREMIERE recherche n'entre dans aucun run. Jamais.
```

**Combien ?** Sonde du 21/08, **249 fiches tirées au hasard et lues en direct** chez Hektor parmi
les 67 483 contacts de typologie « acquéreur » sans recherche connue : **1 seule** portait une
recherche que l'app ignorait. Soit **≈ 270 recherches invisibles**, pas 67 000. *L'image de l'app
est juste à 99,6 %.*

**Ce que la sonde a écarté** : la typologie « acquéreur » **enveloppe** les recherches (aucune
recherche connue hors d'elle) mais elle est posée à la main sur des contacts qui n'ont jamais
rempli de critères, et elle ne bouge pas quand une recherche est créée. **Inutilisable comme
signal.** Il faut relire les fiches.

**Le remède** — `sync_active_searches.py --scope acquereurs`, c'est-à-dire *le run de 03:00 avec
une autre liste d'entrée* : mêmes quatre étapes, mêmes drapeaux, seule la sélection change
(`acquereur_contact_ids`). 71 337 fiches, **≈ 4 h 35**.

> ⚠️ **La pause de 20 s entre les lots ne doit pas être retirée.** Le run de 03:00 tient
> 6 appels/s pendant 10 minutes ; ici il faudrait les tenir 3 h. C'est exactement la forme qui a
> fait **bannir notre IP** au rattrapage des documents. Avec la pause : 4,2 appels/s en moyenne.

**Ce n'est pas un stock, c'est un débit.** La passe du 21/08 remet le compteur à zéro ; le débit,
lui, continue tant que les négociateurs saisissent dans Hektor. D'où **deux** passes, et pas une :

| | Quand | Pourquoi |
|---|---|---|
| **19-R1** | **21/08** — lancée à la main | solde les ~270 accumulées depuis mai |
| **19-R2** | **la veille de la bascule (19bis)** | ⚠️ **dernière occasion.** Tout ce qui aura été saisi dans Hektor entre les deux passes n'existe que là |

Entre les deux, si le délai s'allonge, relancer la même commande de temps en temps — elle est
idempotente et reprenable (chaque lot est indépendant, un lot en échec n'arrête pas le run).

---

## LES TROIS DÉPENDANCES RÉELLES À HEKTOR

| | Ce que Hektor fournit | Comment s'en passer | Délai |
|---|---|---|---|
| **1** | Le numéro de mandat | registre en propre | du code |
| **2** | La signature (ImmoSign) | Yousign | un contrat |
| **3** | **La diffusion portails** | contrats directs ou diffuseur | **contrat + migration commerciale** |

> **Arbitrage Frédéric (20/08) : les contrats démarrent à la fin** (chantier 5), pour préparer la
> coupure. Conséquence assumée : la date sera fixée par leur délai, qui ne commencera à courir
> qu'après le développement. La reprise des 350 annonces en ligne est le seul délai non maîtrisé.

---

## CHANTIER 1 — Maintenant, sans dépendance

| | Quoi | Pourquoi maintenant |
|---|---|---|
| **R1** | **Rebrancher ce qui est irremplaçable** — propositions, relances, retours acquéreur, envois, notifications — par *(contact + search_index)* | **URGENT** : une proposition sur deux a déjà perdu son lien, et rien ne peut la reconstruire |
| **R2** | **Nettoyer le recalculable** — 1 373 rapprochements + 11 966 lignes d'historique | sans risque, **mais seulement après R1** |
| **1.1** | ~~Un échec de worker prévient l'utilisateur et le monitoring~~ **FAIT le 20/08** (`48e475a`) | **indispensable** : un envoi raté laisse une annonce en ligne au mauvais prix |
| **1.2** | **Les recherches acquéreur sont enregistrées** dans l'app | seul endroit où une saisie se perd |
| **1.3** | Le numéro Hektor d'**annonce** a le droit d'être vide | ouvre la création app-first d'annonce |
| **1.4** | ~~**Identité des transactions**~~ **FAIT le 20/08** — 28 980 affaires renumérotées, `app_affaire_id` + `app_dossier_id` posés, clé basculée sur le numéro de l'app, triplet Hektor gardé en clé de réconciliation partielle | **le plus sûr des trois**, vérifié : 0 point d'appel ambigu. ⚠️ **`hektor_affaire_id` n'est unique que dans son type** — 7 541 numéros portés par deux types, 0 partageant l'annonce : Hektor tient trois compteurs qui se télescopent. Le numéro de l'app est **une seule série** pour les trois. Débloque la modale de statut (tâche 13) |
| **1.5** | **Identité des contacts** — renommage préalable, ajouter la case, renuméroter ≈ 186 500 lignes, **puis la case Hektor a le droit d'être vide** | débloque la modale d'ajout : contact + recherche + mandant écrits d'un coup. **Demande une demi-journée de relecture avant** |
| **1.6** | ~~Reprendre `numero_dossier`~~ **-> reporte au jour J** : comprendre la règle de numérotation Hektor et la continuer | référence métier lisible dans 11 tables — **personne ne la fabrique après la coupure** |
| **1.7** | ~~Annuaire négociateurs~~ **-> reporte au jour J** : le worker a besoin de l'`idUser` Hektor pour s'impersonner — 40 + 19, présents dans 14 tables | l'affectation doit survivre sans Hektor |

---

## CHANTIER 2 — Le cœur : Hektor confirme, il n'écrase plus

| | Quoi |
|---|---|
| **2.1** | Écrire la règle : les trois cas d'écart *(envoi pas parti / envoi raté / modifié dans Hektor)* |
| **2.2** | La tolérance de comparaison — la traduction des valeurs existe déjà (`resolveHektorSelectValue`) |
| **2.3** | Brancher au retour du worker *(`push_single_annonce_to_supabase.py:573`)* |
| **2.4** | Même règle sur l'import de nuit |

> **Le garde-fou existe déjà**, côté annonce et côté contact (`base_snapshot` + comparaison
> `date_maj`). Aujourd'hui, en cas d'écart, **Hektor gagne**. La règle 2 **inverse le verdict** :
> l'app garde sa valeur et signale. C'est une modification, pas une construction.

**Puis, dans la foulée :**

| | |
|---|---|
| **2.5** | **Le calque d'annonce disparaît** — il n'existe qu'à un seul endroit : l'édition de champs |
| **2.6** | La barrière : un travail sans numéro Hektor **attend** au lieu d'échouer |

---

## CHANTIER 3 — Appliquer le principe aux 16 workers

**Écrire chez soi d'abord, envoyer ensuite, confirmer au retour.**

| Ordre | Workers |
|---|---|
| **3.1** | Les 3 recherches *(ajouter / modifier / supprimer)* |
| **3.2** | **Statut + affaire** *(offre, compromis, vente)* — le geste le plus riche |
| **3.3** | Archiver / désarchiver / supprimer |
| **3.4** | **Créer un contact, créer un mandant, rattacher** *(après 1.3)* |
| **3.5** | **Affectation du négociateur — en DERNIER** (impersonation du worker) |

**Correctifs à glisser dedans :**

- **3.6** — **Clé propre au registre des affaires** *(28 980 lignes, clé 100 % Hektor)*
- **3.7** — **Fiabiliser le mandat des transactions** : l'app doit toujours le fournir ; aujourd'hui
  le worker le devine dans le HTML de Hektor si elle ne le fait pas
- **3.8** — **La clé de recherche** : aujourd'hui un hachage du contenu, elle change à chaque
  édition — **1 270 rapprochements déjà orphelins**. C'est la seule clé structurellement fausse.
- **3.9** — **Ménage** : `app_contact_override` (vide, non écrite), `app_console_create_update_contact_job`
  (remplacée par l'optimiste), tables `_v1` vides

---

## CHANTIER 3bis — Les recherches deviennent tiennes

**Quatre portes à fermer** — et c'est l'étape qui rend le problème de clé **sans objet** :

| | Porte | Fréquence |
|---|---|---|
| 1 | Run dédié `sync_active_searches` | 03:00 |
| 2 | Run quotidien — `push_contacts` **supprime puis réécrit** | 05:30 |
| 3 | **Read-through** — le MÊME code, avec `--contact-id` | à chaque ouverture de fiche |
| 4 | Les 3 travaux sortants `*_hektor_contact_search` | à l'édition |

**Deux préalables obligatoires :**

| | |
|---|---|
| **R3** | **Corriger le modèle « au moins »** — la modale n'expose que des minimums, le worker sait envoyer 20 critères. Aujourd'hui le run de nuit rattrape ; après la coupure, ce qui n'est pas stocké est **perdu** |
| **R4** | **Mesurer** combien de recherches Hektor portent des critères invisibles dans la modale |

> **Une fois les quatre portes fermées, plus personne ne recalcule le hachage : la clé cesse de
> bouger toute seule.** Le défaut identifié trois fois depuis juin disparaît **sans avoir été
> corrigé** — c'est la solution la plus économique du dossier.

---

## CHANTIER 4 — La création part de l'app

| | Quoi | Dépend de |
|---|---|---|
| **4.1** | **L'annonce** : la création écrit la vraie fiche | 1.4 · 2.3 · 2.6 |
| **4.2** | **Le contact et le mandant** : idem | 1.3 · 2.3 |
| **4.3** | **La modale d'ajout de contact** écrit ses trois objets d'un coup : contact + recherche + relation mandant | 4.2 |
| **4.4** | Les workers deviennent invisibles | **quand l'avertissement d'échec aura fait ses preuves** |

---

## CHANTIER 4bis — Rapatrier les binaires *(à terminer AVANT la coupure)*

| | Quoi | Volume |
|---|---|---|
| **4bis.1** | **Les documents** — `hektor_document_id` pointe vers le stockage de Hektor | **40 493** |
| **4bis.2** | **Les photos** — `hektor_photo_id`, idem | **1 397** |

> Ce ne sont pas des identifiants métier, ce sont **des adresses**. Tant qu'ils pointent vers
> Hektor, ils pointent vers un serveur qui va s'éteindre. **Irréversible : ce qui n'est pas
> descendu avant est perdu.**

---

## CHANTIER 5 — Préparer la coupure : les trois contrats

| | Quoi | Nature |
|---|---|---|
| **5.1** | **Sortie des portails** : combien, chez qui, à quel prix, et **comment reprendre les 350 annonces en ligne sans trou de visibilité** | contrat + migration |
| **5.2** | **Yousign** — l'app ne sait pas *lancer* une signature | contrat + code court |
| **5.3** | **Registre de mandats en propre** — obligation légale, libère `numero_mandat` | code |

---

## CHANTIER 6 — Le jour J, une journée

| | |
|---|---|
| **6.1** | Le distributeur démarre à **100 000**, dans le couloir vide 25 000 → 1 000 000 |
| **6.2** | Le serveur remplit **les deux cases** : les 24 tables qui portent le numéro Hektor continuent sans le savoir |
| **6.3** | Le numéro est **imposé**, pas laissé au compteur local (à 5,25 millions) |
| **6.4** | On éteint l'aspirateur : pipeline, workers, Playwright, file de travaux |
| **6.5** | Les 3 PDF et les 4 workers internes **continuent tels quels** |

---

## LA RÈGLE DES IDENTIFIANTS

> **Pour chaque identifiant que Hektor fabrique, trois questions avant la coupure :**
> **1.** Qui le fabriquera après ? · **2.** Que deviennent les valeurs déjà émises ? · **3.** Qu'est-ce
> qui casse s'il est vide ?
>
> Annonces : répondu. Contacts et affaires : chantier 1. **`numero_dossier`, annuaire, binaires :
> nouvellement identifiés.** Détail : `AUDIT_TOUS_LES_IDENTIFIANTS_2026-08-20.md`.

---

## LES CINQ RÈGLES

1. **Un numéro ne se perd jamais.** *(fait)*
2. **Hektor confirme, il n'écrase pas.**
3. **Une action a toujours une fin visible** — surtout quand elle rate.
4. **Tant que la diffusion passe par Hektor, Hektor doit rester à jour.**
5. **Le miroir se met à jour, il ne se remplace pas.** *(posée le 21/08, tâche 0.2)*

### La règle 5, en clair

`data/hektor.sqlite` — 3,89 Go, 464 952 réponses — est **l'archive de tout ce que Hektor a
jamais dit**. C'est encore lui qui fabrique chaque nuit les 56 890 annonces et les 355 641
contacts, en 37 secondes.

| | |
|---|---|
| **Les mises à jour n'ont pas besoin de suppression** | elles écrasent **en place** : `INSERT ... ON CONFLICT(endpoint_name, object_type, object_id_key, page_key) DO UPDATE SET`. Le miroir grossit et se corrige, il ne se vide jamais pour se remplir |
| **Les suppressions CIBLÉES restent permises** | une annonce (`delete_local_annonce.py`), un contact (`delete_local_contact.py`), les mandats d'une annonce reversés en entier à chaque run (`normalize_source.py`, `refresh_single_annonce.py`), une page de listing réécrite (`sync_raw.py`) |
| **Ce qui est INTERDIT** | supprimer le fichier, le déplacer, vider une table en masse, ou « faire de la place » sur les 3,89 Go |
| **Après la coupure il gèle — il ne devient pas inutile** | il reste la source des annonces jusqu'à C.7, et l'archive ensuite |

> C'est une règle de **conservation**, pas de gel. Elle n'empêche rien de ce qui tourne.

---

## CE QUI RESTE NON MESURÉ

- **La lenteur du front** — la mesure F12 n'a jamais été faite.
- **Les 176 champs du grand bloc** — affichables et modifiables, non filtrables dans les listes.
- **La clé de recherche** — hachage du contenu, elle change à chaque édition : **1 270 rapprochements
  déjà orphelins**.
- **Le coût réel de l'identifiant contact** — quelles tables parmi les 21 qui portent le numéro Hektor.
