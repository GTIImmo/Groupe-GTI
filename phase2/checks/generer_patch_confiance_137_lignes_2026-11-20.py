"""Chantier classeur, ⑮ -- GENERE le patch « confiance » des 137 lignes (accorde par Frederic le 20/11).

Ses mots : « LES 97 LIGNES DE CONFIANCE qui n'attendent rien : OUI, colle-les, avec la repetition montree comme pour
la table. Les 40 autres apres V2. » -- « NKDC0I1M : garde-la, son etiquette ne change pas. »

CE QUE FAIT CE SCRIPT (lecture seule) :
  . lit la liste notice/TEMPS8_LES_137_LIGNES_DU_PATCH_CONFIANCE_2026-11-20.csv (ecrite par temps8) ;
  . relit le gel VIVANT chez Supabase et EXIGE, ligne par ligne, que ses liens soient EXACTEMENT ceux que la mesure
    a juges (pour les 40 de la partie B : ceux que V2 devait laisser -- c'est la preuve que V2 a fait ce qu'on a
    mesure) ; un seul ecart -> rien n'est genere (code 1) ;
  . ecrit supabase/patch_confiance_gel_137_lignes_2026-11-20.sql (+ _INVERSE, _REPETITION).

LE PATCH : la confiance SEULE passe a « sure » sur les liens de ces 137 lignes qui ne le sont pas -- etage, preuves,
gele_par, gele_le, role, ligne : INTACTS. Garde par compte ET empreinte (ID, transaction, role) du gel a l'instant de
la generation, et par la confiance d'avant de chaque lien vise. Sauvegarde datee fermee des sa naissance. Controle dans
la meme transaction : chaque lien vise est « sure », AUCUN autre lien n'a change (toutes colonnes), les 137 lignes
n'ont plus un seul lien non sur. ⛔ Il porte son `commit;`.

Usage : python -u phase2/checks/generer_patch_confiance_137_lignes_2026-11-20.py
"""
from __future__ import annotations

import csv
import hashlib
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))
from phase2.sync import push_upgrade_to_supabase as P  # noqa: E402

LISTE = RACINE / "notice" / "TEMPS8_LES_137_LIGNES_DU_PATCH_CONFIANCE_2026-11-20.csv"
PATCH = RACINE / "supabase" / "patch_confiance_gel_137_lignes_2026-11-20.sql"
INVERSE = RACINE / "supabase" / "patch_confiance_gel_137_lignes_2026-11-20_INVERSE.sql"
REPETITION = RACINE / "supabase" / "patch_confiance_gel_137_lignes_2026-11-20_REPETITION.sql"
SAUVEGARDE = "app_classeur_lien_avant_confiance_20261120"
SURE = "sûre"


def sql_txt(s: str) -> str:
    return "'" + str(s).replace("'", "''") + "'"


def main() -> int:
    with LISTE.open(encoding="utf-8-sig", newline="") as f:
        liste = list(csv.DictReader(f, delimiter=";"))
    parties = {r["id_unique"]: r["partie"] for r in liste}
    attendus = {r["id_unique"]: {int(x) for x in r["tous_les_liens_apres_v2"].split()} for r in liste}
    print("liste : %d lignes (A %d, B %d)" % (len(liste), sum(v == "A" for v in parties.values()),
                                              sum(v == "B" for v in parties.values())), flush=True)
    if (len(liste), sum(v == "A" for v in parties.values())) != (137, 97):
        print("⛔ 137 lignes dont 97 en A attendues", flush=True)
        return 1

    P.load_env_files(P.DEFAULT_ENV_FILES)
    url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
    c = P.SupabaseRestClient(base_url=url, service_role_key=os.environ["SUPABASE_SERVICE_ROLE_KEY"])
    gel = c.fetch_all_rows(path="app_classeur_lien", select="id_unique,app_affaire_id,role,confiance",
                           order="id_unique.asc,app_affaire_id.asc")
    n = len(gel)
    emp = hashlib.md5(",".join("%s:%s:%s" % (r["id_unique"], r["app_affaire_id"], r["role"]) for r in
                               sorted(gel, key=lambda r: (r["id_unique"].encode(), r["app_affaire_id"])))
                      .encode("utf-8")).hexdigest()
    print("gel vivant : %d liens, empreinte %s (attendu 12820 apres V2)" % (n, emp), flush=True)
    if n != 12820:
        print("⛔ le gel n'a pas le compte d'apres V2", flush=True)
        return 1
    par_ligne = defaultdict(dict)
    for r in gel:
        par_ligne[r["id_unique"]][int(r["app_affaire_id"])] = (r["role"], r["confiance"])

    ecarts = []
    vises = []
    for i in sorted(parties):
        vivants = set(par_ligne.get(i, {}))
        if vivants != attendus[i]:
            ecarts.append("%s (%s) : vivant %s / mesure %s" % (i, parties[i], sorted(vivants), sorted(attendus[i])))
            continue
        for a, (role, conf) in sorted(par_ligne[i].items()):
            if conf != SURE:
                vises.append((i, a, role, conf, parties[i]))
    print("ECARTS entre le gel vivant et la mesure : %d (attendu 0)" % len(ecarts), flush=True)
    for e in ecarts:
        print("   ⛔ " + e, flush=True)
    if ecarts:
        return 1
    deja = sum(1 for i in parties for a, (r_, c_) in par_ligne[i].items() if c_ == SURE)
    print("liens vises (non surs) : %d -- partie A %d, partie B %d ; deja surs sur ces lignes : %d"
          % (len(vises), sum(v[4] == "A" for v in vises), sum(v[4] == "B" for v in vises), deja), flush=True)
    from collections import Counter
    print("   leur confiance d'avant : %s" % dict(Counter(v[3] for v in vises)), flush=True)

    valeurs = ",\n    ".join("(%s, %d, %s, %s)" % (sql_txt(i), a, sql_txt(r), sql_txt(cf)) for i, a, r, cf, _ in vises)
    lignes_sql = ",".join(sql_txt(i) for i in sorted(parties))
    nv = len(vises)
    quand = datetime.now().strftime("%d/%m/%Y %H:%M")
    entete = f"""-- ═══════════════════════════════════════════════════════════════════════════════
-- LA CONFIANCE DES 137 LIGNES CONFIRMEES PAR LES AUDITS -> « sure »           20/11/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- ACCORDE PAR FREDERIC le 20/11 : « LES 97 LIGNES DE CONFIANCE qui n'attendent rien : OUI, colle-les, avec la
--   repetition montree comme pour la table. Les 40 autres apres V2. » ; « NKDC0I1M : garde-la ».
-- GENERE le {quand} par phase2/checks/generer_patch_confiance_137_lignes_2026-11-20.py, depuis
--   notice/TEMPS8_LES_137_LIGNES_DU_PATCH_CONFIANCE_2026-11-20.csv et le gel VIVANT (relu : chaque ligne porte
--   exactement les liens mesures). Ne pas le retoucher a la main.
-- CE QU'IL FAIT : {nv} liens de ces 137 lignes passent a « sure ». RIEN D'AUTRE : etage, preuves, gele_par,
--   gele_le, role, ligne_classeur INTACTS ; aucun lien ajoute ni retire.
-- ⛔⛔ IL PORTE SON `commit;` : joue « pour voir », IL SE COMMITE.
-- RETOUR ARRIERE : patch_confiance_gel_137_lignes_2026-11-20_INVERSE.sql
-- CONTROLE       : patch_confiance_gel_137_lignes_2026-11-20_REPETITION.sql (lecture seule)
-- ═══════════════════════════════════════════════════════════════════════════════
"""
    PATCH.write_text(entete + f"""begin;

-- ── ① LA GARDE : le gel est celui qu'on a relu, et chaque lien vise a la confiance d'avant ──
do $$
declare n int; emp text; ko int;
begin
  select count(*), md5(string_agg(id_unique||':'||app_affaire_id||':'||role, ','
                                  order by id_unique collate "C", app_affaire_id))
    into n, emp from app_classeur_lien;
  if n <> {n} or emp <> '{emp}' then
    raise exception '⛔ garde : le gel a bouge (% liens, empreinte %) -- rien n''est ecrit', n, emp;
  end if;
  if to_regclass('public.{SAUVEGARDE}') is not null then
    raise exception '⛔ garde : la sauvegarde {SAUVEGARDE} existe deja -- ce patch a-t-il deja ete joue ?';
  end if;
  select count(*) into ko from (values
    {valeurs}
  ) v(id_unique, app_affaire_id, role, avant)
  left join app_classeur_lien l on l.id_unique = v.id_unique and l.app_affaire_id = v.app_affaire_id
   where l.id_unique is null or l.role <> v.role or l.confiance <> v.avant;
  if ko <> 0 then raise exception '⛔ garde : % lien(s) vise(s) absent(s) ou deja change(s)', ko; end if;
end $$;

-- ── ② LA SAUVEGARDE DATEE, FERMEE DES SA NAISSANCE ──
create table {SAUVEGARDE} as select * from app_classeur_lien;
revoke all on {SAUVEGARDE} from public, anon, authenticated;
alter table {SAUVEGARDE} enable row level security;

-- ── ③ LA CONFIANCE, ET RIEN D'AUTRE ──
update app_classeur_lien l set confiance = 'sûre'
  from (values
    {valeurs}
  ) v(id_unique, app_affaire_id, role, avant)
 where l.id_unique = v.id_unique and l.app_affaire_id = v.app_affaire_id;

-- ── ④ LE CONTROLE, DANS LA MEME TRANSACTION ──
do $$
declare n int; poses int; restes int; temoin int; garde int;
begin
  select count(*) into n from app_classeur_lien;
  if n <> {n} then raise exception '⛔ le gel porte % liens, attendu {n}', n; end if;
  select count(*) into garde from {SAUVEGARDE};
  if garde <> {n} then raise exception '⛔ sauvegarde : % au lieu de {n}', garde; end if;
  -- ⭐ TEMOIN POSITIF : exactement {nv} liens ont change, tous vers « sure »
  select count(*) into poses from app_classeur_lien l join {SAUVEGARDE} s using (id_unique, app_affaire_id)
   where l.confiance is distinct from s.confiance;
  if poses <> {nv} then raise exception '⛔ % lien(s) changes, attendu {nv}', poses; end if;
  -- ⭐ les 137 lignes n'ont plus un seul lien non sur
  select count(*) into restes from app_classeur_lien where id_unique in ({lignes_sql}) and confiance <> 'sûre';
  if restes <> 0 then raise exception '⛔ % lien(s) encore non surs sur les 137 lignes', restes; end if;
  -- ⭐ TEMOIN INVERSE : hors confiance des liens vises, RIEN n'a change, colonne par colonne
  select count(*) into temoin from app_classeur_lien l join {SAUVEGARDE} s using (id_unique, app_affaire_id)
   where (l.role, l.preuves, l.etage, l.gele_par, l.ligne_classeur, l.gele_le)
         is distinct from (s.role, s.preuves, s.etage, s.gele_par, s.ligne_classeur, s.gele_le)
      or (l.confiance is distinct from s.confiance and l.id_unique not in ({lignes_sql}));
  if temoin <> 0 then raise exception '⛔ temoin inverse : % lien(s) non vise(s) ou colonne(s) non visee(s) ont change', temoin; end if;
  raise notice '✅ confiance : {nv} liens -> sure sur 137 lignes ; gel {n} liens, rien d''autre n''a change.';
end $$;

commit;
""", encoding="utf-8")

    INVERSE.write_text(f"""-- INVERSE de patch_confiance_gel_137_lignes_2026-11-20.sql -- il ne juge QUE sa part (lecon 31).
-- Il rend a chaque lien vise la confiance de la sauvegarde {SAUVEGARDE}, SEULEMENT si ce lien n'a rien
-- d'autre de change depuis ; sinon il refuse et n'ecrit rien. La sauvegarde est GARDEE (un numero ne se perd jamais).
-- ⛔ Il porte son `commit;`.
begin;
do $$
declare manque int; bouge int;
begin
  if to_regclass('public.{SAUVEGARDE}') is null then
    raise exception '⛔ la sauvegarde {SAUVEGARDE} manque -- le patch n''a pas ete joue ?';
  end if;
  select count(*) into manque from (values
    {valeurs}
  ) v(id_unique, app_affaire_id, role, avant)
  left join app_classeur_lien l on l.id_unique = v.id_unique and l.app_affaire_id = v.app_affaire_id
   where l.id_unique is null;
  if manque <> 0 then raise exception '⛔ % lien(s) vise(s) n''existent plus : un autre geste est passe -- rien n''est ecrit', manque; end if;
  select count(*) into bouge from app_classeur_lien l join {SAUVEGARDE} s using (id_unique, app_affaire_id)
   where l.id_unique in ({lignes_sql})
     and (l.role, l.preuves, l.etage, l.gele_par, l.ligne_classeur, l.gele_le)
         is distinct from (s.role, s.preuves, s.etage, s.gele_par, s.ligne_classeur, s.gele_le);
  if bouge <> 0 then raise exception '⛔ % lien(s) de ces lignes ont change autrement -- rien n''est ecrit', bouge; end if;
end $$;
update app_classeur_lien l set confiance = s.confiance
  from {SAUVEGARDE} s,
       (values
    {valeurs}
  ) v(id_unique, app_affaire_id, role, avant)
 where l.id_unique = v.id_unique and l.app_affaire_id = v.app_affaire_id
   and s.id_unique = v.id_unique and s.app_affaire_id = v.app_affaire_id and l.confiance = 'sûre';
do $$
declare restes int;
begin
  select count(*) into restes from app_classeur_lien l join {SAUVEGARDE} s using (id_unique, app_affaire_id)
   where l.id_unique in ({lignes_sql}) and l.confiance is distinct from s.confiance;
  if restes <> 0 then raise exception '⛔ % lien(s) n''ont pas retrouve leur confiance d''avant', restes; end if;
  raise notice '✅ inverse : les {nv} liens ont retrouve leur confiance d''avant ; la sauvegarde est gardee.';
end $$;
commit;
""", encoding="utf-8")

    REPETITION.write_text(f"""-- REPETITION de patch_confiance_gel_137_lignes_2026-11-20.sql -- LECTURE SEULE, a jouer APRES le patch.
select json_build_object(
  'liens', (select count(*) from app_classeur_lien), 'attendu_liens', {n},
  'sauvegarde', (select count(*) from {SAUVEGARDE}), 'attendu_sauvegarde', {n},
  'liens_changes', (select count(*) from app_classeur_lien l join {SAUVEGARDE} s using (id_unique, app_affaire_id)
                     where l.confiance is distinct from s.confiance), 'attendu_changes', {nv},
  'changes_vers_autre_chose_que_sure', (select count(*) from app_classeur_lien l join {SAUVEGARDE} s using (id_unique, app_affaire_id)
                     where l.confiance is distinct from s.confiance and l.confiance <> 'sûre'), 'attendu_autre', 0,
  'non_surs_sur_les_137', (select count(*) from app_classeur_lien where id_unique in ({lignes_sql}) and confiance <> 'sûre'), 'attendu_non_surs', 0,
  'lignes_du_patch_presentes', (select count(distinct id_unique) from app_classeur_lien where id_unique in ({lignes_sql})), 'attendu_lignes', 137,
  'autres_colonnes_changees', (select count(*) from app_classeur_lien l join {SAUVEGARDE} s using (id_unique, app_affaire_id)
     where (l.role, l.preuves, l.etage, l.gele_par, l.ligne_classeur, l.gele_le)
        is distinct from (s.role, s.preuves, s.etage, s.gele_par, s.ligne_classeur, s.gele_le)), 'attendu_autres_colonnes', 0,
  'changes_hors_des_137', (select count(*) from app_classeur_lien l join {SAUVEGARDE} s using (id_unique, app_affaire_id)
     where l.confiance is distinct from s.confiance and l.id_unique not in ({lignes_sql})), 'attendu_hors', 0,
  'par_confiance', (select json_object_agg(confiance, c) from (select confiance, count(*) c from app_classeur_lien group by 1) x),
  'transactions_prises_deux_fois', (select count(*) from (select app_affaire_id from app_classeur_lien
                                     group by 1 having count(distinct id_unique) > 1) x), 'attendu_deux_fois', 0,
  'sauvegarde_fermee', (select relrowsecurity from pg_class where oid = 'public.{SAUVEGARDE}'::regclass)
    and not exists (select 1 from information_schema.role_table_grants where table_name = '{SAUVEGARDE}'
                    and grantee in ('anon', 'authenticated')), 'attendu_fermee', true
) r;
""", encoding="utf-8")
    for p_ in (PATCH, INVERSE, REPETITION):
        print("ECRIT : %s (%d octets)" % (p_.relative_to(RACINE), p_.stat().st_size), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
