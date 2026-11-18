-- Répétition de patch_ged_garder_lecture_2026-11-18.sql SANS RIEN GARDER : pose, joue la porte EN UTILISATEUR, contrôle,
-- et ANNULE (rollback).
-- ⛔ Ce fichier ne porte AUCUN « commit » (leçon du 13/11 : un patch joué « à blanc » avec son commit s'est commité).
-- ⚠ La mise en scène (un classement et deux lectures d'essai sur 63331) s'écrit AVANT le passage en `authenticated` :
--   en `authenticated`, une écriture directe serait refusée et la répétition ne prouverait rien (leçon du 16/11).
-- À coller tel quel ; chaque contrôle lève une exception s'il est ROUGE ; la dernière ligne dit « RÉPÉTITION VERTE ».
begin;
set local lock_timeout = '3s';

-- (le corps du patch, recopié sans son begin/commit)
alter table public.app_ged_journal drop constraint app_ged_journal_objet;
alter table public.app_ged_journal add constraint app_ged_journal_objet
  check (objet = any (array['classement'::text, 'rattachement'::text, 'lecture'::text]));
create function public.app_ged_lecture_garder(p_lecture_id uuid) returns jsonb
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  v_cran    text;
  v_lecture public.app_ged_lecture%rowtype;
  v_etat    text;
begin
  if not public.is_app_user_active() then
    raise exception '%', 'Compte inactif : la lecture ne peut pas être gardée.' using errcode = '42501';
  end if;
  select lower(btrim(value)) into v_cran from public.app_setting where key = 'ged_lecture_ia';
  if not (coalesce(v_cran, 'off') in ('on', 'true', '1', 'yes') or (v_cran = 'admin' and public.is_app_admin())) then
    raise exception '%', 'La lecture par l''IA n''est pas ouverte pour toi.' using errcode = '42501';
  end if;
  select * into v_lecture from public.app_ged_lecture where id = p_lecture_id for update;
  if not found then
    raise exception '%', 'Lecture introuvable.';
  end if;
  if not ((select public.is_app_global_reader())
          or v_lecture.hektor_annonce_id in (select m.hid from public.app_mes_biens_portefeuille() m(id, hid))) then
    raise exception '%', 'Ce bien n''est pas dans ton périmètre.' using errcode = '42501';
  end if;
  if v_lecture.etat <> 'pas_ce_type' then
    raise exception '%', 'Cette lecture n''a pas été refusée par l''IA : rien à garder.';
  end if;
  if exists (select 1 from public.app_ged_type t where t.code = v_lecture.type_code and t.sensible) then
    raise exception '%', 'Pièce des personnes : une lecture refusée ne se garde pas, elle se redépose.' using errcode = '42501';
  end if;
  v_etat := case when exists (select 1 from public.app_ged_valeur v where v.lecture_id = v_lecture.id and v.etat <> 'non_vu')
                 then 'lu' else 'incomplet' end;
  update public.app_ged_lecture set etat = v_etat where id = v_lecture.id;
  insert into public.app_ged_journal (objet, objet_id, geste, avant, apres, par)
  values ('lecture', v_lecture.id, 'garder_type',
          jsonb_build_object('etat', v_lecture.etat, 'type_code', v_lecture.type_code, 'hektor_annonce_id', v_lecture.hektor_annonce_id),
          jsonb_build_object('etat', v_etat),
          auth.uid());
  return jsonb_build_object('ok', true, 'etat', v_etat);
end
$function$;
revoke all on function public.app_ged_lecture_garder(uuid) from public, anon, authenticated;
grant execute on function public.app_ged_lecture_garder(uuid) to authenticated;

-- LA MISE EN SCÈNE (en rôle propriétaire) : une lecture refusée d'un carnet (avec une valeur vue), une refusée SANS
-- valeur, une refusée d'une pièce sensible, une lecture « lu »
create temp table rep_ids (role text primary key, id uuid) on commit drop;
grant select on rep_ids to authenticated;
do $scene$
declare c uuid; l uuid;
begin
  insert into public.app_ged_classement (hektor_annonce_id, document_name, type_code, origine)
  values ('63331', 'REPETITION garder lecture', 'copro.carnet', 'humain') returning id into c;
  insert into public.app_ged_lecture (classement_id, hektor_annonce_id, type_code, fiche, etat)
  values (c, '63331', 'copro.carnet', 'copro.carnet/1', 'pas_ce_type') returning id into l;
  insert into public.app_ged_valeur (lecture_id, cle, rang, etat) values (l, 'sous_type', 0, 'lu');
  insert into rep_ids values ('avec_valeur', l);
  insert into public.app_ged_lecture (classement_id, hektor_annonce_id, type_code, fiche, etat)
  values (c, '63331', 'copro.carnet', 'copro.carnet/1', 'pas_ce_type') returning id into l;
  insert into rep_ids values ('sans_valeur', l);
  insert into public.app_ged_lecture (classement_id, hektor_annonce_id, type_code, fiche, etat)
  values (c, '63331', 'justif.identite', 'justif.identite/1', 'pas_ce_type') returning id into l;
  insert into rep_ids values ('sensible', l);
  insert into public.app_ged_lecture (classement_id, hektor_annonce_id, type_code, fiche, etat)
  values (c, '63331', 'copro.carnet', 'copro.carnet/1', 'lu') returning id into l;
  insert into rep_ids values ('deja_lu', l);
end
$scene$;

-- LA PORTE, JOUÉE EN UTILISATEUR (Frédéric, admin : l'interrupteur est en « admin »)
select set_config('request.jwt.claims', json_build_object('sub', 'd4b1685f-948b-4ce8-af15-671b94a725e6',
                  'email', 'frederic.gerphagnon@gti-immobilier.fr', 'role', 'authenticated')::text, true);
set local role authenticated;
do $controle$
declare r jsonb;
begin
  -- ① une lecture refusée AVEC une valeur vue passe à « lu »
  r := public.app_ged_lecture_garder((select id from rep_ids where role = 'avec_valeur'));
  if r->>'etat' <> 'lu' then raise exception 'ROUGE ① : rendu %', r; end if;
  -- ② SANS valeur vue : « incomplet »
  r := public.app_ged_lecture_garder((select id from rep_ids where role = 'sans_valeur'));
  if r->>'etat' <> 'incomplet' then raise exception 'ROUGE ② : rendu %', r; end if;
  -- ③ la même lecture une 2e fois : refusée (rien à garder)
  begin
    perform public.app_ged_lecture_garder((select id from rep_ids where role = 'avec_valeur'));
    raise exception 'ROUGE ③ : une lecture déjà gardée a été regardée une 2e fois';
  exception when raise_exception then
    if sqlerrm like 'ROUGE%' then raise; end if;
  end;
  -- ④ une pièce SENSIBLE : refusée
  begin
    perform public.app_ged_lecture_garder((select id from rep_ids where role = 'sensible'));
    raise exception 'ROUGE ④ : une pièce des personnes a été gardée';
  exception when insufficient_privilege then null;
  end;
  -- ⑤ une lecture « lu » : refusée
  begin
    perform public.app_ged_lecture_garder((select id from rep_ids where role = 'deja_lu'));
    raise exception 'ROUGE ⑤ : une lecture « lu » a été regardée';
  exception when raise_exception then
    if sqlerrm like 'ROUGE%' then raise; end if;
  end;
  -- ⑥ une écriture DIRECTE de la lecture reste interdite à l'écran
  begin
    update public.app_ged_lecture set etat = 'lu' where id = (select id from rep_ids where role = 'sensible');
    if found then raise exception 'ROUGE ⑥ : authenticated écrit app_ged_lecture en direct'; end if;
  exception when insufficient_privilege then null;
  end;
end
$controle$;
reset role;

do $bilan$
declare n int;
begin
  -- ⑦ le journal porte DEUX lignes « lecture », AVANT / APRÈS, au nom de Frédéric
  select count(*) into n from public.app_ged_journal j join rep_ids r on r.id = j.objet_id
   where j.objet = 'lecture' and j.geste = 'garder_type' and j.avant->>'etat' = 'pas_ce_type'
     and j.par = 'd4b1685f-948b-4ce8-af15-671b94a725e6'::uuid;
  if n <> 2 then raise exception 'ROUGE ⑦ : % ligne(s) au journal au lieu de 2', n; end if;
  -- ⑧ la pièce sensible et la lecture « lu » n'ont pas bougé
  select count(*) into n from public.app_ged_lecture l join rep_ids r on r.id = l.id
   where (r.role = 'sensible' and l.etat <> 'pas_ce_type') or (r.role = 'deja_lu' and l.etat <> 'lu');
  if n <> 0 then raise exception 'ROUGE ⑧ : % lecture(s) touchée(s) à tort', n; end if;
  raise notice 'RÉPÉTITION VERTE (8 contrôles) -- rien ne reste : rollback';
end
$bilan$;
rollback;
