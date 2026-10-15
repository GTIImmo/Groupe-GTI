-- ============================================================================
-- REPETITION -- ARCHIVER / DESARCHIVER UN CONTACT (chantier ⑦ point ⑦-1)
-- 15/10/2026
-- ============================================================================
-- ⚠⚠ A COLLER EN UNE SEULE FOIS, EN ENTIER, dans l'editeur SQL. Le `begin;` de la
--    premiere ligne et l'ERREUR VOLONTAIRE de la derniere font que RIEN n'est
--    ecrit : tout est annule. Si tu ne collais qu'un morceau, le patch
--    s'appliquerait pour de vrai.
--
-- CE QU'ELLE JOUE, dans l'ordre reel :
--    1. elle MESURE l'etat d'avant ;
--    2. elle joue LE VRAI PATCH (les 3 verrous + la fonction de saisie) ;
--    3. elle MESURE l'etat d'apres -- y compris un VRAI insert de travail, annule
--       par point de reprise, pour prouver que la contrainte accepte le type ;
--    4. elle joue LE VRAI INVERSE ;
--    5. elle MESURE le retour, et compare aux empreintes d'origine ;
--    6. elle leve une ERREUR VOLONTAIRE qui annule tout et AFFICHE le tableau.
--
-- LE MESSAGE ATTENDU, chiffre, si tout va bien :
--    ESSAI ANNULE -- rien n'a ete ecrit.
--    1-avant | type dans la contrainte       = non
--    1-avant | type dans les droits          = non
--    1-avant | type dans la distribution     = non
--    1-avant | fonction de saisie            = absente
--    1-avant | empreinte contrainte          = 9b5a628a053917c8e4713dfb24aebae6
--    1-avant | empreinte droits              = b581b042e45ec7c93811c410011f1e6a
--    1-avant | empreinte distribution        = 0d3dbd03fb177769c5125860b6881b3b
--    2-apres | type dans la contrainte       = oui
--    2-apres | type dans les droits          = oui
--    2-apres | type dans la branche actions  = oui
--    2-apres | type dans la branche admin    = non
--    2-apres | fonction de saisie            = presente
--    2-apres | droit authenticated           = oui
--    2-apres | droit anon                    = non
--    2-apres | insert d un travail du type   = accepte (annule)
--    2-apres | supprimer un contact reste    = hors de la liste du commercial
--    3-retour| type dans la contrainte       = non
--    3-retour| type dans les droits          = non
--    3-retour| type dans la distribution     = non
--    3-retour| fonction de saisie            = absente
--    3-retour| empreinte contrainte          = IDENTIQUE
--    3-retour| empreinte droits              = IDENTIQUE
--    3-retour| empreinte distribution        = IDENTIQUE
--
-- ⚠ Si une seule ligne « 2-apres » dit « non » la ou on attend « oui », ou si une
--   empreinte de retour n'est pas IDENTIQUE : NE COLLE PAS LE VRAI PATCH, dis-moi.
-- ============================================================================

begin;

create temporary table essai_mesures (
  id     serial,
  etape  text,
  mesure text,
  valeur text
) on commit drop;

-- =============================== 1. AVANT ==================================
insert into essai_mesures (etape, mesure, valeur)
select '1-avant ', 'type dans la contrainte       ',
       case when replace(pg_get_constraintdef(oid), chr(13), '') like '%archive_hektor_contact%' then 'oui' else 'non' end
from pg_constraint where conrelid='public.app_console_job'::regclass and conname='app_console_job_job_type_check';

insert into essai_mesures (etape, mesure, valeur)
select '1-avant ', 'type dans les droits          ',
       case when replace(pg_get_functiondef(p.oid), chr(13), '') like '%archive_hektor_contact%' then 'oui' else 'non' end
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname='public' and p.proname='app_console_can_request_contact_job';

insert into essai_mesures (etape, mesure, valeur)
select '1-avant ', 'type dans la distribution     ',
       case when replace(pg_get_functiondef(p.oid), chr(13), '') like '%archive_hektor_contact%' then 'oui' else 'non' end
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname='public' and p.proname='app_console_claim_next_job';

insert into essai_mesures (etape, mesure, valeur)
values ('1-avant ', 'fonction de saisie            ',
  case when exists (select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
                    where n.nspname='public' and p.proname='app_console_archiver_contact_optimistic')
       then 'presente' else 'absente' end);

insert into essai_mesures (etape, mesure, valeur)
select '1-avant ', 'empreinte contrainte          ', md5(replace(pg_get_constraintdef(oid), chr(13), ''))
from pg_constraint where conrelid='public.app_console_job'::regclass and conname='app_console_job_job_type_check';

insert into essai_mesures (etape, mesure, valeur)
select '1-avant ', 'empreinte droits              ', md5(replace(pg_get_functiondef(p.oid), chr(13), ''))
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname='public' and p.proname='app_console_can_request_contact_job';

insert into essai_mesures (etape, mesure, valeur)
select '1-avant ', 'empreinte distribution        ', md5(replace(pg_get_functiondef(p.oid), chr(13), ''))
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname='public' and p.proname='app_console_claim_next_job';

-- =============================== 2. LE PATCH ===============================

-- VERROU 1 -- LA CONTRAINTE
do $do$
declare
  v_def   text; v_new text;
  v_ancre text := replace('''archive_hektor_annonce''::text', chr(13), '');
  v_ajout text := replace('''archive_hektor_annonce''::text, ''archive_hektor_contact''::text', chr(13), '');
  v_vu    integer;
begin
  select replace(pg_get_constraintdef(oid), chr(13), '') into v_def
  from pg_constraint where conrelid='public.app_console_job'::regclass and conname='app_console_job_job_type_check';
  if v_def is null then raise exception 'STOP : contrainte introuvable'; end if;
  if position('archive_hektor_contact' in v_def) > 0 then
    raise notice 'VERROU 1 : DEJA FAIT'; return;
  end if;
  v_vu := (length(v_def) - length(replace(v_def, v_ancre, ''))) / length(v_ancre);
  if v_vu <> 1 then raise exception 'STOP : ancre contrainte vue % fois', v_vu; end if;
  v_new := replace(v_def, v_ancre, v_ajout);
  execute 'alter table public.app_console_job drop constraint app_console_job_job_type_check';
  execute 'alter table public.app_console_job add constraint app_console_job_job_type_check ' || v_new;
  raise notice 'VERROU 1 : pose';
end
$do$;

-- VERROU 2 -- LES DROITS
do $do$
declare
  v_src   text; v_new text;
  v_ancre text := replace('''delete_hektor_contact_search'')', chr(13), '');
  v_ajout text := replace('''delete_hektor_contact_search'',''archive_hektor_contact'')', chr(13), '');
  v_vu    integer;
begin
  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_src
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  where n.nspname='public' and p.proname='app_console_can_request_contact_job';
  if v_src is null then raise exception 'STOP : droits introuvables'; end if;
  if position('archive_hektor_contact' in v_src) > 0 then
    raise notice 'VERROU 2 : DEJA FAIT'; return;
  end if;
  v_vu := (length(v_src) - length(replace(v_src, v_ancre, ''))) / length(v_ancre);
  if v_vu <> 1 then raise exception 'STOP : ancre droits vue % fois', v_vu; end if;
  v_new := replace(v_src, v_ancre, v_ajout);
  execute v_new;
  raise notice 'VERROU 2 : pose';
end
$do$;

-- VERROU 3 -- LA DISTRIBUTION
do $do$
declare
  v_src   text; v_new text;
  v_ancre text := replace('''unlink_hektor_mandant''))', chr(13), '');
  v_ajout text := replace('''unlink_hektor_mandant'',''archive_hektor_contact''))', chr(13), '');
  v_vu    integer;
begin
  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_src
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  where n.nspname='public' and p.proname='app_console_claim_next_job';
  if v_src is null then raise exception 'STOP : distribution introuvable'; end if;
  if position('archive_hektor_contact' in v_src) > 0 then
    raise notice 'VERROU 3 : DEJA FAIT'; return;
  end if;
  v_vu := (length(v_src) - length(replace(v_src, v_ancre, ''))) / length(v_ancre);
  if v_vu <> 1 then raise exception 'STOP : ancre distribution vue % fois', v_vu; end if;
  v_new := replace(v_src, v_ancre, v_ajout);
  execute v_new;
  raise notice 'VERROU 3 : pose';
end
$do$;

-- LA SAISIE
create or replace function public.app_console_archiver_contact_optimistic(
  p_hektor_contact_id text,
  p_archive boolean
)
returns public.app_console_job
language plpgsql
security definer
set search_path to 'public'
as $fn$
declare
  c           public.app_contact_current%rowtype;
  created_job public.app_console_job;
  clean_id    text;
begin
  clean_id := nullif(trim(coalesce(p_hektor_contact_id, '')), '');
  if clean_id is null or clean_id !~ '^[0-9]+$' then
    raise exception 'invalid_contact_id' using errcode = '22023';
  end if;
  if p_archive is null then
    raise exception 'archive_manquant' using errcode = '22023';
  end if;

  select * into c from public.app_contact_current where hektor_contact_id = clean_id;
  if not found then
    raise exception 'contact_not_found' using errcode = '22023';
  end if;

  if not public.app_console_can_request_contact_job('archive_hektor_contact', clean_id, c.negociateur_email) then
    raise exception 'Ce contact n''est pas dans votre portefeuille : vous ne pouvez pas changer son archivage.'
      using errcode = '42501';
  end if;

  if coalesce(c.archive, false) = p_archive then
    if p_archive then
      raise exception 'Ce contact est deja archive.' using errcode = '22023';
    else
      raise exception 'Ce contact est deja actif.' using errcode = '22023';
    end if;
  end if;

  update public.app_contact_current
     set archive = p_archive
   where hektor_contact_id = clean_id;

  insert into public.app_console_job (
    job_type, app_dossier_id, hektor_annonce_id, payload_json,
    status, priority, requested_by, requested_at
  )
  values (
    'archive_hektor_contact', null, null,
    jsonb_build_object(
      'hektor_contact_id', clean_id,
      'contact_id',        clean_id,
      'archive',           p_archive,
      'base_snapshot',     jsonb_build_object('archive', coalesce(c.archive, false))
    ),
    'pending', 6, auth.uid(), now()
  )
  returning * into created_job;

  return created_job;
end;
$fn$;

revoke all on function public.app_console_archiver_contact_optimistic(text, boolean) from public;
revoke all on function public.app_console_archiver_contact_optimistic(text, boolean) from anon;
grant execute on function public.app_console_archiver_contact_optimistic(text, boolean) to authenticated;
grant execute on function public.app_console_archiver_contact_optimistic(text, boolean) to service_role;

-- =============================== 3. APRES ==================================
insert into essai_mesures (etape, mesure, valeur)
select '2-apres ', 'type dans la contrainte       ',
       case when replace(pg_get_constraintdef(oid), chr(13), '') like '%archive_hektor_contact%' then 'oui' else 'non' end
from pg_constraint where conrelid='public.app_console_job'::regclass and conname='app_console_job_job_type_check';

insert into essai_mesures (etape, mesure, valeur)
select '2-apres ', 'type dans les droits          ',
       case when replace(pg_get_functiondef(p.oid), chr(13), '') like '%archive_hektor_contact%' then 'oui' else 'non' end
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname='public' and p.proname='app_console_can_request_contact_job';

-- ⚠ LE CONTROLE QUI COMPTE VRAIMENT SUR LA DISTRIBUTION : le type doit etre dans
--   la branche « actions » (session negociateur) et PAS dans la branche « admin »
--   (session admin, gestes reserves). Le 12/10, c'est ce genre de controle qui a
--   evite d'ouvrir l'archivage d'une annonce sans que rien ne le signale.
insert into essai_mesures (etape, mesure, valeur)
select '2-apres ', 'type dans la branche actions  ',
       case when split_part(split_part(replace(pg_get_functiondef(p.oid), chr(13), ''), 'worker_kind = ''actions''', 2),
                            'worker_kind = ''documents''', 1) like '%archive_hektor_contact%'
            then 'oui' else 'non' end
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname='public' and p.proname='app_console_claim_next_job';

insert into essai_mesures (etape, mesure, valeur)
select '2-apres ', 'type dans la branche admin    ',
       case when split_part(split_part(replace(pg_get_functiondef(p.oid), chr(13), ''), 'worker_kind = ''admin''', 2),
                            'worker_kind = ''matterport''', 1) like '%archive_hektor_contact%'
            then 'oui' else 'non' end
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname='public' and p.proname='app_console_claim_next_job';

insert into essai_mesures (etape, mesure, valeur)
values ('2-apres ', 'fonction de saisie            ',
  case when exists (select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
                    where n.nspname='public' and p.proname='app_console_archiver_contact_optimistic')
       then 'presente' else 'absente' end);

insert into essai_mesures (etape, mesure, valeur)
values ('2-apres ', 'droit authenticated           ',
  case when has_function_privilege('authenticated',
         'public.app_console_archiver_contact_optimistic(text, boolean)', 'EXECUTE')
       then 'oui' else 'non' end);

insert into essai_mesures (etape, mesure, valeur)
values ('2-apres ', 'droit anon                    ',
  case when has_function_privilege('anon',
         'public.app_console_archiver_contact_optimistic(text, boolean)', 'EXECUTE')
       then 'OUI -- PROBLEME' else 'non' end);

-- ⚠ UNE AVARIE QUI NE CHANGE RIEN NE PROUVE RIEN : on ECRIT vraiment un travail du
--   type neuf, pour prouver que la contrainte l'accepte, et on l'annule par point
--   de reprise. C'est le patron du projet (ecriture interne annulee par savepoint).
-- ⚠⚠ ET LE PIEGE DE LA MESURE, paye le 13/10 : le temoin ne doit PAS dependre de
--    ce que l'epreuve annule. L'annulation efface TOUT ce que le bloc interne a
--    ecrit -- y compris la ligne de mesure. On garde donc le resultat dans une
--    VARIABLE (les variables PL/pgSQL survivent a l'annulation) et on l'ecrit
--    APRES le bloc.
do $do$
declare v_resultat text := 'non teste';
begin
  begin
    insert into public.app_console_job (job_type, payload_json, status, priority, requested_at)
    values ('archive_hektor_contact',
            jsonb_build_object('hektor_contact_id','10000000','contact_id','10000000',
                               'archive', true, 'essai', 'REPETITION du 15/10 -- annulee'),
            'pending', 9, now());
    v_resultat := 'accepte (annule)';
    raise exception 'ANNULATION_INTERNE';
  exception when others then
    if sqlerrm <> 'ANNULATION_INTERNE' then
      v_resultat := 'REFUSE : ' || sqlerrm;
    end if;
  end;
  insert into essai_mesures (etape, mesure, valeur)
  values ('2-apres ', 'insert d un travail du type   ', v_resultat);
end
$do$;

-- ⚠ ET LE CONTROLE JUMEAU, celui qui dort : « supprimer un contact » ne doit PAS
--   avoir rejoint la liste du commercial. On ne regarde que la partie du corps qui
--   SUIT le mot `commercial`.
insert into essai_mesures (etape, mesure, valeur)
select '2-apres ', 'supprimer un contact reste    ',
       case when split_part(replace(pg_get_functiondef(p.oid), chr(13), ''), 'commercial', 2) like '%delete_hektor_contact''%'
            then 'DANS la liste -- PROBLEME' else 'hors de la liste du commercial' end
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname='public' and p.proname='app_console_can_request_contact_job';

-- =============================== 4. L'INVERSE ==============================
drop function if exists public.app_console_archiver_contact_optimistic(text, boolean);

do $do$
declare
  v_src   text; v_new text;
  v_ancre text := replace('''unlink_hektor_mandant'',''archive_hektor_contact''))', chr(13), '');
  v_ajout text := replace('''unlink_hektor_mandant''))', chr(13), '');
  v_vu    integer;
begin
  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_src
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  where n.nspname='public' and p.proname='app_console_claim_next_job';
  if position('archive_hektor_contact' in v_src) = 0 then
    raise notice 'INVERSE distribution : rien a retirer'; return;
  end if;
  v_vu := (length(v_src) - length(replace(v_src, v_ancre, ''))) / length(v_ancre);
  if v_vu <> 1 then raise exception 'STOP : ancre inverse distribution vue % fois', v_vu; end if;
  v_new := replace(v_src, v_ancre, v_ajout);
  execute v_new;
end
$do$;

do $do$
declare
  v_src   text; v_new text;
  v_ancre text := replace('''delete_hektor_contact_search'',''archive_hektor_contact'')', chr(13), '');
  v_ajout text := replace('''delete_hektor_contact_search'')', chr(13), '');
  v_vu    integer;
begin
  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_src
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  where n.nspname='public' and p.proname='app_console_can_request_contact_job';
  if position('archive_hektor_contact' in v_src) = 0 then
    raise notice 'INVERSE droits : rien a retirer'; return;
  end if;
  v_vu := (length(v_src) - length(replace(v_src, v_ancre, ''))) / length(v_ancre);
  if v_vu <> 1 then raise exception 'STOP : ancre inverse droits vue % fois', v_vu; end if;
  v_new := replace(v_src, v_ancre, v_ajout);
  execute v_new;
end
$do$;

do $do$
declare
  v_def   text; v_new text;
  v_ancre text := replace('''archive_hektor_annonce''::text, ''archive_hektor_contact''::text', chr(13), '');
  v_ajout text := replace('''archive_hektor_annonce''::text', chr(13), '');
  v_vu    integer;
begin
  select replace(pg_get_constraintdef(oid), chr(13), '') into v_def
  from pg_constraint where conrelid='public.app_console_job'::regclass and conname='app_console_job_job_type_check';
  if position('archive_hektor_contact' in v_def) = 0 then
    raise notice 'INVERSE contrainte : rien a retirer'; return;
  end if;
  v_vu := (length(v_def) - length(replace(v_def, v_ancre, ''))) / length(v_ancre);
  if v_vu <> 1 then raise exception 'STOP : ancre inverse contrainte vue % fois', v_vu; end if;
  v_new := replace(v_def, v_ancre, v_ajout);
  execute 'alter table public.app_console_job drop constraint app_console_job_job_type_check';
  execute 'alter table public.app_console_job add constraint app_console_job_job_type_check ' || v_new;
end
$do$;

-- =============================== 5. LE RETOUR ==============================
insert into essai_mesures (etape, mesure, valeur)
select '3-retour', 'type dans la contrainte       ',
       case when replace(pg_get_constraintdef(oid), chr(13), '') like '%archive_hektor_contact%' then 'OUI -- PROBLEME' else 'non' end
from pg_constraint where conrelid='public.app_console_job'::regclass and conname='app_console_job_job_type_check';

insert into essai_mesures (etape, mesure, valeur)
select '3-retour', 'type dans les droits          ',
       case when replace(pg_get_functiondef(p.oid), chr(13), '') like '%archive_hektor_contact%' then 'OUI -- PROBLEME' else 'non' end
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname='public' and p.proname='app_console_can_request_contact_job';

insert into essai_mesures (etape, mesure, valeur)
select '3-retour', 'type dans la distribution     ',
       case when replace(pg_get_functiondef(p.oid), chr(13), '') like '%archive_hektor_contact%' then 'OUI -- PROBLEME' else 'non' end
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname='public' and p.proname='app_console_claim_next_job';

insert into essai_mesures (etape, mesure, valeur)
values ('3-retour', 'fonction de saisie            ',
  case when exists (select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
                    where n.nspname='public' and p.proname='app_console_archiver_contact_optimistic')
       then 'PRESENTE -- PROBLEME' else 'absente' end);

insert into essai_mesures (etape, mesure, valeur)
select '3-retour', 'empreinte contrainte          ',
       case when md5(replace(pg_get_constraintdef(oid), chr(13), '')) = '9b5a628a053917c8e4713dfb24aebae6'
            then 'IDENTIQUE' else 'DIFFERENTE : ' || md5(replace(pg_get_constraintdef(oid), chr(13), '')) end
from pg_constraint where conrelid='public.app_console_job'::regclass and conname='app_console_job_job_type_check';

insert into essai_mesures (etape, mesure, valeur)
select '3-retour', 'empreinte droits              ',
       case when md5(replace(pg_get_functiondef(p.oid), chr(13), '')) = 'b581b042e45ec7c93811c410011f1e6a'
            then 'IDENTIQUE' else 'DIFFERENTE : ' || md5(replace(pg_get_functiondef(p.oid), chr(13), '')) end
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname='public' and p.proname='app_console_can_request_contact_job';

insert into essai_mesures (etape, mesure, valeur)
select '3-retour', 'empreinte distribution        ',
       case when md5(replace(pg_get_functiondef(p.oid), chr(13), '')) = '0d3dbd03fb177769c5125860b6881b3b'
            then 'IDENTIQUE' else 'DIFFERENTE : ' || md5(replace(pg_get_functiondef(p.oid), chr(13), '')) end
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname='public' and p.proname='app_console_claim_next_job';

-- ========================= 6. L'ERREUR VOLONTAIRE ==========================
do $do$
declare v_txt text;
begin
  select string_agg(etape || ' | ' || mesure || ' = ' || valeur, chr(10) order by id)
    into v_txt
  from essai_mesures;
  raise exception 'ESSAI ANNULE -- rien n''a ete ecrit. %', chr(10) || v_txt;
end
$do$;

rollback;
