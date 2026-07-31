# Note projet — Runs autonomes : login Hektor headless + tâches planifiées en S4U

Date : 2026-07-31
Statut : plan validé (go utilisateur « comme tu veux, tous les run doivent être mis à jour »), application en cours par étapes.

## Problème

Les runs planifiés GTI ne se déclenchent plus de façon fiable. Cause racine confirmée : les 4 tâches
« GTI * » sont en `LogonType = Interactive` (« exécuter seulement si l'utilisateur est connecté »).
Le serveur OVH tourne 24/7, mais la session RDP admin est **déconnectée la nuit** → Windows refuse la
tâche à son heure avec le code **`0x800710E0`** (« L'opérateur ou l'administrateur a refusé la requête »).

Symptômes observés : run quotidien 05:30 sauté plusieurs jours de suite (26–28/07, puis 29–31/07),
`LastTaskResult = 0x800710E0` sur GTI Quotidien / Health Monitor / Recherches Actives / Relances Email.

Le pipeline lui-même est sain (un lancement manuel se termine en succès en ~50 min). Ce n'est PAS un
plantage du pipeline, c'est un **non-déclenchement** dû à la condition de session.

## Contrainte découverte (audit)

Le pipeline et les workers Console tournent en headless SAUF le **rafraîchissement de session Hektor**
(`Console/playwright_login.js`), codé en dur en `headless: false` (navigateur VISIBLE) — il ignore même
la variable `CONSOLE_HEKTOR_HEADLESS`. Ce login visible exige un bureau interactif, donc :
- il casse en session sans bureau (S4U / session 0) ;
- c'est aussi la piste du blocage worker de 30 min du 23/07 (« Retour session administrateur Hektor »).

Deux scripts Matterport ont le même défaut (navigateur visible, non surveillé) :
`Console/matterport_playwright_login.js` et `Console/matterport_console_actions.js`.

## Preuve (test du 28/07, copie jetable, prod non touchée)

Login `playwright_login.js` forcé en headless :
- 2FA TOTP (Google Authenticator) **passe sans écran** (le code est calculé depuis `HEKTOR_TOTP_SECRET`,
  pas lu à l'écran) ;
- seul le clic final « ADMIN → J'y accède » échouait (sélecteur `:has-text("ADMIN")` sur un conteneur
  fragile) ;
- correction validée : `dialog.getByRole('button', { name: /accède|accede/i }).first()` →
  login complet + session valide (16,8 Ko, cookies Hektor). **Bout en bout OK, sans bureau.**

## Changements

### Code (additif, réversible, respecte `CONSOLE_HEKTOR_HEADLESS` défaut `true`)
1. `Console/playwright_login.js`
   - `headless: false` → piloté par `CONSOLE_HEKTOR_HEADLESS` (défaut headless) ;
   - clic ADMIN via `getByRole` (robuste apostrophe/casse).
2. `Console/matterport_playwright_login.js` — même bascule headless pilotée par env.
3. `Console/matterport_console_actions.js` — défaut `MATTERPORT_HEADLESS` → `true`.

### Tâches planifiées → S4U (« exécuter que l'utilisateur soit connecté ou non »)
- GTI Health Monitor, GTI Recherches Actives, GTI Relances Email : S4U-safe immédiatement (pur HTTP/Python/SMTP).
- GTI Quotidien : S4U-safe **après** le correctif login (son seul chemin visible était le refresh de session).
- Hektor-IngestSemestriel : déjà en `Password` (session-indépendant), rien à changer.
- Hektor Console Worker* : Désactivées (remplacées par les services Windows) — laissées telles quelles.

### Traçabilité
Activer l'historique du Planificateur : `wevtutil set-log Microsoft-Windows-TaskScheduler/Operational /enabled:true`.

## Impact (audit global 3 volets, 2026-07-31)
- App hektor-v1 / écrans / vitrine Android : **aucun impact** (ne consomment que Supabase / un JSON statique ;
  le contrat de données est inchangé — seule la façon de produire les données change).
- Login headless : sûr pour tous les appelants automatiques (flux 100 % scripté, aucune interaction humaine).
- S4U : 3/4 tâches sûres tout de suite, GTI Quotidien après le correctif login. Précédent OK sur la machine
  (workers = S4U, IngestSemestriel = Password).

## Retour arrière (3 niveaux)
1. **Instantané, sans git** : le code respecte `CONSOLE_HEKTOR_HEADLESS` → poser `CONSOLE_HEKTOR_HEADLESS=false`
   (env du service) ramène le navigateur visible. Idem `MATTERPORT_HEADLESS=false`.
2. **Code** : les 3 fichiers dans un commit git isolé (stagé fichier par fichier, jamais `git add .`) →
   `git revert <sha>`.
3. **Tâches** : repasser une tâche en Interactive :
   ```powershell
   $p = New-ScheduledTaskPrincipal -UserId 'admin' -LogonType Interactive -RunLevel Limited
   Set-ScheduledTask -TaskName 'GTI Quotidien' -Principal $p
   ```
   Historique : `wevtutil set-log Microsoft-Windows-TaskScheduler/Operational /enabled:false` (facultatif).

## Vérification post-changement
- Re-test `playwright_login.js` headless sur le vrai fichier (session jetable) → session valide.
- `Get-ScheduledTaskInfo` sur les 4 tâches → `LastTaskResult = 0x0` après un run on-demand / la nuit suivante.
- Contrôle que les workers Console refont bien leur session en headless (services `HektorConsoleWorker*`).
