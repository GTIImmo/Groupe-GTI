#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CHANTIER 7, PIECE ① -- LE PUSH D'UNE SEULE ANNONCE REFUSE UN BROUILLON.
                                                                  20/10/2026

On fait tourner LA VRAIE fonction de push_single_annonce_to_supabase.py :
    est_un_brouillon(hektor_annonce_id)
sur des miroirs JETABLES, puis sur le vrai miroir EN LECTURE SEULE pour prouver
qu'elle nomme exactement les memes annonces que la clause du run de nuit.

RIEN N'EST ECRIT : aucun appel a Supabase, aucun appel a Hektor, et le vrai
miroir n'est ouvert qu'en mode=ro.

LA PREUVE D'ABORD (regle du projet) : le controle (1) exige que la fonction
RECONNAISSE un brouillon. S'il echoue, tous les suivants ne prouvent rien -- et
cet essai le dit au lieu de se declarer vert.

⚠ CE QU'IL FAUT SAVOIR POUR ECRIRE UN ESSAI SUR CETTE FONCTION. Elle lit le
  miroir A TRAVERS export_app_payload.load_brouillon_draft_ids(), donc le chemin
  qu'elle utilise est `export_app_payload.HEKTOR_DB`, PAS
  `push_single_annonce_to_supabase.HEKTOR_DB` que le harnais C.9-e echange. C'est
  volontaire : la question reste a UN SEUL endroit, celui dont le run de nuit se
  sert deja. Un essai doit donc echanger la constante de export_app_payload.

    python phase2/checks/test_piece1_brouillon_refuse.py
    sortie 0 = tout vert · 1 = un controle en echec · 2 = n'a pas pu mesurer
"""

from __future__ import annotations

import ast
import io
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))
from phase2.sync import push_single_annonce_to_supabase as ps  # noqa: E402
from phase2.sync import export_app_payload as ex  # noqa: E402

echecs: list[str] = []


def controle(nom: str, condition: bool, detail: str = "") -> None:
    print(f"{'  OK  ' if condition else 'ECHEC '} {nom}{'' if condition else ' -- ' + detail}")
    if not condition:
        echecs.append(nom)


DOSSIER = Path(tempfile.mkdtemp(prefix="piece1_"))


def miroir_jetable(nom: str, lignes: list[tuple[str, object]] | None) -> Path:
    """Un faux hektor.sqlite. lignes=None -> la table n'existe pas du tout."""
    chemin = DOSSIER / f"{nom}.sqlite"
    con = sqlite3.connect(chemin)
    if lignes is not None:
        con.execute("CREATE TABLE hektor_annonce_draft_state (hektor_annonce_id TEXT, is_draft INTEGER)")
        con.executemany("INSERT INTO hektor_annonce_draft_state VALUES (?, ?)", lignes)
    con.commit()
    con.close()
    return chemin


class MiroirEchange:
    """Echange export_app_payload.HEKTOR_DB le temps d'un controle, puis le remet."""

    def __init__(self, chemin: Path):
        self.chemin = chemin

    def __enter__(self):
        self.avant = ex.HEKTOR_DB
        ex.HEKTOR_DB = self.chemin
        return self

    def __exit__(self, *_):
        ex.HEKTOR_DB = self.avant
        return False


# ───────────────────────── (1) LA PREUVE D'ABORD ─────────────────────────
# Un miroir ou 63131 est un brouillon et 62774 n'en est pas un.
m1 = miroir_jetable("avec_table", [("63131", 1), ("62774", 0), ("63237", 1), ("61999", None)])
with MiroirEchange(m1):
    reconnait = ps.est_un_brouillon("63131")
    temoin_inverse = ps.est_un_brouillon("62774")
    is_draft_nul = ps.est_un_brouillon("61999")
    absente_du_miroir = ps.est_un_brouillon("99999")

controle("(1) LA PREUVE D'ABORD : un brouillon est RECONNU", reconnait is True, f"a rendu {reconnait!r}")
if not reconnait:
    print("\n⛔ LE CONTROLE (1) A ECHOUE : la fonction ne reconnait meme pas un brouillon.")
    print("   Tous les autres controles ne prouveraient RIEN. On s'arrete ici.")
    sys.exit(2)

controle("(2) TEMOIN INVERSE : une vraie annonce n'est PAS prise", temoin_inverse is False,
         f"a rendu {temoin_inverse!r}")
controle("(3) is_draft NULL = pas un brouillon (COALESCE, comme le run de nuit)",
         is_draft_nul is False, f"a rendu {is_draft_nul!r}")
controle("(4) annonce absente du miroir = pas un brouillon", absente_du_miroir is False,
         f"a rendu {absente_du_miroir!r}")

# ───────────────────── (5) LA TABLE N'EXISTE PAS ENCORE ─────────────────────
# Le projet a tranche : « builder inerte ». Elle ne doit PAS casser le read-through.
m2 = miroir_jetable("sans_table", None)
with MiroirEchange(m2):
    try:
        sans_table = ps.est_un_brouillon("63131")
        a_casse = False
    except Exception as exc:  # noqa: BLE001
        sans_table, a_casse = None, True
        print(f"       (exception : {exc})")
controle("(5) table absente : inerte, et le read-through ne casse PAS",
         a_casse is False and sans_table is False, f"casse={a_casse}, rendu={sans_table!r}")

# ───────────────────────── (6) L'INTERRUPTEUR ─────────────────────────
# APP_BROUILLON_BUCKET_ENABLED=0 doit rendre le garde-fou inerte, comme pour le run.
avant_drapeau = ps.BROUILLON_BUCKET_ENABLED
try:
    ps.BROUILLON_BUCKET_ENABLED = False
    with MiroirEchange(m1):
        eteint = ps.est_un_brouillon("63131")
finally:
    ps.BROUILLON_BUCKET_ENABLED = avant_drapeau
controle("(6) interrupteur eteint : le garde-fou est INERTE", eteint is False, f"a rendu {eteint!r}")
controle("(6 bis) et il est RALLUME apres l'essai", ps.BROUILLON_BUCKET_ENABLED is avant_drapeau)

# ──────────────────────── (7) LES ENTREES BIZARRES ────────────────────────
with MiroirEchange(m1):
    bizarres = {}
    for valeur in ("", "   ", "abc", "63131 ", " 63131", None, "63131.0"):
        try:
            bizarres[repr(valeur)] = ps.est_un_brouillon(valeur)
        except Exception as exc:  # noqa: BLE001
            bizarres[repr(valeur)] = f"CASSE: {exc}"
aucune_casse = not any(isinstance(v, str) for v in bizarres.values())
espaces_ok = bizarres.get("'63131 '") is True and bizarres.get("' 63131'") is True
vides_ok = all(bizarres.get(k) is False for k in ("''", "'   '", "'abc'", "None", "'63131.0'"))
controle("(7) entrees bizarres : aucune ne casse", aucune_casse, str(bizarres))
controle("(7 bis) les espaces autour du numero sont ignores", espaces_ok, str(bizarres))
controle("(7 ter) vide / texte / decimal = pas un brouillon", vides_ok, str(bizarres))

# ═══════════ (8) LA MESURE QUI COMPTE : MEME SOURCE QUE LE RUN DE NUIT ═══════════
# Les deux portes du parc vivant doivent nommer LES MEMES annonces. Sinon un
# brouillon passerait par l'une et pas par l'autre -- exactement le defaut qu'on
# corrige. Lecture seule sur le VRAI miroir et la VRAIE base.
VRAI_MIROIR = RACINE / "data" / "hektor.sqlite"
VRAIE_BASE = RACINE / "phase2" / "phase2.sqlite"
if not VRAI_MIROIR.exists() or not VRAIE_BASE.exists():
    print("\n⚠ (8) NON MESURE : le vrai miroir ou la vraie base est absent de cette machine.")
else:
    con = sqlite3.connect(f"file:{VRAIE_BASE.as_posix()}?mode=ro", uri=True, timeout=30)
    try:
        con.execute("ATTACH DATABASE ? AS hektor", (str(VRAI_MIROIR),))
        clause = ex.brouillon_active_exclusion_sql()
        # Ce que le run de nuit ECARTE = ce qui disparait quand on ajoute sa clause.
        ecartees_par_la_nuit = {
            int(r[0]) for r in con.execute(
                f"""SELECT hektor_annonce_id FROM app_view_generale
                      WHERE hektor_annonce_id IS NOT NULL
                    EXCEPT
                    SELECT hektor_annonce_id FROM app_view_generale
                      WHERE hektor_annonce_id IS NOT NULL{clause}"""
            ).fetchall()
        }
        dans_la_vue = {
            int(r[0]) for r in con.execute(
                "SELECT hektor_annonce_id FROM app_view_generale WHERE hektor_annonce_id IS NOT NULL"
            ).fetchall()
        }
    finally:
        con.close()

    refusees_par_la_garde = set(ex.load_brouillon_draft_ids()) & dans_la_vue

    manquantes = ecartees_par_la_nuit - refusees_par_la_garde
    en_trop = refusees_par_la_garde - ecartees_par_la_nuit
    print(f"\n       le run de nuit ecarte   : {len(ecartees_par_la_nuit)} annonces")
    print(f"       ma garde refuse         : {len(refusees_par_la_garde)} annonces")
    controle("(8) LES DEUX PORTES NOMMENT LES MEMES ANNONCES",
             not manquantes and not en_trop,
             f"{len(manquantes)} que la nuit ecarte et pas moi "
             f"{sorted(manquantes)[:5]} · {len(en_trop)} que je refuse et pas elle {sorted(en_trop)[:5]}")
    controle("(8 bis) et il y en a VRAIMENT (sinon on ne mesure rien)",
             len(ecartees_par_la_nuit) > 0, f"{len(ecartees_par_la_nuit)} ecartees")

# ═══════ (9) LE DICTIONNAIRE DE LA BRANCHE PORTE LES CLES QU'ON LUI DEMANDE ═══════
# A la fin du run, le compte rendu lit counts["dossiers_upserted"], ["details_upserted"]
# et ["work_items_replaced"]. Une cle oubliee = KeyError APRES le travail, donc un
# travail « failed » alors que tout s'est bien passe. Le temoin est la branche voisine
# qui marche depuis des mois : les deux dictionnaires doivent avoir LES MEMES CLES.
source = (RACINE / "phase2" / "sync" / "push_single_annonce_to_supabase.py").read_text(encoding="utf-8")
arbre = ast.parse(source)
dicos: dict[str, set[str]] = {}
for noeud in ast.walk(arbre):
    if isinstance(noeud, ast.Dict):
        cles = {k.value for k in noeud.keys if isinstance(k, ast.Constant) and isinstance(k.value, str)}
        if "dossiers_upserted" in cles:
            for marqueur in ("brouillon_skipped", "dirty_annonce_skipped"):
                if marqueur in cles:
                    dicos[marqueur] = cles

attendues = {"dossiers_upserted", "details_upserted", "work_items_replaced"}
garde = dicos.get("brouillon_skipped", set())
voisine = dicos.get("dirty_annonce_skipped", set())
controle("(9) la branche brouillon existe dans le code", bool(garde), str(sorted(dicos)))
controle("(9 bis) elle porte les 3 cles que le compte rendu lira",
         attendues <= garde, f"manque {sorted(attendues - garde)}")
controle("(9 ter) MEMES CLES que la branche voisine, au marqueur pres",
         bool(voisine) and (garde - {"brouillon_skipped"}) == (voisine - {"dirty_annonce_skipped"}),
         f"garde={sorted(garde)} · voisine={sorted(voisine)}")

print()
if echecs:
    print(f"{len(echecs)} controle(s) en ECHEC : " + ", ".join(echecs))
    sys.exit(1)
print("Le push d'une seule annonce refuse un brouillon -- et il refuse EXACTEMENT")
print("les memes que le run de nuit, par la meme source.")
