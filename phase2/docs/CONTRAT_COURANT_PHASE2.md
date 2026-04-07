# Contrat courant de phase 2

Document technique genere a partir du nouveau socle `pipeline/` et `rules/`.

## Workflow central

- workflow principal courant : `mandat_diffusion`

## Entites couvertes

- `dossiers` : Dossiers | source `app_dossier` | Pivot metier interne reliant annonce, mandat et surcouche app.
- `annonces` : Annonces | source `hektor.case_dossier_source + hektor.hektor_annonce` | Base de lecture du bien, du contexte commercial et de l'etat source.
- `mandats` : Mandats | source `hektor.hektor_mandat` | Cadre administratif du dossier, distinct des numeros metier.
- `transactions` : Transactions | source `hektor.hektor_offre + hektor.hektor_compromis + hektor.hektor_vente` | Cycle offre, compromis, vente.
- `contacts` : Contacts | source `hektor.hektor_annonce_detail / proprietaires_json` | Personnes rattachees au dossier et informations utiles de contact.
- `passerelles_diffusion` : Passerelles diffusion | source `hektor.hektor_annonce_broadcast_state` | Etat reel de diffusion par portail et erreurs associees.
- `surcouche_interne` : Surcouche interne | source `app_work_item + app_internal_status + app_note + app_followup + app_blocker` | Pilotage interne, relances, blocages, commentaires et priorites.

## Vues de consommation

- `app_view_demandes_mandat_diffusion` : Demandes mandat / diffusion | 1 ligne = 1 dossier a traiter | File de travail administrative autour de la diffusion et du mandat.
- `app_view_generale` : Vue generale | 1 ligne = 1 dossier | Point d'entree transverse pour lire l'etat global d'un dossier.

## Etats metier de reference

- validation diffusion : `a_controler`, `en_attente_commercial`, `valide`, `refuse`
- visibilite : `non_diffusable`, `en_erreur`, `visible`, `diffusable_non_visible`, `a_verifier`
- statut global : `Sans mandat`, `A valider`, `Valide`, `Diffuse`, `Offre recue`, `Offre validee`, `Compromis fixe`, `Compromis signe`, `Vente fixee`, `Vendu`, `Annule`
- sous-statut : `Estimation`, `Mandat attendu`, `Demande envoyee`, `Non diffuse`, `Diffusion minimale`, `Diffuse multi-portails`, `Mail recu`, `En attente compromis`, `Date fixee`, `Dossier notaire`, `Date acte fixee`, `Annule sans mandat`, `Annule apres offre`, `Mandat annule`, `Vente recente`, `Cloture administrative`
- alertes : `Bloque`, `Erreur diffusion`, `A relancer`
