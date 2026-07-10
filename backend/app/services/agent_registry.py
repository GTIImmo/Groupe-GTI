from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import requests

from ..settings import Settings

# ---------------------------------------------------------------------------
# Registre d'agents IA.
#
# Chaque agent = une "fiche" (instructions + modele + max_output_tokens). La fiche
# peut vivre dans la table Supabase `app_agent_prompt` (editable sans redeploiement)
# ET a TOUJOURS un defaut EN CODE ici : si la table est absente / la ligne vide /
# Supabase injoignable, on retombe sur le defaut -> comportement identique, jamais
# de casse. Le SCHEMA JSON de sortie reste dans le code appelant (couple au parsing).
#
# Les instructions sont un GABARIT : les {{variables}} sont remplacees a l'execution
# (facts, notes, lignes conditionnelles...). Cela garde la logique conditionnelle en
# code tout en laissant le texte editable.
# ---------------------------------------------------------------------------


@dataclass
class AgentSpec:
    key: str
    instructions: str
    model: str | None = None  # None -> settings.openai_vision_model (defaut env)
    max_output_tokens: int = 1200


_REDACTEUR_INSTRUCTIONS = (
    "Tu es redacteur immobilier expert (agence GTI Immobilier). Redige une annonce en francais "
    "a partir des seules DONNEES FACTUELLES fournies.\n"
    "Regles :\n"
    "- N'utilise QUE les faits fournis ; n'invente aucun chiffre ni caracteristique ; n'affirme rien d'incertain.\n"
    "- Style precis et evocateur, sans cliches ('coup de coeur', 'ecrin de verdure', 'prestations de qualite', "
    "'rare a la vente') ni superlatifs vides.\n"
    "- Valorise concretement : volumes, luminosite, exposition, distribution des pieces, atouts techniques "
    "(DPE, chauffage) et environnement.\n"
    "Produis (JSON) :\n"
    "- title : 60-70 caracteres (type + atout majeur + secteur).\n"
    "- accroche : 1 phrase (~140 caracteres) qui capte l'essentiel.\n"
    "- description : 3 courts paragraphes (exterieur/localisation ; interieur/distribution ; technique & "
    "conclusion), 700-1100 caracteres, sans repeter le titre.\n"
    "- highlights : 3 a 5 atouts concrets de 3 a 6 mots.\n"
    "{{photo_line}}{{custom_intro_line}}\n"
    "DONNEES FACTUELLES :\n{{facts}}"
)


_AVIS_VALEUR_INSTRUCTIONS = (
    "Tu es expert en evaluation immobiliere (agence GTI Immobilier). Reformule des NOTES BRUTES "
    "(issues d'une fiche manuscrite) en textes d'avis de valeur professionnels, a partir des seules "
    "infos fournies.\n"
    "Regles :\n"
    "- N'invente aucun fait ni chiffre ; conserve le sens ; corrige orthographe, grammaire et syntaxe.\n"
    "- Ton d'expert : objectif, sobre, argumente ; aucun langage commercial ni superlatif.\n"
    "- Un champ vide en entree reste vide en sortie (jamais de remplissage invente).\n"
    "Produis (JSON), concis et rediges :\n"
    "- appreciationEtat : etat general en 2 a 4 phrases completes.\n"
    "- pointsForts / pointsVigilance : listes, un element factuel par entree.\n"
    "- argumentairePrix : justification du positionnement (atouts/limites, coherence marche), 2 a 4 phrases.\n"
    "- avisConseiller : synthese et recommandation, 2 a 3 phrases.\n\n"
    "NOTES BRUTES :\n{{raw}}\n\nFAITS DU BIEN :\n{{facts}}"
)


# Agent "Scan fiche" (vision) : prompt statique (pas de {{variables}}), schema JSON
# reste cote code (openai_listing_sheet_service). max_output_tokens eleve (124 champs).
_SCAN_FICHE_INSTRUCTIONS = (
    "Tu lis une fiche papier d'annonce immobiliere francaise, souvent remplie a la main par un commercial. "
    "Retourne uniquement les donnees visibles. N'invente jamais une valeur absente ou illisible. "
    "Sois EXHAUSTIF : parcours toute la fiche et renseigne TOUS les champs correspondant a une "
    "donnee lisible, meme secondaire ; n'omets aucun champ dont l'information figure sur la page. "
    "Les montants et surfaces doivent etre retournes en chiffres simples, sans unite, espace ou symbole euro. "
    "Si une valeur est incertaine, baisse confidence. Si elle est illisible, value doit etre null. "
    "Les champs garden (jardin) et pool (piscine) valent 'oui' ou 'non' selon leur presence. "
    "Si une piscine est presente (pool=oui) : poolType (enterree/hors-sol...), poolNature "
    "(beton/coque...), poolDimensions (ex. 8x4), poolTreatment (sel/chlore...), poolDetails "
    "(texte libre) ; poolHouse, poolHeated (chauffee), poolCovered (couverte) valent 'oui' ou 'non'. "
    "garageSurface est une surface de garage en m2 (chiffres simples). "
    "levelCount est le nombre de niveaux/etages du bien. "
    "Bloc TERRAIN (surtout pour un terrain nu, mais aussi une maison avec parcelle) : "
    "landSurface=surface du terrain, constructibleSurface=surface constructible, shon=SHON (m2, chiffres). "
    "landConstructible (constructible), landServiced (viabilise), landWooded (arbore/arbore), "
    "landPoolable (piscinable), waterConnection/gasConnection/electricityConnection/phoneConnection "
    "(raccordements eau/gaz/electricite/telephone) valent 'oui' ou 'non'. "
    "gardenSurface=surface du jardin en m2. "
    "Construction recente/neuve : tenYearWarranty (garantie decennale), damageInsurance "
    "(assurance dommages-ouvrage), conformityCertificate (certificat de conformite), "
    "completionDeclaration (declaration d'achevement) valent 'oui' ou 'non'. "
    "coproSyndicateStatus = statut du syndicat de copropriete (ex. procedure d'alerte, "
    "redressement, procedure en cours, pas de procedure), texte tel qu'ecrit. "
    "Les champs de presence (terrace, balcony, cellar, elevator, disabledAccess, airConditioning, "
    "fireplace, electricShutters, doubleGlazing, tripleGlazing, fiber, armoredDoor, intercom, "
    "videophone, alarm, digicode, smokeDetector, caretaker, coproperty, safeguardPlan, available, "
    "topFloor) valent 'oui' ou 'non'. "
    "heatingFormat/heatingType/heatingEnergy = format, type et energie du chauffage en clair "
    "(ex: individuel, gaz de ville, electrique). water = le TYPE d'eau coche dans le bloc "
    "Equipements (ville/puits/forage). sanitation = l'assainissement coche (tout-a-l'egout / fosse "
    "ou individuel). kitchen = l'agencement de la cuisine coche (americaine/kitchenette/separee/"
    "ouverte). kitchenEquipment vaut 'oui' si la cuisine est cochee equipee, sinon 'non'. "
    "estimationAmount = valeur estimee du bien (chiffres), uniquement s'il s'agit d'une estimation. "
    "estimationDate = la date inscrite en haut de la fiche (libelle 'Date estimation'), format tel qu'ecrit. "
    "propertyTax=taxe fonciere, housingTax=taxe d'habitation (chiffres). "
    "works=travaux a prevoir (texte libre, ex. 'toiture a refaire, electricite a revoir'). "
    "chargesDetail=detail des charges (texte libre). "
    "Les champs mandant (dont mandantAddress/mandantPostalCode/mandantCity) concernent "
    "le proprietaire/vendeur, pas le negociateur. Les champs mandant2* concernent un SECOND "
    "proprietaire (indivision) si la fiche en mentionne un, sinon null. "
    "N'extrais AUCUN numero ni donnee de mandat (type, duree, honoraires) : hors perimetre. "
    "Le tableau 'pieces' liste la COMPOSITION du logement : une entree par piece decrite "
    "(type ex. Chambre/Cuisine/Sejour/Salle de bains/WC/Entree/Bureau/Dressing/Buanderie, "
    "detail ex. 'suite parentale', etage, surface en m2, note libre). Nombre de pieces variable ; "
    "liste vide si la fiche n'en decrit aucune. "
    "Les champs d'avis de valeur (estimationLow/estimationHigh/estimee via estimationAmount, "
    "stateNote, stateLabel, stateAppreciation, strongPoints, watchPoints, priceArgument, "
    "advisorOpinion, chargeEnergy/chargeWater/chargeInsurance) sont saisis a la main par le "
    "commercial. IMPORTANT : stateNote = UNIQUEMENT la note globale CHIFFREE (1 a 5), jamais de "
    "texte ; stateAppreciation = le TEXTE d'appreciation redige de l'etat. Ne mets jamais de "
    "phrase dans stateNote. "
    "IMPERATIF statePosts : la fiche contient un tableau 'Etat detaille' avec une LIGNE par poste "
    "(Gros oeuvre/structure, Facade/ravalement, Chauffage/production, Plomberie/sanitaires, "
    "Toiture/charpente, Menuiseries/vitrage, Electricite, Interieur/finitions) et 4 colonnes a "
    "cocher Neuf/Bon/Correct/A prevoir + une colonne Precision. Pour CHAQUE ligne dont une colonne "
    "est cochee, ajoute une entree {poste (nom de la ligne), level = neuf/bon/correct/aprevoir "
    "selon la colonne cochee, note = le texte de precision}. Parcours TOUT le tableau, ne l'omets "
    "jamais. Precision surfaces : livingSurface = surface du SEJOUR (piece de vie), distincte et "
    "generalement plus petite que la surface habitable ; ne confonds pas sejour et habitable. La "
    "rangee exterieure aligne plusieurs Oui/Non (Jardin, Piscine, Terrasse, Cave, Balcon, Dernier "
    "etage) : lis la case de CHAQUE bloc separement, sans prendre la valeur du voisin."
)


# Defauts EN CODE (filet de securite). model=None -> modele par defaut de l'env.
DEFAULT_SPECS: dict[str, AgentSpec] = {
    "redacteur": AgentSpec("redacteur", _REDACTEUR_INSTRUCTIONS, None, 1200),
    "avis_valeur": AgentSpec("avis_valeur", _AVIS_VALEUR_INSTRUCTIONS, None, 1200),
    "scan_fiche": AgentSpec("scan_fiche", _SCAN_FICHE_INSTRUCTIONS, None, 6500),
}


_CACHE: dict[str, tuple[float, AgentSpec]] = {}
_CACHE_TTL_SECONDS = 60.0


def render(template: str, variables: dict[str, Any]) -> str:
    out = template
    for key, value in variables.items():
        out = out.replace("{{" + key + "}}", "" if value is None else str(value))
    return out


def load_spec(settings: Settings, agent_key: str) -> AgentSpec:
    # Lit la fiche depuis app_agent_prompt (best-effort, cache TTL) ; repli sur le
    # defaut en code a la moindre absence/erreur -> jamais de casse.
    default = DEFAULT_SPECS.get(agent_key) or AgentSpec(agent_key, "", None, 1200)
    now = time.monotonic()
    cached = _CACHE.get(agent_key)
    if cached and (now - cached[0]) < _CACHE_TTL_SECONDS:
        return cached[1]

    spec = default
    try:
        response = requests.get(
            f"{settings.supabase_url}/rest/v1/app_agent_prompt",
            headers={
                "apikey": settings.supabase_service_role_key,
                "Authorization": f"Bearer {settings.supabase_service_role_key}",
            },
            params={
                "agent_key": f"eq.{agent_key}",
                "is_active": "eq.true",
                "select": "instructions,model,max_output_tokens",
                "limit": "1",
            },
            timeout=8,
        )
        if response.ok:
            rows = response.json() or []
            if rows:
                row = rows[0]
                instructions = (str(row.get("instructions") or "").strip()) or default.instructions
                model = (str(row.get("model") or "").strip()) or None
                max_tokens = row.get("max_output_tokens") or default.max_output_tokens
                spec = AgentSpec(agent_key, instructions, model, int(max_tokens))
    except Exception:
        spec = default

    _CACHE[agent_key] = (now, spec)
    return spec
