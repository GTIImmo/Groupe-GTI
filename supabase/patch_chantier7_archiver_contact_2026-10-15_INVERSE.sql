-- ============================================================================
-- INVERSE de patch_chantier7_archiver_contact_2026-10-15.sql
-- 15/10/2026 -- ARCHIVER / DESARCHIVER UN CONTACT : on retire tout
-- ============================================================================
-- Il retire le type `archive_hektor_contact` des TROIS verrous et supprime la
-- fonction de saisie. Il ne touche a RIEN d'autre.
--
-- ⚠ IL REFUSE DE TRAVAILLER S'IL RESTE DES TRAVAUX DE CE TYPE. Retirer le type
--   de la contrainte avec des lignes qui le portent est impossible (la contrainte
--   ne se revaliderait pas), et le retirer de la distribution laisserait des
--   travaux « pending » que personne ne reclamerait plus jamais.
--
-- ⚠ IL VERIFIE D'ABORD QU'IL NE RESTE AUCUNE TRACE de ce qu'il devait retirer
--   (lecon du 15/10 : un retour arriere ne juge que SA part). L'empreinte globale
--   n'est qu'un CONTROLE AFFICHE, pas un veto : si un autre patch est passe sur
--   les memes fonctions depuis, il le DIT au lieu de bloquer.
--
-- Empreintes d'origine mesurees le 15/10 a 20:5x, sans les retours chariot :
--     contrainte    9b5a628a053917c8e4713dfb24aebae6
--     droits        b581b042e45ec7c93811c410011f1e6a
--     distribution  0d3dbd03fb177769c5125860b6881b3b
-- ============================================================================

begin;

-- ---------------------------------------------------------------------------
-- GARDE : aucun travail de ce type ne doit exister
-- ---------------------------------------------------------------------------
do $do$
declare v_n integer;
begin
  select count(*) into v_n from public.app_console_job where job_type = 'archive_hektor_contact';
  if v_n > 0 then
    raise exception 'STOP : % travaux archive_hektor_contact existent encore. Laisse-les finir (ou supprime-les sciemment) avant de jouer cet inverse.', v_n;
  end if;
  raise notice 'GARDE : 0 travail de ce type, on peut retirer';
end
$do$;

-- ---------------------------------------------------------------------------
-- 1/4 -- LA SAISIE : on supprime la fonction neuve
-- ---------------------------------------------------------------------------
drop function if exists public.app_console_archiver_contact_optimistic(text, boolean);

-- ---------------------------------------------------------------------------
-- 2/4 -- LA DISTRIBUTION
-- ---------------------------------------------------------------------------
do $do$
declare
  v_src   text;
  v_new   text;
  v_ancre text := replace('''unlink_hektor_mandant'',''archive_hektor_contact''))', chr(13), '');
  v_ajout text := replace('''unlink_hektor_mandant''))', chr(13), '');
  v_vu    integer;
  v_apres text;
begin
  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_src
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public' and p.proname = 'app_console_claim_next_job';

  if v_src is null then raise exception 'STOP : app_console_claim_next_job introuvable'; end if;

  if position('archive_hektor_contact' in v_src) = 0 then
    raise notice 'DISTRIBUTION : rien a retirer (deja propre)';
  else
    v_vu := (length(v_src) - length(replace(v_src, v_ancre, ''))) / length(v_ancre);
    if v_vu <> 1 then
      raise exception 'STOP : l''ancre inverse de la distribution apparait % fois (attendu 1)', v_vu;
    end if;
    v_new := replace(v_src, v_ancre, v_ajout);
    execute v_new;
  end if;

  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_apres
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public' and p.proname = 'app_console_claim_next_job';

  if position('archive_hektor_contact' in v_apres) > 0 then
    raise exception 'STOP : il reste une trace du type dans la distribution';
  end if;
  if md5(v_apres) = '0d3dbd03fb177769c5125860b6881b3b' then
    raise notice 'DISTRIBUTION : retiree, empreinte d''origine retrouvee';
  else
    raise notice 'DISTRIBUTION : retiree (0 trace), mais l''empreinte est % et non 0d3dbd03... -- un AUTRE patch est passe sur cette fonction depuis le 15/10. Ce n''est pas une erreur de cet inverse.', md5(v_apres);
  end if;
end
$do$;

-- ---------------------------------------------------------------------------
-- 3/4 -- LES DROITS
-- ---------------------------------------------------------------------------
do $do$
declare
  v_src   text;
  v_new   text;
  v_ancre text := replace('''delete_hektor_contact_search'',''archive_hektor_contact'')', chr(13), '');
  v_ajout text := replace('''delete_hektor_contact_search'')', chr(13), '');
  v_vu    integer;
  v_apres text;
begin
  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_src
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public' and p.proname = 'app_console_can_request_contact_job';

  if v_src is null then raise exception 'STOP : app_console_can_request_contact_job introuvable'; end if;

  if position('archive_hektor_contact' in v_src) = 0 then
    raise notice 'DROITS : rien a retirer (deja propre)';
  else
    v_vu := (length(v_src) - length(replace(v_src, v_ancre, ''))) / length(v_ancre);
    if v_vu <> 1 then
      raise exception 'STOP : l''ancre inverse des droits apparait % fois (attendu 1)', v_vu;
    end if;
    v_new := replace(v_src, v_ancre, v_ajout);
    execute v_new;
  end if;

  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_apres
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public' and p.proname = 'app_console_can_request_contact_job';

  if position('archive_hektor_contact' in v_apres) > 0 then
    raise exception 'STOP : il reste une trace du type dans les droits';
  end if;
  if md5(v_apres) = 'b581b042e45ec7c93811c410011f1e6a' then
    raise notice 'DROITS : retires, empreinte d''origine retrouvee';
  else
    raise notice 'DROITS : retires (0 trace), mais l''empreinte est % et non b581b042... -- un AUTRE patch est passe sur cette fonction depuis le 15/10.', md5(v_apres);
  end if;
end
$do$;

-- ---------------------------------------------------------------------------
-- 4/4 -- LA CONTRAINTE
-- ---------------------------------------------------------------------------
do $do$
declare
  v_def   text;
  v_new   text;
  v_ancre text := replace('''archive_hektor_annonce''::text, ''archive_hektor_contact''::text', chr(13), '');
  v_ajout text := replace('''archive_hektor_annonce''::text', chr(13), '');
  v_vu    integer;
  v_apres text;
begin
  select replace(pg_get_constraintdef(oid), chr(13), '') into v_def
  from pg_constraint
  where conrelid = 'public.app_console_job'::regclass and conname = 'app_console_job_job_type_check';

  if v_def is null then raise exception 'STOP : contrainte introuvable'; end if;

  if position('archive_hektor_contact' in v_def) = 0 then
    raise notice 'CONTRAINTE : rien a retirer (deja propre)';
  else
    v_vu := (length(v_def) - length(replace(v_def, v_ancre, ''))) / length(v_ancre);
    if v_vu <> 1 then
      raise exception 'STOP : l''ancre inverse de la contrainte apparait % fois (attendu 1)', v_vu;
    end if;
    v_new := replace(v_def, v_ancre, v_ajout);
    execute 'alter table public.app_console_job drop constraint app_console_job_job_type_check';
    execute 'alter table public.app_console_job add constraint app_console_job_job_type_check ' || v_new;
  end if;

  select replace(pg_get_constraintdef(oid), chr(13), '') into v_apres
  from pg_constraint
  where conrelid = 'public.app_console_job'::regclass and conname = 'app_console_job_job_type_check';

  if position('archive_hektor_contact' in v_apres) > 0 then
    raise exception 'STOP : il reste une trace du type dans la contrainte';
  end if;
  if md5(v_apres) = '9b5a628a053917c8e4713dfb24aebae6' then
    raise notice 'CONTRAINTE : retiree, empreinte d''origine retrouvee';
  else
    raise notice 'CONTRAINTE : retiree (0 trace), mais l''empreinte est % et non 9b5a628a... -- un AUTRE type a ete ajoute depuis le 15/10.', md5(v_apres);
  end if;
end
$do$;

commit;
