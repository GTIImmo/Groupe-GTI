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

---

## 7. ⭐⭐ 11/10 — DOSSIER CLOS : **LE MAIL EST ARRIVÉ**

> **Frédéric, 11/10 au matin : *« c'est bizarre, j'ai pas eu de mail pour me dire que tout est
> revenu à la normale, donc le monitoring doit avoir encore des erreurs »*.**
> Il avait raison de douter — et la cause n'était pas une panne.

### Pourquoi elle se taisait

La sonde voyait **3 critical** et n'envoyait rien, parce que la règle
(`check_gti_health.py:2843`) n'envoie que sur **bascule** vers critical, et un « retour à la
normale » exige **ZÉRO** critical :

```python
newly_critical = [r for r in criticals if previous_status.get(r.status_key) != "critical"]
if newly_critical:                      dispatch(newly_critical, "critical")
elif had_critical and not criticals:    dispatch([], "recovery")
```

➡ **Les 3 l'étant depuis des jours, elle était coincée** : rien de neuf à annoncer, et pas le
droit d'annoncer le retour. ⚠ **C'est un défaut de fond : un seul critical permanent rend la
surveillance muette sur tout le reste du tableau.**

### Les 3 critical, 2 causes — toutes deux déjà connues du projet

```
data.travaux_en_erreur    24 travaux   12 TypeError DEJA CORRIGES le 06/10 (3607d29)
                                      + 6 du contact fantome (reporte le 09/10)
                                      + 3 « database is locked » (note le 06/10)
                                      + 1 timeout 90 s · 1 document · 1 unlink non prouve
data.contact_conflit       1 ligne  ┐  LA MEME : 10076643 MARTIN Mickael, cible
data.contact_push_bloque   1 ligne  ┘  Hektor 145561 qui N'EXISTE PLUS
```

**Deux patchs, appliqués par Frédéric depuis son téléphone** *(mes écritures Supabase restent
refusées par le garde-fou de session — « Production Deploy » ; je ne l'ai pas contourné)* :

```
07:42:38  patch_purge_erreurs_infra_2026-10-11.sql                  24 -> 0
~07:5x    patch_saisie_en_attente_contact_fantome_2026-10-11.sql     1 -> 0
```

⭐ **Un garde-fou neuf dans chacun** : le premier refuse si une saisie en attente
**repartirait** ; le second refuse si la saisie **n'est pas déjà appliquée chez nous** — et
c'est lui qui a garanti C.1'. *(Mesuré : la civilité « M. » était bien déjà dans
`app_contact_current`. Et il a au passage corrigé ma lecture du 09/10 : les 7 champs n'étaient
pas identiques, il y en avait **un** de différent.)*

### ✅ LA PREUVE, sur le terrain, enfin

Sonde de **09:48:55 → 09:52:18, code 0** :

```
71 controles : 65 ok · 6 warning · 0 CRITICAL
une seule ligne [alert] : « whatsapp ignore: WHATSAPP_ALERT_WEBHOOK absent »
   -> AUCUNE ligne « email echoue »   (le 10/10 : « Connection unexpectedly closed »)
interpreteur : C:\Hektor\Projet\.venv\Scripts\python.exe
```

**Et Frédéric a reçu le mail.** ➡ La chaîne entière est prouvée **par une vraie bascule**, et
plus par un essai manuel : le lanceur prend le venv → `requests` et `google.auth` sont là → la
clé de service Workspace signe → le mail part → **il arrive**.

**Après au moins un mois de silence** *(19 tentatives, 0 succès sur 360 sondes)*.

### ⬜ Ce qui reste, et c'est le même point qu'au §5

```
WHATSAPP_ALERT_WEBHOOK   TOUJOURS absent   -> IL N'Y A QU'UN SEUL CANAL
```

⚠ **C'est littéralement la ligne que la sonde imprime à chaque envoi.** Et c'est la cause du
mois de silence : un seul canal, sa panne = silence total. **Le défaut de fond n'est pas
réparé** — on a réparé le canal, pas le fait qu'il soit unique.
