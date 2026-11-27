-- ═══════════════════════════════════════════════════════════════════════════
-- REPETITION DE patch_journal_ancien_numero_2026-11-22.sql -- LECTURE SEULE, A COLLER APRES LE PATCH
-- Chaque ligne doit dire OUI. Fabrique par phase2/checks/fabriquer_patch_journal_ancien_numero.py
-- ═══════════════════════════════════════════════════════════════════════════
with naissances as (select dossier_uuid as u, dossier_numero as n from public.app_dossier_etiquette_journal where evenement = 'pose'
     union all
     select autre_uuid, dossier_numero from public.app_dossier_etiquette_journal where evenement = 'scission'),
j as (select * from public.app_dossier_etiquette_journal)
select 'la colonne ancien_numero existe' as controle,
       case when exists (select 1 from information_schema.columns where table_schema = 'public'
         and table_name = 'app_dossier_etiquette_journal' and column_name = 'ancien_numero') then 'OUI' else 'NON' end as verdict,
       '' as detail
union all
select 'la RPC ecrit ancien_numero (2 fois dans son texte)',
       case when (length(pg_get_functiondef('public.app_poser_etiquettes_dossier'::regproc))
                  - length(replace(pg_get_functiondef('public.app_poser_etiquettes_dossier'::regproc), 'ancien_numero', ''))) / length('ancien_numero') = 2
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
       case when pg_get_constraintdef(oid) like '%restauration%' then 'OUI' else 'NON' end, pg_get_constraintdef(oid)
  from pg_constraint where conname = 'app_dossier_etiquette_journal_evenement_check'
union all
select 'le journal n''a perdu aucune ligne (au moins 11 657, le compte du 22/11)',
       case when count(*) >= 11657 then 'OUI' else 'NON' end, count(*)::text
  from j;
