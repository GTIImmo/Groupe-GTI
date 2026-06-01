## Google Workspace - notifications email

### Contexte

Le projet utilise deja le backend Python pour envoyer certaines notifications email.

Le service central est :

- `backend/app/services/notification_service.py`

Il envoie via Gmail API si les variables Google sont presentes :

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REFRESH_TOKEN`
- `GOOGLE_SENDER_EMAIL`

Sinon il revient au mode SMTP.

### Situation actuelle

Le compte expediteur actuellement utilise pour les notifications est :

- `frederic.gerphagnon@gti-immobilier.fr`

Cette solution fonctionne mais elle lie les notifications systeme au compte personnel de Frederic.

Risques :

- dependance a un compte utilisateur nominatif ;
- interruption possible si le token OAuth est revoque ;
- interruption possible apres changement de mot de passe Google ;
- confusion pour les destinataires, car l'email semble venir de Frederic ;
- moins propre pour les futurs workers et agents IA.

### Compte cible recommande

Le compte Google Workspace existant suivant est identifie comme meilleur expediteur technique :

- `accueil@gti-immobilier.fr`

Raison :

- compte GTI non personnel ;
- adresse deja comprehensible pour les clients et negociateurs ;
- meilleur support pour les notifications automatiques ;
- separation claire entre utilisateur humain et systeme applicatif.

### Decision recommandee

Ne pas casser le flux actuel immediatement.

Etape suivante propre :

1. conserver temporairement `frederic.gerphagnon@gti-immobilier.fr` ;
2. generer un nouveau refresh token Gmail API pour `accueil@gti-immobilier.fr` ;
3. remplacer `GOOGLE_SENDER_EMAIL` par `accueil@gti-immobilier.fr` ;
4. remplacer `GOOGLE_REFRESH_TOKEN` par le token genere pour ce compte ;
5. tester les notifications de diffusion, rendez-vous et estimation ;
6. conserver l'ancien token en secours le temps de valider.

### Double authentification Google

La double authentification Google ne bloque pas le projet si l'envoi reste en OAuth/Gmail API.

Elle intervient seulement au moment ou un administrateur connecte le compte `accueil@gti-immobilier.fr` pour donner le consentement Gmail API et obtenir un refresh token.

Une fois le refresh token genere, le backend peut renouveler ses access tokens sans redemander la double authentification a chaque email.

Points d'attention :

- si le mot de passe du compte est change, Google peut revoquer les tokens OAuth Gmail ;
- si l'acces de l'application est retire dans Google, les notifications s'arretent ;
- si le compte est suspendu ou sans Gmail actif, les notifications s'arretent ;
- si on utilise SMTP classique avec mot de passe, la double authentification impose generalement un mot de passe d'application ;
- si l'organisation impose uniquement des cles de securite comme methode 2FA, les mots de passe d'application peuvent etre indisponibles.

Conclusion :

- OAuth/Gmail API est compatible avec 2FA ;
- SMTP avec mot de passe Google est a eviter ;
- `accueil@gti-immobilier.fr` est le meilleur compte cible court terme ;
- Domain Wide Delegation reste une evolution future pour les agents IA et l'orchestrateur, pas une obligation immediate pour les notifications existantes.

### Validation Google Workspace Domain Wide Delegation

Le 2026-06-01, un outil Gmail Workspace separe a ete ajoute cote backend, sans remplacer le service de notifications existant.

Outil valide :

- envoi Gmail au nom de `frederic.gerphagnon@gti-immobilier.fr` ;
- envoi Gmail au nom de `accueil@gti-immobilier.fr` ;
- journalisation dans `public.app_google_workspace_action_log` avec `action_type = gmail.send` ;
- pas de stockage du corps email ni de l'objet complet dans l'audit, seulement des metadonnees limitees.

Decision :

- conserver temporairement `NotificationService` pour les notifications metier existantes ;
- utiliser le nouvel outil Gmail Workspace pour les futures fonctions modernes ;
- migrer les notifications systeme vers `accueil@gti-immobilier.fr` dans une etape dediee, apres validation fonctionnelle des templates.

### Evolution future

Quand l'orchestrateur Google Workspace sera ajoute :

- garder les notifications systeme sur `accueil@gti-immobilier.fr` ;
- utiliser Domain Wide Delegation seulement pour les actions necessitant une execution au nom d'un collaborateur ;
- journaliser chaque action agent : acteur, compte impersonne, scope Google, objet metier, resultat ;
- limiter les scopes au strict necessaire.
