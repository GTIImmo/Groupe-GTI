# Correctif push contacts Supabase delta - 2026-05-27

## Objectif

Aligner le module contacts avec la règle projet :

- miroir complet Hektor en local ;
- Supabase limité aux données utiles à l'application ;
- aucun push contacts sans option explicite dans le run quotidien ;
- delta réel, sans repush complet provoqué par une date technique.

## Corrections appliquées

### 1. Run quotidien

Fichier : `run_full_pipeline.ps1`

Le push contacts reste protégé par l'option explicite :

```powershell
-PushContactsToSupabase
```

Sans cette option, le pipeline construit la couche contacts locale, mais ne pousse pas les contacts vers Supabase.

Quand l'option est utilisée, le push est forcé sur le périmètre léger :

```powershell
--push-mode update
--contacts-scope eligible
```

Cela évite un envoi accidentel du listing complet des contacts vers Supabase.

### 2. Delta contacts

Fichier : `phase2/sync/push_contacts_to_supabase.py`

Le hash de comparaison ignore maintenant `refreshed_at`.

Raison : `refreshed_at` est régénéré à chaque build local. Il ne représente pas une modification métier du contact, de sa relation ou de sa recherche. Sans cette correction, le mode update pouvait repusher toutes les lignes du scope à chaque run.

### 3. Périmètre Supabase par défaut

Le script de push contacts utilise désormais par défaut :

```powershell
--contacts-scope eligible
--push-mode update
```

Le scope éligible correspond aux contacts utiles à l'app :

- contact lié à une annonce active ;
- contact avec recherche acquéreur active.

Les recherches poussées sont les recherches actives. Les relations poussées sont les relations liées aux annonces actives, sauf option volontaire contraire.

### 4. Nettoyage logique Supabase

Le script sait maintenant calculer les lignes qui étaient poussées auparavant mais qui ne remplissent plus les conditions du scope actuel.

Exemples :

- une relation n'est plus liée à une annonce active ;
- une recherche devient inactive ;
- un contact n'a plus de relation active ni de recherche active.

Ces lignes peuvent être retirées de Supabase pendant le push, sans suppression locale.

## Contrôles effectués

- Syntaxe Python du script de push contacts : OK.
- Syntaxe PowerShell du run quotidien : OK.
- Test hash : OK, `refreshed_at` ne déclenche plus de faux changement.
- Dry-run local sans appel Supabase :

```json
{
  "app_contact_current": {
    "loaded": 54085,
    "to_upload": 54085,
    "to_delete": 0,
    "push_mode": "update"
  },
  "app_contact_relation_current": {
    "loaded": 76956,
    "to_upload": 76956,
    "to_delete": 0,
    "push_mode": "update"
  },
  "app_contact_search_current": {
    "loaded": 343,
    "to_upload": 343,
    "to_delete": 0,
    "push_mode": "update"
  }
}
```

Le volume `to_upload` est normal tant que le premier push contacts n'a pas établi son état local de référence.

## Commandes utiles

Run quotidien sans push contacts :

```powershell
cd C:\Hektor\Projet
powershell -ExecutionPolicy Bypass -File .\run_full_pipeline.ps1
```

Run quotidien avec push contacts léger, uniquement sur accord :

```powershell
cd C:\Hektor\Projet
powershell -ExecutionPolicy Bypass -File .\run_full_pipeline.ps1 -PushContactsToSupabase
```

Contrôle sans push :

```powershell
cd C:\Hektor\Projet
.\.venv\Scripts\python.exe .\phase2\sync\push_contacts_to_supabase.py --push-mode update --contacts-scope eligible --dry-run
```
