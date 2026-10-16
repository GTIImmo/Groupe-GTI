-- ============================================================================
-- REPETITION -- mettre une photo en couverture ((7)-3c)
-- 16/10/2026
-- ============================================================================
-- ⚠⚠ A COLLER EN UNE SEULE FOIS, EN ENTIER. Le `begin;` de la premiere ligne et
--    l'ERREUR VOLONTAIRE de la derniere font que RIEN n'est ecrit.
--
-- Elle joue, dans l'ordre REEL : mesures AVANT -> LES 3 VERROUS + LA RPC ->
-- mesures APRES (dont un VRAI ESSAI sur le bac a sable 62774) -> L'INVERSE ->
-- mesure du RETOUR -> erreur volontaire qui annule tout.
--
-- ⚠ Le patch reel contient un `VALIDATE CONSTRAINT` HORS transaction. Il n'est
--   pas rejoue ici (il ne peut pas l'etre dans une transaction annulee) : c'est
--   la seule difference entre cette repetition et le vrai patch, et elle est
--   sans risque (la contrainte est posee NOT VALID, elle mord des la pose sur
--   les lignes NEUVES -- la validation ne sert qu'a l'existant).
--
-- LE MESSAGE ATTENDU si tout va bien :
--    1-avant  | contrainte connait le type      = non
--    1-avant  | droits connaissent le type      = non
--    1-avant  | distribution connait le type    = non
--    1-avant  | la RPC existe                   = non
--    1-avant  | 62774 : 4 visibles, 1ere 482253, rangs 1..4
--    2-apres  | contrainte connait le type      = oui
--    2-apres  | droits : colle a delete_hektor_photo = oui
--    2-apres  | distribution : branche documents = oui
--    2-apres  | RPC : authenticated oui / anon non = oui
--    2-apres  | ESSAI mettre 487604 en couverture = ok (N renumerotees)
--    2-apres  | 62774 apres : 1ere 487604, rangs 0..3
--    2-apres  | le travail porte les 2 listes   = 4 visibles / 0 masquees
--    2-apres  | l'ordre d'AVANT est garde       = 4 photos
--    2-apres  | RE-ESSAI (deja en couverture)   = ok, sans nouveau travail
--    3-retour | le type a disparu des 3 verrous = oui
--    3-retour | la RPC a disparu                = oui
--    3-retour | contrainte (texte nu)           = IDENTIQUE (+ suffixe NOT VALID,
--                                                  normal : VALIDATE ne se lance pas
--                                                  dans une transaction annulee)
--    3-retour | droits (empreinte)              = IDENTIQUE
--    3-retour | distribution (empreinte)        = IDENTIQUE
--
-- ⚠ Si l'ESSAI dit « non joue : droits refuses », ce n'est PAS un echec : la RPC
--   verifie l'identite de l'appelant et l'editeur SQL n'en a pas toujours une.
--   Les controles de structure, eux, font foi.
-- ============================================================================

begin;

create temporary table essai_mesures (id serial, etape text, mesure text, valeur text) on commit drop;

-- =============================== 1. AVANT ==================================
insert into essai_mesures (etape, mesure, valeur)
select '1-avant ', 'contrainte connait le type   ',
       case when pg_get_constraintdef(c.oid) like '%reorder_hektor_photos%' then 'oui' else 'non' end
from pg_constraint c
where c.conrelid='public.app_console_job'::regclass and c.conname='app_console_job_job_type_check';

insert into essai_mesures (etape, mesure, valeur)
select '1-avant ', 'droits connaissent le type   ',
       case when replace(pg_get_functiondef(p.oid), chr(13),'') like '%reorder_hektor_photos%' then 'oui' else 'non' end
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname='public' and p.proname='app_console_can_request_job';

insert into essai_mesures (etape, mesure, valeur)
select '1-avant ', 'distribution connait le type ',
       case when replace(pg_get_functiondef(p.oid), chr(13),'') like '%reorder_hektor_photos%' then 'oui' else 'non' end
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname='public' and p.proname='app_console_claim_next_job';

insert into essai_mesures (etape, mesure, valeur)
values ('1-avant ', 'la RPC existe                ',
        case when exists (select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
                           where n.nspname='public' and p.proname='app_console_photo_couverture_optimistic')
             then 'oui' else 'non' end);

insert into essai_mesures (etape, mesure, valeur)
select '1-avant ', '62774 : etat de la galerie   ',
       count(*)::text || ' visibles, 1ere ' ||
       (array_agg(hektor_photo_id order by sort_order asc, id asc))[1] ||
       ', rangs ' || min(sort_order)::text || '..' || max(sort_order)::text
from app_console_photo
where hektor_annonce_id='62774' and visible is true and present_in_hektor is true;

-- =========================== 2. LE PATCH ===================================
do $contrainte$
declare v_def text; v_ancre text := replace('''delete_hektor_photo''::text])))', chr(13), ''); v_neuf text;
begin
  select pg_get_constraintdef(c.oid) into v_def from pg_constraint c
   where c.conrelid='public.app_console_job'::regclass and c.conname='app_console_job_job_type_check';
  if position('reorder_hektor_photos' in v_def) > 0 then raise notice 'DEJA FAIT (contrainte)'; return; end if;
  if (length(v_def) - length(replace(v_def, v_ancre, ''))) / length(v_ancre) <> 1 then
    raise exception 'STOP : ancre de contrainte non unique'; end if;
  v_neuf := replace(v_def, v_ancre, replace('''delete_hektor_photo''::text, ''reorder_hektor_photos''::text])))', chr(13), ''));
  execute 'ALTER TABLE public.app_console_job DROP CONSTRAINT app_console_job_job_type_check';
  execute 'ALTER TABLE public.app_console_job ADD CONSTRAINT app_console_job_job_type_check ' || v_neuf || ' NOT VALID';
end $contrainte$;

do $droits$
declare v_def text; v_ancre text := replace('''delete_hektor_photo'',', chr(13), '');
begin
  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_def from pg_proc p
    join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname='app_console_can_request_job';
  if position('reorder_hektor_photos' in v_def) > 0 then raise notice 'DEJA FAIT (droits)'; return; end if;
  if (length(v_def) - length(replace(v_def, v_ancre, ''))) / length(v_ancre) <> 1 then
    raise exception 'STOP : ancre des droits non unique'; end if;
  execute replace(v_def, v_ancre, replace('''delete_hektor_photo'',''reorder_hektor_photos'',', chr(13), ''));
end $droits$;

do $distribution$
declare v_def text; v_ancre text := replace('''delete_hektor_photo''', chr(13), '');
begin
  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_def from pg_proc p
    join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname='app_console_claim_next_job';
  if position('reorder_hektor_photos' in v_def) > 0 then raise notice 'DEJA FAIT (distribution)'; return; end if;
  if (length(v_def) - length(replace(v_def, v_ancre, ''))) / length(v_ancre) <> 1 then
    raise exception 'STOP : ancre de distribution non unique'; end if;
  execute replace(v_def, v_ancre, replace('''delete_hektor_photo'',''reorder_hektor_photos''', chr(13), ''));
end $distribution$;

CREATE OR REPLACE FUNCTION public.app_console_photo_couverture_optimistic(
  p_app_dossier_id bigint, p_hektor_annonce_id text, p_hektor_photo_id text
) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path TO 'public'
AS $fn$
DECLARE
  v_annonce text := nullif(btrim(coalesce(p_hektor_annonce_id, '')), '');
  v_photo   text := nullif(btrim(coalesce(p_hektor_photo_id, '')), '');
  v_avant jsonb; v_premier text; v_visibles jsonb; v_masquees jsonb;
  v_job_id uuid; v_combien integer;
BEGIN
  IF v_annonce IS NULL OR v_photo IS NULL OR p_app_dossier_id IS NULL THEN
    RETURN jsonb_build_object('ok', false, 'erreur', 'parametres_incomplets'); END IF;
  IF NOT coalesce(public.app_console_can_access_dossier(p_app_dossier_id, v_annonce), false) THEN
    RETURN jsonb_build_object('ok', false, 'erreur', 'droits_insuffisants'); END IF;
  SELECT jsonb_agg(jsonb_build_object('hektor_photo_id', hektor_photo_id, 'sort_order', sort_order, 'visible', visible)
                   ORDER BY visible DESC, sort_order ASC, id ASC)
    INTO v_avant FROM public.app_console_photo
   WHERE app_dossier_id = p_app_dossier_id AND present_in_hektor IS TRUE;
  IF NOT EXISTS (SELECT 1 FROM public.app_console_photo
     WHERE app_dossier_id = p_app_dossier_id AND hektor_photo_id = v_photo
       AND visible IS TRUE AND present_in_hektor IS TRUE) THEN
    RETURN jsonb_build_object('ok', false, 'erreur', 'photo_introuvable_ou_masquee'); END IF;
  SELECT hektor_photo_id INTO v_premier FROM public.app_console_photo
   WHERE app_dossier_id = p_app_dossier_id AND visible IS TRUE AND present_in_hektor IS TRUE
   ORDER BY sort_order ASC, id ASC LIMIT 1;
  IF v_premier = v_photo THEN
    RETURN jsonb_build_object('ok', true, 'deja_en_couverture', true); END IF;
  WITH ordonnees AS (
    SELECT id, (row_number() OVER (ORDER BY (hektor_photo_id = v_photo) DESC, sort_order ASC, id ASC) - 1)::integer AS rang
      FROM public.app_console_photo
     WHERE app_dossier_id = p_app_dossier_id AND visible IS TRUE AND present_in_hektor IS TRUE)
  UPDATE public.app_console_photo p SET sort_order = o.rang, updated_at = now()
    FROM ordonnees o WHERE o.id = p.id AND p.sort_order IS DISTINCT FROM o.rang;
  GET DIAGNOSTICS v_combien = ROW_COUNT;
  SELECT coalesce(jsonb_agg(hektor_photo_id ORDER BY sort_order ASC, id ASC), '[]'::jsonb) INTO v_visibles
    FROM public.app_console_photo
   WHERE app_dossier_id = p_app_dossier_id AND visible IS TRUE AND present_in_hektor IS TRUE;
  SELECT coalesce(jsonb_agg(hektor_photo_id ORDER BY sort_order ASC, id ASC), '[]'::jsonb) INTO v_masquees
    FROM public.app_console_photo
   WHERE app_dossier_id = p_app_dossier_id AND visible IS FALSE AND present_in_hektor IS TRUE;
  INSERT INTO public.app_console_job
    (job_type, app_dossier_id, hektor_annonce_id, payload_json, priority, requested_by)
  VALUES ('reorder_hektor_photos', p_app_dossier_id, v_annonce,
     jsonb_build_object('motif','couverture','hektor_photo_id', v_photo,
       'liste_photos', v_visibles, 'liste_photos_hidden', v_masquees,
       'base_snapshot', coalesce(v_avant, '[]'::jsonb)), 20, auth.uid())
  RETURNING id INTO v_job_id;
  RETURN jsonb_build_object('ok', true, 'deja_en_couverture', false, 'job_id', v_job_id,
    'photos_renumerotees', v_combien, 'visibles', jsonb_array_length(v_visibles),
    'masquees', jsonb_array_length(v_masquees));
END $fn$;

REVOKE ALL ON FUNCTION public.app_console_photo_couverture_optimistic(bigint, text, text) FROM public;
GRANT EXECUTE ON FUNCTION public.app_console_photo_couverture_optimistic(bigint, text, text) TO authenticated, service_role;

-- =============================== 3. APRES ==================================
insert into essai_mesures (etape, mesure, valeur)
select '2-apres ', 'contrainte connait le type   ',
       case when pg_get_constraintdef(c.oid) like '%''reorder_hektor_photos''::text%' then 'oui' else 'NON -- PROBLEME' end
from pg_constraint c
where c.conrelid='public.app_console_job'::regclass and c.conname='app_console_job_job_type_check';

insert into essai_mesures (etape, mesure, valeur)
select '2-apres ', 'droits : colle a delete_photo',
       case when replace(pg_get_functiondef(p.oid), chr(13),'') like '%''delete_hektor_photo'',''reorder_hektor_photos''%' then 'oui' else 'NON -- PROBLEME' end
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname='public' and p.proname='app_console_can_request_job';

insert into essai_mesures (etape, mesure, valeur)
select '2-apres ', 'distribution : branche docs  ',
       case when replace(pg_get_functiondef(p.oid), chr(13),'') like '%''sync_hektor_photos'',''upload_hektor_photo'',''delete_hektor_photo'',''reorder_hektor_photos''%'
            then 'oui' else 'NON -- PROBLEME (pas colle a ses soeurs)' end
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname='public' and p.proname='app_console_claim_next_job';

insert into essai_mesures (etape, mesure, valeur)
select '2-apres ', 'RPC : authenticated / anon   ',
       case when array_to_string(p.proacl,' ') like '%authenticated=X%'
             and array_to_string(p.proacl,' ') not like '%anon=%'
            then 'oui / non (correct)' else 'PROBLEME : ' || coalesce(array_to_string(p.proacl,' | '),'(aucun)') end
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname='public' and p.proname='app_console_photo_couverture_optimistic';

-- ⭐ LE VRAI ESSAI, sur le bac a sable 62774 (dossier 3828957).
--    On met LA DERNIERE photo (487604) en couverture : elle doit passer au rang 0.
do $essai$
declare
  r jsonb; v_txt text; v_apres text; v_charge jsonb; v_job uuid;
begin
  begin
    perform set_config('request.jwt.claims',
      '{"sub":"0548613b-7654-42fa-a65d-d9adc815d2c0","role":"authenticated","email":"codex.test@gti-immobilier.fr"}', true);
    r := public.app_console_photo_couverture_optimistic(3828957, '62774', '487604');
    if coalesce((r->>'ok')::boolean, false) then
      v_txt := 'ok : ' || coalesce(r->>'photos_renumerotees','?') || ' renumerotees, '
               || coalesce(r->>'visibles','?') || ' visibles, ' || coalesce(r->>'masquees','?') || ' masquees';
      v_job := (r->>'job_id')::uuid;
    else
      v_txt := 'REFUSE : ' || coalesce(r->>'erreur','?') || ' -- normal si l''editeur n''a pas d''identite';
    end if;
  exception when others then
    v_txt := 'non joue (' || left(sqlerrm, 70) || ')';
  end;
  insert into essai_mesures (etape, mesure, valeur) values ('2-apres ', 'ESSAI 487604 en couverture   ', v_txt);

  select count(*)::text || ' visibles, 1ere ' ||
         (array_agg(hektor_photo_id order by sort_order asc, id asc))[1] ||
         ', rangs ' || min(sort_order)::text || '..' || max(sort_order)::text
    into v_apres
    from app_console_photo
   where hektor_annonce_id='62774' and visible is true and present_in_hektor is true;
  insert into essai_mesures (etape, mesure, valeur) values ('2-apres ', '62774 apres l''essai         ', coalesce(v_apres,'(rien)'));

  if v_job is not null then
    select payload_json into v_charge from app_console_job where id = v_job;
    insert into essai_mesures (etape, mesure, valeur) values
      ('2-apres ', 'le travail porte les 2 listes',
       jsonb_array_length(v_charge->'liste_photos')::text || ' visibles / '
       || jsonb_array_length(v_charge->'liste_photos_hidden')::text || ' masquees'),
      ('2-apres ', 'l''ordre d''AVANT est garde    ',
       jsonb_array_length(v_charge->'base_snapshot')::text || ' photos'),
      ('2-apres ', 'la 1ere de la liste envoyee  ',
       coalesce(v_charge->'liste_photos'->>0, '(vide)'));
    -- RE-ESSAI : elle est deja en couverture, aucun nouveau travail ne doit naitre
    declare r2 jsonb; v_n integer;
    begin
      select count(*) into v_n from app_console_job where job_type='reorder_hektor_photos';
      r2 := public.app_console_photo_couverture_optimistic(3828957, '62774', '487604');
      insert into essai_mesures (etape, mesure, valeur) values
        ('2-apres ', 'RE-ESSAI (deja en couverture)',
         case when coalesce((r2->>'deja_en_couverture')::boolean, false)
                   and (select count(*) from app_console_job where job_type='reorder_hektor_photos') = v_n
              then 'ok, et AUCUN nouveau travail' else 'PROBLEME : ' || r2::text end);
    end;
  end if;
end $essai$;

-- =============================== 4. L'INVERSE ==============================
do $inv$
declare v_def text; v_neuf text;
begin
  select pg_get_constraintdef(c.oid) into v_def from pg_constraint c
   where c.conrelid='public.app_console_job'::regclass and c.conname='app_console_job_job_type_check';
  if position('reorder_hektor_photos' in v_def) > 0 then
    v_neuf := replace(v_def, ', ''reorder_hektor_photos''::text', '');
    execute 'ALTER TABLE public.app_console_job DROP CONSTRAINT app_console_job_job_type_check';
    execute 'ALTER TABLE public.app_console_job ADD CONSTRAINT app_console_job_job_type_check ' || v_neuf || ' NOT VALID';
  end if;

  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_def from pg_proc p
    join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname='app_console_can_request_job';
  if position('reorder_hektor_photos' in v_def) > 0 then
    execute replace(v_def, '''reorder_hektor_photos'',', ''); end if;

  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_def from pg_proc p
    join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname='app_console_claim_next_job';
  if position('reorder_hektor_photos' in v_def) > 0 then
    execute replace(v_def, ',''reorder_hektor_photos''', ''); end if;

  execute 'DROP FUNCTION IF EXISTS public.app_console_photo_couverture_optimistic(bigint, text, text)';
  raise notice 'INVERSE JOUE';
end $inv$;

-- =============================== 5. LE RETOUR ==============================
insert into essai_mesures (etape, mesure, valeur)
select '3-retour', 'le type a disparu des 3      ',
       case when (select pg_get_constraintdef(c.oid) from pg_constraint c
                   where c.conrelid='public.app_console_job'::regclass
                     and c.conname='app_console_job_job_type_check') like '%reorder_hektor_photos%'
              or (select replace(pg_get_functiondef(p.oid), chr(13),'') from pg_proc p
                    join pg_namespace n on n.oid=p.pronamespace
                   where n.nspname='public' and p.proname='app_console_can_request_job') like '%reorder_hektor_photos%'
              or (select replace(pg_get_functiondef(p.oid), chr(13),'') from pg_proc p
                    join pg_namespace n on n.oid=p.pronamespace
                   where n.nspname='public' and p.proname='app_console_claim_next_job') like '%reorder_hektor_photos%'
            then 'NON -- PROBLEME' else 'oui' end;

insert into essai_mesures (etape, mesure, valeur)
values ('3-retour', 'la RPC a disparu             ',
        case when exists (select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
                           where n.nspname='public' and p.proname='app_console_photo_couverture_optimistic')
             then 'NON -- PROBLEME' else 'oui' end);

-- ⚠⚠ CORRIGE LE 16/10 APRES LE PREMIER PASSAGE DE FREDERIC, qui a rendu
--    « empreintes d'origine = 2 sur 3 ».
--    HYPOTHESE A VERIFIER ICI MEME : `pg_get_constraintdef` AJOUTE le suffixe
--    « NOT VALID » au texte quand la contrainte n'est pas validee. Or l'inverse
--    la repose NOT VALID et ne peut PAS lancer VALIDATE dans une transaction
--    annulee -- donc son texte differe de l'original d'exactement ce suffixe,
--    et l'empreinte avec. Ce serait un defaut de MA MESURE, pas du patch :
--    le vrai patch ET le vrai inverse lancent tous deux VALIDATE a la fin.
--    ➡ On mesure donc la contrainte SANS ce suffixe, et on DIT ce qu'on a trouve.
-- ⚠⚠ TROIS LIGNES EXPLICITES, PAS UN COMPTEUR. Le premier passage (16/10) a
--    rendu « empreintes d'origine = 2 sur 3 » : juste, mais muet -- il ne disait
--    pas LAQUELLE, et il a fallu un aller-retour pour le savoir.
--
--    ET LA CONTRAINTE A UNE RAISON LEGITIME DE DIFFERER ICI : l'inverse la repose
--    `NOT VALID`, et `pg_get_constraintdef` AJOUTE ce suffixe au texte. Il ne peut
--    pas en etre autrement dans une repetition : `VALIDATE CONSTRAINT` ne se lance
--    pas dans une transaction annulee. Le vrai patch ET le vrai inverse, eux, le
--    lancent tous les deux a la fin -- donc en production la contrainte revient
--    propre. On mesure donc le texte NU, suffixe retire, et on DIT ce qu'on voit.
insert into essai_mesures (etape, mesure, valeur)
select '3-retour', 'contrainte (texte nu)        ',
       case when md5(btrim(replace(q.t, 'NOT VALID', ''))) = 'beacc240a7974dec70a876b717ed052b'
            then 'IDENTIQUE' else 'DIFFERENTE : ' || md5(btrim(replace(q.t, 'NOT VALID', ''))) end
       || case when q.t like '%NOT VALID' then ' (suffixe NOT VALID present -- normal en repetition)' else '' end
from (select pg_get_constraintdef(c.oid) as t from pg_constraint c
       where c.conrelid='public.app_console_job'::regclass
         and c.conname='app_console_job_job_type_check') q;

insert into essai_mesures (etape, mesure, valeur)
select '3-retour', 'droits (empreinte)           ',
       case when md5(replace(pg_get_functiondef(p.oid), chr(13),'')) = 'd013972f13ce6f881aa0494c4529e3ae'
            then 'IDENTIQUE' else 'DIFFERENTE : ' || md5(replace(pg_get_functiondef(p.oid), chr(13),'')) end
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname='public' and p.proname='app_console_can_request_job';

insert into essai_mesures (etape, mesure, valeur)
select '3-retour', 'distribution (empreinte)     ',
       case when md5(replace(pg_get_functiondef(p.oid), chr(13),'')) = '4da660742838e4e0849bbd70b7b9a7f5'
            then 'IDENTIQUE' else 'DIFFERENTE : ' || md5(replace(pg_get_functiondef(p.oid), chr(13),'')) end
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname='public' and p.proname='app_console_claim_next_job';

-- ========================= 6. L'ERREUR VOLONTAIRE ==========================
do $fin$
declare v_txt text;
begin
  select string_agg(etape || ' | ' || mesure || ' = ' || valeur, chr(10) order by id) into v_txt from essai_mesures;
  raise exception 'ESSAI ANNULE -- rien n''a ete ecrit. %', chr(10) || v_txt;
end $fin$;

rollback;
