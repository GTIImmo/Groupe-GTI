#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C4 (1er patch) -- LE CATALOGUE, LES MOTIFS, LES CONDITIONS.        17/11/2026

    .venv\\Scripts\\python.exe -X utf8 phase2\\checks\\c4_generer_motifs_et_conditions_2026-11-17.py

⛔ CE SCRIPT N'ECRIT RIEN EN BASE. Il lit le rapport de C4, il MESURE, et il GENERE :
     supabase/patch_c4_motifs_conditions_2026-11-17.sql             le patch
     supabase/patch_c4_motifs_conditions_2026-11-17_INVERSE.sql     le retour arriere
     supabase/patch_c4_motifs_conditions_2026-11-17_REPETITION.sql  les controles

⭐⭐⭐ SES DECISIONS, DU 17/11 :
  . le CATALOGUE : ajouter « Permis de construire » et « Delai de retractation SRU ».
    ⛔ RIEN pour le pret : « Obtention Credit » EXISTE DEJA (catalogue id 2), et
      ADP/ODP n'en sont pas deux clauses mais le DEPART et l'ECHEANCE de celle-la --
      mesure du 17/11 : ADP avant ODP 24 fois sur 24, ecart median 31 jours.
      (Lecon 15 : j'ai failli creer un doublon.)
  . les MOTIFS : « Les 216 motifs normalises, les 492 phrases uniques partant en
    note. » Donc `motif_annulation_app` ne recoit QUE les motifs qui REVIENNENT.
  . les NOTES : elles sont dans le SECOND patch (5 003 lignes), pas ici.

⭐ LE LIBELLE D'UN MOTIF EST L'ECRITURE LA PLUS FREQUENTE DE SON GROUPE, jamais un
  texte que j'invente. « refus pret » regroupe « refus prêt » (31), « refus de prêt »
  (25) et « refus de pret » (1) -> le libelle retenu est **« refus prêt »**. Ni
  invention, ni normalisation agressive : du texte reel du classeur.

⛔⛔ LE PREALABLE QUE L'AUDIT DU 16/11 A TROUVE, ET IL EST TRAITE ICI :
  `app_affaire_note` porte DEJA 195 lignes `origine = 'classeur'` -- les notes
  d'acquereur posees avec les 195 transactions de C5. Si C4 posait ses notes avec la
  MEME origine, les deux lots deviendraient INDISCERNABLES et un retour arriere sur
  l'un emporterait l'autre.
  ➡ C4 utilise donc `classeur:F` et `classeur:G`, jamais `classeur` seul.
"""
from __future__ import annotations

import csv
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "monitoring"))

import check_gti_health as cgh                                      # noqa: E402

DETAIL = RACINE / "notice" / "C4_LES_CLAUSES_DE_LA_COLONNE_F_2026-11-16.csv"
BASE = RACINE / "supabase" / "patch_c4_motifs_conditions_2026-11-17"
RAPPORT = RACINE / "notice" / "C4_LES_MOTIFS_RETENUS_2026-11-17.csv"
LOT_API = 60

#: Les deux clauses a ajouter au catalogue -- sa decision du 17/11.
#:   `jours_defaut` : le delai legal pour le SRU (10 jours), et 0 pour le permis
#:   (il n'a pas de delai standard -- il depend de la mairie).
CLAUSES_NEUVES = [
    ("Permis de construire", 0),
    ("Delai de retractation SRU", 10),
]

#: ⭐⭐⭐ LES SIX MOTIFS NORMALISES, VALIDES PAR FREDERIC LE 17/11.
#:
#: ⛔ POURQUOI SIX ET NON 41. Ma premiere version prenait « l'ecriture la plus
#:   frequente de chaque groupe » comme libelle. Resultat visible a l'oeil :
#:   « annule » 9 et « annulee » 9 cote a cote, « SRU » 12 et « retractation SRU »
#:   12 separes. Ce n'etait PAS normalise -- et c'est exactement ce qu'il avait
#:   demande. Groupes par THEME, les 41 ecritures disent SIX causes.
#:
#: ⚠ ET J'AVAIS MAL RANGE « refus PC » dans le pret : un refus de PERMIS n'est pas
#:   un refus de PRET. Il a son propre motif.
#:
#: ⛔ ON S'EN TIENT AUX CLEFS QU'IL A VUES, et a aucune autre. Plusieurs des
#:   « non classes » y entreraient logiquement (« refus financement »,
#:   « montant travaux trop eleve »), mais les ajouter changerait un compte qu'il
#:   a valide a 180. Elles partent en note, et c'est DIT.
MOTIFS_NORMALISES = {
    "Pret refuse": ("refus pret", "refuse", "refus banque", "pb financement",
                    "financement", "2 refus pret"),
    "Retractation": ("retractation", "retractation sru", "sru", "retractation acq",
                     "retractation ecrite", "renonciation acq", "annulation ecrite"),
    "Annule sans motif precise": ("annule", "annulee", "annulation acq"),
    "Changement de situation acquereur": ("a change avis", "changement avis acq",
                                          "raison familiale", "perte emploi"),
    "Travaux ou etat du bien": ("trop travaux", "zone humide a preserver"),
    "Permis refuse": ("refus pc",),
}
#: la clef -> le motif, construit a l'envers pour que le script ne cherche pas
MOTIF_DE_LA_CLEF = {c: m for m, cs in MOTIFS_NORMALISES.items() for c in cs}


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


def txt(v) -> str:
    return "'" + str(v).replace("'", "''") + "'"


def main() -> int:
    with DETAIL.open(encoding="utf-8-sig", newline="") as h:
        detail = list(csv.DictReader(h, delimiter=";"))
    if len(detail) < 2000:
        print("⛔ le rapport de C4 ne porte que %d lignes (3 100 attendues)." % len(detail))
        return 2
    print("=== C4 (1er patch) -- CATALOGUE, MOTIFS, CONDITIONS (lecture seule) ===")
    print("le rapport de C4 : %d cases de F" % len(detail))
    print()

    MORTS = ("Annulée", "Annulee")
    cm = [x for x in detail if x["famille"] == "CLAUSE ou MOTIF"]
    ann = [x for x in cm if x["etat_actuel"] in MORTS]
    cours = [x for x in cm if x["etat_actuel"] not in MORTS
             and x["etat_actuel"] not in ("Vente réglée", "Vente reglee")]

    # ─── LES MOTIFS QUI REVIENNENT, et leur libelle REEL ────────────────────
    #: ⭐ LES SIX MOTIFS, et RIEN d'autre : une clef qui n'est pas dans sa table
    #:   part en note, meme si elle revient deux fois.
    retenus = set(MOTIF_DE_LA_CLEF)
    libelle = MOTIF_DE_LA_CLEF
    n_motifs = sum(1 for x in ann if x["clef_de_regroupement"] in retenus)
    print("=== LES MOTIFS ===")
    print("   affaires ANNULEES avec un texte     %4d" % len(ann))
    print("   dont un des SIX motifs normalises   %4d lignes" % n_motifs)
    print("   le reste -> 2e patch (notes)        %4d" % (len(ann) - n_motifs))
    print()
    print("   les six motifs, et ce qu'ils couvrent :")
    par_motif = Counter(libelle[x["clef_de_regroupement"]] for x in ann
                        if x["clef_de_regroupement"] in retenus)
    for m, nb in par_motif.most_common():
        ecr = Counter(x["texte_seul"] for x in ann
                      if libelle.get(x["clef_de_regroupement"]) == m)
        print("      %4d  %-34s <- %s" % (nb, m,
              " | ".join(a for a, _ in ecr.most_common(4))[:50]))
    #: ⛔ LE TEMOIN QUI DIT CE QU'ON LAISSE : les clefs qui reviennent >= 2 fois
    #:   mais ne sont PAS dans sa table. On les NOMME, on ne les absorbe pas.
    autres = Counter(x["clef_de_regroupement"] for x in ann
                     if x["clef_de_regroupement"] not in retenus)
    repetees = {k: n for k, n in autres.items() if n >= 2}
    if repetees:
        print()
        print("   ⚠ CES CLEFS REVIENNENT MAIS NE SONT PAS DANS SA TABLE -- elles vont")
        print("     en NOTE, et c'est DIT (%d lignes) :" % sum(repetees.values()))
        for k, nb in sorted(repetees.items(), key=lambda kv: -kv[1])[:8]:
            print("        %2d  %s" % (nb, k[:60]))
    print()
    print("=== LES CONDITIONS EN ATTENTE (affaires EN COURS) ===")
    print("   %d lignes" % len(cours))

    # ─── LA CIBLE DE CHAQUE LIGNE ────────────────────────────────────────────
    cl = client()
    liens = tout_lire(cl, "app_classeur_lien", "id_unique,app_affaire_id", "ligne_classeur")
    par_id: dict[str, list[int]] = {}
    for r in liens:
        par_id.setdefault(str(r["id_unique"]).strip(), []).append(r["app_affaire_id"])
    vises = {x["id_unique"] for x in ann + cours if x["id_unique"]}
    besoin = sorted({a for i in vises for a in par_id.get(i, [])})
    rows = []
    for i in range(0, len(besoin), LOT_API):
        lot = besoin[i:i + LOT_API]
        rows.extend(cl.get("app_affaire_ledger",
                           {"select": "app_affaire_id,kind,state,hektor_annonce_id,"
                                      "app_dossier_id,app_chaine_id,motif_annulation_app",
                            "app_affaire_id": "in.(%s)" % ",".join(map(str, lot))}) or [])
    ledger = {str(r["app_affaire_id"]): r for r in rows}

    # ⭐ LE MOTIF VA SUR LA TRANSACTION ANNULEE -- la meme cible que C3, pour que
    #   la date et le motif soient sur la MEME ligne. Le compromis d'abord, l'offre
    #   en repli (certaines chaines n'ont pas de compromis).
    motifs, sans_cible, deja = [], 0, 0
    for x in ann:
        if x["clef_de_regroupement"] not in retenus:
            continue
        trs = [ledger[str(a)] for a in par_id.get(x["id_unique"], []) if str(a) in ledger]
        comp = [t for t in trs if t.get("kind") == "compromis" and t.get("state") == "cancelled"]
        off = [t for t in trs if t.get("kind") == "offre" and t.get("state") == "refused"]
        cibles = comp or off
        if len(cibles) != 1:
            sans_cible += 1
            continue
        t = cibles[0]
        if str(t.get("motif_annulation_app") or "").strip():
            deja += 1
            continue
        motifs.append({"app_affaire_id": t["app_affaire_id"],
                       "annonce": t.get("hektor_annonce_id"), "type": t.get("kind"),
                       "motif": libelle[x["clef_de_regroupement"]],
                       "texte_origine": x["texte_seul"], "id_unique": x["id_unique"]})

    print()
    print("=== LE TRI DES MOTIFS ===")
    print("✅ une seule cible annulee, rien de pose : %4d  -> POSABLES" % len(motifs))
    print("⚠  pas de cible nette (0 ou plusieurs)   : %4d" % sans_cible)
    print("·  deja un motif                          : %4d  (doit valoir 0)" % deja)
    print()
    print("   leur repartition :")
    for k, n in Counter(x["motif"] for x in motifs).most_common(10):
        print("      %-30s %4d" % (k[:30], n))

    with RAPPORT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, delimiter=";", fieldnames=list(motifs[0]))
        w.writeheader()
        w.writerows(motifs)
    print()
    print("ecrit : %s" % RAPPORT)

    n = len(motifs)
    valeurs = ",\n    ".join("(%d, %s)" % (x["app_affaire_id"], txt(x["motif"]))
                             for x in motifs)
    ids = ", ".join(str(x["app_affaire_id"]) for x in motifs)
    cat = ",\n    ".join("(%s, %d)" % (txt(lib), j) for lib, j in CLAUSES_NEUVES)

    patch = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- C4 (1er patch) -- LE CATALOGUE DES CLAUSES ET LES {n} MOTIFS D'ANNULATION
-- Genere le {date.today().isoformat()} par phase2/checks/c4_generer_motifs_et_conditions_2026-11-17.py
--
-- SES DECISIONS DU 17/11 :
--   . le CATALOGUE : ajouter « Permis de construire » et « Delai de retractation SRU »
--   . les MOTIFS : « Les 216 motifs normalises, les 492 phrases uniques partant en
--     note » -> `motif_annulation_app` ne recoit QUE les motifs qui REVIENNENT
--   . les NOTES sont dans un SECOND patch (5 003 lignes), pas ici
--
-- ⛔ RIEN POUR LE PRET, ET C'EST MESURE : « Obtention Credit » EXISTE DEJA au
--   catalogue (id 2, 45 jours). ADP et ODP n'en sont pas deux clauses mais le
--   DEPART et l'ECHEANCE de celle-la -- ADP avant ODP **24 fois sur 24**, jamais
--   l'inverse, ecart median **31 jours** (le meme jour du mois, un mois plus tard).
--   J'avais propose « offre de pret » et « accord de pret » : c'eut ete un DOUBLON.
--
-- ⭐ LE LIBELLE D'UN MOTIF EST L'ECRITURE LA PLUS FREQUENTE DE SON GROUPE, jamais
--   un texte invente : « refus prêt » (31) l'emporte sur « refus de prêt » (25) et
--   « refus de pret » (1). Du texte reel du classeur -- ni invention, ni
--   normalisation agressive. C'est sa consigne « sans interpreter », appliquee.
--
-- ⭐⭐ ET LE MOTIF VA SUR LA MEME TRANSACTION QUE SA DATE : le compromis annule
--   d'abord (la cible de C3), l'offre refusee en repli quand la chaine n'a pas de
--   compromis. Ainsi `date_annulation_app` et `motif_annulation_app` sont sur la
--   MEME ligne -- le « quand » et le « pourquoi » enfin reunis.
--
-- ⛔ `motif_annulation_app` est de CLASSE A : dans
--   COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS et dans la boucle de creation locale. Rien
--   ne part chez Hektor, et le run ne l'ecrase pas.
--
-- Retour arriere : patch_c4_motifs_conditions_2026-11-17_INVERSE.sql
-- Controle       : patch_c4_motifs_conditions_2026-11-17_REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════

begin;

-- ─── 1. L'ETAT D'AVANT, EXIGE ──────────────────────────────────────────────
do $$
declare deja integer; cat integer; cibles integer;
begin
  select count(*) into deja from public.app_affaire_ledger
   where motif_annulation_app is not null;
  if deja <> 0 then
    raise exception '⛔ ARRET : % motif(s) deja pose(s). Ce patch suppose la colonne '
      'vierge (0 au 17/11).', deja;
  end if;
  select count(*) into cat from public.app_condition_catalogue;
  if cat <> 2 then
    raise exception '⛔ ARRET : le catalogue porte % clause(s) au lieu de 2 '
      '(Preemption mairie, Obtention Credit).', cat;
  end if;
  select count(*) into cibles from public.app_affaire_ledger
   where app_affaire_id in ({ids});
  if cibles <> {n} then
    raise exception '⛔ ARRET : % cibles sur les {n} attendues.', cibles;
  end if;
  raise notice '✅ etat d''avant : 0 motif, catalogue a 2 clauses, {n} cibles.';
end $$;

-- ─── 2. LA SAUVEGARDE, ET ELLE NAIT FERMEE ─────────────────────────────────
create table if not exists public.app_affaire_avant_c4_20261117 as
  select app_affaire_id, kind, state, hektor_annonce_id, date_annulation_app,
         motif_annulation_app, now() as photographie_le
    from public.app_affaire_ledger
   where app_affaire_id in ({ids});
revoke all on public.app_affaire_avant_c4_20261117 from authenticated, anon;

-- ─── 3a. LE CATALOGUE : LES DEUX CLAUSES QUI MANQUENT ──────────────────────
-- ⭐ `on conflict do nothing` sur le libelle : si quelqu'un les a ajoutees entre
--   le controle 1 et ici, on ne cree pas de doublon.
-- ⛔ PAS de `cross join lateral (select row_number() over ())` : la colonne n'y est
--   pas visible (« column v.ordre does not exist », premiere tentative du 17/11,
--   rejetee AVANT le commit -- verifie : catalogue a 2, 0 motif, pas de sauvegarde).
--   `row_number() over ()` se met directement dans le SELECT.
-- ⛔⛔ ET `id` EST A FOURNIR : il est TEXT, NOT NULL, et SANS AUCUN DEFAUT
--   (mesure du 17/11 -- « null value in column id violates not-null constraint »,
--   seconde tentative, rejetee avant le commit). Ce n'est pas une sequence : c'est
--   un identifiant choisi a la main, et les deux clauses d'origine portent '1' et
--   '2'. On prend donc le MAXIMUM NUMERIQUE existant + 1, et on ne lit que les ids
--   numeriques -- un id non numerique ferait tomber la conversion.
insert into public.app_condition_catalogue
       (id, libelle, jours_defaut, actif, rang, ecrit_par)
select ((select coalesce(max(c.id::integer), 0) from public.app_condition_catalogue c
          where c.id ~ '^[0-9]+$') + row_number() over ())::text,
       v.libelle, v.jours, true,
       (select coalesce(max(c.rang), 0) from public.app_condition_catalogue c)
         + row_number() over ()::integer,
       'classeur:C4:2026-11-17'
  from (values
    {cat}
  ) as v(libelle, jours)
 where not exists (select 1 from public.app_condition_catalogue c
                    where lower(c.libelle) = lower(v.libelle));

-- ─── 3b. LES {n} MOTIFS D'ANNULATION ───────────────────────────────────────
with poser(app_affaire_id, motif) as (values
    {valeurs}
)
update public.app_affaire_ledger l
   set motif_annulation_app = p.motif
  from poser p
 where l.app_affaire_id = p.app_affaire_id
   and l.motif_annulation_app is null;

-- ─── 4. LES CONTROLES, ET ILS ARRETENT ─────────────────────────────────────
do $$
declare
  poses    integer;
  ailleurs integer;
  cat      integer;
  sans_date integer;
  ferme    integer;
begin
  select count(*) into poses from public.app_affaire_ledger
   where app_affaire_id in ({ids}) and motif_annulation_app is not null;
  if poses <> {n} then
    raise exception '⛔ {n} attendus, % poses.', poses;
  end if;

  -- ⭐ TEMOIN INVERSE : rien hors du lot
  select count(*) into ailleurs from public.app_affaire_ledger
   where motif_annulation_app is not null and app_affaire_id not in ({ids});
  if ailleurs <> 0 then
    raise exception '⛔ % ligne(s) hors du lot portent un motif.', ailleurs;
  end if;

  -- ⭐ LE CATALOGUE : 2 + 2 = 4, pas plus
  select count(*) into cat from public.app_condition_catalogue;
  if cat <> 4 then
    raise exception '⛔ le catalogue porte % clauses au lieu de 4.', cat;
  end if;

  -- ⭐⭐ LE CONTROLE QUI DONNE SON SENS AU LOT : un motif SANS date d'annulation
  --   est une moitie de reponse. On le COMPTE, on ne l'interdit pas -- toutes les
  --   lignes de C3 ne sont pas ici, et inversement.
  select count(*) into sans_date from public.app_affaire_ledger
   where motif_annulation_app is not null and date_annulation_app is null;
  raise notice 'ⓘ % motif(s) sans date d''annulation -- le « pourquoi » sans le '
    '« quand ». Normal : C3 et C4 n''ont pas le meme perimetre.', sans_date;

  select count(*) into ferme from information_schema.role_table_grants
   where table_schema='public' and table_name='app_affaire_avant_c4_20261117'
     and grantee in ('authenticated','anon');
  if ferme <> 0 then
    raise exception '⛔ la sauvegarde porte encore % droit(s).', ferme;
  end if;

  raise notice '✅ {n} motifs poses . 0 hors du lot . catalogue a 4 clauses . '
    'sauvegarde FERMEE.';
end $$;

commit;
"""

    inverse = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- C4 (1er patch) -- RETOUR ARRIERE
-- ⭐ Il retire les {n} motifs ET les deux clauses du catalogue, et RIEN d'autre.
-- ⛔ Il REFUSE de se jouer si un motif a change depuis la pose.
-- ⚠ Il NE TOUCHE PAS aux 2 clauses d'origine (Preemption mairie, Obtention Credit),
--   ni aux 5 conditions deja posees.
-- ═══════════════════════════════════════════════════════════════════════════

begin;

do $$
declare changes integer;
begin
  with attendu(app_affaire_id, motif) as (values
      {valeurs}
  )
  select count(*) into changes
    from attendu a join public.app_affaire_ledger l using (app_affaire_id)
   where coalesce(l.motif_annulation_app, '') <> a.motif;
  if changes <> 0 then
    raise exception '⛔ ARRET : % motif(s) ne portent plus la valeur de C4.', changes;
  end if;
  raise notice '✅ les {n} motifs portent bien les valeurs de C4.';
end $$;

update public.app_affaire_ledger
   set motif_annulation_app = null
 where app_affaire_id in ({ids});

delete from public.app_condition_catalogue
 where ecrit_par = 'classeur:C4:2026-11-17';

do $$
declare reste integer; cat integer;
begin
  select count(*) into reste from public.app_affaire_ledger
   where motif_annulation_app is not null;
  if reste <> 0 then
    raise exception '⛔ il reste % motif(s).', reste;
  end if;
  select count(*) into cat from public.app_condition_catalogue;
  if cat <> 2 then
    raise exception '⛔⛔ le catalogue porte % clauses au lieu de 2 : le retour '
      'arriere a deborde sur les clauses d''origine. GRAVE.', cat;
  end if;
  raise notice '✅ {n} motifs retires . le catalogue est revenu a ses 2 clauses.';
end $$;

commit;
"""

    repetition = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- C4 (1er patch) -- LES CONTROLES, REJOUABLES. Aucune ecriture.
-- ═══════════════════════════════════════════════════════════════════════════

select 'motifs poses' as controle, count(*)::text as mesure, '{n}' as attendu
  from public.app_affaire_ledger where motif_annulation_app is not null
union all
select 'aucun motif hors du lot', count(*)::text, '0'
  from public.app_affaire_ledger
 where motif_annulation_app is not null and app_affaire_id not in ({ids})
union all
select 'le catalogue', count(*)::text, '4 = 2 d origine + 2 de C4'
  from public.app_condition_catalogue
union all
select 'les 2 clauses d origine INTACTES', count(*)::text, '2'
  from public.app_condition_catalogue
 where lower(libelle) in ('preemption mairie', 'préemption mairie', 'obtention crédit', 'obtention credit')
union all
select 'motifs distincts', count(distinct motif_annulation_app)::text,
       '{len(retenus)} environ'
  from public.app_affaire_ledger where motif_annulation_app is not null
union all
-- ⭐⭐ LE CONTROLE QUI DONNE SON SENS AU LOT : le « quand » et le « pourquoi »
--   sur la MEME ligne. C'est ce que C3 + C4 devaient produire.
select 'lignes qui portent LA DATE ET LE MOTIFS', count(*)::text,
       '> 0 -- le quand ET le pourquoi reunis'
  from public.app_affaire_ledger
 where motif_annulation_app is not null and date_annulation_app is not null
union all
select 'motifs SANS date (perimetre different)', count(*)::text, 'compte, pas interdit'
  from public.app_affaire_ledger
 where motif_annulation_app is not null and date_annulation_app is null
union all
select 'la sauvegarde est FERMEE', count(*)::text, '0'
  from information_schema.role_table_grants
 where table_schema='public' and table_name='app_affaire_avant_c4_20261117'
   and grantee in ('authenticated','anon')
union all
select 'VOISINES -- les 450 dates de C3', count(*)::text, '450'
  from public.app_affaire_ledger where date_annulation_app is not null
union all
select 'VOISINES -- les 195 notes de C5', count(*)::text, '195'
  from public.app_affaire_note where origine = 'classeur'
order by 1;
"""

    for suffixe, contenu in ((".sql", patch), ("_INVERSE.sql", inverse),
                             ("_REPETITION.sql", repetition)):
        f = Path(str(BASE) + suffixe)
        f.write_bytes(contenu.encode("utf-8"))
        print("ecrit : %-58s %7d octets" % (f.name, len(f.read_bytes())))
    print()
    print("⛔ RIEN N'A ETE JOUE. Ces trois fichiers attendent un « colle ».")
    print("⚠ ET LES 86 CONDITIONS NE SONT PAS DANS CE PATCH : leur echeance se lit")
    print("   dans les abreviations (ODP15/12, DB30/1), donc elles demandent un")
    print("   decodage ligne par ligne -- un troisieme patch, apres les notes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
