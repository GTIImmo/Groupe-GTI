-- ═══════════════════════════════════════════════════════════════════════════════
-- CHANTIER GED — MORCEAU 2 : ENREGISTRER LE CLASSEMENT D'UN DOCUMENT DÉPOSÉ       12/11/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- Note du chantier : notice/CHANTIER_GED_DOCUMENTS_2026-11-06.md, §12.7.
--
-- ─── CE QUE CE PATCH POSE ───
--   ① une colonne app_ged_classement.app_console_job_id : le travail d'envoi qui porte le fichier. C'est la clé
--     d'accroche : la ligne du document chez nous peut manquer (si sa création échoue, l'envoi part quand même par
--     l'ancien chemin) ; le travail, lui, existe toujours.
--   ② la fonction app_ged_classer(...) que la nouvelle fenêtre de dépôt appelle APRÈS chaque envoi :
--     · gardes : utilisateur actif ; le travail existe, c'est un upload_document_to_hektor, il a été demandé PAR
--       L'APPELANT (on ne classe que ses propres dépôts) ; le type existe et est actif ;
--     · l'annonce et l'identifiant du document sont lus DANS LE TRAVAIL (jamais fournis par l'écran) ;
--     · écrit la fiche de classement, le rattachement au bien, et la ligne de journal ;
--     · idempotente : rappelée pour le même travail, elle rend la fiche existante sans rien écrire.
--
-- ─── CE QUE CE PATCH NE FAIT PAS ───
-- ⛔ rien dans app_console_document (ni document_type, ni metadata_json : la signature), rien chez Hektor,
--   rien dans le worker. Un échec de cette fonction n'empêche JAMAIS un dépôt : l'écran le dit et propose de
--   reclasser.
-- ⛔ aucune lecture des tables de classement par l'écran : elle viendra au morceau 3 (« Reçu / Manque »).
--
-- ─── RETOUR ARRIÈRE ───  supabase/patch_ged_m2_classer_2026-11-12_INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════════

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

commit;

-- ═══════════════════════════════════════════════════════════════════════════════
-- LES CONTRÔLES — à lire après le COMMIT. Tout doit être VERT.
-- ═══════════════════════════════════════════════════════════════════════════════
select '① la colonne app_console_job_id existe' as controle, count(*) as trouve,
       case when count(*) = 1 then 'VERT' else 'ROUGE' end as verdict
  from information_schema.columns
 where table_schema = 'public' and table_name = 'app_ged_classement' and column_name = 'app_console_job_id'
union all
select '② la fonction existe, SECURITY DEFINER', count(*),
       case when count(*) = 1 then 'VERT' else 'ROUGE' end
  from pg_proc where proname = 'app_ged_classer' and prosecdef
union all
select '③ anon ne peut PAS l''appeler', count(*),
       case when count(*) = 0 then 'VERT' else 'ROUGE' end
  from pg_proc p where p.proname = 'app_ged_classer' and has_function_privilege('anon', p.oid, 'execute')
union all
select '④ authenticated peut l''appeler', count(*),
       case when count(*) = 1 then 'VERT' else 'ROUGE' end
  from pg_proc p where p.proname = 'app_ged_classer' and has_function_privilege('authenticated', p.oid, 'execute')
union all
select '⑤ le classement est toujours VIDE (ce patch n''écrit aucune donnée)', count(*),
       case when count(*) = 0 then 'VERT' else 'ROUGE' end
  from public.app_ged_classement
union all
select '⑥ TÉMOIN : app_console_document garde sa seule clé étrangère (signature)', count(*),
       case when count(*) = 1 then 'VERT' else 'ROUGE' end
  from pg_constraint where confrelid = 'public.app_console_document'::regclass;
