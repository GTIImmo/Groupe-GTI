from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EntityContract:
    """Contrat minimal d'un objet metier consolide."""

    key: str
    label: str
    source_table: str
    description: str


@dataclass(frozen=True)
class ViewContract:
    """Contrat minimal d'une vue de consommation de phase 2."""

    key: str
    label: str
    sql_name: str
    grain: str
    purpose: str


ENTITY_CONTRACTS: tuple[EntityContract, ...] = (
    EntityContract(
        key="dossiers",
        label="Dossiers",
        source_table="app_dossier",
        description="Pivot metier interne reliant annonce, mandat et surcouche app.",
    ),
    EntityContract(
        key="annonces",
        label="Annonces",
        source_table="hektor.case_dossier_source + hektor.hektor_annonce",
        description="Base de lecture du bien, du contexte commercial et de l'etat source.",
    ),
    EntityContract(
        key="mandats",
        label="Mandats",
        source_table="hektor.hektor_mandat",
        description="Cadre administratif du dossier, distinct des numeros metier.",
    ),
    EntityContract(
        key="transactions",
        label="Transactions",
        source_table="hektor.hektor_offre + hektor.hektor_compromis + hektor.hektor_vente",
        description="Cycle offre, compromis, vente.",
    ),
    EntityContract(
        key="contacts",
        label="Contacts",
        source_table="hektor.hektor_annonce_detail / proprietaires_json",
        description="Personnes rattachees au dossier et informations utiles de contact.",
    ),
    EntityContract(
        key="passerelles_diffusion",
        label="Passerelles diffusion",
        source_table="hektor.hektor_annonce_broadcast_state",
        description="Etat reel de diffusion par portail et erreurs associees.",
    ),
    EntityContract(
        key="surcouche_interne",
        label="Surcouche interne",
        source_table="app_work_item + app_internal_status + app_note + app_followup + app_blocker",
        description="Pilotage interne, relances, blocages, commentaires et priorites.",
    ),
)


VIEW_CONTRACTS: tuple[ViewContract, ...] = (
    ViewContract(
        key="demandes_mandat_diffusion",
        label="Demandes mandat / diffusion",
        sql_name="app_view_demandes_mandat_diffusion",
        grain="1 ligne = 1 dossier a traiter",
        purpose="File de travail administrative autour de la diffusion et du mandat.",
    ),
    ViewContract(
        key="vue_generale",
        label="Vue generale",
        sql_name="app_view_generale",
        grain="1 ligne = 1 dossier",
        purpose="Point d'entree transverse pour lire l'etat global d'un dossier.",
    ),
)


def build_domain_inventory() -> dict[str, list[dict[str, str]]]:
    """Expose un inventaire simple reutilisable en debug, sync ou documentation."""

    return {
        "entities": [
            {
                "key": contract.key,
                "label": contract.label,
                "source_table": contract.source_table,
                "description": contract.description,
            }
            for contract in ENTITY_CONTRACTS
        ],
        "views": [
            {
                "key": contract.key,
                "label": contract.label,
                "sql_name": contract.sql_name,
                "grain": contract.grain,
                "purpose": contract.purpose,
            }
            for contract in VIEW_CONTRACTS
        ],
    }
