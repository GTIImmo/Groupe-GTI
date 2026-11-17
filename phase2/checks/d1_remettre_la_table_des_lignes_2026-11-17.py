#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""D1 -- REMETTRE `app_classeur_ligne_id` A JOUR, SANS RIEN DEPLACER. 17/11/2026

    .venv\\Scripts\\python.exe -X utf8 phase2\\checks\\d1_remettre_la_table_des_lignes_2026-11-17.py

⛔ CE SCRIPT N'ECRIT RIEN EN BASE. Il MESURE, puis il GENERE un patch.

LE BESOIN : la table porte 4 773 lignes quand le Sheet en a 4 794. Les 21
manquantes sont les plus RECENTES. Elle donne LE NUMERO DE LIGNE, donc sans elle
un re-gel ne sait pas quoi accrocher -- et la sentinelle B2 sous-compte.

⛔⛔ LE CONTROLE IMPERATIF, ET IL PASSE AVANT TOUT : `app_classeur_lien` a pour
  CLEF PRIMAIRE (ligne_classeur + app_affaire_id). Si des lignes ont ete INSEREES
  AU MILIEU du Sheet, tous les numeros suivants ont glisse -- et les 12 790 liens
  garderaient l'ANCIEN numero. La table et les liens ne parleraient plus de la
  meme ligne, en silence.
  ➡ ON NE TOUCHE DONC A RIEN avant d'avoir verifie que CHAQUE id_unique deja
    connu porte LE MEME numero qu'au Sheet. S'il y a UN SEUL decalage, le script
    s'arrete et ne genere rien : ce ne serait plus un ajout mais une migration.

⭐ ET LE GESTE RESTE UN AJOUT PUR : `insert ... where not exists`. Aucune ligne
  existante n'est modifiee, aucun numero n'est deplace.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "monitoring"))
sys.path.insert(0, str(RACINE / "phase2" / "checks"))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import apparier_classeur as ap                                      # noqa: E402
import check_gti_health as cgh                                      # noqa: E402

BASE = RACINE / "supabase" / "patch_d1_table_des_lignes_2026-11-17"


def client():
    for f in (RACINE / ".env", RACINE / "backend" / ".env",
              RACINE / "apps" / "hektor-v1" / ".env"):
        if f.exists():
            cgh.load_env_file(f)
    url = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL")
    cle = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not (url and cle):
        raise SystemExit("⛔ pas d'identifiants Supabase.")
    return cgh.SupabaseClient(url, cle, timeout_seconds=30)


def tout_lire(cl, table, select, ordre):
    out, pas, dep = [], 1000, 0
    while True:
        lot = cl.get(table, {"select": select, "order": ordre,
                             "limit": pas, "offset": dep}) or []
        out.extend(lot)
        if len(lot) < pas:
            return out
        dep += pas


def txt(v) -> str:
    s = str(v if v is not None else "").replace("\r", " ").replace("\n", " ")
    return "'" + s.replace("'", "''") + "'"


def main() -> int:
    ap.load_env_file(RACINE / ".env")
    print("=== D1 -- LA TABLE DES LIGNES DU CLASSEUR (aucune ecriture) ===")
    print()
    entetes_bruts, lignes = ap.lire_classeur()
    entetes = [str(c or "").strip() for c in entetes_bruts]
    if len(lignes) < 3000:
        print("⛔ LECTURE RATEE : %d lignes." % len(lignes))
        return 2
    i_id = entetes.index("ID Unique")
    au_sheet = {}
    doublons = []
    for rang, l in lignes:
        ident = str(l[i_id] if i_id < len(l) else "").strip()
        if not ident:
            continue
        if ident in au_sheet:
            doublons.append((ident, au_sheet[ident], rang))
        au_sheet[ident] = rang
    print("le Sheet : %d lignes . %d id_unique distincts" % (len(lignes), len(au_sheet)))
    #: ⛔ un id_unique en double ferait deux lignes pour une clef : on le DIT
    if doublons:
        print("⛔ %d id_unique EN DOUBLE au Sheet -- on s'arrete, ce n'est plus un ajout :"
              % len(doublons))
        for i, a, b in doublons[:10]:
            print("   %s : lignes %s et %s" % (i, a, b))
        return 2

    cl = client()
    en_base = {str(r["id_unique"]).strip(): int(r["ligne_classeur"])
               for r in tout_lire(cl, "app_classeur_ligne_id",
                                  "id_unique,ligne_classeur", "ligne_classeur")}
    print("la table en base : %d lignes" % len(en_base))
    print()

    # ─── ⛔⛔ LE CONTROLE IMPERATIF : AUCUN NUMERO N'A BOUGE ──────────────────
    print("=== ⛔⛔ LE CONTROLE IMPERATIF : LES NUMEROS ONT-ILS BOUGE ? ===")
    communs = [i for i in en_base if i in au_sheet]
    decales = [(i, en_base[i], au_sheet[i]) for i in communs
               if en_base[i] != au_sheet[i]]
    print("   id_unique connus des DEUX cotes : %d" % len(communs))
    print("   ⛔ dont le numero DIFFERE        : %d" % len(decales))
    if decales:
        print("   ⛔⛔ DES LIGNES ONT GLISSE -- ON NE GENERE RIEN.")
        print("     `ligne_classeur` fait partie de la CLEF PRIMAIRE des 12 790 liens :")
        print("     les mettre a jour ici sans les y suivre casserait le pont en silence.")
        print("     Ce serait une MIGRATION, pas un ajout, et elle demande sa decision.")
        for i, a, b in decales[:12]:
            print("        %-10s base %-6s -> Sheet %-6s" % (i, a, b))
        return 2
    print("   ✅ AUCUN DECALAGE : l'ajout est donc sans danger pour les liens.")
    print()

    #: ⭐ ET LE TEMOIN DANS L'AUTRE SENS : la table ne doit rien porter que le
    #:   Sheet ignore (une ligne supprimee du Sheet resterait en base).
    orphelines = [i for i in en_base if i not in au_sheet]
    print("=== LES ORPHELINES DE LA TABLE (le Sheet ne les a plus) ===")
    print("   %d id_unique en base, absents du Sheet" % len(orphelines))
    if orphelines:
        print("   ⚠ on NE LES RETIRE PAS : des liens les pointent peut-etre. On le DIT.")
        for i in sorted(orphelines)[:10]:
            print("      %-10s ligne %s" % (i, en_base[i]))
    print()

    a_ajouter = sorted(((au_sheet[i], i) for i in au_sheet if i not in en_base))
    print("=== ⭐ CE QU'IL Y A A AJOUTER : %d lignes ===" % len(a_ajouter))
    for rang, i in a_ajouter:
        print("   ligne %-6s %s" % (rang, i))
    if not a_ajouter:
        print("   rien a faire.")
        return 0
    if len(a_ajouter) > 100:
        print("⛔ PLUS DE 100 LIGNES A AJOUTER -- ce n'est plus un rattrapage, on"
              " s'arrete et on en parle.")
        return 2

    valeurs = ",\n    ".join("(%d, %s)" % (rang, txt(i)) for rang, i in a_ajouter)
    n = len(a_ajouter)
    apres = len(en_base) + n
    patch = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- D1 -- REMETTRE `app_classeur_ligne_id` A JOUR : {n} LIGNES RECENTES
-- Genere le 2026-11-17 par phase2/checks/d1_remettre_la_table_des_lignes_2026-11-17.py
--
-- LE BESOIN : la table portait {len(en_base)} lignes quand le Sheet en a {len(au_sheet)}.
--   Les manquantes sont LES PLUS RECENTES. Or c'est elle qui donne LE NUMERO DE
--   LIGNE : sans elle, un re-gel ne sait pas quoi accrocher, et la sentinelle B2
--   (« lignes du classeur sans lien ») SOUS-COMPTE, puisqu'elle la lit.
--
-- ⛔⛔ LE CONTROLE IMPERATIF A ETE PASSE AVANT DE GENERER CE PATCH : sur les
--   {len(communs)} id_unique connus des deux cotes, **AUCUN n'a change de numero**.
--   C'etait la condition absolue : `ligne_classeur` fait partie de la CLEF
--   PRIMAIRE des 12 790 liens. Si une ligne avait glisse, la table et les liens
--   auraient cesse de parler de la meme ligne EN SILENCE -- et ce patch serait
--   une migration, pas un ajout. Le generateur refuse de l'ecrire dans ce cas.
--
-- ⭐ LE GESTE EST UN AJOUT PUR : `where not exists`. Aucune ligne existante n'est
--   modifiee, aucun numero n'est deplace, aucun lien n'est touche.
--
-- ⚠ ET ON NE RETIRE RIEN : la table porte peut-etre des id_unique que le Sheet
--   n'a plus ; des liens les pointent sans doute. Les supprimer casserait le pont.
--
-- RETOUR ARRIERE : patch_d1_table_des_lignes_2026-11-17_INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════
begin;

-- ① LA SAUVEGARDE DATEE
drop table if exists app_classeur_ligne_id_avant_20261117;
create table app_classeur_ligne_id_avant_20261117 as
  select * from app_classeur_ligne_id;

do $$
declare n integer;
begin
  select count(*) into n from app_classeur_ligne_id_avant_20261117;
  if n <> {len(en_base)} then
    raise exception '⛔ LA SAUVEGARDE PORTE % lignes au lieu de {len(en_base)}', n;
  end if;
end $$;

-- ② L'AJOUT
insert into app_classeur_ligne_id (ligne_classeur, id_unique)
values
    {valeurs}
on conflict do nothing;

-- ③ LES CONTROLES, DANS LA MEME TRANSACTION
do $$
declare n integer;
begin
  select count(*) into n from app_classeur_ligne_id;
  if n <> {apres} then
    raise exception '⛔ LA TABLE PORTE % lignes au lieu de {apres}', n;
  end if;

  -- ⭐⭐ AUCUNE LIGNE D'ORIGINE N'A BOUGE -- compare a la sauvegarde, pas compte
  select count(*) into n
    from app_classeur_ligne_id_avant_20261117 s
    left join app_classeur_ligne_id g on g.id_unique = s.id_unique
   where g.id_unique is null or g.ligne_classeur is distinct from s.ligne_classeur;
  if n <> 0 then
    raise exception '⛔ % lignes d origine ont disparu ou change de numero', n;
  end if;

  -- ⭐ LES 12 790 LIENS SONT INTACTS : ce patch ne les touche pas
  select count(*) into n from app_classeur_lien;
  if n <> 12790 then raise exception '⛔ LE GEL PORTE % liens au lieu de 12 790', n; end if;

  -- ⭐ et plus aucun lien ne pointe un id_unique absent de la table
  select count(*) into n from (select distinct k.id_unique from app_classeur_lien k
    where not exists (select 1 from app_classeur_ligne_id g
                       where g.id_unique = k.id_unique)) s;
  if n <> 0 then
    raise notice '⚠ il reste % id_unique pointes par un lien et absents de la table', n;
  else
    raise notice '✅ plus aucun lien orphelin de la table des lignes';
  end if;

  raise notice '✅ {n} lignes ajoutees, la table passe a {apres}';
end $$;

commit;
"""
    inverse = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- LE RETOUR ARRIERE DE L'AJOUT DES {n} LIGNES -- 2026-11-17
--
-- ⭐ Il retire EXACTEMENT les {n} id_unique ajoutes, nommement. Il ne touche a
--   aucune des {len(en_base)} lignes d'origine, et a aucun lien.
-- ⛔ ET IL JUGE SA PROPRE PART : la table doit revenir a {len(en_base)}, et les
--   lignes d'origine etre intactes face a la sauvegarde.
-- ═══════════════════════════════════════════════════════════════════════════
begin;

delete from app_classeur_ligne_id
 where id_unique in ({", ".join(txt(i) for _r, i in a_ajouter)});

do $$
declare n integer;
begin
  select count(*) into n from app_classeur_ligne_id;
  if n <> {len(en_base)} then
    raise exception '⛔ LA TABLE PORTE % lignes au lieu de {len(en_base)}', n;
  end if;
  select count(*) into n
    from app_classeur_ligne_id_avant_20261117 s
    left join app_classeur_ligne_id g on g.id_unique = s.id_unique
   where g.id_unique is null or g.ligne_classeur is distinct from s.ligne_classeur;
  if n <> 0 then raise exception '⛔ % lignes d origine abimees', n; end if;
  select count(*) into n from app_classeur_lien;
  if n <> 12790 then raise exception '⛔ LE GEL A BOUGE : % liens', n; end if;
  raise notice '✅ RETOUR ARRIERE COMPLET';
end $$;

commit;
"""
    for suffixe, contenu in ((".sql", patch), ("_INVERSE.sql", inverse)):
        p = Path(str(BASE) + suffixe)
        p.write_bytes(contenu.encode("utf-8"))
        b = p.read_bytes()
        print()
        print("ecrit : %-52s %5d octets . CR %d" % (p.name, len(b), b.count(b"\r")))
        if b.count(b"\r"):
            print("⛔ DES RETOURS CHARIOT DANS UN PATCH A COLLER.")
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
