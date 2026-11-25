"""UN SEUL GESTE (son mot du 25/11) : le remede de 8016 PUIS les 4 dates d'annulation, par la connexion de la commande.

« VAS-Y, POSE LE REMEDE DE 8016 [...] ET DANS LE MEME GESTE, POSE LES DATES D'ANNULATION QUI RESTENT [...] UN SEUL GESTE, UN
SEUL COMPTE RENDU. »
Chaque patch porte son begin ... commit, ses gardes et son empreinte d'apres exigee : s'il refuse, rien de lui n'est ecrit.
Les empreintes des fichiers sont verifiees AVANT d'envoyer. Puis les deux repetitions, en lecture seule.
"""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.stdout.reconfigure(encoding="utf-8")
import protocole_classeur as P  # noqa: E402
import vague_du_soir as V  # noqa: E402

SU = Path(__file__).resolve().parents[2] / "supabase"
PIECES = [("le remede de 8016", "patch_remede_8016_2026-11-25.sql", sys.argv[1]),
          ("les 4 dates d'annulation", "patch_dates_annulation_2026-11-25.sql", sys.argv[2])]
for quoi, f, attendu in PIECES:
    vu = hashlib.md5((SU / f).read_bytes()).hexdigest()
    if not vu.startswith(attendu):
        print("⛔ %s : %s a l'empreinte %s, pas %s -- RIEN n'est envoye" % (quoi, f, vu[:8], attendu))
        sys.exit(2)
for quoi, f, _a in PIECES:
    V.jouer_sql((SU / f).read_text(encoding="utf-8"), quoi)
cn, cu = P.pooler()
for f in ("patch_remede_8016_2026-11-25_REPETITION.sql", "patch_dates_annulation_2026-11-25_REPETITION.sql"):
    cu.execute((SU / f).read_text(encoding="utf-8"))
    for c, v in zip([d.name for d in cu.description], cu.fetchone()):
        print("   repetition %-48s %s" % (c, v))
cn.rollback()
cn.close()
