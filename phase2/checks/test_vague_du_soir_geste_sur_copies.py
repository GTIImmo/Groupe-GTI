"""LE CHEMIN DU GESTE DE `vague_du_soir.py`, EPROUVE SUR DES COPIES (25/11, apres l'arret de 08:09).

POURQUOI. Le geste de 08:09 s'est arrete a l'etape 2 sur une preuve qui, AU GESTE, comparait le module a lui-meme ; et la
remise n'a pas joue (elle attendait la FIN de l'etape 2). Les deux defauts ne se voyaient qu'au geste : l'essai a blanc posait
dans la scene. Cet essai fait tourner le VRAI `main()` en mode GESTE, mais :
  . le module de nuit, le fichier des coupes et .env sont des COPIES dans un bac a sable (le .env est FACTICE : aucun secret) ;
  . `etape_0` (les gardes) est remplacee par « aucun refus » -- elles sont eprouvees a part ;
  . `jouer_sql` (Supabase en ecriture), `lancer` (doublure, chainage, repartition) et `etape_4` sont des LEURRES qui notent
    leurs appels sans rien toucher ; la lecture de la repetition d'A2 aussi.
QUATRE CAS :
  A  une panne PENDANT la pose (le brouillon n'a pas l'empreinte annoncee)  -> REMIS, copies revenues a l'identique
  B  une panne au POINT DE NON-RETOUR (erreur quelconque, pas un refus)      -> REMIS
  C  une panne PENDANT l'etape 5                                             -> RIEN n'est remis, et il le DIT
  D  le chemin vert                                                          -> etapes 0 a 8 dans l'ordre, la pose prouvee
     (depot moins 10 lignes, .env = ses deux interrupteurs en plus), « 9. ARRET »
Sortie 0 si les quatre cas rendent ce qui est attendu.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import types
from pathlib import Path

sys.path.insert(0, r"C:\Hektor\Projet\phase2\checks")
sys.path.insert(0, r"C:\Hektor\Projet")
sys.stdout.reconfigure(encoding="utf-8")
import vague_du_soir as V  # noqa: E402

BAC = Path(r"C:\Hektor\chantier_classeur_q6_cache\vague_du_soir\test_geste_sur_copies")
md5 = lambda p: hashlib.md5(Path(p).read_bytes()).hexdigest()
REEL_MODULE, REEL_DET = V.MODULE, V.FICHIER_DET
M_REEL = json.loads(Path(r"C:\Hektor\chantier_classeur_q6_cache\vague_du_soir\manifeste_vague_2026-11-25.json")
                    .read_text(encoding="utf-8"))
appels = []


def preparer(cas: str) -> dict:
    d = BAC / cas
    if d.exists():
        shutil.rmtree(d)
    (d / "sync").mkdir(parents=True)
    shutil.copyfile(REEL_MODULE, d / "sync" / "affaire_ledger.py")
    shutil.copyfile(REEL_DET, d / "sync" / "detachements_manuels.csv")
    (d / ".env").write_bytes(b"# .env FACTICE de l'essai (aucun secret)\nAPP_CHAINAGE_V2=1\nAPP_ETIQUETTE_DOSSIER=1\nUNE_CLE=une_valeur\n")
    V.MODULE, V.FICHIER_DET, V.ENV = d / "sync" / "affaire_ledger.py", d / "sync" / "detachements_manuels.csv", d / ".env"
    V.SCENES = d / "scenes"
    avant = {p.name: md5(p) for p in (V.MODULE, V.FICHIER_DET, V.ENV)}
    M = json.loads(json.dumps(M_REEL))
    if cas == "A":
        M["brouillon"]["md5"] = "0" * 32                       # la panne PENDANT la pose
    f = d / "manifeste.json"
    f.write_text(json.dumps(M, ensure_ascii=False), encoding="utf-8")
    return {"d": d, "avant": avant, "manifeste": f}


def leurres(cas: str):
    appels.clear()
    V.etape_0 = lambda M, a_blanc: appels.append("etape_0") or []
    V.jouer_sql = lambda q, quoi: appels.append("jouer_sql:%s" % quoi)

    def lancer(args, quoi):
        appels.append("lancer:%s" % quoi)
        if cas == "C" and "affaire_ledger.py" in args[0]:
            raise V.Refus("panne voulue PENDANT l'etape 5")
    V.lancer = lancer

    def etape_4(M, pose, attendu):
        appels.append("etape_4")
        if cas == "B":
            raise RuntimeError("panne voulue au point de non-retour (une erreur quelconque)")
        return [], {}
    V.etape_4 = etape_4
    V.etape_6 = lambda attendu: appels.append("etape_6") or []
    faux_p = types.ModuleType("protocole_classeur")

    class Cu:
        description = [types.SimpleNamespace(name="leurre")]

        def execute(self, q):
            appels.append("lecture_repetition")

        def fetchone(self):
            return ["-"]

    class Cn:
        def rollback(self):
            pass

        def close(self):
            pass
    faux_p.pooler = lambda: (Cn(), Cu())
    sys.modules["protocole_classeur"] = faux_p


def jouer(cas: str) -> bool:
    b = preparer(cas)
    leurres(cas)
    sys.argv = ["vague_du_soir.py", "--manifeste", str(b["manifeste"]), "--geste", "--accord", md5(b["manifeste"])]
    print("\n════ CAS %s ════" % cas)
    code = V.main()
    apres = {p.name: md5(p) for p in (V.MODULE, V.FICHIER_DET, V.ENV)}
    journal = next(iter((b["d"] / "scenes").glob("*/compte_rendu.txt"))).read_text(encoding="utf-8")
    remis = "TOUT EST REMIS COMME AVANT" in journal
    if cas in ("A", "B"):
        ok = code == 1 and remis and apres == b["avant"]
        print("-> CAS %s : code %s, remis %s, copies revenues a l'identique %s, appels %s => %s" % (
            cas, code, remis, apres == b["avant"], appels, "✅" if ok else "⛔"))
    elif cas == "C":
        ok = (code == 1 and not remis and "RIEN N'EST REMIS PAR LA MACHINE" in journal and apres != b["avant"])
        print("-> CAS C : code %s, remis %s, il le DIT %s, copies restent posees %s => %s" % (
            code, remis, "RIEN N'EST REMIS PAR LA MACHINE" in journal, apres != b["avant"], "✅" if ok else "⛔"))
    else:
        attendus = ["etape_0", "jouer_sql:sauvegardes chez Supabase", "lancer:la doublure du ledger", "etape_4",
                    "lancer:le chainage et sa poussee", "etape_6", "jouer_sql:A2", "jouer_sql:a1_patch", "jouer_sql:a3_patch",
                    "lecture_repetition", "lancer:la repartition"]
        pose_ok = ("10 lignes en moins, 0 ajoutee" in journal and "APP_CHAINAGE_DETACHEMENTS=1, APP_CHAINAGE_GARDE_G2=0" in journal
                   and apres["detachements_manuels.csv"] == M_REEL["brouillon"]["md5"])
        env_txt = V.ENV.read_text(encoding="utf-8")
        ok = code == 0 and appels == attendus and pose_ok and "9. ARRET" in journal and not remis
        print("-> CAS D : code %s, appels dans l'ordre %s, pose prouvee %s, .env pose = %r => %s" % (
            code, appels == attendus, pose_ok, env_txt, "✅" if ok else "⛔"))
        if appels != attendus:
            print("   appels : %s" % appels)
    return ok


def main() -> int:
    if BAC.exists():
        shutil.rmtree(BAC)
    r = {c: jouer(c) for c in ("A", "B", "C", "D")}
    reels = {p.name: md5(p) for p in (REEL_MODULE, REEL_DET)}
    print("\nLES VRAIS FICHIERS DU DEPOT, JAMAIS TOUCHES : %s" % reels)
    print("=> %s" % ("✅ LES QUATRE CAS RENDENT CE QUI EST ATTENDU" if all(r.values()) else "⛔ %s" % r))
    return 0 if all(r.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
