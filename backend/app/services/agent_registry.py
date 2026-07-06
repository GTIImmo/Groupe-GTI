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


# Defauts EN CODE (filet de securite). model=None -> modele par defaut de l'env.
DEFAULT_SPECS: dict[str, AgentSpec] = {
    "redacteur": AgentSpec("redacteur", _REDACTEUR_INSTRUCTIONS, None, 1200),
    "avis_valeur": AgentSpec("avis_valeur", _AVIS_VALEUR_INSTRUCTIONS, None, 1200),
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
