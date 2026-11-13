from __future__ import annotations

import asyncio
import json
from typing import Any

import requests

# Les définitions communes vivent dans assistant_contexte (12/11/2026) ; elles restent importables d'ici.
from .assistant_contexte import TOUS_LES_ROLES, ContexteAssistant, Fonction, LectureRefusee, Refus  # noqa: F401
from .assistant_gestes import FONCTIONS_GESTES
from .assistant_lecteur import FONCTIONS_LECTURE

# ---------------------------------------------------------------------------
# Assistant IA (12/11/2026, étape 1) -- LE CATALOGUE DES FONCTIONS ET LEURS DROITS.
#
# ⛔ LE CONTEXTE RESTE CHEZ NOUS. Il porte l'identité, le rôle et le JETON de la personne ;
#   le SDK le passe aux fonctions, il ne l'envoie JAMAIS au modèle (seuls le nom, la
#   description et les paramètres d'une fonction partent chez OpenAI).
# ⛔ CHAQUE LECTURE PART AVEC LE JETON DE LA PERSONNE et la clé publique : la RLS fait le tri,
#   exactement comme à l'écran (décision du 29/10, « droits comme l'écran »). Jamais la clé
#   de service ici : l'agent contourne ainsi les 38 fonctions sans contrôle (Q2 du 29/10).
# ⛔ DOUBLE VERROU SUR LE RÔLE : une fonction hors du rôle n'est pas proposée au modèle, et
#   si elle était appelée quand même, elle refuse.
# ⛔ La gestion des utilisateurs n'entrera JAMAIS dans ce catalogue (Q5 du 29/10).
#
# Étape 1 : la fonction témoin « qui suis-je ». Étape 2 (12/11/2026) : les lectures de
# assistant_lecteur, sur la liste fermée d'assistant_objets.
# ---------------------------------------------------------------------------


def lire_avec_jeton(ctx: ContexteAssistant, table: str, params: dict[str, str]) -> list[dict[str, Any]]:
    response = requests.get(
        f"{ctx.settings.supabase_url}/rest/v1/{table}",
        headers={"apikey": ctx.settings.supabase_anon_key, "Authorization": f"Bearer {ctx.jeton}"},
        params=params,
        timeout=15,
    )
    if not response.ok:
        raise LectureRefusee(f"lecture de {table} impossible ({response.status_code})")
    return response.json() or []


def qui_suis_je(ctx: ContexteAssistant, _params: dict[str, Any]) -> dict[str, Any]:
    # filtre sur SON id : un admin lit tous les profils, la RLS seule ne suffit pas à dire « moi »
    rows = lire_avec_jeton(ctx, "app_user_profile", {
        "id": f"eq.{ctx.user_id}",
        "select": "display_name,first_name,last_name,role,is_active",
        "limit": "1",
    })
    if not rows:
        return {"trouve": False}
    row = rows[0]
    return {
        "trouve": True,
        "nom_affiche": row.get("display_name"),
        "prenom": row.get("first_name"),
        "nom": row.get("last_name"),
        "role": row.get("role"),
        "actif": row.get("is_active") is True,
    }


_SANS_PARAMETRE = {"type": "object", "properties": {}, "required": [], "additionalProperties": False}

CATALOGUE: tuple[Fonction, ...] = (
    Fonction(
        "qui_suis_je",
        "Donne le nom et le rôle de la personne qui pose la question, lus dans l'application avec ses droits.",
        TOUS_LES_ROLES,
        _SANS_PARAMETRE,
        qui_suis_je,
    ),
)

# Étape 2 (12/11/2026) : les lectures (décrire, chercher, compter + 3 fonctions métier).
CATALOGUE = CATALOGUE + FONCTIONS_LECTURE
# Étape 3 (13/11/2026) : les gestes, qui ne font que PROPOSER une carte (assistant_gestes).
CATALOGUE = CATALOGUE + FONCTIONS_GESTES


def fonctions_du_role(role: str) -> list[Fonction]:
    return [f for f in CATALOGUE if role in f.roles]


async def appeler(ctx: ContexteAssistant, fonction: Fonction, arguments: str) -> str:
    try:
        params = json.loads(arguments or "{}")
    except json.JSONDecodeError:
        params = {}
    trace: dict[str, Any] = {"nom": fonction.nom, "parametres": params}
    ctx.appels.append(trace)
    if ctx.role not in fonction.roles:
        trace["erreur"] = "role"
        return "Refusé : cette fonction n'est pas ouverte à ton rôle."
    try:
        # les lectures sont bloquantes (requests) : hors de la boucle, pour ne pas figer les autres flux
        resultat = await asyncio.to_thread(fonction.executer, ctx, params)
    except Refus as exc:
        trace["erreur"] = "refus"
        return f"Refusé : {exc}"
    except Exception as exc:  # noqa: BLE001 -- le modèle reçoit une phrase, pas une trace
        trace["erreur"] = type(exc).__name__
        return "Erreur : la lecture n'a pas abouti. Dis-le simplement, n'invente rien."
    return json.dumps(resultat, ensure_ascii=False, default=str)


def outils_sdk(role: str) -> list[Any]:
    # ⚠ import du SDK ICI SEULEMENT, jamais au chargement du module (pièce 1 de l'étape 1)
    from agents import FunctionTool

    def invoquer(fonction: Fonction):
        async def _invoquer(tool_ctx: Any, arguments: str) -> str:
            return await appeler(tool_ctx.context, fonction, arguments)
        return _invoquer

    return [
        FunctionTool(
            name=f.nom,
            description=f.description,
            params_json_schema=f.parametres,
            on_invoke_tool=invoquer(f),
            strict_json_schema=True,
        )
        for f in fonctions_du_role(role)
    ]
