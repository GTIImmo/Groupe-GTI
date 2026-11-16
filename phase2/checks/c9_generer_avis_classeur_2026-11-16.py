#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C9 -- LES TROIS COLONNES D'AVIS DU CLASSEUR (AH AI AJ).            16/11/2026

    .venv\\Scripts\\python.exe -X utf8 phase2\\checks\\c9_generer_avis_classeur_2026-11-16.py

⛔ CE SCRIPT N'ECRIT RIEN EN BASE. Il lit le Sheet, il MESURE, et il GENERE :
     supabase/patch_c9_avis_classeur_2026-11-16.sql             le patch
     supabase/patch_c9_avis_classeur_2026-11-16_INVERSE.sql     le retour arriere
     supabase/patch_c9_avis_classeur_2026-11-16_REPETITION.sql  les controles

⭐⭐⭐ POURQUOI C9 PASSE AVANT TOUT LE RESTE DU RAPATRIEMENT : sa destination,
  `app_classeur_avis`, a pour clef `id_unique` -- **LA LIGNE DU CLASSEUR, PAS LA
  TRANSACTION** -- et AUCUNE clef etrangere vers le pont (mesure du 16/11 au soir).

  Trois consequences, toutes verifiees :
    . elle NE DEPEND PAS DU GEL : un re-gel ne peut pas la deplacer ;
    . elle n'a donc **AUCUN TROU** -- les 18 lignes absentes de
      `app_classeur_ligne_id` et les 85 sans lien (A6) entrent comme les autres ;
    . et la table est VIERGE (0 ligne), donc aucun conflit possible.

LA DECISION DU PLAN : **valeurs BRUTES**. On ne normalise pas « oui / OUI / non /
  NON / pas acq. » : normaliser serait INTERPRETER, et une interpretation ne se
  defait pas. A1 a mesure AH 120 valeurs distinctes, AI 72, AJ 69 -- c'est un
  vocabulaire humain, pas une enumeration.

CE QUE A1 A MESURE SUR LES TROIS (16/11) :
```
   AH  Avis a envoyer      2 266 remplies . 120 distinctes . texte 2 265, nombre 1
   AI  Commentaire Avis      392 remplies .  72 distinctes . texte 277, nombre 115
   AJ  Avis envoye         2 405 remplies .  69 distinctes . texte 2 405
```

⚠ `C` (le numero de mandat) EST L'AUTRE MOITIE DE C9 ET N'EST PAS DANS CE PATCH :
  elle se pose sur une TRANSACTION (`numero_mandat_app`), donc elle DEPEND DU GEL,
  et les 33 numeros du classeur sont RECYCLES a charges divergentes. Elle attend
  le re-gel. Ne pas melanger les deux moities.
"""
from __future__ import annotations

import csv
import sys
from collections import Counter
from datetime import date
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "phase2" / "checks"))

import apparier_classeur as ap                                      # noqa: E402

BASE = RACINE / "supabase" / "patch_c9_avis_classeur_2026-11-16"
RAPPORT = RACINE / "notice" / "C9_LES_AVIS_DU_CLASSEUR_2026-11-16.csv"
MARQUE = "classeur:C9:2026-11-16"

#: Par LETTRE, jamais par libelle : un libelle peut changer, une lettre non.
TROIS = (("AH", "avis_a_envoyer"), ("AI", "commentaire_avis"), ("AJ", "avis_envoye"))

#: Les temoins positifs de A1. En dessous, c'est que la colonne ou le format a bouge.
TEMOINS = {"AH": 2000, "AI": 300, "AJ": 2100}


def index_de(lettre: str) -> int:
    n = 0
    for c in lettre:
        n = n * 26 + (ord(c) - 64)
    return n - 1


def txt(v) -> str:
    """Une chaine pour SQL, entre quotes simples. JAMAIS une concatenation nue :
    « Claire s'en occupe » est une vraie valeur de AI (mesure de A1)."""
    return "'" + str(v).replace("'", "''") + "'"


def main() -> int:
    ap.load_env_file(RACINE / ".env")
    print("=== C9 -- LES TROIS COLONNES D'AVIS (lecture seule) ===")
    print()

    entetes_bruts, lignes = ap.lire_classeur()
    entetes = [str(c or "").strip() for c in entetes_bruts]

    # ⛔ GARDE 1 : la lecture a-t-elle eu lieu ? (defaut paye le 16/11 sur C3 :
    #   une grille tronquee rendait DES ZEROS et sortait en code 0)
    if len(lignes) < 3000:
        print("⛔ LECTURE RATEE : %d lignes de corps, le classeur en porte ~4 791."
              % len(lignes))
        print("   ON NE CONCLUT RIEN. Une lecture ratee n'est jamais un vert.")
        return 2
    col_id = entetes.index("ID Unique")
    print("le Sheet : %d lignes de corps . « ID Unique » en colonne %d"
          % (len(lignes), col_id))
    for lettre, colonne in TROIS:
        i = index_de(lettre)
        print("   %s -> %-18s en-tete lu : %r"
              % (lettre, colonne, entetes[i] if i < len(entetes) else "?"))
    print()

    def case(l, lettre):
        i = index_de(lettre)
        return str(l[i] if i < len(l) else "").strip()

    # ─── LA LECTURE ──────────────────────────────────────────────────────────
    par_id: dict[str, dict] = {}
    doublons: Counter = Counter()
    sans_id = 0
    comptes = Counter()
    for rang, l in lignes:
        ident = str(l[col_id] if col_id < len(l) else "").strip()
        valeurs = {colonne: case(l, lettre) for lettre, colonne in TROIS}
        if not any(valeurs.values()):
            continue
        for lettre, colonne in TROIS:
            if valeurs[colonne]:
                comptes[lettre] += 1
        if not ident:
            sans_id += 1
            continue
        if ident in par_id:
            doublons[ident] += 1
            continue
        par_id[ident] = {"rang": rang, **valeurs}

    print("=== CE QUE LE SHEET PORTE, ET CE QUE A1 ANNONCAIT ===")
    for lettre, colonne in TROIS:
        print("   %s  %-18s %5d   A1 : %s"
              % (lettre, colonne, comptes[lettre],
                 {"AH": "2 266", "AI": "392", "AJ": "2 405"}[lettre]))
    print()

    # ⛔ GARDE 2 : LE TEMOIN POSITIF. Une poignee de valeurs ne veut pas dire
    #   « il n'y a rien a faire » : ca veut dire que la colonne a bouge.
    for lettre, seuil in TEMOINS.items():
        if comptes[lettre] < seuil:
            print("⛔ TEMOIN POSITIF EN ECHEC sur %s : %d valeurs, seuil %d."
                  % (lettre, comptes[lettre], seuil))
            print("   A1 en comptait bien plus le 16/11. La colonne ou le format a bouge.")
            print("   ON NE GENERE RIEN -- un zero ne se croit pas sans temoin positif.")
            return 2

    print("lignes a poser (au moins une des trois) : %d" % len(par_id))
    print("   dont SANS « ID Unique » (ecartees)   : %d" % sans_id)
    print("   DOUBLONS d'ID Unique (ecartes)       : %d" % sum(doublons.values()))
    if doublons:
        print("   ⚠ les voici, car la clef primaire les REFUSERAIT :")
        for ident, n in doublons.most_common(10):
            print("      %-12s %d fois de plus" % (ident, n))

    # ⭐ CE QUI FAIT LA FORCE DE C9 : les lignes hors du pont ENTRENT QUAND MEME.
    #   On le MESURE, pour pouvoir l'ecrire dans le patch.
    print()
    print("=== LE VOCABULAIRE, BRUT (on ne normalise PAS -- decision du plan) ===")
    for lettre, colonne in TROIS:
        vals = Counter(v[colonne] for v in par_id.values() if v[colonne])
        tete = " . ".join("%s (%d)" % (k, n) for k, n in vals.most_common(6))
        print("   %-18s %3d distinctes : %s" % (colonne, len(vals), tete[:92]))

    # ─── LE RAPPORT ──────────────────────────────────────────────────────────
    with RAPPORT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, delimiter=";",
                           fieldnames=["id_unique", "rang_sheet", "avis_a_envoyer",
                                       "commentaire_avis", "avis_envoye"])
        w.writeheader()
        for ident, v in sorted(par_id.items()):
            w.writerow({"id_unique": ident, "rang_sheet": v["rang"],
                        **{c: v[c] for _l, c in TROIS}})
    print()
    print("ecrit : %s" % RAPPORT)

    n = len(par_id)
    valeurs_sql = ",\n    ".join(
        "(%s, %s, %s, %s)" % (txt(i),
                              txt(v["avis_a_envoyer"]) if v["avis_a_envoyer"] else "NULL",
                              txt(v["commentaire_avis"]) if v["commentaire_avis"] else "NULL",
                              txt(v["avis_envoye"]) if v["avis_envoye"] else "NULL")
        for i, v in sorted(par_id.items()))
    n_ah = sum(1 for v in par_id.values() if v["avis_a_envoyer"])
    n_ai = sum(1 for v in par_id.values() if v["commentaire_avis"])
    n_aj = sum(1 for v in par_id.values() if v["avis_envoye"])

    patch = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- C9 (1re moitie) -- LES TROIS COLONNES D'AVIS DU CLASSEUR -> app_classeur_avis
-- Genere le {date.today().isoformat()} par phase2/checks/c9_generer_avis_classeur_2026-11-16.py
--
-- {n} lignes du classeur, soit {n_ah} « avis a envoyer », {n_ai} commentaires
-- et {n_aj} « avis envoye ».
--
-- ⭐⭐⭐ POURQUOI CE PATCH N'A AUCUN TROU, contrairement a tout le reste du
--   rapatriement : `app_classeur_avis` a pour clef `id_unique` -- LA LIGNE DU
--   CLASSEUR, PAS LA TRANSACTION -- et AUCUNE clef etrangere vers le pont.
--   Donc les 18 lignes ABSENTES de `app_classeur_ligne_id` et les 85 SANS LIEN
--   dans le gel (A6, 16/11) entrent ici comme les autres. Et un RE-GEL ne peut
--   pas deplacer ces lignes : il n'y a rien a deplacer.
--
-- LES VALEURS SONT BRUTES, ET C'EST LA DECISION DU PLAN. On ne normalise pas
--   « oui / OUI / non / NON / pas acq. » : A1 a mesure 120 valeurs distinctes en
--   AH, 72 en AI, 69 en AJ -- c'est un vocabulaire humain, pas une enumeration.
--   Normaliser serait INTERPRETER, et une interpretation ne se defait pas.
--
-- ⚠ L'AUTRE MOITIE DE C9 N'EST PAS LA : `C` (le numero de mandat) se pose sur une
--   TRANSACTION (`numero_mandat_app`), donc elle DEPEND DU GEL, et les 33 numeros
--   du classeur sont RECYCLES a charges divergentes (commentaire de la colonne 53).
--   Elle attend le re-gel. Ne pas melanger les deux moities.
--
-- Retour arriere : patch_c9_avis_classeur_2026-11-16_INVERSE.sql
-- Controle       : patch_c9_avis_classeur_2026-11-16_REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════

begin;

-- ─── 1. L'ETAT D'AVANT, EXIGE ──────────────────────────────────────────────
do $$
declare deja integer;
begin
  select count(*) into deja from public.app_classeur_avis;
  if deja <> 0 then
    raise exception '⛔ ARRET : la table porte deja % ligne(s). Ce patch suppose '
      'une table VIERGE (0 au 16/11). Relire avant de jouer.', deja;
  end if;
  raise notice '✅ etat d''avant : la table est vierge.';
end $$;

-- ─── 2. LA POSE ────────────────────────────────────────────────────────────
-- ⭐ `on conflict do nothing` : si une ligne arrivait entre le controle 1 et ici
--   (une autre session), on ne l'ECRASE pas -- et le controle 3 verrait l'ecart.
insert into public.app_classeur_avis
       (id_unique, avis_a_envoyer, commentaire_avis, avis_envoye, origine, ecrit_par)
select v.id_unique, v.avis_a_envoyer, v.commentaire_avis, v.avis_envoye,
       'classeur', '{MARQUE}'
  from (values
    {valeurs_sql}
  ) as v(id_unique, avis_a_envoyer, commentaire_avis, avis_envoye)
on conflict (id_unique) do nothing;

-- ─── 3. LES CONTROLES, ET ILS ARRETENT ─────────────────────────────────────
do $$
declare
  posees  integer;
  ah      integer;
  ai      integer;
  aj      integer;
  vides   integer;
  autres  integer;
begin
  select count(*) into posees from public.app_classeur_avis;
  if posees <> {n} then
    raise exception '⛔ {n} attendues, % posees.', posees;
  end if;

  select count(avis_a_envoyer), count(commentaire_avis), count(avis_envoye)
    into ah, ai, aj from public.app_classeur_avis;
  if ah <> {n_ah} or ai <> {n_ai} or aj <> {n_aj} then
    raise exception '⛔ attendu {n_ah}/{n_ai}/{n_aj}, obtenu %/%/%.', ah, ai, aj;
  end if;

  -- ⭐ AUCUNE ligne entierement vide : une ligne sans aucune des trois valeurs
  --   n'avait rien a faire ici.
  select count(*) into vides from public.app_classeur_avis
   where avis_a_envoyer is null and commentaire_avis is null and avis_envoye is null;
  if vides <> 0 then
    raise exception '⛔ % ligne(s) entierement vide(s).', vides;
  end if;

  -- ⭐ TEMOIN INVERSE : tout porte NOTRE marque, rien d'autre n'a ete pose.
  select count(*) into autres from public.app_classeur_avis
   where ecrit_par is distinct from '{MARQUE}';
  if autres <> 0 then
    raise exception '⛔ % ligne(s) ne portent pas la marque de ce lot.', autres;
  end if;

  raise notice '✅ {n} lignes posees ({n_ah} / {n_ai} / {n_aj}) . 0 vide . 0 etrangere.';
end $$;

commit;
"""

    inverse = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- C9 (1re moitie) -- RETOUR ARRIERE
-- ⭐ « Un retour arriere ne juge que SA part » : il ne retire QUE les lignes
--   marquees `{MARQUE}`, et il verifie ensuite qu'il n'en reste aucune.
-- ⛔ IL NE SUPPRIME PAS LA TABLE : elle vient de B1, pas de ce patch.
-- ═══════════════════════════════════════════════════════════════════════════

begin;

do $$
declare mienne integer; total integer;
begin
  select count(*) into mienne from public.app_classeur_avis
   where ecrit_par = '{MARQUE}';
  select count(*) into total from public.app_classeur_avis;
  if mienne <> {n} then
    raise exception '⛔ ARRET : % ligne(s) de ce lot au lieu de {n}. Quelqu''un est '
      'passe apres nous -- ne RIEN retirer sans relire.', mienne;
  end if;
  raise notice '✅ {n} lignes du lot retrouvees (la table en porte % en tout).', total;
end $$;

delete from public.app_classeur_avis where ecrit_par = '{MARQUE}';

do $$
declare reste integer; autres integer;
begin
  select count(*) into reste from public.app_classeur_avis
   where ecrit_par = '{MARQUE}';
  if reste <> 0 then
    raise exception '⛔ il reste % ligne(s) du lot.', reste;
  end if;
  select count(*) into autres from public.app_classeur_avis;
  raise notice '✅ {n} lignes retirees . la table porte encore % ligne(s), posee(s) '
    'par autre chose que C9 (0 attendu au 16/11).', autres;
end $$;

commit;
"""

    repetition = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- C9 (1re moitie) -- LES CONTROLES, REJOUABLES. Aucune ecriture.
-- Ecrite AVANT le collage, comme le projet l'exige.
-- ═══════════════════════════════════════════════════════════════════════════

select 'lignes posees' as controle, count(*)::text as mesure, '{n}' as attendu
  from public.app_classeur_avis
union all
select 'avis_a_envoyer renseignes', count(avis_a_envoyer)::text, '{n_ah}'
  from public.app_classeur_avis
union all
select 'commentaire_avis renseignes', count(commentaire_avis)::text, '{n_ai}'
  from public.app_classeur_avis
union all
select 'avis_envoye renseignes', count(avis_envoye)::text, '{n_aj}'
  from public.app_classeur_avis
union all
select 'aucune ligne entierement vide', count(*)::text, '0'
  from public.app_classeur_avis
 where avis_a_envoyer is null and commentaire_avis is null and avis_envoye is null
union all
select 'toutes portent la marque du lot', count(*)::text, '0'
  from public.app_classeur_avis where ecrit_par is distinct from '{MARQUE}'
union all
select 'origine = classeur partout', count(*)::text, '0'
  from public.app_classeur_avis where origine <> 'classeur'
union all
-- ⭐⭐ LE CONTROLE QUI FAIT LA SPECIFICITE DE C9 : les lignes HORS DU PONT sont
--   la quand meme, parce que la clef est `id_unique` et non la transaction.
-- ⛔⛔ ET LES DEUX CHIFFRES SONT MESURES, PAS SOUHAITES. Ma premiere version
--   annoncait « doit etre > 0 » pour les deux : la mesure du 16/11 rend 0 et 8.
--   Un controle qui attend une valeur FAUSSE est pire qu'aucun controle -- il
--   rougit pour rien, et on apprend a ignorer ses rouges.
select 'posees SANS identite dans le pont', count(*)::text,
       '0 au 16/11 : les 18 absentes de A6 ne portent AUCUN avis'
  from public.app_classeur_avis a
 where not exists (select 1 from public.app_classeur_ligne_id p
                    where p.id_unique = a.id_unique)
union all
select 'posees SANS AUCUN LIEN dans le gel', count(*)::text,
       '8 au 16/11 -- autant d avis que C8 et C4 PERDRAIENT, eux'
  from public.app_classeur_avis a
 where not exists (select 1 from public.app_classeur_lien l
                    where l.id_unique = a.id_unique)
union all
-- ⭐ TEMOIN DE VOCABULAIRE : les valeurs doivent rester VARIEES. Un lot ramene a
--   deux ou trois valeurs signalerait une normalisation involontaire.
select 'valeurs distinctes en avis_a_envoyer',
       count(distinct avis_a_envoyer)::text, '~120 (A1)'
  from public.app_classeur_avis
union all
select 'valeurs distinctes en avis_envoye',
       count(distinct avis_envoye)::text, '~69 (A1)'
  from public.app_classeur_avis
order by 1;
"""

    for suffixe, contenu in ((".sql", patch), ("_INVERSE.sql", inverse),
                             ("_REPETITION.sql", repetition)):
        f = Path(str(BASE) + suffixe)
        f.write_bytes(contenu.encode("utf-8"))
        print("ecrit : %-58s %7d octets" % (f.name, len(f.read_bytes())))

    print()
    print("⛔ RIEN N'A ETE JOUE. Ces trois fichiers attendent un « colle ».")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
