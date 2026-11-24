# -*- coding: utf-8 -*-
"""Etape ⑥ du run du recrutement : la MONTEE, base locale -> schema « recrutement » (R4, 24/11/2026).

    python -X utf8 recrutement/pousser.py              -> envoie, controle, valide
    python -X utf8 recrutement/pousser.py --essai      -> fait tout dans une transaction puis l'ANNULE
    python -X utf8 recrutement/pousser.py --preparer   -> sans reseau : prepare les lignes et les verifie

Interprete : le Python SYSTEME (psycopg2). Connexion : le robot (recrutement/robot.py), qui n'a de droits
que sur le schema « recrutement » et ne peut RIEN supprimer.

CE QU'ELLE ENVOIE : les fiches (+ l'agence GTI la plus proche et sa distance), les entreprises qu'elles
citent, les collectes et la sante de chaque source. Par « insert ... on conflict do update » : une fiche
deja la est mise a jour, jamais effacee. Elle NE TOUCHE JAMAIS au carnet des corrections ni a la liste
« ne plus contacter » (ce sont les ecritures de l'app ; le robot n'a que le droit de les LIRE).

AVANT D'ECRIRE, chaque ligne est verifiee contre les regles du schema (region, coordonnee avec sa source,
SIREN a 9 chiffres, etats connus) : une ligne fautive arrete tout AVANT la premiere ecriture, avec un
message clair, au lieu d'un refus de la base au milieu.
APRES AVOIR ECRIT, et AVANT de valider, les controles du plan (§14, R4.3) :
  - autant de fiches collectees en base qu'en local (celles de trop sont signalees : le robot ne
    supprime pas -- un effacement passe par l'app) ;
  - 0 coordonnee pour iad (contact cache, regle du 20/11) ;
  - 0 donnee de registre pour une personne en opposition ;
  - 0 personne de la liste « ne plus contacter ».
Un controle rouge ANNULE tout (rien n'est valide). Le journal ne porte que des COMPTES, jamais un nom.
Sortie : 0 = envoye (ou essai vert), 1 = refuse / echec.
"""
import argparse
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import collecte_annuaires as ca  # noqa: E402

ETATS_SUIVI = {"nouveau", "present", "absent", "parti", "revenu"}
COLONNES_FICHE = ("reseau", "identifiant", "origine", "url", "prenom", "nom", "fonction", "agence", "commune",
                  "code_postal", "departement", "lat", "lon", "agence_gti_proche", "distance_km", "telephone",
                  "email", "source_contact", "siren", "rsac_ville", "nb_annonces", "nb_avis", "note_avis",
                  "distinction", "desactive", "etat_suivi", "etat_depuis", "motif_depart", "premiere_vue",
                  "derniere_vue")


def _date(v):
    if not v:
        return None
    try:
        return dt.date.fromisoformat(str(v)[:10])
    except ValueError:
        return None


def _horodatage(v):
    """« 2026-11-20 18:41:32 » (heure locale du serveur) -> datetime AVEC son fuseau ; « 2026-11-20 » -> minuit."""
    if not v:
        return None
    s = str(v)
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(s[:19] if fmt.endswith("%S") else s[:10], fmt).astimezone()
        except ValueError:
            continue
    return None


def preparer(con) -> dict:
    """Les lignes a envoyer, et les fautes trouvees AVANT tout envoi (comptes par reseau, jamais un nom)."""
    agences = ca.agences_placees(con)
    fiches, fautes = [], {}

    def faute(reseau, quoi):
        fautes.setdefault(f"{reseau} : {quoi}", 0)
        fautes[f"{reseau} : {quoi}"] += 1

    for f in con.execute("select * from fiche"):
        lat, lon = f["lat"], f["lon"]
        if lat is None:
            c = ca.position_commune(con, f["commune"], f["code_postal"])
            if c is not None:
                lat, lon = c["lat"], c["lon"]
        proche, dist = None, None
        if lat is not None and agences:
            proche, d = min(((a[0], ca.distance_km(lat, lon, a[1], a[2])) for a in agences), key=lambda x: x[1])
            dist = round(d, 1)
        ligne = {
            "reseau": f["reseau"], "identifiant": f["identifiant"], "origine": "collecte", "url": f["url"],
            "prenom": f["prenom"], "nom": f["nom"], "fonction": f["fonction"], "agence": f["agence"],
            "commune": f["commune"], "code_postal": f["code_postal"], "departement": f["departement"],
            "lat": lat, "lon": lon, "agence_gti_proche": proche, "distance_km": dist,
            "telephone": f["telephone"], "email": f["email"], "source_contact": f["source_contact"],
            "siren": f["siren"], "rsac_ville": f["rsac_ville"], "nb_annonces": f["nb_annonces"],
            "nb_avis": f["nb_avis"], "note_avis": None if f["note_avis"] is None else round(float(f["note_avis"]), 2),
            "distinction": f["distinction"], "desactive": bool(f["desactive"]),
            "etat_suivi": f["etat_suivi"], "etat_depuis": _date(f["etat_depuis"]), "motif_depart": f["motif_depart"],
            "premiere_vue": _date(f["premiere_vue"]), "derniere_vue": _date(f["derniere_vue"]),
        }
        # LES REGLES DU SCHEMA, verifiees ici d'abord
        if not ligne["reseau"] or not ligne["identifiant"]:
            faute(ligne["reseau"], "cle vide"); continue
        if ligne["departement"] not in ca.DEPARTEMENTS:
            faute(ligne["reseau"], "hors de la region"); continue
        if (ligne["telephone"] or ligne["email"]) and not ligne["source_contact"]:
            faute(ligne["reseau"], "coordonnee sans source"); continue
        if ligne["siren"] and not (len(ligne["siren"]) == 9 and ligne["siren"].isdigit()):
            faute(ligne["reseau"], "SIREN mal forme"); continue
        if ligne["etat_suivi"] and ligne["etat_suivi"] not in ETATS_SUIVI:
            faute(ligne["reseau"], f"etat inconnu {ligne['etat_suivi']}"); continue
        if ligne["note_avis"] is not None and not (0 <= ligne["note_avis"] < 10):
            faute(ligne["reseau"], "note hors bornes"); continue
        if ligne["reseau"] in ca.RESEAUX_CONTACT_CACHE and (ligne["telephone"] or ligne["email"]):
            faute(ligne["reseau"], "coordonnee la ou elle est cachee"); continue
        fiches.append(ligne)

    sirens = {l["siren"] for l in fiches if l["siren"]}
    entreprises = []
    for e in con.execute("select * from entreprise"):
        if e["siren"] not in sirens:
            continue
        opp = bool(e["opposition"])
        etat = e["etat"] if e["etat"] in ("A", "C") else None
        entreprises.append({
            "siren": e["siren"], "trouve": None if e["trouve"] is None else bool(e["trouve"]),
            # ⛔ OPPOSITION : aucune donnee du registre ne monte, seulement le fait
            "date_creation": None if opp else _date(e["date_creation"]), "etat": None if opp else etat,
            "naf": None if opp else e["naf"], "siege_cp": None if opp else e["siege_cp"],
            "siege_commune": None if opp else e["siege_commune"], "opposition": opp,
            "lu_le": _horodatage(e["lu_le"]),
        })
    collectes = [{"numero": c["numero"], "debut": _horodatage(c["debut"]), "fin": _horodatage(c["fin"]),
                  "etat": c["etat"], "note": c["note"]}
                 for c in con.execute("select * from collecte where etat in ('en_cours', 'finie')")]
    sources = [dict(s) for s in con.execute("select collecte, reseau, vus, precedent, sante, raison from source_etat")]
    # les 17 agences et leur position (la carte « Où recruter » de l'écran) -- R6, 24/11
    dep_agence = dict(ca.AGENCES_GTI)
    agences_gti = [{"nom": nom, "departement": dep_agence.get(nom), "lat": lat, "lon": lon} for nom, lat, lon in agences]
    return {"fiches": fiches, "entreprises": entreprises, "collectes": collectes, "sources": sources,
            "agences": agences_gti, "fautes": fautes}


def _upsert(cur, table, colonnes, cle, lignes):
    from psycopg2.extras import execute_values
    if not lignes:
        return 0
    maj = ", ".join(f"{c} = excluded.{c}" for c in colonnes if c not in cle)
    sql = (f"insert into recrutement.{table} ({', '.join(colonnes)}) values %s "
           f"on conflict ({', '.join(cle)}) do update set {maj}, monte_le = now()") if table in ("fiche", "entreprise", "collecte", "agence_gti") else (
           f"insert into recrutement.{table} ({', '.join(colonnes)}) values %s "
           f"on conflict ({', '.join(cle)}) do update set {maj}")
    execute_values(cur, sql, [tuple(l[c] for c in colonnes) for l in lignes], page_size=500)
    return len(lignes)


def envoyer(paquet: dict, essai: bool) -> int:
    import robot
    con = robot.connexion()
    rouges = []
    try:
        cur = con.cursor()
        n_c = _upsert(cur, "collecte", ("numero", "debut", "fin", "etat", "note"), ("numero",), paquet["collectes"])
        n_s = _upsert(cur, "source_etat", ("collecte", "reseau", "vus", "precedent", "sante", "raison"),
                      ("collecte", "reseau"), paquet["sources"])
        n_e = _upsert(cur, "entreprise", ("siren", "trouve", "date_creation", "etat", "naf", "siege_cp", "siege_commune",
                                          "opposition", "lu_le"), ("siren",), paquet["entreprises"])
        n_f = _upsert(cur, "fiche", COLONNES_FICHE, ("reseau", "identifiant"), paquet["fiches"])
        # la table des agences n'existe qu'une fois le patch de l'ecran pose (R6) : sans elle, on passe
        cur.execute("select to_regclass('recrutement.agence_gti') is not null")
        n_a = (_upsert(cur, "agence_gti", ("nom", "departement", "lat", "lon"), ("nom",), paquet["agences"])
               if cur.fetchone()[0] else 0)
        print(f"envoye : {n_f} fiches, {n_e} entreprises, {n_c} collectes, {n_s} etats de source, {n_a} agences")

        # LES CONTROLES, AVANT DE VALIDER (un rouge annule tout)
        locales = {(l["reseau"], l["identifiant"]) for l in paquet["fiches"]}
        cur.execute("select reseau, identifiant from recrutement.fiche where origine = 'collecte'")
        distantes = {(r[0], r[1]) for r in cur.fetchall()}
        manquantes, en_trop = locales - distantes, distantes - locales
        print(f"controle : {len(distantes)} fiches collectees en base pour {len(locales)} en local ; "
              f"manquantes {len(manquantes)}, en trop {len(en_trop)}")
        if manquantes:
            rouges.append(f"{len(manquantes)} fiches envoyees introuvables en base")
        if en_trop:
            par_reseau = {}
            for r, _ in en_trop:
                par_reseau[r] = par_reseau.get(r, 0) + 1
            print(f"  ⚠ en base mais plus en local (le robot ne supprime pas ; un effacement passe par l'app) : {par_reseau}")
        cur.execute("select count(*) from recrutement.fiche where reseau = any(%s) and (telephone is not null or email is not null)",
                    (list(ca.RESEAUX_CONTACT_CACHE),))
        n = cur.fetchone()[0]
        print(f"controle : coordonnees en base la ou elles sont cachees ({', '.join(ca.RESEAUX_CONTACT_CACHE)}) : {n}")
        if n:
            rouges.append(f"{n} coordonnees iad en base")
        cur.execute("select count(*) from recrutement.entreprise where opposition and "
                    "coalesce(date_creation::text, etat, naf, siege_cp, siege_commune) is not null")
        n = cur.fetchone()[0]
        print(f"controle : donnees de registre gardees pour une personne en opposition : {n}")
        if n:
            rouges.append(f"{n} entreprises en opposition avec des donnees")
        cur.execute("select empreinte from recrutement.liste_noire")
        noire = {r[0] for r in cur.fetchall()}
        touchees = sum(1 for l in paquet["fiches"]
                       if any(e in noire for _, e in ca.empreintes_personne(
                           siren=l["siren"], telephone=l["telephone"], email=l["email"],
                           prenom=l["prenom"], nom=l["nom"], departement=l["departement"])))
        print(f"controle : personnes envoyees qui sont sur la liste « ne plus contacter » : {touchees} "
              f"(liste : {len(noire)} empreintes)")
        if touchees:
            rouges.append(f"{touchees} personnes de la liste noire envoyees")
        if rouges or essai:
            con.rollback()
            print(("⛔ ROUGE, TOUT EST ANNULE : " + " ; ".join(rouges)) if rouges else "essai : tout est ANNULE (rien n'est valide)")
            return 1 if rouges else 0
        con.commit()
        print("valide.")
        return 0
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--essai", action="store_true", help="tout faire puis ANNULER")
    p.add_argument("--preparer", action="store_true", help="sans reseau : preparer et verifier les lignes")
    args = p.parse_args()
    con = ca.ouvrir_base()
    paquet = preparer(con)
    print(f"prepare : {len(paquet['fiches'])} fiches, {len(paquet['entreprises'])} entreprises, "
          f"{len(paquet['collectes'])} collectes, {len(paquet['sources'])} etats de source")
    if paquet["fautes"]:
        print("⛔ LIGNES FAUTIVES, RIEN N'EST ENVOYE :")
        for quoi, n in sorted(paquet["fautes"].items()):
            print(f"   {quoi} : {n}")
        return 1
    if args.preparer:
        print("preparation verte (aucun envoi)")
        return 0
    try:
        return envoyer(paquet, args.essai)
    except Exception as e:
        print(f"⛔ ECHEC : {e.__class__.__name__} : {str(e)[:300]}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
