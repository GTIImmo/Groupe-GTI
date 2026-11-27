#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""TEMPS 2 DU CHANTIER CLASSEUR -- LE REGISTRE JUGE SUR LUI-MEME, SANS LE GEL.   19/11/2026

    .venv\Scripts\python.exe -X utf8 phase2\checks\temps2_registre_juge_sur_lui_meme_2026-11-19.py

⛔ CE SCRIPT N'ECRIT RIEN EN BASE. Des GET chez Supabase, un CSV dans notice/.
⛔ IL NE LIT NI LE GEL (app_classeur_lien) NI LE SHEET : le registre doit tenir debout seul.

LA QUESTION (Frederic, 19/11) : app_affaire_ledger respecte-t-il SES PROPRES INVARIANTS ?
Chaque invariant est une fonction qui rend la liste de ses cas. Les dates sont celles DU
CHAINAGE (`_date_de_tri`, la premiere proposition d'une offre) et les acquereurs ceux DU
CHAINAGE (`_acquereurs`) : on juge le registre avec les yeux de la regle, pas avec une copie.

⭐ UN ZERO NE SE CROIT PAS SANS TEMOIN POSITIF. Chaque detecteur est rejoue sur le registre
  augmente d'un JEU SEME en memoire (des dossiers fabriques, chacun portant exactement le
  defaut qu'un detecteur cherche). Le detecteur doit trouver CHAQUE cas seme qui le concerne,
  et le compte reel ne doit pas bouger. Sinon : sortie 2, « pas pu mesurer ».

Sortie : 0 mesure faite (les anomalies sont des CONSTATS, listes dans le CSV)
         2 un temoin seme n'a pas ete vu, ou la lecture a echoue.
"""
from __future__ import annotations

import csv
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import date as Date
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
os.chdir(RACINE)
sys.path.insert(0, str(RACINE))
sys.path.insert(0, str(RACINE / "monitoring"))
import check_gti_health as cgh                                      # noqa: E402
from phase2.sync.affaire_ledger import (                            # noqa: E402
    ETATS_COMPROMIS_MORTS, ETATS_OFFRE_ACCEPTEE, ETATS_OFFRE_MORTS,
    FENETRE_OFFRE_REGULARISEE_JOURS, _acquereurs, _date_de_tri)

SORTIE = RACINE / "notice" / "TEMPS2_REGISTRE_ANOMALIES_2026-11-19.csv"
NOS_GESTES = "2026-11-10"          # le premier geste de masse (temps 1)
CHAMPS = ("app_affaire_id,app_chaine_id,app_dossier_uuid,app_dossier_numero,hektor_annonce_id,"
          "kind,state,date,hektor_affaire_id,present_in_hektor,transaction_origine,"
          "acquereurs_json,hektor_acquereur_id,numero_mandat,hektor_mandat_id,montant,"
          "propositions_json,last_seen_at")


def client():
    for f in (RACINE / ".env", RACINE / "backend" / ".env", RACINE / "apps" / "hektor-v1" / ".env"):
        if f.exists():
            cgh.load_env_file(f)
    url = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL")
    cle = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not (url and cle):
        raise SystemExit("⛔ pas d'identifiants Supabase -- rien n'est mesure.")
    return cgh.SupabaseClient(url, cle, timeout_seconds=90)


def lire_registre(cl) -> list[dict]:
    out, apres = [], 0
    while True:
        page = cl.get("app_affaire_ledger", {"select": CHAMPS, "app_affaire_id": "gt.%d" % apres,
                                             "order": "app_affaire_id.asc", "limit": "1000"}) or []
        if not page:
            return out
        out.extend(page)
        apres = int(page[-1]["app_affaire_id"])


# ═══ LA LIGNE, VUE PAR LE CHAINAGE ═════════════════════════════════════════════
def preparer(l: dict) -> dict:
    t = dict(l)
    t["genre"] = str(l.get("kind") or "").strip().lower()
    t["etat"] = str(l.get("state") or "").strip().lower()
    t["numero"] = str(l.get("hektor_affaire_id") or "").strip()
    t["effacee"] = bool(t["numero"]) and l.get("present_in_hektor") is False   # la regle du run
    t["tri"] = _date_de_tri(l.get("kind"), l.get("date"), l.get("propositions_json"))
    t["acqs"] = _acquereurs(l.get("acquereurs_json"))
    if not t["acqs"] and str(l.get("hektor_acquereur_id") or "").strip() not in ("", "0"):
        t["acqs"] = {str(l["hektor_acquereur_id"]).strip()}
    props = l.get("propositions_json")
    if isinstance(props, str):
        try:
            props = json.loads(props)
        except ValueError:
            props = None
    t["journal"] = [p for p in props if isinstance(p, dict)] if isinstance(props, list) else []
    t["classeur"] = bool(str(l.get("transaction_origine") or "").strip())
    return t


def jour(txt):
    try:
        return Date.fromisoformat(str(txt)[:10])
    except (TypeError, ValueError):
        return None


def par_chaine(lignes):
    d = defaultdict(list)
    for t in lignes:
        d[t.get("app_chaine_id")].append(t)
    return d


# ═══ LES INVARIANTS -- chacun rend [(cle, detail)] ═════════════════════════════
def i_deux_ventes(ch):
    return [(c, "%d ventes" % n) for c, m in ch.items()
            if (n := sum(1 for t in m if not t["effacee"] and t["genre"] == "vente")) >= 2]


def i_deux_compromis_vivants(ch):
    return [(c, "%d compromis vivants" % n) for c, m in ch.items()
            if (n := sum(1 for t in m if not t["effacee"] and t["genre"] == "compromis"
                         and t["etat"] not in ETATS_COMPROMIS_MORTS)) >= 2]


def i_deux_biens(ch):
    return [(c, "biens %s" % sorted(b)) for c, m in ch.items()
            if len(b := {str(t.get("hektor_annonce_id")) for t in m}) >= 2]


def i_etiquette_pas_bijective(ch):
    out = [(c, "%d etiquettes" % len(u)) for c, m in ch.items()
           if len(u := {t.get("app_dossier_uuid") for t in m}) != 1]
    chaines_par_u = defaultdict(set)
    numeros_par_u = defaultdict(set)
    u_par_numero = defaultdict(set)
    for m in ch.values():
        for t in m:
            chaines_par_u[t.get("app_dossier_uuid")].add(t.get("app_chaine_id"))
            numeros_par_u[t.get("app_dossier_uuid")].add(t.get("app_dossier_numero"))
            u_par_numero[t.get("app_dossier_numero")].add(t.get("app_dossier_uuid"))
    out += [(u, "etiquette sur %d chaines" % len(s)) for u, s in chaines_par_u.items() if len(s) > 1]
    out += [(u, "etiquette a %d numeros" % len(s)) for u, s in numeros_par_u.items() if len(s) > 1]
    out += [(n, "numero sur %d etiquettes" % len(s)) for n, s in u_par_numero.items() if len(s) > 1]
    return out


def i_numero_pas_le_minimum(ch):
    out = []
    for c, m in ch.items():
        viv = [int(t["app_affaire_id"]) for t in m if not t["effacee"]]
        if viv and c is not None and int(c) != min(viv):
            out.append((c, "le plus petit membre vivant est %d" % min(viv)))
    return out


def i_sans_chaine_ni_etiquette(ch):
    return [(t["app_affaire_id"], "sans chaine / etiquette / numero")
            for m in ch.values() for t in m
            if t.get("app_chaine_id") is None or not t.get("app_dossier_uuid")
            or not t.get("app_dossier_numero")]


def i_numero_de_dossier_mal_forme(ch):
    out = []
    for c, m in ch.items():
        n = str(m[0].get("app_dossier_numero") or "")
        if not (len(n) == 10 and n[0] == "D" and n[1:5].isdigit() and 2000 <= int(n[1:5]) <= 2030):
            out.append((c, "numero %s" % n))
    return out


def i_chaine_toute_effacee(ch):
    return [(c, "%d membres, tous effaces chez Hektor" % len(m)) for c, m in ch.items()
            if all(t["effacee"] for t in m)]


def i_bloc_apres_la_vente(ch):
    """Le test empirique du verificateur (③) : un bloc date APRES la vente qui ferme sa chaine."""
    out = []
    for c, m in ch.items():
        viv = [t for t in m if not t["effacee"]]
        ventes = [jour(t["tri"]) for t in viv if t["genre"] == "vente" and jour(t["tri"])]
        if not ventes:
            continue
        v = min(ventes)
        for t in viv:
            if t["genre"] != "vente" and jour(t["tri"]) and jour(t["tri"]) > v:
                meme = any(t["acqs"] & x["acqs"] for x in viv if x["genre"] == "vente")
                out.append((c, "%s %s du %s APRES la vente du %s%s" % (
                    t["genre"], t["app_affaire_id"], t["tri"], v,
                    " (meme acheteur)" if meme else "")))
    return out


def i_vente_avant_compromis(ch):
    out = []
    for c, m in ch.items():
        viv = [t for t in m if not t["effacee"]]
        for v in (t for t in viv if t["genre"] == "vente" and jour(t["tri"])):
            for cp in (t for t in viv if t["genre"] == "compromis" and jour(t["tri"])):
                if jour(v["tri"]) < jour(cp["tri"]):
                    out.append((c, "vente %s du %s AVANT le compromis %s du %s" % (
                        v["app_affaire_id"], v["tri"], cp["app_affaire_id"], cp["tri"])))
    return out


def i_offre_loin_apres_compromis(ch):
    """Une offre datee plus de 31 jours APRES le compromis de son dossier (la regle B tolere 31)."""
    out = []
    for c, m in ch.items():
        viv = [t for t in m if not t["effacee"]]
        cps = [jour(t["tri"]) for t in viv if t["genre"] == "compromis" and jour(t["tri"])]
        if not cps:
            continue
        for o in (t for t in viv if t["genre"] == "offre" and jour(t["tri"])):
            ecart = (jour(o["tri"]) - min(cps)).days
            if ecart > FENETRE_OFFRE_REGULARISEE_JOURS:
                out.append((c, "offre %s datee %d j apres le compromis" % (o["app_affaire_id"], ecart)))
    return out


def i_refus_de_nous_dans_un_dossier_vendu(ch):
    """Une offre que NOUS avons refusee (entree « refus » du 10/11 ou apres) dans un dossier
    qui porte une vente -- la famille des 20 refus a tort du 11/11."""
    out = []
    for c, m in ch.items():
        viv = [t for t in m if not t["effacee"]]
        ventes = [t for t in viv if t["genre"] == "vente"]
        if not ventes:
            continue
        for o in viv:
            if o["genre"] != "offre" or o["etat"] not in ETATS_OFFRE_MORTS:
                continue
            if not any(e.get("type") == "refus" and str(e.get("date") or "") >= NOS_GESTES
                       for e in o["journal"]):
                continue
            meme = any(o["acqs"] & v["acqs"] for v in ventes)
            out.append((c, "offre %s refusee par nous, dossier vendu, %s" % (
                o["app_affaire_id"], "MEME acheteur que la vente" if meme else "autre acheteur")))
    return out


def i_deux_offres_acceptees(ch):
    return [(c, "%d offres acceptees" % n) for c, m in ch.items()
            if (n := sum(1 for t in m if not t["effacee"] and t["genre"] == "offre"
                         and t["etat"] in ETATS_OFFRE_ACCEPTEE)) >= 2]


def i_etat_contre_journal(ch):
    """L'ETAT d'une offre contre le DERNIER mouvement de son journal (ecrit par Hektor seul)."""
    attendu = {"accepte": ETATS_OFFRE_ACCEPTEE, "refus": ETATS_OFFRE_MORTS, "proposition": {"proposed"}}
    out = []
    for c, m in ch.items():
        for o in m:
            if o["genre"] != "offre" or not o["journal"]:
                continue
            dernier = max(o["journal"], key=lambda e: str(e.get("date") or ""))
            ok = attendu.get(str(dernier.get("type") or ""))
            if ok is not None and o["etat"] not in ok:
                out.append((c, "offre %s etat %s, dernier mouvement %s du %s" % (
                    o["app_affaire_id"], o["etat"] or "(vide)", dernier.get("type"), dernier.get("date"))))
    return out


def i_doublon_de_numero(ch):
    vus = defaultdict(list)
    for m in ch.values():
        for t in m:
            if t["numero"]:
                vus[(t["genre"], t["numero"])].append(t["app_affaire_id"])
    return [("%s %s" % k, "lignes %s" % v) for k, v in vus.items() if len(v) > 1]


def i_copie_du_classeur(ch):
    """Une transaction du CLASSEUR qui double une transaction de HEKTOR : meme bien, meme genre,
    meme jour de tri. (Les 25 copies de C5 que la 1re session a nommees.)"""
    par_bien = defaultdict(list)
    for m in ch.values():
        for t in m:
            par_bien[str(t.get("hektor_annonce_id"))].append(t)
    out = []
    for bien, ts in par_bien.items():
        hek = [t for t in ts if not t["classeur"] and t["tri"]]
        for k in (t for t in ts if t["classeur"] and t["tri"]):
            jum = [h for h in hek if h["genre"] == k["genre"] and h["tri"][:10] == k["tri"][:10]]
            if jum:
                out.append((k.get("app_chaine_id"), "%s %s du classeur double %s (bien %s)%s" % (
                    k["genre"], k["app_affaire_id"], [h["app_affaire_id"] for h in jum], bien,
                    "" if any(h.get("app_chaine_id") == k.get("app_chaine_id") for h in jum)
                    else " -- dans un AUTRE dossier")))
    return out


def i_plage_app_sans_numero(ch):
    return [(t["app_affaire_id"], "%s ne dans l'app, jamais numerote par Hektor" % t["genre"])
            for m in ch.values() for t in m
            if int(t["app_affaire_id"]) >= 1_000_000 and not t["numero"] and not t["classeur"]]


def i_classeur_avec_numero(ch):
    return [(t["app_affaire_id"], "transaction du classeur PORTANT un numero Hektor")
            for m in ch.values() for t in m if t["classeur"] and t["numero"]]


def i_sans_date_de_tri(ch):
    return [(t["app_affaire_id"], "%s %s sans date de tri" % (t["genre"], t["etat"] or "(vide)"))
            for m in ch.values() for t in m if not t["effacee"] and t["tri"] is None]


def i_offre_sans_etat(ch):
    return [(t["app_affaire_id"], "offre sans etat") for m in ch.values() for t in m
            if t["genre"] == "offre" and not t["etat"]]


def i_genre_inconnu(ch):
    return [(t["app_affaire_id"], "genre %r" % t["genre"]) for m in ch.values() for t in m
            if t["genre"] not in ("offre", "compromis", "vente")]


def i_sans_bien(ch):
    return [(t["app_affaire_id"], "sans bien") for m in ch.values() for t in m
            if t.get("hektor_annonce_id") in (None, "")]


def i_non_relue_cette_nuit(ch, nuit):
    """Le geste LIRE : une transaction presente chez Hektor que le run de la nuit n'a pas revue."""
    return [(t["app_affaire_id"], "vue la derniere fois le %s" % t.get("last_seen_at"))
            for m in ch.values() for t in m
            if t["numero"] and not t["effacee"] and str(t.get("last_seen_at") or "")[:10] < nuit]


INVARIANTS = [
    # (famille, nom, fonction, gravite)
    ("DOSSIER", "deux ventes dans un dossier", i_deux_ventes, "dur"),
    ("DOSSIER", "deux compromis vivants", i_deux_compromis_vivants, "dur"),
    ("DOSSIER", "un dossier sur deux biens", i_deux_biens, "dur"),
    ("ETIQUETTE", "etiquette, chaine et numero pas en bijection", i_etiquette_pas_bijective, "dur"),
    ("DOSSIER", "numero de chaine different du plus petit membre vivant", i_numero_pas_le_minimum, "dur"),
    ("ETIQUETTE", "transaction sans chaine, etiquette ou numero", i_sans_chaine_ni_etiquette, "dur"),
    ("ETIQUETTE", "numero de dossier mal forme", i_numero_de_dossier_mal_forme, "a juger"),
    ("DOSSIER", "dossier dont tous les membres sont effaces chez Hektor", i_chaine_toute_effacee, "constat"),
    ("SEQUENCE", "un bloc date apres la vente de son dossier", i_bloc_apres_la_vente, "a juger"),
    ("SEQUENCE", "une vente datee avant le compromis de son dossier", i_vente_avant_compromis, "a juger"),
    ("SEQUENCE", "une offre datee plus de 31 j apres le compromis", i_offre_loin_apres_compromis, "a juger"),
    ("SEQUENCE", "une offre refusee PAR NOUS dans un dossier vendu", i_refus_de_nous_dans_un_dossier_vendu, "a juger"),
    ("DOSSIER", "deux offres acceptees dans un dossier", i_deux_offres_acceptees, "a juger"),
    ("TRANSACTION", "etat d'une offre contraire a son journal Hektor", i_etat_contre_journal, "a juger"),
    ("TRANSACTION", "meme numero Hektor sur deux lignes", i_doublon_de_numero, "dur"),
    ("TRANSACTION", "transaction du classeur qui double une transaction Hektor", i_copie_du_classeur, "a juger"),
    ("TRANSACTION", "nee dans l'app, jamais numerotee", i_plage_app_sans_numero, "a juger"),
    ("TRANSACTION", "transaction du classeur portant un numero Hektor", i_classeur_avec_numero, "dur"),
    ("TRANSACTION", "sans date de tri (ne rejoint jamais par la sequence)", i_sans_date_de_tri, "constat"),
    ("TRANSACTION", "offre sans etat", i_offre_sans_etat, "constat"),
    ("TRANSACTION", "genre inconnu", i_genre_inconnu, "dur"),
    ("TRANSACTION", "transaction sans bien", i_sans_bien, "dur"),
]


# ═══ LE JEU SEME : un cas fabrique par detecteur ════════════════════════════════
def jeu_seme() -> list[dict]:
    b, n = 99999990, 99000000          # des numeros qu'aucune ligne ne porte
    def L(i, ch, genre, etat, d, bien=b, acq="1", num=None, u=None, numero=None, **kw):
        base = {"app_affaire_id": n + i, "app_chaine_id": n + ch, "app_dossier_uuid": u or "seme-%d" % ch,
                "app_dossier_numero": numero or "D2026-9%03d" % ch, "hektor_annonce_id": bien, "kind": genre,
                "state": etat, "date": d, "hektor_affaire_id": num if num is not None else str(n + i),
                "present_in_hektor": True, "transaction_origine": None,
                "acquereurs_json": [{"id": acq}], "hektor_acquereur_id": None, "numero_mandat": "1",
                "hektor_mandat_id": 1, "montant": 1, "propositions_json": None,
                "last_seen_at": "2099-01-01"}
        base.update(kw)
        return base
    s = []
    s += [L(1, 1, "vente", "", "2020-01-01"), L(2, 1, "vente", "", "2020-02-01")]                 # 2 ventes
    s += [L(3, 3, "compromis", "active", "2020-01-01"), L(4, 3, "compromis", "active", "2020-02-01")]
    s += [L(5, 5, "offre", "accepted", "2020-01-01"), L(6, 5, "offre", "accepted", "2020-01-02", bien=b + 1)]
    s += [L(7, 7, "offre", "proposed", "2020-01-01", u="seme-x"), L(8, 8, "offre", "proposed", "2020-01-01", u="seme-x")]
    s += [L(10, 9, "offre", "proposed", "2020-01-01")]                                             # numero != min
    s += [L(11, 11, "offre", "proposed", "2020-01-01", numero="D0000-0001")]
    s += [L(12, 12, "offre", "accepted", "2020-01-01", present_in_hektor=False)]
    s += [L(13, 13, "vente", "", "2020-01-01"), L(14, 13, "offre", "accepted", "2020-06-01"),
          L(15, 13, "compromis", "active", "2020-07-01")]                                         # apres vente + vente < cp
    s += [L(16, 16, "compromis", "active", "2020-01-01"), L(17, 16, "offre", "accepted", "2020-06-01")]
    s += [L(18, 18, "vente", "", "2020-01-01"),
          L(19, 18, "offre", "refused", "2019-06-01",
            propositions_json=[{"type": "proposition", "date": "2019-06-01"}, {"type": "refus", "date": "2026-11-11"}])]
    s += [L(20, 20, "offre", "accepted", "2020-01-01",
            propositions_json=[{"type": "proposition", "date": "2020-01-01"}, {"type": "refus", "date": "2020-02-01"}])]
    s += [L(21, 21, "offre", "proposed", "2020-01-01", num="777"), L(22, 22, "offre", "proposed", "2020-01-01", num="777")]
    s += [L(23, 23, "compromis", "cancelled", "2020-03-03", bien=b + 2),
          L(24, 24, "compromis", "cancelled", "2020-03-03", bien=b + 2, num="", transaction_origine="classeur")]
    s += [L(1000000 - n + 1_000_000, 25, "offre", "proposed", "2020-01-01", num="")]   # plage app sans numero
    s += [L(26, 26, "offre", "proposed", "2020-01-01", transaction_origine="classeur")]
    s += [L(27, 27, "compromis", "cancelled", None)]
    s += [L(28, 28, "offre", "", "2020-01-01")]
    s += [L(29, 29, "location", "", "2020-01-01")]
    s += [L(30, 30, "offre", "proposed", "2020-01-01", bien=None)]
    s += [L(31, 31, "offre", "proposed", "2020-01-01", last_seen_at="2000-01-01")]
    s += [L(32, 32, "offre", "proposed", "2020-01-01", app_dossier_uuid=None)]
    return s


def main() -> int:
    cl = client()
    brutes = lire_registre(cl)
    if len(brutes) < 30000:
        print("⛔ registre lu incomplet (%d lignes) -- pas pu mesurer (code 2)." % len(brutes))
        return 2
    nuit = max(str(l.get("last_seen_at") or "") for l in brutes)[:10]
    reel = [preparer(l) for l in brutes]
    ch_reel = par_chaine(reel)
    ch_seme = par_chaine(reel + [preparer(l) for l in jeu_seme()])

    lignes_csv, temoins_rates = [], []
    print("REGISTRE : %d transactions . %d dossiers . derniere relecture %s" % (len(reel), len(ch_reel), nuit))
    for famille, nom, f, gravite in INVARIANTS + [("LECTURE", "transaction presente non relue la nuit derniere",
                                                    lambda c: i_non_relue_cette_nuit(c, nuit), "a juger")]:
        cas = f(ch_reel)
        cas_seme = f(ch_seme)
        vu = len(cas_seme) - len(cas)
        if vu < 1:
            temoins_rates.append(nom)
        print("  %-12s %-62s %6d   temoin seme vu : %s" % (famille, nom, len(cas), "oui (+%d)" % vu if vu >= 1 else "⛔ NON"))
        for cle, detail in cas:
            lignes_csv.append({"famille": famille, "invariant": nom, "gravite": gravite,
                               "cle": cle, "detail": detail})

    # LES CONSTATS QUI NE SONT PAS DES DEFAUTS, mais qu'on doit savoir
    solitaires = Counter()
    for m in ch_reel.values():
        if len(m) == 1:
            t = m[0]
            nous = any(e.get("type") == "refus" and str(e.get("date") or "") >= NOS_GESTES for e in t["journal"])
            solitaires["%s %s%s%s" % (t["genre"], t["etat"] or "(vide)", " (classeur)" if t["classeur"] else "",
                                      " (refus de nous)" if nous else "")] += 1
    print("DOSSIERS A UNE SEULE TRANSACTION : %d" % sum(solitaires.values()))
    for k, v in solitaires.most_common():
        print("     %-50s %5d" % (k, v))
    multi_acq = sum(1 for m in ch_reel.values()
                    if len(set().union(*[t["acqs"] for t in m])) >= 2)
    vendus = [m for m in ch_reel.values() if any(t["genre"] == "vente" and not t["effacee"] for t in m)]
    print("DOSSIERS A DEUX ACQUEREURS OU PLUS : %d (normal : le contact change dans la chaine)" % multi_acq)
    print("DOSSIERS VENDUS SANS OFFRE : %d . SANS COMPROMIS : %d" % (
        sum(1 for m in vendus if not any(t["genre"] == "offre" for t in m)),
        sum(1 for m in vendus if not any(t["genre"] == "compromis" for t in m))))

    with SORTIE.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["famille", "invariant", "gravite", "cle", "detail"])
        w.writeheader()
        w.writerows(lignes_csv)
    print("CSV : %s (%d lignes)" % (SORTIE, len(lignes_csv)))
    if temoins_rates:
        print("⛔ TEMOINS SEMES NON VUS : %s -- ces zeros ne prouvent rien (code 2)." % temoins_rates)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
