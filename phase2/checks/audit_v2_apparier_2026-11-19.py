# -*- coding: utf-8 -*-
"""AUDIT V2, TEMPS 1 -- MON APPARIEMENT INDEPENDANT. 19/11/2026, session de reprise V2.

    .venv\Scripts\python.exe -X utf8 phase2\checks\audit_v2_photo_2026-11-19.py
    .venv\Scripts\python.exe -X utf8 phase2\checks\audit_v2_apparier_2026-11-19.py

Lit UNIQUEMENT la photo prise par a1_photo.py (Sheet, registre, annonces, mandats,
contacts, MODELO). N'ecrit QUE dans le dossier de travail.

⛔ LES QUATRE REGLES D'INDEPENDANCE (dossier V2, § 3) :
  1. le gel (app_classeur_lien) n'est PAS lu ici -- il n'est meme pas dans la photo ;
  2. aucune valeur posee par nous ne sert de preuve : les colonnes *_app, les notes,
     la repartition reconstituee, le carnet des mandats « classeur », les avis --
     aucune n'est lue (le registre est lu SANS elles, voir a1_photo.py) ;
  3. les 190 transactions transaction_origine='classeur' sont RETIREES des candidats ;
  4. la date d'une offre est sa PREMIERE PROPOSITION ; un refus ou une acceptation
     dates a partir du 11/11/2026 sont NOS gestes et ne prouvent rien.

LES FAMILLES DE PREUVE (toutes venues de Hektor, de MODELO ou de la ligne elle-meme) :
  LIEN    le pont nomme par l'agence : lien d'administration (id=), reference Netty
          (colonne B ou lien CRM prod_ref=) -> numero de dossier -> l'annonce
  MODELO  le numero du Sheet dans MODELO -> sa reference produit -> l'annonce
  MANDAT  le numero du Sheet porte par une transaction ou le registre des mandats
  ACQ     un NOM DE FAMILLE d'acquereur (les prenoms ne comptent pas)
  VEND    un NOM DE FAMILLE de vendeur (mandants de la transaction, de l'annonce)
  DATES   une transaction du BON GENRE au JOUR PRES (la preuve interne)
  PRIX    a 1 % pres (prix, ou prix +/- la commission)
  VILLE   la ville du bien
"""
from __future__ import annotations

import csv
import json
import pickle
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

RACINE = Path(r"C:\Hektor\Projet")
ICI = RACINE / ".tmp" / "audit_v2_2026-11-19"   # la photo prise par audit_v2_photo_2026-11-19.py
SORTIE_CSV = RACINE / "notice" / "AUDIT_INDEPENDANT_V2_MON_APPARIEMENT_2026-11-19.csv"
sys.path.insert(0, str(RACINE / "phase2" / "checks"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ⭐ on n'emprunte que des LECTEURS DE FORME (ils ne decident rien)
from rapport_gel_tous_les_champs import date_du_classeur_tolerante  # noqa: E402
from apparier_v2_socle import somme, MOTS_VIDES  # noqa: E402

NOS_GESTES = date(2026, 11, 11)   # regle 4 : a partir de ce jour, un refus/une acceptation est a nous

# ─────────────────────────────────────────────────────────────────────────────
# OUTILS
# ─────────────────────────────────────────────────────────────────────────────
def sa(t) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", str(t or ""))
                   if unicodedata.category(c) != "Mn")


def norm(t) -> str:
    return sa(t).lower().strip()


VIDES = {norm(m) for m in MOTS_VIDES} | {"mme", "mlle", "mr", "mrs", "m", "melle",
                                          "non", "trouve", "trouvee", "acquereur",
                                          "vendeur", "famille", "gti", "agence",
                                          "immobilier", "particulier", "commune",
                                          "mairie", "ville", "ste", "cie", "notaire",
                                          "maitre", "earl", "gaec", "selarl", "fils",
                                          "freres", "heritiers", "neant"}


def jets(texte):
    """Les mots d'un texte, avec leur forme d'origine (pour la casse)."""
    return [m for m in re.split(r"[^A-Za-z\u00c0-\u024f]+", str(texte or "")) if m]


PRENOMS = set()          # rempli plus bas, par la MESURE sur les contacts


def noms_famille_du_sheet(texte):
    """(noms de famille, fiable?) -- dans le Sheet le NOM est en MAJUSCULES et le
    prenom en casse mixte (« M. DUCHET Cedric »). Quand aucun mot n'est en
    majuscules, on garde tous les mots mais on le DIT (fiable=False).
    ⭐ (banc d'essai 23a2a8e1) « SCI FLORANTIN representee par M. Porcu Daniel Mme
      Desfonds Florence » : les vrais noms y sont en casse mixte. On ajoute donc les
      mots en casse mixte QUI NE SONT PAS DES PRENOMS (mesure sur 357 000 contacts)."""
    mots = [m for m in jets(texte) if len(m) >= 3 and norm(m) not in VIDES]
    maj = {norm(m) for m in mots if m.isupper()}
    if maj:
        mixtes = {norm(m) for m in mots if not m.isupper() and len(m) >= 4
                  and norm(m) not in PRENOMS}
        return maj | mixtes, True
    return {norm(m) for m in mots}, False


def jour(x):
    s = str(x or "").strip()[:10]
    if not s or s.startswith("0000") or s.startswith("1990-01-01"):
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def date_sheet(v):
    d = date_du_classeur_tolerante(v)
    return d if isinstance(d, date) else None


def charge_json(blob):
    if blob in (None, "", b""):
        return None
    if isinstance(blob, (dict, list)):
        return blob
    try:
        return json.loads(blob)
    except Exception:  # noqa: BLE001
        return None


CHAMPS_NOM = ("nom", "raison_sociale", "raisonsociale", "societe", "denomination", "lastname")


def personnes(blob):
    j = charge_json(blob)
    out = []

    def desc(o):
        if isinstance(o, dict):
            if any(k in o for k in CHAMPS_NOM + ("prenom",)):
                out.append(o)
            for v in o.values():
                if isinstance(v, (dict, list)):
                    desc(v)
        elif isinstance(o, list):
            for v in o:
                desc(v)
    desc(j)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# LA PHOTO
# ─────────────────────────────────────────────────────────────────────────────
P = pickle.load(open(ICI / "photo" / "base.pkl", "rb"))
S = json.load(open(ICI / "photo" / "sheet.json", encoding="utf-8"))
E = S["entetes"]
IX = {n: i for i, n in enumerate(E)}


def case(l, n):
    i = IX[n]
    return re.sub(r"\s+", " ", str(l[i])).strip() if i < len(l) else ""


CONTACTS = P["contacts"]

# ⭐ LES PRENOMS, PAR LA MESURE : un mot qui sert au moins 3 fois plus souvent de
#   prenom que de nom dans les 357 000 contacts est un prenom.
_cp, _cn = Counter(), Counter()
for _nom, _prenom, _disp in CONTACTS.values():
    for m in jets(_prenom):
        if len(m) >= 3:
            _cp[norm(m)] += 1
    for m in jets(_nom):
        if len(m) >= 3:
            _cn[norm(m)] += 1
PRENOMS |= {m for m, n in _cp.items() if n >= 5 and n >= 3 * _cn.get(m, 0)}
print("prenoms reconnus par la mesure : %d (temoins : %s)" % (
    len(PRENOMS), ", ".join("%s=%s" % (m, m in PRENOMS) for m in ("florence", "daniel", "desfonds", "porcu", "martin"))))


def noms_personne(p):
    """Les mots du NOM DE FAMILLE d'une personne Hektor (jamais le prenom)."""
    out = set()
    for ch in CHAMPS_NOM:
        if p.get(ch):
            out |= {norm(m) for m in jets(p[ch]) if len(m) >= 3 and norm(m) not in VIDES}
    if not out:
        cid = str(p.get("id") or "").strip()
        c = CONTACTS.get(cid) if cid else None
        if c and c[0]:
            out |= {norm(m) for m in jets(c[0]) if len(m) >= 3 and norm(m) not in VIDES}
    return out


def ids_personne(p):
    v = str(p.get("id") or "").strip()
    return {v} if v and v not in ("0",) else set()


# ── LE REGISTRE, sans les 190 transactions creees depuis le Sheet (regle 3)
TX = {}
C5 = set()
for t in P["ledger"]:
    if t["transaction_origine"] == "classeur":
        C5.add(t["app_affaire_id"])
        continue
    k = t["kind"]
    acq_p = personnes(t["acquereurs_json"]) or personnes(t["acquereur_json"])
    vend_p = personnes(t["mandants_json"])
    # ⭐ la VRAIE date
    vraie = None
    refus_jours = set()
    if k == "offre":
        props = charge_json(t["propositions_json"])
        if isinstance(props, dict):
            props = [props]
        pr, ac = [], []
        for e in props or []:
            if not isinstance(e, dict):
                continue
            d = jour(e.get("date"))
            ty = str(e.get("type") or "").lower()
            if not d:
                continue
            if ty == "proposition":
                pr.append(d)
            elif ty == "accepte" and d < NOS_GESTES:
                ac.append(d)
            elif ty == "refus" and d < NOS_GESTES:
                refus_jours.add(d)
        vraie = min(pr) if pr else (min(ac) if ac else None)
        if vraie is None:
            d = jour(t["date"])
            vraie = d if d and d < NOS_GESTES else None
    else:
        vraie = jour(t["date"])
    TX[t["app_affaire_id"]] = {
        "id": t["app_affaire_id"], "k": k, "etat": t["state"], "annonce": str(t["hektor_annonce_id"] or ""),
        "hektor": t["hektor_affaire_id"], "chaine": t["app_chaine_id"], "dossier": t["app_dossier_numero"],
        "mandat": re.sub(r"\D", "", str(t["numero_mandat"] or "")),
        "date": vraie, "date_acte": jour(t["date_acte"]) if k == "compromis" else None,
        "refus": refus_jours,
        "montant": float(t["montant"]) if t["montant"] not in (None, "") else None,
        "hon": float(t["honoraires_entree"]) if t["honoraires_entree"] not in (None, "") else None,
        "acq": set().union(*[noms_personne(p) for p in acq_p]) if acq_p else set(),
        "acq_ids": set().union(*[ids_personne(p) for p in acq_p]) if acq_p else set(),
        "vend": set().union(*[noms_personne(p) for p in vend_p]) if vend_p else set(),
        "present": t["present_in_hektor"],
    }
print("registre : %d transactions candidates (%d creees depuis le Sheet ecartees)" % (len(TX), len(C5)))
if len(C5) != 190:
    print("⚠ attendu 190 transactions 'classeur', lu %d" % len(C5))

TX_DE_ANNONCE = defaultdict(list)
for t in TX.values():
    if t["annonce"]:
        TX_DE_ANNONCE[t["annonce"]].append(t)

# ── LES ANNONCES (cinq index, unis)
ANN = defaultdict(lambda: {"dossiers": set(), "mandats": set(), "ville": set(), "prix": set(),
                           "mandants": set(), "titre": ""})
DOSSIER_VERS_ANNONCES = defaultdict(set)
MANDAT_VERS_ANNONCES = defaultdict(set)
for tab in ("app_annonces_current", "app_archive_annonce_index_current",
            "app_historical_annonce_index_current", "app_mandat_register_current",
            "app_registre_mandats_current"):
    for a in P[tab]:
        h = str(a["hektor_annonce_id"] or "").strip()
        if not h:
            continue
        e = ANN[h]
        nd = str(a["numero_dossier"] or "").strip().upper()
        if nd:
            e["dossiers"].add(nd)
            DOSSIER_VERS_ANNONCES[nd].add(h)
        nm = re.sub(r"\D", "", str(a["numero_mandat"] or ""))
        if nm:
            e["mandats"].add(nm)
            MANDAT_VERS_ANNONCES[nm].add(h)
        if a["ville"]:
            e["ville"].add(norm(a["ville"]))
        if a["prix"] not in (None, ""):
            try:
                e["prix"].add(float(a["prix"]))
            except (TypeError, ValueError):
                pass
        if a["mandants_texte"]:
            e["mandants"] |= noms_famille_du_sheet(a["mandants_texte"])[0]
        if a["titre_bien"] and not e["titre"]:
            e["titre"] = str(a["titre_bien"])[:60]

# ── LE REGISTRE DES MANDATS (app_mandat) -- ⛔ sans les lignes nees du classeur
MANDATS_RECHERCHE = {}
MODELO_VERS_ANNONCES = defaultdict(set)
for m in P["app_mandat"]:
    if str(m.get("origine") or "").lower().startswith("classeur") or \
       str(m.get("source_app") or "").lower().startswith("classeur"):
        continue
    nm = re.sub(r"\D", "", str(m["numero_mandat"] or ""))
    h = str(m["hektor_annonce_id"] or "").strip()
    # ⛔ BORD (19/11) : 539 mandats de notre registre SONT NES DE MODELO. Les ranger
    #   sous « MANDAT » ferait compter deux fois la meme source : ils vont a MODELO.
    if "modelo" in (str(m.get("origine") or "").lower(), str(m.get("source_app") or "").lower()):
        if nm and h:
            MODELO_VERS_ANNONCES[nm].add(h)
        continue
    if nm and h:
        MANDAT_VERS_ANNONCES[nm].add(h)
        ANN[h]["mandats"].add(nm)
        if m["mandants_texte"]:
            ANN[h]["mandants"] |= noms_famille_du_sheet(m["mandants_texte"])[0]
    ty = norm(m.get("type")) + " " + norm(m.get("type_app"))
    if nm and "recherch" in ty and m["mandants_texte"]:
        MANDATS_RECHERCHE.setdefault(nm, set()).update(noms_famille_du_sheet(m["mandants_texte"])[0])
for t in TX.values():
    if t["mandat"] and t["annonce"]:
        MANDAT_VERS_ANNONCES[t["mandat"]].add(t["annonce"])
        ANN[t["annonce"]]["mandats"].add(t["mandat"])
    if t["annonce"]:
        ANN[t["annonce"]]["mandants"] |= t["vend"]

# ── MODELO : numero de mandat -> references produit -> numero de dossier
MODELO = defaultdict(list)
for m in P["modelo"]:
    nm = re.sub(r"\D", "", str(m.get("mandate_number") or ""))
    if not nm:
        continue
    ref = ""
    j = charge_json(m.get("linked_product_ref"))
    if isinstance(j, dict):
        ref = str(j.get("product_ref") or "").strip().upper()
    elif isinstance(m.get("linked_product_ref"), str) and re.fullmatch(r"V[A-Z]\d+", m["linked_product_ref"].strip().upper()):
        ref = m["linked_product_ref"].strip().upper()
    MODELO[nm].append({"ref": ref, "nom": noms_famille_du_sheet(m.get("contact_full_name"))[0],
                       "debut": jour(m.get("date_start")), "fin": jour(m.get("date_end")),
                       "compromis": jour(m.get("date_of_sales_agreement")),
                       "acte": jour(m.get("date_of_deed")), "deleted": m.get("deleted")})

# ── LA FORCE D'UN NOM : sur combien de BIENS il apparait
FREQ_ACQ = Counter()
FREQ_VEND = Counter()
_vu_a, _vu_v = defaultdict(set), defaultdict(set)
for t in TX.values():
    for n in t["acq"]:
        _vu_a[n].add(t["annonce"])
for h, e in ANN.items():
    for n in e["mandants"]:
        _vu_v[n].add(h)
FREQ_ACQ = {n: len(s) for n, s in _vu_a.items()}
FREQ_VEND = {n: len(s) for n, s in _vu_v.items()}

ACQ_VERS_TX = defaultdict(set)
for t in TX.values():
    for n in t["acq"]:
        ACQ_VERS_TX[n].add(t["id"])
VEND_VERS_ANN = defaultdict(set)
for h, e in ANN.items():
    for n in e["mandants"]:
        VEND_VERS_ANN[n].add(h)
DATE_VERS_TX = defaultdict(set)
for t in TX.values():
    if t["date"]:
        DATE_VERS_TX[(t["k"], t["date"])].add(t["id"])

print("annonces connues : %d . dossiers : %d . mandats : %d . MODELO : %d numeros"
      % (len(ANN), len(DOSSIER_VERS_ANNONCES), len(MANDAT_VERS_ANNONCES), len(MODELO)))


# ─────────────────────────────────────────────────────────────────────────────
# LA LIGNE DU SHEET
# ─────────────────────────────────────────────────────────────────────────────
def lire_ligne(rang, l):
    iu = case(l, "ID Unique")
    mandat = re.sub(r"\D", "", case(l, "Mandat"))
    lien_crm = case(l, "Lien CRM")
    ref = case(l, "product_ref").upper()
    ref = ref if re.fullmatch(r"V[A-Z]\d+", ref) else ""
    netty = ""
    m = re.search(r"prod_ref=(V[A-Z]\d+)", lien_crm, re.I)
    if m:
        netty = m.group(1).upper()
    lien_id = ""
    if re.search(r"(la-boite-immo\.com|gti-immobilier\.fr)/admin", lien_crm, re.I):
        m = re.search(r"[?&]id=(\d+)", lien_crm)
        if m:
            lien_id = m.group(1)
    acq, acq_fiable = noms_famille_du_sheet(case(l, "Acquéreur"))
    vend, vend_fiable = noms_famille_du_sheet(case(l, "Vendeur"))
    d = {
        "offre": date_sheet(case(l, "Offre Achat")),
        "compromis": date_sheet(case(l, "Compromis")),
        "prevue": date_sheet(case(l, "Vente Prévue")),
        "fixee": date_sheet(case(l, "Vente Fixée")),
        "reglee": date_sheet(case(l, "Vente Réglée")),
        "annulee": date_sheet(case(l, "Annulée")),
    }
    return {"rang": rang, "iu": iu, "mandat": mandat, "ref": ref, "netty": netty, "lien_id": lien_id,
            "acq": acq, "acq_fiable": acq_fiable, "acq_txt": case(l, "Acquéreur"),
            "vend": vend, "vend_fiable": vend_fiable, "vend_txt": case(l, "Vendeur"),
            "d": d, "prix": somme(case(l, "Prix")), "com": somme(case(l, "Commission TTC")),
            "ville": norm(case(l, "Ville")), "ville_txt": case(l, "Ville"),
            "etat": case(l, "Etat Actuel"), "nature": case(l, "Nature")}


def noms_voisins(a, b):
    """Deux noms de famille d'au moins 5 lettres qui ne different que d'une faute
    de frappe (STRIPOLLI / STRIPPOLI). Rend la paire, ou None."""
    from difflib import SequenceMatcher
    best = None
    for x in a:
        for y in b:
            if len(x) >= 5 and len(y) >= 5 and x != y:
                q = SequenceMatcher(None, x, y).ratio()
                if q >= 0.85 and (best is None or q > best[0]):
                    best = (q, x, y)
    return (best[1], best[2]) if best else None


def prix_colle(m, p, c):
    if not m or not p:
        return False
    for cible in (p, p + (c or 0), p - (c or 0)):
        if cible and abs(m - cible) <= 0.01 * cible:
            return True
    return False


def ecart(a, b):
    return abs((a - b).days) if a and b else None


def juger_tx(L, t):
    """Ce que la ligne et UNE transaction ont en commun. Rend (score, preuves, designe).

    ⛔⛔ CORRIGE APRES LE PREMIER BANC D'ESSAI (TR42PT5H / 739a0db1) : sur un MEME
      bien, deux acheteurs successifs ont presque le meme prix et les memes
      honoraires. Le prix et les honoraires CONFIRMENT, ils ne DESIGNENT pas.
      Seuls designent : une date du bon genre au jour pres (ou a 3 jours), l'acte
      prevu au jour pres, le refus au jour de l'annulation, un nom d'acquereur.
    ⛔ ET UN ACQUEREUR DIFFERENT EST UN VETO quand les deux cotes portent un nom
      fiable -- sauf date au jour pres, et alors on le DIT (question a poser)."""
    designe = False
    pr = []
    sc = 0
    d = L["d"]
    if t["k"] == "offre":
        cibles = [("offre", d["offre"])]
    elif t["k"] == "compromis":
        cibles = [("compromis", d["compromis"])]
    else:
        cibles = [("fixee", d["fixee"]), ("reglee", d["reglee"])]
    best = None
    for nom_c, dc in cibles:
        e = ecart(dc, t["date"])
        if e is not None and (best is None or e < best[0]):
            best = (e, nom_c)
    jour_exact = False
    if best is not None:
        if best[0] == 0:
            sc += 6
            jour_exact = designe = True
            pr.append("date %s au jour pres" % t["k"])
        elif best[0] <= 3:
            sc += 3
            designe = True
            pr.append("date %s a %d j" % (t["k"], best[0]))
        elif t["k"] == "vente" and best[0] <= 10:
            sc += 2
            designe = True
            pr.append("date vente a %d j" % best[0])
        elif best[0] > 400:
            sc -= 3
            pr.append("date %s a %d j (!)" % (t["k"], best[0]))
    # l'acte prevu du compromis contre la « Vente Prevue » du Sheet
    if t["k"] == "compromis" and t["date_acte"] and d["prevue"] and t["date_acte"] == d["prevue"]:
        sc += 2
        jour_exact = designe = True
        pr.append("acte prevu au jour pres")
    # l'annulation d'une offre refusee AVANT nos gestes
    if t["k"] == "offre" and d["annulee"] and d["annulee"] in t["refus"]:
        sc += 2
        jour_exact = designe = True
        pr.append("refus au jour de l'annulation")
    commun = L["acq"] & t["acq"]
    veto = False
    voisin = noms_voisins(L["acq"], t["acq"]) if not commun else None
    if commun:
        rare = min(FREQ_ACQ.get(n, 99) for n in commun)
        sc += 5 if rare <= 5 else 3
        designe = True
        pr.append("acquereur %s%s" % ("/".join(sorted(commun)), "" if rare <= 5 else " (nom frequent)"))
    elif voisin:
        # ⚠ BASTET / BASSET etaient DEUX personnes (un couple) : la ressemblance est
        #   un indice a examiner, jamais une conclusion. Elle designe faiblement et
        #   elle se DIT.
        sc += 2
        designe = True
        pr.append("NOM VOISIN %s~%s" % voisin)
    elif L["acq"] and t["acq"] and L["acq_fiable"]:
        if jour_exact:
            sc -= 2
            pr.append("ACQUEREUR DIFFERENT malgre la date (%s / %s)"
                      % ("/".join(sorted(L["acq"]))[:30], "/".join(sorted(t["acq"]))[:30]))
        else:
            veto = True
            pr.append("acquereur different (veto)")
    if prix_colle(t["montant"], L["prix"], L["com"]):
        sc += 2
        pr.append("prix")
    if L["com"] and t["hon"] and abs(L["com"] - t["hon"]) <= 1:
        sc += 1
        pr.append("honoraires = commission")
    if veto or not designe:
        return -1, pr
    return sc, pr


def roles_de_la_ligne(L):
    d = L["d"]
    r = set()
    if d["offre"]:
        r.add("offre")
    if d["compromis"]:
        r.add("compromis")
    if d["fixee"] or d["reglee"] or L["etat"].lower().startswith("vente r"):
        r.add("vente")
    return r


def candidats_annonces(L):
    """Toutes les annonces que UNE famille au moins designe, avec la famille."""
    c = defaultdict(set)
    if L["lien_id"]:
        c[L["lien_id"]].add("LIEN")
    for r in {L["ref"], L["netty"]} - {""}:
        for h in DOSSIER_VERS_ANNONCES.get(r, ()):
            c[h].add("LIEN")
    if L["mandat"]:
        for mm in MODELO.get(L["mandat"], ()):
            if mm["ref"]:
                for h in DOSSIER_VERS_ANNONCES.get(mm["ref"], ()):
                    c[h].add("MODELO")
        for h in MODELO_VERS_ANNONCES.get(L["mandat"], ()):
            c[h].add("MODELO")
        for h in MANDAT_VERS_ANNONCES.get(L["mandat"], ()):
            c[h].add("MANDAT")
    for n in L["acq"]:
        if FREQ_ACQ.get(n, 0) <= 40:
            for tid in ACQ_VERS_TX.get(n, ()):
                c[TX[tid]["annonce"]].add("~acq")
    for n in L["vend"]:
        if FREQ_VEND.get(n, 0) <= 40:
            for h in VEND_VERS_ANN.get(n, ()):
                c[h].add("~vend")
    for g, k in (("offre", "offre"), ("compromis", "compromis"), ("fixee", "vente"), ("reglee", "vente")):
        dd = L["d"][g]
        if dd:
            for tid in DATE_VERS_TX.get((k, dd), ()):
                c[TX[tid]["annonce"]].add("~date")
    c.pop("", None)
    return c


def juger_annonce(L, h, fam0, interdites):
    """Sur UNE annonce : la meilleure transaction de chaque genre, et le total."""
    e = ANN.get(h)
    fam = set(f for f in fam0 if not f.startswith("~"))
    if L["mandat"] and e and L["mandat"] in e["mandats"]:
        fam.add("MANDAT")
    if e and L["vend"] and (L["vend"] & e["mandants"]):
        fam.add("VEND")
    if e and L["ville"] and L["ville"] not in ("non trouve",) and \
            any(L["ville"] == v or L["ville"] in v or v in L["ville"] for v in e["ville"] if v):
        fam.add("VILLE")
    choix = {}
    annulee = L["etat"].lower().startswith("annul")
    for t in TX_DE_ANNONCE.get(h, ()):
        if t["id"] in interdites:
            continue
        # ⛔ (banc d'essai M8QJWMBM) une affaire ANNULEE au Sheet n'a pas de vente
        if annulee and t["k"] == "vente":
            continue
        sc, pr = juger_tx(L, t)
        k = t["k"]
        if k not in choix or sc > choix[k][0] or (sc == choix[k][0] and t["id"] < choix[k][2]["id"]):
            choix[k] = (sc, pr, t)
    # on ne garde une transaction que si ELLE porte une preuve propre (score > 0)
    garde = {k: v for k, v in choix.items() if v[0] > 0}
    # ⛔ (banc d'essai SOF45TS3) LA CHRONOLOGIE : une affaire annulee en 2023 ne se
    #   rattache pas, par un nom seul, a un achat de 2018. Quand AUCUNE transaction
    #   gardee ne tombe a la bonne date, celles qui sont a plus de deux ans de TOUTES
    #   les dates de la ligne sont ecartees.
    dates_ligne = [x for x in L["d"].values() if x]
    ancre = any(("au jour pres" in p or "au jour de l'annulation" in p
                 or (p.startswith("date") and "(!)" not in p))
                for v in garde.values() for p in v[1])
    if dates_ligne and not ancre:
        for k in list(garde):
            t = garde[k][2]
            if t["date"] and min(abs((t["date"] - x).days) for x in dates_ligne) > 730:
                del garde[k]
    preuves_tx = set()
    drapeaux = set()
    # ⭐ (banc d'essai GIYHBFP5, T90Q8ZKA) : chez Hektor le contact acquereur CHANGE
    #   souvent DANS la chaine (offre au nom de l'un, compromis et vente au nom de
    #   l'autre). Si UNE transaction gardee porte le nom du Sheet, l'ecart des autres
    #   est une variation interne a Hektor, pas un desaccord : on le note, sans plafond.
    un_nom_colle = any(p.startswith("acquereur ") and "different" not in p
                       for v in garde.values() for p in v[1])
    for sc, pr, t in garde.values():
        for p in pr:
            if "au jour pres" in p or "au jour de l'annulation" in p:
                preuves_tx.add("DATES")
            elif p.startswith("acquereur") and "different" not in p:
                preuves_tx.add("ACQ")
            elif p == "prix":
                preuves_tx.add("PRIX")
            elif p.startswith("date") and "(!)" not in p:
                preuves_tx.add("dates~")
            if p.startswith("ACQUEREUR DIFFERENT"):
                drapeaux.add("ACQ_VARIE_DANS_LA_CHAINE" if un_nom_colle else "ACQ_DIFFERENT")
            if p.startswith("NOM VOISIN"):
                drapeaux.add("NOM_VOISIN")
                preuves_tx.add("acq~")
            if "(nom frequent)" in p:
                preuves_tx.add("acq_frequent")
            if "(!)" in p:
                drapeaux.add("DATE_ELOIGNEE")
    fam |= {p for p in preuves_tx if p.isupper()}
    total = sum(v[0] for v in garde.values())
    poids = {"LIEN": 8, "MODELO": 4, "MANDAT": 3, "VEND": 3, "VILLE": 1}
    total += sum(poids.get(f, 0) for f in fam)
    return {"annonce": h, "fam": fam, "garde": garde, "total": total,
            "dates_proches": "dates~" in preuves_tx, "drapeaux": drapeaux}


def force_du_bien(f):
    """Le pont vers le BIEN : fort, moyen ou faible."""
    if "LIEN" in f or ("MODELO" in f and "VEND" in f):
        return 2
    if ("MANDAT" in f and "VEND" in f) or ("MODELO" in f and "MANDAT" in f):
        return 1
    return 0


def force_de_l_affaire(r):
    """La preuve que CES transactions sont l'affaire de la ligne."""
    f = r["fam"]
    preuves = [x for v in r["garde"].values() for x in v[1]]
    acq_rare = any(x.startswith("acquereur ") and "(nom frequent)" not in x
                   and "different" not in x for x in preuves)
    gros = "ACQ" in f and not acq_rare        # seuls des noms frequents
    if "DATES" in f and "ACQ" in f:
        return 3
    if "DATES" in f or ("ACQ" in f and not gros):
        return 2
    if "ACQ" in f or r.get("dates_proches") or "NOM_VOISIN" in r.get("drapeaux", ()):
        return 1
    return 0


def certitude(r, L):
    if r is None:
        return "AUCUNE"
    f = r["fam"]
    b = force_du_bien(f)
    if not r["garde"]:
        return {2: "CERTAINE", 1: "SOLIDE"}.get(b, "FAIBLE")   # le BIEN seul
    a = force_de_l_affaire(r)
    # ⛔ un acquereur different, meme a la bonne date, ne fait jamais une certitude
    plafond = "ACQ_DIFFERENT" in r.get("drapeaux", ())
    if a == 3 or (a == 2 and b >= 1):
        return "SOLIDE" if plafond else "CERTAINE"
    if a == 2 or (a == 1 and b >= 1):
        return "SOLIDE"
    return "FAIBLE"


def apparier(L, interdites=frozenset()):
    cands = candidats_annonces(L)
    res = []
    for h, f0 in cands.items():
        r = juger_annonce(L, h, f0, interdites)
        if r["total"] > 0:
            res.append(r)
    # ⭐ BORD (19/11) : sans le numero d'annonce en dernier departage, deux biens a
    #   egalite se classaient selon l'ordre de parcours de Python (hachage aleatoire)
    #   -- le second candidat changeait d'une execution a l'autre. Rejouable a l'octet.
    res.sort(key=lambda r: (-r["total"], -len(r["fam"]), r["annonce"]))
    return res


# ─────────────────────────────────────────────────────────────────────────────
# LE TOUR
# ─────────────────────────────────────────────────────────────────────────────
LIGNES = [lire_ligne(r, l) for r, l in S["lignes"]]
LIGNES = [L for L in LIGNES if L["iu"]]
print("lignes du Sheet : %d (avec un ID Unique)" % len(LIGNES))

RES = {}
for L in LIGNES:
    RES[L["iu"]] = apparier(L)

# ── L'EXCLUSIVITE : une transaction a une seule ligne. On sert d'abord la ligne
#    dont la preuve est la plus forte (certitude, puis score), et chaque ligne
#    suivante est REJUGEE sans les transactions deja prises. Les pertes sont
#    ECRITES (conflits), jamais tues.
ORDRE_CERT = {"CERTAINE": 4, "SOLIDE": 3, "FAIBLE": 2, "AUCUNE": 1}
LIGNE_DE = {L["iu"]: L for L in LIGNES}


def force(iu):
    r = RES[iu][0] if RES[iu] else None
    return (ORDRE_CERT[certitude(r, LIGNE_DE[iu])], r["total"] if r else -999)


# ⛔⛔ (banc d'essai M8QJWMBM) LE CONFLIT SE TRANCHE SUR LA TRANSACTION, pas sur la
#   ligne : une vente designee AU JOUR PRES par une ligne bat la meme vente designee
#   par un NOM par une autre ligne. On itere : chaque transaction disputee va a la
#   ligne dont la preuve SUR CETTE TRANSACTION est la plus forte (puis la ligne la
#   plus complete) ; les perdantes sont REJUGEES sans elle.
exclues = defaultdict(set)
choix_courant = {L["iu"]: (RES[L["iu"]][0] if RES[L["iu"]] else None) for L in LIGNES}
conflits = defaultdict(list)
for tour in range(8):
    reclam = defaultdict(list)
    for iu, r in choix_courant.items():
        if r:
            for k, (sc, pr, t) in r["garde"].items():
                reclam[t["id"]].append((sc, force(iu), len(r["garde"]), iu))
    a_rejuger = set()
    for tid, cl in reclam.items():
        if len(cl) > 1:
            cl.sort(reverse=True)
            gagnant = cl[0][3]
            for c in cl[1:]:
                exclues[c[3]].add(tid)
                conflits[c[3]].append((tid, gagnant))
                a_rejuger.add(c[3])
    print("  tour %d : %d transactions disputees, %d lignes rejugees"
          % (tour + 1, sum(1 for c in reclam.values() if len(c) > 1), len(a_rejuger)))
    if not a_rejuger:
        break
    for iu in a_rejuger:
        r = apparier(LIGNE_DE[iu], frozenset(exclues[iu]))
        choix_courant[iu] = r[0] if r else None
        RES[iu] = r

# ⭐ CONSOLIDATION : une ligne perdante a pu exclure une transaction que son
#   gagnant a ensuite LACHEE (il a lui-meme ete rejuge ailleurs). On rejuge les
#   perdantes contre ce qui est REELLEMENT pris aujourd'hui, et on verifie qu'il
#   ne reste aucune transaction a deux lignes.
prises = {}
for iu, r in choix_courant.items():
    for k, (sc, pr, t) in (r["garde"].items() if r else []):
        prises[t["id"]] = iu
rattrapes = 0
for iu in list(conflits):
    autres = frozenset(tid for tid, o in prises.items() if o != iu)
    r = apparier(LIGNE_DE[iu], autres)
    neuf = r[0] if r else None
    ancien = choix_courant[iu]
    if neuf and (not ancien or neuf["total"] > ancien["total"]):
        for k, (sc, pr, t) in (ancien["garde"].items() if ancien else []):
            prises.pop(t["id"], None)
        for k, (sc, pr, t) in neuf["garde"].items():
            prises[t["id"]] = iu
        choix_courant[iu] = neuf
        RES[iu] = r
        rattrapes += 1
double = Counter(t["id"] for r in choix_courant.values() if r for (sc, pr, t) in r["garde"].values())
print("  consolidation : %d lignes ameliorees . transactions a deux lignes : %d"
      % (rattrapes, sum(1 for v in double.values() if v > 1)))
if any(v > 1 for v in double.values()):
    raise SystemExit("ARRET : l'exclusivite n'est pas tenue")

choisi = {}
for iu, r in choix_courant.items():
    if r:
        choisi[iu] = dict(r)
        choisi[iu]["second"] = RES[iu][1] if RES[iu] and len(RES[iu]) > 1 else None
    else:
        choisi[iu] = None

# ─────────────────────────────────────────────────────────────────────────────
# L'ECRITURE
# ─────────────────────────────────────────────────────────────────────────────
compte = Counter()
lignes_csv = []
for L in LIGNES:
    iu = L["iu"]
    r = choisi.get(iu)
    cert = certitude(r, L)
    if r and not r["garde"]:
        cert_aff = cert + "/BIEN_SANS_TRANSACTION"
    else:
        cert_aff = cert
    compte[cert_aff] += 1
    tx = {k: (v[2] if r else None) for k, v in (r["garde"].items() if r else [])}
    dossiers = sorted({str(t["dossier"]) for t in tx.values() if t and t["dossier"]})
    sec = r.get("second") if r else None
    lignes_csv.append({
        "id_unique": iu, "rang": L["rang"], "etat": L["etat"], "mandat": L["mandat"],
        "acquereur": L["acq_txt"][:60], "vendeur": L["vend_txt"][:60], "ville": L["ville_txt"][:40],
        "prix": L["prix"] or "", "commission": L["com"] or "",
        "offre_sheet": L["d"]["offre"] or "", "compromis_sheet": L["d"]["compromis"] or "",
        "vente_sheet": L["d"]["fixee"] or L["d"]["reglee"] or "", "annulee_sheet": L["d"]["annulee"] or "",
        "annonce": r["annonce"] if r else "", "dossier": " ".join(dossiers),
        "offre": tx.get("offre", {}) and tx["offre"]["id"] if tx.get("offre") else "",
        "compromis": tx["compromis"]["id"] if tx.get("compromis") else "",
        "vente": tx["vente"]["id"] if tx.get("vente") else "",
        "familles": " ".join(sorted(r["fam"])) if r else "",
        "n_familles": len(r["fam"]) if r else 0,
        "certitude": cert_aff, "score": r["total"] if r else 0,
        "drapeaux": " ".join(sorted(r.get("drapeaux", ()))) if r else "",
        "preuves": " | ".join("%s: %s" % (k, ", ".join(v[1])) for k, v in sorted((r["garde"] if r else {}).items())),
        "second_annonce": sec["annonce"] if sec else "", "second_score": sec["total"] if sec else "",
        "conflits": " ".join("%s->%s" % (a, b) for a, b in conflits.get(iu, [])),
        "roles_sheet": " ".join(sorted(roles_de_la_ligne(L))),
    })

with open(SORTIE_CSV, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(lignes_csv[0].keys()), delimiter=";")
    w.writeheader()
    w.writerows(lignes_csv)
print("ecrit : %d lignes" % len(lignes_csv))
for k, v in sorted(compte.items(), key=lambda x: -x[1]):
    print("  %-34s %5d" % (k, v))
