# Porte d'entrée du projet

> Ce fichier ne contient **aucune connaissance**. Il contient des **adresses**.
> Le savoir est dans le plan, la liste, les notes et le code. En cas de désaccord,
> **c'est le code qui gagne, puis le plan, puis cette page.**
> Il se lit en trois minutes. Il ne remplace rien.

---

## 0. LA METHODE — *posee par Frederic le 20/09/2026, elle ne s'oublie jamais*

> **A chaque chapitre du plan, dans cet ordre, sans qu'il ait a le redemander :**
>
> 1. **AUDITER** le sujet — le code et la base d'abord, les notes ensuite. En cas de
>    desaccord, le code gagne.
> 2. **EXPLIQUER** clairement et simplement : ce que j'ai trouve, ce que je vais faire,
>    ce que ca touche, comment on revient en arriere, comment on verifiera.
> 3. **CODER**, en additif, derriere un interrupteur quand c'est possible.
> 4. **CONTROLER** : essais hors ligne, puis preuve en reel si necessaire. Dire aussi
>    ce qui a rate.
> 5. **METTRE A JOUR LE PLAN** : la case cochee AVEC sa mesure, la page de tete, le
>    journal des decisions, le commit qui porte l'identifiant de la tache.
> 6. **PASSER A L'ETAPE SUIVANTE** et recommencer.
>
> **LE FEU VERT, au cas par cas selon le risque** *(arbitrage du 20/09)* :
>
> | | |
> |---|---|
> | **J'enchaine sans attendre** | tache additive et reversible : code neuf dormant, lecture, mesure, audit, mise a jour des documents |
> | **J'attends le « vas-y »** | modification de code existant, du run de nuit, des workers |
> | **Accord OBLIGATOIRE, toujours** | ecriture en base de production · ecriture chez Hektor (creer / modifier / supprimer) · lancer un run ou un rattrapage · redemarrer un service · deployer · tout geste irreversible |
>
> ⚠ **UN AUDIT BALAIE LES OBJETS *ET* LES GESTES — regle posee par Frederic le 21/09**,
> apres un audit qui n'avait mesure QUE la modification d'une annonce et avait manque les
> 167 champs de la CREATION. « Tu vas trop vite dans tes audits, il faut les rendre plus
> approfondis. »
>
> **Avant de conclure quoi que ce soit, dresser le tableau, meme s'il est vide :**
>
> |  | creer | modifier | supprimer / archiver | lire / remonter |
> |---|---|---|---|---|
> | **annonce** | | | | |
> | **contact** | | | | |
> | **recherche** | | | | |
> | **relation** (mandant, proprietaire, acquereur) | | | | |
> | **transaction** (offre, compromis, vente) | | | | |
> | **mandat** | | | | |
> | **document / photo** | | | | |
> | **RDV / visite** | | | | |
>
> Une case qu'on ne sait pas remplir se DIT (« non mesure »), elle ne se saute pas. Et si
> l'audit ne porte que sur un objet, l'ecrire en tete : « audit limite a X, les autres ne
> sont pas mesures ».
>
> **Une seule tache en code a la fois.** Les audits peuvent tourner en parallele.
> **Chaque message de travail commence par une ligne de position** : `L0 · C.1' · 2 sur 4`.
> **Rien n'est fini tant que ce n'est pas ecrit dans les documents** : cette conversation
> sera resumee, les fichiers survivent.

---

## 1. Où tu es

Le dépôt est **`C:\Hektor\Projet`**. `C:\Hektor` n'est pas un dépôt git : si une commande
git répond *« not a git repository »*, tu es au mauvais endroit.

| | |
|---|---|
| front | `apps/hektor-v1/` — valider avec `npm run build`, **jamais** `tsc --noEmit` |
| worker | `Console/console_job_worker.js` |
| synchro | `phase2/` |
| API | `backend/` |
| tâches planifiées | `scheduled/` |
| documents de travail | `notice/` — 123 notes |

---

## 2. Où on en est — *à mettre à jour en fin de session*

> **24/09/2026 — `L4-c` EST FAIT, `C.9` EST OUVERT (audit fait, AUCUN code écrit).**
> ➡ `notice/AUDIT_C9_ANNONCE_NEE_DANS_APP_2026-09-24.md` — lire **§4** *(ce que la seconde
> passe a réfuté de la première)* et **§5** *(l'ordre C.9-a → C.9-f et le feu vert de chacun)*.
> **24/09 fin de matinée — C.9 : a, b, c, e1, e2, e3 EN SERVICE, et l'ESSAI RÉEL A RÉUSSI.**
> « ESSAI C9 bis » créée depuis l'app (interrupteur `app_setting.c9_annonce_nait_dans_app`,
> **éteint** hors essai) : ligne **10 000 000**, Hektor **63147**, **un seul numéro** des deux
> côtés, adoptée par le serveur. Détail et chiffres : bloc C.9 de la liste.
> ⚠ **L'ORDRE A CHANGÉ** *(accord de Frédéric)* : **e avant d** — d et f préparent la coupure ;
> **d doit vivre DANS le build** (la clé d'un lien ne se recalcule que pour 57 % des lignes).
> ⚠ **D8** trouvé en auditant e : le rafraîchissement effaçait le numéro de l'app une minute
> après la création → corrigé par e1 + e2.
> ⚠ **Les patchs SQL de production, c'est Frédéric qui les applique** (l'outil est bloqué).
> **EN COURS : le run de jour lancé à 12 h 35, puis la descente** — faire le bilan (C.9-a avant
> le bootstrap, push avec C.9-c, sonde C.9-b après la descente). **Puis C.9-d, dans le build
> (go obligatoire), puis C.9-f.** Deux annonces de test à supprimer plus tard : 63146, 63147.
> ✅ **L4-c-bis CORRIGÉ le 24/09 après-midi** (répété sur copie, 23 fiches réparées, sonde
> `data.contacts_identite` en service) — **à vérifier le 25/09** : les 23 sous leur identité dans
> Supabase. Hors plan noté : C.16 et le registre se contredisent (date « absent depuis » réécrite).
> ✅ **C.9-d CODÉ le 24/09 au soir** — le build tient **le carnet des liens** (`app_relation_registry`,
> recette exacte de chaque clé, doublure lue par personne). Répété sur copie : 100 % des recettes
> refabriquent leur clé. **1re nuit = 24→25 : vérifier la ligne `[carnet des liens]` du build.**
> ✅ **D6 CODÉ aussi** : le recensement « connu de l'app seule » marque ses départs (26 lignes
> périmées ce soir). **Run de jour 16:05-18:09 : C.9-d, D6, L4-c-bis PROUVÉS en réel.**
> ✅ **SECONDE PASSE DU BUILD** (24/09 soir) : un contact neuf ne passe plus une nuit sous son
> numéro Hektor (le run relance le build après le registre, avant le push). Répétée sur copie,
> **en service à la nuit du 25/09** — vérifier la ligne `[seconde passe]`. Reste une mesure : les
> 97 rapprochements laissés sous un ancien numéro sont-ils bien rattachés dans les écrans ?
> ✅ **TABLES SATELLITES** : 13 tables figeaient le numéro du contact (69 rapprochements sans nom).
> Fonction de réparation + appel de nuit + sonde — **APPLIQUÉE le 25/09 à 00 h 07 : 72 lignes
> retraduites, 0 rapprochement sans contact.** Cette nuit : les 30 des 8 contacts neufs.
> ➡ `notice/AUDIT_RAPPROCHEMENTS_NUMERO_CONTACT_2026-09-24.md`
> **25/09 MATIN, À CONTRÔLER** : journal du run (lignes `[seconde passe]`, `[carnet des liens]`,
> « retraduction satellites », « départs marqués »), sondes `data.contacts_satellites`,
> `data.contacts_identite`, `data.annonce_un_numero` à 0. **Puis C.9-f.**
> ✅ **C.9-f CODÉ le 25/09** — l'identifiant d'un lien se fabrique avec **notre** numéro de bien ;
> le carnet fige les existants. **Répétition sur copie : 0 identifiant changé sur 167 496.**
> Deux garde-fous (carnet trop court, trop d'identifiants disparus → le build recommence sans
> substituer). **EN SERVICE à la nuit du 26/09** — vérifier la ligne `[numero de bien dans la cle]`.
> ⭐ **e3 ALLUMÉ LE 25/09 À 08 h 15 PAR FRÉDÉRIC** — `c9_annonce_nait_dans_app = 'on'`.
> **Une annonce créée dans l'app naît désormais avec NOTRE numéro** (la prochaine : 10 000 001).
> Retour arrière : la même requête avec `'off'`, immédiat.
> **IL RESTE : (1) contrôle de la nuit du 26/09 (C.9-f) ; (2) surveiller la 1re annonce réelle
> d'un négociateur ; (3) supprimer les annonces de test 63146 et 63147.**
> ⚠ Connus : le compte formation n'est proposable que depuis l'écran Estimations · un refus
> consomme un numéro.
> ⛔→✅ **L5 AUDITÉ le 25/09 : son gros morceau n'existait pas.** Les « 102 champs d'annonce et
> 40 de contact » sont une **mesure réfutée** — 0 créable sans être corrigible, fait depuis le
> 02/06. **L5 = 6-10 j, pas 2-3 sem** : restent **les photos** *(supprimer, réordonner,
> principale)*, **le mandat existant** *(dates, durée, avenant)*, **la fusion de doublons**
> *(ton arbitrage : app ou admin ?)*. ➡ `notice/AUDIT_L5_GESTES_MANQUANTS_2026-09-25.md`
> ⚠ **Les autres chiffrages du plan n'ont pas été revérifiés** : ordres de grandeur, pas mesures.
> ⛔ **DÉCISION DE FRÉDÉRIC (25/09) : LES DOCUMENTS D'ABORD, LES PHOTOS ENSUITE.**
> · **`D.0`** — arrêté depuis le **23/08** *(33 j)*, 0 en erreur : **arrêté, pas cassé**. Deux
>   trous : blocs **ImmoSign** et **« Mes documents »** sans `force_transfert` *(jamais indexés)* ;
>   signature masquée en connexion **administrateur**. Reprise **déjà conçue** *(empreinte de
>   contenu + « procédure en cours » = 242 annonces)*, derrière le frein anti-bannissement.
>   ⚠ **Ne jamais rejouer les annonces en échec · cadence lente · un 403 arrête tout.**
> · **Les photos** *(noté au plan, après)* : **13 437 vignettes pointent chez Hektor**, 1,7 %
>   rapatriées — et **le serveur n'est lisible ni par Vercel ni par Render**, donc rapatrier ne
>   suffit pas à afficher. **Le chemin d'affichage est un arbitrage de Frédéric.**
> ✅ **Le reste du plan fonctionne** : 36 types de travaux, **0 en erreur**. Les 3 exceptions
>   restent **numéro de mandat** *(`L9`)*, **signature** *(`A.2`)*, **portails** *(`A.1`)*.
> ➡ `notice/AUDIT_DOCUMENTS_ET_ETAT_DES_FONCTIONS_2026-09-25.md` · `notice/AUDIT_PHOTOS_2026-09-25.md`
> *(historique)* **L4-c-bis, trouvé à 14 h 35** : les contacts créés chez Hektor **depuis la bascule** restent
> sous leur numéro Hektor (23 au 24/09) — le registre met l'identité dans `app_contact_id`, le
> build ne lit que `hektor_contact_id`. **DÉCISION DE FRÉDÉRIC (14 h 45) : on le corrige AVANT de reprendre C.9**, registre et
> couche d'un seul geste, répété sur copie : le correctif naïf refait le doublement du 24/09.
>
> · la bascule contact a été jouée le **23/09 à 19h05** *(61 985 contacts sur notre numéro)* ;
> · le premier run d'après a **doublé 294 179 identités** dans le registre local — réparé,
>   cause fermée, contrôle chaque nuit *(`f974ef9`, `376dc7b`)* ; Supabase jamais touché ;
> · vérification complète le 24/09 : **rien de perdu, rien de cassé** *(§6 de la note)*.
>   ⚠ **À revérifier le 25/09 au matin** : 3 contacts encore sous leur numéro Hektor dans
>   Supabase, et l'alarme « critères différents : 1 » de la descente.
>
> ⛔ La section ci-dessous date du 22/09 : elle décrit une bascule **faite depuis**.

> **22/09/2026 (soir) — IL NE RESTE QU'À ALLUMER LA BASCULE** *(`L4-c ⑤`)* : remplir
> `app_contact_identite_app` avec les **356 147 paires**. **Plus une ligne de code à écrire.**
> ⚠ **Trois conditions, toutes écrites dans la liste** : code et données **la même nuit**
> *(le push remplace les 167 459 clés de relation en une fois)* · les **9 liens d'agenda**
> dans la même fenêtre · et **écrire la commande complète et la MONTRER avant de l'exécuter**.
> ➡ `notice/AUDIT_L4C_PORTE_ET_IDENTITE_2026-09-22.md`
>
> **FAIT LE 22/09 :**
> · **`L4-b′` la porte est fermée** *(`a19d9c5`)* — 9 sortants envoyaient un numéro à Hektor
>   sans traduction, dont 5 sans garde-fou ; la traduction était **calculée puis jetée**, et
>   le filtre des mandants **écartait en silence**. Garde-fou : `Console/test_porte_contacts.js`.
> · **`L4-c ⓪` la doublure est montée dans la plage de l'app** *(`2a4e0f0`)* — **194 683
>   numéros** existaient dans les deux séries en désignant des personnes **différentes**.
>   244 834 lignes côté serveur + 463 543 en local, build complet par-dessus, **0 clé changée**.
>   Désormais : **sous 10 M c'est Hektor, au-dessus c'est nous.**
>
> **ET LE 22/09 APRÈS-MIDI, DEUX DE PLUS** *(run réel, 121 min, résultat 0)* :
> · ⛔ **le décalage avait cassé le couloir du registre** — le prochain contact aurait reçu
>   le numéro **1**, et l'INSERT aurait réussi. Puis, le filtre retiré, le registre local et
>   le distributeur Supabase auraient donné **le même numéro à deux personnes**.
>   ➡ **trois étages** : `< 10 M` Hektor · `10 M–20 M` la doublure · `≥ 20 M` l'app.
>   **Prouvé** : 12 contacts livrés ont reçu 10 356 138 à 10 356 149.
> · ⛔ **le run mourait d'impatience** : 4 tentatives en **2,5 secondes**, et un unique 500
>   sur une page d'archives tuait 2 heures de travail. ➡ **2 s · 8 s · 30 s**. Le run
>   relancé est passé. ⚠ **les 403 lèvent toujours immédiatement** — la patience ne vaut que
>   pour les 5xx.
>
> ⚠ **LA LEÇON DE CES DEUX JOURS, et elle vaut pour la suite** : **sept défauts** trouvés —
> par des **essais réels**, des **répétitions sur copie** et les **questions de Frédéric**.
> **Aucun n'aurait planté. Les sept auraient fait des dégâts muets.** Ici, un défaut ne crie
> jamais : il faut aller le chercher. ➡ Ne jamais conclure sans mesurer, ne jamais déployer
> sans éprouver, et **répéter sur une copie avant tout geste irréversible**.
>
> ⚠ **CE QUI COMMANDE CE LOT** : le registre des recherches **bouge avec le contact, pas
> après** — son ancrage est la paire `(hektor_contact_id, rang)`, donc une **position**. Si
> l'identité change sans lui, aucune recherche n'est reconnue le lendemain : 11 368 clés
> neuves, et tout ce qui pend dessous orphelin, **sans un bruit**.
>
> **LE SOCLE EST ÉPROUVÉ.** Run complet + descente rejoués en vrai le 21/09 au soir
> *(20 h 23 → 23 h 14, résultat 0)* :
> couloir des annonces **+7 pour 7 annonces** *(l'ancien défaut donnait +61 235)* ·
> les deux témoins nés dans l'app **ont survécu** alors que leurs jumelles chez Hektor
> n'existent plus · **aucune clé perdue** · **aucun 403 neuf** · **toutes les sondes à zéro**.
>
> ⚠ **DEUX DÉFAUTS INVISIBLES TROUVÉS LE MÊME SOIR**, tous deux dans des étapes
> `Invoke-OptionalStepWithRetry` — qui **n'arrêtent pas le run** et le laissent finir en
> « succès » : un chemin de script coupé par un `\r` (`ab94c9d`), et une colonne manquante
> qui faisait tomber le recensement (`8ee966f`). **Vérifier que ces étapes ont une sonde**
> *(tâche C.17-ter)* — c'est la classe de défaut la plus dangereuse ici.
>
> **`C.9`, la création d'annonce, vient après.** Son audit est déjà fait *(voir le journal
> du plan)* : l'annonce vit déjà sous **son** numéro, donc elle ne peut pas fabriquer deux
> fiches ; ses trous sont `app_mandat_champ_app` et les empreintes de relation.
>
> **Ce qui vient d'être fait, et qui sert de patron.** Un contact **naît dans l'app**, prouvé
> deux fois en réel : identité `10 000 002` tirée de la plage de l'app, case cible `605 453`
> rapportée par le worker, **une seule fiche**. L'essai a trouvé **deux défauts que rien
> d'autre n'aurait trouvés** — la case cible ne partait pas *(un `updated_at` inexistant
> faisait rejeter tout le PATCH)*, et le retour fabriquait **une seconde fiche**.
> ⚠ **La leçon du second, elle vaut pour C.9** : la substitution d'un numéro se fait **à
> l'entrée du build**, jamais au push — les clés des relations et des recherches sont des
> **empreintes calculées sur ce numéro**, et traduire après coup ferait supprimer ces lignes
> au run suivant. `4e82f25` · `13ecedc` · `6cbb59a` · `21565cb`.
>
> ~~**Deux fiches d'essai sont gardées exprès** — `10000001` et `10000002`~~ — **supprimées le
> 22/09** pour libérer la plage *(liste, bloc L4-c ⓪)*. Ces deux numéros sont aujourd'hui la
> **doublure** des contacts Hektor 1 et 2 — ce ne sont plus des fiches d'essai.
>
> ⛔ **Ne jamais relire la section ci-dessous comme un ordre du jour** : elle date d'avant
> le 19/09 et décrit le chantier des transactions, terminé.

> **18/09/2026 — LES TRANSACTIONS SONT PRÊTES.** L'audit global du 18/09 a relu la liste
> `① CE QUI RESTE À FAIRE` contre le code, **rubrique par rubrique, sous les mêmes numéros**
> (C.4, C.4-bis/C.1', C.19-d 3.5, C.17-ter, D.0, 0.3, E.0-bis, A.2). L'ordre avant E.2 est dans
> la **page de tête de la liste** ; on commence par **C.4 : archiver une recherche vise la
> mauvaise** quand le contact en a plusieurs.
> Ce qui suit dans cette section date d'avant le 18/09 : il reste vrai, il n'est plus l'ordre.

**Chantier : `C.19-d` — LE REGISTRE DES TRANSACTIONS.**
⚬ **LA PAGE DE TÊTE DE LA LISTE REMPLACE SA LECTURE** : `notice/LISTE_TACHES_A_COCHER_2026-08-29.md`,
les **57 premières lignes**. Elle porte la tâche en cours, les trois suivantes, ce qui attend
Frédéric, et les renvois par numéro de ligne. Le reste du document est une **archive** : on
l’ouvre à la ligne indiquée, jamais en entier (6 500 lignes).

Cinq phases, à partir de la **ligne 1372**.

```
PHASE 0  mesurer, bloquante        l. 1912   0.1 quasi finie  ·  0.2 0.3 0.4 faites
PHASE 1  le registre, invisible    l. 2328   terminee
PHASE 2  l'ecran                   l. 2903   reste 2.4 (l. 3333), 2.6, 2.7 COTE ECRAN (l. 3556), 26bis-TRANSACTIONS (l. 2906)
PHASE 3  l'ecriture part chez Hektor  l. 3635   EN COURS
PHASE 4  menage                    l. 5290   reste 4.1 (l. 5293), 4.2 (l. 5297)  ·  4.3 faite le 07/09
```

**Au 08/09/2026 — LES TROIS GENRES SONT MODIFIABLES, ET PROUVÉS EN RÉEL.**

```
compromis  50078   165 000 → 175 000, quatre fois · aucun doublon · fiche vérifiée
vente      23301   créée, modifiée 175 000 → 176 500, supprimée · annonce rendue intacte
offre      33050   165 000 → 167 000  ·  33048 REFUSÉE re-acceptée puis re-refusée
```

**Au 10/09/2026 — CE QUE L'API CACHE, LE WORKER LE LIT MAINTENANT.**

Le registre a gagné quatre colonnes tirées de `payload_json` (`mandants_json`,
`notaires_json`, `propositions_json`, `commission_agence`) et le worker ne jette
plus le formulaire de Hektor : à chaque écriture il en tire ce que l'API ne rend
jamais, **sans une requête de plus**, dans `app_affaire_console`.

```
notairesAcquereur[] · notairesMandant[]     0 sur 10 586 par l'API
unitesEntreePercent / unitesSortiePercent   le partage de la commission
conditions suspensives : retenues + CATALOGUE de l'agence
montantHonoraireEntree / tauxHonoraireEntree   le TAUX VENDEUR (manque n°1 de 0.1)
```

Prouvé trois fois en réel sur le compromis 50078, et rejouable hors ligne :
`node Console/test_lecture_console.js` — onze assertions sur du HTML capturé.

⭐ **`2.6` A CHANGÉ DE NATURE.** La piste « la typologie du contact filtre » venait
de quatre mesures ; **le parc la dément à 39 %** — sur 12 446 acquéreurs réels de
compromis, 4 886 ne portent PAS la typologie et sont pourtant attachés. Et la
comparaison console/API sur 649 compromis donne **zéro écart** : l'API ne cache
rien, le défaut est bien à l'ÉCRITURE. L'instrumentation que le dossier réclamait
depuis le 06/09 est posée (ce qui part vraiment, ce que le formulaire garde, ce
que `findProspect` rend). ⚠ Reste l'essai avec deux contacts, jamais fait.

⚠ **LES TROIS ESSAIS « DEUX ACQUÉREURS » (02, 06 et 07/09) UTILISAIENT LE MÊME
  COUPLE**, dont un contact que Hektor n'a jamais attaché. Ils ne prouvent donc
  pas que Hektor n'en garde qu'un.

### Les outils du 10/09

```
Console/lecture_assistant.js                  le lecteur, PARTAGE (extrait du worker)
Console/test_lecture_console.js               11 assertions, N'APPELLE PAS HEKTOR
Console/extract_hektor_compromis_console.js   le rattrapage, LECTURE SEULE
phase2/sync/sync_hektor_compromis_console.py  son pilote, cadence de reference
```

⚠ **LA CADENCE N'EST PAS NEGOCIABLE** : 1 requête par compromis, 0,5 s entre deux,
lots de 100 avec 60 s, vagues de 2 000 avec 300 s. C'est la méthode de
`notice/NOTE_EXTRACTION_CHAUFFAGE_HEKTOR_2026-06-09.md`, la seule qui n'ait jamais
rien déclenché (56 926 lectures). La coquille est écartée pour lire — mesuré le
10/09 : le formulaire arrive identique sans elle, ce qui divise le flux par deux.

**LA TÂCHE OUVERTE est `3.5` — L'ESSAI RÉEL DE LA SUPPRESSION** (liste, l. 5163).

Les cinq pièces sont codées depuis le 07/09 et le journal a été ajouté le 16/09 —
mais il n'avait **jamais été lu** (`request` au lieu de `_request`, corrigé le 17/09
par `bcb05fe`). Sans ce correctif, une suppression ordonnée par l'app **revenait au
run suivant**. Il ne reste que la preuve de bout en bout. ⚠ **Elle écrit chez Hektor
et demande un go explicite.**

**Les deux suivantes** : les **mandants depuis l'app** (lot 3, l. 4018), puis
**2.7 côté écran** (l. 3556) et **2.6** (l. 3412).

⛔ **CE QUE FRÉDÉRIC A MIS DE CÔTÉ**, et qu'on cesse de remonter à chaque tour : les
**2 dettes** (la surveillance qui crie depuis juillet · le numéro de contact qui ne
voyage pas avec sa fiche).

### `3.2e` — la répartition de commission *(détail : liste, section 3.2e)*

⛔ **RIEN NE PART CHEZ HEKTOR** (Frédéric, 14/09, 06bd38b) : leur modèle ne sait pas
exprimer un quart des répartitions réelles — l'acquéreur est suivi par une AUTRE agence
dans 26,6 % des cas. *« Mieux vaut un champ absent qu'un champ menteur. »*
La table existe et elle est remplie ; le reste est **garé**. ✅ Le point 1 — lever
`VenteDateStart` à 2000 — est fait (993dcc5). ⛔ L'étape de conversion reste
**désactivée dans le run** (8456e9f).

**Au 17/09 — LA JOURNÉE QUI A TOUT ÉPROUVÉ D'UN COUP.** `2.7` (couverture mandat
48 % → 74,9 %), `3.3` (le contrat d'autorité vidé), `3.1` (le verdict du carnet), le
chaînage (12 670 chaînes, les 4 copies de la règle d'accord, test ⑤ à 0 écart) et la
note libre d'une transaction. ⚠ **Et un bannissement d'IP à 06:34** : le balayage du
miroir fabriquait un client neuf par pièce, donc 17 logins OAuth en 22 s. Corrigé
(`c524f7e`), **pas encore éprouvé en réel** — le run de 5 h est son juge.

> ⭐ **`0.1` est quasi finie.** Sa phrase *« l'assistant refuse d'avancer sous
> automatisation »* était **fausse** : il refuse un formulaire qu'on ne lui rend pas
> fidèlement. **23 champs de données classés sur 24** ; le dernier,
> `agenceReseauSelected` (la rétrocession), est **hors périmètre par décision de Frédéric**,
> pas par oubli. Reste le relevé de l'offre.
>
> ⚠ **« C » NE VEUT PAS DIRE « il refuse l'écriture ».** Hektor *calcule* le net vendeur et
> la commission si on n'envoie rien — mais **il garde ce qu'on lui envoie, sans vérifier**.
> Il a accepté une fiche à *« 177 345 € »* pour un prix public de 175 000 sans broncher.
> **Rien ne rattrape une incohérence : l'alerte de la modale est le seul filet.**
>
> ⚠ Le risque des **conditions suspensives est LEVÉ** (mesuré le 08/09) : une modification
> les préserve. Le principe *« on repose ce que Hektor a rendu »* les protège sans code.

### Les outils du 08/09 — tous rejouables

```
Console/releve_assistant_etapes.js      l'inventaire des étapes    N'ÉCRIT JAMAIS
Console/mesure_reprise_compromis.js     le formulaire pré-rempli ? N'ÉCRIT JAMAIS
Console/mesure_reprise_panier.js        le panier retient-il l'id ? N'ÉCRIT JAMAIS
Console/campagne_champs_compromis.js    ⚠ LE SEUL QUI ÉCRIT CHEZ HEKTOR
phase2/checks/verifier_regle_chainage.py       les 3 copies de la règle, confrontées
phase2/checks/test_chainage_vente_ferme.py     le correctif du run, sur registre jetable
```

> ⚠ **Il existe deux tâches nommées `0.1`** — celle de la phase 0 (l. 1919) et une autre,
> sans rapport, l. 340.

---

## 3. Avant de coder — la liste de relecture *(plan, l. 378)*

Elle existe *« parce que le 20/08 j'ai oublié trois fois un point déjà documenté »*.

1. La **section du plan** qui concerne la tâche — et ses voisines, les pièges y sont.
2. Les **notes citées** par cette section : elles portent les décisions déjà prises.
3. `notice/*.md` **et la racine**, par mot-clé — 123 notes, dont 111 ne sont citées nulle part.
4. `git log --all --diff-filter=D -- 'notice/*'` — 12 notes supprimées le 19/08 portent
   encore de la doctrine active. **À lancer depuis `C:\Hektor\Projet`.**
5. La **mémoire projet** : `C:\Users\admin\.claude\projects\C--Hektor\memory\`.

**Les trois questions, avant de dire qu'une chose est cassée :**
**Est-ce documenté ?** (ici, ce qui ressemble à une négligence est presque toujours une
décision écrite) · **Est-ce mesuré ?** (mesurer, *puis* conclure) · **Qu'est-ce que j'oublie ?**
(les cas voisins : la recherche supprimée, les contacts, les affaires…)

---

## 4. Ce qui ne se discute pas

- **Lire le CODE, pas les notes**, pour établir un état. *L'inventaire de `C.4` a été faux
  quatre fois parce que la liste ne suivait pas le code — c'est de là que vient l'impression
  de refaire les mêmes choses.*
- **Une mesure approximative vaut une mesure fausse.**
- **Une tâche n'est cochée que si son ÉNONCÉ est couvert**, et la mesure doit répondre à la
  question posée — pas montrer que « ça marche ». *(plan, l. 27)*
- **Ne rien écraser.** Additif et chirurgical, jamais de remplacement massif.
- **Pas de code sans « go » explicite.** Un message court, en cadrage, est une **question**.
- **Stager fichier par fichier.** Jamais `git add .` : 73 fichiers non suivis traînent
  dans le dépôt.
- **Les 5 règles du projet** et **la règle des identifiants** : plan, lignes 2236 à 2270.
  *(un numéro ne se perd jamais · Hektor confirme, il n'écrase pas · une action a une fin
  visible · Hektor reste à jour tant qu'il diffuse · le miroir se met à jour, il ne se
  remplace pas)*

---

## 5. Les adresses

| | |
|---|---|
| le **pourquoi** | `notice/PLAN_DEV_ACTUALISE_2026-08-20.md` (2 278 l.) |
| le **quoi**, item par item | `notice/LISTE_TACHES_A_COCHER_2026-08-29.md` (6 500 l. — lire la page de tête, l. 1-44) |
| le protocole de test en cours | `notice/PROTOCOLE_TEST_STATUTS_TRANSACTIONS_2026-09-01.md` |
| les pièges déjà payés | la mémoire projet (voir §3.5) |

> Ces deux documents pèsent 116 k tokens. **Ne jamais les lire en entier** : ouvrir la
> section concernée par son numéro de ligne, comme ci-dessus.

---

## 6. Pièges d'outillage

- **4 services worker** partagent `console_job_worker.js` : redémarrer **un seul ne suffit
  pas**. Un correctif non redémarré n'est pas actif — plusieurs essais ont été perdus comme ça.
- Le front se valide par `npm run build` dans `apps/hektor-v1` (c'est ce que fait Vercel).
- Vérifier un écran qui « plante » : **la console du déployé d'abord**, la base ensuite.

---

## 7. En fin de session — deux gestes, deux minutes

1. **Mettre à jour le §2** de cette page : la tâche ouverte et son numéro de ligne.
2. **Réécrire la mémoire de reprise** (`reprise-…` dans le dossier mémoire), toujours la même,
   jamais une nouvelle par date. *Elle datait du 02/09 alors que 68 commits avaient suivi.*
