-- Répétition de patch_ged_masquer_2026-11-20.sql SANS RIEN GARDER : pose, joue la porte EN UTILISATEUR, contrôle, ANNULE.
-- ⛔ Aucun « commit » ici (leçon du 13/11) : la dernière instruction LÈVE « RÉPÉTITION VERTE » exprès, pour que rien ne
--   reste même par un outil qui commiterait. Toute autre erreur = ROUGE, et rien ne reste non plus.
-- Joué sur le bien d'essai 63331, en Frédéric (admin : l'interrupteur ged_propositions est en « admin »).
begin;
set local lock_timeout = '3s';

-- (le corps du patch, recopié sans son begin/commit)
do $garde$
begin
  if to_regclass('public.app_ged_jugement') is null then raise exception 'ARRET : app_ged_jugement absente (morceau 10)'; end if;
  if md5(pg_get_functiondef('public.app_ged_juger(text, text, text, text, text, text, text)'::regprocedure)) <> '4d945b66df874c19f5a7b8e0643197c6' then
    raise exception 'ARRET : app_ged_juger a change depuis le 20/11 -- quelqu''un est passe avant, relire avant de poser';
  end if;
  if (select pg_get_constraintdef(oid) from pg_constraint where conname = 'app_ged_jugement_verdict'
        and conrelid = 'public.app_ged_jugement'::regclass)
     <> 'CHECK ((verdict = ANY (ARRAY[''vrai''::text, ''faux''::text, ''deja_su''::text])))' then
    raise exception 'ARRET : le CHECK du verdict a change -- patch deja applique ?';
  end if;
end
$garde$;

-- ─────────────────────────────────────────────────────── ① LE CHECK DU JOURNAL
alter table public.app_ged_jugement drop constraint app_ged_jugement_verdict;
alter table public.app_ged_jugement add constraint app_ged_jugement_verdict
  check (verdict in ('vrai', 'faux', 'deja_su', 'masque', 'reaffiche'));

comment on table public.app_ged_jugement is
  'GED morceau 10 (16/11/2026) : le jugement humain d''une ligne « À regarder », qui et quand. Depuis le 20/11 (visuel V3) : '
  '« masque » / « reaffiche » (un point d''attention écarté pour TOUT LE MONDE sur le bien, réversible). '
  'Journal : jamais modifié ni effacé ; le plus récent d''une ligne fait foi. Écrit par app_ged_juger seule.';

-- ─────────────────────────────────────────────────────── ② LA PORTE D'ÉCRITURE (seule la garde du verdict change)
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
  -- Visuel V3 (20/11/2026) : « masque » / « reaffiche » en plus (décision de Frédéric : masquer vaut pour tout le monde).
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
  if coalesce(p_verdict, '') not in ('vrai', 'faux', 'deja_su', 'masque', 'reaffiche') then
    raise exception '%', 'Verdict inconnu (vrai, faux, deja_su, masque ou reaffiche).';
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
  'GED morceau 10 (16/11/2026) : garde le jugement d''une ligne « À regarder » (vrai / faux / deja_su ; depuis le 20/11 : '
  'masque / reaffiche, pour tout le monde sur le bien). Auteur = auth.uid(). Interrupteur ged_propositions, périmètre du '
  'bien. N''écrit que dans app_ged_jugement.';

-- Les droits ne changent pas (create or replace les garde) ; on les repose quand même, à l'identique.
revoke all on function public.app_ged_juger(text, text, text, text, text, text, text) from public, anon, authenticated;
grant execute on function public.app_ged_juger(text, text, text, text, text, text, text) to authenticated;

-- LA PORTE, JOUÉE EN UTILISATEUR
select set_config('request.jwt.claims', json_build_object('sub', 'd4b1685f-948b-4ce8-af15-671b94a725e6',
                  'role', 'authenticated')::text, true);
set local role authenticated;
do $joue$
declare r jsonb; v text;
begin
  -- ① masquer une ligne
  r := public.app_ged_juger('63331', 'REPET', 'REPET|une ligne d''essai', 'une ligne d''essai', 'alerte', 'masque', null);
  if coalesce((r->>'ok')::boolean, false) is not true then raise exception 'ROUGE ① : rendu %', r; end if;
  if not exists (select 1 from public.app_ged_jugement where hektor_annonce_id = '63331' and cle = 'REPET|une ligne d''essai'
                   and verdict = 'masque') then raise exception 'ROUGE ① : « masque » absent du journal'; end if;
  -- ② la réafficher (⚠ dans UNE transaction, now() est le même pour les deux lignes : on vérifie la présence, pas l'ordre ;
  --   à l'écran chaque clic est sa propre transaction, et le plus récent fait foi)
  r := public.app_ged_juger('63331', 'REPET', 'REPET|une ligne d''essai', 'une ligne d''essai', 'alerte', 'reaffiche', null);
  if not exists (select 1 from public.app_ged_jugement where hektor_annonce_id = '63331' and cle = 'REPET|une ligne d''essai'
                   and verdict = 'reaffiche') then raise exception 'ROUGE ② : « reaffiche » absent du journal'; end if;
  -- ③ un verdict inconnu est refusé
  begin
    r := public.app_ged_juger('63331', 'REPET', 'REPET|une ligne d''essai', 'une ligne d''essai', 'alerte', 'bidon', null);
    raise exception 'ROUGE ③ : un verdict inconnu est passé';
  exception when others then
    if sqlerrm not like 'Verdict inconnu%' then raise; end if;
  end;
  -- ④ les anciens verdicts passent toujours
  r := public.app_ged_juger('63331', 'REPET', 'REPET|une autre ligne', 'une autre ligne', 'info', 'vrai', null);
  -- ⑤ authenticated n'écrit toujours PAS en direct
  begin
    insert into public.app_ged_jugement (hektor_annonce_id, regle, cle, texte, niveau, verdict, juge_par)
    values ('63331', 'REPET', 'REPET|direct', 'direct', 'info', 'masque', auth.uid());
    raise exception 'ROUGE ⑤ : authenticated écrit le journal en direct';
  exception when insufficient_privilege then null;
  end;
end
$joue$;
reset role;

do $bilan$
declare n int;
begin
  -- ⑥ trois lignes d'essai, auteur = Frédéric
  select count(*) into n from public.app_ged_jugement where regle = 'REPET' and juge_par = 'd4b1685f-948b-4ce8-af15-671b94a725e6';
  if n <> 3 then raise exception 'ROUGE ⑥ : % ligne(s) d''essai au lieu de 3', n; end if;
  -- ⑦ les jugements d'avant n'ont pas bougé
  select count(*) into n from public.app_ged_jugement where regle <> 'REPET' and verdict in ('masque', 'reaffiche');
  if n <> 0 then raise exception 'ROUGE ⑦ : % ancien(s) jugement(s) touché(s)', n; end if;
  -- ⑧ la porte reste fermée à anon
  if has_function_privilege('anon', 'public.app_ged_juger(text, text, text, text, text, text, text)'::regprocedure, 'execute') then
    raise exception 'ROUGE ⑧ : anon peut appeler la porte';
  end if;
  raise exception 'RÉPÉTITION VERTE (8 contrôles) -- rien ne reste';
end
$bilan$;
