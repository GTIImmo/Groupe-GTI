# -*- coding: utf-8 -*-
"""ETAPE (1) DU CHANTIER DE LA CHARGE -- POSER LES 955 DU CLASSEUR (04/11/2026).

SES DEUX DECISIONS DU 04/11 :
  1. « go »  -> on pose les lignes du classeur sur le registre des mandats
  2. « oui » -> LA VALEUR DU CLASSEUR FAIT FOI, comme une saisie humaine
               -> donc elle va AU CARNET, avec origine = 'classeur'

CE SCRIPT N'ECRIT RIEN. Il MESURE et il GENERE le SQL. C'est le patch qui ecrit.
  (lecon du projet : « je l'eprouve, Frederic colle » -- et l'outil refuse
   l'ecriture de production depuis un script)

LE CHEMIN, MESURE LE 04/11 AVANT D'ECRIRE UNE LIGNE :
    ligne du classeur  --(ID Unique)-->  app_classeur_lien
                       --(app_affaire_id)-->  app_affaire_ledger
                       --(hektor_annonce_id + numero_mandat)-->  le mandat
    4 679 lignes reliees . 0 pointe plusieurs annonces . 4 645 citent UN mandat
    . 0 en cite plusieurs . 4 642 de ces mandats EXISTENT au registre

⛔ LE PIEGE EVITE, et il aurait tout detruit : la cle de liaison est « ID Unique »,
   JAMAIS le numero de ligne. charger_classeur() filtre les lignes vides
   (`[l for l in val[1:] if any(...)]`), donc l'indice dans la liste ne vaut PAS
   `ligne_classeur` : une seule ligne vide au milieu et tout glisse.

⛔⛔ L'AUTRE PIEGE, TROUVE DANS app_reposer_charge_mandat_app : elle filtre
   `origine = 'mandat_app'` AUX QUATRE ENDROITS, y compris dans son EFFACEMENT.
   Elle n'est appelee par personne aujourd'hui (temoin positif : sa soeur
   app_reposer_cloture_mandat_app EST appelee, push_single_annonce_to_supabase.py:710).
   Mais le jour ou on l'ajoute au run par symetrie, elle EFFACERAIT toute valeur
   du registre sans ligne 'mandat_app' -- donc les 955 du classeur.
   -> le patch l'elargit aux DEUX origines. Mecanisme installe a moitie, encore
      une fois ; une reserve non traitee devient le bug.

LES GARDES :
  . on ne pose QUE la ou le carnet est VIDE pour (annonce, mandat, charge_commission)
  . 1re passe : confiance « sure » SEULEMENT (les « a valider » et « bonne » apres,
    s'il le demande)
  . les valeurs acceptees sont celles de la RPC existante : 'vendeur' / 'acquereur'
    (minuscules, sans accent). Toute autre valeur est REFUSEE, pas devinee.
  . TEMOINS MESURES, jamais rappeles de memoire (lecon du 04/11 au matin : mon
    temoin choisi de souvenir etait faux, le garde-fou m'a arrete)
"""
from __future__ import annotations

import io
import os
import sys
from collections import defaultdict
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "phase2" / "sync"))
sys.path.insert(0, str(RACINE / "phase2" / "checks"))

from rapport_gel_tous_les_champs import charger_classeur, client, lire_tout  # noqa: E402

SORTIE_RAPPORT = RACINE / "notice" / "POSE_CHARGE_CLASSEUR_2026-11-04.md"
SORTIE_SQL = RACINE / "supabase" / "patch_charge_classeur_2026-11-04_DONNEES.sql"

COLONNE = "Charge Commission"
CLE = "ID Unique"
CHAMP = "charge_commission"
ORIGINE = "classeur"
CONFIANCES_1RE_PASSE = {"sûre"}


def mot_de_charge(v: str) -> str | None:
    """Normalise vers le vocabulaire de la RPC : 'vendeur' ou 'acquereur'.

    ⚠ `.lower()[:3]` NE SUFFIT PAS : Hektor ecrit « Acheteur » (-> 'ach') et le
    classeur « Acquereur » (-> 'acq'). On teste les deux racines explicitement.
    Toute autre valeur rend None : on REFUSE, on ne devine pas.
    """
    s = (v or "").strip().lower()
    for a, b in zip("éèêëàâäïîôöùûüç", "eeeeaaaiioouuuc"):
        s = s.replace(a, b)
    if not s:
        return None
    if s.startswith("vend") or s.startswith("mandant") or s.startswith("bailleur"):
        return "vendeur"
    if s.startswith("acq") or s.startswith("ach") or s.startswith("locataire"):
        return "acquereur"
    return None


def main() -> int:
    cl = client()
    entetes, lignes = charger_classeur()
    idx = {n: i for i, n in enumerate(entetes)}
    if COLONNE not in idx or CLE not in idx:
        raise SystemExit("ARRET : colonne '%s' ou '%s' absente du classeur" % (COLONNE, CLE))

    def case(l, nom):
        i = idx.get(nom)
        return str(l[i]).strip() if i is not None and i < len(l) else ""

    print("classeur : %d lignes, %d colonnes ('%s' en %d)"
          % (len(lignes), len(entetes), COLONNE, idx[COLONNE] + 1))

    # ── la charge, par ID Unique ───────────────────────────────────────────────
    charge_par_id: dict[str, str] = {}
    refusees: list[tuple[str, str]] = []
    vides = 0
    doublons: list[str] = []
    for l in lignes:
        iu = case(l, CLE)
        brut = case(l, COLONNE)
        if not iu:
            continue
        if not brut:
            vides += 1
            continue
        m = mot_de_charge(brut)
        if m is None:
            refusees.append((iu, brut))
            continue
        if iu in charge_par_id and charge_par_id[iu] != m:
            doublons.append(iu)
        charge_par_id[iu] = m
    print("  classeur : %d renseignees, %d vides, %d REFUSEES (valeur inconnue), %d doublons divergents"
          % (len(charge_par_id), vides, len(refusees), len(doublons)))

    # ── le pont et le registre ────────────────────────────────────────────────
    liens = lire_tout(cl, "app_classeur_lien", "id_unique,app_affaire_id,confiance",
                      "id_unique.asc,app_affaire_id.asc")
    led = lire_tout(cl, "app_affaire_ledger",
                    "app_affaire_id,hektor_annonce_id,numero_mandat", "app_affaire_id.asc")
    reg = lire_tout(cl, "app_mandat_register_current",
                    "hektor_annonce_id,numero_mandat,mandat_charge_honoraires_app",
                    "hektor_annonce_id.asc,numero_mandat.asc")
    carnet = lire_tout(cl, "app_mandat_champ_app",
                       "hektor_annonce_id,numero_mandat,champ,valeur_app,origine",
                       "hektor_annonce_id.asc,numero_mandat.asc,champ.asc")
    print("  pont : %d liens . registre : %d mandats . carnet : %d lignes"
          % (len(liens), len(reg), len(carnet)))

    affaire = {}
    for a in led:
        ann = a.get("hektor_annonce_id")
        man = (a.get("numero_mandat") or "").strip()
        if ann is not None and man:
            affaire[a["app_affaire_id"]] = (str(ann).strip(), man)

    mandats_existants = {(str(r["hektor_annonce_id"]).strip(),
                          str(r["numero_mandat"]).strip()) for r in reg
                         if r.get("hektor_annonce_id") is not None and r.get("numero_mandat")}
    colonne_deja = {(str(r["hektor_annonce_id"]).strip(), str(r["numero_mandat"]).strip())
                    for r in reg
                    if (r.get("mandat_charge_honoraires_app") or "").strip()}
    carnet_deja = {(str(k["hektor_annonce_id"]).strip(), str(k["numero_mandat"]).strip())
                   for k in carnet if k.get("champ") == CHAMP}

    par_id = defaultdict(list)
    for x in liens:
        par_id[str(x.get("id_unique") or "").strip()].append(x)

    # ── le croisement ─────────────────────────────────────────────────────────
    a_poser: dict[tuple[str, str], tuple[str, str]] = {}   # (ann, man) -> (charge, id_unique)
    conflits: list[str] = []
    ecartes_pour_conflit: set[tuple[str, str]] = set()
    motifs = defaultdict(int)
    for iu, m in sorted(charge_par_id.items()):
        ls = par_id.get(iu) or []
        if not ls:
            motifs["la ligne n est pas reliee par le gel"] += 1
            continue
        retenus = [x for x in ls if (x.get("confiance") or "").strip() in CONFIANCES_1RE_PASSE]
        if not retenus:
            motifs["lien hors 1re passe (a valider / bonne)"] += 1
            continue
        cibles = {affaire[x["app_affaire_id"]] for x in retenus
                  if x.get("app_affaire_id") in affaire}
        if not cibles:
            motifs["l affaire ne cite ni annonce ni mandat"] += 1
            continue
        if len(cibles) > 1:
            motifs["la ligne vise PLUSIEURS mandats"] += 1
            continue
        cible = next(iter(cibles))
        if cible not in mandats_existants:
            motifs["le mandat n est pas au registre"] += 1
            continue
        if cible in carnet_deja:
            motifs["le carnet porte DEJA une valeur (on n ecrase pas)"] += 1
            continue
        if cible in colonne_deja:
            motifs["la colonne du registre est deja remplie"] += 1
            continue
        if cible in a_poser:
            # ⚠ LE CLASSEUR A UNE LIGNE PAR TRANSACTION, pas par mandat : offre,
            #   compromis et vente d'un meme bien visent LE MEME mandat. Deux
            #   lignes qui disent la meme charge se FONDENT -- il faut le compter,
            #   sinon l'ecart entre « renseignees » et « a poser » reste inexplique.
            if a_poser[cible][0] != m:
                # ⛔⛔ CORRIGE LE 04/11 APRES COUP, ET J'AVAIS POSE 2 VALEURS FAUSSES :
                #   ma 1re version se contentait de NOTER le conflit et GARDAIT la
                #   premiere valeur rencontree -- donc une charge ARBITRAIRE, decidee
                #   par l'ordre de lecture du classeur. 46338/17322 avait recu
                #   « acquereur » et 47174/17639 « vendeur » sans aucune raison.
                #   Les deux ont ete RETIREES de la base.
                #   Un conflit ECARTE le mandat : on ne devine pas une charge.
                conflits.append("%s/%s : %s contre %s (ID %s et %s)"
                                % (cible[0], cible[1], a_poser[cible][0], m,
                                   a_poser[cible][1], iu))
                a_poser.pop(cible, None)
                ecartes_pour_conflit.add(cible)
            else:
                motifs["fondue : meme mandat, meme charge (2e transaction)"] += 1
            continue
        if cible in ecartes_pour_conflit:
            # une 3e ligne sur un mandat deja juge en conflit ne le ressuscite pas
            continue
        a_poser[cible] = (m, iu)

    nb_v = sum(1 for c, _ in a_poser.values() if c == "vendeur")
    nb_a = sum(1 for c, _ in a_poser.values() if c == "acquereur")
    print()
    print("  A POSER : %d  (%d vendeur, %d acquereur)" % (len(a_poser), nb_v, nb_a))
    for k in sorted(motifs, key=lambda x: -motifs[x]):
        print("    ecartees -- %-48s %d" % (k, motifs[k]))
    if conflits:
        print("    CONFLITS (deux lignes, deux charges) : %d" % len(conflits))

    # ── LES TEMOINS, MESURES ICI, JAMAIS RAPPELES DE MEMOIRE ──────────────────
    print()
    print("  LES TEMOINS :")
    # ⚠ « rien a poser » a DEUX sens, et les confondre fait crier au loup :
    #   . rien a poser ET rien de deja pose -> le pont est casse, ON ARRETE
    #   . rien a poser PARCE QUE tout est deja pose -> c'est le 2e passage, normal
    deja = motifs.get("le carnet porte DEJA une valeur (on n ecrase pas)", 0)
    if not a_poser and deja == 0:
        raise SystemExit("ARRET : rien a poser et rien de deja pose -- verifier le pont")
    if not a_poser:
        print("    rien a poser : les %d lignes sont DEJA au carnet (2e passage, normal)" % deja)
    elif nb_a == 0:
        raise SystemExit("ARRET : zero acquereur a poser alors qu'il y a du travail. "
                         "Le classeur en porte 61 : le pont ou la normalisation perd "
                         "la classe RARE.")
    if refusees:
        print("    ATTENTION : %d valeurs du classeur refusees, les 5 premieres :" % len(refusees))
        for iu, brut in refusees[:5]:
            print("       ID %-14s valeur « %s »" % (iu, brut[:40]))
    t_v = next((k for k, v in sorted(a_poser.items()) if v[0] == "vendeur"), None)
    t_a = next((k for k, v in sorted(a_poser.items()) if v[0] == "acquereur"), None)
    if t_v:
        print("    temoin positif VENDEUR   : annonce %s mandat %s (ID %s)"
              % (t_v[0], t_v[1], a_poser[t_v][1]))
    if t_a:
        print("    temoin positif ACQUEREUR : annonce %s mandat %s (ID %s)"
              % (t_a[0], t_a[1], a_poser[t_a][1]))

    # temoin inverse : une ligne VIDE au classeur ne doit JAMAIS etre posee
    vides_posees = 0
    for l in lignes:
        iu = case(l, CLE)
        if iu and not case(l, COLONNE):
            for x in (par_id.get(iu) or []):
                c = affaire.get(x.get("app_affaire_id"))
                if c and c in a_poser and a_poser[c][1] == iu:
                    vides_posees += 1
    print("    temoin INVERSE : lignes VIDES au classeur qui seraient posees : %d (doit etre 0)"
          % vides_posees)
    if vides_posees:
        raise SystemExit("ARRET : une ligne vide du classeur serait posee -- le pont est faux")

    # ── LE SQL ────────────────────────────────────────────────────────────────
    q = lambda s: "'" + str(s).replace("'", "''") + "'"
    sql = []
    sql.append("-- =====================================================================")
    sql.append("-- LES DONNEES DE L ETAPE (1) : LA CHARGE, DEPUIS LE CLASSEUR -- 04/11/2026")
    sql.append("-- =====================================================================")
    sql.append("-- Genere par phase2/checks/poser_charge_classeur_2026-11-04.py")
    sql.append("-- %d lignes : %d vendeur, %d acquereur" % (len(a_poser), nb_v, nb_a))
    sql.append("-- origine = 'classeur' -- SA DECISION DU 04/11 : elle FAIT FOI.")
    sql.append("-- ⛔ A COLLER APRES patch_charge_classeur_2026-11-04.sql, qui elargit")
    sql.append("--    app_reposer_charge_mandat_app aux deux origines. Sans lui, la")
    sql.append("--    premiere repose EFFACERAIT ces %d lignes." % len(a_poser))
    sql.append("-- ON CONFLICT DO NOTHING : on n ecrase JAMAIS une saisie humaine.")
    sql.append("-- =====================================================================")
    sql.append("")
    sql.append("insert into public.app_mandat_champ_app")
    sql.append("  (hektor_annonce_id, numero_mandat, champ, valeur_app, origine, ecrit_par, ecrit_le)")
    sql.append("values")
    corps = []
    for (ann, man), (m, iu) in sorted(a_poser.items()):
        corps.append("  (%s, %s, %s, %s, %s, %s, now())"
                     % (q(ann), q(man), q(CHAMP), q(m), q(ORIGINE), q("classeur:" + iu)))
    sql.append(",\n".join(corps))
    sql.append("on conflict (hektor_annonce_id, numero_mandat, champ) do nothing;")
    sql.append("")
    sql.append("-- Puis on repose le reflet sur la colonne du registre.")
    sql.append("select public.app_reposer_charge_mandat_app(null, 10000) as repose;")
    sql.append("")
    SORTIE_SQL.parent.mkdir(parents=True, exist_ok=True)
    io.open(SORTIE_SQL, "w", encoding="utf-8", newline="\n").write("\n".join(sql))

    # ── LE RAPPORT ────────────────────────────────────────────────────────────
    r = []
    r.append("# LA CHARGE DEPUIS LE CLASSEUR -- etape (1) posee le 04/11/2026")
    r.append("")
    r.append("Ses deux decisions du 04/11 : **go** sur la pose, et **oui**, la valeur du")
    r.append("classeur **fait foi** -- donc elle va au carnet avec `origine = 'classeur'`.")
    r.append("")
    r.append("## Ce que le classeur porte")
    r.append("")
    r.append("```")
    r.append("lignes du classeur                 %d" % len(lignes))
    r.append("charge renseignee                  %d" % len(charge_par_id))
    r.append("charge vide                        %d" % vides)
    r.append("valeur REFUSEE (inconnue)          %d" % len(refusees))
    r.append("doublons divergents                %d" % len(doublons))
    r.append("```")
    r.append("")
    r.append("## Ce qui est pose, et ce qui est ecarte")
    r.append("")
    r.append("```")
    r.append("A POSER                            %d   (%d vendeur, %d acquereur)"
             % (len(a_poser), nb_v, nb_a))
    for k in sorted(motifs, key=lambda x: -motifs[x]):
        r.append("ecartee -- %-42s %d" % (k, motifs[k]))
    r.append("conflits (deux lignes, deux charges) %d" % len(conflits))
    r.append("```")
    r.append("")
    if conflits:
        r.append("### Les conflits, NOMMES (un controle qui agrege perd ce qui sert a agir)")
        r.append("")
        r.append("```")
        for c in conflits[:60]:
            r.append(c)
        r.append("```")
        r.append("")
    if refusees:
        r.append("### Les valeurs refusees, NOMMEES")
        r.append("")
        r.append("```")
        for iu, brut in refusees[:60]:
            r.append("ID %-16s « %s »" % (iu, brut[:50]))
        r.append("```")
        r.append("")
    r.append("## Les temoins")
    r.append("")
    r.append("```")
    r.append("positif VENDEUR    %s" % ("annonce %s mandat %s" % t_v if t_v else "rien a poser"))
    r.append("positif ACQUEREUR  %s" % ("annonce %s mandat %s" % t_a if t_a else "rien a poser"))
    r.append("INVERSE            lignes vides du classeur qui seraient posees : %d" % vides_posees)
    r.append("```")
    r.append("")
    r.append("Les temoins sont **mesures ici**, jamais rappeles de memoire : le 04/11 au")
    r.append("matin, un temoin choisi de souvenir etait faux et le garde-fou a arrete le")
    r.append("script.")
    r.append("")
    r.append("## Ce que ca pourrait casser ailleurs")
    r.append("")
    r.append("`app_reposer_charge_mandat_app` filtre `origine = 'mandat_app'` **aux quatre")
    r.append("endroits**, dont son effacement. Elle n'est appelee par personne aujourd'hui")
    r.append("(temoin positif : sa soeur de la cloture **est** appelee,")
    r.append("`push_single_annonce_to_supabase.py:710`). Le jour ou on l'ajoute au run par")
    r.append("symetrie, elle **effacerait** toute valeur sans ligne `mandat_app`.")
    r.append("Le patch l'elargit aux deux origines : la saisie humaine garde la main")
    r.append("(la RPC fait `ON CONFLICT DO UPDATE` et repasse l'origine a `mandat_app`).")
    r.append("")
    SORTIE_RAPPORT.parent.mkdir(parents=True, exist_ok=True)
    io.open(SORTIE_RAPPORT, "w", encoding="utf-8", newline="\n").write("\n".join(r))

    print()
    print("  SQL     : %s" % SORTIE_SQL)
    print("  rapport : %s" % SORTIE_RAPPORT)
    print("FIN -- aucune ecriture en base, classeur en LECTURE seule")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
