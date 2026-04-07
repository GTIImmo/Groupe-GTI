from __future__ import annotations

from phase2.rules.status_policy import VALIDATION_POLICY


def event_type_label_case(event_type_expr: str) -> str:
    return f"""
CASE {event_type_expr}
    WHEN 'demande_diffusion' THEN 'Demande diffusion'
    WHEN 'baisse_prix' THEN 'Avenant baisse prix'
    WHEN 'annulation_mandat' THEN 'Annulation mandat'
    WHEN 'mandat_actif_non_diffusable' THEN 'Mandat actif non diffusable'
    WHEN 'diffusable_non_visible' THEN 'Bien diffusable non visible'
    WHEN 'mandat_archive_cloture' THEN 'Mandat archive avec cloture'
    WHEN 'mandat_non_diffuse' THEN 'Mandat non diffuse'
    WHEN 'bien_non_visible' THEN 'Bien non visible'
    WHEN 'piece_manquante' THEN 'Piece manquante'
    WHEN 'donnee_incomplete' THEN 'Donnee incomplete'
    ELSE {event_type_expr}
END
""".strip()


def validation_diffusion_state_case(
    *,
    work_status_expr: str,
    internal_status_expr: str,
    valide_source_expr: str | None = None,
) -> str:
    waiting_condition = VALIDATION_POLICY.waiting_condition(internal_status_expr=internal_status_expr)
    approved_condition = VALIDATION_POLICY.approved_condition(
        valide_source_expr=valide_source_expr,
        internal_status_expr=internal_status_expr,
    )
    return f"""
CASE
    WHEN COALESCE({work_status_expr}, '') = 'refused' THEN 'refuse'
    WHEN {waiting_condition} THEN 'en_attente_commercial'
    WHEN {approved_condition} THEN 'valide'
    ELSE 'a_controler'
END
""".strip()


def visibility_state_case(
    *,
    diffusable_expr: str,
    has_diffusion_error_expr: str,
    nb_portails_actifs_expr: str,
) -> str:
    return f"""
CASE
    WHEN COALESCE({diffusable_expr}, '0') <> '1' THEN 'non_diffusable'
    WHEN COALESCE({has_diffusion_error_expr}, 0) = 1 THEN 'en_erreur'
    WHEN COALESCE({nb_portails_actifs_expr}, 0) > 0 THEN 'visible'
    WHEN COALESCE({diffusable_expr}, '0') = '1' AND COALESCE({nb_portails_actifs_expr}, 0) = 0 THEN 'diffusable_non_visible'
    ELSE 'a_verifier'
END
""".strip()


def alerte_principale_case(
    *,
    has_open_blocker_expr: str,
    has_diffusion_error_expr: str,
    date_relance_prevue_expr: str,
) -> str:
    return f"""
CASE
    WHEN COALESCE({has_open_blocker_expr}, 0) = 1 THEN 'Bloque'
    WHEN COALESCE({has_diffusion_error_expr}, 0) = 1 THEN 'Erreur diffusion'
    WHEN {date_relance_prevue_expr} IS NOT NULL
         AND {date_relance_prevue_expr} <= date('now') THEN 'A relancer'
    ELSE NULL
END
""".strip()
