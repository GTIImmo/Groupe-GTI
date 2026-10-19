# LES LEÇONS DE MÉTHODE — *déménagées de `CLAUDE.md` §2 le 19/10/2026*

> ⚠ **LES NUMÉROS SONT CONSERVÉS**, et ce n'est pas cosmétique : le code, les commits et les
> autres notes y renvoient par leur numéro *(« leçon 30 », « la règle n° 4 de cette page »,
> « même famille que la leçon 23 »)*. **Ne jamais renuméroter.** Une leçon neuve prend le
> numéro suivant, 32.
>
> **Pourquoi elles ont déménagé** : elles pesaient **14 576 caractères** dans une section qui
> s'annonce *« une page, pas une archive »* et qui doit porter **le présent**. Le §2 était monté
> à **79 966 caractères, 91 % de `CLAUDE.md`**.
>
> ⭐ **Les six qui servent au chantier en cours sont rappelées dans `CLAUDE.md` §2**, en une
> ligne chacune. Celle-ci est la source complète.

---

1. ⭐ **Mesurer LE GESTE DE L'ÉCRAN, pas un geste plausible.** Trois fois le 12/10 j'ai cru à
   une avarie grave en comptant des lignes que l'app ne compte jamais *(l'écran lit les
   affaires et les photos **par annonce**, compte les contacts en **estimé** et les annonces en
   **exact**)*. **Lire comment l'écran lit, avant de crier.**

2. ⭐ **Une répétition vérifie les DEUX SENS** : que la nouvelle phrase **apparaît** *et* que
   l'ancienne **disparaît** ; et qu'un patch **a changé quelque chose**, pas seulement que
   l'inverse revient. *(Mémoire : « répétition : le témoin inverse ».)*

3. ⭐ **Modifier une fonction sans rien écraser** : le patch ne **recopie** pas la fonction, il
   la **lit dans la base**, vérifie son empreinte *(sans les retours chariot)*, contrôle que
   **l'ancre est unique**, insère après elle, réexécute.

4. ⭐ **Contrôler un droit sans mot de passe**, en empruntant l'identité, en lecture seule :
   `BEGIN; SET LOCAL ROLE authenticated; SET LOCAL request.jwt.claims = …'{"sub":"<uuid>"}'…;`
   puis des lectures, puis `ROLLBACK;`

5. ⭐ **Une règle de lecture doit sortir ses parties constantes** : `(select f())` est évalué
   **une fois**, `f()` **une fois par ligne** — 8,15 s contre 0,076 s pour un déplacement de
   parenthèses.

6. ⭐ **`service_role` porte `rolbypassrls`** → **aucune règle RLS ne peut casser** les
   workers, le backend, `phase2`, le run ni les crons. À ressortir chaque fois que la question
   se pose.

7. ⭐ **Un remplacement en masse ne se relit qu'en le faisant IMPRIMER** : lignes changées
   **et** lignes gardées avec leur raison. C'est ainsi que 3 défauts sont sortis.

8. ⚠ **Ne jamais conclure « le déploiement est cassé » juste après un push** : sonder en
   boucle, puis parler. *(Render `/health` rend le commit ; pour Vercel, chercher une chaîne
   neuve dans `/assets/index-*.js`.)*

9. ⭐⭐ **UNE CAUSE STRUCTURELLE SE BALAIE DANS TOUTE SA FAMILLE** *(12/10)*. Le 08/10, 5a a
   réparé « désarchiver » pour les archives — **une case sur huit**, alors que les 7 autres
   partageaient la même supposition *(« le bien est dans `app_dossier_current` »)*, fausse
   depuis le 20/05 pour **44 259 biens**. **Ce que Frédéric signale est un symptôme, jamais
   le périmètre.**

10. ⭐ **LE NOM D'UNE COLONNE MENT — et une mesure peut être une tautologie.** `app_archive_id`
   / `app_historical_id` **sont** `app_dossier_id`, renommés. J'avais conclu l'inverse d'un
   « 0 archive n'existe comme `app_dossier_id` » qui ne disait que *« aucune archive n'est
   dans la table des vivants »* — **la définition d'une archive**. Vérifier par un **second
   chemin** *(ici : les anciens travaux du même bien)*.

11. ⚠ **L'ÉCRAN PEUT PORTER UNE RÈGLE QUE LA BASE IGNORE.** L'écran a trois états
   *(vivant · index sans détail · index avec détail)*, les RPC n'en connaissaient qu'un :
   le bouton restait affiché et échouait en jargon. **Avant de corriger une fonction, lire
   ce que l'écran promet.**

12. ⚠ **Deux règles PostgreSQL** : deux règles « permissive » se combinent en **OU** *(ajouter
   une règle stricte à côté d'une large ne cloisonne rien — il faut remplacer)* · et une **vue**
   n'applique les règles des tables qu'avec `security_invoker`.

13. ⭐⭐ **UNE SENTINELLE QUI CRIE AU LOUP N'EST PLUS UNE SENTINELLE** *(13/10)*. « le push
   n'est pas passé » revenait **chaque matin depuis le 08/10** et repartait seul deux heures
   plus tard : le moniteur passe à 07:48, entre le push *(06:56)* et la descente de la doublure
   *(~07:58)* — il comparait **le registre du matin à la copie de la veille**. **Quand on ne
   peut pas savoir, on dit « non concluant », on ne crie pas** — et le vrai rouge reste intact.
   ⚠ Et **un rouge quotidien n'est pas forcément de mon fait** : l'historique des alertes le
   datait d'avant mon travail. *(`notice/SENTINELLE_MANDAT_FRAICHEUR_2026-10-13.md`.)*

14. ⚠ **DEUX DATES NE SE COMPARENT PAS COMME DEUX TEXTES.** `app_mandat.last_seen_at` est en
   **UTC**, `sb_pull_state.derniere_descente` est **locale sans fuseau écrit** : comparer les
   chaînes rendait l'**inverse** de la vérité, à **deux heures** près.

15. ⭐⭐ **CHERCHER SI LE PROJET A DÉJÀ TRANCHÉ — avant de proposer une forme.** Le 13/10,
   Frédéric a demandé « une colonne supplémentaire » : ce patron tournait **déjà dans la vue
   que je venais de lire** *(photos : `COALESCE(x_app, x)` + les deux colonnes nues + une
   **re-pose après le push**, 24 497 lignes sur 24 505)*. J'avais proposé une jointure — que
   la **RLS à 0 politique** rendait impossible. **Il avait la bonne forme avant moi.**

16. ⚠⚠ **NE PAS RELIRE SA PROPRE ÉCRITURE COMME SI ELLE FAISAIT AUTORITÉ.** Le worker écrivait
   notre date dans **la colonne de Hektor** *(« confort d'affichage, sans autorité »)*, et le
   magasin relisait **ce même registre** comme « ce que dit l'app ». **La boucle était fermée** :
   4 fausses « décisions de l'app », et **deux de mes comptages faux** *(« 0 sur 2 » puis
   « 4 sur 7 » — le vrai était 0 sur 3)*. ➡ **Toujours demander : qui a ÉCRIT cette valeur ?**
   Une colonne « ce que dit l'app » qui est aussi écrite par l'app ne prouve rien.

17. ⚠ **UN TÉMOIN NE DOIT PAS DÉPENDRE D'UNE TABLE QUE L'ÉPREUVE MODIFIE.** Mon témoin inverse
   a rendu `117 / 117 / 118` : l'épreuve d'effacement supprimait la ligne de carnet qui servait
   à **exclure** ce couple du décompte. Le patch était sain ; **la mesure était mal bâtie**.
   ➡ **Figer la liste des exclus AVANT les épreuves.**

18. ⭐ **AVANT DE CRIER À LA PERTE, REGARDER SI LA LIGNE EST UN BIEN D'ESSAI.** Le 13/10 j'ai
   bâti une alerte complète *(« une ligne du coffre a disparu, rien ne l'explique, sentinelle à
   poser »)* sur la clôture de **62774** — **le bac à sable du projet**, dont les traces sont
   **retirées exprès** *(« Bac a sable 62774 : propre »)*. **Les 2 clôtures réelles sur 2
   étaient intactes.** Les biens d'essai sont listés dans la mémoire de reprise : **62963,
   62774, 284/107, 15633/49544, contact 10355757**. **Les écarter d'abord.**

19. ⚠⚠ **UN HEARTBEAT NON ENREGISTRÉ PART DANS LE VIDE *ET COMPTE POUR UN SUCCÈS*.**
   `monitoring/heartbeat.py` écrit en **`PATCH` FILTRÉ** sur `app_worker_registry` : une clé
   **sans ligne** touche **0 ligne**, reçoit **204**, et `200 <= status < 300` compte un succès.
   Et `check_gti_health` **énumère la table** — donc il ne la regarde jamais. ⚠ **9 des 40 clés
   du run sont dans ce cas**, dont **`phase2.adresses_photos`**, alors que le commentaire du run
   promet le contraire depuis le 27/09 *(→ chantier ④)*. **Poser une étape avec `-WorkerKey`
   n'est PAS la faire surveiller : il faut la ligne de registre.**

20. ⚠ **UN `revoke ... from public` N'ENLÈVE PAS UN DROIT PAR DÉFAUT.** Supabase pose
   `GRANT EXECUTE ... TO authenticated` sur **toute nouvelle fonction** ; ce n'est pas PUBLIC,
   donc le `revoke` le laisse. **Relire `proacl` après avoir créé une fonction** — mon patch
   annonçait « `service_role` seulement » et la base disait autre chose.

21. ⚠⚠ **UN JOURNAL QUI AVALE SON ERREUR NE PROUVE RIEN.** `insertDeletedAnnonceLog` et son
   jumeau contacts journalisent l'échec d'écriture **et laissent la suppression continuer** :
   résultat mesurable, **une de leurs lignes a un `before_json` vide et aucun demandeur** — on a
   détruit sans savoir quoi. ➡ **Pour une trace de geste irréversible, l'écriture de la trace
   est une CONDITION, pas un effet de bord** : elle s'écrit **avant**, et si elle rate, on ne
   détruit pas.

22. ⚠ **UNE COLONNE POSÉE EN BASE NE REMONTE PAS TOUTE SEULE À L'ÉCRAN.** Deux fois le 13/10 :
   la clôture de mandat *(le cockpit lisait la fiche, qui n'a pas la colonne)* et la mention
   « supprimé chez Hektor » *(le `select` du front **nomme** ses colonnes)*. **Après avoir ajouté
   une colonne, chercher le `select` qui doit la porter** — sinon le silence est total.

23. ⭐⭐ **UNE ALERTE DOIT ÉCOUTER LA RÉPONSE DE L'HUMAIN** *(14/10)*. L'écran offrait deux
   boutons pour trancher un geste abandonné, et le rouge ne les regardait pas : Frédéric
   recevait un e-mail **chaque matin pour un problème qu'il avait déjà traité**. ➡ Quand on
   ajoute un bouton « j'ai traité », **chercher toutes les sondes qui comptent la même
   chose** — ici le bandeau et `geste_abandonne` écoutaient, le rouge non.
   ⚠ Et dans le même geste : **ne jamais soustraire des NOMBRES, croiser des IDENTIFIANTS**
   *(les 2 gestes tranchés n'existaient plus : « 2 − 2 = 0 » aurait effacé une vraie alerte)*.

24. ⚠ **UNE COLONNE « dernière exécution » PORTE SOUVENT LE DÉPART, PAS LA FIN**
   *(14/10)*. `sb_pull_state.derniere_descente` **et** `derniere_complete` valent toutes
   deux l'heure de **départ** *(149 lignes sur 154 identiques)*. Mon correctif de la veille
   en a déduit « la Descente a fini » et a gardé un faux avertissement.
   ➡ **Avant de conclure « c'est fini », vérifier que la colonne mesure une FIN.**

25. ⚠⚠ **UN POURCENTAGE ANNONCE SE MESURE SUR LE GESTE FINAL** *(14/10)*. J'ai promis
   « −21 % d'e-mails » en comptant **7 bascules** de `monitor.summary` sur 33. Rejeu du mois
   entier : **14 e-mails avant, 14 après — gain ZERO**. `dispatch` envoie **une** liste, donc
   toutes les bascules d'un même passage partent dans **un seul** e-mail, et le résumé n'a
   jamais basculé seul. ➡ **Mesurer sur ce qui PART, pas sur l'intermédiaire qui lui
   ressemble.** Même famille que la leçon 1. *(Le correctif reste : 7 e-mails plus propres.)*

26. ⚠⚠ **UN SEUIL ABSOLU SUR UN COMPTEUR QUI CROIT EST UNE ALARME A RETARDEMENT**
   *(14/10)*. Frédéric a demandé « monte le seuil » pour deux sondes jamais vertes. Mesure :
   elles montent de **+15,8** et **+2,7 par jour** — un seuil à 2 000 serait franchi dans
   **25 jours**. ➡ **Sur un compteur cumulatif, surveiller l'EMBALLEMENT** *(`rule: "growth"`,
   déjà dans le fichier)*, **pas le total** — et **régler les paramètres sur la vitesse
   mesurée**, jamais sur un chiffre rond. ⚠ Le prix à dire : une dérive **lente** ne sonnera
   plus jamais.

27. ⚠⚠ **UN SEUIL QUI PORTE UN RAISONNEMENT NE SE MONTE PAS « POUR FAIRE TAIRE »** *(14/10)*.
   Le seuil 4 de `ecart_statut_regle` tolérait **quatre REMONTÉES** nommées, et le commentaire
   disait : *« un cinquième écart veut dire que quelque chose a bougé »*. Les 2 nouveaux sont
   des **REDESCENTES** — autre famille — et l'un n'a **aucun numéro de dossier**.
   ➡ **Lire ce qu'un seuil PROTÈGE avant de le déplacer** ; proposer de changer **la règle**
   plutöt que le chiffre.

28. ⭐⭐ **DEUX ÉCRITURES DE LA MÊME TRANSACTION SE RECONNAISSENT À LA MICROSECONDE**
   *(15/10)*. Il fallait savoir quelles lignes du carnet appartenaient à *ce* travail et
   pas à un geste plus récent qui avait réussi. `now()` est **figé** pendant une
   transaction, et les deux colonnes l'ont pour défaut : donc
   `app_annonce_champ_app.ecrit_le = app_console_job.requested_at` **exactement**.
   Mesure : **un seul couple à 0,000 s** sur 21, les autres à 44 s, 124 s, 8 006 s,
   473 236 s. ➡ **Un horodatage de transaction est un IDENTIFIANT** — même famille que
   « on croise sur les identifiants, jamais sur les nombres » (leçon 23). ⚠ Et il n'était
   pas décoratif : les 2 lignes visées avaient été écrites **plus tard** (+2 h 14, +2 min)
   par le geste que Frédéric avait refait à la main. Sans lui, on effaçait du vrai.

29. ⚠⚠ **UNE RÈGLE ÉLARGIE DANS UNE VUE NE L'EST PAS DANS LES FONCTIONS QUI LA DOUBLENT**
   *(15/10)*. Le 14/10 j'ai élargi `app_en_attente_humain` à « 5 tentatives **OU** plus de
   3 h » et j'ai écrit « le travail devient visible ». **Faux à moitié** : `app_action_status`
   (le bandeau) et `app_action_resolve` (le clic) portent **leur propre copie** du `>= 5`.
   Résultat mesuré : 47824 sonne, apparaît dans le moniteur, et **n'a aucun bouton** — le
   clic était refusé **en silence**, parce que le front **jetait** le `{"resolved": false}`
   que la RPC rendait depuis toujours. ➡ **Après avoir changé un seuil, chercher qui
   d'autre porte le même seuil** ; et **un front qui jette le compte-rendu d'une RPC
   fabrique un bouton menteur**.

30. ⚠⚠⚠ **TROISIÈME FOIS : MES ÉPREUVES NE TRAVERSENT PAS LE COPIER-COLLER** *(15/10)*.
   Frédéric colle `patch_aligner_seuil_trancher` → `STOP : l'ancre du repli apparait 0 fois`.
   J'avais protégé l'**empreinte** avec `replace(…, chr(13), '')` et laissé les **ancres**
   nues : collé depuis Windows, le fichier arrive en **CRLF**, et une ancre **multi-lignes**
   ne se retrouve plus dans un corps stocké en LF. Une seule de mes trois ancres était
   multi-lignes — **c'est la seule qui a cassé**. Reproduit et guéri en lecture seule :
   la même ancre donne **1** en LF, **0** collée, **1** quand on nettoie **les deux côtés**.
   ⚠ **La leçon était déjà écrite, deux fois** *(mémoire « empreinte md5 faussée par les
   fins de ligne Windows », élargie le 12/10 : « ça touche TOUTE ANCRE MULTILIGNE »)*.
   ➡ **Règle mécanique : dans un patch destiné à être COLLÉ, envelopper
   `replace(…, chr(13), '')` autour de CHAQUE ancre, de CHAQUE texte inséré** *(sinon le CRLF
   entre dans `prosrc` et c'est l'INVERSE qui ne retrouvera plus rien)* **et du
   `pg_get_functiondef`/`pg_get_viewdef` lu. Puis COMPTER les ancres multi-lignes avant
   d'envoyer.**
   ⚠⚠ **Et la cause profonde : mon épreuve ne reproduisait pas LE TRANSPORT.** Trois épreuves
   vertes n'ont rien vu parce qu'elles passent par l'outil SQL, jamais par un copier-coller.
   **Le remède est d'éprouver le transport lui-même** : exécuter le patch via
   `EXECUTE replace(texte, chr(10), chr(13)||chr(10))` — ce qui a reproduit l'erreur exacte,
   puis prouvé la guérison (aller **et** retour, empreinte d'origine retrouvée).

31. ⭐⭐ **UN RETOUR ARRIÈRE NE JUGE QUE SA PROPRE PART** *(15/10)*. Deux patchs du même jour
   touchaient **la même fonction**. L'inverse du premier exigeait l'empreinte d'**avant les
   deux** : les deux posés, il **défaisait correctement sa part, puis refusait** —
   `STOP : on ne retombe PAS sur l'empreinte d'origine (2315de8f…)`, et `2315de8f` **est**
   l'empreinte « second patch seul ». Le travail était bon, **le juge trop strict**. Il
   refusait sans rien casser *(l'exception annule tout)*, mais il **bloquait**.
   ➡ **Un inverse vérifie d'abord qu'il ne reste AUCUNE TRACE de ce qu'il devait retirer** ;
   l'empreinte globale ne s'exige que si l'autre patch n'est pas là — sinon il **dit**
   pourquoi elle diffère et **nomme l'autre inverse à jouer**. ⚠ Et ça ne se voit qu'en
   **éprouvant la chaîne complète dans l'ordre réel**, pas chaque patch isolément.
