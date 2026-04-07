from __future__ import annotations


WORKFLOW_MANDAT_DIFFUSION = "mandat_diffusion"


EVENT_TYPE_LABELS: dict[str, str] = {
    "demande_diffusion": "Demande diffusion",
    "baisse_prix": "Avenant baisse prix",
    "annulation_mandat": "Annulation mandat",
    "mandat_actif_non_diffusable": "Mandat actif non diffusable",
    "diffusable_non_visible": "Bien diffusable non visible",
    "mandat_archive_cloture": "Mandat archive avec cloture",
    "mandat_non_diffuse": "Mandat non diffuse",
    "bien_non_visible": "Bien non visible",
    "piece_manquante": "Piece manquante",
    "donnee_incomplete": "Donnee incomplete",
}


VALIDATION_DIFFUSION_STATES: tuple[str, ...] = (
    "a_controler",
    "en_attente_commercial",
    "valide",
    "refuse",
)


VISIBILITY_STATES: tuple[str, ...] = (
    "non_diffusable",
    "en_erreur",
    "visible",
    "diffusable_non_visible",
    "a_verifier",
)


GLOBAL_STATUSES: tuple[str, ...] = (
    "Sans mandat",
    "A valider",
    "Valide",
    "Diffuse",
    "Offre recue",
    "Offre validee",
    "Compromis fixe",
    "Compromis signe",
    "Vente fixee",
    "Vendu",
    "Annule",
)


SUB_STATUSES: tuple[str, ...] = (
    "Estimation",
    "Mandat attendu",
    "Demande envoyee",
    "Non diffuse",
    "Diffusion minimale",
    "Diffuse multi-portails",
    "Mail recu",
    "En attente compromis",
    "Date fixee",
    "Dossier notaire",
    "Date acte fixee",
    "Annule sans mandat",
    "Annule apres offre",
    "Mandat annule",
    "Vente recente",
    "Cloture administrative",
)


ALERT_TYPES: tuple[str, ...] = (
    "Bloque",
    "Erreur diffusion",
    "A relancer",
)


def event_type_label(event_type: str | None) -> str | None:
    if not event_type:
        return None
    return EVENT_TYPE_LABELS.get(event_type, event_type)
