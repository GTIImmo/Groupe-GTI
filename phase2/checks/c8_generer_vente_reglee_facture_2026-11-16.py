#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C8 -- « VENTE REGLEE » (Y) ET « NUMERO DE FACTURE » (AA).           16/11/2026

    .venv\\Scripts\\python.exe -X utf8 phase2\\checks\\c8_generer_vente_reglee_facture_2026-11-16.py

⛔ CE SCRIPT N'ECRIT RIEN EN BASE. Il lit le Sheet, il MESURE, et il GENERE :
     supabase/patch_c8_vente_reglee_facture_2026-11-16.sql             le patch
     supabase/patch_c8_vente_reglee_facture_2026-11-16_INVERSE.sql     le retour arriere
     supabase/patch_c8_vente_reglee_facture_2026-11-16_REPETITION.sql  les controles

LES DEUX PLUS GROS POSTES DU CHANTIER. A1 du 16/11 :
```
   Y   Vente Reglee        3 756 remplies . 1 646 distinctes
                           ⛔ date 2 962 ET TEXTE 794  -- 21 %
   AA  Numero de facture   3 741 remplies . 3 735 distinctes . GGTI00003620
```

⭐⭐⭐ SUR QUELLE TRANSACTION ? LA VENTE, et la mesure est d'une nettete parfaite :
```
   lignes du classeur reliees a UNE vente       3 735
   lignes reliees a PLUSIEURS ventes                0   <- AUCUNE ambiguite
```
C'est logique : « vente reglee » date le REGLEMENT d'une vente, et une facture suit
une vente. Ni l'offre ni le compromis ne portent ca.

⛔⛔ LE PIEGE DE Y, ET IL A DEJA COUTE 924 LIGNES LE 14/11 : le classeur ecrit ses
  dates sous DEUX formes -- « 22/04/2025 » mais aussi « 29 decembre23 ». Une lecture
  qui n'en connait qu'une rend None sur l'autre, EN SILENCE.

⭐ MAIS CE PATCH N'A PAS BESOIN DU PARSEUR, et c'est important de le dire : la colonne
  est en TEXT, et la decision de A1 est de poser les valeurs **BRUTES**. On ne
  convertit rien, donc on ne perd rien -- ni les 2 962 dates ni les 794 textes.
  ⚠ Le parseur sert a LIRE et a COMPARER, pas a POSER. Et le commentaire de la
    colonne le dit : « Lecture tolerante : charge de C8 ». ➡ Ce sera un SECOND geste,
    une fonction de lecture, pas ce patch-ci. On pose d'abord ce qui ne se perd pas.

⚠ CE QUE CE PATCH LAISSE DE COTE, ET IL LE COMPTE : les lignes du classeur qui
  portent une valeur mais ne sont reliees a AUCUNE vente chez nous. A6 du 16/11 en
  annonce 21 pour Y et 21 pour AA parmi les 103 lignes hors du pont.
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

BASE = RACINE / "supabase" / "patch_c8_vente_reglee_facture_2026-11-16"
RAPPORT = RACINE / "notice" / "C8_VENTE_REGLEE_ET_FACTURE_2026-11-16.csv"
MARQUE = "classeur:C8:2026-11-16"
LOT_API = 60

#: Les temoins positifs de A1. En dessous, la colonne ou le format a bouge.
TEMOINS = {"Y": 3400, "AA": 3400}


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
    """⚠ Sans pagination, PostgREST s'arrete a 1 000 lignes EN SILENCE."""
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
    print("=== C8 -- « VENTE REGLEE » ET « NUMERO DE FACTURE » (lecture seule) ===")
    print()

    entetes_bruts, lignes = ap.lire_classeur()
    entetes = [str(c or "").strip() for c in entetes_bruts]
    if len(lignes) < 3000:
        print("⛔ LECTURE RATEE : %d lignes de corps. ON NE CONCLUT RIEN." % len(lignes))
        return 2
    col_id = entetes.index("ID Unique")
    print("le Sheet : %d lignes de corps" % len(lignes))
    for lettre in ("Y", "AA"):
        i = index_de(lettre)
        print("   %-3s en-tete lu : %r" % (lettre, entetes[i] if i < len(entetes) else "?"))

    def case(l, lettre):
        i = index_de(lettre)
        return str(l[i] if i < len(l) else "").strip()

    du_classeur: dict[str, dict] = {}
    comptes = Counter()
    doublons = 0
    for _rang, l in lignes:
        y, aa = case(l, "Y"), case(l, "AA")
        if y:
            comptes["Y"] += 1
        if aa:
            comptes["AA"] += 1
        if not (y or aa):
            continue
        ident = str(l[col_id] if col_id < len(l) else "").strip()
        if not ident:
            continue
        if ident in du_classeur:
            doublons += 1
            continue
        du_classeur[ident] = {"y": y, "aa": aa}

    print()
    print("=== CE QUE LE SHEET PORTE, ET CE QUE A1 ANNONCAIT ===")
    print("   Y   Vente Reglee       %5d   A1 : 3 756" % comptes["Y"])
    print("   AA  Numero de facture  %5d   A1 : 3 741" % comptes["AA"])
    print("   lignes portant au moins une des deux : %d  (doublons ecartes : %d)"
          % (len(du_classeur), doublons))

    for lettre, seuil in TEMOINS.items():
        if comptes[lettre] < seuil:
            print()
            print("⛔ TEMOIN POSITIF EN ECHEC sur %s : %d, seuil %d. La colonne a bouge."
                  % (lettre, comptes[lettre], seuil))
            print("   ON NE GENERE RIEN.")
            return 2

    # ⭐ LA FORME DE Y : on la MESURE, pour pouvoir l'ecrire dans le patch -- et pour
    #   prouver qu'on ne perd AUCUNE des deux formes en posant du brut.
    import re
    formes = Counter()
    for v in du_classeur.values():
        if not v["y"]:
            continue
        formes["date jj/mm/aaaa" if re.match(r"^\d{1,2}/\d{1,2}/\d{4}$", v["y"])
               else "TEXTE (ex: 29 decembre23)"] += 1
    print()
    print("=== LA FORME DE Y -- le piege du 14/11, mesure ===")
    for f, n in formes.most_common():
        print("   %-28s %5d" % (f, n))
    print("   ⭐ on pose du BRUT : les deux formes survivent, aucune conversion.")

    # ─── LA CIBLE : LA VENTE DE LA CHAINE ────────────────────────────────────
    cl = client()
    liens = tout_lire(cl, "app_classeur_lien", "id_unique,app_affaire_id", "ligne_classeur")
    par_id: dict[str, list[int]] = {}
    for r in liens:
        par_id.setdefault(str(r["id_unique"]).strip(), []).append(r["app_affaire_id"])
    besoin = sorted({a for i in du_classeur for a in par_id.get(i, [])})
    rows = []
    for i in range(0, len(besoin), LOT_API):
        lot = besoin[i:i + LOT_API]
        rows.extend(cl.get("app_affaire_ledger",
                           {"select": "app_affaire_id,kind,hektor_annonce_id,"
                                      "vente_reglee_app,numero_facture_app",
                            "app_affaire_id": "in.(%s)" % ",".join(map(str, lot))}) or [])
    ledger = {str(r["app_affaire_id"]): r for r in rows}

    nettes, plusieurs, aucune, deja = [], [], [], []
    for ident, v in sorted(du_classeur.items()):
        ventes = [ledger[str(a)] for a in par_id.get(ident, [])
                  if str(a) in ledger and ledger[str(a)].get("kind") == "vente"]
        if not ventes:
            aucune.append((ident, v))
        elif len(ventes) > 1:
            plusieurs.append((ident, v, ventes))
        elif (str(ventes[0].get("vente_reglee_app") or "").strip()
              or str(ventes[0].get("numero_facture_app") or "").strip()):
            deja.append((ident, v, ventes[0]))
        else:
            nettes.append((ident, v, ventes[0]))

    print()
    print("=== LE TRI ===")
    print("✅ UNE vente, rien de pose     : %4d  -> POSABLES" % len(nettes))
    print("⚠  PLUSIEURS ventes            : %4d  -> on ne choisit pas" % len(plusieurs))
    print("⚠  AUCUNE vente chez nous      : %4d  -> hors de portee (A6)" % len(aucune))
    print("·  DEJA pose                   : %4d  -> doit valoir 0" % len(deja))
    total = len(nettes) + len(plusieurs) + len(aucune) + len(deja)
    print()
    print("partition : %d = %d" % (total, len(du_classeur)))
    if total != len(du_classeur):
        print("⛔ LA PARTITION NE BOUCLE PAS -- ne rien poser.")
        return 2

    n_y = sum(1 for _i, v, _t in nettes if v["y"])
    n_aa = sum(1 for _i, v, _t in nettes if v["aa"])
    print()
    print("ce que les %d posables portent : Y %d . AA %d" % (len(nettes), n_y, n_aa))
    print("ce que les %d hors de portee emportent : Y %d . AA %d"
          % (len(aucune), sum(1 for _i, v in aucune if v["y"]),
             sum(1 for _i, v in aucune if v["aa"])))

    with RAPPORT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, delimiter=";", fieldnames=[
            "verdict", "id_unique", "app_affaire_id", "annonce",
            "vente_reglee", "numero_facture"])
        w.writeheader()
        for verdict, lot in (("nette", nettes), ("deja_pose", deja)):
            for ident, v, t in lot:
                w.writerow({"verdict": verdict, "id_unique": ident,
                            "app_affaire_id": t["app_affaire_id"],
                            "annonce": t.get("hektor_annonce_id"),
                            "vente_reglee": v["y"], "numero_facture": v["aa"]})
        for ident, v, ts in plusieurs:
            for t in ts:
                w.writerow({"verdict": "plusieurs_ventes", "id_unique": ident,
                            "app_affaire_id": t["app_affaire_id"],
                            "annonce": t.get("hektor_annonce_id"),
                            "vente_reglee": v["y"], "numero_facture": v["aa"]})
        for ident, v in aucune:
            w.writerow({"verdict": "aucune_vente", "id_unique": ident,
                        "app_affaire_id": "", "annonce": "",
                        "vente_reglee": v["y"], "numero_facture": v["aa"]})
    print()
    print("ecrit : %s" % RAPPORT)

    n = len(nettes)
    valeurs = ",\n    ".join(
        "(%d, %s, %s)" % (t["app_affaire_id"],
                          txt(v["y"]) if v["y"] else "NULL",
                          txt(v["aa"]) if v["aa"] else "NULL")
        for _i, v, t in nettes)
    ids = ", ".join(str(t["app_affaire_id"]) for _i, _v, t in nettes)
    forme_date = formes.get("date jj/mm/aaaa", 0)
    forme_texte = formes.get("TEXTE (ex: 29 decembre23)", 0)

    patch = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- C8 -- « VENTE REGLEE » (Y) ET « NUMERO DE FACTURE » (AA) SUR LEUR VENTE
-- Genere le {date.today().isoformat()} par phase2/checks/c8_generer_vente_reglee_facture_2026-11-16.py
--
-- {n} ventes, soit {n_y} dates de reglement et {n_aa} numeros de facture.
-- LES DEUX PLUS GROS POSTES DU CHANTIER.
--
-- ⭐⭐ LA CIBLE EST LA VENTE, et la mesure est d'une nettete parfaite : AUCUNE
--   ligne du classeur n'est reliee a plusieurs ventes. C'est logique -- « vente
--   reglee » date le REGLEMENT d'une vente, et une facture suit une vente ; ni
--   l'offre ni le compromis ne portent ca.
--
-- ⛔⛔ LE PIEGE DE Y, ET IL A DEJA COUTE 924 LIGNES LE 14/11 : le classeur ecrit
--   ses dates sous DEUX formes. Mesure de ce lot :
--       date jj/mm/aaaa           {forme_date}
--       TEXTE (29 decembre23)     {forme_texte}
--   ⭐ ET CE PATCH N'EN PERD AUCUNE, parce qu'il ne CONVERTIT RIEN : la colonne
--     est en TEXT (decision de A1) et on pose les valeurs BRUTES. Le parseur
--     tolerant sert a LIRE et a COMPARER, pas a POSER.
--   ➡ « Lecture tolerante : charge de C8 » (commentaire de la colonne) reste donc
--     A FAIRE, en SECOND geste : une fonction de lecture, pas ce patch-ci. On pose
--     d'abord ce qui ne se perd pas.
--
-- ⚠ CE QUE CE PATCH LAISSE DE COTE, ET IL LE COMPTE : {len(aucune)} ligne(s) du
--   classeur portent une valeur sans qu'aucune vente ne leur soit reliee chez nous
--   (les trous du pont mesures par A6 le 16/11). Elles ne sont PAS perdues : elles
--   sont dans notice/C8_VENTE_REGLEE_ET_FACTURE_2026-11-16.csv, verdict
--   « aucune_vente », et le re-gel les rattrapera.
--
-- ⛔ CES DEUX COLONNES SONT DE CLASSE A : Hektor ne les connait pas, et elles sont
--   dans COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS depuis B1 (16/11). Rien ne part chez lui.
--
-- Retour arriere : patch_c8_vente_reglee_facture_2026-11-16_INVERSE.sql
-- Controle       : patch_c8_vente_reglee_facture_2026-11-16_REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════

begin;

-- ─── 1. L'ETAT D'AVANT, EXIGE ──────────────────────────────────────────────
do $$
declare deja integer; cibles integer;
begin
  select count(*) into deja from public.app_affaire_ledger
   where vente_reglee_app is not null or numero_facture_app is not null;
  if deja <> 0 then
    raise exception '⛔ ARRET : % ligne(s) portent deja une de ces deux valeurs. '
      'Ce patch suppose deux colonnes vierges (0 au 16/11).', deja;
  end if;

  select count(*) into cibles from public.app_affaire_ledger
   where app_affaire_id in ({ids}) and kind = 'vente';
  if cibles <> {n} then
    raise exception '⛔ ARRET : % ventes retrouvees sur les {n} attendues.', cibles;
  end if;
  raise notice '✅ etat d''avant : 0 valeur posee, {n} ventes retrouvees.';
end $$;

-- ─── 2. LA SAUVEGARDE DATEE, ET ELLE NAIT FERMEE ───────────────────────────
-- ⛔⛔ LA LECON DU 16/11 AU SOIR : une sauvegarde creee par `create table ... as`
--   HERITE du droit par defaut du schema ET NAIT SANS RLS. Mesure du jour : 18
--   sauvegardes du projet etaient ainsi REELLEMENT ouvertes a `authenticated`,
--   TRUNCATE comprise -- et elles portent les MEMES donnees que les tables
--   protegees. Celle-ci naitra fermee, et c'est desormais le patron.
create table if not exists public.app_affaire_avant_c8_20261116 as
  select app_affaire_id, kind, hektor_annonce_id,
         vente_reglee_app, numero_facture_app, now() as photographie_le
    from public.app_affaire_ledger
   where app_affaire_id in ({ids});
revoke all on public.app_affaire_avant_c8_20261116 from authenticated, anon;

-- ─── 3. LA POSE ────────────────────────────────────────────────────────────
with poser(app_affaire_id, reglee, facture) as (values
    {valeurs}
)
update public.app_affaire_ledger l
   set vente_reglee_app   = coalesce(p.reglee,  l.vente_reglee_app),
       numero_facture_app = coalesce(p.facture, l.numero_facture_app)
  from poser p
 where l.app_affaire_id = p.app_affaire_id
   and l.kind = 'vente'
   and l.vente_reglee_app is null
   and l.numero_facture_app is null;

-- ─── 4. LES CONTROLES, ET ILS ARRETENT ─────────────────────────────────────
do $$
declare
  y        integer;
  aa       integer;
  ailleurs integer;
  pas_vente integer;
  sauve    integer;
  ferme    integer;
begin
  select count(vente_reglee_app), count(numero_facture_app) into y, aa
    from public.app_affaire_ledger where app_affaire_id in ({ids});
  if y <> {n_y} or aa <> {n_aa} then
    raise exception '⛔ attendu Y {n_y} / AA {n_aa}, obtenu % / %.', y, aa;
  end if;

  -- ⭐ TEMOIN INVERSE : rien hors du lot
  select count(*) into ailleurs from public.app_affaire_ledger
   where (vente_reglee_app is not null or numero_facture_app is not null)
     and app_affaire_id not in ({ids});
  if ailleurs <> 0 then
    raise exception '⛔ % ligne(s) HORS du lot portent une valeur.', ailleurs;
  end if;

  -- ⭐ QUE DES VENTES
  select count(*) into pas_vente from public.app_affaire_ledger
   where (vente_reglee_app is not null or numero_facture_app is not null)
     and kind <> 'vente';
  if pas_vente <> 0 then
    raise exception '⛔ % ligne(s) qui ne sont pas des ventes portent une valeur.', pas_vente;
  end if;

  select count(*) into sauve from public.app_affaire_avant_c8_20261116;
  if sauve <> {n} then
    raise exception '⛔ la sauvegarde porte % lignes sur {n}.', sauve;
  end if;

  -- ⭐⭐ ET LA SAUVEGARDE EST-ELLE BIEN FERMEE ? (la lecon du soir)
  select count(*) into ferme from information_schema.role_table_grants
   where table_schema='public' and table_name='app_affaire_avant_c8_20261116'
     and grantee in ('authenticated','anon');
  if ferme <> 0 then
    raise exception '⛔ la sauvegarde porte encore % droit(s) pour '
      'authenticated/anon.', ferme;
  end if;

  raise notice '✅ Y {n_y} . AA {n_aa} . 0 hors du lot . 0 non-vente . '
    'sauvegarde {n} ET FERMEE.';
end $$;

commit;
"""

    inverse = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- C8 -- RETOUR ARRIERE
-- ⭐ « Un retour arriere ne juge que SA part » : il ne vide que les {n} ventes de
--   ce lot, et il REFUSE de se jouer si une valeur a change depuis la pose.
-- ═══════════════════════════════════════════════════════════════════════════

begin;

do $$
declare changees integer;
begin
  with attendu(app_affaire_id, reglee, facture) as (values
      {valeurs}
  )
  select count(*) into changees
    from attendu a join public.app_affaire_ledger l using (app_affaire_id)
   where coalesce(l.vente_reglee_app, '')   is distinct from coalesce(a.reglee, '')
      or coalesce(l.numero_facture_app, '') is distinct from coalesce(a.facture, '');
  if changees <> 0 then
    raise exception '⛔ ARRET : % ligne(s) ne portent plus la valeur posee par C8. '
      'Quelqu''un est passe apres nous -- ne RIEN effacer sans relire.', changees;
  end if;
  raise notice '✅ les {n} ventes portent bien les valeurs de C8.';
end $$;

update public.app_affaire_ledger
   set vente_reglee_app = null, numero_facture_app = null
 where app_affaire_id in ({ids});

do $$
declare reste integer;
begin
  select count(*) into reste from public.app_affaire_ledger
   where app_affaire_id in ({ids})
     and (vente_reglee_app is not null or numero_facture_app is not null);
  if reste <> 0 then
    raise exception '⛔ il reste % ligne(s) du lot.', reste;
  end if;
  raise notice '✅ {n} ventes videes de leurs deux valeurs.';
end $$;

-- ⚠ La sauvegarde n'est PAS supprimee : elle prouve l'etat d'avant.
commit;
"""

    repetition = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- C8 -- LES CONTROLES, REJOUABLES. Aucune ecriture.
-- ═══════════════════════════════════════════════════════════════════════════

select 'vente_reglee_app renseignes' as controle, count(vente_reglee_app)::text as mesure,
       '{n_y}' as attendu from public.app_affaire_ledger
union all
select 'numero_facture_app renseignes', count(numero_facture_app)::text, '{n_aa}'
  from public.app_affaire_ledger
union all
select 'toutes sur une VENTE', count(*)::text, '0'
  from public.app_affaire_ledger
 where (vente_reglee_app is not null or numero_facture_app is not null) and kind <> 'vente'
union all
select 'aucune valeur hors du lot', count(*)::text, '0'
  from public.app_affaire_ledger
 where (vente_reglee_app is not null or numero_facture_app is not null)
   and app_affaire_id not in ({ids})
union all
-- ⭐⭐ LE TEMOIN QUI PROUVE QU'ON N'A RIEN PERDU : les DEUX formes de date sont la.
--   Si l'une tombait a 0, c'est qu'une conversion s'etait glissee quelque part.
select 'Y au format jj/mm/aaaa', count(*)::text, '{forme_date} (environ)'
  from public.app_affaire_ledger
 where vente_reglee_app ~ '^[0-9]{{1,2}}/[0-9]{{1,2}}/[0-9]{{4}}$'
union all
select 'Y en TEXTE (29 decembre23)', count(*)::text, '{forme_texte} (environ)'
  from public.app_affaire_ledger
 where vente_reglee_app is not null
   and vente_reglee_app !~ '^[0-9]{{1,2}}/[0-9]{{1,2}}/[0-9]{{4}}$'
union all
select 'numeros de facture DISTINCTS', count(distinct numero_facture_app)::text,
       'proche de {n_aa} -- ils sont quasi uniques'
  from public.app_affaire_ledger where numero_facture_app is not null
union all
select 'la sauvegarde est FERMEE a authenticated/anon', count(*)::text, '0'
  from information_schema.role_table_grants
 where table_schema='public' and table_name='app_affaire_avant_c8_20261116'
   and grantee in ('authenticated','anon')
union all
select 'VOISINES -- les 450 dates de C3', count(*)::text, '450'
  from public.app_affaire_ledger where date_annulation_app is not null
union all
select 'VOISINES -- les 2 588 avis', (select count(*)::text from public.app_classeur_avis), '2588'
order by 1;
"""

    for suffixe, contenu in ((".sql", patch), ("_INVERSE.sql", inverse),
                             ("_REPETITION.sql", repetition)):
        f = Path(str(BASE) + suffixe)
        f.write_bytes(contenu.encode("utf-8"))
        print("ecrit : %-62s %7d octets" % (f.name, len(f.read_bytes())))

    print()
    print("⛔ RIEN N'A ETE JOUE. Ces trois fichiers attendent un « colle ».")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
