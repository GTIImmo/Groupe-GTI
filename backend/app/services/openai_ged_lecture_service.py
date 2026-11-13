from __future__ import annotations

import json
import re
from typing import Any

import requests
from fastapi import HTTPException

from ..settings import Settings
from . import agent_registry
from .ged_garde_rib import nom_dit_rib, texte_porte_un_rib
from .openai_ged_classement_service import OpenAIGedClassementService, cout_usd
from .openai_listing_sheet_service import _extract_output_text

# ---------------------------------------------------------------------------
# GED (12/11/2026, morceau 6) -- LES FICHES DE LECTURE : l'IA LIT des valeurs dans un document déjà déposé et classé.
# L'IA EXTRAIT ; notre code comparera (morceau 7). Rien ne s'écrit sur le bien. Chaque valeur : {v, page, etat} avec
# etat lu / incertain / non_vu (« non_vu » = pas dans ce qu'on lui a montré, JAMAIS « absent du document »).
# Schéma STRICT : le modèle ne peut rendre QUE les champs de la fiche (ni date de naissance, ni numéro de pièce, ni IBAN).
# Lot 1 : l'état des risques, le DPE, le dossier de diagnostics (catalogue : E_synthese_catalogue.md §5, fiches 1 à 3).
# Lot 2 (§12.14) : la taxe foncière, le titre de propriété, la fiche synthétique, les charges de copropriété. Les deux
# premiers lisent des NOMS (liste « personnes » : nom, prénoms, qualité -- jamais naissance, adresse ni état civil) :
# c'est ce qui permettra de les comparer aux mandants (morceau 7).
# Lot 3 (§12.15) : l'offre, le compromis, le PV d'AG. Lot 4 (§12.16) : le mandat déposé à la main, l'avenant, la fin de
# mandat, l'acte, l'annulation, la facture d'honoraires, les petits diagnostics, les surfaces, le règlement.
# ---------------------------------------------------------------------------

AGENT_KEY = "ged_lecture"
MAX_PAGES_HD = 6
MAX_IMAGE_HD_OCTETS = 1_600_000
MAX_TEXTE = 20000
MAX_TEXTE_LONG = 40000  # le titre : 9 pages en médiane, jusqu'à 40 (mesuré le 12/11)
MAX_TEXTE_COMPROMIS = 80000  # 124 000 car. en médiane ; prêt et honoraires lus avant 80 000 (31/32, 39/40 ; §12.15)
MAX_PERSONNES = 12

_ETAT = {"type": "string", "enum": ["lu", "incertain", "non_vu"]}


def _champ(sorte: str, enum: list[str] | None = None) -> dict[str, Any]:
    v: dict[str, Any] = {"type": ["number", "null"]} if sorte == "num" else {"type": ["string", "null"]}
    if enum:
        v = {"type": ["string", "null"], "enum": [*enum, None]}
    if sorte == "date":
        v["description"] = "AAAA-MM-JJ"
    if sorte == "nom":
        v["description"] = "tel qu'imprimé, sans titre de civilité"
    return {"type": "object", "additionalProperties": False, "required": ["v", "page", "etat"],
            "properties": {"v": v, "page": {"type": ["integer", "null"]}, "etat": _ETAT}}


CLASSES = ["A", "B", "C", "D", "E", "F", "G"]
DIAGNOSTICS = ["dpe", "erp", "amiante", "plomb", "termites", "electricite", "gaz", "surface", "assainissement",
               "merule", "audit", "autre"]

# Une fiche : version (dans le nom enregistré), consigne propre, champs simples, des listes ; « texte_max » si long.
FICHES: dict[str, dict[str, Any]] = {
    "diag.erp": {
        "version": 1,
        "consigne": "C'est un état des risques et pollutions (ERP). date_etablissement : la date à laquelle CET état a "
                    "été établi ou signé par le vendeur ou son mandataire — PAS la date de l'arrêté préfectoral cité "
                    "dedans. commune et code_insee : ceux du bien.",
        "champs": {"date_etablissement": ("date", None), "commune": ("txt", None), "code_insee": ("txt", None)},
    },
    "diag.dpe": {
        "version": 1,
        "consigne": "C'est un diagnostic de performance énergétique (DPE). modele : « 2021 » s'il porte un numéro ADEME "
                    "de 13 caractères et deux étiquettes énergie et climat, sinon « ancien ». conso_ep : la "
                    "consommation d'énergie PRIMAIRE en kWh/m²/an ; conso_ef : l'énergie FINALE si elle est imprimée ; "
                    "emissions : kg CO2/m²/an. date_validite : telle qu'imprimée. diagnostiqueur_societe : la société, "
                    "pas la personne.",
        "champs": {"modele": ("txt", ["2021", "ancien", "inconnu"]), "numero_ademe": ("txt", None),
                   "date_etablissement": ("date", None), "date_validite": ("date", None),
                   "classe_energie": ("txt", CLASSES), "classe_ges": ("txt", CLASSES), "conso_ep": ("num", None),
                   "emissions": ("num", None), "conso_ef": ("num", None), "surface_reference": ("num", None),
                   "methode": ("txt", None), "diagnostiqueur_societe": ("txt", None), "commune": ("txt", None)},
    },
    "diag.dossier": {
        "version": 1,
        "consigne": "C'est un dossier de diagnostic technique (plusieurs diagnostics réunis). Lis la synthèse ou le "
                    "sommaire : pour CHAQUE diagnostic présent, son nom (dans la liste donnée), la date de son "
                    "rapport, sa conclusion en quelques mots (par exemple « présence d'amiante », « anomalies », "
                    "« classe D ») et la page où il commence. Si la page du DPE est lisible, remplis aussi les champs "
                    "dpe_*. commune : celle du bien.",
        "champs": {"commune": ("txt", None), "dpe_classe_energie": ("txt", CLASSES), "dpe_classe_ges": ("txt", CLASSES),
                   "dpe_conso_ep": ("num", None), "dpe_emissions": ("num", None), "dpe_date": ("date", None)},
        "listes": [("diagnostics", {"diagnostic": ("txt", DIAGNOSTICS), "date_rapport": ("date", None),
                                    "conclusion": ("txt", None)})],
    },
}

# ── Lot 2 ─────────────────────────────────────────────────────────────────────
OUI_NON = ["oui", "non"]
QUALITES = ["proprietaire", "usufruitier", "nu_proprietaire", "indivisaire", "heritier", "donataire", "redevable", "vendeur",
            "acquereur", "mandant", "autre"]
DROITS = ["pleine_propriete", "usufruit", "nue_propriete", "indivision", "non_precise"]
_EXCEPTION_NOMS = ("personnes : EXCEPTION à la règle commune -- recopie ICI, et nulle part ailleurs, le nom et les prénoms "
                   "de chaque personne tels qu'imprimés (sans « M. », « Mme »), avec sa qualité. Rien d'autre sur elles : "
                   "ni date ou lieu de naissance, ni adresse, ni profession, ni situation de famille.")
_LOTS = ("lots", {"numero": ("txt", None), "nature": ("txt", None)})
_CHARGES_COPRO = {
    "version": 1,
    "consigne": "C'est un document de charges de copropriété : appel de fonds, budget prévisionnel ou arrêté / "
                "décompte de charges. sous_type : lequel. periode : celle de l'appel. provision_budget : la part "
                "« budget prévisionnel / charges courantes » de CE document (pas le fonds de travaux, pas les travaux). "
                "budget_annuel_lot : le budget annuel du lot s'il est imprimé. charges_courantes_lot : pour un arrêté, "
                "le total des charges réelles du lot sur l'exercice. cotisation_fonds_travaux, appel_travaux et "
                "objet_travaux : s'ils sont appelés. lots : les numéros de lots concernés et leur nature (appartement, "
                "cave, parking…). syndic_nom : seulement si le syndic est une société. JAMAIS le nom ni l'adresse du "
                "copropriétaire destinataire, ni le solde, ni les impayés, ni les relances.",
    "champs": {"sous_type": ("txt", ["appel_de_fonds", "budget", "arrete_de_charges", "autre"]),
               "date_document": ("date", None), "periode": ("txt", ["mois", "trimestre", "semestre", "annuel", "autre"]),
               "exercice_debut": ("date", None), "exercice_fin": ("date", None), "provision_budget": ("num", None),
               "budget_annuel_lot": ("num", None), "charges_courantes_lot": ("num", None),
               "cotisation_fonds_travaux": ("num", None), "appel_travaux": ("num", None), "objet_travaux": ("txt", None),
               "syndic_nom": ("txt", None)},
    "listes": [_LOTS],
}
FICHES.update({
    "justif.taxe": {
        "version": 1,
        "consigne": "C'est un avis de taxe foncière. annee_imposition : l'année de l'impôt. montant_total : le montant "
                    "total de l'impôt (« montant de votre impôt », total des cotisations) -- PAS la somme restant à "
                    "payer, qui va dans somme_a_payer. dont_teom : la taxe d'enlèvement des ordures ménagères. commune "
                    "et adresse_biens : celles DES BIENS imposés, jamais l'adresse du destinataire. plusieurs_biens : "
                    "oui si l'avis porte plusieurs locaux ou propriétés. " + _EXCEPTION_NOMS + " Ici : chaque "
                    "redevable, qualité redevable, usufruitier ou nu_proprietaire. JAMAIS de numéro fiscal, de "
                    "référence d'avis ni de numéro de rôle.",
        "champs": {"annee_imposition": ("num", None), "date_etablissement": ("date", None), "montant_total": ("num", None),
                   "dont_teom": ("num", None), "somme_a_payer": ("num", None), "commune": ("txt", None),
                   "adresse_biens": ("txt", None), "plusieurs_biens": ("txt", OUI_NON)},
        "listes": [("personnes", {"nom": ("nom", None), "prenoms": ("nom", None), "qualite": ("txt", QUALITES)})],
    },
    "justif.titre": {
        "version": 1,
        "texte_max": MAX_TEXTE_LONG,
        "consigne": "C'est un titre de propriété : acte de vente, donation, partage, attestation de propriété après "
                    "décès, notoriété… nature_acte et date_acte : celles de CET acte. etude_notariale : l'étude ou le "
                    "notaire (un professionnel). " + _EXCEPTION_NOMS + " Ici : les personnes qui DEVIENNENT "
                    "propriétaires par cet acte (acquéreurs, donataires, attributaires, héritiers), JAMAIS les vendeurs "
                    "ni les propriétaires antérieurs cités dans l'origine de propriété ; droits : pleine propriété, "
                    "usufruit, nue-propriété, indivision ; quote_part si imprimée (« moitié », « 1/2 »). "
                    "deces_mentionne : oui si l'acte constate un décès (succession). commune, adresse_ou_lieudit, "
                    "contenance_totale_m2 : du bien vendu. lots : les numéros de lots de copropriété et leurs "
                    "tantièmes. extrait_partiel : oui si seules quelques pages de l'acte sont présentes.",
        "champs": {"nature_acte": ("txt", ["vente", "donation", "donation_partage", "attestation_succession", "notoriete",
                                           "partage", "adjudication", "echange", "autre"]),
                   "date_acte": ("date", None), "etude_notariale": ("txt", None), "deces_mentionne": ("txt", OUI_NON),
                   "commune": ("txt", None), "adresse_ou_lieudit": ("txt", None), "contenance_totale_m2": ("num", None),
                   "extrait_partiel": ("txt", OUI_NON)},
        "listes": [("personnes", {"nom": ("nom", None), "prenoms": ("nom", None), "qualite": ("txt", QUALITES),
                                  "droits": ("txt", DROITS), "quote_part": ("txt", None)}),
                   ("lots", {"numero": ("txt", None), "tantiemes": ("txt", None)})],
    },
    "copro.carnet": {
        "version": 1,
        "consigne": "C'est une fiche synthétique de copropriété ou un carnet d'entretien. sous_type : lequel ; pour un "
                    "carnet d'entretien, laisse tout le reste non_vu. Les montants sont ceux de l'IMMEUBLE. "
                    "immatriculation : le numéro du registre des copropriétés. nb_lots_total : tous les lots ; "
                    "nb_lots_principaux : habitation, bureaux, commerces. syndic_nom : seulement si le syndic est une "
                    "société ; un syndic bénévole (une personne) : syndic_nom non_vu et syndic_type = benevole. "
                    "procedure : « aucune » seulement si la fiche l'écrit ; mandataire ad hoc, administration "
                    "provisoire si elle le dit. plan_sauvegarde : oui ou non s'il est écrit.",
        "champs": {"sous_type": ("txt", ["fiche_synthetique", "carnet_entretien", "autre"]),
                   "date_etablissement": ("date", None), "immatriculation": ("txt", None), "nb_lots_total": ("num", None),
                   "nb_lots_principaux": ("num", None), "syndic_nom": ("txt", None),
                   "syndic_type": ("txt", ["professionnel", "benevole", "cooperatif"]),
                   "budget_previsionnel": ("num", None), "fonds_travaux_solde": ("num", None),
                   "procedure": ("txt", ["aucune", "mandataire_ad_hoc", "administration_provisoire", "autre"]),
                   "plan_sauvegarde": ("txt", OUI_NON), "commune": ("txt", None)},
    },
    "copro.appel_fonds": _CHARGES_COPRO,
    "copro.arrete_charges": _CHARGES_COPRO,
})

# ── Lot 3 (§12.15) : la vente ──────────────────────────────────────────────────
_SIGNATURES_FIN = "Les signatures sont souvent sur les DERNIÈRES pages, montrées en image après le texte : compte-les là. "
_PRET = "JAMAIS le montant d'un prêt, son taux, sa durée, la banque, l'apport ni le plan de financement."
_SIGNE = _SIGNATURES_FIN + _PRET
FICHES.update({
    "transaction.offre": {
        "version": 1,
        "consigne": "C'est une offre d'achat (proposition d'acquisition) et, s'il y en a une, la réponse du vendeur. "
                    "montant_offert : le prix proposé ; base_prix : « fai » s'il s'entend frais d'agence (honoraires) "
                    "inclus, « net_vendeur » s'il est net vendeur. date_offre ; validite_jusquau ou validite_jours. "
                    "condition_pret : oui si l'offre est faite sous condition d'obtenir un prêt. acceptation_vendeur : "
                    "acceptee, refusee, contre_proposition, ou non_signee si la case du vendeur est vide ; "
                    "date_acceptation. signatures_acquereurs_nb, signatures_vendeurs_nb : les signatures VISIBLES. "
                    "reference_bien : le numéro de mandat ou l'adresse du bien. " + _EXCEPTION_NOMS + " Ici : les "
                    "acquéreurs (qualité acquereur) ; ni leur adresse, ni leur téléphone, ni leur courriel. " + _SIGNE,
        "champs": {"montant_offert": ("num", None), "base_prix": ("txt", ["fai", "net_vendeur"]),
                   "date_offre": ("date", None), "validite_jusquau": ("date", None), "validite_jours": ("num", None),
                   "condition_pret": ("txt", OUI_NON),
                   "acceptation_vendeur": ("txt", ["acceptee", "refusee", "contre_proposition", "non_signee"]),
                   "date_acceptation": ("date", None), "signatures_acquereurs_nb": ("num", None),
                   "signatures_vendeurs_nb": ("num", None), "reference_bien": ("txt", None)},
        "listes": [("personnes", {"nom": ("nom", None), "prenoms": ("nom", None), "qualite": ("txt", QUALITES)})],
    },
    "transaction.avant_contrat": {
        "version": 1,
        "texte_max": MAX_TEXTE_COMPROMIS,
        "consigne": "C'est un compromis ou une promesse de vente. date_signature : la date à laquelle il est signé ; "
                    "forme : ssp_agence s'il est signé sous seing privé (à l'agence), notaire s'il est reçu par un "
                    "notaire. prix : le prix de vente ; prix_net_vendeur ; honoraires : la rémunération de l'agence ; "
                    "charge_honoraires : qui la paie (vendeur, acquereur, les_deux). mobilier : le prix du mobilier s'il "
                    "est cité. condition_pret (oui, non, renonciation) et date_limite_pret : la date limite d'obtention "
                    "du prêt. date_reiteration : la date limite de signature de l'acte authentique. sequestre (montant) "
                    "et sequestre_depositaire (notaire, agence). notaire_vendeur, notaire_acquereur : les études. "
                    "reference_bien : le numéro de mandat cité. signatures_vendeurs_nb, signatures_acquereurs_nb : les "
                    "signatures VISIBLES. " + _EXCEPTION_NOMS + " Ici : les VENDEURS (qualité vendeur) et les "
                    "ACQUÉREURS (qualité acquereur). " + _SIGNE,
        "champs": {"date_signature": ("date", None), "forme": ("txt", ["ssp_agence", "notaire"]),
                   "nature": ("txt", ["compromis", "promesse_unilaterale"]), "prix": ("num", None),
                   "prix_net_vendeur": ("num", None), "honoraires": ("num", None),
                   "charge_honoraires": ("txt", ["vendeur", "acquereur", "les_deux"]), "mobilier": ("num", None),
                   "condition_pret": ("txt", ["oui", "non", "renonciation"]), "date_limite_pret": ("date", None),
                   "date_reiteration": ("date", None), "sequestre": ("num", None),
                   "sequestre_depositaire": ("txt", ["notaire", "agence"]), "notaire_vendeur": ("txt", None),
                   "notaire_acquereur": ("txt", None), "reference_bien": ("txt", None),
                   "signatures_vendeurs_nb": ("num", None), "signatures_acquereurs_nb": ("num", None)},
        "listes": [("personnes", {"nom": ("nom", None), "prenoms": ("nom", None), "qualite": ("txt", QUALITES)})],
    },
    "copro.pv_ag": {
        "version": 1,
        "texte_max": MAX_TEXTE_LONG,
        "consigne": "C'est un procès-verbal ou une convocation d'assemblée générale de copropriété. type_piece : pv ou "
                    "convocation (une convocation n'a pas de résolution votée). date_ag ; nature_ag (ordinaire, "
                    "extraordinaire). syndic_nom : seulement si le syndic est une société ; syndic_type. "
                    "budget_vote : le budget prévisionnel voté ; cotisation_fonds_travaux_pct. procedure : seulement si le PV "
                    "mentionne un mandataire ad hoc, une administration provisoire ou un plan de sauvegarde du SYNDICAT "
                    "(un litige contre un copropriétaire n'en est pas une) ; sinon non_vu — un PV ne prouve pas l'absence. travaux : chaque travail VOTÉ (pas seulement proposé), "
                    "son objet en quelques mots, son montant pour tout l'immeuble, les dates du premier et du dernier "
                    "appel de fonds. JAMAIS : la feuille de présence, un nom de copropriétaire, un débiteur, un vote "
                    "nominatif, un contentieux contre une personne.",
        "champs": {"type_piece": ("txt", ["pv", "convocation", "autre"]), "date_ag": ("date", None),
                   "nature_ag": ("txt", ["ordinaire", "extraordinaire"]), "syndic_nom": ("txt", None),
                   "syndic_type": ("txt", ["professionnel", "benevole", "cooperatif"]), "budget_vote": ("num", None),
                   "cotisation_fonds_travaux_pct": ("num", None),
                   "procedure": ("txt", ["mandataire_ad_hoc", "administration_provisoire", "plan_sauvegarde"])},
        "listes": [("travaux", {"objet": ("txt", None), "montant_immeuble": ("num", None),
                                "premier_appel": ("date", None), "dernier_appel": ("date", None)})],
    },
})

# ── Lot 4 (§12.16) : le reste ─────────────────────────────────────────────────
# Le mandat n'est lu que DÉPOSÉ À LA MAIN (celui que l'app fait signer ne passe pas par l'outil de dépôt). Les noms : les
# mandants (mandat, avenant, fin), les vendeurs et acquéreurs (acte, annulation). Les diagnostics, la facture et le
# règlement : AUCUN nom. Lire un avenant ou une fin de mandat ne touche jamais au mandat.
_MANDANTS = _EXCEPTION_NOMS + " Ici : chaque MANDANT (qualité mandant) ; jamais le négociateur ni l'agence. "
_PERSONNES = [("personnes", {"nom": ("nom", None), "prenoms": ("nom", None), "qualite": ("txt", QUALITES)})]
_HONORAIRES = ["vendeur", "acquereur", "les_deux"]
_NATURE_MANDAT = ["exclusif", "simple", "semi_exclusif", "autre"]
_SANS_PROPRIETAIRE = "JAMAIS le nom ni l'adresse du propriétaire ou du donneur d'ordre."


def _rapport(sujet: str, resultats: list[str], consigne_resultat: str) -> dict[str, Any]:
    # un petit diagnostic : sa date, son résultat, sa conclusion ; la validité se calcule au morceau 7
    return {
        "version": 1,
        "consigne": f"C'est un rapport de diagnostic {sujet}. date_etablissement : la date du rapport (à défaut, celle de "
                    f"la visite) ; date_validite : seulement si elle est imprimée. resultat : {consigne_resultat} "
                    "conclusion : la conclusion du rapport en quelques mots. diagnostiqueur_societe : la société, pas la "
                    "personne. commune : celle du bien. " + _SANS_PROPRIETAIRE,
        "champs": {"date_etablissement": ("date", None), "date_validite": ("date", None), "resultat": ("txt", resultats),
                   "conclusion": ("txt", None), "diagnostiqueur_societe": ("txt", None), "commune": ("txt", None)},
    }


_ANOMALIES = ["sans_anomalie", "anomalies", "danger_grave"]
FICHES.update({
    "mandat.vente": {
        "version": 1,
        "texte_max": MAX_TEXTE_LONG,
        "consigne": "C'est un mandat de vente signé. numero_mandat : son numéro (registre des mandats). date_signature. "
                    "nature : exclusif, simple, semi_exclusif (ou co-exclusif). duree_mois : la durée initiale en mois ; "
                    "date_fin si elle est imprimée. prix : le prix de présentation ; prix_net_vendeur ; honoraires (le "
                    "montant) et honoraires_pct (le pourcentage) ; charge_honoraires : qui les paie. commune : celle DU "
                    "BIEN. signatures_mandants_nb : les signatures VISIBLES des mandants ; signature_agence : oui si "
                    "l'agence a signé. " + _MANDANTS + _SIGNATURES_FIN,
        "champs": {"numero_mandat": ("txt", None), "date_signature": ("date", None), "nature": ("txt", _NATURE_MANDAT),
                   "duree_mois": ("num", None), "date_fin": ("date", None), "prix": ("num", None),
                   "prix_net_vendeur": ("num", None), "honoraires": ("num", None), "honoraires_pct": ("num", None),
                   "charge_honoraires": ("txt", _HONORAIRES), "commune": ("txt", None),
                   "signatures_mandants_nb": ("num", None), "signature_agence": ("txt", OUI_NON)},
        "listes": _PERSONNES,
    },
    "mandat.avenant": {
        "version": 1,
        "consigne": "C'est un avenant à un mandat de vente. numero_mandat : celui du mandat modifié. date_avenant. objet : "
                    "ce que l'avenant change d'abord (baisse_prix, hausse_prix, honoraires, duree, exclusivite, autre). "
                    "ancien_prix s'il est rappelé ; nouveau_prix, nouveau_net_vendeur, nouveaux_honoraires, "
                    "nouveaux_honoraires_pct, charge_honoraires, nouvelle_date_fin, nouvelle_nature : seulement ce que "
                    "l'avenant fixe. signatures_mandants_nb : les signatures VISIBLES des mandants ; signature_agence. "
                    + _MANDANTS + _SIGNATURES_FIN,
        "champs": {"numero_mandat": ("txt", None), "date_avenant": ("date", None),
                   "objet": ("txt", ["baisse_prix", "hausse_prix", "honoraires", "duree", "exclusivite", "autre"]),
                   "ancien_prix": ("num", None), "nouveau_prix": ("num", None), "nouveau_net_vendeur": ("num", None),
                   "nouveaux_honoraires": ("num", None), "nouveaux_honoraires_pct": ("num", None),
                   "charge_honoraires": ("txt", _HONORAIRES), "nouvelle_date_fin": ("date", None),
                   "nouvelle_nature": ("txt", _NATURE_MANDAT), "signatures_mandants_nb": ("num", None),
                   "signature_agence": ("txt", OUI_NON)},
        "listes": _PERSONNES,
    },
    "mandat.fin": {
        "version": 1,
        "consigne": "C'est la fin d'un mandat : résiliation, dénonciation, ou courrier qui y met fin. numero_mandat. "
                    "date_courrier ; date_effet : la date à laquelle le mandat prend fin, si elle est écrite. "
                    "a_l_initiative_de : mandant ou agence. motif : vendu_ailleurs, retrait_vente (le bien n'est plus à "
                    "vendre), autre_agence, autre ; non_vu s'il n'est pas donné. Une raison personnelle (santé, "
                    "séparation, décès, argent) : autre, sans la recopier. signatures_mandants_nb. " + _MANDANTS
                    + _SIGNATURES_FIN,
        "champs": {"numero_mandat": ("txt", None), "date_courrier": ("date", None), "date_effet": ("date", None),
                   "a_l_initiative_de": ("txt", ["mandant", "agence"]),
                   "motif": ("txt", ["vendu_ailleurs", "retrait_vente", "autre_agence", "autre"]),
                   "signatures_mandants_nb": ("num", None)},
        "listes": _PERSONNES,
    },
    "transaction.acte": {
        "version": 1,
        "texte_max": MAX_TEXTE_LONG,
        "consigne": "C'est un acte authentique de vente ou une attestation de vente établie par le notaire (ce_type : vrai "
                    "pour une attestation de vente ou d'acquisition, même courte, même si elle cite le financement). nature : "
                    "acte_authentique, attestation, autre. date_vente : le jour où la vente a été signée chez le "
                    "notaire (PAS la date d'envoi de l'attestation, qui va dans date_document). prix : le prix de vente ; "
                    "mobilier : s'il est distingué. etude_notariale : l'étude ou le notaire qui a reçu l'acte. commune : "
                    "celle du bien vendu. lots : les numéros de lots de copropriété vendus. extrait_partiel : oui si "
                    "seules quelques pages de l'acte sont présentes. " + _EXCEPTION_NOMS + " Ici : les VENDEURS (qualité "
                    "vendeur) et les ACQUÉREURS (qualité acquereur) ; ni leur régime matrimonial. JAMAIS le prêt (montant, "
                    "banque, taux) ni le financement.",
        "champs": {"nature": ("txt", ["acte_authentique", "attestation", "autre"]), "date_vente": ("date", None),
                   "date_document": ("date", None), "prix": ("num", None), "mobilier": ("num", None),
                   "etude_notariale": ("txt", None), "commune": ("txt", None), "extrait_partiel": ("txt", OUI_NON)},
        "listes": [*_PERSONNES, ("lots", {"numero": ("txt", None)})],
    },
    "transaction.annulation": {
        "version": 1,
        "consigne": "C'est l'annulation d'une vente : rétractation de l'acquéreur, refus de prêt, accord des parties, "
                    "caducité, désistement. nature : retractation, refus_pret, accord_amiable, caducite, desistement, "
                    "autre. date_document ; date_compromis : celle du compromis annulé s'il est rappelé. "
                    "a_l_initiative_de : acquereur, vendeur, les_deux. sequestre_restitue : oui ou non s'il est écrit ; "
                    "montant_sequestre. " + _EXCEPTION_NOMS + " Ici : les vendeurs (vendeur) et les acquéreurs "
                    "(acquereur). Une raison personnelle n'est jamais recopiée. " + _PRET,
        "champs": {"nature": ("txt", ["retractation", "refus_pret", "accord_amiable", "caducite", "desistement", "autre"]),
                   "date_document": ("date", None), "date_compromis": ("date", None),
                   "a_l_initiative_de": ("txt", ["acquereur", "vendeur", "les_deux"]),
                   "sequestre_restitue": ("txt", OUI_NON), "montant_sequestre": ("num", None)},
        "listes": _PERSONNES,
    },
    "facture.honoraires": {
        "version": 1,
        "consigne": "C'est une facture ou une note d'honoraires de L'AGENCE immobilière. ce_type : faux si c'est la facture "
                    "d'un fournisseur (énergie, eau, travaux, diagnostiqueur, artisan…). numero_facture, date_facture, "
                    "montant_ht, montant_tva, montant_ttc. objet : vente, location, estimation, autre. reference_bien : "
                    "le numéro de mandat, à défaut la commune du bien. payeur : la QUALITÉ de celui qui paie (vendeur, "
                    "acquereur, autre), jamais son nom ni son adresse.",
        "champs": {"numero_facture": ("txt", None), "date_facture": ("date", None), "montant_ht": ("num", None),
                   "montant_tva": ("num", None), "montant_ttc": ("num", None),
                   "objet": ("txt", ["vente", "location", "estimation", "autre"]), "reference_bien": ("txt", None),
                   "payeur": ("txt", ["vendeur", "acquereur", "autre"])},
    },
    "diag.electricite": _rapport("de l'installation intérieure d'ÉLECTRICITÉ", _ANOMALIES,
                                 "sans_anomalie si le rapport n'en relève aucune, anomalies s'il en relève, danger_grave "
                                 "s'il signale un danger grave et immédiat."),
    "diag.gaz": _rapport("de l'installation intérieure de GAZ", _ANOMALIES,
                         "sans_anomalie si aucune ; anomalies pour des anomalies A1 ou A2 ; danger_grave pour un danger "
                         "grave et immédiat (DGI) ou une alimentation coupée."),
    "diag.amiante": _rapport("AMIANTE (repérage avant vente)", ["absence", "presence"],
                             "presence si au moins un matériau ou produit contenant de l'amiante est repéré, absence s'il "
                             "n'en est repéré aucun."),
    "diag.plomb": _rapport("PLOMB (constat de risque d'exposition, CREP)", ["absence", "sous_le_seuil", "au_dessus_du_seuil"],
                           "absence si aucun revêtement ne contient de plomb, sous_le_seuil si du plomb est trouvé sous "
                           "1 mg/cm², au_dessus_du_seuil s'il y en a au-dessus."),
    "diag.termites": _rapport("TERMITES (état parasitaire)", ["absence", "presence"],
                              "presence si des indices d'infestation de termites sont relevés, absence sinon."),
    "diag.assainissement": {
        "version": 1,
        "consigne": "C'est un document d'assainissement : rapport de contrôle du SPANC (non collectif) ou attestation de "
                    "raccordement au réseau (collectif). type : collectif ou non_collectif. date_controle : la date de "
                    "la visite ou du rapport. conformite : conforme ; non_conforme (sans travaux obligatoires) ; "
                    "travaux_obligatoires (non conforme AVEC travaux imposés sous un délai ou dans l'année de la vente) ; "
                    "absence_installation ; raccorde (attestation de raccordement). delai_travaux_mois s'il est écrit. "
                    "organisme : le SPANC ou la société, pas la personne. commune. " + _SANS_PROPRIETAIRE,
        "champs": {"type": ("txt", ["collectif", "non_collectif"]), "date_controle": ("date", None),
                   "conformite": ("txt", ["conforme", "non_conforme", "travaux_obligatoires", "absence_installation", "raccorde"]),
                   "delai_travaux_mois": ("num", None), "organisme": ("txt", None), "commune": ("txt", None)},
    },
    "diag.surface": {
        "version": 1,
        "consigne": "C'est un certificat de mesurage : surface Carrez (lot de copropriété) et / ou surface habitable. "
                    "date_mesurage. surface_carrez et surface_habitable en m², telles qu'imprimées ; surface_hors_carrez : "
                    "le total des surfaces non comptées (moins de 1,80 m, annexes) s'il est donné. lots : les numéros des "
                    "lots mesurés. diagnostiqueur_societe : la société. commune. " + _SANS_PROPRIETAIRE,
        "champs": {"date_mesurage": ("date", None), "surface_carrez": ("num", None), "surface_habitable": ("num", None),
                   "surface_hors_carrez": ("num", None), "diagnostiqueur_societe": ("txt", None), "commune": ("txt", None)},
        "listes": [("lots", {"numero": ("txt", None)})],
    },
    "copro.reglement": {
        "version": 1,
        "texte_max": MAX_TEXTE_LONG,
        "consigne": "C'est un règlement de copropriété, un état descriptif de division (EDD) ou un modificatif. sous_type. "
                    "date_acte : la date de l'acte ; etude_notariale. commune et adresse_immeuble : celles de l'IMMEUBLE. "
                    "nb_lots : le nombre total de lots s'il est écrit. destination : la clause de destination de "
                    "l'immeuble (habitation, mixte s'il admet aussi des activités professionnelles ou commerciales, "
                    "autre). modificatifs_mentionnes : oui si des modificatifs postérieurs sont cités. lots : les numéros "
                    "de lots et leurs tantièmes, seulement si l'état descriptif est dans ce qu'on te montre. JAMAIS le "
                    "nom d'un copropriétaire ni du requérant.",
        "champs": {"sous_type": ("txt", ["reglement", "edd", "reglement_et_edd", "modificatif"]),
                   "date_acte": ("date", None), "etude_notariale": ("txt", None), "commune": ("txt", None),
                   "adresse_immeuble": ("txt", None), "nb_lots": ("num", None),
                   "destination": ("txt", ["habitation", "mixte", "autre"]), "modificatifs_mentionnes": ("txt", OUI_NON)},
        "listes": [("lots", {"numero": ("txt", None), "tantiemes": ("txt", None)})],
    },
})
# Pages lues en haute définition (le navigateur les choisit ; même réglage dans gedClassementIa.ts) : le titre a ses
# parties et sa désignation dans les premières pages ; un compromis scanné : les 4 premières et les 2 dernières
# (signatures) ; un compromis en texte envoie AUSSI ses 2 dernières pages en image, une offre sa dernière.
# Lot 4 : le mandat comme le compromis ; l'avenant et la fin de mandat : leur dernière page (signatures) ;
# l'acte (attestation : 4 pages, 41 scans sur 50) et le règlement (37 pages) : 6 pages.
PAGES_HD = {"justif.titre": MAX_PAGES_HD, "copro.pv_ag": MAX_PAGES_HD, "transaction.avant_contrat": MAX_PAGES_HD,
            "mandat.vente": MAX_PAGES_HD, "transaction.acte": MAX_PAGES_HD, "copro.reglement": MAX_PAGES_HD}
FIN_EN_IMAGE = {"transaction.avant_contrat": 2, "transaction.offre": 1, "mandat.vente": 2, "mandat.avenant": 1,
                "mandat.fin": 1}

_CONSIGNE_COMMUNE = (
    "Tu lis un document d'une agence immobilière française pour en relever quelques valeurs. Rends UNIQUEMENT les champs "
    "demandés. Pour chaque champ : v = la valeur (dates en AAAA-MM-JJ, nombres sans unité avec un point décimal), "
    "page = la page où tu l'as lue, etat = « lu » si tu l'as lue nettement, « incertain » si tu hésites (écriture, "
    "scan pâle, jour et mois ambigus), « non_vu » si elle n'est pas dans ce qu'on te montre (v = null). N'invente rien. "
    "ce_type : faux si ce document n'est manifestement pas du type annoncé. Ne recopie jamais un nom de personne (sauf "
    "dans la liste « personnes » quand la fiche la demande), une date de naissance, une adresse personnelle, un numéro "
    "fiscal ou bancaire.\n"
)

agent_registry.DEFAULT_SPECS.setdefault(AGENT_KEY, agent_registry.AgentSpec(AGENT_KEY, _CONSIGNE_COMMUNE, "gpt-6-luna", 1800))


def schema(fiche: dict[str, Any]) -> dict[str, Any]:
    props: dict[str, Any] = {"ce_type": {"type": "boolean"}}
    for cle, (sorte, enum) in fiche["champs"].items():
        props[cle] = _champ(sorte, enum)
    for nom, champs in fiche.get("listes", []):
        props[nom] = {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": [*champs.keys(), "page"],
            "properties": {**{c: _champ(s, e) for c, (s, e) in champs.items()}, "page": {"type": ["integer", "null"]}},
        }}
    return {"type": "object", "additionalProperties": False, "required": list(props.keys()), "properties": props}


def _valeur(sorte: str, enum: list[str] | None, brut: Any) -> tuple[str | None, float | None, str | None]:
    # (texte, nombre, date) normalisés ; une valeur qui ne tient pas sa forme est jetée (None)
    if brut is None or brut == "":
        return None, None, None
    if sorte == "num":
        try:
            x = float(brut)
            return None, x, None
        except (TypeError, ValueError):
            return None, None, None
    texte = re.sub(r"\s+", " ", str(brut)).strip()[:200]
    # ⛔ un long numéro (fiscal, de rôle, de sécurité sociale…) n'est jamais gardé, quel que soit le champ
    if re.search(r"\d{9,}", re.sub(r"[\s.\-]", "", texte)):
        return None, None, None
    if sorte == "nom":
        # un nom : des lettres ; un chiffre ou une arobase trahit une adresse, une date, un numéro
        return (None, None, None) if re.search(r"[\d@]", texte) or len(texte) > 80 else (texte or None, None, None)
    if sorte == "date":
        return (None, None, texte) if re.fullmatch(r"(19[5-9]\d|20\d\d)-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])", texte) else (None, None, None)
    if enum and texte not in enum:
        return None, None, None
    return texte or None, None, None


def normaliser(brut: Any, fiche: dict[str, Any], nb_pages: int) -> tuple[bool, list[dict[str, Any]]]:
    if not isinstance(brut, dict):
        raise HTTPException(status_code=502, detail="Réponse de lecture inattendue")
    valeurs: list[dict[str, Any]] = []

    def ajouter(cle: str, rang: int, sorte: str, enum: list[str] | None, champ: Any) -> None:
        champ = champ if isinstance(champ, dict) else {}
        etat = champ.get("etat") if champ.get("etat") in {"lu", "incertain", "non_vu"} else "non_vu"
        texte, nombre, date = _valeur(sorte, enum, champ.get("v"))
        if texte is None and nombre is None and date is None:
            etat = "non_vu"
        page = champ.get("page") if isinstance(champ.get("page"), int) and 1 <= champ["page"] <= max(nb_pages, 1) else None
        valeurs.append({"cle": cle, "rang": rang, "valeur": texte, "valeur_num": nombre, "valeur_date": date, "page": page, "etat": etat})

    for cle, (sorte, enum) in fiche["champs"].items():
        ajouter(cle, 0, sorte, enum, brut.get(cle))
    for nom, champs in fiche.get("listes", []):
        for rang, item in enumerate((brut.get(nom) or [])[:MAX_PERSONNES if nom == "personnes" else 30]):
            if isinstance(item, dict):
                for c, (s, e) in champs.items():
                    ajouter(f"{nom}.{c}", rang, s, e, item.get(c))
    return bool(brut.get("ce_type", True)), valeurs


def verifier_image_hd(data_url: str) -> str:
    # même forme que la vignette, plafond plus haut (une page lisible)
    m = re.fullmatch(r"data:(image/(?:jpeg|png|webp));base64,([A-Za-z0-9+/=]+)", data_url.strip())
    if not m or len(m.group(2)) * 3 // 4 > MAX_IMAGE_HD_OCTETS:
        raise HTTPException(status_code=413, detail="Page trop lourde ou invalide")
    return data_url.strip()


class OpenAIGedLectureService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.portier = OpenAIGedClassementService(settings)  # interrupteur, plafond du jour

    def _headers(self) -> dict[str, str]:
        key = self.settings.supabase_service_role_key
        return {"apikey": key, "Authorization": f"Bearer {key}"}

    def classement_du_travail(self, job_id: str) -> dict[str, Any] | None:
        r = requests.get(f"{self.settings.supabase_url}/rest/v1/app_ged_classement", headers=self._headers(),
                         params={"app_console_job_id": f"eq.{job_id}", "select": "id,hektor_annonce_id,type_code,decide_par,document_name", "limit": "1"}, timeout=10)
        if not r.ok:
            raise HTTPException(status_code=503, detail="Classement illisible")
        rows = r.json() or []
        return rows[0] if rows else None

    def type_sensible(self, code: str) -> bool:
        return any(t.get("code") == code and t.get("sensible") for t in self.portier.types())

    def lire(self, classement: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.openai_api_key:
            raise HTTPException(status_code=503, detail="OPENAI_API_KEY non configure sur le backend")
        code = str(classement.get("type_code") or "")
        fiche = FICHES.get(code)
        if not fiche:
            raise HTTPException(status_code=422, detail="Pas de fiche de lecture pour ce type")
        if self.type_sensible(code):
            raise HTTPException(status_code=422, detail="Pièce des personnes : lue plus tard (morceau 9)")
        nom = str(payload.get("nomFichier") or classement.get("document_name") or "")
        texte = str(payload.get("texte") or "")[:fiche.get("texte_max", MAX_TEXTE)]
        pages = payload.get("pages") or []
        nb_pages = int(payload.get("nbPages") or len(pages) or 1)
        if nom_dit_rib(nom) or texte_porte_un_rib(texte):
            raise HTTPException(status_code=422, detail="Relevé d'identité bancaire : jamais envoyé à l'IA")
        if not pages and not texte.strip():
            raise HTTPException(status_code=400, detail="Rien à lire")
        if len(pages) > MAX_PAGES_HD:
            raise HTTPException(status_code=413, detail=f"{MAX_PAGES_HD} pages au plus")
        contenu: list[dict[str, Any]] = []
        for p in pages:
            contenu.append({"type": "input_text", "text": f"Page {int(p.get('numero') or 0)} sur {nb_pages}"})
            contenu.append({"type": "input_image", "image_url": verifier_image_hd(str(p.get("image") or "")), "detail": "high"})
        if self.portier.depense_du_jour() >= 2.0:
            raise HTTPException(status_code=429, detail="Plafond de dépense du jour atteint : lecture en pause")

        spec = agent_registry.load_spec(self.settings, AGENT_KEY)
        model = spec.model or "gpt-6-luna"
        entete = f"Type annoncé : {code}\nNombre de pages du document : {nb_pages}"
        if texte.strip():
            entete += f"\nTexte du document :\n{texte}"
        requete: dict[str, Any] = {
            "model": model, "store": False,
            "instructions": spec.instructions + fiche["consigne"],
            "input": [{"role": "user", "content": [{"type": "input_text", "text": entete}, *contenu]}],
            "text": {"format": {"type": "json_schema", "name": "ged_lecture", "strict": True, "schema": schema(fiche)}},
            "max_output_tokens": spec.max_output_tokens,
        }
        if not model.startswith("gpt-4"):
            requete["reasoning"] = {"effort": "none"}
        reponse = requests.post("https://api.openai.com/v1/responses",
                                headers={"Authorization": f"Bearer {self.settings.openai_api_key}", "Content-Type": "application/json"},
                                json=requete, timeout=90)
        if not reponse.ok:
            try:
                message = reponse.json().get("error", {}).get("message")
            except Exception:
                message = reponse.text.strip()[:300]
            raise HTTPException(status_code=502, detail=message or "Erreur OpenAI")
        corps = reponse.json()
        try:
            brut = json.loads(_extract_output_text(corps))
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=502, detail="Réponse de lecture non JSON") from exc
        ce_type, valeurs = normaliser(brut, fiche, nb_pages)
        usage = corps.get("usage") or {}
        etat = "pas_ce_type" if not ce_type else ("lu" if any(v["etat"] != "non_vu" for v in valeurs) else "incomplet")
        return {"fiche": f"{code}/{fiche['version']}", "model": model, "etat": etat, "valeurs": valeurs, "usage": usage,
                "costUsd": cout_usd(model, usage), "pagesLues": [int(p.get("numero") or 0) for p in pages], "parTexte": bool(texte.strip())}

    def enregistrer(self, classement: dict[str, Any], resultat: dict[str, Any], user_id: str | None) -> str:
        ligne = {"classement_id": classement["id"], "hektor_annonce_id": classement["hektor_annonce_id"],
                 "type_code": classement["type_code"], "fiche": resultat["fiche"], "modele": resultat["model"],
                 "etat": resultat["etat"], "pages_lues": resultat["pagesLues"] or None, "par_texte": resultat["parTexte"],
                 "input_tokens": resultat["usage"].get("input_tokens"), "output_tokens": resultat["usage"].get("output_tokens"),
                 "cout_usd": resultat["costUsd"], "lu_par": user_id}
        r = requests.post(f"{self.settings.supabase_url}/rest/v1/app_ged_lecture",
                          headers={**self._headers(), "Prefer": "return=representation"}, json=[ligne], timeout=15)
        if not r.ok:
            raise HTTPException(status_code=503, detail="Lecture non enregistrée")
        lecture_id = r.json()[0]["id"]
        lignes = [{**v, "lecture_id": lecture_id} for v in resultat["valeurs"]]
        if lignes:
            r = requests.post(f"{self.settings.supabase_url}/rest/v1/app_ged_valeur", headers=self._headers(), json=lignes, timeout=15)
            if not r.ok:
                raise HTTPException(status_code=503, detail="Valeurs lues non enregistrées")
        return lecture_id

