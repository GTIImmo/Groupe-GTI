#!/usr/bin/env python
"""LE DETECTEUR DES CICATRICES DU LOT DU CLASSEUR -- chantier classeur, 22/11/2026 soir (reponses 21 quater, § 3).

SON MOT : « CES DEUX COPIES SONT PASSEES A TRAVERS LE FILET DU 18/11, ET IL FAUT LE REPARER. Le detecteur ecrit le 18/11
  cherchait « une ligne posee sur une chaine qui en portait DEJA une ». [...] mes deux copies ont CREE LEUR PROPRE CHAINE
  [...] AJOUTE AU LOT DU CLASSEUR un detecteur qui attrape aussi cette forme -- « une copie SEULE DANS SA PROPRE CHAINE,
  sur un bien dont une de nos operations a touche une offre ». Et fais-le CRIER, pas corriger tout seul. »

LA CAUSE (son § 2, mesuree) : nos gestes de masse du 11-12/11 ont deplace la colonne `date` des offres touchees (chez
Hektor, `date` porte le DERNIER mouvement) ; le 16/11 le lot ne retrouve plus l'offre A SA DATE, croit qu'elle manque, et
en pose une SECONDE. Le remede des lecteurs existe deja en base : app_dossier_jour_date_transaction() (la date du journal
de l'offre). ⛔ ON NE CORRIGE PAS LA DONNEE (son § 5) : ce detecteur LIT, il n'ecrit rien, nulle part.

CE QU'IL REGARDE, pour chaque copie (ou chaque ligne qu'un lot s'apprete a poser) :
  NOS GESTES        les travaux change_hektor_offre_status termines, sans auteur humain (nos campagnes), plus la cascade
                    automatique d'un geste humain -- la meme definition que l'inventaire du temps 1 (19/11)
  LA JUMELLE        une VRAIE piece du meme bien, du meme genre, dont la VRAIE date (le journal, par la fonction de la
                    base -- aucune regle recopiee ici) est la date de la copie : c'est la meme transaction, posee deux fois
  ⛔ CICATRICE      la jumelle porte une colonne `date` DEPLACEE (brute <> vraie) ET un de nos gestes l'a touchee : la
                    cause du 18/11 et du 21 quater, nommee
  FORME 18/11       la copie est sur une chaine qui porte deja une vraie piece du meme genre (le filet du 18/11)
  FORME 21 QUATER   la copie est SEULE dans sa propre chaine, sur un bien dont un de nos gestes a touche une offre (son
                    motif, mot pour mot)

USAGE :
  python -u phase2/checks/classeur_detecteur_cicatrices.py            les copies en base ET les 5 retirees le 18/11 (leur
                                                                     sauvegarde datee : le TEMOIN POSITIF)
  depuis le lot : import classeur_detecteur_cicatrices as DC ; DC.crier_avant_de_poser(...)  (il refuse de generer)
CODES : 0 rien ne crie . 1 au moins une CICATRICE, ou une ligne d'une des deux formes (nommees) . 2 pas pu lire
⚠ Il lui faut psycopg2 (le python du systeme) : la vraie date est calculee PAR LA BASE. Une lecture ratee n'est jamais
  un vert : sans base, il rend 2.
"""
from __future__ import annotations

import csv
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
SORTIE = RACINE / "notice" / ("CLASSEUR_DETECTEUR_CICATRICES_%s.csv" % date.today().isoformat())
SAUVEGARDE_18_11 = "app_affaire_ledger_avant_doublons_classeur_20261118"

NOS_GESTES_SQL = """
select (payload_json->>'app_affaire_id')::bigint, coalesce(payload_json->>'origine', payload_json->>'source', '?'),
       to_char(created_at at time zone 'Europe/Paris', 'DD/MM/YYYY HH24:MI')
  from public.app_console_job
 where job_type = 'change_hektor_offre_status' and status = 'done' and payload_json ? 'app_affaire_id'
   and (requested_by is null
        or coalesce(payload_json->>'origine', payload_json->>'source') = 'cascade_annulation_compromis')
 order by created_at"""

VRAIES_SQL = """
select l.app_affaire_id, l.kind, coalesce(l.state, ''), left(coalesce(l.date, ''), 10),
       public.app_dossier_jour_date_transaction(l.kind, l.date, l.propositions_json, l.app_affaire_id),
       l.hektor_annonce_id, l.app_chaine_id
  from public.app_affaire_ledger l
 where coalesce(l.transaction_origine, '') <> 'classeur' and l.hektor_annonce_id = any(%s)"""


def dire(s: str = "") -> None:
    print(s, flush=True)


def connexion():
    """La lecture seule du projet (REPEATABLE READ, READ ONLY) -- jamais une ecriture."""
    import sauvegarde_datee_classeur as S
    return S.connexion()


def lire_contexte(cu, biens: set[int]) -> dict:
    """Nos gestes, et les vraies pieces des biens regardes avec leur VRAIE date (calculee par la base)."""
    cu.execute(NOS_GESTES_SQL)
    gestes = defaultdict(list)
    for a, o, q in cu.fetchall():
        gestes[int(a)].append("%s %s" % (o, q))
    cu.execute(VRAIES_SQL, (sorted(biens),))
    vraies = defaultdict(list)
    for a, k, s, brute, vraie, b, ch in cu.fetchall():
        vraies[int(b)].append({"id": int(a), "kind": k, "state": s, "brute": brute, "vraie": vraie or "",
                               "chaine": ch, "gestes": gestes.get(int(a), [])})
    cu.execute("select app_chaine_id, count(*) from public.app_affaire_ledger where app_chaine_id is not null "
               "group by 1")
    taille = {int(c): int(n) for c, n in cu.fetchall()}
    return {"gestes": gestes, "vraies": vraies, "taille": taille}


def juger(c: dict, ctx: dict) -> dict:
    """Une copie (ou une ligne a poser) : c = {kind, date (AAAA-MM-JJ), bien, chaine (ou None), copie (id ou None)}.
    Rend ses signaux -- et ne decide rien."""
    vr = ctx["vraies"].get(int(c["bien"]), [])
    jum = [v for v in vr if v["kind"] == c["kind"] and v["vraie"] and v["vraie"] == c["date"]]
    cic = [v for v in jum if v["brute"] != v["vraie"] and v["gestes"]]
    touchees = [v for v in vr if v["kind"] == "offre" and v["gestes"]]
    forme_18 = c.get("chaine") is not None and any(v["chaine"] == c["chaine"] and v["kind"] == c["kind"] for v in vr)
    seule = c.get("chaine") is not None and c.get("seule", ctx["taille"].get(int(c["chaine"]), 0) <= 1)
    forme_21 = bool(seule and touchees)
    if cic:
        verdict = "CICATRICE"
    elif jum:
        verdict = "JUMELLE_SANS_CICATRICE"
    elif forme_21 or forme_18:
        verdict = "FORME_SANS_JUMELLE"
    elif touchees:
        verdict = "BIEN_TOUCHE_SANS_JUMELLE"
    else:
        verdict = "RIEN"
    return {"verdict": verdict, "jumelles": jum, "cicatrices": cic, "touchees": touchees, "forme_18_11": forme_18,
            "forme_21_quater": forme_21, "seule": bool(seule)}


def decrire(v: dict) -> str:
    return "%d %s %s brute %s vraie %s chaine %s%s" % (v["id"], v["kind"], v["state"], v["brute"] or "-",
                                                     v["vraie"] or "-", v["chaine"],
                                                     (" -- NOS GESTES : %s" % " + ".join(v["gestes"])) if v["gestes"]
                                                     else "")


def crier_avant_de_poser(pretes: list[dict], entendu: set[str]) -> int:
    """⛔ LE FILET DU LOT, AVANT DE GENERER LE PATCH : chaque ligne a poser qui a une JUMELLE (meme bien, meme genre, meme
    VRAIE date), ou qui tombe sur un bien dont un de nos gestes a touche une offre, est NOMMEE et le lot S'ARRETE. Il ne
    corrige rien : l'humain declare la ligne hors jeu (app_classeur_ligne_exclue, avec son pourquoi), ou la relance avec
    --entendu=ID,ID apres l'avoir regardee. Rend 0 (rien ne crie, ou tout est entendu), 3 (ca crie), 2 (pas pu lire).
    pretes : [{id_unique, role/kind, date (AAAA-MM-JJ), annonce}] -- la chaine d'une ligne a poser n'existe pas encore :
    la forme 21 quater (seule dans sa chaine) ne se voit qu'apres la nuit, d'ou le controle sur le bien."""
    if not pretes:
        return 0
    try:
        cn, cu = connexion()
    except Exception as e:  # noqa: BLE001
        dire("⛔ LE FILET DES CICATRICES n'a pas pu lire la base (%s) -- rien n'est genere (code 2)."
             % str(e).splitlines()[0][:160])
        dire("   ⚠ il lui faut psycopg2 : lancer le lot avec le python du systeme (python -X utf8 ...)")
        return 2
    try:
        ctx = lire_contexte(cu, {int(p["annonce"]) for p in pretes})
        cn.rollback()
    finally:
        cn.close()
    crient = []
    for p in pretes:
        j = juger({"kind": p["kind"], "date": str(p["date"])[:10], "bien": p["annonce"], "chaine": None}, ctx)
        if j["verdict"] != "RIEN":
            crient.append((p, j))
    dire("=== ⛔ LE FILET DES CICATRICES (21 quater) : %d ligne(s) sur %d crient ===" % (len(crient), len(pretes)))
    for p, j in crient:
        dire("   %s %-10s %s du %s, bien %s : %s" % ("⛔" if j["verdict"] == "CICATRICE" else "⚠", p["id_unique"],
                                                   p["kind"], str(p["date"])[:10], p["annonce"], j["verdict"]))
        for v in j["jumelles"]:
            dire("        sa JUMELLE (meme genre, meme VRAIE date) : %s" % decrire(v))
        for v in j["touchees"]:
            if v not in j["jumelles"]:
                dire("        offre du bien touchee par NOS GESTES : %s" % decrire(v))
    reste = [p for p, _j in crient if p["id_unique"] not in entendu]
    if crient and not reste:
        dire("   toutes ENTENDUES (--entendu) : le lot continue -- c'est une decision humaine, nommee ici")
        return 0
    if reste:
        dire("   ⛔ RIEN N'EST GENERE. Pour chaque ligne : la declarer hors jeu (app_classeur_ligne_exclue, son pourquoi),")
        dire("      ou relancer avec --entendu=%s apres l'avoir regardee." % ",".join(p["id_unique"] for p in reste))
        return 3
    return 0


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        cn, cu = connexion()
    except Exception as e:  # noqa: BLE001
        dire("⛔ la base n'a pas pu etre lue (%s) -- code 2" % str(e).splitlines()[0][:160])
        return 2
    try:
        copies = []
        for source, table in (("en base", "public.app_affaire_ledger"), ("retiree le 18/11", "public." + SAUVEGARDE_18_11)):
            cu.execute("select app_affaire_id, kind, coalesce(state, ''), left(coalesce(date, ''), 10), hektor_annonce_id, "
                       "app_chaine_id, payload_json->>'classeur_id_unique', payload_json->>'classeur_lot' from %s "
                       "where transaction_origine = 'classeur' order by 1" % table)
            for a, k, s, d, b, ch, iu, lot in cu.fetchall():
                copies.append({"source": source, "copie": int(a), "kind": k, "state": s, "date": d, "bien": int(b),
                               "chaine": ch, "id_unique": iu, "lot": lot})
        ctx = lire_contexte(cu, {c["bien"] for c in copies})
        cn.rollback()
    finally:
        cn.close()
    lignes, cpt = [], defaultdict(int)
    for c in copies:
        if c["source"] != "en base":
            # retiree : sa chaine d'alors porte aujourd'hui les autres pieces, elle-meme en plus
            c["seule"] = ctx["taille"].get(int(c["chaine"]), 0) == 0
        j = juger(c, ctx)
        cpt[(c["source"], j["verdict"])] += 1
        cpt[(c["source"], "forme 18/11")] += j["forme_18_11"]
        cpt[(c["source"], "forme 21 quater")] += j["forme_21_quater"]
        cpt[(c["source"], "seule dans sa chaine")] += j["seule"]
        lignes.append((c, j))
    for source in ("en base", "retiree le 18/11"):
        n = sum(1 for c, _j in lignes if c["source"] == source)
        dire("LES COPIES %s : %d" % (source.upper(), n))
        for k in ("CICATRICE", "JUMELLE_SANS_CICATRICE", "FORME_SANS_JUMELLE", "BIEN_TOUCHE_SANS_JUMELLE", "RIEN",
                  "seule dans sa chaine", "forme 18/11", "forme 21 quater"):
            dire("   %-28s %4d" % (k, cpt[(source, k)]))
        for c, j in lignes:
            if c["source"] == source and (j["verdict"] == "CICATRICE" or j["forme_18_11"] or j["forme_21_quater"]):
                dire("   %s copie %d %-10s %s/%s du %s, bien %s, chaine %s%s : %s%s%s" % (
                    "⛔" if j["verdict"] == "CICATRICE" else "⚠", c["copie"], c["id_unique"], c["kind"], c["state"],
                    c["date"], c["bien"], c["chaine"], " (SEULE)" if j["seule"] else "", j["verdict"],
                    " . forme 18/11" if j["forme_18_11"] else "", " . forme 21 quater" if j["forme_21_quater"] else ""))
                for v in j["jumelles"]:
                    dire("        jumelle : %s" % decrire(v))
    with SORTIE.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["source", "copie", "id_unique", "lot", "genre", "etat", "date_de_la_copie", "bien", "chaine",
                    "seule_dans_sa_chaine", "verdict", "forme_18_11", "forme_21_quater", "jumelles",
                    "offres_du_bien_touchees_par_nos_gestes"])
        for c, j in lignes:
            w.writerow([c["source"], c["copie"], c["id_unique"], c["lot"], c["kind"], c["state"], c["date"], c["bien"],
                        c["chaine"], "oui" if j["seule"] else "", j["verdict"], "oui" if j["forme_18_11"] else "",
                        "oui" if j["forme_21_quater"] else "", " | ".join(decrire(v) for v in j["jumelles"]),
                        " | ".join(decrire(v) for v in j["touchees"])])
    crie = [1 for c, j in lignes if c["source"] == "en base" and (j["verdict"] == "CICATRICE" or j["forme_18_11"]
                                                                    or j["forme_21_quater"])]
    temoin = sum(1 for c, j in lignes if c["source"] != "en base" and j["verdict"] == "CICATRICE")
    dire("TEMOIN POSITIF : %d des %d copies retirees le 18/11 sortent CICATRICE" % (
        temoin, sum(1 for c, _j in lignes if c["source"] != "en base")))
    dire("-> %s" % SORTIE)
    return 1 if crie else 0


if __name__ == "__main__":
    sys.exit(main())
