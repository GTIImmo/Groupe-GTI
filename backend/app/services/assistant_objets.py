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
#
# ⭐ LES VALEURS DES COLONNES À LISTE (13/11/2026, après la preuve des 30 questions : 5 réponses
#   fausses parce que le modèle DEVINAIT les valeurs -- « exclusif » au lieu de « EXCLUSIF »,
#   « en attente » au lieu de « pending », « Maison » alors que type_bien est un CODE « 1 »).
#   Chaque colonne à liste porte ses valeurs (valeur stockée, libellé), MESURÉES en base le 13/11
#   (`select col, count(*) group by col`) et, pour les codes, reprises des tables de l'écran
#   (App.tsx draftAnnoncePropertyGroups + hektorPropertyTypeLabelsHorsWizard, FAMILLES_OFFRE,
#   ContactSearchFields DEFAULT_OFFER_OPTIONS). Le lecteur traduit ce que dit le modèle vers la
#   valeur stockée, et REFUSE une valeur inconnue au lieu de rendre un zéro muet.
#   ⚠ Une valeur NOUVELLE en base serait refusée jusqu'à son ajout ici : le refus le dit en clair.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Colonne:
    nom: str
    type: str
    description: str
    # (valeur stockée, libellé) ; vide = colonne libre
    valeurs: tuple[tuple[str, str], ...] = ()


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


def C(nom: str, type_: str, description: str, valeurs: tuple[tuple[str, str], ...] = ()) -> Colonne:
    return Colonne(nom, type_, description, valeurs)


def _memes(*valeurs: str) -> tuple[tuple[str, str], ...]:
    return tuple((v, v) for v in valeurs)


# type_bien est un CODE Hektor (idtype). Libellés de l'écran (App.tsx, groupes de création + hors
# formulaire). ⚠ Valables pour offre_type 0 (vente) ; en immobilier professionnel (10) les mêmes
# codes ont un autre sens (App.tsx:10195). Le registre des mandats porte aussi quelques libellés en clair.
_TYPES_BIEN = (
    ("1", "Maison"), ("39", "Maison de village"), ("38", "Maison de ville"), ("25", "Villa"), ("22", "Propriété"),
    ("30", "Ferme"), ("10", "Mas"), ("11", "Bastide"), ("28", "Château"), ("27", "Rez de villa"), ("49", "Viager maison"),
    ("2", "Appartement"), ("4", "Studio"), ("18", "Duplex"), ("41", "Triplex"), ("31", "Loft"), ("26", "Rez de jardin"),
    ("50", "Viager appartement"),
    ("5", "Terrain"), ("43", "Terrain à bâtir"), ("44", "Terrain agricole"), ("45", "Terrain de loisir"),
    ("17", "Chalet"), ("15", "Garage"), ("16", "Parking"), ("21", "Immeuble"), ("23", "Commerce"), ("29", "Cave"),
    ("24", "Cabanon"), ("7", "Viager"), ("20", "Autre"),
)
_TYPES_BIEN_EN_CLAIR = _memes(
    "Maison", "Maison / Villa / Mas", "Maison / Appartement / Studio", "Maison / Appartement", "Maison / Terrain",
    "Maison / Immeuble", "Appartement / Studio / Duplex", "Terrain / Terrain à batir / Terrain agricole",
    "Garage / Parking / Chalet")
_OFFRE_TYPE = (("0", "Vente"), ("10", "Immobilier professionnel"), ("6", "Neuf"))
_MANDAT_TYPE = (("SIMPLE", "simple"), ("EXCLUSIF", "exclusif"), ("ACCORD", "accord"),
                *_memes("Vente de fonds de commerce", "Mandat de recherche",
                        "Mandat de recherche exclusif en cas de demarchage",
                        "Mandat de recherche non exclusif en cas de demarchage", "Mandat de recherche d'un terrain"))
# ⚠ deux écritures d'une même agence selon la table (espaces en fin, casse) : le lecteur les prend toutes
_AGENCES = _memes(
    "Groupe GTI Saint-Etienne", "Groupe GTI Montbrison", "Groupe GTI COURPIERE", "Groupe Gti Le Puy en Velay",
    "Groupe GTI ANNONAY", "Groupe GTI Firminy", "Groupe GTI Tence", "Groupe GTI Craponne-sur-Arzon",
    "Groupe GTI Saint-Bonnet-le-Château", "Groupe GTI Ambert   ", "Groupe GTI Ambert", "Groupe GTI Issoire",
    "Groupe GTI Saint-Just-Saint-Rambert", "Groupe GTI Monistrol sur Loire", "Groupe GTI Dunières", "Groupe GTI BRIOUDE",
    "Groupe GTI Yssingeaux", "Groupe GTI Saint-Didier-en-Velay", "Agences supprimée", "Compte formation")
_OUI_NON = (("1", "oui"), ("0", "non"))


def _bien_communes(statuts: tuple[str, ...], types_en_clair: bool = False) -> tuple[Colonne, ...]:
    return (
        C("numero_dossier", "texte", "numéro de dossier de l'agence"),
        C("numero_mandat", "texte", "numéro du mandat"),
        C("titre_bien", "texte", "titre de l'annonce"),
        C("type_bien", "texte", "type du bien (CODE : filtre avec le libellé, ex. Maison)",
          _TYPES_BIEN + (_TYPES_BIEN_EN_CLAIR if types_en_clair else ())),
        C("ville", "texte", "commune du bien"),
        C("code_postal", "texte", "code postal"),
        C("prix", "nombre", "prix affiché en euros"),
        C("statut_annonce", "texte", "statut de l'annonce", _memes(*statuts)),
        C("offre_type", "texte", "famille d'offre (CODE)", _OFFRE_TYPE),
        C("commercial_nom", "texte", "négociateur du bien"),
        C("negociateur_email", "texte", "e-mail du négociateur"),
        C("agence_nom", "texte", "agence", _AGENCES),
        C("mandat_type", "texte", "type de mandat", _MANDAT_TYPE),
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
         *_bien_communes(("Actif", "Sous offre", "Sous compromis", "Estimation")),
         C("archive", "texte", "archivé", _OUI_NON),
         C("diffusable", "texte", "diffusable sur les portails", _OUI_NON),
         C("validation_diffusion_state", "texte", "validation de la diffusion",
           (("a_controler", "à contrôler"), ("valide", "validée"))),
         C("nb_portails_actifs", "nombre", "nombre de portails où l'annonce est diffusée"),
         C("portails_resume", "texte", "portails de diffusion"),
         C("has_diffusion_error", "booleen", "erreur de diffusion"),
         C("offre_state", "texte", "état de l'offre en cours",
           (("proposed", "proposée"), ("accepted", "acceptée"), ("refused", "refusée"))),
         C("compromis_state", "texte", "état du compromis en cours", (("active", "en cours"), ("cancelled", "annulé"))),
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
        (C("hektor_annonce_id", "nombre", "numéro de l'annonce"), *_bien_communes(("Vendu", "Clos")),
         C("date_maj", "date", "dernière mise à jour")),
        ("hektor_annonce_id", "titre_bien", "ville", "prix", "statut_annonce", "commercial_nom", "date_maj"),
        "hektor_annonce_id",
    ),
    Objet(
        "biens_archives", "app_archive_annonce_index_current",
        "Les biens ARCHIVÉS.",
        (C("hektor_annonce_id", "nombre", "numéro de l'annonce"),
         *_bien_communes(("Clos", "Vendu", "Actif", "Estimation", "Sous offre")),
         C("date_maj", "date", "dernière mise à jour")),
        ("hektor_annonce_id", "titre_bien", "ville", "prix", "statut_annonce", "commercial_nom", "date_maj"),
        "hektor_annonce_id",
    ),
    Objet(
        "mandats", "app_v_mandat_statut",
        "Le registre des mandats, avec le statut calculé EXACTEMENT comme l'écran (statut_mandat, etat_mandat).",
        (C("app_dossier_id", "nombre", "identifiant du bien"),
         C("hektor_annonce_id", "nombre", "numéro de l'annonce"),
         *_bien_communes(("Clos", "Vendu", "Actif", "Estimation", "Sous compromis", "Sous offre", "Recherche active",
                          "Sans recherche", "Contact inconnu", "Recherche archivée"), types_en_clair=True),
         C("mandat_date_cloture", "date", "date de clôture du mandat"),
         C("statut_mandat", "texte", "statut du mandat (calcul de l'écran)", _memes("Actif", "Vendu", "Clos", "Échu")),
         C("etat_mandat", "texte", "état (calcul de l'écran)", _memes("En cours", "Annulé")),
         C("register_source_kind", "texte", "origine ; 'recherche' = mandat de recherche (le pilotage les exclut)",
           _memes("actif", "historique", "recherche"))),
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
         C("agence_nom", "texte", "agence", _AGENCES),
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
         C("offre", "texte", "type de projet (CODE)",
           (("0", "Achat / Vente"), ("2", "Location"), ("8", "Saisonnier"), ("10", "Immobilier professionnel"),
            ("11", "code 11 (non documenté)"))),
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
         C("role_contact", "texte", "rôle du contact sur ce bien",
           _memes("mandant", "proprietaire", "acquereur_offre", "acquereur_compromis", "acquereur_vente",
                  "notaire_vendeur", "notaire_acquereur")),
         C("transaction_type", "texte", "étape", _memes("offre", "compromis", "vente")),
         C("transaction_state", "texte", "état",
           (("proposed", "offre proposée"), ("accepted", "offre acceptée"), ("refused", "offre refusée"),
            ("active", "compromis en cours"), ("cancelled", "annulé"), ("vente", "vente"))),
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
        (C("label", "texte", "intitulé"), C("sub", "texte", "détail"),
         C("type", "texte", "type de relance", _memes("relance", "contact")),
         C("due_date", "date", "échéance"),
         C("status", "texte", "état", (("a_faire", "à faire"), ("fait", "faite"), ("reporte", "reportée"))),
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
         C("kind", "texte", "étape", _memes("offre", "compromis", "vente")),
         C("state", "texte", "état ; VIDE pour une vente",
           (("proposed", "offre proposée"), ("accepted", "offre acceptée"), ("refused", "offre refusée"),
            ("active", "compromis en cours"), ("cancelled", "compromis annulé"))),
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
        (C("request_type", "texte", "type de demande",
           (("demande_diffusion", "diffusion"), ("demande_baisse_prix", "baisse de prix"),
            ("demande_annulation_mandat", "annulation de mandat"))),
         C("request_status", "texte", "état", (("pending", "en attente"), ("accepted", "acceptée"), ("refused", "refusée"))),
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
        (C("type", "texte", "type",
           _memes("nouveau_rapprochement", "mandat_echu", "job_echec", "contact_conflit_ecriture", "recherche_conflit_ecriture",
                  "signature_a_contresigner", "signature_signee", "demande_visite", "estimation_consultee")),
         C("title", "texte", "titre"), C("body", "texte", "texte"),
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
         C("user_type", "texte", "fonction", (("NEGO", "négociateur"), ("AGENCE", "compte d'agence"), ("SECRETAIRE", "secrétaire"))),
         C("site", "texte", "site")),
        ("display_name", "email", "portable", "site"),
        "display_name",
    ),
)

PAR_NOM = {o.nom: o for o in OBJETS}


def _valeurs_lisibles(colonne: Colonne) -> str:
    return " | ".join(v if v == l else f"{l} [{v}]" for v, l in colonne.valeurs)


def liste_pour_consignes() -> str:
    # Les colonnes ET leurs valeurs sont dans les consignes (13/11) : le modèle ne devine plus un nom
    # de colonne (19 réponses sur 30 commençaient par un appel refusé) ni une valeur.
    # ⚠ Texte IDENTIQUE d'un appel à l'autre : il est en tête des consignes, OpenAI le met en cache.
    blocs = []
    for o in OBJETS:
        lignes = [f"## {o.nom} : {o.description}"]
        for c in o.colonnes:
            ligne = f"  - {c.nom} ({c.type}) : {c.description}"
            if c.valeurs:
                ligne += f" ; valeurs : {_valeurs_lisibles(c)}"
            lignes.append(ligne)
        blocs.append("\n".join(lignes))
    return "\n".join(blocs)
