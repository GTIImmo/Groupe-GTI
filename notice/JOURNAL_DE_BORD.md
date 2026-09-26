# Journal de bord — l'historique de la page de tête

> Ce fichier existe pour une raison simple : **la page de tête de `CLAUDE.md` avait grossi
> à 467 lignes sur 609**, et elle portait quatre états datés dont trois étaient marqués
> *« ne jamais relire comme un ordre du jour »*. Un document qui se contredit lui-même ne
> tient plus le fil.
>
> **Ce qui est ici est de l'HISTOIRE, pas un ordre du jour.** On l'ouvre pour comprendre
> *pourquoi* une décision a été prise, jamais pour savoir quoi faire. Le présent est dans
> `CLAUDE.md` §2 ; le détail par tâche est dans `notice/LISTE_TACHES_A_COCHER_2026-08-29.md`.
>
> Déplacé ici le 26/09/2026. Rien n'a été récrit : les blocs sont tels quels, du plus
> récent au plus ancien.

---

## 25/09/2026 — *l'ancienne page de tête de la liste (`C.9` / `L4-c-bis`, jour par jour)*

> Déplacée ici le 26/09. Elle annonçait *« tenir à jour, 15 lignes, rien de plus »* et en
> faisait **192**, dont 130 de journal — et elle était arrêtée au **25/09 à 00 h 10**,
> donc elle ignorait le chantier des documents et des photos. Le détail par tâche vit
> dans la section `C.9` de la liste ; ceci est la trace des mesures, dans l'ordre.


> **Mis à jour le 25/09/2026 (00 h 10).** Cette page remplace la lecture du document. Le reste est une
> archive qu'on ouvre **par numéro de ligne**, jamais en entier.

```
OU ON EST, EN TROIS NIVEAUX

  ETAPE 2       L0 OK  L1 OK  L2 OK  L3 OK  L4 EN COURS   puis L5 L6 L7 L8 L9
  L4            L4-a OK  L4-b OK  L4-b' OK  L4-c OK  C.9 EN COURS
  L4-c          (0) OK (1) OK (2) OK (3) OK (4) OK  (5) OK -- BASCULE FAITE 23/09 19h05
  C.9           a OK  b OK  c OK  e1 OK  e2 OK  e3 OK (eteint) -- ESSAI REEL OK 24/09
                RUN DE JOUR 12:35 + descente : OK (1 numero des deux cotes, 0 ecart)
                d OK + D6 OK : PROUVES au RUN DE JOUR 24/09 16:05-18:09 (code 0, 0 403)
                SECONDE PASSE du build : 1re nuit 25/09 -> « 0 contact a traduire, rien
                  n'est ecrit » en 1 s (aucun contact neuf chez Hektor cette nuit : le
                  registre annonce « a numeroter 0 »). Le chemin inerte est prouve ; le cas
                  AVEC un contact neuf reste a voir en reel (sur copie le 24/09 : 8/8)
                ORDRE DECIDE 24/09 soir (Frederic : « Oui, d'abord le plan ») :
                  (1) ✅ FAIT : les rapprochements n'etaient PAS rattaches -> audit
                      (notice/AUDIT_RAPPROCHEMENTS_NUMERO_CONTACT_2026-09-24.md),
                      fonction de retraduction des 13 tables satellites + appel de nuit
                      + sonde ; APPLIQUEE 25/09 00:07 : 72 lignes retraduites, 0
                      rapprochement sans contact (bloc L4-c-bis ci-dessous)
                  (2) ✅ FAIT le 25/09 : C.9-f code, 15/15, repete sur copie -> 0 cle
                      changee ; EN SERVICE a la nuit du 26/09 (le run de 05:00 lit le
                      fichier). (ancien libelle ci-dessous)
                  (2) C.9-f : audit -> explication -> code -> repetition sur COPIE
                      (le carnet EXISTE dans la vraie base depuis le run de 16:05 :
                      plus besoin d'attendre une nuit). Attendu : 0 cle changee.
                      Si 0 sur la copie -> en service DES LA NUIT du 25/09, en meme
                      temps que la seconde passe (chacune sa ligne au journal).
                  (3) 25/09 matin : controle de la nuit (seconde passe, carnet, D6,
                      retraduction satellites = les 30 des 8 neufs, sonde
                      data.contacts_satellites, sondes a 0)
                  (4) decision de Frederic : allumer e3 pour de bon
                ➡ notice/AUDIT_C9_ANNONCE_NEE_DANS_APP_2026-09-24.md · detail : bloc C.9
  L4-c-bis      ✅ CORRIGE 24/09 (code e414fe0 + 23 fiches reparees 15:4x, go de Frederic)
                repetition sur COPIE de la vraie base : registre -> build -> registre :
                23 traduits, 5 liens et 4 recherches suivent (cles IDENTIQUES), 0 second
                numero, controles a 0. Reel : 23 lignes reparees en transaction verifiee ;
                le build traduira cette nuit (605491 -> 10650346). Sonde data.contacts_
                identite INSCRITE (critical, prouvee : mal rangee / bloque > 36 h / ok).
                ✅ VERIFIE au run de jour du 24/09 (16:05-18:09) : dans Supabase, les 10
                qui y sont (contacts eligibles) sont sous leur identite, 0 sous l'ancien
                numero, 0 ancienne cle de lien ; les 13 autres n'y ont jamais ete (non
                eligibles). Regles mal rangee / desaccord : 0 / 0. 8 contacts NEUFS du jour
                (605514-605521) passent une nuit sous leur n° Hektor -- ⛔ PAS « normal » :
                ➡ SECONDE PASSE DU BUILD (24/09 soir, « Oui » de Frederic). Le run fait
                  build -> registre -> push : le registre numerote les contacts neufs
                  APRES le build, qui les a ecrits sous leur n° Hektor ; ils partaient
                  vers Supabase sous ce numero et changeaient d'identite le lendemain,
                  laissant derriere eux ce que l'app leur avait accroche (mesure : 67
                  rapprochements des contacts L4-c-bis encore sous l'ancien numero ;
                  30 pour les 8 neufs). Depuis la bascule du 23/09 seulement.
                  Correctif : le run relance le build APRES le registre, AVANT le push,
                  avec --seulement-si-contacts-a-traduire (0 -> s'arrete sans rien ecrire).
                  Non bloquante, 1 essai. ~4 min les jours ou il y a des contacts neufs.
                  test_seconde_passe_contacts_neufs.py 7/7 ; PREUVE sur cc9010f : echoue.
                  REPETITION sur COPIE de la vraie base (8 neufs a traduire) : 211 s,
                  8/8 traduits, leurs 5 recherches gardent LEUR cle, 0 autre lien ni
                  recherche change, carnet 100 % / 0 conflit ; registre derriere : 0
                  second numero ; 2e passe : « 0 a traduire », rien ecrit. Vraie base
                  intacte. EN SERVICE a la nuit du 25/09.
                  [ ] A COCHER apres la nuit : ligne « [seconde passe] » au journal,
                      et au run suivant « contacts a traduire » = 0 avant le build.
                  [x] MESURE (lecture, 24/09 soir) : NON, ils ne sont PAS rattaches.
                      - app_upsert_one_rapprochement : ON CONFLICT met a jour le score,
                        JAMAIS hektor_contact_id -> un rapprochement ne sous le n° Hektor
                        le garde pour toujours.
                      - app_get_rapprochements_for_dossier : LEFT JOIN contact PAR CE
                        NUMERO -> ligne affichee SANS nom/email/tel/nego ;
                        app_count_rapprochements_for_contact : filtre PAR CE NUMERO ->
                        le compteur « N biens » de la fiche ne les compte pas ;
                        app_generate_rapprochement_alerts : meme jointure.
                      - Parc entier : 69 lignes / 5 contacts sous un ANCIEN n° Hektor
                        (tous eligibles), 0 action de negociateur dessus ; 50 135 bons.
                        + les 30 des 8 neufs deviendront orphelins CETTE NUIT (traduits).
                      - C'etait une table « figee » de la bascule du 23/09 (13 tables
                        traduites a la main, que le build ne refait pas).
                  [~] REPARATION CODEE 24/09 soir (« Oui ») -- audit complet :
                      notice/AUDIT_RAPPROCHEMENTS_NUMERO_CONTACT_2026-09-24.md
                      supabase/patch_retraduire_satellites_2026-09-24.sql : fonction
                      app_contact_retraduire_satellites(p_appliquer) sur les 13 tables
                      figees ; a blanc par defaut ; saute+compte ambigus / contradictoires
                      / collisions (4 index uniques) ; « le compte doit tomber juste »
                      (ecarts) ; trace app_contact_retraduction_log ; service_role seul.
                      PREUVE sur copies temporaires annulees (vraies donnees + 6 cas
                      pieges) : 1re passe a trouve MON defaut (17 lignes ni traduites ni
                      comptees : app_contact_id VIDE sur 10 fiches -> NULL) ; corrigee ;
                      2e passe : 74 traduites (69 + 3 compteurs + 2 pieges), 3 sautees,
                      0 ecart, rejeu = rien, 0 rapprochement sans contact ; prod intacte.
                      Appel de nuit : propager_numeros_contact.py AVANT la propagation,
                      protege (fonction absente -> l'etape continue). Sonde
                      data.contacts_satellites (a blanc : ecart critical, reste warning).
                      test_retraduire_satellites.py 9/9 ; PREUVE sur cb711df : echoue.
                      [x] APPLIQUE 24/09 ~23:50 par Frederic (empreinte du corps installe
                          = celle du fichier, 50c8da99…, aux fins de ligne pres). A blanc :
                          72 traduisibles, 0 saute, 0 ecart. Pour de bon (00:07, go de
                          Frederic, l'etape de nuit elle-meme) : 72 traduits (69 + 3).
                          Apres : 0 rapprochement sans contact sur 50 204, 0 desaccord de
                          colonnes, rejeu a blanc = 0, trace 1 ligne ; l'ecran du bien
                          1379038 affiche de nouveau « M. Jeremy KUPKOWSKI » (10650346).
                      [x] NUIT DU 25/09 (run 05:00-06:55, exit 0) : « retraduction
                          satellites (applique) : a traduire 30, traduits 30, sautes 0,
                          ecarts {} » -> 0 rapprochement sans contact sur 50 207 ; sonde
                          a blanc = 0 ; trace 2 lignes (72 le 24/09, 30 le 25/09).
                          ⚠ NOTE : la propagation qui suit a rempli 4 app_contact_id (dont
                            3 rapprochements) -- les DEUX etapes servent, dans cet ordre.
                      ⚠ HORS PLAN NOTE : 10 fiches de app_contact_current (Supabase) sous
                        identite ont app_contact_id VIDE (les contacts L4-c-bis) --
                        pousser_numeros_contact ne les a pas remplies. Non traite.
                  (ancien) REPARATION a decider par Frederic (ecriture prod = son geste) :
                      UPDATE app_rapprochement -> identite, via hektor_target_id, APRES
                      la nuit du 25/09 (couvre 69 + 30). + garde durable a discuter
                      (le moteur met a jour hektor_contact_id, ou re-traduction des
                      tables figees apres le push). La seconde passe empeche les
                      NOUVEAUX cas ; elle ne repare pas les anciens.
                ⚠ HORS PLAN, trouve en passant : C.16 et le registre se contredisent --
                  le registre leve chaque nuit les 7 658 marques « disparu » de C.16
                  (contacts supprimes chez Hektor mais toujours dans la couche), C.16
                  les repose aussitot : etat final juste, mais la date « absent depuis »
                  est reecrite chaque nuit. Preexistant (l'ancienne regle faisait pareil).
  (historique)  TROUVE 24/09 14:35
                Tout contact cree chez Hektor DEPUIS LA BASCULE reste sous son numero
                Hektor, indefiniment : 23 au 24/09 (~10 de plus par jour).
                Cause : registre_contacts.py l. 232 inscrit le n° Hektor dans la colonne
                hektor_contact_id (qui porte l'IDENTITE depuis le 23/09) et l'identite
                dans app_contact_id ; build_contacts_layer.py l. 357 ne lit QUE
                hektor_contact_id -> pour eux cible = identite -> jamais traduits.
                ⚠ Correctif naif (lire app_contact_id) = la couche passe sous 10650346,
                  le registre ne la reconnait plus (il cherche 605491) -> SECOND numero :
                  le mecanisme exact du 294 179 du matin. Registre ET couche d'un geste.
                ⚠ Le controle de nuit est AVEUGLE a ce cas (il ne cherche que les
                  doublons) : ajouter « n° d'app attribue mais n° Hektor en identite ».
                ⚠ Ce matin j'avais dit « decalage de 24 h » : c'etait faux.
```

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
> ✅ **`D.0 ①` LE MANDAT / L'ANNEXE EST RÉGLÉ (25/09).** Sous le nom « Mandat », 88 annonces
>   n'affichaient que l'**annexe** (197 Ko) ou le **barème** : l'archive ImmoSign contient DEUX
>   pdf et `extractPdfFromZip` prenait **le premier**. Correctif `19d7a33` *(on écarte
>   annexe/barème, sinon le plus gros)*, prouvé sur **120 archives réelles** — l'ancienne
>   version en choisissait 28, la nouvelle 0. **4 services redémarrés à 13 h 09.**
>   Rattrapage `Console/rattrapage_mandat_signe.js` passé par Frédéric : **88 rattrapés,
>   0 restant**, taille moyenne 1,00 Mo, 0 écart taille ↔ métadonnée, l'ancien PDF tracé dans
>   `annexe_ecartee`. ⚠ **Il doit tourner dans un PowerShell ADMINISTRATEUR** : ces fichiers
>   appartiennent au service (LocalSystem), `BUILTIN\Utilisateurs` n'a que `(RX)` dessus —
>   créer un fichier passe, l'écraser non. *(Ce n'était PAS le bac à sable : même refus sans lui.)*
> ⛔⛔ **`D.0 ②` — LE VRAI CHANTIER : LE RATTRAPAGE EST À 29,5 %, PAS À 97 %.**
>   ⚠ **Ma 1re mesure était fausse par omission** — elle ne portait que sur `daily-cloud`
>   (13 437 annonces) alors que le parc en fait **58 140**. *Frédéric l'a relevé : « tu es
>   juste sur le périmètre des annonces de l'app et pas les archives ».* **Même classe
>   d'erreur que L5 : une liste partielle prise pour la liste entière.**
>   ➡ `notice/AUDIT_RATTRAPAGE_DOCUMENTS_2026-09-25.md`
>
>   | périmètre | annonces | empreinte | lue sans empreinte | **jamais lue** |
>   |---|---:|---:|---:|---:|
>   | archive | 35 299 | 4 055 | 4 531 | **26 713** |
>   | courant | 13 437 | 13 068 | 17 | 352 |
>   | historique | 8 920 | 26 | 0 | **8 894** |
>   | brouillon | 484 | 0 | 0 | **484** |
>   | **total** | **58 140** | **17 149** | 4 548 | **36 443** |
>
>   Le rattrapage a tourné du 18 au 23/08 (scope `archive`, **10 786 jobs**, `lot: empreinte`)
>   puis s'est **arrêté** — pas échoué : **0 en erreur**. Le 20/08 à 10 h 08, `7143a1a` posait
>   le frein : *« notre IP a été bannie »*.
>   **Débit mesuré** : 877/h avant le frein, **594/h après** → **36 443 ÷ 594 ≈ 61 h**.
>   ⭐ **L'OUTIL EST `Console/enqueue_empreinte_lot.js`** *(21/08, lots de 3 000)*, PAS
>   `enqueue_console_sync_jobs.js` sans `--detect` — celui-ci ne saute que les jobs
>   `pending`/`running`, jamais les `done`, et ré-empilerait les 3 000 premières déjà faites.
>   Ses 3 exclusions : empreinte posée · **job en erreur = NE JAMAIS REJOUER** · déjà en file.
>   Reprise **par identifiant**, jamais par position.
> ✅ **① FAIT (25/09, `3f2c203`) — l'empreinte porte enfin NOTRE numéro.**
>   `app_console_document_fingerprint` était la **seule** table de la chaîne documents sans
>   numéro d'app *(sa clé primaire EST `hektor_annonce_id`)* et **absente de `REPOINT_TABLES`**,
>   alors que document / photo / job y sont. C'est **le carnet du rattrapage** : une ligne
>   laissée sous un dossier fantôme ferait refaire les 61 h.
>   ⚠ **GARDE DE FRÉDÉRIC : « ne pas casser les workers qui ont besoin des id hektor ».**
>   Tout est **additif** : clé de conflit inchangée, numéro Hektor toujours envoyé, les 3 autres
>   points d'appel intacts, appel à 2 arguments n'écrase rien. Patch appliqué par Frédéric :
>   **17 149/17 149 remplies, 0 incohérence**, clé primaire toujours `hektor_annonce_id`.
>   Garde-fou `Console/test_empreinte_numero_app.js` *(12 contrôles, prouvé au rouge)*.
>   **Workers redémarrés à 14 h 13, APRÈS le patch.**
> ✅ **② FAIT (25/09) — la détection freine et s'arrête au 403.**
>   `enqueue_console_sync_jobs.js` lisait Hektor avec un `fetch` **nu** : **aucune cadence**
>   *(mesuré : 0 ms entre 3 lectures)* et un **403 avalé** puis `continue` — la mécanique exacte
>   du bannissement. Désormais : même frein que le worker, **piloté par les mêmes variables
>   d'environnement** *(un seul réglage, pas deux vérités)*, et `ArretBalayage` sur
>   401/403/429/503, session morte, connexion refusée. Un **500 ou un timeout isolé** continue
>   de passer sans rien conclure. Ce qui est déjà trouvé **est quand même enfilé**.
>   Garde-fou `Console/test_frein_detection.js` *(15 contrôles, prouvé au rouge deux fois)*.
> ⭐⭐ **25/09 SOIR — L'AJOUT DEVIENT AUTONOME (lots 1, 2a, 2b faits, DORMANTS).**
>   *Remarque de Frédéric : « les documents photos attendent toujours une confirmation de
>   Hektor avant de sauvegarder, contrairement au reste du dev comme contact ». Exact.*
>   Contacts, annonces et recherches ont leur couche optimiste ; **documents et photos
>   étaient les deux SEULES entités à exiger Hektor pour exister**. À la coupure, ajouter
>   un document depuis l'app aurait **cessé de fonctionner** — absent des 3 exceptions.
>   **L'INVERSION** : notre serveur d'abord, Hektor ensuite. Si Hektor ne répond pas, le
>   document existe quand même — dans l'app et chez nous.
>   · **lot 1** (`7428303`) : base *(3 colonnes + index partiel × 2 tables, appliquées)* +
>     `completerEnvoiDocumentDiffere`. L'envoi Hektor **extrait et partagé** ; l'ordre du
>     chemin d'origine **préservé à l'identique**. 18 contrôles, rouge prouvé 2×.
>   · **lot 2a** (`db5c38c`) : la jumelle photo. ⚠ Préalable levé : `hektor_photo_id` était
>     **NOT NULL** — l'app ne pouvait pas créer une photo avant l'envoi. Contrainte retirée,
>     unicité conservée *(les NULL y sont distincts)*, 1 397 photos intactes. 25 contrôles.
>   · **lot 2b** (`ec838b2`) : `Console/reprendre_envois_hektor.js`. **Il ne s'acharne pas** —
>     respiration 15 min, pas de repose par-dessus une file, et un échec de +24 h est
>     **signalé et sort en 1**. Le tri est une fonction pure. 14 contrôles.
>   ⚠⚠ **VÉRIFIÉ AVANT D'ÉCRIRE, c'était le risque qui pouvait tout arrêter** : une ligne
>   **sans numéro Hektor SURVIT à la synchro de nuit**. Les deux nettoyages ne suppriment
>   que des lignes qui *ont* un numéro Hektor devenu obsolète.
> ⛔ **LOT 2c BLOQUÉ SUR UN PRÉALABLE DE SÉCURITÉ (25/09 au soir)** : le front n'a que
>   **SELECT** sur `app_console_document` et `app_console_photo` — il ne peut créer qu'un
>   *travail*. **C'est précisément pourquoi le schéma est « Hektor d'abord ».** Il faut une
>   **RPC SECURITY DEFINER** *(patron de la signature manuscrite)* qui crée la ligne pour le
>   front — **et qui vérifie que le négociateur a accès à l'annonce**, sinon n'importe qui
>   dépose un document sur n'importe quel bien. **À faire de tête reposée.**
> ✅ **ET LA FUITE EST BOUCHÉE** (`c95cb9b`) : une photo ajoutée depuis l'app est enfin
>   **gardée sur le serveur** (+ Supabase si l'annonce est vivante), comme les documents le
>   font depuis des mois. Best-effort et bruyant : lever ferait rejouer le travail donc
>   **renvoyer la photo**, et Hektor en aurait deux. Explique les 42 photos « en attente ».
> ✅ **MATTERPORT** (`80676d0` + patch appliqué) : 4 484 groupes portent nos deux numéros,
>   **0 incohérence**, l'identifiant **intact** *(les 5 049 scans y pendent)*, et le run le
>   recalcule à chaque passage. ⚠ Il ne parle JAMAIS à Hektor — vérifié.
> ⭐ **PHOTOS — le rapatriement est prêt** (`3c17057` + `f27f9b5`) : **444 431 photos**, dont
>   **435 166 à faire**, **~110 Go**, **~7 h** à 17/s. ⚠⚠ **LES ADRESSES SONT DÉJÀ CHEZ NOUS**
>   (miroir local, `hektor_annonce_detail.images_json`) → **le rapatriement ne touche JAMAIS
>   Hektor** et peut tourner en parallèle du rattrapage documents. *(Les « 13 nuits de quota »
>   que j'annonçais n'existent pas — je n'avais pas appliqué la règle « chercher d'abord en
>   local ».)* Calibré sur 900 téléchargements, **0 refus**. ⚠ **Échéance : AVANT la coupure**,
>   après quoi le CDN ne sert plus rien. ➡ `notice/AUDIT_PHOTOS_2026-09-25.md`
> ⚠⚠ **ET LA LEÇON DU JOUR, écrite parce qu'elle se répétera** : j'ai corrigé l'empreinte
>   documentaire le matin *(numéro Hektor seul)*, puis écrit l'après-midi un script créant
>   435 126 lignes **avec le seul numéro Hektor**. *« Comment as-tu pu oublier alors qu'on a
>   tout fait pour que tu ne perdes pas le fil ? »* → **j'applique la règle quand j'INSPECTE
>   l'existant, pas quand j'ÉCRIS.** Les garde-fous du projet sont tous tournés vers l'audit.
>   **Il manque une sonde nocturne** : « une table porte-t-elle un numéro Hektor sans le
>   nôtre ? ». ➡ `notice/AUDIT_DEUX_NUMEROS_PARTOUT_2026-09-25.md`
> ⛔⛔ **LE POINT LE PLUS GRAVE, TROUVÉ LE 25/09 AU SOIR : L'APP AFFICHE LES PHOTOS
>   DEPUIS HEKTOR.** Le front lit `photo_url_listing` et `images_preview_json` — des
>   adresses `staticlbi`, donc l'abonnement Hektor. **30 occurrences dans `App.tsx`.**
>   ➡ **Le jour de la coupure, TOUTES les photos disparaissent de l'écran en même temps**
>   *(fiches, listes, vitrine publique)* — **même avec les 110 Go rapatriés sur le serveur.**
>   **Rapatrier remplit le coffre ; ça n'a jamais suffi à afficher.** Preuve côté documents :
>   les 22 023 poussés dans Supabase sont visibles, les 22 493 restés sur le serveur non.
>   ➡ **DEUX gestes** : `P1` verser les vivantes dans Supabase *(~29 Go → 62 sur 100 inclus)*
>   et `P2` faire lire l'app chez nous *(30 points, derrière un interrupteur, repli sur
>   l'adresse Hektor tant qu'elle répond)*. **`P2` est le seul point dont l'échéance est la
>   coupure elle-même — il ne se rattrape pas après.**
>   ➡ **LA LISTE COMPLÈTE, D1→D8 et P1→P8** : `notice/RESTE_A_FAIRE_DOCUMENTS_PHOTOS_2026-09-25.md`
>   *(ajouter et supprimer exigent encore Hektor · l'état ne suit pas dans les deux sens :
>   2,2 Go bloqués, ×4 en 5 semaines · le repassage n'est branché nulle part · supprimer /
>   réordonner / photo principale n'existent NI chez nous NI comme commandes Hektor connues)*
> ⛔ **IL RESTE :**
>   ③ **relancer le rattrapage** — `enqueue_empreinte_lot.js`, lots de 3 000, archive →
>      historique → brouillon. **~61 h.** *(go de Frédéric obligatoire)*
>   ④ `run_full_pipeline.ps1:1033` n'appelle **jamais `--detect`** → le drapeau ajouté tel quel
>      empilerait tout le périmètre chaque nuit ; et l'étape est **bloquante** (`throw`) alors
>      que ses voisines sont en `Invoke-OptionalStepWithRetry` : une session morte tuerait
>      Matterport, les **liens publics de RDV**, **la vitrine**, l'export Android ;
>   ⑤ **Frédéric** : allumer `-EnqueueConsoleDocuments` dans `run_quotidien.ps1`.
>   ▫ petit : **53 documents sur 4 annonces** (49540, 33151, 61654, 35884) portent un
>      `app_dossier_id` absent des 4 index.
>   ✅ Vérifié sain : les 4 séries d'index partagent **une seule** numérotation, **0 collision
>      sur 58 140** ; documents et photos portent les deux numéros à 100 % ; le front lit par
>      `app_dossier_id` ; les actions vers Hektor passent par `hektor_annonce_id`.
> · **Les photos** *(noté au plan, après)* : **13 437 vignettes pointent chez Hektor**, 1,7 %
>   rapatriées — et **le serveur n'est lisible ni par Vercel ni par Render**, donc rapatrier ne
>   suffit pas à afficher. **Le chemin d'affichage est un arbitrage de Frédéric.**
> ✅ **Le reste du plan fonctionne** : 36 types de travaux, **0 en erreur**. Les 3 exceptions
>   restent **numéro de mandat** *(`L9`)*, **signature** *(`A.2`)*, **portails** *(`A.1`)*.
> ⚠⚠ **LA VITRINE PUBLIQUE ET LES 2 SYSTÈMES DE RDV** *(signalés par Frédéric le 25/09,
>   absents de tous mes audits alors que ce sont 2 étapes du run)* : hébergement GitHub sain,
>   **2 227 liens publics ont déjà jeton + notre numéro**, RDV Google aux deux numéros. Mais la
>   vitrine fabrique ses liens avec le **n° Hektor**, le service **retombe sur `hektor_annonce_id`**
>   après le jeton, et la **fiche visite PDF vient de Hektor**. ⚠⚠ **Liens PUBLICS déjà diffusés
>   (QR, imprimés) : recouvrement, PAS remplacement** ➡ `notice/AUDIT_VITRINE_ET_RDV_2026-09-25.md`
> ⚠⚠ **TROIS TRAVAUX ONT UNE DATE DE PÉREMPTION, pas seulement une priorité** : **`L9`**
>   *(le registre se remplit depuis le miroir)* et **`C.9-couple`** *(seul moment où l'on peut
>   comparer NOTRE paire à celle de Hektor — l'app envoie le conjoint, c'est **Hektor** qui crée
>   la 2ᵉ fiche et pose le lien ; à la coupure, personne ne le fera)*. **Son 1er pas est une
>   MESURE d'1 h** : créer un couple d'essai et regarder si Hektor fait une fiche ou deux.
>   **Et la vitrine / les liens publics de RDV** *(ci-dessus)* : l'ancienne forme doit survivre
>   pendant que Hektor vit. *(Les deux rappelés par Frédéric le 25/09 — je les avais omis.)*
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
