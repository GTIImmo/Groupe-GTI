# Console Matterport Playwright

Ces scripts pilotent la console web Matterport avec Playwright, comme les scripts console Hektor.

## Fichiers

- `Console/matterport_playwright_login.js`
  - ouvre `https://authn.matterport.com/login`
  - laisse faire la connexion manuellement
  - sauvegarde la session locale dans `Console/matterport_storage_state.json`

- `Console/matterport_inspect_model.js`
  - reutilise `Console/matterport_storage_state.json`
  - ouvre un modele Matterport
  - capture les URLs, captures ecran, texte de page et evenements reseau expurges
  - ecrit les sorties dans `Console/exports/matterport_inspect_*`

- `Console/matterport_console_actions.js`
  - reutilise `Console/matterport_storage_state.json`
  - ouvre la ligne d'un modele dans la console Matterport
  - inspecte le menu actions et le panneau `Partager et inviter`
  - change la confidentialite ou clique `Archiver l'Espace` uniquement avec `--confirm`

## Configuration locale

Tu peux mettre ces valeurs dans `Console/.env` :

```env
MATTERPORT_LOGIN_URL=https://authn.matterport.com/login
MATTERPORT_MODELS_URL=https://my.matterport.com/models
MATTERPORT_STORAGE_STATE_PATH=C:\Users\frede\Desktop\Projet\Console\matterport_storage_state.json
MATTERPORT_EMAIL=ton-email-matterport
MATTERPORT_PASSWORD=ton-mot-de-passe-matterport
MATTERPORT_TEST_MODEL_ID=Rt4rHP4jpFX
```

Ces valeurs restent locales dans `Console/.env`. Ne les mets jamais dans un fichier versionne ou dans une note projet.

Si Matterport demande une double authentification, le script pre-remplit email/mot de passe puis tu termines le controle dans la fenetre ouverte.

## Commandes

Connexion / renouvellement de session :

```powershell
cd C:\Users\frede\Desktop\Projet\Console
node matterport_playwright_login.js
```

Inspection d'un modele :

```powershell
cd C:\Users\frede\Desktop\Projet\Console
node matterport_inspect_model.js Rt4rHP4jpFX
```

Ou avec une URL Showcase :

```powershell
node matterport_inspect_model.js "https://my.matterport.com/show/?m=Rt4rHP4jpFX"
```

Lister les actions disponibles sur une ligne Matterport :

```powershell
node matterport_console_actions.js menu vrpJSLcek3T
```

Lire l'etat de confidentialite d'un modele :

```powershell
node matterport_console_actions.js share vrpJSLcek3T
```

Changer la confidentialite, apres validation explicite :

```powershell
node matterport_console_actions.js visibility vrpJSLcek3T --visibility=unlisted --confirm
```

Mettre en ligne pour l'app, c'est-a-dire choisir `Non repertorie` dans Matterport :

```powershell
node matterport_console_actions.js online vrpJSLcek3T --confirm
```

Remettre hors ligne pour l'app, c'est-a-dire choisir `Prive` dans Matterport :

```powershell
node matterport_console_actions.js offline vrpJSLcek3T --confirm
```

Archiver un modele, apres validation explicite :

```powershell
node matterport_console_actions.js archive vrpJSLcek3T --confirm
```

Reactiver un modele archive, apres validation explicite :

```powershell
node matterport_console_actions.js reactivate vrpJSLcek3T --confirm
```

Pour mettre en ligne un modele archive dans l'app, il faut donc enchainer :

```powershell
node matterport_console_actions.js reactivate vrpJSLcek3T --confirm
node matterport_console_actions.js online vrpJSLcek3T --confirm
```

Valeurs de confidentialite observees dans l'HTML Matterport :

- `private` : prive, limite aux collaborateurs
- `password` : protege par mot de passe
- `unlisted` : non repertorie, visible par les personnes qui ont le lien. C'est le bon choix pour afficher l'URL de visite virtuelle dans l'app
- `public` : public et indexable, parfois desactive par Matterport selon le modele ou le compte

## Securite

- Les cookies/session restent en local dans `Console/matterport_storage_state.json`.
- Les captures reseau sont expurgees des headers `cookie`, `authorization`, `token`, `secret`, `password`.
- Le script ne contourne pas le blocage API Matterport. Il automatise uniquement une session web legitime.
- Les actions qui modifient Matterport demandent `--confirm`; sans ce parametre le script fait seulement une lecture.
