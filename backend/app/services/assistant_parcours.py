"""Le parcours guidé de l'assistant (étape 4, chapitre 6, P1 — 19/11/2026).

Le MOTEUR DE QUESTIONS, sans modèle : un clic ne coûte rien (décision du 18/11, §78-80). Les 19 questions de la création
vivent en DONNÉES (parcours_creation.json, dans la langue de la fenêtre « Nouvelle annonce ») ; ce module dit quelle
question vient ensuite, pour quel type de bien, et vérifie qu'une réponse ne touche que les cases de SA question.

⛔ Les coordonnées d'un NOUVEAU mandant ne passent JAMAIS ici : l'écran les dépose lui-même dans le schéma privé
   (app_assistant_mandant_deposer, P3). Une réponse qui en porte est refusée.
⛔ Ce module n'écrit rien et n'appelle personne : la lecture et l'écriture de la table app_assistant_parcours sont
   dans ParcoursStore (clé de service, comme les cartes), et les routes dans routers/assistant.py.

Note : notice/ETAPE4_ECRAN_ACCUEIL_ASSISTANT_AUDIT_2026-11-16.md §88 (les questions), §91 (la mémoire), §93 (P1).
Couverture vérifiée contre App.tsx : apps/hektor-v1/test_etape4_parcours_couverture.cjs.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import requests
from fastapi import HTTPException

from ..settings import Settings

DONNEES: dict[str, Any] = json.loads((Path(__file__).with_name("parcours_creation.json")).read_text(encoding="utf-8"))
QUESTIONS: list[dict[str, Any]] = DONNEES["questions"]
PAR_ID: dict[str, dict[str, Any]] = {q["id"]: q for q in QUESTIONS}
GENRES: tuple[str, ...] = tuple(DONNEES["genres"])
PROFIL_PAR_TYPE: dict[str, str] = DONNEES["profil_par_type"]
CLES_PIECE: frozenset[str] = frozenset(DONNEES["cles_piece"])

# Réservé au suivi des questions dans `reponses` (jamais une case de la fenêtre).
CLE_ETATS = "_questions"
# Ce qu'un geste fait de la question : répondue, « je complète plus tard », « je ne sais pas ».
ETAT_PAR_GESTE = {"repondre": "faite", "passer": "passee", "nsp": "nsp"}
# P4-a (19/11) : « connue » = l'essentiel de la question était dans la demande (lue par l'IA) : elle n'est pas
# reposée, elle s'affiche en pastille verte, modifiable. `_sources` dit d'où vient chaque case pré-remplie.
ETAT_CONNUE = "connue"
CLE_SOURCES = "_sources"
SOURCES = frozenset({"demande", "scan", "phrase"})  # P4-b : « scan » = la fiche lue ; P4-d : « phrase » = une phrase libre
CLE_DOUTES = "_doutes"          # P4-b : les cases lues à moins de 75 % -> « à vérifier », leur question est reposée
CLE_FICHE = "_fiche"            # P4-b : la fiche lue (pages, coût), les pages de l'avis gardées à part, le coffre
# P4-c (20/11) : ce que les SERVICES PUBLICS disent du bien (DPE ADEME, base des bâtiments, cadastre, registre des
# copropriétés), lu pour UNE adresse. ⛔ Ce sont des PROPOSITIONS : aucune case n'est posée ; l'écran demande « C'est bien
# ça ? » dans la question concernée et la personne valide elle-même (parcours_publics.py).
CLE_PUBLICS = "_publics"
# P4-d (20/11) : les PHRASES LIBRES tapées ou dictées pendant le parcours (sans téléphone ni e-mail), avec ce qu'elles
# ont rempli ; affichées « gardées » sous leur question.
CLE_PHRASES = "_phrases"
# Ce qui fait relire les services : l'adresse, le type (maison ou appartement ne demandent pas la même chose) et la
# surface (elle départage les DPE d'un même immeuble).
CASES_PUBLICS = ("adresse_haut", "cp", "ville", "type", "surfappart")
# ⛔ règle du 18/11 : les coordonnées d'un nouveau mandant vivent à part (assistant_prive), jamais dans les réponses.
COORDONNEES = frozenset({"civilite", "nom", "prenom", "email", "telephone", "mandant_email", "mandant_telephone"})
MANDANT_CHOIX = frozenset({"", "existant", "nouveau"})
MAX_VALEUR = 4000          # caractères d'une case (le texte de l'annonce est la plus longue)
MAX_PIECES = 60
MAX_PHOTOS = 40
MAX_REPONSES = 200_000     # taille du JSON des réponses


class RefusParcours(ValueError):
    """Une réponse que le moteur refuse : la phrase va telle quelle à la personne."""


def annee_a_paris() -> int:
    return datetime.now(ZoneInfo("Europe/Paris")).year


def profil(reponses: dict[str, Any]) -> str:
    # Avant que le type soit dit, la fenêtre part sur son type par défaut (vérifié par l'essai de couverture, ⑧).
    type_id = str(reponses.get("type") or DONNEES["type_par_defaut"]).strip()
    return PROFIL_PAR_TYPE.get(type_id, PROFIL_PAR_TYPE[DONNEES["type_par_defaut"]])


def posee(question: dict[str, Any], reponses: dict[str, Any], annee: int) -> bool:
    profils = question.get("profils")
    if profils and profil(reponses) not in profils:
        return False
    si = question.get("si")
    if not si:
        return True
    valeur = str(reponses.get(si["champ"]) or "").strip()
    if "vaut" in si:
        return valeur == si["vaut"]
    if "moins_de_ans" in si:
        # année inconnue : on demande (le bien peut être récent) ; connue : seulement s'il a moins de N ans
        return not valeur.isdigit() or int(valeur) > annee - int(si["moins_de_ans"])
    return True


def etats(reponses: dict[str, Any]) -> dict[str, str]:
    brut = reponses.get(CLE_ETATS)
    return dict(brut) if isinstance(brut, dict) else {}


def questions_posees(reponses: dict[str, Any], annee: int) -> list[dict[str, Any]]:
    return [q for q in QUESTIONS if posee(q, reponses, annee)]


def suivante(reponses: dict[str, Any], annee: int) -> dict[str, Any] | None:
    faits = etats(reponses)
    return next((q for q in questions_posees(reponses, annee) if q["id"] not in faits), None)


def _valeur_simple(cle: str, valeur: Any) -> str:
    if valeur is None:
        return ""
    if isinstance(valeur, bool) or not isinstance(valeur, (str, int, float)):
        raise RefusParcours(f"La case « {cle} » attend un texte ou un nombre.")
    texte = str(valeur).strip()
    if len(texte) > MAX_VALEUR:
        raise RefusParcours(f"La case « {cle} » est trop longue ({len(texte)} caractères, {MAX_VALEUR} au plus).")
    return texte


def _pieces(valeur: Any) -> list[dict[str, str]]:
    if not isinstance(valeur, list) or len(valeur) > MAX_PIECES:
        raise RefusParcours(f"La composition attend une liste de {MAX_PIECES} pièces au plus.")
    pieces = []
    for piece in valeur:
        if not isinstance(piece, dict):
            raise RefusParcours("Chaque pièce de la composition doit être décrite par ses cases.")
        inconnues = sorted(set(piece) - CLES_PIECE)
        if inconnues:
            raise RefusParcours(f"Case de pièce inconnue : {', '.join(inconnues)}.")
        propre = {k: _valeur_simple(k, v) for k, v in piece.items()}
        if any(propre.values()):
            pieces.append({k: v for k, v in propre.items() if v})
    return pieces


def _photos(valeur: Any) -> list[str]:
    if not isinstance(valeur, list) or len(valeur) > MAX_PHOTOS:
        raise RefusParcours(f"Les photos attendent une liste de {MAX_PHOTOS} fichiers au plus.")
    numeros = [_valeur_simple("photos", v) for v in valeur]
    if any(len(n) > 64 for n in numeros):
        raise RefusParcours("Numéro de fichier invalide.")
    return [n for n in numeros if n]


def enregistrer(reponses: dict[str, Any], question_id: str, valeurs: Any, geste: str) -> dict[str, Any]:
    """Rend les NOUVELLES réponses ; ne touche que les cases de la question. Lève RefusParcours sinon."""
    question = PAR_ID.get(question_id)
    if not question:
        raise RefusParcours("Question inconnue.")
    if geste not in ETAT_PAR_GESTE:
        raise RefusParcours("Geste inconnu.")
    nouvelles = {k: v for k, v in reponses.items()}
    if geste == "repondre":
        if not isinstance(valeurs, dict) or not valeurs:
            raise RefusParcours("Réponse vide : réponds, ou choisis « Je ne sais pas » ou « Je complète plus tard ».")
        for cle, valeur in valeurs.items():
            if cle.startswith("_") or cle in COORDONNEES:
                raise RefusParcours("Les coordonnées d'un nouveau mandant se saisissent dans leurs cases protégées.")
            if cle not in question["champs"]:
                raise RefusParcours(f"La case « {cle} » n'appartient pas à la question « {question['titre']} ».")
            if cle == "composition":
                propre: Any = _pieces(valeur)
            elif cle == "photos":
                propre = _photos(valeur)
            else:
                propre = _valeur_simple(cle, valeur)
                if cle == "mandant_choix" and propre not in MANDANT_CHOIX:
                    raise RefusParcours("Le mandant est « existant » ou « nouveau ».")
            if propre in ("", []):
                nouvelles.pop(cle, None)  # vider une case = la retirer (la fenêtre la laissera vide)
            else:
                nouvelles[cle] = propre
    suivi = etats(reponses)
    suivi[question_id] = ETAT_PAR_GESTE[geste]
    nouvelles[CLE_ETATS] = suivi
    if len(json.dumps(nouvelles, ensure_ascii=False)) > MAX_REPONSES:
        raise RefusParcours("Le parcours est trop long pour être gardé.")
    return nouvelles


def appliquer_depart(reponses: dict[str, Any], valeurs: dict[str, Any], source: str, annee: int,
                     doutes: dict[str, float] | None = None) -> dict[str, Any]:
    """P4-a : pré-remplit le parcours avec ce que la personne a DÉJÀ dit (traduit dans la langue de la fenêtre). Ne
    remplace jamais une réponse donnée ; ignore une case qui n'est d'aucune question (la fenêtre ne la montre pas) ou
    qui ne passe pas les contrôles d'une réponse ; marque « connue » chaque question posée dont l'essentiel est dit."""
    if source not in SOURCES:
        raise RefusParcours("Source inconnue.")
    toutes = {c for q in QUESTIONS for c in q["champs"]}
    nouvelles = dict(reponses)
    sources = dict(nouvelles.get(CLE_SOURCES) or {})
    for cle, valeur in (valeurs or {}).items():
        if cle.startswith("_") or cle in COORDONNEES or cle not in toutes or cle in nouvelles:
            continue
        try:
            propre: Any = _pieces(valeur) if cle == "composition" else _photos(valeur) if cle == "photos" \
                else _valeur_simple(cle, valeur)
            if cle == "mandant_choix" and propre not in MANDANT_CHOIX:
                continue
        except RefusParcours:
            continue
        if propre in ("", []):
            continue
        nouvelles[cle] = propre
        sources[cle] = source
        if doutes and cle in doutes:
            nouvelles.setdefault(CLE_DOUTES, {})[cle] = doutes[cle]
    if sources:
        nouvelles[CLE_SOURCES] = sources
    suivi = etats(nouvelles)
    a_verifier = set(nouvelles.get(CLE_DOUTES) or {})
    for q in questions_posees(nouvelles, annee):
        essentiels = q.get("essentiels") or []
        if essentiels and q["id"] not in suivi and all(nouvelles.get(c) not in (None, "", []) for c in essentiels) \
                and not a_verifier & set(q["champs"]):
            suivi[q["id"]] = ETAT_CONNUE
    if suivi:
        nouvelles[CLE_ETATS] = suivi
    if len(json.dumps(nouvelles, ensure_ascii=False)) > MAX_REPONSES:
        raise RefusParcours("Le parcours est trop long pour être gardé.")
    return nouvelles


def vue(ligne: dict[str, Any], annee: int | None = None) -> dict[str, Any]:
    """Ce que l'écran reçoit : la question à poser, le repère « 4 sur 17 », les réponses (sans le suivi interne)."""
    annee = annee or annee_a_paris()
    reponses = dict(ligne.get("reponses") or {})
    posees = questions_posees(reponses, annee)
    faits = etats(reponses)
    q = suivante(reponses, annee)
    return {
        "id": ligne.get("id"),
        "genre": ligne.get("genre"),
        "etat": ligne.get("etat"),
        "app_dossier_id": ligne.get("app_dossier_id"),
        "maj_le": ligne.get("maj_le"),
        "profil": profil(reponses),
        "question": ({k: q[k] for k in ("id", "titre", "phrase", "forme", "champs")} if q else None),
        "repere": {"rang": (posees.index(q) + 1) if q else len(posees), "total": len(posees),
                   "faites": sum(1 for p in posees if p["id"] in faits)},
        # P2 (19/11) : chaque question posée avec sa forme et ses cases -> « Modifier » une réponse déjà donnée
        "questions": [{"id": p["id"], "titre": p["titre"], "etat": faits.get(p["id"]), "phrase": p["phrase"],
                       "forme": p["forme"], "champs": p["champs"], "essentiels": p.get("essentiels") or []}
                      for p in posees],
        "reponses": {k: v for k, v in reponses.items() if not k.startswith("_")},
        # P4-a : d'où vient une case pré-remplie (« demande ») -- l'écran le dit sur la pastille
        "sources": dict(reponses.get(CLE_SOURCES) or {}),
        # P4-b : les cases à vérifier, la fiche lue (sans ses coordonnées : elles sont au coffre)
        "doutes": dict(reponses.get(CLE_DOUTES) or {}),
        "fiche": dict(reponses.get(CLE_FICHE) or {}) or None,
        # P4-c : les propositions des services publics encore utiles (question posée, rien encore dit sur ces cases)
        "publics": publics_vue(reponses, annee),
        # P4-d : les phrases libres gardées (le texte sans coordonnées, la question, ce qu'elles ont rempli)
        "phrases": [p for p in reponses.get(CLE_PHRASES) or [] if isinstance(p, dict)],
        "fin": q is None,
    }


def cle_publics(reponses: dict[str, Any]) -> str | None:
    """P4-c : la clé d'une lecture des services publics, ou None si l'adresse ne suffit pas (la rue ET le code postal
    ou la ville : une ville seule placerait le point au centre de la commune, le DPE et la parcelle seraient d'un autre)."""
    valeurs = {c: str(reponses.get(c) or "").strip() for c in CASES_PUBLICS}
    if not valeurs["adresse_haut"] or not (valeurs["cp"] or valeurs["ville"]):
        return None
    return "|".join(" ".join(valeurs[c].lower().split()) for c in CASES_PUBLICS)


def publics_vue(reponses: dict[str, Any], annee: int) -> dict[str, Any]:
    """Ce que l'écran reçoit des services publics : faut-il (re)lire, et les propositions encore utiles. Une proposition
    ne se montre que si sa question est posée pour ce bien et qu'AUCUNE de ses cases n'a de réponse : elle ne remplace
    jamais ce que la personne a dit (ni la fiche de visite)."""
    cle = cle_publics(reponses)
    gardee = reponses.get(CLE_PUBLICS) if isinstance(reponses.get(CLE_PUBLICS), dict) else {}
    posees = {q["id"] for q in questions_posees(reponses, annee)}
    utiles = []
    for p in gardee.get("propositions") or []:
        cases = p.get("cases") or {}
        if p.get("question") in posees and cases and all(reponses.get(c) in (None, "", []) for c in cases):
            utiles.append(p)
    return {"possible": cle is not None, "a_jour": cle is not None and gardee.get("cle") == cle,
            "le": gardee.get("le"), "propositions": utiles}


def seul_publics_a_bouge(avant: dict[str, Any], apres: dict[str, Any]) -> bool:
    """P4-c : entre la lecture et l'écriture d'une réponse, seule la lecture des services publics (lancée par l'écran en
    arrière-plan) a écrit. Alors la réponse se rejoue sur la ligne fraîche sans rien écraser ; un AUTRE changement (un
    second onglet) reste refusé, comme avant."""
    a = {k: v for k, v in (avant or {}).items() if k != CLE_PUBLICS}
    b = {k: v for k, v in (apres or {}).items() if k != CLE_PUBLICS}
    return a == b


class ParcoursStore:
    """La table app_assistant_parcours (P3). Écriture par la CLÉ DE SERVICE seule (la table refuse l'écran) ; la relecture
    pour l'écran passe par le JETON de la personne (la règle de lecture de la base dit qui voit quoi)."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _url(self) -> str:
        return f"{self.settings.supabase_url}/rest/v1/app_assistant_parcours"

    def _service(self) -> dict[str, str]:
        key = self.settings.supabase_service_role_key
        return {"apikey": key, "Authorization": f"Bearer {key}"}

    def creer(self, user_id: str, conversation_id: str | None, genre: str, etape: str | None,
              reponses: dict[str, Any] | None = None) -> dict[str, Any]:
        # P4-a : `reponses` = le départ déjà rempli de la demande (appliquer_depart), sinon vide
        r = requests.post(self._url(), headers={**self._service(), "Prefer": "return=representation"},
                          json=[{"user_id": user_id, "conversation_id": conversation_id, "genre": genre,
                                 "reponses": reponses or {}, "etape": etape}], timeout=10)
        if not r.ok or not (r.json() or []):
            raise HTTPException(status_code=503, detail="Parcours non créé")
        return r.json()[0]

    def lire_service(self, parcours_id: str) -> dict[str, Any] | None:
        r = requests.get(self._url(), headers=self._service(),
                         params={"id": f"eq.{parcours_id}", "select": "*", "limit": "1"}, timeout=10)
        if not r.ok:
            raise HTTPException(status_code=503, detail="Parcours illisible")
        rows = r.json() or []
        return rows[0] if rows else None

    def lire_avec_jeton(self, jeton: str, parcours_id: str) -> dict[str, Any] | None:
        r = requests.get(self._url(), headers={"apikey": self.settings.supabase_anon_key, "Authorization": f"Bearer {jeton}"},
                         params={"id": f"eq.{parcours_id}", "select": "*", "limit": "1"}, timeout=10)
        if not r.ok:
            raise HTTPException(status_code=503, detail="Parcours illisible")
        rows = r.json() or []
        return rows[0] if rows else None

    def lister_conversation_avec_jeton(self, jeton: str, conversation_id: str) -> list[dict[str, Any]]:
        # P2 (19/11) : les parcours d'une conversation rouverte, dans l'ordre où ils ont commencé (la règle de lecture dit
        # lesquels la personne voit)
        r = requests.get(self._url(), headers={"apikey": self.settings.supabase_anon_key, "Authorization": f"Bearer {jeton}"},
                         params={"conversation_id": f"eq.{conversation_id}", "select": "*", "order": "cree_le.asc",
                                 "limit": "20"}, timeout=10)
        if not r.ok:
            raise HTTPException(status_code=503, detail="Parcours illisibles")
        return r.json() or []

    def terminer(self, ligne: dict[str, Any], app_dossier_id: int | None) -> dict[str, Any] | None:
        # P2 (19/11) : la fenêtre a créé la fiche. ⛔ Même condition que l'écriture d'une réponse (à LUI, en cours, avant la
        #   création) : un parcours ne se termine qu'une fois. Ensuite la règle de lecture passe au négociateur du bien.
        r = requests.patch(self._url(), headers={**self._service(), "Prefer": "return=representation"},
                           params={"id": f"eq.{ligne['id']}", "user_id": f"eq.{ligne['user_id']}", "etat": "eq.en_cours",
                                   "app_dossier_id": "is.null"},
                           json={"etat": "termine", "app_dossier_id": app_dossier_id,
                                 "termine_le": datetime.now(timezone.utc).isoformat()}, timeout=10)
        if not r.ok:
            raise HTTPException(status_code=503, detail="Fin du parcours non gardée")
        rows = r.json() or []
        return rows[0] if rows else None

    def ecrire_reponses(self, ligne: dict[str, Any], reponses: dict[str, Any], etape: str | None) -> dict[str, Any] | None:
        # ⛔ CONDITIONNELLE : seulement si personne n'a écrit depuis la lecture (même maj_le), à LUI, encore en cours et
        #   avant la création. Deux onglets, deux clics : un seul passe, l'autre recharge.
        r = requests.patch(self._url(), headers={**self._service(), "Prefer": "return=representation"},
                           params={"id": f"eq.{ligne['id']}", "user_id": f"eq.{ligne['user_id']}", "etat": "eq.en_cours",
                                   "app_dossier_id": "is.null", "maj_le": f"eq.{ligne['maj_le']}"},
                           json={"reponses": reponses, "etape": etape}, timeout=10)
        if not r.ok:
            raise HTTPException(status_code=503, detail="Réponse non gardée")
        rows = r.json() or []
        return rows[0] if rows else None
