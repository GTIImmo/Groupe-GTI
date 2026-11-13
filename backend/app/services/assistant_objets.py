from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

# ---------------------------------------------------------------------------
# Assistant IA (12/11/2026, étape 2) -- LA LISTE FERMÉE DE CE QUE L'ASSISTANT PEUT LIRE.
# Note : notice/ETAPE2_AGENT_QUI_REPOND_AUDIT_2026-11-12.md §4. Décision de Frédéric le 12/11 :
# « oui » à la liste fermée (à l'intérieur, l'assistant cherche, filtre et compte librement).
#
# ⛔ LISTE BLANCHE : un objet absent d'ici ne se lit pas, une colonne absente non plus.
# ⛔ Chaque SOURCE est une vue ou une table dont les règles de lecture portent DÉJÀ le
#   périmètre (mesuré le 12/11) : la lecture part avec le jeton de la personne, la base fait le tri.
#   Jamais une table « lisible par tous » seule (notes et conditions de transaction, notifications…) :
#   les notes passent par la fonction notes_transaction (après l'affaire), les notifications ont un
#   filtre IMPOSÉ sur l'e-mail de la personne, comme l'écran (App.tsx:26315).
# ⛔ Jamais une des 20 fonctions de lecture de l'écran qui ne contrôlent pas l'appelant.
#
# Types : `nombre`, `date` (texte AAAA-MM-JJ… comparable dans l'ordre), `texte`, `booleen`, `json`.
# ⚠ Plusieurs montants et bornes sont stockés en TEXTE (prix des recherches, montant des
#   transactions) : ils ne se comparent PAS (« 90000 » > « 200000 » en texte). Typés `texte` ici,
#   donc seulement égal / parmi / vide. À corriger un jour par des vues typées (base).
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Colonne:
    nom: str
    type: str
    description: str


@dataclass(frozen=True)
class Objet:
    nom: str
    source: str
    description: str
    colonnes: tuple[Colonne, ...]
    par_defaut: tuple[str, ...]
    cle: str
    # filtres posés par NOTRE serveur, que l'IA ne voit ni ne peut retirer (params PostgREST)
    filtres_imposes: Callable[[str | None], list[tuple[str, str]]] = field(default=lambda email: [])

    def colonne(self, nom: str) -> Colonne | None:
        return next((c for c in self.colonnes if c.nom == nom), None)


def C(nom: str, type_: str, description: str) -> Colonne:
    return Colonne(nom, type_, description)


_BIEN_COMMUNES = (
    C("numero_dossier", "texte", "numéro de dossier de l'agence"),
    C("numero_mandat", "texte", "numéro du mandat"),
    C("titre_bien", "texte", "titre de l'annonce"),
    C("type_bien", "texte", "Maison, Appartement, Terrain…"),
    C("ville", "texte", "commune du bien"),
    C("code_postal", "texte", "code postal"),
    C("prix", "nombre", "prix affiché en euros"),
    C("statut_annonce", "texte", "Actif, Sous offre, Sous compromis, Vendu, Clos, Estimation…"),
    C("offre_type", "texte", "vente ou location"),
    C("commercial_nom", "texte", "négociateur du bien"),
    C("negociateur_email", "texte", "e-mail du négociateur"),
    C("agence_nom", "texte", "agence"),
    C("mandat_type", "texte", "simple, exclusif…"),
    C("mandat_date_debut", "date", "début du mandat"),
    C("mandat_date_fin", "date", "fin du mandat"),
    C("mandat_montant", "nombre", "prix du mandat en euros"),
    C("mandants_texte", "texte", "noms des mandants"),
)

OBJETS: tuple[Objet, ...] = (
    Objet(
        "biens", "app_dossiers_current",
        "Les biens VIVANTS (en vente, sous offre, sous compromis, estimations). Par défaut l'écran cache les "
        "« Estimation » : précise-le si tu les comptes. Les vendus/clos sont dans biens_historique.",
        (C("app_dossier_id", "nombre", "identifiant du bien dans l'app (clé)"),
         C("hektor_annonce_id", "nombre", "numéro de l'annonce (celui qu'on cite, ex. 63330)"),
         *_BIEN_COMMUNES,
         C("archive", "texte", "'1' = archivé, '0' = non"),
         C("diffusable", "texte", "'1' = diffusable sur les portails"),
         C("validation_diffusion_state", "texte", "état de la validation de diffusion"),
         C("nb_portails_actifs", "nombre", "nombre de portails où l'annonce est diffusée"),
         C("portails_resume", "texte", "portails de diffusion"),
         C("has_diffusion_error", "booleen", "erreur de diffusion"),
         C("offre_state", "texte", "état de l'offre en cours"),
         C("compromis_state", "texte", "état du compromis en cours"),
         C("photo_url_listing", "texte", "photo de couverture ; vide = pas de photo"),
         C("date_enregistrement_annonce", "date", "date de création de l'annonce"),
         C("date_relance_prevue", "date", "prochaine relance prévue"),
         C("price_change_last_old_value", "nombre", "ancien prix (dernière baisse ou hausse)"),
         C("price_change_last_new_value", "nombre", "nouveau prix"),
         C("price_change_last_detected_at", "date", "date du dernier changement de prix")),
        ("hektor_annonce_id", "app_dossier_id", "titre_bien", "type_bien", "ville", "prix", "statut_annonce", "commercial_nom"),
        "app_dossier_id",
    ),
    Objet(
        "biens_historique", "app_historical_annonce_index_current",
        "Les biens VENDUS ou CLOS (historique).",
        (C("hektor_annonce_id", "nombre", "numéro de l'annonce"), *_BIEN_COMMUNES,
         C("date_maj", "date", "dernière mise à jour")),
        ("hektor_annonce_id", "titre_bien", "ville", "prix", "statut_annonce", "commercial_nom", "date_maj"),
        "hektor_annonce_id",
    ),
    Objet(
        "biens_archives", "app_archive_annonce_index_current",
        "Les biens ARCHIVÉS.",
        (C("hektor_annonce_id", "nombre", "numéro de l'annonce"), *_BIEN_COMMUNES,
         C("date_maj", "date", "dernière mise à jour")),
        ("hektor_annonce_id", "titre_bien", "ville", "prix", "statut_annonce", "commercial_nom", "date_maj"),
        "hektor_annonce_id",
    ),
    Objet(
        "mandats", "app_v_mandat_statut",
        "Le registre des mandats, avec le statut calculé EXACTEMENT comme l'écran (statut_mandat, etat_mandat).",
        (C("app_dossier_id", "nombre", "identifiant du bien"),
         C("hektor_annonce_id", "nombre", "numéro de l'annonce"),
         *_BIEN_COMMUNES,
         C("mandat_date_cloture", "date", "date de clôture du mandat"),
         C("statut_mandat", "texte", "Actif, Vendu, Clos ou Échu (calcul de l'écran)"),
         C("etat_mandat", "texte", "En cours ou Annulé (calcul de l'écran)"),
         C("register_source_kind", "texte", "'recherche' = mandat de recherche (le pilotage les exclut)")),
        ("numero_mandat", "hektor_annonce_id", "titre_bien", "mandat_type", "mandat_date_fin", "statut_mandat", "commercial_nom"),
        "numero_mandat",
    ),
    Objet(
        "contacts", "app_contacts_current",
        "L'annuaire des contacts (acquéreurs, vendeurs, propriétaires…). Les fiches de ménage sont masquées comme à l'écran.",
        (C("hektor_contact_id", "texte", "numéro du contact (clé)"),
         C("display_name", "texte", "nom affiché"),
         C("civilite", "texte", "civilité"), C("nom", "texte", "nom"), C("prenom", "texte", "prénom"),
         C("email", "texte", "e-mail"), C("phone_primary", "texte", "téléphone"), C("phone_secondary", "texte", "2e téléphone"),
         C("ville", "texte", "ville"), C("code_postal", "texte", "code postal"),
         C("commercial_nom", "texte", "négociateur qui suit le contact"), C("negociateur_email", "texte", "son e-mail"),
         C("agence_nom", "texte", "agence"),
         C("archive", "booleen", "contact archivé"),
         C("date_enregistrement", "date", "date de création"), C("date_maj", "date", "dernière mise à jour"),
         C("relation_roles_json", "json", "rôles : liste parmi mandant, proprietaire, acquereur…"),
         C("active_search_count", "nombre", "nombre de recherches actives"),
         C("linked_annonce_count", "nombre", "nombre de biens liés"),
         C("commentaires", "texte", "commentaire libre")),
        ("hektor_contact_id", "display_name", "phone_primary", "email", "ville", "commercial_nom", "active_search_count"),
        "hektor_contact_id",
        lambda email: [("or", "(couple_role.is.null,couple_role.neq.menage_resolu)")],  # = SANS_FICHE_DE_MENAGE, api.ts:207
    ),
    Objet(
        "recherches", "app_contact_searches_current",
        "Les recherches des acquéreurs (critères). Un contact peut en avoir plusieurs.",
        (C("contact_search_key", "texte", "clé de la recherche"),
         C("hektor_contact_id", "texte", "numéro du contact"),
         C("is_active", "booleen", "recherche active"), C("archive", "booleen", "recherche archivée"),
         C("offre", "texte", "vente ou location"),
         C("villes_json", "json", "villes recherchées"), C("types_json", "json", "types de bien recherchés"),
         C("criteres_json", "json", "autres critères"),
         C("prix_min", "texte", "budget minimum (texte : ne se compare pas)"), C("prix_max", "texte", "budget maximum (texte)"),
         C("surface_min", "texte", "surface minimum (texte)"), C("pieces_min", "texte", "pièces minimum (texte)"),
         C("contact_date_maj", "date", "dernière mise à jour du contact")),
        ("contact_search_key", "hektor_contact_id", "is_active", "villes_json", "types_json", "prix_max"),
        "contact_search_key",
    ),
    Objet(
        "relations", "app_contact_relations_current",
        "Qui est lié à quel bien : mandant, propriétaire, acquéreur, et les transactions vues du contact.",
        (C("hektor_contact_id", "texte", "numéro du contact"),
         C("app_dossier_id", "nombre", "identifiant du bien"), C("hektor_annonce_id", "texte", "numéro de l'annonce"),
         C("numero_dossier", "texte", "numéro de dossier"), C("titre_bien", "texte", "titre du bien"),
         C("role_contact", "texte", "mandant, proprietaire, acquereur…"),
         C("transaction_type", "texte", "offre, compromis, vente"), C("transaction_state", "texte", "état"),
         C("transaction_date", "date", "date"), C("transaction_amount", "texte", "montant (texte)"),
         C("is_active_annonce", "booleen", "le bien est encore vivant"),
         C("proprietaire_depuis", "date", "propriétaire depuis")),
        ("hektor_contact_id", "hektor_annonce_id", "titre_bien", "role_contact", "transaction_type", "transaction_state"),
        "hektor_contact_id",
    ),
    Objet(
        "rapprochements", "app_rapprochement",
        "Les acquéreurs rapprochés d'un bien, avec un score (plus haut = plus pertinent).",
        (C("app_dossier_id", "nombre", "identifiant du bien"),
         C("contact_search_key", "texte", "recherche de l'acquéreur"), C("hektor_contact_id", "texte", "numéro de l'acquéreur"),
         C("score", "nombre", "score de pertinence"), C("eligible", "booleen", "rapprochement retenu"),
         C("first_seen_at", "date", "apparu le"), C("computed_at", "date", "calculé le")),
        ("app_dossier_id", "hektor_contact_id", "contact_search_key", "score", "eligible"),
        "app_dossier_id",
    ),
    Objet(
        "relances", "app_relance_rapprochement",
        "Les relances à faire (rappeler un acquéreur, relancer après une visite…).",
        (C("label", "texte", "intitulé"), C("sub", "texte", "détail"), C("type", "texte", "type de relance"),
         C("due_date", "date", "échéance"), C("status", "texte", "a_faire, fait, reporte…"),
         C("negociateur_email", "texte", "à qui elle revient"),
         C("hektor_contact_id", "texte", "contact"), C("app_dossier_id", "nombre", "bien"),
         C("contact_search_key", "texte", "recherche"), C("created_at", "date", "créée le")),
        ("label", "due_date", "status", "hektor_contact_id", "app_dossier_id", "negociateur_email"),
        "due_date",
    ),
    Objet(
        "transactions", "app_affaire_ledger",
        "Les offres, compromis et ventes (une ligne par étape). Un commercial ne voit que celles de SES biens. "
        "Les notes et conditions se lisent avec la fonction notes_transaction.",
        (C("app_affaire_id", "nombre", "identifiant de la transaction (pour notes_transaction)"),
         C("app_dossier_id", "nombre", "identifiant du bien"), C("hektor_annonce_id", "nombre", "numéro de l'annonce"),
         C("kind", "texte", "offre, compromis ou vente"), C("state", "texte", "état (en cours, acceptée, refusée, annulée…)"),
         C("montant", "texte", "montant en euros (texte : ne se compare pas)"),
         C("date", "date", "date enregistrée de l'étape"), C("date_acte", "date", "date de l'acte"),
         C("date_fin_retractation", "date", "fin du délai de rétractation"),
         C("prix_net_vendeur", "texte", "net vendeur (texte)"), C("commission_agence", "texte", "commission (texte)"),
         C("numero_mandat", "texte", "numéro du mandat"),
         C("notaire_acquereur_nom", "texte", "notaire de l'acquéreur"), C("notaire_mandant_nom", "texte", "notaire du vendeur"),
         C("date_annulation_app", "date", "date d'annulation"), C("motif_annulation_app", "texte", "motif d'annulation"),
         C("app_chaine_id", "nombre", "chaîne offre → compromis → vente")),
        ("app_affaire_id", "hektor_annonce_id", "kind", "state", "montant", "date"),
        "date",
    ),
    Objet(
        "demandes", "app_diffusion_requests_current",
        "Les demandes envoyées aux admins : diffusion, baisse de prix, annulation, corrections.",
        (C("request_type", "texte", "type de demande"), C("request_status", "texte", "état"),
         C("requested_by_name", "texte", "demandée par"), C("requested_at", "date", "demandée le"),
         C("processed_by_name", "texte", "traitée par"), C("processed_at", "date", "traitée le"),
         C("request_comment", "texte", "commentaire"), C("refusal_reason", "texte", "motif de refus"),
         C("numero_dossier", "texte", "dossier"), C("titre_bien", "texte", "bien"), C("commercial_nom", "texte", "négociateur"),
         C("app_dossier_id", "nombre", "identifiant du bien"), C("follow_up_needed", "booleen", "suivi nécessaire")),
        ("request_type", "request_status", "titre_bien", "requested_by_name", "requested_at"),
        "requested_at",
    ),
    Objet(
        "documents", "app_console_document",
        "Les documents des biens (mandat, diagnostics, compromis…). Un commercial ne voit que ceux de SES biens.",
        (C("app_dossier_id", "nombre", "identifiant du bien"), C("hektor_annonce_id", "texte", "numéro de l'annonce"),
         C("document_type", "texte", "type"), C("document_name", "texte", "nom du fichier"),
         C("created_at_hektor", "date", "déposé le"), C("present_in_hektor", "booleen", "présent chez Hektor")),
        ("hektor_annonce_id", "document_type", "document_name", "created_at_hektor"),
        "created_at_hektor",
    ),
    Objet(
        "notifications", "app_notification",
        "TES notifications (et seulement les tiennes).",
        (C("type", "texte", "type"), C("title", "texte", "titre"), C("body", "texte", "texte"),
         C("app_dossier_id", "nombre", "bien concerné"), C("read_at", "date", "lue le (vide = non lue)"),
         C("created_at", "date", "créée le")),
        ("title", "body", "created_at", "read_at"),
        "created_at",
        lambda email: [("negociateur_email", f"eq.{email or ''}")],
    ),
    Objet(
        "negociateurs", "app_user_directory",
        "L'annuaire des négociateurs et collaborateurs.",
        (C("display_name", "texte", "nom"), C("prenom", "texte", "prénom"), C("nom", "texte", "nom de famille"),
         C("email", "texte", "e-mail"), C("tel", "texte", "téléphone"), C("portable", "texte", "portable"),
         C("user_type", "texte", "NEGO = négociateur"), C("site", "texte", "agence")),
        ("display_name", "email", "portable", "site"),
        "display_name",
    ),
)

PAR_NOM = {o.nom: o for o in OBJETS}


def liste_pour_consignes() -> str:
    return "\n".join(f"- {o.nom} : {o.description}" for o in OBJETS)
