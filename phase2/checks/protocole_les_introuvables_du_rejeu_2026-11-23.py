"""P-a, LES SIGNAUX « [X] detachement : transaction introuvable » DU REJEU EXACT -- LECTURE SEULE (23/11).

Son message du 23/11 au soir, point 5 : « Les deux signaux « transaction introuvable » d'abord : un rejeu avec deux lignes
qu'on n'explique pas n'est pas un rejeu vert. » Le rejeu E (protocole_portes.py) ne garde que le COMPTE des signaux. Ici :
le MEME module de production, charge a part comme le rejeu E (protocole_portes.charger), sur une COPIE EN MEMOIRE du
registre de l'image, le brouillon des coupes du passage -- une seule difference : la ligne qui signale « introuvable »
ecrit AUSSI le morceau et les transactions absentes de la place. Rien d'autre n'est change ; rien n'est ecrit hors du cache.

USAGE : python -u phase2/checks/protocole_les_introuvables_du_rejeu_2026-11-23.py [passage]
"""
import sys, os, io, json, sqlite3, contextlib, importlib.util, time
sys.path.insert(0, r"C:\Hektor\Projet\phase2\checks"); sys.path.insert(0, r"C:\Hektor\Projet")
import protocole_classeur as P, protocole_portes as PO, piece_copie_ou_vraie as PC
sys.stdout.reconfigure(encoding="utf-8")
PASSAGE = int(sys.argv[1]) if len(sys.argv) > 1 else 73
IMAGE = "2026-11-23_080234"
brouillon = P.DOSSIER / ("brouillon_detachements_protocole_passage_%d.csv" % PASSAGE)
ANCRE = '                    signale("[X] detachement : transaction introuvable -- le morceau est ignore")\n'
ESPION = ('                    print("@@INTROUVABLE", annonce, sorted(ids_), sorted(t for t in ids_ if t not in place), '
          'flush=True)\n' + ANCRE)
ANCRE_M = '                    signale("[M] rattachement manuel : transaction introuvable")\n'
ESPION_M = ('                    print("@@INTROUVABLE_M", annonce, source_id, cible_id, flush=True)\n' + ANCRE_M)

source = PO.MODULE.read_text(encoding="utf-8")
for a_, b_ in ((ANCRE, ESPION), (ANCRE_M, ESPION_M)):
    if source.count(a_) != 1:
        raise SystemExit("⛔ l'ancre n'est pas unique dans le module de production (%d) : %r" % (source.count(a_), a_[:60]))
for avant, apres in (("ROOT = Path(__file__).resolve().parents[2]", "ROOT = Path(%r)" % str(PO.RACINE)),
                     ('FICHIER_RATTACHEMENTS = Path(__file__).resolve().parent / "rattachements_manuels.csv"',
                      "FICHIER_RATTACHEMENTS = Path(%r)" % str(PO.FICHIER_RAT_PROD)),
                     ('FICHIER_DETACHEMENTS = Path(__file__).resolve().parent / "detachements_manuels.csv"',
                      "FICHIER_DETACHEMENTS = Path(%r)" % str(brouillon)),
                     (ANCRE, ESPION), (ANCRE_M, ESPION_M)):
    if avant not in source:
        raise SystemExit("⛔ ancre introuvable %r" % avant[:60])
    source = source.replace(avant, apres)
tmp = P.DOSSIER / "_module_portes_espion_introuvables.py"
tmp.write_text(source, encoding="utf-8")
spec = importlib.util.spec_from_file_location("al_espion", tmp)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

env = {"APP_CHAINAGE_GARDE_G2": "0", "APP_CHAINAGE_DETACHEMENTS": "1"}
os.environ.update(env)
t0 = time.time()
src = sqlite3.connect("file:%s?mode=ro" % (P.IMAGES / IMAGE / "registre.sqlite").as_posix(), uri=True)
mem = sqlite3.connect(":memory:")
src.backup(mem)
src.close()
reg = {int(r[0]): r for r in mem.execute("select app_affaire_id, hektor_annonce_id, kind, state, date, montant, "
                                          "present_in_hektor, hektor_affaire_id, app_chaine_id, app_dossier_id "
                                          "from %s" % mod.LEDGER_TABLE)}
with contextlib.redirect_stdout(io.StringIO()) as sortie:
    res = mod.recalculer_les_chaines(mem)
lignes = [l for l in sortie.getvalue().splitlines() if l.startswith("@@INTROUVABLE")]
print("REJEU E INSTRUMENTE, passage %d, %.0f s ; compte rendu [X]/[M] : %s" % (
    PASSAGE, time.time() - t0, {k: v for k, v in res.items() if str(k)[:3] in ("[X]", "[M]")}))
print("LES SIGNAUX, UN PAR UN (%d) :" % len(lignes))
for l in lignes:
    print("  " + l)
    if l.startswith("@@INTROUVABLE "):
        _t, annonce, reste = l.split(" ", 2)
        manquantes = json.loads(reste[reste.index("] [") + 2:])
        for t in manquantes:
            r = reg.get(t)
            print("     transaction %s : %s" % (t, ("ABSENTE du registre" if r is None else
                                                   "bien %s, %s %s, date %r, montant %s, present_in_hektor %r, numero Hektor "
                                                   "%r, chaine %s, dossier %s" % r[1:])))
# le temoin : le compte du rejeu E en cache, identique (le meme brouillon, le meme module hors l'espion)
cache = sorted(P.DOSSIER.glob("rejeu_%s_E_*.json" % IMAGE), key=lambda p: p.stat().st_mtime)[-1]
resE = json.loads(cache.read_text(encoding="utf-8"))["res"]
memes = {k: v for k, v in resE.items() if str(k)[:3] in ("[X]", "[M]")} == {k: v for k, v in res.items()
                                                                           if str(k)[:3] in ("[X]", "[M]")}
print("TEMOIN : le compte rendu [X]/[M] = celui du rejeu E en cache (%s) : %s" % (cache.name, "OUI" if memes else
                                                                                   "⛔ NON %s" % resE))
mem.close()
