from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationPolicy:
    approved_internal_statuses: tuple[str, ...] = ("pret_diffusion",)
    waiting_internal_statuses: tuple[str, ...] = ("en_attente_commercial",)
    approved_source_values: tuple[str, ...] = ("1",)

    def approved_condition(self, *, valide_source_expr: str | None, internal_status_expr: str) -> str:
        approved_internal = " OR ".join(
            f"COALESCE({internal_status_expr}, '') = '{status}'" for status in self.approved_internal_statuses
        )
        approved_source = (
            " OR ".join(f"COALESCE({valide_source_expr}, '0') = '{value}'" for value in self.approved_source_values)
            if valide_source_expr
            else ""
        )
        parts = [part for part in (approved_source, approved_internal) if part]
        return "(" + " OR ".join(parts) + ")" if parts else "(0 = 1)"

    def waiting_condition(self, *, internal_status_expr: str) -> str:
        waiting_internal = " OR ".join(
            f"COALESCE({internal_status_expr}, '') = '{status}'" for status in self.waiting_internal_statuses
        )
        return "(" + waiting_internal + ")" if waiting_internal else "(0 = 1)"


@dataclass(frozen=True)
class OfferPolicy:
    accepted_state: str = "accepted"
    received_event_type: str = "offre_recue"

    def accepted_condition(self, *, offre_state_expr: str, offre_event_date_expr: str) -> str:
        return (
            f"(COALESCE({offre_state_expr}, '') = '{self.accepted_state}' "
            f"AND {offre_event_date_expr} IS NOT NULL)"
        )

    def received_condition(
        self,
        *,
        offre_id_expr: str,
        offre_state_expr: str,
        event_type_expr: str,
    ) -> str:
        return (
            f"({event_type_expr} = '{self.received_event_type}' "
            f"OR ({offre_id_expr} IS NOT NULL AND COALESCE({offre_state_expr}, '') <> '{self.accepted_state}'))"
        )


VALIDATION_POLICY = ValidationPolicy()
OFFER_POLICY = OfferPolicy()
