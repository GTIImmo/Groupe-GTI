-- RETOUR ARRIÈRE de supabase/patch_ged_masquer_2026-11-20.sql (visuel V3, morceau 1 : « Masquer »).
-- Il remet le CHECK du verdict et la garde de app_ged_juger EXACTEMENT comme le 16/11 (vrai / faux / deja_su).
-- ⛔ Il REFUSE s'il existe déjà des « masque » / « reaffiche » dans le journal : un journal ne s'efface pas. Dans ce cas,
--   retirer d'abord l'écran du morceau 4, puis décider à la main de ces lignes (aucune suppression automatique ici).
-- Un retour arrière ne juge que SA part (leçon 31) : il vérifie que la fonction en place est bien celle du patch.
begin;
set local lock_timeout = '3s';

do $garde$
begin
  if not exists (select 1 from pg_proc where oid = 'public.app_ged_juger(text, text, text, text, text, text, text)'::regprocedure
                   and prosrc like '%''masque'', ''reaffiche''%') then
    raise exception 'ARRET : app_ged_juger n''est pas celle du patch du 20/11 -- rien a defaire, ou quelqu''un est passe apres';
  end if;
  if exists (select 1 from public.app_ged_jugement where verdict in ('masque', 'reaffiche')) then
    raise exception 'ARRET : % ligne(s) masque / reaffiche dans le journal -- on ne les efface pas ici',
      (select count(*) from public.app_ged_jugement where verdict in ('masque', 'reaffiche'));
  end if;
end
$garde$;

alter table public.app_ged_jugement drop constraint app_ged_jugement_verdict;
alter table public.app_ged_jugement add constraint app_ged_jugement_verdict check (verdict in ('vrai', 'faux', 'deja_su'));

comment on table public.app_ged_jugement is
  'GED morceau 10 (16/11/2026) : le jugement humain (vrai / faux / deja_su) d''une ligne « À regarder », qui et quand. '
  'Journal : jamais modifié ni effacé ; le plus récent d''une ligne fait foi. Écrit par app_ged_juger seule.';

create or replace function public.app_ged_juger(
  p_hektor_annonce_id text,
  p_regle             text,
  p_cle               text,
  p_texte             text,
  p_niveau            text,
  p_verdict           text,
  p_commentaire       text
) returns jsonb
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  v_cran text;
  v_id   uuid;
begin
  -- GED morceau 10 (16/11/2026) : GARDER le jugement d'une ligne. N'écrit QUE dans app_ged_jugement.
  if not public.is_app_user_active() then
    raise exception '%', 'Compte inactif : le jugement ne peut pas être écrit.' using errcode = '42501';
  end if;
  select lower(btrim(value)) into v_cran from public.app_setting where key = 'ged_propositions';
  if not (coalesce(v_cran, 'off') in ('on', 'true', '1', 'yes') or (v_cran = 'admin' and public.is_app_admin())) then
    raise exception '%', 'Les lignes « À regarder » ne sont pas ouvertes pour toi.' using errcode = '42501';
  end if;
  if coalesce(btrim(p_hektor_annonce_id), '') = '' or coalesce(btrim(p_regle), '') = '' or coalesce(btrim(p_cle), '') = ''
     or coalesce(btrim(p_texte), '') = '' then
    raise exception '%', 'Ligne incomplète.';
  end if;
  if coalesce(p_verdict, '') not in ('vrai', 'faux', 'deja_su') then
    raise exception '%', 'Verdict inconnu (vrai, faux ou deja_su).';
  end if;
  if coalesce(p_niveau, '') not in ('alerte', 'piece', 'info') then
    raise exception '%', 'Niveau inconnu (alerte, piece ou info).';
  end if;
  if not ((select public.is_app_global_reader())
          or p_hektor_annonce_id in (select m.hid from public.app_mes_biens_portefeuille() m(id, hid))) then
    raise exception '%', 'Ce bien n''est pas dans ton périmètre.' using errcode = '42501';
  end if;

  insert into public.app_ged_jugement (hektor_annonce_id, regle, cle, texte, niveau, verdict, commentaire, juge_par)
  values (btrim(p_hektor_annonce_id), btrim(p_regle), btrim(p_cle), left(p_texte, 1000), p_niveau, p_verdict,
          nullif(left(btrim(coalesce(p_commentaire, '')), 500), ''), auth.uid())
  returning id into v_id;
  return jsonb_build_object('ok', true, 'id', v_id);
end
$function$;

comment on function public.app_ged_juger(text, text, text, text, text, text, text) is
  'GED morceau 10 (16/11/2026) : garde le jugement (vrai / faux / deja_su) d''une ligne « À regarder » (auteur = '
  'auth.uid()). Interrupteur ged_propositions, périmètre du bien. N''écrit que dans app_ged_jugement.';

revoke all on function public.app_ged_juger(text, text, text, text, text, text, text) from public, anon, authenticated;
grant execute on function public.app_ged_juger(text, text, text, text, text, text, text) to authenticated;

commit;

-- CONTRÔLES — tout VERT.
select '① le CHECK est revenu à vrai / faux / deja_su' as controle, count(*) as trouve,
       case when count(*) = 1 then 'VERT' else 'ROUGE' end as verdict
  from pg_constraint where conname = 'app_ged_jugement_verdict'
   and pg_get_constraintdef(oid) = 'CHECK ((verdict = ANY (ARRAY[''vrai''::text, ''faux''::text, ''deja_su''::text])))'
union all
select '② la porte est revenue à l''empreinte du 16/11', count(*),
       case when count(*) = 1 then 'VERT' else 'ROUGE' end
  from pg_proc where oid = 'public.app_ged_juger(text, text, text, text, text, text, text)'::regprocedure
   and md5(pg_get_functiondef(oid)) = '4d945b66df874c19f5a7b8e0643197c6'
union all
select '③ la porte : fermée à anon, ouverte à authenticated', count(*),
       case when count(*) = 1 then 'VERT' else 'ROUGE' end
  from pg_proc p where p.oid = 'public.app_ged_juger(text, text, text, text, text, text, text)'::regprocedure
   and p.prosecdef and not has_function_privilege('anon', p.oid, 'execute')
   and has_function_privilege('authenticated', p.oid, 'execute');
