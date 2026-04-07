## SMTP notification decision diffusion

### Ce qui a ete mis en place

Quand Pauline accepte ou refuse une demande de diffusion :

- la decision est enregistree dans l'app
- un appel backend local est fait vers `/api/notifications/diffusion-decision`
- le serveur Vite envoie un email SMTP au `negociateur_email`

### Fichiers modifies

- `apps/hektor-v1/src/App.tsx`
- `apps/hektor-v1/src/lib/api.ts`
- `apps/hektor-v1/vite.config.ts`
- `apps/hektor-v1/.env.smtp.example`

### Variables a configurer

Voir :

- `apps/hektor-v1/.env.smtp.example`

Variables :

- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASS`
- `SMTP_SECURE`
- `SMTP_FROM`
- `SMTP_ALLOW_USER_FROM`

### Logique expediteur

Deux modes existent :

1. mode recommande

- `SMTP_ALLOW_USER_FROM=false`
- l'email part avec `SMTP_FROM`
- l'email utilisateur de l'app est mis en `reply-to`

2. mode expediteur utilisateur direct

- `SMTP_ALLOW_USER_FROM=true`
- l'email part avec l'email de l'utilisateur connecte
- a utiliser seulement si le SMTP l'autorise reellement

### Pourquoi ce choix

Beaucoup de serveurs SMTP refusent un `from` arbitraire qui ne correspond pas au compte authentifie.

Le mode par defaut evite donc les rejets :

- expediteur technique stable
- reponse adressee au bon utilisateur grace au `reply-to`

### Comportement en cas d'erreur

Si l'envoi SMTP echoue :

- la decision metier reste enregistree
- un message d'erreur est affiche dans l'app
- l'utilisateur sait que l'email n'est pas parti
