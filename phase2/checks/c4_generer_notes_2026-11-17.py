#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C4 (2e patch) -- LES NOTES DE F ET DE G, EN BLOC, SANS INTERPRETER.  17/11/2026

    .venv\\Scripts\\python.exe -X utf8 phase2\\checks\\c4_generer_notes_2026-11-17.py

⛔ CE SCRIPT N'ECRIT RIEN EN BASE. Il lit le Sheet et le rapport de C4, il MESURE, et
   il GENERE les trois fichiers SQL habituels.

SA CONSIGNE, DEPUIS LE 31/10 ET REPETEE LE 17/11 : **« en bloc, tels quels, sans
aucune interpretation »**. Donc on ne REFORMULE RIEN, on ne RESUME RIEN. Le texte du
classeur arrive tel qu'il est ecrit.

⛔⛔ LE PREALABLE QUE L'AUDIT DU 16/11 A TROUVE, ET IL COMMANDE TOUT CE PATCH :
  `app_affaire_note` porte DEJA **195 lignes `origine = 'classeur'`** -- les notes
  d'acquereur posees avec les 195 transactions de C5. Si ce patch utilisait la MEME
  valeur, les deux lots deviendraient **INDISCERNABLES**, et un retour arriere sur
  l'un emporterait l'autre.
  ➡ **C4 utilise `classeur:F` et `classeur:G`, jamais `classeur` seul.**
  ⭐ Et deux origines plutot qu'une : F et G ne disent pas la meme chose, et on doit
    pouvoir retirer l'une sans l'autre.

CE QUI ENTRE, et d'ou ca vient :
```
   de F  les textes des affaires ANNULEES qui ne sont PAS un des six motifs
         (y compris les 36 clefs repetees hors de sa table -- declarees)
   de F  les remarques des affaires REGLEES  (« V pb apres vente », « protocole »)
   de F  le FINANCEMENT                      (« 260K 25a », « relais »)
   de F  la DATE BUTOIR                      sa decision du 17/11 : DB va en note,
         parce qu'elle vaut « Vente Prevue » dans 60 cas sur 65
   de G  les COMMENTAIRES, tous
```
⛔ **CE QUI N'ENTRE PAS** : les 86 lignes des affaires EN COURS. Ce sont des
  CONDITIONS avec une echeance, pas des notes -- elles vont dans le 3e patch.
  Et les « V » seuls, les pictogrammes seuls, les prenoms : ECARTES (deja connus).
"""
from __future__ import annotations

import csv
import os
import sys
from collections import Counter
from datetime import date
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "phase2" / "checks"))
sys.path.insert(0, str(RACINE / "monitoring"))

import apparier_classeur as ap                                      # noqa: E402
import check_gti_health as cgh                                      # noqa: E402

DETAIL = RACINE / "notice" / "C4_LES_CLAUSES_DE_LA_COLONNE_F_2026-11-16.csv"
MOTIFS = RACINE / "notice" / "C4_LES_MOTIFS_RETENUS_2026-11-17.csv"
BASE = RACINE / "supabase" / "patch_c4_notes_2026-11-17"
RAPPORT = RACINE / "notice" / "C4_LES_NOTES_A_POSER_2026-11-17.csv"
LOT_API = 60

#: ⭐ La transaction la PLUS AVANCEE de la chaine porte la note. La table a aussi
#:   `app_chaine_id`, donc la note reste joignable au dossier entier.
RANG = {"vente": 3, "compromis": 2, "offre": 1}
MORTS = ("Annulée", "Annulee")
REGLES = ("Vente réglée", "Vente reglee")


def client():
    for f in (RACINE / ".env", RACINE / "backend" / ".env",
              RACINE / "apps" / "hektor-v1" / ".env"):
        if f.exists():
            cgh.load_env_file(f)
    url = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL")
    cle = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not (url and cle):
        raise SystemExit("⛔ pas d'identifiants Supabase -- rien n'est genere.")
    return cgh.SupabaseClient(url, cle, timeout_seconds=30)


def tout_lire(cl, table, select, ordre):
    out, debut = [], 0
    while True:
        r = cl.get(table, {"select": select, "limit": "1000",
                           "offset": str(debut), "order": ordre}) or []
        out.extend(r)
        if len(r) < 1000:
            return out
        debut += 1000


def index_de(lettre: str) -> int:
    n = 0
    for c in lettre:
        n = n * 26 + (ord(c) - 64)
    return n - 1


def txt(v) -> str:
    return "'" + str(v).replace("'", "''") + "'"


def main() -> int:
    ap.load_env_file(RACINE / ".env")
    print("=== C4 (2e patch) -- LES NOTES DE F ET DE G (lecture seule) ===")
    print()

    with DETAIL.open(encoding="utf-8-sig", newline="") as h:
        detail = list(csv.DictReader(h, delimiter=";"))
    with MOTIFS.open(encoding="utf-8-sig", newline="") as h:
        deja_motif = {x["id_unique"] for x in csv.DictReader(h, delimiter=";")}
    print("le rapport de F : %d cases . motifs deja poses : %d"
          % (len(detail), len(deja_motif)))

    # ─── CE QUI ENTRE, PAR SOURCE ────────────────────────────────────────────
    #: ⭐ chaque entree porte SA source, pour que la note dise d'ou elle vient
    de_f: dict[str, list[tuple[str, str]]] = {}
    comptes = Counter()
    for x in detail:
        ident, t = x["id_unique"], x["texte_seul"].strip()
        fam, etat = x["famille"], x["etat_actuel"]
        if not (ident and t):
            continue
        quoi = None
        if fam == "CLAUSE ou MOTIF" and etat in MORTS and ident not in deja_motif:
            quoi = "F : le texte de l'annulation"
        elif fam == "CLAUSE ou MOTIF" and etat in REGLES:
            quoi = "F : remarque d'apres-vente"
        elif fam.startswith("FINANCEMENT"):
            quoi = "F : le financement"
        if quoi:
            de_f.setdefault(ident, []).append((quoi, t))
            comptes[quoi] += 1
    #: la DATE BUTOIR -- sa decision du 17/11
    for x in detail:
        ident = x["id_unique"]
        import re
        m = re.search(r"(?<![A-Za-z])DB\s*(\d{1,2}\s*/\s*\d{1,2})", x["texte_seul"])
        if ident and m:
            de_f.setdefault(ident, []).append(("F : date butoir", "DB " + m.group(1)))
            comptes["F : date butoir"] += 1

    # ─── LA COLONNE G, lue au Sheet ──────────────────────────────────────────
    entetes_bruts, lignes = ap.lire_classeur()
    entetes = [str(c or "").strip() for c in entetes_bruts]
    if len(lignes) < 3000:
        print("⛔ LECTURE RATEE : %d lignes. ON NE CONCLUT RIEN." % len(lignes))
        return 2
    i_g, i_id = index_de("G"), entetes.index("ID Unique")
    de_g: dict[str, str] = {}
    for _rang, l in lignes:
        g = str(l[i_g] if i_g < len(l) else "").strip()
        ident = str(l[i_id] if i_id < len(l) else "").strip()
        if g and ident:
            de_g[ident] = g
    comptes["G : le commentaire"] = len(de_g)
    print()
    print("=== CE QUI ENTRE, PAR SOURCE ===")
    for k, n in comptes.most_common():
        print("   %-34s %5d" % (k, n))
    print("   %-34s %5d" % ("TOTAL", sum(comptes.values())))

    #: ⛔ LE TEMOIN POSITIF sur G : A1 en comptait 4 131.
    if len(de_g) < 3500:
        print()
        print("⛔ TEMOIN POSITIF EN ECHEC sur G : %d, attendu ~4 131." % len(de_g))
        return 2

    # ─── LA CIBLE ────────────────────────────────────────────────────────────
    cl = client()
    liens = tout_lire(cl, "app_classeur_lien", "id_unique,app_affaire_id", "ligne_classeur")
    par_id: dict[str, list[int]] = {}
    for r in liens:
        par_id.setdefault(str(r["id_unique"]).strip(), []).append(r["app_affaire_id"])
    vises = set(de_f) | set(de_g)
    besoin = sorted({a for i in vises for a in par_id.get(i, [])})
    rows = []
    for i in range(0, len(besoin), LOT_API):
        lot = besoin[i:i + LOT_API]
        rows.extend(cl.get("app_affaire_ledger",
                           {"select": "app_affaire_id,kind,hektor_annonce_id,"
                                      "app_dossier_id,app_chaine_id",
                            "app_affaire_id": "in.(%s)" % ",".join(map(str, lot))}) or [])
    ledger = {str(r["app_affaire_id"]): r for r in rows}

    # ⛔⛔ LA CLE PRIMAIRE DE `app_affaire_note` EST `app_affaire_id` SEUL --
    #   mesure du 17/11, apres que ma premiere version ait ete REJETEE :
    #   « duplicate key value violates unique constraint app_affaire_note_pkey ».
    #   DONC : UNE SEULE NOTE PAR TRANSACTION. 204 notes pour 204 transactions,
    #   c'est la regle de la table et pas un hasard.
    #   ➡ TROIS consequences, toutes traitees ici :
    #     1. les textes d'une meme ligne (F et G) sont FUSIONNES en UNE note,
    #        chacun prefixe de SA source -- rien n'est perdu, rien n'est melange ;
    #     2. on vise une transaction LIBRE de la chaine quand la plus avancee porte
    #        deja une note (les 195 de C5, les 9 saisies) -- additif, jamais un
    #        ecrasement ;
    #     3. si TOUTE la chaine est prise, on ECARTE et on COMPTE. On ne touche
    #        JAMAIS a une note existante : celles de C5 sont a elles.
    occupees = {str(r["app_affaire_id"]) for r in tout_lire(
        cl, "app_affaire_note", "app_affaire_id,origine", "app_affaire_id")}
    print()
    print("transactions portant DEJA une note : %d (les 195 de C5 + 9 saisies)"
          % len(occupees))

    notes, sans_lien, toute_prise = [], 0, 0
    for ident in sorted(vises):
        trs = [ledger[str(a)] for a in par_id.get(ident, []) if str(a) in ledger]
        if not trs:
            sans_lien += 1
            continue
        libres = [r for r in trs if str(r["app_affaire_id"]) not in occupees]
        if not libres:
            toute_prise += 1
            continue
        t = max(libres, key=lambda r: RANG.get(str(r.get("kind")), 0))
        occupees.add(str(t["app_affaire_id"]))      # une seule note par transaction
        # ⭐ LA FUSION : chaque morceau garde SA source en tete, et l'ordre est
        #   stable (F d'abord, G ensuite) pour que deux executions donnent le
        #   MEME texte -- sinon la repetition ne pourrait rien comparer.
        morceaux = ["%s -- %s" % (quoi, texte) for quoi, texte in de_f.get(ident, [])]
        if ident in de_g:
            morceaux.append("G : le commentaire -- " + de_g[ident])
        origine = ("classeur:F+G" if (de_f.get(ident) and ident in de_g)
                   else "classeur:G" if ident in de_g else "classeur:F")
        notes.append({"app_affaire_id": t["app_affaire_id"],
                      "app_dossier_id": t.get("app_dossier_id"),
                      "app_chaine_id": t.get("app_chaine_id"),
                      "origine": origine, "morceaux": len(morceaux),
                      "texte": "\n".join(morceaux), "id_unique": ident})

    print()
    print("=== LE TRI ===")
    print("✅ notes posables (UNE par transaction) : %5d" % len(notes))
    print("⛔ lignes sans aucun lien au gel        : %5d  (hors de portee, A6)" % sans_lien)
    print("⚠  toute la chaine porte deja une note  : %5d  -> ECARTEES, jamais ecrasees"
          % toute_prise)
    print("   morceaux fusionnes : %d textes dans %d notes"
          % (sum(x["morceaux"] for x in notes), len(notes)))
    print()
    for k, n in Counter(x["origine"] for x in notes).most_common():
        print("   %-18s %5d" % (k, n))
    print()
    print("   la note la plus longue : %d caracteres"
          % max(len(x["texte"]) for x in notes))

    with RAPPORT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, delimiter=";", fieldnames=list(notes[0]))
        w.writeheader()
        w.writerows(notes)
    print()
    print("ecrit : %s" % RAPPORT)

    n = len(notes)
    n_f = sum(1 for x in notes if x["origine"] == "classeur:F")
    n_g = sum(1 for x in notes if x["origine"] == "classeur:G")
    n_fg = sum(1 for x in notes if x["origine"] == "classeur:F+G")
    valeurs = ",\n    ".join(
        "(%d, %s, %s, %s, %s)"
        % (x["app_affaire_id"],
           x["app_dossier_id"] if x["app_dossier_id"] else "NULL",
           x["app_chaine_id"] if x["app_chaine_id"] else "NULL",
           txt(x["origine"]), txt(x["texte"]))
        for x in notes)

    patch = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- C4 (2e patch) -- LES {n} NOTES DE F ET DE G, EN BLOC, SANS INTERPRETER
-- Genere le {date.today().isoformat()} par phase2/checks/c4_generer_notes_2026-11-17.py
--
-- SA CONSIGNE, depuis le 31/10 : « en bloc, tels quels, SANS AUCUNE
-- INTERPRETATION ». Aucun texte n'est reformule ni resume.
--
-- ⛔⛔ ET LE PREALABLE QUE L'AUDIT DU 16/11 A TROUVE, TRAITE ICI :
--   `app_affaire_note` porte DEJA **195 lignes `origine = 'classeur'`** -- les
--   notes d'acquereur posees avec les 195 transactions de C5. Si ce patch utilisait
--   la meme valeur, les deux lots seraient INDISCERNABLES et un retour arriere sur
--   l'un emporterait l'autre.
--   ➡ CE PATCH UTILISE `classeur:F` ({n_f}) ET `classeur:G` ({n_g}),
--     JAMAIS `classeur` seul. Deux origines et non une, parce que F et G ne disent
--     pas la meme chose et qu'on doit pouvoir retirer l'une sans l'autre.
--
-- CE QUI ENTRE :
--   de F  le texte des annulations qui n'est PAS un des six motifs (y compris les
--         36 clefs repetees hors de sa table -- declarees, pas absorbees)
--   de F  les remarques d'apres-vente . le FINANCEMENT . la DATE BUTOIR
--         (sa decision du 17/11 : DB va en note, elle vaut « Vente Prevue »
--          dans 60 cas sur 65)
--   de G  tous les commentaires
--
-- ⛔ CE QUI N'ENTRE PAS : les 86 lignes des affaires EN COURS -- ce sont des
--   CONDITIONS avec une echeance, pas des notes (3e patch). Et les « V » seuls,
--   les pictogrammes, les prenoms : ECARTES, deja connus.
--
-- Retour arriere : patch_c4_notes_2026-11-17_INVERSE.sql
-- Controle       : patch_c4_notes_2026-11-17_REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════

begin;

-- ─── 1. L'ETAT D'AVANT, EXIGE ──────────────────────────────────────────────
do $$
declare c5 integer; deja integer;
begin
  select count(*) into c5 from public.app_affaire_note where origine = 'classeur';
  if c5 <> 195 then
    raise exception '⛔ ARRET : % notes `classeur` au lieu des 195 de C5. L''etat '
      'd''avant n''est pas celui que j''ai mesure.', c5;
  end if;
  select count(*) into deja from public.app_affaire_note
   where origine in ('classeur:F', 'classeur:G', 'classeur:F+G');
  if deja <> 0 then
    raise exception '⛔ ARRET : % note(s) de C4 deja posee(s).', deja;
  end if;
  raise notice '✅ etat d''avant : 195 notes de C5, 0 note de C4.';
end $$;

-- ─── 2. LA POSE ────────────────────────────────────────────────────────────
insert into public.app_affaire_note
       (app_affaire_id, app_dossier_id, app_chaine_id, origine, texte, ecrit_par)
select v.aff, v.dossier, v.chaine, v.origine, v.texte, 'classeur:C4:2026-11-17'
  from (values
    {valeurs}
  ) as v(aff, dossier, chaine, origine, texte);

-- ─── 3. LES CONTROLES, ET ILS ARRETENT ─────────────────────────────────────
do $$
declare
  f integer; g integer; fg integer; c5 integer; vides integer; marque integer;
begin
  select count(*) into f from public.app_affaire_note where origine = 'classeur:F';
  select count(*) into g from public.app_affaire_note where origine = 'classeur:G';
  select count(*) into fg from public.app_affaire_note where origine = 'classeur:F+G';
  if f <> {n_f} or g <> {n_g} or fg <> {n_fg} then
    raise exception '⛔ attendu F {n_f} / G {n_g} / F+G {n_fg}, obtenu % / % / %.',
      f, g, fg;
  end if;

  -- ⭐⭐ LE TEMOIN QUI JUSTIFIE TOUT LE PREALABLE : les 195 notes de C5 doivent
  --   etre INTACTES et TOUJOURS DISCERNABLES.
  select count(*) into c5 from public.app_affaire_note where origine = 'classeur';
  if c5 <> 195 then
    raise exception '⛔⛔ % notes `classeur` au lieu de 195 : le patch a touche '
      'au lot de C5. GRAVE.', c5;
  end if;

  select count(*) into vides from public.app_affaire_note
   where origine in ('classeur:F','classeur:G','classeur:F+G') and btrim(coalesce(texte,'')) = '';
  if vides <> 0 then
    raise exception '⛔ % note(s) vide(s).', vides;
  end if;

  select count(*) into marque from public.app_affaire_note
   where origine in ('classeur:F','classeur:G','classeur:F+G')
     and ecrit_par is distinct from 'classeur:C4:2026-11-17';
  if marque <> 0 then
    raise exception '⛔ % note(s) sans la marque du lot.', marque;
  end if;

  raise notice '✅ F {n_f} . G {n_g} . F+G {n_fg} . LES 195 DE C5 INTACTES . '
    '0 vide . 0 sans marque.';
end $$;

commit;
"""

    inverse = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- C4 (2e patch) -- RETOUR ARRIERE
-- ⭐⭐ ET C'EST ICI QUE LE PREALABLE PAIE : il suffit de viser `classeur:F` et
--   `classeur:G`. Sans ces deux origines distinctes, il aurait fallu viser
--   `classeur` -- et EMPORTER LES 195 NOTES DE C5 avec.
-- ═══════════════════════════════════════════════════════════════════════════

begin;

do $$
declare n integer;
begin
  select count(*) into n from public.app_affaire_note
   where origine in ('classeur:F','classeur:G','classeur:F+G');
  if n <> {n} then
    raise exception '⛔ ARRET : % notes de C4 au lieu de {n}.', n;
  end if;
  raise notice '✅ {n} notes de C4 retrouvees.';
end $$;

delete from public.app_affaire_note
 where origine in ('classeur:F', 'classeur:G', 'classeur:F+G')
   and ecrit_par = 'classeur:C4:2026-11-17';

do $$
declare reste integer; c5 integer;
begin
  select count(*) into reste from public.app_affaire_note
   where origine in ('classeur:F','classeur:G','classeur:F+G');
  if reste <> 0 then
    raise exception '⛔ il reste % note(s) de C4.', reste;
  end if;
  select count(*) into c5 from public.app_affaire_note where origine = 'classeur';
  if c5 <> 195 then
    raise exception '⛔⛔ % notes de C5 au lieu de 195 : LE RETOUR ARRIERE A '
      'DEBORDE. GRAVE.', c5;
  end if;
  raise notice '✅ {n} notes retirees . LES 195 DE C5 SONT INTACTES.';
end $$;

commit;
"""

    repetition = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- C4 (2e patch) -- LES CONTROLES, REJOUABLES. Aucune ecriture.
-- ═══════════════════════════════════════════════════════════════════════════

select 'notes de F' as controle, count(*)::text as mesure, '{n_f}' as attendu
  from public.app_affaire_note where origine = 'classeur:F'
union all
select 'notes de G', count(*)::text, '{n_g}'
  from public.app_affaire_note where origine = 'classeur:G'
union all
select 'notes de F+G (une ligne qui porte les deux)', count(*)::text, '{n_fg}'
  from public.app_affaire_note where origine = 'classeur:F+G'
union all
select '⭐ LES 195 NOTES DE C5, INTACTES ET DISCERNABLES', count(*)::text, '195'
  from public.app_affaire_note where origine = 'classeur'
union all
select 'aucune note vide', count(*)::text, '0'
  from public.app_affaire_note
 where origine in ('classeur:F','classeur:G','classeur:F+G') and btrim(coalesce(texte,'')) = ''
union all
select 'toutes portent la marque du lot', count(*)::text, '0'
  from public.app_affaire_note
 where origine in ('classeur:F','classeur:G','classeur:F+G')
   and ecrit_par is distinct from 'classeur:C4:2026-11-17'
union all
select 'toutes rattachees a une CHAINE', count(*)::text, '0'
  from public.app_affaire_note
 where origine in ('classeur:F','classeur:G','classeur:F+G') and app_chaine_id is null
union all
select 'textes DISTINCTS (le vocabulaire est varie)',
       count(distinct texte)::text, 'proche du total'
  from public.app_affaire_note where origine in ('classeur:F','classeur:G','classeur:F+G')
union all
select 'VOISINES -- les 169 motifs de C4', count(*)::text, '169'
  from public.app_affaire_ledger where motif_annulation_app is not null
union all
select 'VOISINES -- les 450 dates de C3', count(*)::text, '450'
  from public.app_affaire_ledger where date_annulation_app is not null
order by 1;
"""

    for suffixe, contenu in ((".sql", patch), ("_INVERSE.sql", inverse),
                             ("_REPETITION.sql", repetition)):
        f = Path(str(BASE) + suffixe)
        f.write_bytes(contenu.encode("utf-8"))
        print("ecrit : %-50s %8d octets" % (f.name, len(f.read_bytes())))
    print()
    print("⛔ RIEN N'A ETE JOUE. Ces trois fichiers attendent un « colle ».")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
