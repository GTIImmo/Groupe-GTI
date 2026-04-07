# Note write-back Hektor diffusion

Date: 2026-03-31

## Objet

Documenter la premiere couche technique locale de write-back Hektor pour la diffusion.

Cette couche ne part pas du front React.

Elle passe par un script Python local afin de :

- reutiliser l'authentification OAuth / JWT Hektor existante
- ne pas exposer `HEKTOR_CLIENT_SECRET` dans le navigateur
- appliquer ensuite le futur pilotage de la console `Diffusion`

## Script ajoute

- `phase2/sync/hektor_diffusion_writeback.py`

## Principe

### 1. Seed des cibles par defaut

Commande :

```powershell
.\.venv\Scripts\python.exe phase2\sync\hektor_diffusion_writeback.py seed-default-targets --app-dossier-id 123
```

Effet :

- lit les passerelles `supports_write = 1` depuis `data/hektor.sqlite`
- insere / met a jour `app_diffusion_target`
- met toutes les cibles a `enabled`
- source : `accepted_default`

Usage prevu :

- apres acceptation d'une demande de diffusion
- le bien devient diffusable
- les passerelles par defaut sont preparees dans `app_diffusion_target`

### 2. Application des cibles sur Hektor

Commande de test :

```powershell
.\.venv\Scripts\python.exe phase2\sync\hektor_diffusion_writeback.py apply-targets --app-dossier-id 123 --dry-run
```

Commande reelle :

```powershell
.\.venv\Scripts\python.exe phase2\sync\hektor_diffusion_writeback.py apply-targets --app-dossier-id 123
```

Effet :

- lit `app_diffusion_target`
- lit l'etat live des passerelles via `ListPasserelles`
- verifie `diffusable`
- appelle `Diffuse` si le bien doit devenir diffusable
- appelle :
  - `addAnnonceToPasserelle`
  - `removeAnnonceToPasserelle`
- journalise les actions dans `app_broadcast_action`
- met a jour `last_applied_at`, `last_apply_status`, `last_apply_error` dans `app_diffusion_target`

## Endpoints utilises

- `GET /Api/Annonce/AnnonceById/`
- `GET /Api/Annonce/ListPasserelles/`
- `GET /Api/Annonce/Diffuse/`
- `GET /Api/Passerelle/addAnnonceToPasserelle/`
- `GET /Api/Passerelle/removeAnnonceToPasserelle/`

## Variables requises

Le script reutilise les variables deja utilisees par la phase 1 :

- `HEKTOR_BASE_URL`
- `HEKTOR_CLIENT_ID`
- `HEKTOR_CLIENT_SECRET`
- `HEKTOR_VERSION`

## Limites actuelles

- le front React n'appelle pas encore ce script
- la console `Diffusion` prepare l'UI mais ne persiste pas encore ses cibles dans Supabase / SQLite
- `Diffuse` est traite comme un toggle a verifier prudemment sur un dossier test
- le parsing de `ListPasserelles` est tolerant, mais doit etre confirme sur reponse reelle de votre instance

## Etape suivante

1. persister les choix de la console `Diffusion` dans `app_diffusion_target`
2. brancher un point d'execution serveur ou local pour lancer `apply-targets`
3. verifier sur un dossier test :
   - seed des cibles
   - dry-run
   - run reel
   - relecture Hektor
