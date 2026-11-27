#!/usr/bin/env python3
"""FABRIQUE LE PATCH « L'ANCIEN NUMERO DANS SA LIGNE DU JOURNAL » -- chantier classeur, ㉑bis, 22/11/2026 (soir).

Son mot (reponses au rapport 21 bis, point 1 a) : « L'ANCIEN NUMERO RESTE TRACE. Le journal des etiquettes existe
  (11 657 lignes) : chaque changement doit y laisser sa ligne, avec l'ancien et le neuf. »

LA MESURE DU 22/11 (lecture seule) : chaque changement laisse BIEN sa ligne (pose 11 454, propagation 13, fusion 47,
  scission 143 = 11 657). MAIS l'ancien numero n'y est PAS ecrit :
    . une ligne de SCISSION porte l'ANCIEN uuid (dossier_uuid) avec le NEUF numero (dossier_numero) et le neuf uuid
      (autre_uuid) -- 141 des 143 portent le numero de la neuve, 0 celui de l'ancienne ;
    . une ligne de FUSION porte le dossier garde (uuid + numero) et l'uuid absorbe, SANS son numero.
  L'ancien numero se RETROUVE par la ligne de naissance de l'ancien uuid (190 sur 190), mais pas dans la ligne du
  changement. Ce patch l'y ecrit.

CE QUE FAIT CE SCRIPT : il LIT la fonction en production (pooler, lecture seule), verifie que chaque ancre y est presente
  le nombre de fois attendu, et ECRIT trois fichiers dans supabase/ -- le patch, sa repetition, son inverse. Il ne joue
  RIEN. Le patch se colle par Frederic, s'il le veut.
USAGE : python -u phase2/checks/fabriquer_patch_journal_ancien_numero.py
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import protocole_classeur as P  # noqa: E402

SUPA = P.RACINE / "supabase"
NOM = "patch_journal_ancien_numero_2026-11-22"
FONCTION = "public.app_poser_etiquettes_dossier"
CK_OLD = "CHECK ((evenement = ANY (ARRAY['pose'::text, 'propagation'::text, 'fusion'::text, 'scission'::text])))"

# (ancre sur UNE ligne, remplacement, nombre attendu) -- lecon 30 : des ancres d'une seule ligne
REMPLACEMENTS = [
    ("         l.app_dossier_uuid as absorbee\n",
     "         l.app_dossier_uuid as absorbee, l.app_dossier_numero as absorbee_num\n", 1),
    ("      (evenement, dossier_uuid, dossier_numero, autre_uuid, app_chaine_id, transactions, combien, pourquoi)\n",
     "      (evenement, dossier_uuid, dossier_numero, autre_uuid, app_chaine_id, transactions, combien, pourquoi,\n"
     "       ancien_numero)\n", 2),
    ("           'deux dossiers etiquetes reunis dans un seul groupe'\n",
     "           'deux dossiers etiquetes reunis dans un seul groupe',\n"
     "           f.absorbee_num\n", 1),
    ("    from _fusions f group by f.garde, f.garde_num, f.absorbee, f.app_chaine_id;\n",
     "    from _fusions f group by f.garde, f.garde_num, f.absorbee, f.app_chaine_id, f.absorbee_num;\n", 1),
    ("           'le dossier s''est coupe : cette part recoit une etiquette neuve'\n",
     "           'le dossier s''est coupe : cette part recoit une etiquette neuve',\n"
     "           min(l.app_dossier_numero)\n", 1),
]

NAISSANCES = """(select dossier_uuid as u, dossier_numero as n from public.app_dossier_etiquette_journal where evenement = 'pose'
     union all
     select autre_uuid, dossier_numero from public.app_dossier_etiquette_journal where evenement = 'scission')"""

# L'EPREUVE A BLANC DES DEUX SELECT NEUFS, EN LECTURE SEULE : les tables temporaires de la RPC refaites en CTE, a
#   l'identique. Une faute de regroupement se voit a l'ANALYSE de la requete, meme quand elle ne rend aucune ligne.
EPREUVE_SELECT = """with multi as (
    select app_chaine_id from public.app_affaire_ledger
    where app_chaine_id is not null and app_dossier_uuid is not null
    group by app_chaine_id having count(distinct app_dossier_uuid) > 1
  ),
  gagnante as (
    select distinct on (l.app_chaine_id)
           l.app_chaine_id, l.app_dossier_uuid as garde, l.app_dossier_numero as garde_num
    from public.app_affaire_ledger l join multi using (app_chaine_id)
    where l.app_dossier_uuid is not null
    order by l.app_chaine_id, l.app_affaire_id
  ),
  _fusions as (
    select l.app_affaire_id, l.app_chaine_id, g.garde, g.garde_num,
           l.app_dossier_uuid as absorbee, l.app_dossier_numero as absorbee_num
    from public.app_affaire_ledger l join gagnante g using (app_chaine_id)
    where l.app_dossier_uuid is not null and l.app_dossier_uuid is distinct from g.garde
  ),
  etalees as (
    select app_dossier_uuid from public.app_affaire_ledger
    where app_dossier_uuid is not null and app_chaine_id is not null
    group by app_dossier_uuid having count(distinct app_chaine_id) > 1
  ),
  tete as (
    select distinct on (l.app_dossier_uuid) l.app_dossier_uuid, l.app_chaine_id as garde_chaine
    from public.app_affaire_ledger l join etalees using (app_dossier_uuid)
    order by l.app_dossier_uuid, l.app_affaire_id
  ),
  _scissions_num as (
    select distinct l.app_dossier_uuid as ancienne, l.app_chaine_id,
           public.app_dossier_annee_ouverture(l.app_chaine_id) as annee, 1 as rang, gen_random_uuid() as neuve
    from public.app_affaire_ledger l
    join tete t on t.app_dossier_uuid = l.app_dossier_uuid
    where l.app_chaine_id is distinct from t.garde_chaine
  ),
  ligne_fusion as (
    select 'fusion' as evenement, f.garde, f.garde_num, f.absorbee, f.app_chaine_id,
           array_agg(f.app_affaire_id order by f.app_affaire_id) as transactions, count(*) as combien,
           'deux dossiers etiquetes reunis dans un seul groupe' as pourquoi,
           f.absorbee_num as ancien_numero
    from _fusions f group by f.garde, f.garde_num, f.absorbee, f.app_chaine_id, f.absorbee_num
  ),
  ligne_scission as (
    select 'scission' as evenement, s.ancienne, public.app_dossier_numero_format(s.annee, s.rang) as numero,
           s.neuve, s.app_chaine_id,
           array_agg(l.app_affaire_id order by l.app_affaire_id) as transactions, count(*) as combien,
           'le dossier s''est coupe : cette part recoit une etiquette neuve' as pourquoi,
           min(l.app_dossier_numero) as ancien_numero
    from _scissions_num s
    join public.app_affaire_ledger l on l.app_chaine_id = s.app_chaine_id
                                    and l.app_dossier_uuid = s.ancienne
    group by s.ancienne, s.neuve, s.annee, s.rang, s.app_chaine_id
  )
select (select count(*) from ligne_fusion) as fusions_en_attente,
       (select count(*) from ligne_scission) as scissions_en_attente,
       (select count(*) from ligne_fusion where ancien_numero is null)
     + (select count(*) from ligne_scission where ancien_numero is null) as sans_ancien_numero"""


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    cn, cu = P.pooler()
    cu.execute("select pg_get_functiondef(%s::regproc), md5(pg_get_functiondef(%s::regproc))", (FONCTION, FONCTION))
    texte, md5_avant = cu.fetchone()
    cu.execute(EPREUVE_SELECT)
    epreuve = cu.fetchone()
    cu.execute("select exists (select 1 from information_schema.columns where table_schema = 'public' and table_name = "
               "'app_dossier_etiquette_journal' and column_name = 'ancien_numero')")
    deja = cu.fetchone()[0]
    cn.rollback()
    cn.close()
    assert hashlib.md5(texte.encode("utf-8")).hexdigest() == md5_avant, "md5 local et md5 Postgres different"
    assert "\r" not in texte, "un retour chariot dans la fonction lue"
    if deja:
        print("⛔ la colonne ancien_numero existe DEJA chez Supabase -- rien a fabriquer")
        return 1
    print("fonction lue : %d caracteres, md5 %s" % (len(texte), md5_avant))
    print("epreuve a blanc des deux SELECT neufs (lecture seule) : fusions en attente %s, scissions en attente %s, "
          "sans ancien numero %s -- la requete est ANALYSEE, donc valide" % epreuve)
    neuf = texte
    for ancre, par, n in REMPLACEMENTS:
        k = neuf.count(ancre)
        if k != n:
            print("⛔ ancre trouvee %d fois (attendu %d) : %r" % (k, n, ancre[:80]))
            return 1
        neuf = neuf.replace(ancre, par)
    n_mot = neuf.count("ancien_numero")
    print("fonction neuve : %d caracteres, « ancien_numero » %d fois, « absorbee_num » %d fois" % (
        len(neuf), n_mot, neuf.count("absorbee_num")))

    entete = """-- ═══════════════════════════════════════════════════════════════════════════
-- L'ANCIEN NUMERO DANS SA LIGNE DU JOURNAL DES ETIQUETTES        22/11/2026 (soir)
-- Fabrique par phase2/checks/fabriquer_patch_journal_ancien_numero.py -- NE PAS RETOUCHER A LA MAIN.
--
-- SON MOT (reponses au rapport 21 bis, point 1 a) : « L'ANCIEN NUMERO RESTE TRACE. [...] chaque changement doit y
--   laisser sa ligne, avec l'ancien et le neuf. »
--
-- LA MESURE (lecture seule, 22/11) : chaque changement laisse BIEN sa ligne -- pose 11 454, propagation 13,
--   fusion 47, scission 143. Mais l'ANCIEN NUMERO n'y est pas ecrit :
--     . SCISSION : dossier_uuid = l'ANCIEN uuid, dossier_numero = le NEUF numero (141 sur 143 ; 0 l'ancien) ;
--     . FUSION   : dossier_uuid / dossier_numero = le dossier GARDE, autre_uuid = l'absorbe, SANS son numero.
--   L'ancien numero se retrouve par la ligne de naissance de l'ancien uuid (190 sur 190), pas dans la ligne.
--
-- CE QUE LE PATCH FAIT :
--   1. une colonne neuve, ancien_numero (texte, vide pour une pose ou une propagation) ;
--   2. la RPC app_poser_etiquettes_dossier l'ecrit a CHAQUE fusion (le numero absorbe) et a CHAQUE scission
--      (le numero du dossier coupe). Rien d'autre ne change dans la fonction : 5 remplacements, ancres d'une ligne ;
--   3. les 190 lignes deja ecrites (143 scissions, 47 fusions) recoivent leur ancien numero, lu dans leur ligne de
--      naissance -- et le patch S'ARRETE si une seule reste vide ;
--   4. la contrainte des evenements accepte « restauration » : une restauration est aussi un changement de numero,
--      elle doit pouvoir laisser sa ligne (sauvegarde_datee_classeur.py l'ecrit).
-- CE QU'IL NE FAIT PAS : il ne touche a aucune etiquette, a aucun numero, a aucune ligne du registre.
-- ⛔ IL S'ARRETE SEUL, sans rien laisser, si la fonction n'est plus celle lue le 22/11 (empreinte %s),
--   si la colonne existe deja, ou si la contrainte des evenements a change.
-- Ensuite : %s_REPETITION.sql (lecture seule). Retour arriere : %s_INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════
""" % (md5_avant, NOM, NOM)
    patch = entete + """
begin;

do $garde$
begin
  if md5(pg_get_functiondef('%(f)s'::regproc)) <> '%(m)s' then
    raise exception 'la fonction app_poser_etiquettes_dossier a change depuis le 22/11 -- patch ARRETE, rien n''est fait';
  end if;
  if exists (select 1 from information_schema.columns where table_schema = 'public'
               and table_name = 'app_dossier_etiquette_journal' and column_name = 'ancien_numero') then
    raise exception 'la colonne ancien_numero existe deja -- patch ARRETE, rien n''est fait';
  end if;
  if (select pg_get_constraintdef(oid) from pg_constraint
       where conname = 'app_dossier_etiquette_journal_evenement_check')
     is distinct from %(ck_old)s then
    raise exception 'la contrainte des evenements a change depuis le 22/11 -- patch ARRETE, rien n''est fait';
  end if;
end
$garde$;

alter table public.app_dossier_etiquette_journal add column ancien_numero text;
-- UNE RESTAURATION EST AUSSI UN CHANGEMENT DE NUMERO : elle doit pouvoir laisser sa ligne (son mot : « chaque
--   changement doit y laisser sa ligne »). Aujourd'hui la contrainte ne connait que pose, propagation, fusion, scission.
alter table public.app_dossier_etiquette_journal drop constraint app_dossier_etiquette_journal_evenement_check;
alter table public.app_dossier_etiquette_journal add constraint app_dossier_etiquette_journal_evenement_check
  check (evenement in ('pose', 'propagation', 'fusion', 'scission', 'restauration'));
comment on column public.app_dossier_etiquette_journal.ancien_numero is
  'Le numero AVANT le changement (22/11/2026, son mot : « avec l''ancien et le neuf »). FUSION : le numero absorbe '
  '(le neuf est dossier_numero, celui du dossier garde). SCISSION : le numero du dossier coupe (le neuf est '
  'dossier_numero, porte par autre_uuid). RESTAURATION : le numero quitte (le neuf est dossier_numero, celui de la '
  'sauvegarde). Vide pour une pose ou une propagation : rien ne change de numero.';

%(fn)s;

-- les lignes deja ecrites : l'ancien numero, lu dans la ligne de naissance de l'ancien uuid
update public.app_dossier_etiquette_journal j
   set ancien_numero = b.n
  from %(nais)s b
 where j.evenement = 'scission' and j.ancien_numero is null and b.u = j.dossier_uuid;

update public.app_dossier_etiquette_journal j
   set ancien_numero = b.n
  from %(nais)s b
 where j.evenement = 'fusion' and j.ancien_numero is null and b.u = j.autre_uuid;

do $controle$
declare v_vides integer; v_egaux integer; v_mots integer;
begin
  select count(*) into v_vides from public.app_dossier_etiquette_journal
   where evenement in ('fusion', 'scission') and ancien_numero is null;
  if v_vides > 0 then
    raise exception '%% ligne(s) de fusion ou de scission restent sans ancien numero -- patch ARRETE, rien n''est fait', v_vides;
  end if;
  select count(*) into v_egaux from public.app_dossier_etiquette_journal
   where evenement in ('fusion', 'scission') and ancien_numero = dossier_numero;
  if v_egaux > 0 then
    raise exception '%% ligne(s) ou l''ancien numero est egal au neuf -- patch ARRETE, rien n''est fait', v_egaux;
  end if;
  select (length(pg_get_functiondef('%(f)s'::regproc))
          - length(replace(pg_get_functiondef('%(f)s'::regproc), 'ancien_numero', ''))) / length('ancien_numero')
    into v_mots;
  if v_mots <> %(n)d then
    raise exception 'la fonction posee porte %% fois ancien_numero (attendu %(n)d) -- patch ARRETE', v_mots;
  end if;
end
$controle$;

commit;
""" % {"f": FONCTION, "m": md5_avant, "fn": neuf.rstrip("\n"), "nais": NAISSANCES, "n": n_mot,
       "ck_old": "'%s'" % CK_OLD.replace("'", "''")}

    repetition = """-- ═══════════════════════════════════════════════════════════════════════════
-- REPETITION DE %s.sql -- LECTURE SEULE, A COLLER APRES LE PATCH
-- Chaque ligne doit dire OUI. Fabrique par phase2/checks/fabriquer_patch_journal_ancien_numero.py
-- ═══════════════════════════════════════════════════════════════════════════
with naissances as %s,
j as (select * from public.app_dossier_etiquette_journal)
select 'la colonne ancien_numero existe' as controle,
       case when exists (select 1 from information_schema.columns where table_schema = 'public'
         and table_name = 'app_dossier_etiquette_journal' and column_name = 'ancien_numero') then 'OUI' else 'NON' end as verdict,
       '' as detail
union all
select 'la RPC ecrit ancien_numero (%d fois dans son texte)',
       case when (length(pg_get_functiondef('%s'::regproc))
                  - length(replace(pg_get_functiondef('%s'::regproc), 'ancien_numero', ''))) / length('ancien_numero') = %d
            then 'OUI' else 'NON' end, ''
union all
select 'aucune fusion ni scission sans ancien numero',
       case when count(*) = 0 then 'OUI' else 'NON' end, count(*)::text
  from j where evenement in ('fusion', 'scission') and ancien_numero is null
union all
select 'chaque scission : ancien numero = la naissance de l''ancien uuid',
       case when count(*) filter (where b.n is distinct from j.ancien_numero) = 0 then 'OUI' else 'NON' end,
       count(*)::text || ' lignes, ' || count(*) filter (where b.n is distinct from j.ancien_numero)::text || ' ecart(s)'
  from j left join naissances b on b.u = j.dossier_uuid where j.evenement = 'scission'
union all
select 'chaque fusion : ancien numero = la naissance de l''uuid absorbe',
       case when count(*) filter (where b.n is distinct from j.ancien_numero) = 0 then 'OUI' else 'NON' end,
       count(*)::text || ' lignes, ' || count(*) filter (where b.n is distinct from j.ancien_numero)::text || ' ecart(s)'
  from j left join naissances b on b.u = j.autre_uuid where j.evenement = 'fusion'
union all
select 'ancien et neuf toujours differents',
       case when count(*) = 0 then 'OUI' else 'NON' end, count(*)::text
  from j where evenement in ('fusion', 'scission') and ancien_numero = dossier_numero
union all
select 'les poses et propagations n''ont pas d''ancien numero (rien n''y change de numero)',
       case when count(*) = 0 then 'OUI' else 'NON' end, count(*)::text
  from j where evenement in ('pose', 'propagation') and ancien_numero is not null
union all
select 'la contrainte accepte la restauration',
       case when pg_get_constraintdef(oid) like '%%restauration%%' then 'OUI' else 'NON' end, pg_get_constraintdef(oid)
  from pg_constraint where conname = 'app_dossier_etiquette_journal_evenement_check'
union all
select 'le journal n''a perdu aucune ligne (au moins 11 657, le compte du 22/11)',
       case when count(*) >= 11657 then 'OUI' else 'NON' end, count(*)::text
  from j;
""" % (NOM, NAISSANCES, n_mot, FONCTION, FONCTION, n_mot)

    inverse = """-- ═══════════════════════════════════════════════════════════════════════════
-- INVERSE DE %s.sql -- remet la RPC lue le 22/11 (empreinte %s) et retire la colonne
-- ⚠ Il ne juge que SA part (lecon 31) : il s'arrete si la fonction n'est pas celle que le patch a posee.
-- Fabrique par phase2/checks/fabriquer_patch_journal_ancien_numero.py -- NE PAS RETOUCHER A LA MAIN.
-- ═══════════════════════════════════════════════════════════════════════════
begin;

do $garde$
begin
  if pg_get_functiondef('%s'::regproc) not like '%%min(l.app_dossier_numero)%%' then
    raise exception 'la fonction n''est pas celle du patch -- inverse ARRETE, rien n''est fait';
  end if;
end
$garde$;

%s;

do $restaurations$
begin
  if exists (select 1 from public.app_dossier_etiquette_journal where evenement = 'restauration') then
    raise exception 'des restaurations sont au journal : l''inverse les effacerait -- inverse ARRETE, rien n''est fait';
  end if;
end
$restaurations$;

alter table public.app_dossier_etiquette_journal drop constraint app_dossier_etiquette_journal_evenement_check;
alter table public.app_dossier_etiquette_journal add constraint app_dossier_etiquette_journal_evenement_check
  check (evenement in ('pose', 'propagation', 'fusion', 'scission'));
alter table public.app_dossier_etiquette_journal drop column ancien_numero;

do $controle$
begin
  if pg_get_functiondef('%s'::regproc) like '%%ancien_numero%%' then
    raise exception 'la fonction remise porte encore ancien_numero -- inverse ARRETE';
  end if;
  if exists (select 1 from information_schema.columns where table_schema = 'public'
               and table_name = 'app_dossier_etiquette_journal' and column_name = 'ancien_numero') then
    raise exception 'la colonne ancien_numero est encore la -- inverse ARRETE';
  end if;
end
$controle$;

commit;
""" % (NOM, md5_avant, FONCTION, texte.rstrip("\n"), FONCTION)
    for suffixe, contenu in (("", patch), ("_REPETITION", repetition), ("_INVERSE", inverse)):
        f = SUPA / ("%s%s.sql" % (NOM, suffixe))
        f.write_bytes(contenu.encode("utf-8"))           # LF seulement (lecon 30)
        print("-> %s (%d octets)" % (f, len(contenu.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
