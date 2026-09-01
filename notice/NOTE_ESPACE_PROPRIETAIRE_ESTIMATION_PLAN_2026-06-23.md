# Plan — Email estimation + PDF « avis de valeur » archivé & tracké

> Document de travail. **Direction finale arrêtée le 2026-06-24** (a pivoté depuis un
> « espace client web » vers une approche plus simple et plus durable). Méthode : audit →
> plan → impl, **STOP entre lots**, **dry-run d'abord**. Backend FastAPI (Render) + worker
> Console (Node, Windows) + front `hektor-v1`. Déploiement front `git push origin refonte-mobile:main`.

## 1. Objectif

Depuis le bouton **« Envoyer dossier »** du listing Estimations :
1. **Générer un PDF « avis de valeur » professionnel** du bien.
2. **L'archiver comme document du dossier** (archive locale + Supabase) **et le pousser dans
   les documents Hektor** de l'annonce → le PDF reste dans le dossier, comme les autres docs.
3. **Envoyer au propriétaire un email soigné** avec un bouton **« Récupérer mon estimation »**.
4. **Tracer** : ouverture du mail (pixel) + clic sur le bouton (signal fort) → score côté négo.

**Décision produit (2026-06-24)** : pas d'espace web interactif (jugé peu utile pour un
propriétaire). Email + PDF téléchargeable tracké = l'essentiel, plus simple, et le PDF reste
archivé. Le vCard « ajouter le négo aux contacts » et les actions RDV/question sont **reportés**
(réexaminés plus tard, éventuellement comme liens dans l'email).

## 2. Décisions actées

| # | Décision |
|---|---|
| Approche | Email + **vrai fichier PDF** téléchargeable (pas d'espace web riche) |
| Contenu PDF | Avis de valeur pro : bien (détail annonce : surface, pièces, photos, DPE) + **valeur + fourchette saisies par le négo** + avis/méthodo + fiche négo + mentions |
| Génération PDF | **Côté worker Console (Node)** — rend le HTML de l'avis de valeur en PDF (Puppeteer headless ; fidèle au rendu) |
| Stockage | **Archive locale + bucket Supabase** (`app_console_document`) **+ push Hektor** (`upload_document_to_hektor`) |
| Tracking | Ouverture mail (pixel) + **clic bouton (fort)** → `app_email_envoi`/`app_email_event`, score chaud/tiède/froid |
| Fourchette | **Saisie par le négo** avant envoi (pré-remplie depuis `prix`) |
| Envoi | **Dry-run d'abord** ; envoi réel = lot final, après validation |

## 3. Briques existantes réutilisées (rien à réinventer)

**Documents** (`app_console_document`, bucket `hektor-console-documents`, worker `console_job_worker.js`) :
- Chemin cloud `annonces/{annonce_id}/documents/{doc_id}/avis_de_valeur.pdf` ; archive locale
  `C:\Hektor\HektorConsoleDocuments\annonces\{annonce_id}\documents\{doc_id}\`.
- `persistConsoleDocumentFile()` (local + cloud), `uploadStorageObject()`, `writeLocalArchiveFile()`.
- `handleUploadDocumentToHektor()` (job `upload_document_to_hektor`) = upload vers Hektor +
  upsert `app_console_document` — **réutilisable pour pousser notre PDF dans Hektor**.
- `loadConsoleDocuments()` + `createConsoleDocumentSignedUrl()` (URL signée) pour servir le PDF.
- Scope quotidien `daily-cloud` inclut déjà **`Estimation`** → les estimations sont déjà gérées.

**Email / tracking** (déjà déployé en prod pour les acquéreurs) :
- Tokens HMAC signés (`email_tokens.py`), pixel `/r/o/{token}.png`, clic `/r/feedback|...`.
- `app_email_envoi`/`app_email_event`, scoring, opt-out, plafond quotidien.
- Design email premium (`email_shell`/`email_header`/`email_footer`/`_button`).
- Envoi Google Workspace depuis la boîte du négo (DWD, repli `accueil@`).

**HTML avis de valeur** : `estimationDossierHtml()` créé côté front (App.tsx) — **à porter
côté worker** (ou recréer un template worker) pour le rendu Puppeteer.

## 4. Lots (STOP à chaque fin)

### Lot 1 — Génération + archivage du PDF (worker)
- Ajouter la génération PDF au worker : **Puppeteer** (headless Chromium) rend le HTML avis
  de valeur en PDF A4. (Alternative plus légère : `pdfkit`, mais redessin manuel — à trancher
  au démarrage selon contrainte d'install sur le service Windows.)
- Template/HTML avis de valeur **côté worker** (port de `estimationDossierHtml`), pré-rempli :
  détail annonce (`app_dossier_detail_current`) + valeur/fourchette + texte négo.
- Nouveau `job_type` (ex. `generate_estimation_pdf`) : charge le détail → génère le HTML →
  Puppeteer → buffer PDF → `persistConsoleDocumentFile`-like (local + cloud, source dédiée
  ex. `app_generated_estimation`) → **push Hektor** (réutilise le flux `upload_document_to_hektor`).
- Front : bouton « Envoyer dossier » → **saisie fourchette** (basse / estimée / haute) → crée
  le job → feedback de progression (le PDF apparaît ensuite dans les documents du dossier).
- **STOP** : valider le PDF (rendu, archivé local+Supabase, présent dans Hektor).

### Lot 2 — Email + tracking (dry-run)
- `email_tokens.py` : action `estim` ; lien tracké vers le PDF.
- Template email « votre estimation est disponible » (design premium) + version texte.
- `POST /emails/estimation/send` = chokepoint **dry-run** : filtre opt-out → crée
  `app_email_envoi` (type estimation) → mail avec bouton **« Récupérer mon estimation »** →
  URL `/r/...` qui **log le clic puis redirige vers l'URL signée du PDF**.
- Pixel ouverture + clic → score ; (option) chip d'état dans le listing Estimations.
- **STOP** : valider aperçu email + chaîne de tracking en dry-run.

### Lot 3 — Envoi réel
- Vérifier DKIM/DMARC, plafond, mailbox négo (repli `accueil@`).
- Test E2E contrôlé (adresse interne) puis nettoyage.
- **STOP obligatoire avant le 1er envoi réel** (`email_real_send_enabled`).

## 5. Points de vigilance

- **Puppeteer sur le worker Windows** : embarque Chromium (~poids install). Vérifier que le
  service Windows peut le lancer (sandbox, chemins). Sinon repli `pdfkit` (PDF dessiné, plus
  léger, moins fidèle au HTML). **À trancher au tout début du Lot 1.**
- **Push Hektor = écriture** (`upload_uploadeddoc.php`) : respecter les gardes existantes du
  worker ; le PDF doit être généré **à la demande** (au clic « Envoyer dossier »), pas dépendre
  du **run quotidien documents** (actuellement bloqué, sera activé local+Supabase par l'utilisateur).
- **Code front Lot 3 déjà déployé** (avis de valeur imprimable + composeur Gmail) : sera
  **remplacé** par le nouveau flux (saisie fourchette → job worker). Retirer/adapter proprement.
- **STOP avant migration** (si nouvelle source/colonne `app_console_document` ou champ) et
  **avant 1er envoi réel**.
- Réutilisation **additive** : ne pas casser l'email/espace acquéreur existant.

## 6. Reste à trancher au démarrage du Lot 1

1. **Puppeteer vs pdfkit** (selon faisabilité d'install sur le service Windows).
2. **Source/type** du document généré dans `app_console_document` (ex. `app_generated_estimation`,
   visibility `shared` ou `private`, `document_type` = « Avis de valeur »).
3. Le bouton « Envoyer dossier » : génère le PDF **puis** propose l'envoi mail, ou les deux en
   un seul geste ?
