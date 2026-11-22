"""L'OUTIL DE COUPE CORRIGE (20/11/2026, soir) -- UNE PIECE NE SE DONNE QUE PAR UNE PREUVE INTERNE.

LECTURE SEULE. Ce module n'ecrit rien : il dit a QUELLE ligne du classeur une piece (offre, compromis, vente)
appartient, ou il S'ABSTIENT.

LE DEFAUT QU'IL CORRIGE (trouve le 20/11 au soir, en relisant ses 23 questions)
  Le code qui fabriquait les coupes (temps6_les_803_lignes..., bloc « part / dispute / nom seul ») :
    1. donnait une piece au NOM qu'elle porte quand aucune ligne ne la designait (« [nom seul] ») -- or Hektor recopie
       le nom du premier acheteur sur TOUS les compromis du bien : le nom ne vaut rien ;
    2. appelait « par la date » une piece dont la ligne avait sa case REMPLIE (Offre Achat, Compromis...) -- sans
       comparer la date de la piece a celle de la case ;
    3. ne regardait que les lignes du GROUPE, pas les autres lignes du meme bien (la 3e ligne oubliee, FARGE-DEBISE,
       sur le groupe 40).

LA REGLE NEUVE (ses mots du 20/11 au soir : « LA PREUVE INTERNE DECIDE. Quand le prix ET les honoraires d'une piece
designent une offre, c'est regle -- je te suis meme si le nom dit le contraire. Sinon : A PART. Pas de « plutot »,
pas de « probable ». »)
  Une piece va a une ligne SEULEMENT si, parmi TOUTES les lignes du classeur qui portent le meme bien :
    . DATE   sa date tombe AU JOUR EXACT sur la case de son genre (offre -> Offre Achat ; compromis -> Compromis ;
             vente -> Vente Prevue / Fixee / Reglee / Signee) de cette ligne, et d'aucune autre ;   ou
    . PRIX + HONORAIRES   son montant = le prix d'une OFFRE de la ligne (sa case Prix, ou une offre Hektor datee au
             jour exact de sa case Offre Achat) ET ses honoraires (montant - net vendeur) = la Commission TTC de la
             ligne, a 1 EUR pres, et d'aucune autre ligne.
  Le NOM n'entre JAMAIS. Sinon : ABSTENTION -> la piece est mise A PART (seule dans son dossier).
  Une piece CREEE DEPUIS le classeur (C5) appartient a la ligne qui l'a creee : elle ne decide pas, elle suit.

LES CONTRADICTIONS (pour juger une attribution DEJA faite, `juger`) :
  la date tombe au jour exact sur une AUTRE ligne et pas sur la sienne ; le prix + les honoraires sont ceux d'une
  AUTRE ligne et pas les siens ; la piece est datee plus de 15 jours APRES l'annulation de toutes ses lignes ; un
  compromis ou une vente date plus de 2 jours AVANT l'offre de toutes ses lignes.

LES LIGNES DU BIEN : celles que le gel relie a une piece du bien, + celles dont le Mandat est un numero de ce bien
(registre des transactions ou des mandats) et d'aucun autre, + celles dont le numero de dossier (product_ref) est celui
du bien et d'aucun autre, + celles qui portent le meme Lien CRM qu'une ligne du bien.
⚠ LA LIMITE : une ligne du classeur qu'aucun de ces quatre chemins ne relie a un bien n'est pas vue (mesure : voir le
compte rendu).
"""
from __future__ import annotations

import json
import re
import sqlite3
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
CACHE = Path(r"C:\Hektor\chantier_classeur_q6_cache")
BASE = RACINE / "phase2" / "phase2.sqlite"

import sys as _sys  # noqa: E402
_sys.path.insert(0, str(Path(__file__).resolve().parent))
import piece_copie_ou_vraie as PC  # noqa: E402  -- LA fonction unique copie / vraie piece (22/11)

COLS_DATE = {"offre": ["Offre Achat"], "compromis": ["Compromis"],
             "vente": ["Vente Prévue", "Vente Fixée", "Vente Réglée", "Signée"]}
MOIS = {"janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6, "juillet": 7,
        "août": 8, "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12, "decembre": 12}

PROUVEE_DATE = "PROUVEE PAR LA DATE"
PROUVEE_PH = "PROUVEE PAR PRIX + HONORAIRES"
PROPRE_C5 = "CREEE DEPUIS CETTE LIGNE (C5)"
CONTREDITE = "CONTREDITE"
CONFLIT = "CONFLIT DATE / PRIX"
SANS_PREUVE = "SANS PREUVE INTERNE"


def d_sheet(s) -> date | None:
    """Les deux formats du classeur (jj/mm/aaaa et « 20 février21 »)."""
    s = (s or "").strip()
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})$", s)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            return None
    m = re.match(r"(\d{1,2}) ?([a-zéû]+)\.? ?(\d{2})$", s.lower())
    if m and m.group(2) in MOIS:
        try:
            return date(2000 + int(m.group(3)), MOIS[m.group(2)], int(m.group(1)))
        except ValueError:
            return None
    return None


def d_reg(s) -> date | None:
    try:
        d = datetime.strptime((s or "")[:10], "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None
    return d if d.year > 1990 else None


def nombre(x) -> float | None:
    try:
        return float(str(x).replace(" ", "").replace("\u202f", "").replace(",", "."))
    except (TypeError, ValueError):
        return None


class Donnees:
    """La photo du classeur (t6_photo.json), le registre local (lecture seule) et le gel fourni par l'appelant."""

    def __init__(self, gel: list[tuple[str, int]] | None = None):
        P = json.loads((CACHE / "t6_photo.json").read_text(encoding="utf-8"))
        self.entete = P["entete"]
        self.LIG = P["lignes"]
        self.TX = {int(a): v for a, v in P["tx"].items()}
        self.col = {c: k for k, c in enumerate(self.entete)}
        self.gel_l: dict[str, set] = defaultdict(set)
        self.gel_t: dict[int, set] = defaultdict(set)
        for i, a, *_ in (gel if gel is not None else P["gel"]):
            self.gel_l[i].add(int(a))
            self.gel_t[int(a)].add(i)
        con = sqlite3.connect("file:%s?mode=ro" % BASE, uri=True)
        self.REG: dict[int, dict] = {}
        mandats_du_bien: dict[str, set] = defaultdict(set)
        for a, b, k, st, d, m, ps, nv, nm, orig, num in con.execute(
                "select app_affaire_id, hektor_annonce_id, kind, state, date, montant, propositions_json, "
                "prix_net_vendeur, numero_mandat, transaction_origine, hektor_affaire_id from app_affaire_ledger"):
            dd = d_reg(d)
            if k == "offre":
                dd = None                       # la date d'une offre = sa 1re proposition (la colonne date ment)
                try:
                    pp = json.loads(ps) if ps else []
                    props = [x for x in (pp if isinstance(pp, list) else [pp])
                             if isinstance(x, dict) and x.get("type") == "proposition"]
                    if props:
                        dd = d_reg(props[0].get("date"))
                except (TypeError, ValueError):
                    pass
            mm = nombre(m) if m not in (None, "") else None
            nvf = nombre(nv) if nv not in (None, "") else None
            hh = (mm - nvf) if (mm is not None and nvf is not None and nvf > 0) else None
            self.REG[int(a)] = {"bien": str(b), "genre": k, "etat": st, "date": dd, "montant": mm, "hon": hh,
                                # ⭐ 22/11 : la fonction unique, sur le registre lu ICI (avant : la marque de la photo
                                #   du 19/11 -- juste, mesure 190/190 et 0/340, mais muette sur une piece nee apres)
                                "c5": PC.est_copie(a, orig, num)}
            if nm not in (None, ""):
                mandats_du_bien[str(nm).strip()].add(str(b))
        refs_du_bien: dict[str, set] = defaultdict(set)
        for nm, b, nd in con.execute("select numero_mandat, hektor_annonce_id, numero_dossier "
                                     "from app_mandat_register_current where hektor_annonce_id is not null"):
            if nm not in (None, ""):
                mandats_du_bien[str(nm).strip()].add(str(b))
            if nd not in (None, "") and not str(nd).strip().isdigit():
                refs_du_bien[str(nd).strip().upper()].add(str(b))
        con.close()
        self.par_bien: dict[str, list] = defaultdict(list)
        for a, r in self.REG.items():
            self.par_bien[r["bien"]].append(a)
        # les lignes du bien : gel + Mandat (unique) + numero de dossier (unique)
        self.lignes_bien: dict[str, set] = defaultdict(set)
        # ⭐ 22/11 (protocole) : PAR QUOI chaque ligne est rattachee a chaque bien -- note seulement, ne decide rien
        self.rattache_par: dict[tuple, set] = defaultdict(set)
        self.mandats_du_bien, self.refs_du_bien = mandats_du_bien, refs_du_bien
        for i, ts in self.gel_l.items():
            for a in ts:
                if a in self.REG:
                    self.lignes_bien[self.REG[a]["bien"]].add(i)
                    self.rattache_par[(self.REG[a]["bien"], i)].add("gel")
        for i in self.LIG:
            m = self.case(i, "Mandat").strip()
            if m and len(mandats_du_bien.get(m, ())) == 1:
                self.lignes_bien[next(iter(mandats_du_bien[m]))].add(i)
                self.rattache_par[(next(iter(mandats_du_bien[m])), i)].add("mandat")
            ref = self.case(i, "product_ref").strip().upper()
            if ref and not ref.isdigit() and len(refs_du_bien.get(ref, ())) == 1:
                self.lignes_bien[next(iter(refs_du_bien[ref]))].add(i)
                self.rattache_par[(next(iter(refs_du_bien[ref])), i)].add("product_ref")
        # ⭐ LE LIEN CRM (20/11 soir) : deux lignes qui portent le meme lien vers la fiche du CRM parlent du meme bien
        #   (trouve sur POCHELON 6FQO29C8, dont le Mandat n'est connu d'aucun registre). On le propage depuis les
        #   lignes deja rattachees, quand le lien ne mene qu'a UN bien.
        bien_de_ligne: dict[str, set] = defaultdict(set)
        for b, ls in self.lignes_bien.items():
            for i in ls:
                bien_de_ligne[i].add(b)
        biens_du_lien: dict[str, set] = defaultdict(set)
        for i in self.LIG:
            lien = self.case(i, "Lien CRM").strip()
            if lien and bien_de_ligne.get(i):
                biens_du_lien[lien] |= bien_de_ligne[i]
        for i in self.LIG:
            lien = self.case(i, "Lien CRM").strip()
            if lien and len(biens_du_lien.get(lien, ())) == 1:
                self.lignes_bien[next(iter(biens_du_lien[lien]))].add(i)
                self.rattache_par[(next(iter(biens_du_lien[lien])), i)].add("lien_crm")

    def case(self, i: str, colonne: str) -> str:
        r = self.LIG[i]["row"]
        k = self.col[colonne]
        return str(r[k]) if k < len(r) and r[k] is not None else ""

    # ── les indices d'UNE piece sur UNE ligne ──
    def dates_de(self, i: str, genre: str) -> set:
        return {d for d in (d_sheet(self.case(i, c)) for c in COLS_DATE.get(genre, [])) if d}

    def touche_date(self, a: int, i: str) -> bool:
        p = self.REG[a]
        return bool(p["date"]) and p["date"] in self.dates_de(i, p["genre"])

    def offres_de_la_ligne(self, i: str, bien: str) -> set:
        """Le prix de L'OFFRE de la ligne : sa case Prix, ET le montant de chaque offre Hektor du bien dont la date
        tombe AU JOUR EXACT sur sa case Offre Achat (une offre prouvee par la date -- jamais par le nom)."""
        out = set()
        prix = nombre(self.case(i, "Prix"))
        if prix is not None:
            out.add(round(prix))
        d_off = d_sheet(self.case(i, "Offre Achat"))
        if d_off:
            for o in self.par_bien.get(bien, []):
                q = self.REG[o]
                if q["genre"] == "offre" and q["date"] == d_off and q["montant"] is not None:
                    out.add(round(q["montant"]))
        return out

    def touche_ph(self, a: int, i: str) -> bool:
        """LE CRITERE 1 : le prix de la piece = le prix d'une offre de la ligne ET ses honoraires = la commission de la
        ligne (a 1 EUR pres)."""
        p = self.REG[a]
        com = nombre(self.case(i, "Commission TTC"))
        if p["montant"] is None or p["hon"] is None or com is None or abs(p["hon"] - com) > 1:
            return False
        return any(abs(p["montant"] - x) <= 1 for x in self.offres_de_la_ligne(i, p["bien"]))

    def touche_prix(self, a: int, i: str) -> bool:
        p, prix = self.REG[a], nombre(self.case(i, "Prix"))
        return p["montant"] is not None and prix is not None and abs(p["montant"] - prix) <= 1

    def ph_definis(self, a: int, i: str) -> bool:
        return (self.REG[a]["hon"] is not None and bool(self.offres_de_la_ligne(i, self.REG[a]["bien"]))
                and nombre(self.case(i, "Commission TTC")) is not None)

    def contre_dates(self, a: int, lignes: set) -> list[str]:
        """La piece datee apres l'annulation (+15 j) de TOUTES ses lignes, ou (compromis, vente) avant leur offre."""
        p = self.REG[a]
        if not p["date"] or not lignes:
            return []
        out = []
        ann = [d_sheet(self.case(i, "Annulée")) for i in lignes]
        if all(ann) and all((p["date"] - d).days > 15 for d in ann):
            out.append("datee le %s, plus de 15 j apres l'annulation de sa ligne (%s)"
                       % (p["date"], ", ".join(str(d) for d in ann)))
        if p["genre"] in ("compromis", "vente"):
            off = [d_sheet(self.case(i, "Offre Achat")) for i in lignes]
            if all(off) and all((d - p["date"]).days > 2 for d in off):
                out.append("datee le %s, avant l'offre de sa ligne (%s)" % (p["date"], ", ".join(str(d) for d in off)))
        return out

    def lignes_du_bien(self, a: int) -> set:
        return set(self.lignes_bien.get(self.REG[a]["bien"], set()))


def noms_ligne(D: Donnees, i: str) -> set:
    """Les noms de l'acquereur ECRITS DANS LE CLASSEUR -- ils servent a reunir les lignes d'un meme acheteur (les
    jumelles, un couple sur deux lignes), JAMAIS a donner une piece."""
    v = D.LIG.get(i, {})
    if v.get("noms_ab"):
        return set(v["noms_ab"])
    return {m for m in re.findall(r"[A-ZÀ-Ý'\-]{4,}", D.case(i, "Acquéreur")) if m not in ("NAN",)}


def classes_acheteurs(D: Donnees, lignes: set) -> dict:
    """ligne -> representant de sa classe (union des lignes qui partagent un nom d'acquereur)."""
    p = {i: i for i in lignes}

    def t(x):
        while p[x] != x:
            x = p[x]
        return x
    lst = sorted(lignes)
    for k, x in enumerate(lst):
        for y in lst[k + 1:]:
            if noms_ligne(D, x) & noms_ligne(D, y):
                p[t(x)] = t(y)
    return {i: t(i) for i in lignes}


def trancher(D: Donnees, a: int, classes: dict) -> tuple:
    """LE COEUR. `classes` = {classe: lignes}. Rend (classe | None, preuve | raison, conflit: bool).
    Le NOM n'entre jamais. La DATE au jour exact d'abord ; le PRIX + LES HONORAIRES ensuite ; sinon on s'abstient."""
    p = D.REG[a]

    def ont(test, cs=None):
        return {c for c, ls in classes.items() if (cs is None or c in cs) and any(test(a, i) for i in ls)}
    compat = {c for c in classes if not D.contre_dates(a, classes[c])}
    Dc, PHc = ont(D.touche_date), ont(D.touche_ph)
    if len(Dc) == 1:
        c = next(iter(Dc))
        # un prix + honoraires qui designe un acheteur IMPOSSIBLE par les dates (piece datee avant son offre, ou bien
        # apres son annulation) ne contredit rien (FARDELLA, 20/11 : compromis du 28/03, l'offre COSTA est du 30/04)
        if (PHc & compat) and c not in PHc and any(D.ph_definis(a, i) for i in classes[c]):
            PHc = PHc & compat
            return None, "la date designe %s, le prix + les honoraires designent %s" % (
                "/".join(sorted(classes[c])), " ".join("/".join(sorted(classes[x])) for x in sorted(PHc))), True
        return c, PROUVEE_DATE, False
    if len(Dc) > 1:
        sous = PHc & Dc
        if len(sous) == 1:
            return next(iter(sous)), PROUVEE_DATE + " + PRIX + HONORAIRES", False
        if p["genre"] == "offre":
            Pc = ont(D.touche_prix, Dc)
            if len(Pc) == 1:
                return next(iter(Pc)), PROUVEE_DATE + " + PRIX", False
        return None, "sa date tombe sur plusieurs acheteurs (%s)" % " ".join(
            "/".join(sorted(classes[x])) for x in sorted(Dc)), False
    PHc &= compat
    if len(PHc) == 1:
        return next(iter(PHc)), PROUVEE_PH, False
    if len(PHc) > 1:
        return None, "prix + honoraires de plusieurs acheteurs (%s)" % " ".join(
            "/".join(sorted(classes[x])) for x in sorted(PHc)), False
    return None, ("sans date, " if not p["date"] else "date %s sur aucune case, " % p["date"]) + (
        "honoraires inconnus" if p["hon"] is None else "prix %s + honoraires %s : ceux d'aucune ligne"
        % (p["montant"], p["hon"])), False


def _classes_autour(D: Donnees, a: int, lignes: set) -> dict:
    cl = classes_acheteurs(D, lignes)
    out: dict = defaultdict(set)
    for i, c in cl.items():
        out[c].add(i)
    return dict(out)


def juger(D: Donnees, a: int, cible: set, autour: set | None = None) -> tuple[str, str]:
    """Une attribution DEJA faite (la piece a -> les lignes `cible`) : prouvee, contredite, en conflit, ou sans
    preuve. `autour` = les lignes du groupe (ajoutees aux lignes du bien)."""
    if a not in D.REG:
        return SANS_PREUVE, "absente du registre"
    p = D.REG[a]
    if p["c5"]:
        origine = D.gel_t.get(a, set())
        if origine and origine & cible:
            return PROPRE_C5, "creee depuis %s" % ",".join(sorted(origine))
        if origine:
            return CONTREDITE, "creee depuis %s, donnee a %s" % (",".join(sorted(origine)), ",".join(sorted(cible)))
        return SANS_PREUVE, "C5 sans ligne d'origine"
    bien = D.lignes_du_bien(a) | set(autour or ()) | set(cible)
    classes = _classes_autour(D, a, bien)
    ici = {c for c, ls in classes.items() if ls & set(cible)}
    c, quoi, conflit = trancher(D, a, classes)
    if c is not None:
        if c in ici:
            return (PROUVEE_DATE if quoi.startswith(PROUVEE_DATE) else PROUVEE_PH), quoi + (
                " (%s)" % p["date"] if quoi.startswith(PROUVEE_DATE) else "")
        return CONTREDITE, "%s -> %s, pas %s" % (quoi, "/".join(sorted(classes[c])), "/".join(sorted(cible)))
    if conflit:
        return CONFLIT, quoi
    if not any(D.touche_date(a, i) for i in cible):
        contre = D.contre_dates(a, set(cible))
        if contre:
            return CONTREDITE, " ; ".join(contre)
    return SANS_PREUVE, quoi


def decider(D: Donnees, a: int, autour: set | None = None) -> tuple:
    """LE NEUF, pour couper : la piece est confrontee a TOUS les acheteurs du bien (les lignes du groupe `autour` ET
    les lignes du bien hors du groupe -- la 3e ligne oubliee). Rend (lignes de l'acheteur | None, preuve | raison)."""
    if a not in D.REG:
        return None, "absente du registre"
    if D.REG[a]["c5"]:
        origine = D.gel_t.get(a, set())
        return (set(origine), PROPRE_C5) if origine else (None, "C5 sans ligne d'origine")
    classes = _classes_autour(D, a, D.lignes_du_bien(a) | set(autour or ()))
    if not classes:
        return None, "aucune ligne du classeur sur ce bien"
    c, quoi, _conflit = trancher(D, a, classes)
    if c is None:
        return None, quoi
    # dans la classe (un meme acheteur sur plusieurs lignes), on garde les lignes que la preuve touche : deux affaires
    # du meme acheteur (DEBARD) ne se confondent pas ; deux saisies de la meme affaire (les jumelles) restent ensemble
    test = D.touche_date if quoi.startswith(PROUVEE_DATE) else D.touche_ph
    precises = {i for i in classes[c] if test(a, i)}
    return (precises or set(classes[c])), quoi


def prouvee_par_sa_chaine(D: Donnees, a: int, compagnes: set, prouvees: set) -> str | None:
    """Une OFFRE ACCEPTEE sans preuve a elle (sa date tombe a un jour de la case) suit le compromis ACTIF de son
    morceau quand Hektor lui-meme les enchaine : le compromis est prouve, il suit l'offre de 0 a 31 jours (la regle B
    du chainage), et c'est la SEULE offre acceptee du bien."""
    p = D.REG.get(a)
    if not p or p["genre"] != "offre" or p["etat"] not in ("accepted", "acceptee") or not p["date"]:
        return None
    autres_acc = [o for o in D.par_bien[p["bien"]] if o != a and D.REG[o]["genre"] == "offre"
                  and D.REG[o]["etat"] in ("accepted", "acceptee")]
    if autres_acc:
        return None
    for c in compagnes & prouvees:
        q = D.REG.get(c)
        if q and q["genre"] == "compromis" and q["etat"] == "active" and q["date"]                 and 0 <= (q["date"] - p["date"]).days <= 31:
            return "offre acceptee, seule du bien, suivie %d j plus tard par le compromis actif %d (prouve)" % (
                (q["date"] - p["date"]).days, c)
    return None


def neutre(piece: int, morceaux: list) -> bool:
    """LE CRITERE 2 (sa trouvaille du 20/11, regle de la pose) : la place d'une piece ne change AUCUNE etiquette
    quand elle n'est la plus petite transaction d'aucun des morceaux ou elle pourrait aller (et qu'aucun ne la
    tient seule)."""
    for m in morceaux:
        reste = set(m) - {piece}
        if not reste or piece < min(reste):
            return False
    return True


def ancienne_attribution(a: int, des: list, dat: list, cls: dict, noms_tx: set, noms_ligne) -> tuple[str | None, str]:
    """L'ANCIEN (recopie de temps6, pour le temoin) : la ligne qui designe, puis « case remplie », puis LE NOM."""
    cs = {cls[i] for i in (dat or des)}
    if len(cs) == 1:
        return cs.pop(), ("date" if dat else "case vide")
    if cs:
        return None, "disputee"
    cs = {cls[i] for i in cls if noms_tx & noms_ligne(i)}
    if len(cs) == 1:
        return cs.pop(), "nom seul"
    return None, "sans ligne"
