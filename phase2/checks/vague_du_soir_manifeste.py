"""LE MANIFESTE DU JOUR DE LA VAGUE -- les pieces que Frederic accorde, avec leurs empreintes (lecture et fabrication).

La commande `vague_du_soir.py --geste` exige `--accord <md5 de ce manifeste>` : il accorde CE fichier, donc CES pieces.

USAGE : python -X utf8 phase2/checks/vague_du_soir_manifeste.py --date J --image I --passage-ab P
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, r"C:\Hektor\Projet\phase2\checks")
sys.path.insert(0, r"C:\Hektor\Projet")
import protocole_classeur as P  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
ap = argparse.ArgumentParser()
ap.add_argument("--date", required=True)
ap.add_argument("--image", required=True)
ap.add_argument("--passage-ab", type=int, required=True, help="le passage a blanc de la vague entiere (R26 + retrait de E)")
a = ap.parse_args()
md5 = lambda p: hashlib.md5(Path(p).read_bytes()).hexdigest()
AB = P.DOSSIER.parent / "protocole_a_blanc_retrait_e"
SU = Path(r"C:\Hektor\Projet\supabase")
rejeux = sorted(AB.glob("rejeu_%s_E_*.json" % a.image))
if len(rejeux) != 1:
    raise SystemExit("⛔ le rejeu E de la vague entiere n'est pas unique pour l'image %s : %s" % (a.image, rejeux))
M = {"jour": a.date, "image": a.image, "image_dossier": str(P.IMAGES / a.image),
     "passage": "%d (a blanc : R26 + le retrait de E)" % a.passage_ab,
     "brouillon": {"chemin": str(AB / ("brouillon_detachements_protocole_passage_%d.csv" % a.passage_ab))},
     "attendu_E": {"chemin": str(rejeux[0])},
     "a2_patch": {"chemin": str(SU / ("patch_a2_vague_%s.sql" % a.date))},
     "a2_pregarde": {"chemin": str(SU / ("patch_a2_vague_%s_PREGARDE.sql" % a.date))},
     "a2_repetition": {"chemin": str(SU / ("patch_a2_vague_%s_REPETITION.sql" % a.date))},
     "a1_patch": {"chemin": str(SU / ("patch_a1_vague_%s.sql" % a.date))},
     "a3_patch": {"chemin": str(SU / ("patch_a3_vague_%s.sql" % a.date))},
     "a1_a3_inverse": {"chemin": str(SU / ("patch_a1_a3_vague_%s_INVERSE.sql" % a.date))},
     "commande": {"chemin": str(Path(__file__).resolve().parent / "vague_du_soir.py")},
     "fichier_en_place_md5": md5(r"C:\Hektor\Projet\phase2\sync\detachements_manuels.csv")}
for k, v in list(M.items()):
    if isinstance(v, dict) and "chemin" in v:
        v["md5"] = md5(v["chemin"])
corps = json.loads((Path(r"C:\Hektor\chantier_classeur_q6_cache\vague_du_soir") / ("corps_a1_a3_%s.json" % a.date))
                   .read_text(encoding="utf-8"))
M["a1a3_empreintes"] = corps["empreintes"]
f = Path(r"C:\Hektor\chantier_classeur_q6_cache\vague_du_soir") / ("manifeste_vague_%s.json" % a.date)
f.write_text(json.dumps(M, ensure_ascii=False, indent=1), encoding="utf-8")
print("-> %s\n   md5 DU MANIFESTE (celui qu'il accorde) : %s" % (f, md5(f)))
for k, v in M.items():
    if isinstance(v, dict) and "md5" in v:
        print("   %-14s %s  %s" % (k, v["md5"][:8], Path(v["chemin"]).name))
