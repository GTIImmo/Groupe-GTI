-- ============================================================================
-- REPETITION -- la date de cloture reservee au manager / admin ((7)-3a piece 2)
-- 16/10/2026
-- ============================================================================
-- ⚠⚠ A COLLER EN UNE SEULE FOIS, EN ENTIER. Le `begin;` de la premiere ligne et
--    l ERREUR VOLONTAIRE de la derniere font que RIEN n est ecrit.
--
-- Elle joue, dans l ordre REEL : mesures AVANT (dont le TEMOIN INVERSE : un
-- negociateur est-il accepte aujourd hui ?) -> LE VRAI PATCH -> mesures APRES
-- (les TROIS identites, en empruntant leur JWT) -> LE VRAI INVERSE -> mesure du
-- RETOUR -> erreur volontaire qui annule tout.
--
-- LE MESSAGE ATTENDU si tout va bien :
--    1-avant  | la garde est dans la fonction  = non
--    1-avant  | empreinte de la fonction       = 09280b46e6832db15dce53ca5e30e9db
--    1-avant  | ancre vue combien de fois      = 1
--    1-avant  | TEMOIN INVERSE negociateur     = ACCEPTE (ok=true) -- le trou est reel
--    2-apres  | la garde est dans la fonction  = oui
--    2-apres  | la fonction compile            = oui (elle a ete reexecutee)
--    2-apres  | negociateur (legrand)          = REFUSE : droits_insuffisants
--    2-apres  | le refus est en francais       = oui
--    2-apres  | admin (codex.test)             = ACCEPTE (ok=true)
--    2-apres  | service_role (worker/re-pose)  = ACCEPTE (ok=true)
--    3-retour | la garde est dans la fonction  = non
--    3-retour | trace is_app_manager_or_admin  = non
--    3-retour | trace droits_insuffisants      = non
--    3-retour | empreinte de la fonction       = IDENTIQUE
--
-- ⚠ CE QUE CETTE REPETITION NE PEUT PAS PROUVER : il n y a AUCUN manager actif
--   dans app_user_profile aujourd hui (mesure du 16/10 : 4 admin, 2 commercial,
--   0 manager). La branche « manager » repose donc sur
--   is_app_manager_or_admin(), qui est deja en production et teste role in
--   ('admin','manager'). Non eprouve en reel, et je le dis.
--
-- ⚠ Les essais d ACCEPTATION ecrivent une date sur l annonce d essai 24933
--   (mandat 11939) -- dans la transaction, donc ANNULEE. Rien ne reste.
-- ============================================================================

begin;

create temporary table essai_mesures (
  id serial, etape text, mesure text, valeur text
) on commit drop;

-- =============================== 1. AVANT ==================================
insert into essai_mesures (etape, mesure, valeur)
select '1-avant ', 'la garde est dans la fonction ',
       case when replace(pg_get_functiondef(p.oid), chr(13), '') like '%GARDE MANAGER ADMIN%' then 'oui' else 'non' end
from pg_proc p join pg_namespace n on n.oid = p.pronamespace
where n.nspname='public' and p.proname='app_set_mandat_cloture_optimistic';

insert into essai_mesures (etape, mesure, valeur)
select '1-avant ', 'empreinte de la fonction      ', md5(replace(pg_get_functiondef(p.oid), chr(13), ''))
from pg_proc p join pg_namespace n on n.oid = p.pronamespace
where n.nspname='public' and p.proname='app_set_mandat_cloture_optimistic';

insert into essai_mesures (etape, mesure, valeur)
select '1-avant ', 'ancre vue combien de fois     ',
       ((length(s) - length(replace(s, '  IF v_annonce is null OR v_numero is null THEN', '')))
         / length('  IF v_annonce is null OR v_numero is null THEN'))::text
from (select replace(pg_get_functiondef(p.oid), chr(13), '') as s
      from pg_proc p join pg_namespace n on n.oid = p.pronamespace
      where n.nspname='public' and p.proname='app_set_mandat_cloture_optimistic') q;

-- ⭐ LE TEMOIN INVERSE. Si le negociateur est DEJA refuse avant le patch, alors
--    le patch ne prouverait rien. Il doit etre ACCEPTE ici.
do $do$
declare r jsonb; v_txt text;
begin
  begin
    perform set_config('request.jwt.claims',
      '{"sub":"05beded4-3e17-4a0c-ab58-e2c63da3da24","role":"authenticated","email":"legrand@gti-immobilier.fr"}', true);
    r := public.app_set_mandat_cloture_optimistic('24933', '11939', '2026-10-16');
    v_txt := case when coalesce((r->>'ok')::boolean, false)
                  then 'ACCEPTE (ok=true) -- le trou est reel'
                  else 'DEJA REFUSE : ' || coalesce(r->>'erreur','?') || ' -- le patch ne prouverait rien' end;
  exception when others then
    v_txt := 'non joue (' || left(sqlerrm, 70) || ')';
  end;
  perform set_config('request.jwt.claims', '', true);
  insert into essai_mesures (etape, mesure, valeur)
  values ('1-avant ', 'TEMOIN INVERSE negociateur    ', v_txt);
end
$do$;

-- =============================== 2. LE PATCH ===============================
do $do$
declare
  v_src   text;
  v_new   text;
  v_ancre text := replace('  IF v_annonce is null OR v_numero is null THEN', chr(13), '');
  v_ajout text;
  v_vu    integer;
begin
  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_src
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public' and p.proname = 'app_set_mandat_cloture_optimistic';
  if v_src is null then raise exception 'STOP : fonction introuvable'; end if;
  if position('GARDE MANAGER ADMIN' in v_src) > 0 then
    raise notice 'DEJA FAIT'; return;
  end if;
  if not exists (
    select 1 from pg_proc p join pg_namespace n on n.oid = p.pronamespace
     where n.nspname = 'public' and p.proname = 'is_app_manager_or_admin'
  ) then
    raise exception 'STOP : is_app_manager_or_admin() est introuvable';
  end if;
  v_vu := (length(v_src) - length(replace(v_src, v_ancre, ''))) / length(v_ancre);
  if v_vu <> 1 then raise exception 'STOP : ancre vue % fois', v_vu; end if;

  v_ajout := replace(
'  -- GARDE MANAGER ADMIN -- DEBUT
  -- (7)-3a piece 2 (16/10/2026) : SEUL UN MANAGER OU UN ADMIN FIXE LA DATE.
  -- Demande de Frederic du 16/10. Elle REMPLACE la decision du 13/10 qui disait
  -- que `authenticated` etait VOULU ici (patch_chantier3_3c_piece4_droits, l.22).
  -- On garde le GRANT a authenticated et on refuse PROPREMENT : le front avale
  -- les erreurs de cette fonction (console.warn), donc une erreur de permission
  -- serait un silence. `anon` n a aucun droit (chantier (1)).
  -- `service_role` passe : le worker et la re-pose n ont pas de auth.uid().
  IF coalesce(v_role, '''') <> ''service_role''
     AND NOT public.is_app_manager_or_admin() THEN
    RETURN jsonb_build_object(
      ''ok'', false,
      ''erreur'', ''droits_insuffisants'',
      ''message'', ''Seul un manager ou un administrateur peut fixer la date de cloture du mandat. Un negociateur passe par une demande d annulation de mandat.'');
  END IF;
  -- GARDE MANAGER ADMIN -- FIN
' || v_ancre, chr(13), '');

  v_new := replace(v_src, v_ancre, v_ajout);
  execute v_new;
  raise notice 'PATCH POSE';
end
$do$;

-- =============================== 3. APRES ==================================
insert into essai_mesures (etape, mesure, valeur)
select '2-apres ', 'la garde est dans la fonction ',
       case when replace(pg_get_functiondef(p.oid), chr(13), '') like '%GARDE MANAGER ADMIN%' then 'oui' else 'NON -- PROBLEME' end
from pg_proc p join pg_namespace n on n.oid = p.pronamespace
where n.nspname='public' and p.proname='app_set_mandat_cloture_optimistic';

insert into essai_mesures (etape, mesure, valeur)
values ('2-apres ', 'la fonction compile           ', 'oui (elle a ete reexecutee sans erreur)');

-- LES TROIS IDENTITES, en empruntant leur JWT (on ne change PAS de role
-- Postgres : la fonction lit le role DANS les claims, et is_app_manager_or_admin
-- lit auth.uid(), qui vient des claims aussi).
do $do$
declare
  r jsonb;
  v_nego text; v_fr text; v_admin text; v_svc text;
begin
  -- a) le negociateur : il doit etre REFUSE
  begin
    perform set_config('request.jwt.claims',
      '{"sub":"05beded4-3e17-4a0c-ab58-e2c63da3da24","role":"authenticated","email":"legrand@gti-immobilier.fr"}', true);
    r := public.app_set_mandat_cloture_optimistic('24933', '11939', '2026-10-16');
    v_nego := case when coalesce((r->>'ok')::boolean, false)
                   then 'ACCEPTE -- PROBLEME, la garde ne mord pas'
                   else 'REFUSE : ' || coalesce(r->>'erreur','?') end;
    v_fr := case when coalesce(r->>'message','') like '%manager ou un administrateur%' then 'oui' else 'NON : ' || left(coalesce(r->>'message','(aucun message)'), 50) end;
  exception when others then
    v_nego := 'non joue (' || left(sqlerrm, 70) || ')'; v_fr := 'non mesure';
  end;

  -- b) l administrateur : il doit etre ACCEPTE
  begin
    perform set_config('request.jwt.claims',
      '{"sub":"0548613b-7654-42fa-a65d-d9adc815d2c0","role":"authenticated","email":"codex.test@gti-immobilier.fr"}', true);
    r := public.app_set_mandat_cloture_optimistic('24933', '11939', '2026-10-16');
    v_admin := case when coalesce((r->>'ok')::boolean, false)
                    then 'ACCEPTE (ok=true)'
                    else 'REFUSE -- PROBLEME : ' || coalesce(r->>'erreur','?') end;
  exception when others then
    v_admin := 'non joue (' || left(sqlerrm, 70) || ')';
  end;

  -- c) le service_role : le worker et la re-pose ne doivent PAS etre enfermes
  begin
    perform set_config('request.jwt.claims', '{"role":"service_role"}', true);
    r := public.app_set_mandat_cloture_optimistic('24933', '11939', '2026-10-16');
    v_svc := case when coalesce((r->>'ok')::boolean, false)
                  then 'ACCEPTE (ok=true)'
                  else 'REFUSE -- PROBLEME : ' || coalesce(r->>'erreur','?') end;
  exception when others then
    v_svc := 'non joue (' || left(sqlerrm, 70) || ')';
  end;

  perform set_config('request.jwt.claims', '', true);

  insert into essai_mesures (etape, mesure, valeur) values
    ('2-apres ', 'negociateur (legrand)         ', v_nego),
    ('2-apres ', 'le refus est en francais      ', v_fr),
    ('2-apres ', 'admin (codex.test)            ', v_admin),
    ('2-apres ', 'service_role (worker/re-pose) ', v_svc);
end
$do$;

-- =============================== 4. L INVERSE ==============================
do $do$
declare
  v_src text; v_new text; v_debut integer; v_fin integer;
  v_borne_d text := replace('  -- GARDE MANAGER ADMIN -- DEBUT', chr(13), '');
  v_borne_f text := replace('  -- GARDE MANAGER ADMIN -- FIN', chr(13), '');
begin
  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_src
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public' and p.proname = 'app_set_mandat_cloture_optimistic';
  if position('GARDE MANAGER ADMIN' in v_src) = 0 then
    raise notice 'INVERSE : rien a retirer'; return;
  end if;
  v_debut := position(v_borne_d in v_src);
  v_fin   := position(v_borne_f in v_src);
  if v_debut = 0 or v_fin = 0 or v_fin <= v_debut then
    raise exception 'STOP : bornes introuvables';
  end if;
  v_new := substr(v_src, 1, v_debut - 1) || substr(v_src, v_fin + length(v_borne_f) + 1);
  execute v_new;
  raise notice 'INVERSE JOUE';
end
$do$;

-- =============================== 5. LE RETOUR ==============================
insert into essai_mesures (etape, mesure, valeur)
select '3-retour', 'la garde est dans la fonction ',
       case when replace(pg_get_functiondef(p.oid), chr(13), '') like '%GARDE MANAGER ADMIN%' then 'OUI -- PROBLEME' else 'non' end
from pg_proc p join pg_namespace n on n.oid = p.pronamespace
where n.nspname='public' and p.proname='app_set_mandat_cloture_optimistic';

insert into essai_mesures (etape, mesure, valeur)
select '3-retour', 'trace is_app_manager_or_admin ',
       case when replace(pg_get_functiondef(p.oid), chr(13), '') like '%is_app_manager_or_admin%' then 'OUI -- PROBLEME' else 'non' end
from pg_proc p join pg_namespace n on n.oid = p.pronamespace
where n.nspname='public' and p.proname='app_set_mandat_cloture_optimistic';

insert into essai_mesures (etape, mesure, valeur)
select '3-retour', 'trace droits_insuffisants     ',
       case when replace(pg_get_functiondef(p.oid), chr(13), '') like '%droits_insuffisants%' then 'OUI -- PROBLEME' else 'non' end
from pg_proc p join pg_namespace n on n.oid = p.pronamespace
where n.nspname='public' and p.proname='app_set_mandat_cloture_optimistic';

insert into essai_mesures (etape, mesure, valeur)
select '3-retour', 'empreinte de la fonction      ',
       case when md5(replace(pg_get_functiondef(p.oid), chr(13), '')) = '09280b46e6832db15dce53ca5e30e9db'
            then 'IDENTIQUE' else 'DIFFERENTE : ' || md5(replace(pg_get_functiondef(p.oid), chr(13), '')) end
from pg_proc p join pg_namespace n on n.oid = p.pronamespace
where n.nspname='public' and p.proname='app_set_mandat_cloture_optimistic';

-- ========================= 6. L ERREUR VOLONTAIRE ==========================
do $do$
declare v_txt text;
begin
  select string_agg(etape || ' | ' || mesure || ' = ' || valeur, chr(10) order by id)
    into v_txt from essai_mesures;
  raise exception 'ESSAI ANNULE -- rien n a ete ecrit. %', chr(10) || v_txt;
end
$do$;

rollback;
