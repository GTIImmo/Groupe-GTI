from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from ..settings import Settings

# ---------------------------------------------------------------------------
# Assistant IA -- LES DÉFINITIONS COMMUNES au catalogue (étape 1) et au lecteur (étape 2).
# Module à part (12/11/2026) : le catalogue importe le lecteur et le lecteur a besoin de ces
# définitions ; les loger ici évite que les deux modules s'importent l'un l'autre (le témoin
# inverse l'a fait planter en important le lecteur en premier).
#
# ⛔ LE CONTEXTE RESTE CHEZ NOUS. Il porte l'identité, le rôle et le JETON de la personne ;
#   le SDK le passe aux fonctions, il ne l'envoie JAMAIS au modèle.
# ---------------------------------------------------------------------------

TOUS_LES_ROLES = frozenset({"admin", "manager", "commercial"})


@dataclass
class ContexteAssistant:
    settings: Settings
    user_id: str
    email: str | None
    role: str
    jeton: str
    # les fonctions appelées pendant le tour (nom, paramètres, erreur) : pour le fil et le journal
    appels: list[dict[str, Any]] = field(default_factory=list)
    # étape 3 (13/11/2026) : la conversation, le nom affiché (libellé d'une demande, comme l'écran) et les
    # cartes proposées pendant le tour (envoyées à l'écran dans le flux)
    conversation_id: str | None = None
    nom: str | None = None
    cartes: list[dict[str, Any]] = field(default_factory=list)


class LectureRefusee(Exception):
    pass


class Refus(Exception):
    """Une demande hors de la liste fermée (étape 2) : le message part TEL QUEL au modèle, pour qu'il se corrige."""


@dataclass(frozen=True)
class Fonction:
    nom: str
    description: str
    roles: frozenset[str]
    parametres: dict[str, Any]
    executer: Callable[[ContexteAssistant, dict[str, Any]], Any]
