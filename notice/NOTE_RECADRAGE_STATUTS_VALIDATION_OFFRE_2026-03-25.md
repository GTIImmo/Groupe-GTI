# Note recadrage statuts validation / offre

Date : 25/03/2026

## Objet

Corriger dans la phase 2 la confusion entre :

- validation metier
- diffusable technique
- diffusion reelle sur passerelles
- cycle offre

## Probleme identifie

Avant correctif :

- `validation_diffusion_state = valide` et `statut_global = Valide` reposaient surtout sur `diffusable = 1`
- le champ source `src.valide` etait expose dans la vue, mais pas reellement utilise comme critere principal
- `Offre recue` dependait d'un `event_type` local uniquement, donc pas vraiment parametrable

Cela ne suivait pas correctement l'intention des notes metier :

- `Valide` = validation / autorisation
- `Diffuse` = diffusion reelle sur au moins une passerelle
- `Offre recue` / `Offre validee` = etapes du cycle transactionnel

## Correctif applique

### Nouvelle politique explicite

Ajout du module :

- `phase2/rules/status_policy.py`

Il centralise deux politiques :

- `ValidationPolicy`
- `OfferPolicy`

### Validation

La validation approuvee est maintenant calculee par une methode explicite :

- source Hektor : `src.valide = 1`
- ou statut interne : `pret_diffusion`

Conséquence :

- `validation_diffusion_state = valide` repose maintenant sur la validation source / interne
- plus directement sur `diffusable`

### Offre

Le cycle offre est maintenant explicite :

- `Offre validee` si `offre_state = accepted` et `offre_event_date` renseignee
- `Offre recue` si :
  - `event_type = offre_recue`
  - ou `offre_id IS NOT NULL` avec une offre non acceptee

Conséquence :

- `Offre recue` devient une vraie lecture metier parametrable
- elle ne depend plus seulement d'un event local

## Impact sur les statuts globaux

Nouvelle logique :

- `Diffuse` : validation approuvee + au moins une passerelle active
- `Valide` : validation approuvee + pas de passerelle active
- `A valider` : mandat present, mais validation non acquise
- `Offre recue` / `Offre validee` passent avant `Diffuse` et `Valide`

## Fichiers modifies

- `phase2/rules/status_policy.py`
- `phase2/rules/sql_fragments.py`
- `phase2/pipeline/view_common.py`

## Verification locale

Commande relancee :

```powershell
.\.venv\Scripts\python.exe phase2\refresh_views.py
```

Resultat observe :

- `A valider` : `15277`
- `Valide` : `80`
- `Diffuse` : `269`
- `Offre recue` : `9`
- `Offre validee` : `920`

Controle cible :

- `Valide` avec `valide = 1` : `79`
- `Valide` sans `valide = 1` : `1`
- `Diffuse` avec portails actifs : `269`
- `Offre recue` avec `offre_id` : `9`
- `Offre validee` avec `offre_state = accepted` : `920`

## Lecture metier retenue

- `valide` = validation source / autorisation
- `diffusable` = capacite technique de diffusion
- `visible` / `nb_portails_actifs` = diffusion reelle
- `Offre recue` / `Offre validee` = cycle transactionnel

## Suite possible

Le systeme est maintenant plus coherent, mais il reste une etape si l'on veut aller plus loin :

- rendre les politiques encore plus parametrables par table de configuration
- au lieu de les garder en constantes Python
