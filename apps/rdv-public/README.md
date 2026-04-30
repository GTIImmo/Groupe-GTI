# RDV Public

Mini front public statique pour les QR codes GTI.

## URLs supportees

- `https://.../rdv/index.html`
- `https://.../rdv/index.html?ref=<token>`
- `https://.../rdv/index.html?ref=<hektor_annonce_id>`
- `https://.../rdv/estimation.html`
- `https://.../rdv/estimation.html?ref=<token>`

## API attendue

Le front appelle :

- `GET /api/public/appointments/annonce/{ref}/bootstrap`
- `POST /api/public/appointments/annonce/{ref}/request`
- `GET /api/public/appointments/estimation/bootstrap`
- `POST /api/public/appointments/estimation/request`

Par defaut, la base API est `window.location.origin + /api`.

Pour pointer vers un backend different, renseigner l'attribut :

```html
<body data-api-base="https://mon-backend.exemple.com">
```

## Deploiement statique

Ce dossier peut etre publie tel quel sur :

- GitHub Pages
- Vercel (mode statique)
- Netlify

Pour des liens profonds GitHub Pages, prevoir une redirection `404.html` ou un domaine qui reecrit vers `index.html`.
