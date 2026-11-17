#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""COMBIEN DE LIENS DU GEL POINTENT LA MAUVAISE TRANSACTION ?       17/11/2026

    .venv\\Scripts\\python.exe -X utf8 phase2\\checks\\audit_liens_du_gel_mauvaise_cible_2026-11-17.py

⛔ LECTURE SEULE. Aucune ecriture, aucun patch.

⭐⭐⭐ CE QUI A DECLENCHE CET AUDIT : un lien FAUX trouve par hasard le 17/11.
  La ligne AYIHPHF5 (compromis du 17/05/2021) est liee a la transaction 14111,
  dont la date est le 06/04/2021 -- alors que la transaction 14109 du MEME BIEN
  porte EXACTEMENT 2021-05-17. L'apparieur a choisi un candidat a 41 jours quand
  il en existait un a 0 jour.
  ⭐ Et c'est la ligne Z3DYDC4X qui decrit le compromis du 06/04/2021 : les deux
    lignes se sont donc echangees leur cible.

⛔ UN LIEN FAUX TROUVE PAR HASARD EST PRESQUE TOUJOURS UNE FAMILLE (lecon 9 :
  « une cause structurelle se balaie dans TOUTE sa famille -- ce que Frederic
  signale est un symptome, jamais le perimetre »). On mesure donc TOUT le gel.

LA METHODE, et elle ne suppose rien :
  pour chaque lien (ligne du classeur -> transaction), on compare LA DATE que le
  classeur donne pour ce role a la date de la transaction pointee. Puis on
  cherche, SUR LE MEME BIEN, s'il existe une transaction DU MEME ROLE dont la
  date colle MIEUX. Si oui, le lien est suspect -- et s'il en existe une a
  ECART ZERO alors que le lien pointe ailleurs, il est FAUX.

⚠ CE QUE CET AUDIT NE FAIT PAS : corriger. Deplacer un lien n'est pas additif, et
  c'est la decision de Frederic.
"""
from __future__ import annotations

import csv
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "monitoring"))
sys.path.insert(0, str(RACINE / "phase2" / "checks"))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import apparier_classeur as ap                                      # noqa: E402
import check_gti_health as cgh                                      # noqa: E402

RAPPORT = RACINE / "notice" / "AUDIT_LIENS_MAUVAISE_CIBLE_2026-11-17.csv"
MOIS = {"janvier": 1, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
        "juillet": 7, "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11,
        "decembre": 12}
#: le role du lien -> la colonne du Sheet qui donne SA date
COLONNE_DU_ROLE = {"offre": "Offre Achat", "compromis": "Compromis",
                   "vente": "Vente Réglée"}


def sans_accent(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def date_du_classeur(v: str):
    t = (v or "").strip()
    if not t:
        return None
    m = re.fullmatch(r"(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})", t)
    if m:
        j, mo, a = (int(x) for x in m.groups())
        a = a + 2000 if a < 100 else a
        try:
            return date(a, mo, j)
        except ValueError:
            return None
    m = re.fullmatch(r"(\d{1,2})\s*([a-z]+)\s*(\d{2,4})", sans_accent(t))
    if m:
        mo = MOIS.get(m.group(2))
        a = int(m.group(3))
        a = a + 2000 if a < 100 else a
        if mo:
            try:
                return date(a, mo, int(m.group(1)))
            except ValueError:
                return None
    return None


def date_de_nous(v):
    t = str(v or "").strip()[:10]
    if not t or t.startswith("0000"):
        return None
    try:
        return date.fromisoformat(t)
    except ValueError:
        return None


def client():
    for f in (RACINE / ".env", RACINE / "backend" / ".env",
              RACINE / "apps" / "hektor-v1" / ".env"):
        if f.exists():
            cgh.load_env_file(f)
    url = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL")
    cle = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not (url and cle):
        raise SystemExit("⛔ pas d'identifiants Supabase.")
    return cgh.SupabaseClient(url, cle, timeout_seconds=30)


def tout_lire(cl, table, select, ordre):
    out, pas, dep = [], 1000, 0
    while True:
        lot = cl.get(table, {"select": select, "order": ordre,
                             "limit": pas, "offset": dep}) or []
        out.extend(lot)
        if len(lot) < pas:
            return out
        dep += pas


def main() -> int:
    ap.load_env_file(RACINE / ".env")
    print("=== LES LIENS DU GEL POINTENT-ILS LA BONNE TRANSACTION ? ===")
    print()
    entetes_bruts, lignes = ap.lire_classeur()
    entetes = [str(c or "").strip() for c in entetes_bruts]
    if len(lignes) < 3000:
        print("⛔ LECTURE RATEE : %d lignes." % len(lignes))
        return 2
    i_id = entetes.index("ID Unique")
    idx = {r: entetes.index(c) for r, c in COLONNE_DU_ROLE.items() if c in entetes}
    #: la date que le classeur donne, par ligne et par role
    au_sheet = {}
    for _rang, l in lignes:
        ident = str(l[i_id] if i_id < len(l) else "").strip()
        if not ident:
            continue
        au_sheet[ident] = {
            r: date_du_classeur(str(l[i] if i < len(l) else ""))
            for r, i in idx.items()}
    print("le Sheet : %d lignes lues" % len(au_sheet))

    cl = client()
    liens = tout_lire(cl, "app_classeur_lien",
                      "id_unique,app_affaire_id,role,confiance,gele_par,ligne_classeur",
                      "ligne_classeur")
    registre = tout_lire(cl, "app_affaire_ledger",
                         "app_affaire_id,kind,state,date,hektor_annonce_id,app_chaine_id",
                         "app_affaire_id")
    par_aff = {r["app_affaire_id"]: r for r in registre}
    par_bien = defaultdict(list)
    for r in registre:
        if r.get("hektor_annonce_id"):
            par_bien[str(r["hektor_annonce_id"])].append(r)
    print("le gel : %d liens . le registre : %d transactions"
          % (len(liens), len(registre)))
    print()

    tri = Counter()
    suspects = []
    for k in liens:
        ident, role = str(k["id_unique"]).strip(), str(k["role"])
        aff = k["app_affaire_id"]
        t = par_aff.get(aff)
        if t is None:
            tri["la transaction a disparu"] += 1
            continue
        d_sheet = (au_sheet.get(ident) or {}).get(role)
        if d_sheet is None:
            tri["le classeur ne donne pas de date pour ce role"] += 1
            continue
        d_nous = date_de_nous(t.get("date"))
        if d_nous is None:
            tri["notre transaction n a pas de date lisible"] += 1
            continue
        ecart = abs((d_sheet - d_nous).days)
        if ecart == 0:
            tri["✅ la date COLLE a l exact"] += 1
            continue
        #: ⭐ existe-t-il, SUR LE MEME BIEN, un meilleur candidat du MEME role ?
        bien = str(t.get("hektor_annonce_id") or "")
        mieux = []
        for autre in par_bien.get(bien, []):
            if autre["app_affaire_id"] == aff or autre.get("kind") != role:
                continue
            da = date_de_nous(autre.get("date"))
            if da is None:
                continue
            e2 = abs((d_sheet - da).days)
            if e2 < ecart:
                mieux.append((e2, autre))
        if not mieux:
            tri["ecart, mais AUCUN meilleur candidat sur le bien"] += 1
            continue
        mieux.sort(key=lambda x: x[0])
        e2, autre = mieux[0]
        #: ⭐⭐⭐ LES DEUX FAMILLES EXPLIQUEES, ET IL FAUT LES ECARTER SINON ON
        #:   CORRIGERAIT DES LIENS JUSTES. Mesure du 17/11 : sur 11 « faux »,
        #:   NEUF l'etaient a tort.
        #:
        #:   ① NOS PROPRES GESTES. La transaction pointee porte une date du
        #:     11-12/11/2026 (heures groupees 19:03-19:30 et 15:26-15:27) : c'est
        #:     le chantier « la date d'une offre refusee EST la date du refus »,
        #:     1 435 offres touchees. Le gel du 29/10 pointait LA BONNE offre ;
        #:     c'est SA DATE qui a change depuis. Le lien est juste.
        #:   ② LA LIGNE A DEJA PLUSIEURS LIENS pour ce role (f1aedc01 en a deux,
        #:     un par offre du bien) : on comparait celui qui colle le moins.
        apres_le_gel = d_nous >= date(2026, 11, 10)
        plusieurs = sum(1 for x in liens
                        if str(x["id_unique"]).strip() == ident
                        and str(x["role"]) == role) > 1
        if apres_le_gel:
            tri["⭐ ECARTE : la date a ete changee par NOS gestes du 11-12/11"] += 1
            continue
        if plusieurs:
            tri["⭐ ECARTE : la ligne porte plusieurs liens de ce role"] += 1
            continue
        gravite = ("⛔ FAUX -- un candidat a ECART ZERO existe" if e2 == 0
                   else "⚠ suspect -- un candidat colle MIEUX")
        tri[gravite] += 1
        suspects.append({
            "id_unique": ident, "role": role, "ligne": k["ligne_classeur"],
            "confiance": k["confiance"], "gele_par": k["gele_par"],
            "date_du_classeur": d_sheet.isoformat(),
            "lien_actuel": aff, "sa_date": d_nous.isoformat(), "son_ecart": ecart,
            "meilleur_candidat": autre["app_affaire_id"],
            "sa_date_a_lui": date_de_nous(autre.get("date")).isoformat(),
            "son_ecart_a_lui": e2, "bien": bien, "gravite": gravite,
            "le_candidat_est_il_libre": "oui" if not any(
                str(x["app_affaire_id"]) == str(autre["app_affaire_id"])
                for x in liens) else "NON, deja lie"})

    print("=== LE TRI DES %d LIENS ===" % len(liens))
    for k, n in tri.most_common():
        print("   %-54s %6d  %5.1f %%" % (k[:54], n, 100.0 * n / len(liens)))
    print("   %-54s %6d" % ("-- total", sum(tri.values())))
    print()
    faux = [s for s in suspects if s["gravite"].startswith("⛔")]
    print("=== ⛔ LES LIENS FAUX (un candidat a ECART ZERO existe) : %d ===" % len(faux))
    for s in sorted(faux, key=lambda s: -s["son_ecart"])[:25]:
        print("   %-10s %-10s classeur %s . lie a %-8s (%s, %+d j) . mieux : %-8s (%s, 0 j) %s"
              % (s["id_unique"], s["role"], s["date_du_classeur"], s["lien_actuel"],
                 s["sa_date"], s["son_ecart"], s["meilleur_candidat"],
                 s["sa_date_a_lui"], s["le_candidat_est_il_libre"]))
    print()
    if faux:
        print("   par CONFIANCE du lien faux :")
        for c, n in Counter(s["confiance"] for s in faux).most_common():
            print("      %-14s %4d" % (c, n))
        print("   par QUI l'a pose :")
        for g, n in Counter(s["gele_par"] for s in faux).most_common():
            print("      %-34s %4d" % (g[:34], n))
        print("   par ROLE :")
        for r, n in Counter(s["role"] for s in faux).most_common():
            print("      %-12s %4d" % (r, n))
        print("   le meilleur candidat est-il LIBRE ?")
        for v, n in Counter(s["le_candidat_est_il_libre"] for s in faux).most_common():
            print("      %-16s %4d" % (v, n))
    print()
    if suspects:
        with RAPPORT.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, delimiter=";", fieldnames=list(suspects[0]))
            w.writeheader()
            w.writerows(sorted(suspects, key=lambda s: (s["gravite"], -s["son_ecart"])))
        print("ecrit : %s" % RAPPORT)
    #: ⛔⛔ LE TEMOIN : le cas connu DOIT etre dans la liste des faux, sinon la
    #:   methode ne sait pas reconnaitre ce qu'on lui a montre.
    print()
    print("=== ⛔⛔ LE TEMOIN DE LA METHODE ===")
    #: ⛔⛔ MON PREMIER TEMOIN EST DEVENU UN PIEGE, ET IL A FAIT UN FAUX ROUGE.
    #:   Il exigeait de retrouver AYIHPHF5 parmi les faux. C'etait juste AVANT la
    #:   correction ; une fois AYIHPHF5 recible, le script sortait en CODE 2 alors
    #:   que tout allait bien. Un faux rouge est aussi grave qu'un faux vert --
    #:   « un essai qui crie tous les jours n'est plus un essai ».
    #: ➡ LE TEMOIN JUSTE ne verifie pas un CAS, il verifie une CAPACITE : la
    #:   methode sait-elle encore MESURER des ecarts et TROUVER des candidats ?
    #:   Si elle ne voit plus rien du tout, c'est elle qui est cassee.
    vus = tri["✅ la date COLLE a l exact"]
    ecarts_vus = sum(n for k, n in tri.items() if "ecart" in k or "ECART" in k
                     or "MIEUX" in k or "ECARTE" in k)
    print("   liens dont la date COLLE a l exact        %6d" % vus)
    print("   liens ou la methode a MESURE un ecart     %6d" % ecarts_vus)
    if vus < 5000 or ecarts_vus < 100:
        print("   ⛔ LA METHODE NE MESURE PLUS RIEN -- le resultat ne vaut rien.")
        return 2
    print("   ✅ la methode voit les deux cotes : elle mesure encore.")
    print()
    print("=== ⭐ CE QUI RESTE, ET IL EST EXPLIQUE ===")
    print("   Les cas « FAUX » restants sont ceux que les deux familles ci-dessus")
    print("   n'ecartent pas. Au 17/11 apres correction il en reste %d, et chacun"
          % len(faux))
    print("   doit etre regarde A LA MAIN avant tout geste : corriger en masse")
    print("   aurait abime NEUF liens justes sur onze.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
