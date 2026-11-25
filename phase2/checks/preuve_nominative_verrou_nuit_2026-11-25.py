"""LA PREUVE NOMINATIVE DU VERROU DE LA NUIT DU 24 AU 25/11 -- LECTURE SEULE (son mot du 25/11).

SON MOT : « ⬜ ET FAIS LA PREUVE NOMINATIVE PENDANT LA PREPARATION, puisque tu l'as signalee toi-meme comme non prouvee :
rejoue le calcul SANS pousser, et nomme-moi les 6 dossiers refuses. Si ce sont bien mes 6, le verrou est prouve par les
NOMS et plus par les comptes. »

CE QUE LE JOURNAL DU RUN DIT (comptes seulement) : nuit du 24 -> 7 408 lignes envoyees, 4 357 dossiers deja a jour,
3 704 proteges ; nuit du 25 -> 7 420, 4 351, 3 710 ; 0 ligne ecrite les deux nuits. Le calcul local est IDENTIQUE les deux
nuits (16 122 lignes, 7 791 suppositions, 270 hektor) : seule la COPIE a laquelle il se compare a change.

CE QUE CE SCRIPT FAIT -- rien n'est envoye, rien n'est ecrit (phase2.sqlite en mode=ro) :
  1. le calcul de la nuit, la VRAIE fonction (`calculer` de repartition_commission.py), puis `a_envoyer` contre la copie
     locale d'aujourd'hui (= Supabase : empreinte b531b578, verifiee ici) -> la nuit du 25, rejouee ;
  2. les dossiers que la base PROTEGE, par SA regle (app_repartition_absorber, patch du 15/09) : une part dont l'origine ne
     commence pas par « hektor » -> on n'y touche pas ;
  3. LE CONTREFACTUEL de la nuit du 24 : la meme copie, ④ et ⑤ DEFAITS (les parts que les deux patchs ont mises de cote
     reprennent leur place) -> on doit retrouver 7 408 / 4 357 / 3 704 ;
  4. la difference, NOMMEE.
"""
from __future__ import annotations

import hashlib
import importlib.util
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding="utf-8")

spec = importlib.util.spec_from_file_location("rc", RACINE / "phase2" / "sync" / "repartition_commission.py")
RC = importlib.util.module_from_spec(spec)
spec.loader.exec_module(RC)

QUATRE = {1027, 1875, 4234, 6391, 9370, 27984}          # ④ : les 6 chaines des suppositions (patch du 24/11)


def dire(s=""):
    print(s, flush=True)


def jouer(lignes: list[dict], copie: dict[tuple, tuple]) -> dict:
    """La nuit, rejouee contre une copie {(chaine, cote, rang): (uid, nom, pct, origine)}."""
    en_ligne = defaultdict(set)
    origines = defaultdict(set)
    for (c, cote, rang), (uid, nom, pct, orig) in copie.items():
        en_ligne[c].add(RC.empreinte({"cote": cote, "rang": rang, "hektor_user_id": uid, "nom_au_moment": nom,
                                      "pourcentage": pct, "origine": orig}))
        origines[c].add(orig or "")
    env, inchanges = RC.a_envoyer([dict(l) for l in lignes], dict(en_ligne))
    chaines = {int(l["app_chaine_id"]) for l in env}
    proteges = {c for c in chaines if any(not o.startswith("hektor") for o in origines.get(c, ()))}
    return {"lignes": len(env), "inchanges": inchanges, "chaines": chaines, "proteges": proteges,
            "ecrits": chaines - proteges}


def main() -> int:
    con = sqlite3.connect("file:%s?mode=ro" % (RACINE / "phase2" / "phase2.sqlite").as_posix(), uri=True)
    con.execute("PRAGMA busy_timeout = 60000")
    lignes, compte = RC.calculer(con)
    compte.pop("_nommes", None)
    rows = con.execute("select app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_par "
                       "from app_affaire_repartition").fetchall()
    mdc = con.execute("select ancien_app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, "
                      "mise_de_cote_par from app_affaire_repartition_mise_de_cote").fetchall()
    con.close()
    dire("LA PREUVE NOMINATIVE DU VERROU -- le calcul de la nuit, rejoue SANS pousser (lecture seule)")
    dire("   le calcul local : %d lignes (%s)" % (len(lignes), ", ".join("%s %d" % kv for kv in sorted(compte.items()))))
    # la copie locale = Supabase ? (la meme empreinte que le temoin de la nuit)
    txt = ";".join("|".join(str(x) for x in r if x is not None) for r in sorted(
        ((int(r[0]), r[1], int(r[2]), r[3], r[4], ("%.3f" % float(r[5])), r[6], r[7]) for r in rows),
        key=lambda r: (r[0], r[1], r[2])))
    dire("   la copie locale : %d parts, empreinte %s (Supabase ce matin : b531b578 ; %s)" % (
        len(rows), hashlib.md5(txt.encode()).hexdigest()[:8],
        "IDENTIQUE" if hashlib.md5(txt.encode()).hexdigest().startswith("b531b578") else "⚠ a lire : format du pourcentage"))
    copie = {(int(r[0]), r[1], int(r[2])): (r[3], r[4], r[5], r[6]) for r in rows}

    n25 = jouer(lignes, copie)
    dire()
    dire("① LA NUIT DU 25, REJOUEE : %d lignes a envoyer, %d dossiers deja a jour, %d dossiers envoyes dont %d PROTEGES "
         "et %d que la base aurait ecrits" % (n25["lignes"], n25["inchanges"], len(n25["chaines"]), len(n25["proteges"]),
                                              len(n25["ecrits"])))
    dire("   le journal du run : 7 420 / 4 351 / proteges 3 710 / ecrites 0 -> %s" % (
        "IDENTIQUE" if (n25["lignes"], n25["inchanges"], len(n25["proteges"]), len(n25["ecrits"])) == (7420, 4351, 3710, 0)
        else "⛔ DIFFERENT"))

    # le contrefactuel : ④ et ⑤ defaits (la mise de cote reprend sa place)
    avant = dict(copie)
    defaits = defaultdict(int)
    for c, cote, rang, uid, nom, pct, orig, par in mdc:
        avant[(int(c), cote, int(rang))] = (uid, nom, pct, orig)
        defaits[par] += 1
    n24 = jouer(lignes, avant)
    dire()
    dire("② LA NUIT DU 24, CONTREFACTUELLE (la meme copie, ④ et ⑤ defaits : %s) : %d lignes, %d deja a jour, %d proteges, "
         "%d ecrits" % (dict(defaits), n24["lignes"], n24["inchanges"], len(n24["proteges"]), len(n24["ecrits"])))
    dire("   le journal du run : 7 408 / 4 357 / proteges 3 704 / ecrites 0 -> %s" % (
        "IDENTIQUE" if (n24["lignes"], n24["inchanges"], len(n24["proteges"]), len(n24["ecrits"])) == (7408, 4357, 3704, 0)
        else "⛔ DIFFERENT"))

    nouveaux = sorted(n25["proteges"] - n24["proteges"])
    perdus = sorted(n24["proteges"] - n25["proteges"])
    dire()
    dire("③ LA DIFFERENCE, NOMMEE : %d dossier(s) proteges cette nuit et pas la nuit d'avant : %s ; %d dans l'autre sens %s"
         % (len(nouveaux), nouveaux, len(perdus), perdus))
    for c in nouveaux:
        env_c = sorted((l["cote"], int(l["rang"]), l["hektor_user_id"], l.get("nom_au_moment"), str(l["pourcentage"]),
                        l.get("origine")) for l in lignes if int(l["app_chaine_id"]) == c)
        base_c = sorted((k[1], k[2], v[0], v[1], str(v[2]), v[3]) for k, v in copie.items() if k[0] == c)
        dire("   chaine %5d : la nuit envoyait %s" % (c, env_c))
        dire("                 la base portait  %s -> PROTEGEE, rien ecrit" % base_c)
    dire()
    dire("-> %s" % ("⭐ CE SONT EXACTEMENT LES 6 CHAINES DE ④ (%s) : LE VERROU EST PROUVE PAR LES NOMS" % sorted(QUATRE)
                   if set(nouveaux) == QUATRE and not perdus else "⛔ LA DIFFERENCE N'EST PAS ④ -- a lire avant toute suite"))
    return 0 if set(nouveaux) == QUATRE and not perdus else 1


if __name__ == "__main__":
    sys.exit(main())
