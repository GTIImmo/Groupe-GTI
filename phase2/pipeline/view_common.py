from __future__ import annotations

from phase2.rules.sql_fragments import (
    alerte_principale_case,
    event_type_label_case,
    validation_diffusion_state_case,
    visibility_state_case,
)


SQL_TYPE_DEMANDE_LABEL = event_type_label_case("wi.event_type")
SQL_VALIDATION_DIFFUSION_DEMANDES = validation_diffusion_state_case(
    work_status_expr="wi.status",
    internal_status_expr="ist.internal_status",
    valide_source_expr=None,
)
SQL_ETAT_VISIBILITE = visibility_state_case(
    diffusable_expr="src.diffusable",
    has_diffusion_error_expr="ba.has_diffusion_error",
    nb_portails_actifs_expr="ba.nb_portails_actifs",
)
SQL_VALIDATION_DIFFUSION_GENERALE = """
CASE
    WHEN COALESCE(src.valide, '0') = '1' THEN 'valide'
    ELSE 'a_controler'
END
""".strip()
SQL_ALERTE_PRINCIPALE = alerte_principale_case(
    has_open_blocker_expr="ob.has_open_blocker",
    has_diffusion_error_expr="ba.has_diffusion_error",
    date_relance_prevue_expr="lf.date_relance_prevue",
)
