# LES ALERTES NE PARTAIENT PLUS — 09/10/2026

> Trouvé en creusant le statut des archives : la surveillance voyait tout et **ne le disait
> à personne depuis au moins un mois**. Corrigé le jour même.
> Matière du **chantier ④ « aucun échec silencieux »** : c'est le défaut silencieux ultime,
> puisque c'est le dispositif d'alerte lui-même qui était muet.

---

## 1. LE FAIT

```
360 sondes conservees  (09/09 -> 09/10, un mois)
 19 ont tente d'envoyer une alerte
  0 y est parvenue        « [alert] email echoue: Connection unexpectedly closed »
    WhatsApp : « WHATSAPP_ALERT_WEBHOOK absent »  -- jamais configure
```

Les `critical` du 09/10 — `relation_disparue`, `travaux_en_erreur`, `gti_descente` code 1 —
**n'ont jamais été envoyés**. C'est Frédéric qui a vu le problème des archives, pas la sonde.

## 2. LE DIAGNOSTIC, étape par étape

Éliminés par la mesure, dans l'ordre :

| | verdict |
|---|---|
| le code | ✅ correct — STARTTLS bien appelé avec `SMTP_SECURE=false`, délai 20 s |
| la configuration | ✅ complète et chargée (`.env` racine) |
| le réseau | ✅ testé : TCP OK, `EHLO 250`, **STARTTLS OK** sur 587, sans se connecter |

Puis **un seul email d'essai**, avec l'accord de Frédéric, en capturant l'exception entière :

```
OK   connexion
OK   starttls
>>> ECHEC a l'etape : login (authentification)
    type    : SMTPServerDisconnected
    message : Connection unexpectedly closed
```

Gmail **raccroche sur la commande `AUTH`** : le mot de passe d'application de
`accueil@gti-immobilier.fr` n'est plus valide. *(Aucun message n'est parti : la panne
survient avant l'envoi.)*

## 3. ⭐ LA BONNE SOLUTION EST VENUE DE FRÉDÉRIC

> *« Mon projet a accès à mon compte Google Workspace où il y a l'adresse
> accueil@gti-immobilier.fr, je peux pas envoyer grâce à cet accès ? Ça évite les problèmes
> de changement de mot de passe utilisateur, non ? »*

**Oui — et c'était déjà en place.** Mesuré :

```
GOOGLE_WORKSPACE_AUTH_MODE      domain_wide_delegation
GOOGLE_WORKSPACE_SUBJECT_EMAIL  accueil@gti-immobilier.fr
GOOGLE_WORKSPACE_SCOPES         gmail.send · calendar.freebusy · calendar.events
cle de service                  secrets\google-workspace-service-account.json  (presente)
```

Jeton valide obtenu à l'essai, **sans aucun mot de passe utilisateur**.

**Et le backend s'en servait déjà** : `notification_service.py` l. 185 essaie Workspace
d'abord et ne retombe sur SMTP qu'à défaut. ➡ **Les mails clients n'étaient donc PAS
cassés** — j'avais eu tort de le craindre.

**Le vrai défaut était donc étroit** : la surveillance était la **seule** chose restée sur
l'ancien chemin. Personne ne l'a fait suivre quand le backend est passé au Workspace.

## 4. LE CORRECTIF

`monitoring/check_gti_health.py` : la surveillance reçoit **le même ordre que le backend** —
Workspace d'abord, SMTP en repli.

- `GMAIL_SEND_SCOPE` (une constante, on ne duplique pas le code du backend : la surveillance
  doit tourner **même si le backend est cassé**) ;
- `_has_google_workspace()` — même condition que le backend ;
- `_send_via_workspace()` — un POST `requests` vers l'API Gmail, **la technique exacte du
  backend**, aucune bibliothèque nouvelle ;
- `_send_email()` essaie Workspace, et n'utilise SMTP que si ça échoue.

⚠ **Vérifié avant d'écrire** : `google.oauth2`, `google.auth.transport.requests` et
`requests 2.34.2` sont présents dans **le python du SYSTÈME** — celui qu'utilise la tâche
planifiée, pas le venv. *(Piège déjà payé le matin même avec `openpyxl`.)*

**Épreuve** : compilation OK avec le python du système, CRLF conservés, et **un email d'essai
réellement parti** — aucun message d'erreur, `_has_google_workspace()` rend `True`.

## 5. CE QUI RESTE

- ⏰ **La sonde suivante (19:48) est la vraie preuve** : son journal ne doit plus porter
  `[alert] email echoue`.
- ⬜ **Le second canal n'existe toujours pas.** Le numéro de Frédéric est configuré
  (`0658770893`) mais `WHATSAPP_ALERT_WEBHOOK` n'a jamais été renseigné. **Tant qu'il n'y a
  qu'un canal, sa panne = silence total** — c'est ce qui vient de durer un mois.
- ⬜ `SMTP_PASS` est désormais inutile pour la surveillance. On peut le retirer un jour,
  mais il reste le filet, donc rien ne presse.
- ⚠ **La leçon de fond** : une garde qu'on n'a jamais vue se déclencher n'est pas une garde.
  Personne n'avait jamais vérifié qu'une alerte **arrivait**.

---

## 6. 10/10 — LE CORRECTIF NE MARCHAIT PAS, ET POURQUOI

Le run du 10/10 l'a dit tout de suite :

```
[alert] workspace echoue: ModuleNotFoundError: No module named 'requests'
[alert] repli sur SMTP
[alert] email echoue: Connection unexpectedly closed
```

⭐ **Le repli a bien joué** — la mécanique était juste. C'est l'environnement qui manquait.

### Mon erreur : j'ai vérifié le mauvais interpréteur

J'avais écrit *« vérifié dans le python du SYSTÈME »*. J'avais testé
`C:\Python314\python.exe` **depuis ma session**, qui voit le site-packages de
l'**utilisateur** (`AppData\Roaming\Python\Python314\site-packages`). **La tâche planifiée
ne le voit pas.** Reproduit avec `python -s` (= le contexte de la tâche) :

```
requests                        NON
google.oauth2.service_account   NON
google.auth.transport.requests  NON
urllib.request / json / base64  OUI   (bibliotheque standard seulement)
```

**Rien de Google n'était disponible.** Et on ne peut pas s'en passer : signer le jeton
demande du RSA, que la bibliothèque standard n'a pas.

### Le correctif : le lanceur préfère le venv du projet

`monitoring/run_gti_health.ps1` — **même patron que `run_archived_annonce_details.ps1`** :

```powershell
$Python = $env:GTI_MONITOR_PYTHON          # garde la priorite
if (-not $Python) {
    $VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    if (Test-Path -LiteralPath $VenvPython) { $Python = $VenvPython }
}
if (-not $Python) { ...l'ancien comportement, mot pour mot... }
```

### Les épreuves

```
parseur PowerShell OK, BOM et CRLF conserves
le venv, avec -s : requests + google.oauth2 + google.auth.transport  ->  TOUS presents
la sonde entiere lancee par le venv, --no-alerts --dry-run : 70 controles, 0 « unknown »
   comparee controle par controle a la tache de 07:48 : un seul ecart, la sonde des
   taches planifiees -- et il vient de MON mode de lancement, pas du venv
le LANCEUR relance en vrai a 08:23 : « interpreteur : ...\.venv\Scripts\python.exe »,
   71 controles, AUCUNE ligne [alert]
UN EMAIL d'essai envoye depuis l'environnement EXACT de la tache (venv + -s) : PARTI,
   aucune erreur, `_has_google_workspace()` rend True
```

⏰ **La vraie preuve reste la prochaine bascule vers critical** : l'alerte ne part que sur un
changement d'état, pas à chaque sonde.

### La leçon, et elle est générale

**Vérifier une dépendance, c'est la vérifier dans l'interpréteur ET le contexte de celui qui
l'exécutera.** `python -c "import X"` depuis une session interactive ne prouve rien pour une
tâche planifiée : `python -s -c "import X"` si.
