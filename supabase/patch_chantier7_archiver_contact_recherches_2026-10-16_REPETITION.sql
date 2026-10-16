-- ============================================================================
-- REPETITION -- archiver un contact archive aussi ses recherches (chantier ⑦-1 bis)
-- 16/10/2026
-- ============================================================================
-- ⚠⚠ A COLLER EN UNE SEULE FOIS, EN ENTIER. Le `begin;` de la premiere ligne et
--    l'ERREUR VOLONTAIRE de la derniere font que RIEN n'est ecrit.
--
-- Elle joue, dans l'ordre reel : mesure AVANT -> LE VRAI PATCH -> mesures APRES
-- (dont un ESSAI DE COMPORTEMENT sur un vrai contact, annule par point de reprise)
-- -> LE VRAI INVERSE -> mesure du RETOUR -> erreur volontaire qui annule tout.
--
-- LE MESSAGE ATTENDU si tout va bien :
--    1-avant  | le bloc est dans la fonction   = non
--    1-avant  | empreinte de la fonction       = 85e3c91dc701b4a60d9e2fb07d805e4d
--    1-avant  | contacts actifs a recherche    = <un nombre, ~3 961>
--    2-apres  | le bloc est dans la fonction   = oui
--    2-apres  | la fonction compile            = oui (elle a ete reexecutee)
--    2-apres  | essai sur un vrai contact      = joue : N recherche(s) archivee(s),
--                                                N verrou(s) poses  (ou « non joue :
--                                                droits refuses dans l'editeur »)
--    3-retour | le bloc est dans la fonction   = non
--    3-retour | trace app_search_pending       = non
--    3-retour | empreinte de la fonction       = IDENTIQUE
--
-- ⚠ Si « essai sur un vrai contact » dit « non joue », ce n'est PAS un echec : la
--   fonction verifie les droits avec l'identite de l'appelant, et l'editeur SQL n'en
--   a pas. Les controles de structure, eux, font foi.
-- ============================================================================

begin;

create temporary table essai_mesures (
  id serial, etape text, mesure text, valeur text
) on commit drop;

-- =============================== 1. AVANT ==================================
insert into essai_mesures (etape, mesure, valeur)
select '1-avant ', 'le bloc est dans la fonction  ',
       case when replace(pg_get_functiondef(p.oid), chr(13), '') like '%BLOC RECHERCHES ARCHIVEES%' then 'oui' else 'non' end
from pg_proc p join pg_namespace n on n.oid = p.pronamespace
where n.nspname='public' and p.proname='app_console_archiver_contact_optimistic';

insert into essai_mesures (etape, mesure, valeur)
select '1-avant ', 'empreinte de la fonction      ', md5(replace(pg_get_functiondef(p.oid), chr(13), ''))
from pg_proc p join pg_namespace n on n.oid = p.pronamespace
where n.nspname='public' and p.proname='app_console_archiver_contact_optimistic';

insert into essai_mesures (etape, mesure, valeur)
select '1-avant ', 'contacts actifs a recherche   ', count(*)::text
from app_contact_current where not archive and coalesce(active_search_count, 0) > 0;

-- =============================== 2. LE PATCH ===============================
do $do$
declare
  v_src   text;
  v_new   text;
  v_ancre text := replace('  returning * into created_job;', chr(13), '');
  v_ajout text;
  v_vu    integer;
begin
  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_src
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public' and p.proname = 'app_console_archiver_contact_optimistic';
  if v_src is null then raise exception 'STOP : fonction introuvable'; end if;
  if position('BLOC RECHERCHES ARCHIVEES' in v_src) > 0 then
    raise notice 'DEJA FAIT'; return;
  end if;
  v_vu := (length(v_src) - length(replace(v_src, v_ancre, ''))) / length(v_ancre);
  if v_vu <> 1 then raise exception 'STOP : ancre vue % fois', v_vu; end if;

  v_ajout := replace(v_ancre || '
' || '
  -- BLOC RECHERCHES ARCHIVEES -- DEBUT
  -- ⑦-1 bis (16/10) : ET SES RECHERCHES ACTIVES, DANS LA MEME TRANSACTION.
  -- Hektor les archive quand on archive la fiche (mesure du 16/10) : on le dit tout
  -- de suite chez nous, au lieu d''attendre ~30 s que sa reponse revienne.
  -- Patron de C.4 (30/08), deja en production pour le geste par recherche :
  --   l''etat d''avant part dans app_search_pending.base_snapshot, et le verrou
  --   porte le numero du travail (efface au succes, rearme a l''echec).
  -- ⚠ Les deux CTE voient le MEME instantane : `avant` lit bien l''etat d''AVANT
  --   meme si `maj` ecrit dans la meme instruction.
  -- ⚠ Au desarchivage on ne touche a rien : Hektor ne les rend pas.
  if p_archive then
    with avant as (
      select s.search_index, s.archive, s.is_active, s.criteres_json, s.prix_max
        from public.app_contact_search_current s
       where s.hektor_contact_id = clean_id
         and coalesce(s.archive, false) is not true
    ), maj as (
      update public.app_contact_search_current s
         set archive = true, is_active = false, refreshed_at = now()
       where s.hektor_contact_id = clean_id
         and coalesce(s.archive, false) is not true
      returning s.search_index
    )
    insert into public.app_search_pending (hektor_contact_id, search_index, base_snapshot,
                                           push_search, push_after, source, dirty_by, push_job_id)
    select clean_id, a.search_index,
           jsonb_build_object(''archive'', a.archive, ''is_active'', a.is_active,
                              ''criteres_json'', a.criteres_json, ''prix_max'', a.prix_max),
           null, now(), ''nego_app'', auth.uid()::text, created_job.id
      from avant a
    on conflict on constraint app_search_pending_pkey do update
      set push_job_id = excluded.push_job_id,
          conflict    = false,
          updated_at  = now();
  end if;
  -- BLOC RECHERCHES ARCHIVEES -- FIN', chr(13), '');

  v_new := replace(v_src, v_ancre, v_ajout);
  execute v_new;
  raise notice 'PATCH POSE';
end
$do$;

-- =============================== 3. APRES ==================================
insert into essai_mesures (etape, mesure, valeur)
select '2-apres ', 'le bloc est dans la fonction  ',
       case when replace(pg_get_functiondef(p.oid), chr(13), '') like '%BLOC RECHERCHES ARCHIVEES%' then 'oui' else 'NON -- PROBLEME' end
from pg_proc p join pg_namespace n on n.oid = p.pronamespace
where n.nspname='public' and p.proname='app_console_archiver_contact_optimistic';

insert into essai_mesures (etape, mesure, valeur)
values ('2-apres ', 'la fonction compile           ', 'oui (elle a ete reexecutee sans erreur)');

-- ⚠ L'ESSAI DE COMPORTEMENT, sur un VRAI contact, annule par point de reprise.
--   Le temoin ne depend pas de ce que l'epreuve annule : il passe par des VARIABLES,
--   ecrites APRES le bloc (lecon du 13/10).
do $do$
declare
  v_cible     text;
  v_avant     integer;
  v_apres     integer;
  v_verrous   integer;
  v_resultat  text := 'non teste';
begin
  select c.hektor_contact_id into v_cible
  from app_contact_current c
  where not c.archive and coalesce(c.active_search_count, 0) > 0
    and c.hektor_contact_id <> '10059959'      -- on ne touche pas a Gladys
  order by c.hektor_contact_id
  limit 1;

  if v_cible is null then
    v_resultat := 'aucun contact candidat';
  else
    begin
      select count(*) into v_avant from app_contact_search_current
       where hektor_contact_id = v_cible and coalesce(archive, false) is not true;

      perform public.app_console_archiver_contact_optimistic(v_cible, true);

      select count(*) into v_apres from app_contact_search_current
       where hektor_contact_id = v_cible and coalesce(archive, false) is not true;
      select count(*) into v_verrous from app_search_pending
       where hektor_contact_id = v_cible and push_job_id is not null;

      v_resultat := format('joue sur %s : %s active(s) avant, %s apres, %s verrou(s)',
                           v_cible, v_avant, v_apres, v_verrous);
      raise exception 'ANNULATION_INTERNE';
    exception when others then
      if sqlerrm <> 'ANNULATION_INTERNE' then
        v_resultat := format('non joue (%s) -- normal si c''est un refus de droits dans l''editeur', left(sqlerrm, 60));
      end if;
    end;
  end if;

  insert into essai_mesures (etape, mesure, valeur)
  values ('2-apres ', 'essai sur un vrai contact     ', v_resultat);
end
$do$;

-- =============================== 4. L'INVERSE ==============================
do $do$
declare
  v_src text; v_new text; v_debut integer; v_fin integer;
  v_borne_d text := replace('  -- BLOC RECHERCHES ARCHIVEES -- DEBUT', chr(13), '');
  v_borne_f text := replace('  -- BLOC RECHERCHES ARCHIVEES -- FIN', chr(13), '');
begin
  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_src
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public' and p.proname = 'app_console_archiver_contact_optimistic';
  if position('BLOC RECHERCHES ARCHIVEES' in v_src) = 0 then
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
select '3-retour', 'le bloc est dans la fonction  ',
       case when replace(pg_get_functiondef(p.oid), chr(13), '') like '%BLOC RECHERCHES ARCHIVEES%' then 'OUI -- PROBLEME' else 'non' end
from pg_proc p join pg_namespace n on n.oid = p.pronamespace
where n.nspname='public' and p.proname='app_console_archiver_contact_optimistic';

insert into essai_mesures (etape, mesure, valeur)
select '3-retour', 'trace app_search_pending      ',
       case when replace(pg_get_functiondef(p.oid), chr(13), '') like '%app_search_pending%' then 'OUI -- PROBLEME' else 'non' end
from pg_proc p join pg_namespace n on n.oid = p.pronamespace
where n.nspname='public' and p.proname='app_console_archiver_contact_optimistic';

insert into essai_mesures (etape, mesure, valeur)
select '3-retour', 'empreinte de la fonction      ',
       case when md5(replace(pg_get_functiondef(p.oid), chr(13), '')) = '85e3c91dc701b4a60d9e2fb07d805e4d'
            then 'IDENTIQUE' else 'DIFFERENTE : ' || md5(replace(pg_get_functiondef(p.oid), chr(13), '')) end
from pg_proc p join pg_namespace n on n.oid = p.pronamespace
where n.nspname='public' and p.proname='app_console_archiver_contact_optimistic';

-- ========================= 6. L'ERREUR VOLONTAIRE ==========================
do $do$
declare v_txt text;
begin
  select string_agg(etape || ' | ' || mesure || ' = ' || valeur, chr(10) order by id)
    into v_txt from essai_mesures;
  raise exception 'ESSAI ANNULE -- rien n''a ete ecrit. %', chr(10) || v_txt;
end
$do$;

rollback;
