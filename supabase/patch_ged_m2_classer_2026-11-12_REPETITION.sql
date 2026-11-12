-- RÉPÉTITION — patch_ged_m2_classer_2026-11-12.sql (fabriquée à partir du patch : ne pas éditer à la main).
-- Pose la colonne et la fonction DANS une transaction, essaie la fonction en se mettant à la place d'un admin
-- (deux faux travaux sur le bien d'essai 62774), relit les contrôles, puis lève une erreur VOLONTAIRE qui porte
-- les verdicts : RIEN n'est gardé. Attendu : « 12 OK, 0 KO ».

begin;
set local lock_timeout = '3s';

do $garde$
begin
  if to_regclass('public.app_ged_classement') is null then
    raise exception 'ARRET : app_ged_classement absente -- poser d''abord le morceau 1.';
  end if;
  if exists (select 1 from information_schema.columns where table_schema = 'public'
              and table_name = 'app_ged_classement' and column_name = 'app_console_job_id') then
    raise exception 'ARRET : la colonne app_console_job_id existe deja -- patch deja applique ?';
  end if;
  if to_regprocedure('public.app_ged_classer(uuid,text,text,text,text,text)') is not null then
    raise exception 'ARRET : app_ged_classer existe deja -- patch deja applique ?';
  end if;
end
$garde$;

-- ─────────────────────────────────────────────────────── ① LA COLONNE
alter table public.app_ged_classement add column app_console_job_id uuid;
create unique index app_ged_classement_un_par_travail_uidx
  on public.app_ged_classement (app_console_job_id)
  where app_console_job_id is not null;
comment on column public.app_ged_classement.app_console_job_id is
  'GED morceau 2 : le travail upload_document_to_hektor qui porte le fichier. Clé d''accroche quand la ligne du '
  'document n''a pas pu être créée chez nous.';

-- ─────────────────────────────────────────────────────── ② LA FONCTION
create function public.app_ged_classer(
  p_job_id           uuid,
  p_type_code        text,
  p_origine          text,
  p_type_propose     text,
  p_type_propose_par text,
  p_sha256           text
) returns jsonb
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  v_job      record;
  v_doc_id   uuid;
  v_nom      text;
  v_existant uuid;
  v_id       uuid;
begin
  -- GED morceau 2 (12/11/2026) : enregistrer le type d'un document déposé avec la nouvelle fenêtre.
  -- Écrit CHEZ NOUS seulement (app_ged_*). Jamais app_console_document, jamais Hektor.
  if not public.is_app_user_active() then
    raise exception '%', 'Compte inactif : le classement ne peut pas être écrit.' using errcode = '42501';
  end if;
  if p_job_id is null then
    raise exception '%', 'Le travail d''envoi est obligatoire.';
  end if;
  if coalesce(p_origine, '') not in ('humain', 'ia', 'nom') then
    raise exception '%', 'Origine inconnue (humain, ia ou nom).';
  end if;
  if p_type_propose_par is not null and p_type_propose_par not in ('ia', 'nom') then
    raise exception '%', 'Proposition inconnue (ia ou nom).';
  end if;
  if not exists (select 1 from public.app_ged_type where code = p_type_code and actif) then
    raise exception '%', 'Type de document inconnu ou désactivé : ' || coalesce(p_type_code, '(vide)');
  end if;

  select j.id, j.job_type, j.requested_by, j.hektor_annonce_id, j.payload_json
    into v_job
    from public.app_console_job j
   where j.id = p_job_id;
  if v_job.id is null or v_job.job_type <> 'upload_document_to_hektor' then
    raise exception '%', 'Travail d''envoi introuvable.';
  end if;
  if v_job.requested_by is distinct from auth.uid() then
    raise exception '%', 'On ne classe que ses propres dépôts.' using errcode = '42501';
  end if;

  -- déjà classé (rappel de l'écran) : on rend la fiche, on n'écrit rien
  select id into v_existant from public.app_ged_classement where app_console_job_id = p_job_id;
  if v_existant is not null then
    return jsonb_build_object('ok', true, 'classement_id', v_existant, 'deja', true);
  end if;

  v_doc_id := nullif(v_job.payload_json ->> 'app_document_id', '')::uuid;
  v_nom := coalesce(nullif(v_job.payload_json ->> 'original_filename', ''), nullif(v_job.payload_json ->> 'document_label', ''), 'document');

  insert into public.app_ged_classement
    (app_console_job_id, app_console_document_id, hektor_annonce_id, sha256, document_name,
     type_code, origine, type_propose, type_propose_par, decide_par, decide_le)
  values
    (p_job_id, v_doc_id, v_job.hektor_annonce_id::text, nullif(btrim(coalesce(p_sha256, '')), ''), v_nom,
     p_type_code, p_origine, nullif(p_type_propose, ''), p_type_propose_par, auth.uid(), now())
  returning id into v_id;

  insert into public.app_ged_rattachement (classement_id, objet, objet_id, origine, cree_par)
  values (v_id, 'bien', v_job.hektor_annonce_id::text, 'humain', auth.uid());

  insert into public.app_ged_journal (objet, objet_id, geste, avant, apres, par)
  values ('classement', v_id, 'classer', null,
          jsonb_build_object('type_code', p_type_code, 'origine', p_origine, 'type_propose', p_type_propose,
                             'type_propose_par', p_type_propose_par, 'app_console_job_id', p_job_id,
                             'app_console_document_id', v_doc_id),
          auth.uid());

  return jsonb_build_object('ok', true, 'classement_id', v_id, 'app_console_document_id', v_doc_id, 'deja', false);
end
$function$;

comment on function public.app_ged_classer(uuid, text, text, text, text, text) is
  'GED morceau 2 (12/11/2026) : enregistre le type d''un document déposé par la nouvelle fenêtre (le sien seulement). '
  'Annonce et document lus dans le travail d''envoi. Idempotente. N''écrit que dans app_ged_*.';

-- ⛔ chaque rôle nommé : la fonction n'est ouverte qu'aux utilisateurs connectés
revoke all on function public.app_ged_classer(uuid, text, text, text, text, text) from public, anon, authenticated;
grant execute on function public.app_ged_classer(uuid, text, text, text, text, text) to authenticated;


-- ─────────────────────────────────────────────────────── LES ESSAIS (dans la transaction, puis tout est annulé)
do $essai$
declare
  v_admin uuid; v_autre uuid; v_dossier bigint; v_job uuid := gen_random_uuid(); v_job_autre uuid := gen_random_uuid();
  v_doc uuid := gen_random_uuid(); r jsonb; r2 jsonb; n int; ok int := 0; ko int := 0; journal text := ''; v_refus text;
  c record;
begin
  select id into v_admin from public.app_user_profile where is_active and role = 'admin' order by id limit 1;
  select id into v_autre from public.app_user_profile where is_active and id <> v_admin order by id limit 1;
  select app_dossier_id into v_dossier from public.app_dossier_current where hektor_annonce_id::text = '62774' limit 1;

  -- deux faux travaux d'envoi (jamais vus par le worker : la transaction est annulée)
  insert into public.app_console_job (id, job_type, app_dossier_id, hektor_annonce_id, payload_json, priority, requested_by, status)
  values (v_job, 'upload_document_to_hektor', v_dossier, '62774',
          jsonb_build_object('app_document_id', v_doc, 'original_filename', 'ESSAI GED DPE.pdf'), 99, v_admin, 'done'),
         (v_job_autre, 'upload_document_to_hektor', v_dossier, '62774',
          jsonb_build_object('original_filename', 'ESSAI GED autre.pdf'), 99, v_autre, 'done');

  perform set_config('request.jwt.claims', json_build_object('sub', v_admin, 'role', 'authenticated')::text, true);
  set local role authenticated;

  -- ① classer son propre dépôt
  r := public.app_ged_classer(v_job, 'diag.dpe', 'humain', 'diag.dpe', 'nom', 'abc123');
  if (r->>'ok')::boolean and (r->>'deja')::boolean = false and (r->>'app_console_document_id')::uuid = v_doc
  then ok := ok + 1; journal := journal || E'\nOK  ① classer son dépôt'; else ko := ko + 1; journal := journal || E'\nKO  ① ' || r::text; end if;

  -- ② rappel : idempotent
  r2 := public.app_ged_classer(v_job, 'diag.erp', 'humain', null, null, null);
  if (r2->>'deja')::boolean and r2->>'classement_id' = r->>'classement_id'
  then ok := ok + 1; journal := journal || E'\nOK  ② rappel sans rien écrire'; else ko := ko + 1; journal := journal || E'\nKO  ② ' || r2::text; end if;

  -- ③ le dépôt d'un autre : refusé
  v_refus := 'non refusé';
  begin perform public.app_ged_classer(v_job_autre, 'diag.dpe', 'humain', null, null, null);
  exception when others then v_refus := 'refusé'; end;
  if v_refus = 'refusé' then ok := ok + 1; journal := journal || E'\nOK  ③ le dépôt d''un autre est refusé'; else ko := ko + 1; journal := journal || E'\nKO  ③ dépôt d''un autre accepté'; end if;

  -- ④ un type inconnu : refusé
  v_refus := 'non refusé';
  begin perform public.app_ged_classer(gen_random_uuid(), 'pas.un.type', 'humain', null, null, null);
  exception when others then v_refus := 'refusé'; end;
  if v_refus = 'refusé' then ok := ok + 1; journal := journal || E'\nOK  ④ type inconnu refusé'; else ko := ko + 1; journal := journal || E'\nKO  ④ type inconnu accepté'; end if;

  -- ⑤ ce qui a été écrit : 1 fiche, 1 rattachement au bien, 1 ligne de journal
  reset role;
  select count(*) into n from public.app_ged_classement where app_console_job_id = v_job and type_code = 'diag.dpe'
     and app_console_document_id = v_doc and hektor_annonce_id = '62774' and decide_par = v_admin and sha256 = 'abc123';
  if n = 1 and (select count(*) from public.app_ged_rattachement where objet = 'bien' and objet_id = '62774') = 1
     and (select count(*) from public.app_ged_journal where geste = 'classer') = 1
  then ok := ok + 1; journal := journal || E'\nOK  ⑤ une fiche, un rattachement, une ligne de journal';
  else ko := ko + 1; journal := journal || E'\nKO  ⑤ écritures inattendues'; end if;

  -- ⑥ TÉMOIN : rien n'a touché app_console_document
  if not exists (select 1 from public.app_console_document where id = v_doc)
  then ok := ok + 1; journal := journal || E'\nOK  ⑥ app_console_document intacte';
  else ko := ko + 1; journal := journal || E'\nKO  ⑥ une ligne de document est apparue'; end if;

  -- les contrôles du patch
  for c in select '⑦ la colonne app_console_job_id existe' as controle, count(*) as trouve,
       case when count(*) = 1 then 'VERT' else 'ROUGE' end as verdict
  from information_schema.columns
 where table_schema = 'public' and table_name = 'app_ged_classement' and column_name = 'app_console_job_id'
union all
select '⑧ la fonction existe, SECURITY DEFINER', count(*),
       case when count(*) = 1 then 'VERT' else 'ROUGE' end
  from pg_proc where proname = 'app_ged_classer' and prosecdef
union all
select '⑨ anon ne peut PAS l''appeler', count(*),
       case when count(*) = 0 then 'VERT' else 'ROUGE' end
  from pg_proc p where p.proname = 'app_ged_classer' and has_function_privilege('anon', p.oid, 'execute')
union all
select '⑩ authenticated peut l''appeler', count(*),
       case when count(*) = 1 then 'VERT' else 'ROUGE' end
  from pg_proc p where p.proname = 'app_ged_classer' and has_function_privilege('authenticated', p.oid, 'execute')
union all
select '⑫ le classement ne porte que la fiche de l''essai ①', count(*),
       case when count(*) = 1 then 'VERT' else 'ROUGE' end
  from public.app_ged_classement
union all
select '⑪ TÉMOIN : app_console_document garde sa seule clé étrangère (signature)', count(*),
       case when count(*) = 1 then 'VERT' else 'ROUGE' end
  from pg_constraint where confrelid = 'public.app_console_document'::regclass
  loop
    if c.verdict = 'VERT' then ok := ok + 1; else ko := ko + 1; end if;
    journal := journal || E'\n' || c.verdict || '  ' || c.controle || ' : ' || c.trouve;
  end loop;

  raise exception 'RÉPÉTITION GED morceau 2 (rien n''est gardé) : % OK, % KO%', ok, ko, journal;
end
$essai$;

rollback;
