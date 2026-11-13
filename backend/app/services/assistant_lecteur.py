from __future__ import annotations

import html
import json
import re
import unicodedata
from typing import Any

import requests

from .assistant_contexte import TOUS_LES_ROLES, ContexteAssistant, Fonction, LectureRefusee, Refus
from .assistant_objets import OBJETS, PAR_NOM, Colonne, Objet, _valeurs_lisibles

# ---------------------------------------------------------------------------
# Assistant IA (12/11/2026, étape 2) -- LE LECTEUR : décrire, chercher, compter.
# Note : notice/ETAPE2_AGENT_QUI_REPOND_AUDIT_2026-11-12.md §4.
#
# L'IA ne compose JAMAIS d'adresse ni de requête : elle donne un objet, des colonnes et des
# filtres ; ce module VÉRIFIE chaque nom contre la liste fermée (assistant_objets), traduit en
# paramètres de lecture et lit AVEC LE JETON de la personne (la base applique le périmètre).
# Un nom inconnu, un opérateur interdit pour le type, une valeur illisible = refus en clair,
# avant toute lecture.
# Les sommes et regroupements se calculent ICI sur les lignes lues, avec un plafond : la réponse
# DIT combien de lignes ont été lues et si le plafond a coupé (jamais un total faux en silence).
# ---------------------------------------------------------------------------

MAX_LIGNES_RENDUES = 50
LIMITE_PAR_DEFAUT = 20
PLAFOND_LIGNES_CALCUL = 5000
PAGE = 1000
MAX_CARACTERES_VALEUR = 300
MAX_FICHES = 10

OPERATEURS = ("egal", "different", "superieur", "superieur_ou_egal", "inferieur", "inferieur_ou_egal",
              "contient", "commence_par", "parmi", "est_vide", "n_est_pas_vide", "json_contient")
_COMPARAISONS = {"superieur": "gt", "superieur_ou_egal": "gte", "inferieur": "lt", "inferieur_ou_egal": "lte"}
_PERMIS = {
    "nombre": {"egal", "different", "parmi", "est_vide", "n_est_pas_vide", *_COMPARAISONS},
    "date": {"egal", "different", "commence_par", "est_vide", "n_est_pas_vide", *_COMPARAISONS},
    "texte": {"egal", "different", "contient", "commence_par", "parmi", "est_vide", "n_est_pas_vide"},
    "booleen": {"egal", "est_vide", "n_est_pas_vide"},
    "json": {"json_contient", "est_vide", "n_est_pas_vide"},
}


# ── lecture avec le jeton ─────────────────────────────────────────────────────
def _lire(ctx: ContexteAssistant, source: str, params: list[tuple[str, str]], *, compter: bool = False,
          debut: int = 0, fin: int | None = None) -> tuple[list[dict[str, Any]], int | None]:
    entetes = {"apikey": ctx.settings.supabase_anon_key, "Authorization": f"Bearer {ctx.jeton}"}
    if compter:
        entetes["Prefer"] = "count=exact"
    if fin is not None:
        entetes["Range-Unit"] = "items"
        entetes["Range"] = f"{debut}-{fin}"
    r = requests.get(f"{ctx.settings.supabase_url}/rest/v1/{source}", headers=entetes, params=params, timeout=15)
    if r.status_code == 500 and "57014" in r.text:
        # 13/11 : délai de la base dépassé (8 s). Le registre des transactions met 8,4 s au premier appel à froid,
        # puis ~2,4 s : UNE seule nouvelle tentative, jamais une boucle.
        r = requests.get(f"{ctx.settings.supabase_url}/rest/v1/{source}", headers=entetes, params=params, timeout=15)
    if r.status_code == 404:
        raise Refus(f"Cet objet n'est pas encore disponible dans la base ({source}).")
    if not r.ok and r.status_code != 416:
        raise LectureRefusee(f"lecture de {source} impossible ({r.status_code})")
    total = None
    plage = r.headers.get("Content-Range") or ""
    if "/" in plage and plage.rsplit("/", 1)[1].isdigit():
        total = int(plage.rsplit("/", 1)[1])
    return (r.json() or []) if r.ok else [], total


# ── traduction des filtres ────────────────────────────────────────────────────
def _objet(nom: str) -> Objet:
    objet = PAR_NOM.get(str(nom or "").strip())
    if not objet:
        raise Refus(f"Objet inconnu « {nom} ». Objets lisibles : {', '.join(o.nom for o in OBJETS)}.")
    return objet


def _colonne(objet: Objet, nom: str):
    colonne = objet.colonne(str(nom or "").strip())
    if not colonne:
        raise Refus(f"Colonne inconnue « {nom} » pour {objet.nom}. Appelle decrire('{objet.nom}').")
    return colonne


def _valeur(type_: str, brut: str, colonne: str) -> str:
    v = str(brut if brut is not None else "").strip()
    if type_ == "nombre":
        try:
            float(v.replace(",", ".").replace(" ", ""))
        except ValueError:
            raise Refus(f"« {v} » n'est pas un nombre (colonne {colonne}).") from None
        return v.replace(",", ".").replace(" ", "")
    if type_ == "date" and not re.fullmatch(r"\d{4}(-\d{2}(-\d{2}([ T]\d{2}:\d{2}(:\d{2})?)?)?)?", v):
        raise Refus(f"« {v} » n'est pas une date AAAA-MM-JJ (colonne {colonne}).")
    if type_ == "booleen":
        if v.lower() not in {"true", "false", "vrai", "faux", "oui", "non"}:
            raise Refus(f"« {v} » : réponds vrai ou faux (colonne {colonne}).")
        return "true" if v.lower() in {"true", "vrai", "oui"} else "false"
    return v


def _quoter(v: str) -> str:
    # une valeur dans une liste PostgREST : entre guillemets, guillemets et barres échappés
    return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _norme(texte: Any) -> str:
    # comparer sans casse, sans accents, sans espaces en trop (« exclusif » = « EXCLUSIF », « Échu » = « echu »)
    sans_accents = unicodedata.normalize("NFKD", str(texte or "")).encode("ascii", "ignore").decode("ascii")
    return " ".join(sans_accents.lower().replace("_", " ").split())


def _stockees(colonne: Colonne, demande: str, *, partiel: str | None = None) -> list[str]:
    # 13/11 : la valeur DITE par le modèle -> la ou les valeurs STOCKÉES (par la valeur ou son libellé).
    # ⛔ Rien ne correspond = REFUS avec la liste : jamais un filtre sur une valeur qui n'existe pas (zéro muet).
    cible = _norme(demande)
    if partiel == "contient":
        trouvees = [v for v, l in colonne.valeurs if cible and (cible in _norme(v) or cible in _norme(l))]
    elif partiel == "commence_par":
        trouvees = [v for v, l in colonne.valeurs if cible and (_norme(v).startswith(cible) or _norme(l).startswith(cible))]
    else:
        trouvees = [v for v, l in colonne.valeurs if cible in {_norme(v), _norme(l)}]
    if not trouvees:
        raise Refus(f"La valeur « {demande} » n'existe pas dans {colonne.nom}. Valeurs possibles : "
                    f"{_valeurs_lisibles(colonne)}. Choisis-en une ; si aucune ne convient, dis-le sans conclure « aucun ».")
    return list(dict.fromkeys(trouvees))


def _filtre_liste(nom: str, valeurs: list[str], *, exclure: bool = False) -> tuple[str, str]:
    if len(valeurs) == 1:
        return (nom, f"{'neq' if exclure else 'eq'}.{valeurs[0]}")
    return (nom, f"{'not.in' if exclure else 'in'}.(" + ",".join(_quoter(v) for v in valeurs[:60]) + ")")


MOI = "moi"
# colonnes texte qui sont des IDENTIFIANTS : égalité stricte (rapide, indexée), jamais « sans les majuscules »
_IDENTIFIANT = re.compile(r"(_id|_key|email|^numero_|code_postal)$|^numero_")


def traduire_filtres(objet: Objet, filtres: list[dict[str, Any]], moi: str | None = None) -> list[tuple[str, str]]:
    params: list[tuple[str, str]] = []
    for f in filtres or []:
        colonne = _colonne(objet, f.get("colonne"))
        op = str(f.get("operateur") or "")
        if op not in _PERMIS[colonne.type]:
            raise Refus(f"Opérateur « {op} » impossible sur {colonne.nom} ({colonne.type}). "
                        f"Possibles : {', '.join(sorted(_PERMIS[colonne.type]))}.")
        brut = f.get("valeur")
        if colonne.nom == "negociateur_email" and _norme(brut) == MOI:
            # 13/11 : « mes … » -> le modèle écrit « moi », NOTRE serveur met l'adresse. Elle ne part jamais chez
            # OpenAI (règle de l'étape 1) et le modèle ne peut plus en fabriquer une (il en a inventé 5 le 13/11).
            if not moi:
                raise Refus("Je ne connais pas l'e-mail de la personne : je ne peux pas filtrer sur « moi ».")
            brut = moi
        if op == "est_vide":
            params.append((colonne.nom, "is.null"))
        elif op == "n_est_pas_vide":
            params.append((colonne.nom, "not.is.null"))
        elif colonne.valeurs and op in {"egal", "different", "parmi", "contient", "commence_par"}:
            # colonne à liste : on filtre sur la ou les valeurs STOCKÉES, jamais sur le mot du modèle
            if op == "parmi":
                morceaux = [x for x in str(brut or "").split("|") if x.strip()]
                if not morceaux:
                    raise Refus(f"« parmi » demande des valeurs séparées par | (colonne {colonne.nom}).")
                valeurs = list(dict.fromkeys(v for m in morceaux for v in _stockees(colonne, m)))
            else:
                valeurs = _stockees(colonne, str(brut or ""), partiel=op if op in {"contient", "commence_par"} else None)
            params.append(_filtre_liste(colonne.nom, valeurs, exclure=op == "different"))
        elif op == "parmi":
            valeurs = [_valeur(colonne.type, x, colonne.nom) for x in str(brut or "").split("|") if x.strip()]
            if not valeurs:
                raise Refus(f"« parmi » demande des valeurs séparées par | (colonne {colonne.nom}).")
            params.append((colonne.nom, "in.(" + ",".join(_quoter(x) for x in valeurs[:50]) + ")"))
        elif op in {"contient", "commence_par"}:
            v = re.sub(r"[*%]", "", str(brut or "")).strip()  # pas de joker glissé par le modèle
            if not v:
                raise Refus(f"Valeur vide pour « {op} » (colonne {colonne.nom}).")
            params.append((colonne.nom, f"ilike.{'*' if op == 'contient' else ''}{v}*"))
        elif op == "json_contient":
            v = str(brut or "").strip()
            params.append((colonne.nom, "cs." + json.dumps([v], ensure_ascii=False)))
        elif op in {"egal", "different"} and colonne.type == "texte" and not _IDENTIFIANT.search(colonne.nom):
            # 13/11 : un texte libre (nom, prénom, ville…) se compare SANS les majuscules -- « Durand » ne trouvait
            # que 4 fiches sur ~80, presque toutes écrites « DURAND ». ilike sans joker = égalité sans la casse.
            # Les identifiants (numéros, clés, e-mails) restent en égalité stricte : elle garde l'index.
            v = re.sub(r"[*%]", "", str(brut or "")).strip()
            if not v:
                raise Refus(f"Valeur vide pour « {op} » (colonne {colonne.nom}) : pour une case vide, utilise est_vide.")
            params.append((colonne.nom, f"{'not.ilike' if op == 'different' else 'ilike'}.{v}"))
        else:
            v = _valeur(colonne.type, brut, colonne.nom)
            code = {"egal": "eq", "different": "neq"}.get(op) or _COMPARAISONS[op]
            params.append((colonne.nom, f"{code}.{v}"))
    return params


def _court(valeur: Any) -> Any:
    if isinstance(valeur, (dict, list)):
        valeur = json.dumps(valeur, ensure_ascii=False)
    if isinstance(valeur, str) and len(valeur) > MAX_CARACTERES_VALEUR:
        return valeur[:MAX_CARACTERES_VALEUR] + "…"
    return valeur


def _lisible(objet: Objet, nom: str, valeur: Any) -> Any:
    # un CODE (type_bien « 1 », offre_type « 0 »…) part au modèle avec son libellé : « Maison », pas « 1 »
    colonne = objet.colonne(nom)
    if colonne and colonne.valeurs and isinstance(valeur, (str, int)) and str(valeur).isdigit():
        return next((l for v, l in colonne.valeurs if v == str(valeur)), valeur)
    return _court(valeur)


# 13/11 : un zéro ne se croit pas sans vérification (5 fausses réponses sur 30 étaient des zéros crus)
_ZERO = ("0 ligne avec ces filtres. Avant de répondre « aucun », vérifie : la bonne colonne ? la bonne valeur ? "
         "le bon objet (un bien absent de biens peut être dans biens_historique ou biens_archives) ? un nom propre "
         "peut s'écrire autrement (essaie contient). Si tu réponds « aucun », dis avec quels filtres.")


# ── les trois gestes génériques ───────────────────────────────────────────────
def decrire(ctx: ContexteAssistant, params: dict[str, Any]) -> dict[str, Any]:
    objet = _objet(params.get("objet"))
    return {"objet": objet.nom, "description": objet.description,
            "colonnes": [{"nom": c.nom, "type": c.type, "sens": c.description,
                          **({"valeurs": _valeurs_lisibles(c)} if c.valeurs else {})} for c in objet.colonnes],
            "colonnes_par_defaut": list(objet.par_defaut)}


def chercher(ctx: ContexteAssistant, params: dict[str, Any]) -> dict[str, Any]:
    objet = _objet(params.get("objet"))
    colonnes = [_colonne(objet, c).nom for c in (params.get("colonnes") or [])] or list(objet.par_defaut)
    filtres = traduire_filtres(objet, params.get("filtres") or [], moi=ctx.email)
    tri = str(params.get("tri") or "").strip() or objet.cle
    _colonne(objet, tri)
    ordre = "asc" if params.get("ordre") == "asc" else "desc"
    limite = max(1, min(int(params.get("limite") or LIMITE_PAR_DEFAUT), MAX_LIGNES_RENDUES))
    requete = [("select", ",".join(dict.fromkeys(colonnes))), *filtres, *objet.filtres_imposes(ctx.email),
               ("order", f"{tri}.{ordre}.nullslast")]
    lignes, total = _lire(ctx, objet.source, requete, compter=True, debut=0, fin=limite - 1)
    resultat = {"objet": objet.nom, "total": total, "rendues": len(lignes),
                "lignes": [{k: _lisible(objet, k, v) for k, v in ligne.items()} for ligne in lignes]}
    if total == 0 and filtres:
        resultat["attention"] = _ZERO
    return resultat


def compter(ctx: ContexteAssistant, params: dict[str, Any]) -> dict[str, Any]:
    objet = _objet(params.get("objet"))
    filtres = traduire_filtres(objet, params.get("filtres") or [], moi=ctx.email) + objet.filtres_imposes(ctx.email)
    groupe = str(params.get("regrouper_par") or "").strip()
    somme = str(params.get("somme_de") or "").strip()
    if groupe:
        _colonne(objet, groupe)
    if somme and _colonne(objet, somme).type != "nombre":
        raise Refus(f"La somme ne se fait que sur une colonne nombre ({somme} n'en est pas une).")
    if not groupe and not somme:
        _, total = _lire(ctx, objet.source, [("select", objet.cle), *filtres], compter=True, debut=0, fin=0)
        return {"objet": objet.nom, "total": total, **({"attention": _ZERO} if total == 0 and params.get("filtres") else {})}
    # regrouper ou sommer : on lit les lignes (colonnes utiles seulement), page par page, jusqu'au plafond
    colonnes = ",".join(dict.fromkeys([c for c in (groupe, somme) if c] or [objet.cle]))
    lues: list[dict[str, Any]] = []
    total = None
    while len(lues) < PLAFOND_LIGNES_CALCUL:
        page, total = _lire(ctx, objet.source, [("select", colonnes), *filtres, ("order", f"{objet.cle}.asc")],
                            compter=total is None, debut=len(lues), fin=len(lues) + PAGE - 1)
        lues.extend(page)
        if len(page) < PAGE:
            break
    groupes: dict[str, dict[str, float]] = {}
    for ligne in lues:
        cle = str(ligne.get(groupe)) if groupe else "tout"
        g = groupes.setdefault(cle, {"nombre": 0, "somme": 0.0})
        g["nombre"] += 1
        if somme and isinstance(ligne.get(somme), (int, float)):
            g["somme"] += float(ligne[somme])
    resultat = sorted(({"valeur": _lisible(objet, groupe, k) if groupe else k, "nombre": int(v["nombre"]),
                        **({"somme": round(v["somme"], 2)} if somme else {})}
                       for k, v in groupes.items()), key=lambda x: -x["nombre"])
    sortie = {"objet": objet.nom, "total": total, "lignes_lues": len(lues),
              "tronque": total is not None and len(lues) < total, "groupes": resultat[:MAX_LIGNES_RENDUES]}
    if total == 0 and params.get("filtres"):
        sortie["attention"] = _ZERO
    return sortie


# ── les fonctions métier ──────────────────────────────────────────────────────
_RUBRIQUES = ("ag_interieur_json", "ag_exterieur_json", "terrain_json", "diagnostiques_json", "copropriete_json")
_SIMPLES = ("surface", "surface_habitable_detail", "surface_terrain_detail", "nb_pieces", "nb_chambres", "etage_detail",
            "garage_box_detail", "terrasse_detail", "ascenseur_detail", "copropriete_detail", "honoraires_resume",
            "prix_net_vendeur", "ville_publique_detail", "latitude_detail", "longitude_detail", "texte_principal_titre",
            "detail_statut_name", "etat_transaction")


def _proprietes(texte: Any) -> list[str]:
    try:
        bloc = json.loads(texte) if isinstance(texte, str) else texte
    except (TypeError, ValueError):
        return []
    props = (bloc or {}).get("props") if isinstance(bloc, dict) else None
    sortie = []
    for p in (props or {}).values():
        if isinstance(p, dict):
            v = str(p.get("value") if p.get("value") is not None else "").strip()
            if v and v not in {"0", "null", "None"}:
                label = re.sub(r"<[^>]+>", "", str(p.get("label") or "")).strip()
                sortie.append(f"{label} : {v}")
    return sortie


def fiches_biens(ctx: ContexteAssistant, params: dict[str, Any]) -> dict[str, Any]:
    # ⛔ un EXTRAIT choisi : la fiche porte aussi les téléphones et e-mails des propriétaires, ils ne partent pas
    ids = [int(x) for x in (params.get("app_dossier_ids") or [])[:MAX_FICHES] if str(x).strip().lstrip("-").isdigit()]
    if not ids:
        raise Refus("Donne au moins un app_dossier_id (identifiant du bien, colonne de biens).")
    lignes, _ = _lire(ctx, "app_dossier_details_current",
                      [("select", "app_dossier_id,hektor_annonce_id,detail_payload_json"), ("app_dossier_id", f"in.({','.join(map(str, ids))})")])
    fiches = []
    for ligne in lignes:
        try:
            d = json.loads(ligne.get("detail_payload_json") or "{}")
        except ValueError:
            d = {}
        texte = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", str(d.get("texte_principal_html") or "")))).strip()
        fiches.append({
            "app_dossier_id": ligne.get("app_dossier_id"), "hektor_annonce_id": ligne.get("hektor_annonce_id"),
            **{k: d.get(k) for k in _SIMPLES if d.get(k) not in (None, "", "0", "null")},
            "caracteristiques": [x for r in _RUBRIQUES for x in _proprietes(d.get(r))][:80],
            "texte_annonce": texte[:1500],
        })
    return {"fiches": fiches, "introuvables_ou_hors_droits": sorted(set(ids) - {f["app_dossier_id"] for f in fiches})}


def notes_transaction(ctx: ContexteAssistant, params: dict[str, Any]) -> dict[str, Any]:
    # ⛔ les notes et conditions sont lisibles par tous dans la base : on lit D'ABORD la transaction avec le jeton,
    #   et seulement si la personne la voit, ses notes. C'est le geste de l'écran (à travers le registre).
    try:
        affaire = int(params.get("app_affaire_id"))
    except (TypeError, ValueError):
        raise Refus("Donne l'app_affaire_id de la transaction (colonne de transactions).") from None
    visible, _ = _lire(ctx, "app_affaire_ledger", [("select", "app_affaire_id,kind,state,app_dossier_id"),
                                                    ("app_affaire_id", f"eq.{affaire}"), ("limit", "1")])
    if not visible:
        raise Refus("Transaction introuvable ou hors de tes droits : je ne peux pas lire ses notes.")
    notes, _ = _lire(ctx, "app_affaire_note", [("select", "texte,ecrit_le,origine"), ("app_affaire_id", f"eq.{affaire}"),
                                               ("order", "ecrit_le.desc"), ("limit", "30")])
    conditions, _ = _lire(ctx, "app_affaire_condition", [("select", "rang,libelle,jours,date_echeance,etat,date_levee,note"),
                                                         ("app_affaire_id", f"eq.{affaire}"), ("order", "rang.asc"), ("limit", "30")])
    return {"transaction": visible[0], "notes": [{k: _court(v) for k, v in n.items()} for n in notes],
            "conditions": [{k: _court(v) for k, v in c.items()} for c in conditions]}


def agenda(ctx: ContexteAssistant, params: dict[str, Any]) -> dict[str, Any]:
    # La route de l'écran, appelée telle quelle : MÊME garde (hors admin, l'agenda de la personne seulement).
    from ..routers import google_workspace as gw
    from .google_calendar_event_link_service import GoogleCalendarEventLinkService
    from .supabase_admin import SupabaseAdminService

    dossier = int(params.get("app_dossier_id") or 0) or None
    reponse = gw.list_google_calendar_event_links(
        appDossierId=dossier, hektorAnnonceId=None, hektorContactId=(str(params.get("hektor_contact_id") or "").strip() or None),
        calendarEmail=None, startAt=(str(params.get("debut") or "").strip() or None), endAt=(str(params.get("fin") or "").strip() or None),
        limit=50, authorization=f"Bearer {ctx.jeton}", settings=ctx.settings,
        admin_service=SupabaseAdminService(ctx.settings), link_service=GoogleCalendarEventLinkService(ctx.settings),
    )
    garder = ("event_type", "summary", "starts_at", "ends_at", "status", "location", "app_dossier_id", "hektor_annonce_id",
              "hektor_contact_id", "google_calendar_email")
    evenements = [{k: _court(e.get(k)) for k in garder if e.get(k) not in (None, "")}
                  for e in reponse.get("events") or [] if str(e.get("status") or "") != "deleted"]  # comme l'écran
    return {"evenements": evenements, "nombre": len(evenements)}


# ── les schémas vus par le modèle (stricts : tout est obligatoire, "" ou [] = rien) ──
_NOMS = [o.nom for o in OBJETS]
_FILTRES = {"type": "array", "items": {"type": "object", "additionalProperties": False,
            "required": ["colonne", "operateur", "valeur"],
            "properties": {"colonne": {"type": "string"}, "operateur": {"type": "string", "enum": list(OPERATEURS)},
                           "valeur": {"type": "string", "description": "pour « parmi » : valeurs séparées par |"}}}}


def _schema(proprietes: dict[str, Any]) -> dict[str, Any]:
    return {"type": "object", "additionalProperties": False, "required": list(proprietes), "properties": proprietes}


FONCTIONS_LECTURE: tuple[Fonction, ...] = (
    Fonction("decrire", "Décrit un objet lisible : ses colonnes et ce qu'elles veulent dire. À appeler avant de filtrer "
             "sur une colonne que tu ne connais pas.", TOUS_LES_ROLES,
             _schema({"objet": {"type": "string", "enum": _NOMS}}), decrire),
    Fonction("chercher", f"Cherche des lignes d'un objet, avec des filtres (tous combinés par ET), un tri et une limite "
             f"(au plus {MAX_LIGNES_RENDUES}). Rend aussi le total exact des lignes qui correspondent. colonnes=[] = colonnes "
             f"par défaut ; tri=\"\" = tri par défaut.", TOUS_LES_ROLES,
             _schema({"objet": {"type": "string", "enum": _NOMS}, "filtres": _FILTRES,
                      "colonnes": {"type": "array", "items": {"type": "string"}}, "tri": {"type": "string"},
                      "ordre": {"type": "string", "enum": ["asc", "desc"]}, "limite": {"type": "integer"}}), chercher),
    Fonction("compter", f"Compte les lignes d'un objet qui correspondent aux filtres ; peut regrouper par une colonne et "
             f"faire la somme d'une colonne nombre (sur {PLAFOND_LIGNES_CALCUL} lignes au plus : la réponse dit si c'est "
             f"tronqué). regrouper_par=\"\" et somme_de=\"\" = juste le total.", TOUS_LES_ROLES,
             _schema({"objet": {"type": "string", "enum": _NOMS}, "filtres": _FILTRES,
                      "regrouper_par": {"type": "string"}, "somme_de": {"type": "string"}}), compter),
    Fonction("fiches_biens", f"Caractéristiques détaillées de 1 à {MAX_FICHES} biens (surface, pièces, chambres, terrain, "
             "étage, diagnostics, texte de l'annonce…), par app_dossier_id.", TOUS_LES_ROLES,
             _schema({"app_dossier_ids": {"type": "array", "items": {"type": "integer"}}}), fiches_biens),
    Fonction("notes_transaction", "Notes et conditions suspensives d'une transaction, par app_affaire_id (seulement si "
             "tu as le droit de voir la transaction).", TOUS_LES_ROLES,
             _schema({"app_affaire_id": {"type": "integer"}}), notes_transaction),
    Fonction("agenda", "Les rendez-vous de l'agenda entre deux dates (AAAA-MM-JJ ou date-heure ISO), éventuellement pour "
             "un bien (app_dossier_id, 0 = tous) ou un contact (hektor_contact_id, \"\" = tous).", TOUS_LES_ROLES,
             _schema({"debut": {"type": "string"}, "fin": {"type": "string"}, "app_dossier_id": {"type": "integer"},
                      "hektor_contact_id": {"type": "string"}}), agenda),
)
