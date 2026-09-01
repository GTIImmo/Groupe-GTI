# Plan — Avis de valeur PREMIUM (6 pages) : design maquette + saisie négo + DVF

> Suite du chantier [[feature-pdf-estimation-mail]] (Lots 1-2 faits : génération PDF
> worker + email tracké). Ici : remplacer le PDF simple actuel (`estimationAvisValeurHtml`,
> 1 page) par le **document pro 6 pages** de la maquette Claude Design
> (`C:\Users\admin\Downloads\Avis de valeur GTI.html`). Décision user (2026-06-24) :
> **doc complet + saisie négo si donnée absente + données marché DVF.** Méthode : lots, STOP entre lots.

## Maquette (référence)
Charte : magenta `#c5005f`, titres **Spectral** serif, corps **Inter**, A4. 6 pages :
1. **Couverture** : header dégradé sombre + logo, photo héro pleine largeur, « Avis de valeur »
   (Spectral 50px), bien, localité, tags (surface/pièces/terrain/DPE), bloc réf/propriétaire/conseiller/date+validité.
2. **Bien** : galerie photos, caractéristiques (type/surface/terrain/année/pièces/chambres/SdE/garage), DPE+GES, descriptif.
3. **État & diagnostics** : note d'état (étoiles), chauffage/expo/toiture/menuiseries, points forts / vigilance, méthode, diagnostics, charges annuelles.
4. **Valeur & marché** : valeur vénale (gros chiffre + jauge bas/conseillé/haut), prix/m², marché (prix moyen, délai, acquéreurs), graphique évolution prix.
5-6. **Comparables** (ventes similaires) + **conclusion / signature**.

## Écart de données (ce qui pilote les lots)
- ✅ **On a** : titre, bien, localité, valeur+fourchette, négo, réf, date, photos annonce.
- ⚠️ **Détail annonce** (à charger) : surface, pièces, terrain, DPE/GES, descriptif, année.
- ❌ **Saisie négo** : état, chauffage/expo/toiture/menuiseries, points forts/vigilance, méthode, validité, charges (taxe foncière, énergie, eau, assurance), diagnostics.
- ❌ **DVF (open data)** : comparables, prix moyen €/m², délai de vente, évolution prix, nb acquéreurs (acquéreurs = peut venir de nos recherches Supabase, pas DVF).

## Lots (STOP entre lots)

### Lot A — Port du DESIGN 6 pages dans le worker (données qu'on a + détail)
- Porter le HTML/CSS de la maquette dans `estimationAvisValeurHtml` (worker), **fidèle** (Spectral/Inter/magenta, A4, @page).
- Brancher : couverture + page Bien + page Valeur avec les données **système** (charger le **détail annonce** côté worker : photos, surface, pièces, terrain, DPE/GES, descriptif, année) + valeur/fourchette/négo déjà au payload.
- Sections sans données (état, charges, marché, comparables) : **placeholders « à compléter »** ou masquées proprement (le doc reste beau et cohérent).
- Polices : embarquer Spectral/Inter (déjà des @font-face dans la maquette) ou Google Fonts (Playwright charge le réseau).
- **STOP** : valider le rendu 6 pages avec données réelles.

### Lot B — Saisie négo (champs éditoriaux/manquants)
- Étendre la modale (ou éditeur dédié) : état, points forts/vigilance, méthode, validité, charges, chauffage/expo/toiture, diagnostics.
- Passer ces champs au payload → remplir les pages 2-3.
- **STOP** : valider le formulaire + rendu.

### Lot 3 (FIN DE CHANTIER) — Envoi réel de l'email estimation
- Demandé par l'utilisateur : à prévoir **à la fin du dev**. Active l'envoi réel de
  l'email « estimation disponible » (aujourd'hui en dry-run) : `EMAIL_REAL_SEND_ENABLED=true`
  sur Render + worker, vérifier **DKIM + DMARC** (gti-immobilier.fr, La Boîte Immo), plafond
  quotidien, mailbox négo (repli `accueil@`). Test E2E réel contrôlé puis nettoyage.
  **STOP obligatoire avant le 1er envoi réel.** (Cf. [[email-rapprochement-tinder]] pour l'état DKIM/DMARC.)

### Lot C — Données marché DVF
- Intégrer **DVF** (Demandes de Valeurs Foncières, data.gouv / API) : ventes comparables géolocalisées (rayon, type, surface), prix moyen €/m², évolution annuelle.
- Alimenter page 4 (marché + graphique) + pages 5-6 (comparables). Nb « acquéreurs en recherche » = depuis nos recherches Supabase (rapprochement), pas DVF.
- **STOP** : valider la fiabilité des comparables (DVF a du bruit : filtrer type/surface/période).

## Vigilance
- **Charge données worker** : le worker doit charger le détail annonce (app_dossier_detail_current) ; photos = `images_preview_json`/`photo_url_listing` (URLs CDN, Playwright les charge).
- **Poids PDF** : 6 pages + photos → vérifier la taille ; Playwright `page.pdf` gère le multi-page (CSS `.page{page-break-after}`).
- **DVF** : open data, fiabilité variable → toujours afficher « à titre indicatif », filtrer agressivement.
- **Fallback gracieux** : toute donnée absente ne doit jamais casser le rendu (placeholders).
- Le PDF généré continue d'alimenter le Lot 2 (email + download) sans changement de plomberie.
