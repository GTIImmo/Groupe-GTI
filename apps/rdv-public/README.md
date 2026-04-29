# RDV Public

Mini front public statique pour les QR codes annonce.

## URLs supportées

- `https://.../rdv/annonce/<token>`
- `https://.../rdv/annonce/<hektor_annonce_id>`
- fallback simple : `index.html?ref=<token>`

## API attendue

Le front appelle :

- `GET /api/public/appointments/annonce/{ref}`
- `GET /api/public/appointments/annonce/{ref}/slots`
- `POST /api/public/appointments/annonce/{ref}/request`

Par défaut, la base API est `window.location.origin + /api`.

Pour pointer vers un backend différent, renseigner l'attribut :

```html
<body data-api-base="https://mon-backend.exemple.com">
```

## Déploiement statique

Ce dossier peut être publié tel quel sur :

- GitHub Pages
- Vercel (mode statique)
- Netlify

Pour des liens profonds GitHub Pages, prévoir une redirection `404.html` ou un domaine qui réécrit vers `index.html`.
