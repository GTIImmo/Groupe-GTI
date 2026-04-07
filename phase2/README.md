# Phase 2

La phase 2 reste la couche de consolidation metier entre l'extraction/source et la future application.

## Regle simple

- Phase 1 extrait et normalise.
- Phase 2 consolide, qualifie, controle.
- L'app React affiche.

## Etat actuel

Les fichiers historiques encore utilises sont conserves a la racine de `phase2` :

- `bootstrap_phase2.py` : initialise la base phase 2.
- `refresh_views.py` : calcule les vues et statuts metier.
- `schema_phase2.sql` : schema actuel de reference.
- `phase2.sqlite` : base consolidee actuelle.
- `export_mini_app_html.py` : export legacy de l'app HTML.
- `export_vue_generale_html.py` : export legacy de la vue generale HTML.
- `app_metier.html` : sortie HTML legacy.
- `vue_generale.html` : sortie HTML legacy.

Ces fichiers restent en place tant que la migration vers React + Supabase + Vercel n'est pas terminee.

## Arborescence cible

La nouvelle organisation de la phase 2 est la suivante :

```text
phase2/
  README.md
  schema_phase2.sql
  bootstrap_phase2.py
  refresh_views.py
  phase2.sqlite
  export_mini_app_html.py
  export_vue_generale_html.py
  app_metier.html
  vue_generale.html
  docs/
    PLAN_REFONTE_REACT_SUPABASE_VERCEL.md
  pipeline/
    README.md
  rules/
    README.md
  checks/
    README.md
  sync/
    README.md
  legacy_front/
    README.md
    _inline_script.js
    _tmp_app_script.js
```

## Rangement par categorie

### A garder comme reference metier

- `refresh_views.py`
- `schema_phase2.sql`
- `bootstrap_phase2.py`
- `phase2.sqlite`

### A remplacer progressivement

- `export_mini_app_html.py`
- `export_vue_generale_html.py`
- `app_metier.html`
- `vue_generale.html`

### A ne plus utiliser comme base de travail

- `legacy_front/_inline_script.js`
- `legacy_front/_tmp_app_script.js`

## Prochaine etape

Le travail neuf doit partir des sous-dossiers `pipeline/`, `rules/`, `checks/` et `sync/`.
