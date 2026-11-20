"""Le parcours guidé, P4-c (20/11/2026) : ce que les SERVICES PUBLICS disent du bien, PROPOSÉ à confirmer.

Quand l'adresse du bien est dite, l'écran demande en arrière-plan (route POST /assistant/parcours/{id}/publics) :
  - le DPE réel de l'ADEME (étiquettes, consommation, émissions, date) et, à l'adresse exacte, sa surface ;
  - l'année de construction (base nationale des bâtiments, BDNB) ;
  - la surface de la parcelle (cadastre) -- pour une maison ou un terrain seulement ;
  - la copropriété (registre national RNIC : lots, syndic, procédure) -- pour un appartement ou un immeuble.
Ce sont LES MÊMES SERVICES que l'éditeur d'avis de valeur (routers/geo.py), appelés tels quels, avec le jeton de la
personne. Ils sont publics, gratuits, sans clé ; on ne leur envoie que l'adresse du bien (jamais un nom, jamais un e-mail).

⛔ RIEN N'EST POSÉ EN SILENCE (décision du 18/11, maquette E03, E04, E05, N07) : on garde des PROPOSITIONS dans
   `_publics` ; la question concernée les montre (« C'est bien ça ? Oui / Autre ») et la personne valide elle-même. Une
   proposition dont une case a déjà une réponse ne se montre pas (assistant_parcours.publics_vue).
⛔ Un service qui ne répond pas ne fait rien tomber : il ne propose rien, c'est tout (et l'erreur est notée).
⛔ « Pas de DPE » (maquette E05) n'est pas proposé : son sens n'est pas tranché (non concerné ? vierge ? pas encore fait ?).

Note : notice/ETAPE4_ECRAN_ACCUEIL_ASSISTANT_AUDIT_2026-11-16.md §98.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, Callable

import requests

from . import assistant_parcours as moteur

GEOCODAGE = "https://data.geopf.fr/geocodage/search"
SCORE_MIN = 0.35        # le garde-fou de l'écran (lib/api.ts, geocodeAddress) : en dessous, l'adresse est introuvable
PROFILS_TERRAIN = frozenset({"house", "land"})        # un appartement : la parcelle est celle de tout l'immeuble
PROFILS_COPRO = frozenset({"apartment", "building"})  # la question copropriété n'est posée qu'à eux
SOURCE_ADEME = "ADEME, DPE"
SOURCE_BDNB = "base nationale des bâtiments"
SOURCE_CADASTRE = "cadastre"
SOURCE_RNIC = "registre national des copropriétés"


def _nombre(v: Any) -> float | None:
    try:
        n = float(v)
    except (TypeError, ValueError):
        return None
    return n if n == n else None  # NaN


def _entier(v: Any) -> str | None:
    n = _nombre(v)
    return str(int(round(n))) if n is not None and n >= 0 else None


def _surface(v: Any) -> str | None:
    n = _nombre(v)
    if n is None or n <= 0:
        return None
    n = round(n, 1)
    return str(int(n)) if n == int(n) else str(n)


def _mille(n: str) -> str:
    """« 1245 » -> « 1 245 » pour la phrase (la case garde le nombre nu, comme la fenêtre)."""
    entier, _, dec = n.partition(".")
    groupes = []
    while len(entier) > 3:
        groupes.insert(0, entier[-3:])
        entier = entier[:-3]
    groupes.insert(0, entier)
    return " ".join(groupes) + ("," + dec if dec else "")


def date_fr(iso: Any) -> str | None:
    """« 2023-03-14 » -> « 14/03/2023 » : la forme que tape la personne dans la fenêtre (le worker accepte les deux)."""
    t = str(iso or "").strip()[:10]
    if len(t) == 10 and t[4] == "-" and t[7] == "-" and (t[:4] + t[5:7] + t[8:]).isdigit() and t[:4] != "0000":
        return f"{t[8:]}/{t[5:7]}/{t[:4]}"
    return None


def geocoder(rue: str, cp: str, ville: str) -> dict[str, Any] | None:
    """L'adresse -> un point, par le même service que l'écran (Géoplateforme), avec le même garde-fou."""
    q = " ".join(x for x in (rue, cp, ville) if x).strip()
    if not q:
        return None
    params = {"q": q, "index": "address", "limit": "1"}
    if cp:
        params["postcode"] = cp
    r = requests.get(GEOCODAGE, params=params, timeout=10)
    if not r.ok:
        return None
    f = ((r.json() or {}).get("features") or [None])[0] or {}
    coords = (f.get("geometry") or {}).get("coordinates") or []
    props = f.get("properties") or {}
    score = _nombre(props.get("score"))
    if len(coords) < 2 or (score is not None and score < SCORE_MIN):
        return None
    lon, lat = _nombre(coords[0]), _nombre(coords[1])
    if lat is None or lon is None:
        return None
    # « housenumber » = le numéro est trouvé ; sinon le point est sur la rue (ou la commune) : approché
    return {"lat": lat, "lon": lon, "label": props.get("label"), "score": score,
            "precis": props.get("type") == "housenumber"}


def interroger(appels: dict[str, Callable[[], Any]]) -> tuple[dict[str, Any], list[str]]:
    """Les services en parallèle ; un service qui tombe ne propose rien et son nom est noté."""
    resultats: dict[str, Any] = {}
    erreurs: list[str] = []
    if not appels:
        return resultats, erreurs
    with ThreadPoolExecutor(max_workers=len(appels)) as pool:
        futurs = {nom: pool.submit(f) for nom, f in appels.items()}
        for nom, futur in futurs.items():
            try:
                resultats[nom] = futur.result()
            except Exception:  # noqa: BLE001 -- un service public en panne ne fait pas tomber le parcours
                resultats[nom] = None
                erreurs.append(nom)
    return resultats, erreurs


def propositions(brut: dict[str, Any], profil: str, annee: int, point_precis: bool) -> list[dict[str, Any]]:
    """Les réponses brutes des services -> les propositions de l'écran (fonction pure, testée sans réseau).
    Chacune : sa question, sa phrase, sa source, sa prudence éventuelle, la question à poser et les cases qu'un « Oui »
    remplira dans la carte (dans la langue de la fenêtre)."""
    sortie: list[dict[str, Any]] = []
    dpe = brut.get("dpe") or {}
    if dpe.get("found"):
        cases = {k: v for k, v in (("dpe_cons", _entier(dpe.get("conso_ep_m2"))),
                                   ("dpe_ges", _entier(dpe.get("ges_emission"))),
                                   ("dpe_date", date_fr(dpe.get("date")))) if v}
        if cases.get("dpe_cons") or cases.get("dpe_ges"):
            lettres = " · ".join(x for x in (f"DPE {dpe['etiquette_dpe']}" if dpe.get("etiquette_dpe") else "",
                                             f"GES {dpe['etiquette_ges']}" if dpe.get("etiquette_ges") else "") if x)
            morceaux = [lettres + (f" du {cases['dpe_date']}" if cases.get("dpe_date") else "")]
            if cases.get("dpe_cons"):
                morceaux.append(f"{cases['dpe_cons']} kWh/m²/an")
            if cases.get("dpe_ges"):
                morceaux.append(f"{cases['dpe_ges']} kg CO₂/m²/an")
            nb = dpe.get("nb_adresse") or 0
            if dpe.get("matched_by") != "adresse":
                prudence = "Le DPE le plus proche : il n'y en a pas à cette adresse exacte. Il peut être celui d'un voisin."
            elif nb > 1 and not dpe.get("par_surface"):
                prudence = f"{nb} DPE à cette adresse : c'est le plus récent, pas forcément celui de ce logement."
            elif nb > 1:
                prudence = f"{nb} DPE à cette adresse : c'est celui dont la surface est la plus proche."
            else:
                prudence = None
            sortie.append({"id": "dpe", "question": "energie", "source": SOURCE_ADEME, "prudence": prudence,
                           "phrase": ", ".join(x for x in morceaux if x) + ".", "demande": "C'est lui ?",
                           "oui": "Oui", "non": "Un autre", "cases": cases})
        # La surface du DPE : seulement quand le DPE est À L'ADRESSE et seul (sinon c'est peut-être un autre logement)
        surface = _surface(dpe.get("surface"))
        if surface and dpe.get("matched_by") == "adresse" and (dpe.get("nb_adresse") or 0) <= 1:
            sortie.append({"id": "surface", "question": "interieur", "source": SOURCE_ADEME, "prudence": None,
                           "phrase": f"{_mille(surface)} m² habitables d'après le DPE.", "demande": "C'est bien ça ?",
                           "oui": f"Oui, {_mille(surface)} m²", "non": "Autre", "cases": {"surfappart": surface}})
    bdnb = brut.get("bdnb") or {}
    an = _entier(bdnb.get("annee_construction"))
    if bdnb.get("found") and an and 1000 <= int(an) <= annee:
        sortie.append({"id": "annee", "question": "energie", "source": SOURCE_BDNB,
                       "prudence": None if point_precis else "L'adresse est approchée : le bâtiment peut être un voisin.",
                       "phrase": f"Construit en {an}.", "demande": "C'est bien ça ?", "oui": "Oui", "non": "Autre",
                       "cases": {"ANNEE_CONS": an}})
    cad = brut.get("cadastre") or {}
    parcelles = [p for p in cad.get("parcelles") or [] if isinstance(p, dict)]
    terrain = _surface(cad.get("contenance_totale"))
    if profil in PROFILS_TERRAIN and point_precis and parcelles and terrain:
        refs = [p.get("reference") for p in parcelles if p.get("reference")]
        nom = (f"parcelle {refs[0]}" if len(refs) == 1 else f"parcelles {', '.join(refs)}") if refs else "la parcelle"
        sortie.append({"id": "terrain", "question": "dehors", "source": SOURCE_CADASTRE,
                       "prudence": "La parcelle sous l'adresse : un terrain fait de plusieurs parcelles peut être plus grand.",
                       "phrase": f"{_mille(terrain)} m² au cadastre ({nom}).", "demande": "C'est bien ça ?",
                       "oui": f"Oui, {_mille(terrain)} m²", "non": "Autre", "cases": {"surfterrain": terrain}})
    copro = brut.get("copro") or {}
    if profil in PROFILS_COPRO and copro.get("found"):
        cases = {"copropriete": "OUI",
                 "copropriete_statut_syndicat": "PROCEDURE_EN_COURS" if copro.get("procedure") else "PAS_DE_PROCEDURE"}
        lots = _entier(copro.get("nb_lots"))
        if lots and lots != "0":
            cases["copropriete_nb_lot"] = lots
        morceaux = [f"Copropriété de {_mille(lots)} lots" if lots and lots != "0" else "Copropriété immatriculée"]
        if copro.get("syndic_nom"):
            morceaux.append(f"syndic {copro['syndic_nom']}")
        morceaux.append("une procédure en cours" if copro.get("procedure") else "pas de procédure")
        prudence = None if copro.get("match") in ("cadastre", "parcelle") else \
            "Trouvée sur une parcelle voisine de la même rue : vérifie que c'est bien la bonne."
        sortie.append({"id": "copro", "question": "copropriete", "source": SOURCE_RNIC, "prudence": prudence,
                       "phrase": ", ".join(morceaux) + ".", "demande": "C'est elle ?", "oui": "Oui", "non": "Une autre",
                       "cases": cases})
    return sortie


def lire(reponses: dict[str, Any], authorization: str, settings: Any, annee: int) -> dict[str, Any]:
    """Une lecture complète pour l'adresse dite : ce qui se garde dans `_publics` (clé, heure, propositions, erreurs)."""
    from ..routers import geo  # les routes de l'éditeur d'avis, appelées telles quelles (même code, même garde)

    cle = moteur.cle_publics(reponses)
    garde = {"cle": cle, "le": datetime.now(timezone.utc).isoformat(timespec="seconds"), "propositions": [], "erreurs": []}
    if cle is None:
        return garde
    rue, cp, ville = (str(reponses.get(c) or "").strip() for c in ("adresse_haut", "cp", "ville"))
    try:
        point = geocoder(rue, cp, ville)
    except Exception:  # noqa: BLE001
        garde["erreurs"].append("geocodage")
        return garde
    if not point:
        garde["introuvable"] = True  # l'adresse n'est pas trouvée : rien à proposer (on ne devine pas un point)
        return garde
    lat, lon = point["lat"], point["lon"]
    profil = moteur.profil(reponses)
    surface = _nombre(reponses.get("surfappart"))
    appels: dict[str, Callable[[], Any]] = {
        "dpe": lambda: geo.dpe(lat=lat, lon=lon, surface=surface, authorization=authorization, settings=settings),
        "bdnb": lambda: geo.bdnb(lat=lat, lon=lon, authorization=authorization, settings=settings),
    }
    if profil in PROFILS_TERRAIN | PROFILS_COPRO:
        appels["cadastre"] = lambda: geo.cadastre(lat=lat, lon=lon, candidates=0, authorization=authorization,
                                                  settings=settings)
    brut, erreurs = interroger(appels)
    if brut.get("dpe"):
        brut["dpe"] = {**brut["dpe"], "par_surface": bool(surface)}
    if profil in PROFILS_COPRO and point["precis"]:
        # la copropriété après le cadastre : la parcelle sous l'adresse est son meilleur repère (comme l'éditeur d'avis)
        idus = ",".join(p.get("idu") for p in (brut.get("cadastre") or {}).get("parcelles") or [] if p.get("idu"))
        plus, err = interroger({"copro": lambda: geo.copro_rnie(lat=lat, lon=lon, parcelles=idus,
                                                                 authorization=authorization, settings=settings)})
        brut.update(plus)
        erreurs += err
    garde["propositions"] = propositions(brut, profil, annee, point["precis"])
    garde["erreurs"] = erreurs
    garde["precis"] = point["precis"]
    return garde
