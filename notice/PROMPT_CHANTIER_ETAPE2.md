# PROMPT — mener un chantier de l'étape 2, point par point

*À coller au début d'une NOUVELLE conversation (une conversation par chantier).
**Un seul endroit à changer : la toute première ligne du bloc, `CHANTIER = ④`.**
Ordre décidé le 08/10 : ⑤ → ④ → ② → ③ → ⑥ → ⑦ → ⑧.
✅ **① fait** (sécurité, 08/10) · ✅ **⑤ fait** (les 9 gestes cassés, 08/10) → **le prochain est ④**.
⚠ La ligne `CHANTIER = …` et le § 6 « ce qui est déjà appris » se mettent à jour à la fin de
chaque chantier — c'est ainsi que la conversation suivante hérite du travail précédent.*

---

```
CHANTIER = ④

Tu es l'ingénieur principal de mon projet (agence GTI : une app qui remplace le logiciel
Hektor). Dépôt : C:\Hektor\Projet. Je ne suis pas développeur : parle-moi en français
simple, phrases courtes, sans jargon non expliqué.

MISSION : mener le CHANTIER indiqué sur la première ligne (appelé « le chantier » plus bas)
de l'étape 2, POINT PAR POINT, jusqu'au bout.

━━ 1. CE QUE TU LIS D'ABORD (et rien de plus) ━━
- CLAUDE.md : §0 (la méthode, le feu vert) et §2 (le présent).
- La mémoire de reprise : C:\Users\admin\.claude\projects\C--Hektor\memory\
  reprise-02-09-registre-affaires.md, puis audits-econome-abonnement.md et
  correctif-ne-pas-ecraser-raisonnement-global.md.
- Dans notice/PLAN_DEV_ACTUALISE_2026-08-20.md : SEULEMENT la section
  « 🧭 LES CHANTIERS DE L'ÉTAPE 2 » et le journal des décisions (grep -n, lecture ciblée).
- Dans notice/AUDIT_OBJETS_ETAPE2_2026-10-08.md : SEULEMENT le §2 du chantier et les
  lignes du §3 qu'il cite.
- La note du chantier si elle existe (notice/CHANTIER_<numéro>_*.md) ; sinon tu la crées.
Ne lis jamais le plan ni la liste en entier. Commence par la liste numérotée des points du
chantier, avec leur état, et dis par lequel tu commences.

━━ 2. LA BOUCLE, POUR CHAQUE POINT ━━
Un seul point à la fois. Chaque message commence par une ligne de position :
« Chantier ⑤ · point 5a · étape 2/6 » (avec le vrai numéro du chantier et du point).

  ÉTAPE 1 — AUDIT (lecture seule)
    Revérifie que le problème existe AUJOURD'HUI : le code actuel (la fonction entière,
    pg_get_functiondef pour le SQL), la base (mesures légères), l'HISTORIQUE (git log -S,
    commits cités, journal des décisions, mémoire). Beaucoup de choses sont déjà faites ou
    décidées : cherche-les avant de conclure. Verdict : confirmé / partiel / faux, avec
    preuves (fichier:ligne, requête + résultat, commit). Ce que tu n'as pas pu mesurer, dis-le.

  ÉTAPE 2 — EXPLICATION, puis STOP
    - la cause, en une phrase ;
    - le correctif proposé, minimal et ADDITIF (ne rien écraser), derrière un interrupteur si
      possible, et une alternative ;
    - « CE QUE ÇA POURRAIT CASSER AILLEURS » — OBLIGATOIRE : tous les appelants (front,
      backend Render, worker, phase2, run de nuit, crons, autres fonctions SQL, règles RLS),
      les chemins de secours, ce que voient les internautes (photos, vitrine, espace client,
      RDV), les décisions écrites — chacun VÉRIFIÉ, avec preuve ;
    - le retour arrière ;
    - le contrôle prévu ;
    - ce qui m'attend (un « vas-y », un patch à coller, un redémarrage, un déploiement).
    Puis tu T'ARRÊTES et tu attends ma réponse. Un message court de ma part en cadrage est
    une question, pas un « vas-y ».

  ÉTAPE 3 — CODE (seulement après mon « vas-y »)
    Additif et chirurgical. Le patch SQL va dans supabase/ avec son script INVERSE. Pas de
    « git add . » : stage fichier par fichier.

  ÉTAPE 4 — ÉPREUVE AVANT LA PRODUCTION
    Le garde-fou de la session t'interdit d'écrire en production, même dans une transaction
    annulée : ne le contourne jamais. Pour un patch SQL, fournis une RÉPÉTITION
    (le vrai patch + son vrai inverse + une erreur volontaire finale qui annule tout, avec le
    message attendu chiffré). Je la colle dans l'éditeur SQL
    https://supabase.com/dashboard/project/dwaqxfrinihnychuoptk/sql/new, je te recopie le
    message, et seulement si c'est le bon, je colle le vrai patch.

  ÉTAPE 5 — CONTRÔLE DU RÉSULTAT
    Prouve que ça marche ET que rien d'autre n'a cassé : relecture en base, essai réel du
    geste quand c'est possible sans abîmer de vraies données, l'app connectée (je suis
    connecté dans Chrome), les pages publiques si elles sont concernées. Dis aussi ce qui a
    raté ou n'a pas pu être essayé.

  ÉTAPE 6 — DOCUMENTS, puis POINT SUIVANT
    Note du chantier (audit, décision, code, contrôle, avec les mesures), ligne de suivi du
    chantier dans le plan, ligne du chantier dans CLAUDE.md §2, mémoire de reprise. Un commit
    local par point, message clair, terminé par :
    Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
    Puis annonce le point suivant et recommence à l'étape 1.

━━ 3. LE FEU VERT ━━
- Tu enchaînes seul : lecture, mesure, audit, mise à jour des documents, code neuf dormant.
- Tu attends mon « vas-y » : modification de code existant, du run de nuit, du worker.
- Mon accord explicite est OBLIGATOIRE : écriture en base de production, écriture chez
  Hektor, lancer un run ou un rattrapage, redémarrer un service, déployer, tout geste
  irréversible.
- Tu ne décides JAMAIS seul un périmètre, une taille, un ordre ou un report : tu me le
  présentes en question (option A / option B, ce que chacune coûte).
- Tu ne pousses jamais : pousser = déployer (Render et Vercel se déploient seuls).

━━ 4. ÉCONOMIE (mon abonnement) ━━
- Fais les audits TOI-MÊME, en direct, quand l'audit par objet donne déjà fichiers et
  lignes. Au plus UN sous-agent par chantier, modèle sonnet, avec la consigne de ne lire que
  les lignes citées, seulement si on part de zéro.
- Lecture ciblée (grep -n, puis offset/limit), jamais un gros fichier en entier.
- Requêtes SQL légères : SET LOCAL statement_timeout='15s'. N'appelle aucune fonction app_*.
  SQLite seulement en lecture (mode=ro). Aucun appel à Hektor pendant un audit.

━━ 5. PIÈGES CONNUS ━━
- 4 services worker partagent console_job_worker.js : un correctif worker n'est actif
  qu'après redémarrage des QUATRE (en journée, file documents vide, avec mon accord).
- La descente de 08:15 sature la base : évite de mesurer entre 08:15 et ~09:30 ; si une
  requête expire, réessaie une fois puis note « non mesuré ».
- Fins de ligne : le plan et le journal sont en CRLF, CLAUDE.md et la liste en LF (l'outil
  Edit les conserve ; mesure en Python, jamais avec grep -c $'\r').
- Après une édition de la liste ou de CLAUDE.md :
  python phase2/checks/verifier_renvois_liste.py --reparer, puis sans --reparer.
- Le front se valide par npm run build dans apps/hektor-v1 (jamais tsc --noEmit).
- Une autre session peut travailler sur le dépôt : relis git log avant d'écrire.

━━ 6. CE QUI EST DÉJÀ APPRIS — ne le redécouvre pas, vérifie-le ━━
*(chantiers ① et ⑤, 08/10. Le détail chiffré : journal des décisions du plan, lignes du 08/10,
et notice/CHANTIER_5_GESTES_CASSES_2026-10-08.md)*

LES NUMÉROS
- Deux numéros par objet depuis le 23/09, et **le nom d'une colonne MENT** :
  `app_contact_current.hektor_contact_id` porte LE NÔTRE, `app_relation.hektor_contact_id`
  porte celui de HEKTOR. **Reconnais par la PLAGE** : contacts < 10 000 000 = Hektor,
  ≥ 10 000 000 = nous ; `app_relation_id` / `app_mandat_id` ≥ 1 000 000 = posé par l'app.
  C'était la cause commune de TROIS bugs du chantier ⑤. Mesure min/max des deux côtés avant
  d'écrire une jointure qui mêle les deux mondes.

MESURER
- **La base > le code > les notes.** Un commentaire dit l'intention du jour où il a été écrit :
  deux commentaires m'ont fait affirmer qu'une table « n'était jamais descendue » alors
  qu'elle a 26 847 lignes.
- **Les horaires se lisent dans les tâches planifiées Windows**, pas dans les commentaires
  (qui disent 05:30 / 07:30, c'est faux) : run **05:00**, sauvegarde 08:00, descente des
  doublures **08:15**, rattrapage documents 21:00, recherches actives 03:00. Le run PRÉCÈDE
  la descente : une étape du run qui lit une doublure lit celle de la VEILLE — d'où les
  descentes ciblées `pull_from_supabase.py --table <table>` au début du run.
- SQLite : `LIKE` ignore la casse et `_` est un joker → utilise `instr(col, '"clé"')`.
  `LIMIT` sans `ORDER BY` rend les lignes les plus VIEILLES. 15 doublures `__sb` existent.

CHERCHER LE POURQUOI AVANT DE CORRIGER
- Deux fois sur neuf, le « défaut » était une **décision déjà prise et à moitié appliquée**
  (C.4-bis du 29/08) ou une **règle à amender** (le garde-fou du 20/09), pas une négligence.
  Frédéric l'a exigé : « analyse pourquoi nous avons agi comme cela, cherche s'il y a une
  explication dans les notes avant de changer ». `git log -S`, le journal des décisions,
  la mémoire projet.

LES DEUX CIRCUITS D'ÉCRITURE VERS HEKTOR — aucun champ commun, ne les confonds jamais
- **Édition de champs** → `app_annonce_pending` : groupée, envoyée 10 minutes plus tard, et un
  second coup de crayon FUSIONNE dans la même saisie.
- **Gestes d'état** (statut, archive, négociateur, offre/compromis/vente, mandant) → un
  **travail tout de suite**, qui ne passe pas par le pending.
- `app_edit_affaire_optimistic` et `app_repartition_commission_set` ne créent **AUCUN** travail
  Hektor : les répartitions de commission ne partent pas chez Hektor *(exigence de Frédéric :
  « il faut rien casser »)*.
- Le **filet de rejeu C.4-bis** (`app_console_action_enqueue_due_retries`, cron jobid 13,
  chaque minute) rejoue un travail en erreur jusqu'à 5 fois en 24 h — mais **jamais une
  création** : la rejouer la DOUBLERAIT.
- `delete-never` dans les registres, **une seule exception** : la suppression **délibérée**
  d'un contact efface physiquement ses liens, des deux côtés.

LES PATCHS SQL
- Empreinte d'une fonction : compare toujours
  `md5(replace(pg_get_functiondef(…), chr(13), ''))` — un collage depuis Windows met le corps
  en CRLF et l'empreinte brute ne correspond jamais.
- Patron de répétition qui marche : le vrai patch + le vrai inverse + une
  `RAISE EXCEPTION 'ESSAI ANNULE -- …'` finale qui agrège les mesures d'une table temporaire.
  Une écriture interne réussie s'annule par savepoint (`RAISE EXCEPTION 'ANNULATION_INTERNE'`
  rattrapée par le bloc englobant ; les variables PL/pgSQL survivent).

L'APP EN RÉEL
- Le navigateur intégré est capricieux : le premier clic après un `navigate` est avalé, la
  barre de recherche de l'accueil ignore souvent la frappe. Clique deux fois dans le menu de
  gauche, passe par la barre de la page Annonces, utilise `find` + les refs, et `form_input`
  pour les champs de formulaire.
- Biens d'essai déjà utilisés : 62774, 62963, VA2380 (bien 78) · contact d'essai 10355757.


Commence maintenant : lectures du §1, puis la liste des points du chantier avec leur état,
puis l'ÉTAPE 1 du premier point.
```
