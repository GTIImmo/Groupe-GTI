-- ═══════════════════════════════════════════════════════════════════════════════
-- CHANTIER GED — LE RECOURS : « C'EST BIEN CE TYPE : GARDER LA LECTURE »          18/11/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- Note du chantier : notice/CHANTIER_GED_DOCUMENTS_2026-11-06.md §12.33 (couche B), §12.36. « Vas y » de Frédéric (18/11).
--
-- ─── POURQUOI ───
--   L'étape 2 (la lecture par l'IA) peut juger « pas_ce_type » un document qui EST du type classé (prouvé au banc,
--   §12.34 ; la cause est corrigée au serveur depuis le 18/11, 9d5a6fd). Ce patch est le FILET : un humain qui sait que
--   le type est juste garde la lecture, sans nouvel appel payé. Le verdict de l'IA n'est jamais perdu : il est écrit
--   AVANT / APRÈS au journal de la GED.
--
-- ─── CE QUE CE PATCH POSE ───
--   ① app_ged_journal     son CHECK `objet` accepte « lecture » (en plus de classement et rattachement).
--   ② app_ged_lecture_garder(lecture)   la seule porte : compte actif, interrupteur ged_lecture_ia ouvert POUR
--                        L'APPELANT (le même que la lecture), bien dans son périmètre, lecture « pas_ce_type », type NON
--                        sensible. Elle passe la lecture à « lu » (« incomplet » si aucune valeur n'a été vue) et écrit
--                        le journal (objet « lecture », geste « garder_type ») ; l'auteur est auth.uid().
--
-- ─── CE QUE CE PATCH NE FAIT PAS ───
-- ⛔ Rien sur la fiche, rien chez Hektor, aucune valeur touchée : les valeurs lues sont DÉJÀ en base (app_ged_valeur).
-- ⛔ Pas pour les types SENSIBLES (pièces des personnes) : leur registre privé ne se remplit que par une lecture jugée
--   juste par l'IA, et leurs valeurs privées ont été jetées au refus.
--
-- ─── CE QUE ÇA POURRAIT TOUCHER AILLEURS ───
--   · Les lecteurs de l'écran ne prennent que etat = 'lu' (gedBilanFiche, gedBilanCompromis, gedRemplir, gedReglesLues,
--     dateEtatLue) : une lecture gardée y entre, comme voulu -- les cartes « Ce que dit… » apparaissent. Aucun lecteur
--     ne change.
--   · app_ged_journal n'est lu par aucun écran ni script (mesuré le 18/11) : seul son CHECK s'élargit.
--
-- ─── RETOUR ARRIÈRE ───
-- supabase/patch_ged_garder_lecture_2026-11-18_INVERSE.sql. Répétition sans rien garder :
-- supabase/patch_ged_garder_lecture_2026-11-18_REPETITION.sql.
-- ═══════════════════════════════════════════════════════════════════════════════

begin;
set local lock_timeout = '3s';

do $garde$
begin
  if to_regclass('public.app_ged_lecture') is null or to_regclass('public.app_ged_journal') is null then
    raise exception 'ARRET : morceau 6 ou journal GED absent';
  end if;
  if exists (select 1 from pg_proc where proname = 'app_ged_lecture_garder' and pronamespace = 'public'::regnamespace) then
    raise exception 'ARRET : app_ged_lecture_garder existe deja -- patch deja applique ?';
  end if;
  if (select pg_get_constraintdef(oid) from pg_constraint where conrelid = 'public.app_ged_journal'::regclass and conname = 'app_ged_journal_objet')
     is distinct from 'CHECK ((objet = ANY (ARRAY[''classement''::text, ''rattachement''::text])))' then
    raise exception 'ARRET : le CHECK app_ged_journal_objet a change depuis la mesure du 18/11';
  end if;
  if not exists (select 1 from public.app_setting where key = 'ged_lecture_ia') then raise exception 'ARRET : ged_lecture_ia absent'; end if;
end
$garde$;

-- ─────────────────────────────────────────────────────── ① LE JOURNAL ACCEPTE « lecture »
alter table public.app_ged_journal drop constraint app_ged_journal_objet;
alter table public.app_ged_journal add constraint app_ged_journal_objet
  check (objet = any (array['classement'::text, 'rattachement'::text, 'lecture'::text]));

-- ─────────────────────────────────────────────────────── ② LA PORTE
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
  -- GED 18/11/2026 : un humain GARDE une lecture que l'IA a jugée « pas_ce_type ». Écrit app_ged_lecture.etat et le
  -- journal, rien d'autre.
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

comment on function public.app_ged_lecture_garder(uuid) is
  'GED 18/11/2026 : garde une lecture jugée « pas_ce_type » par l''IA (-> lu, ou incomplet sans valeur). Interrupteur '
  'ged_lecture_ia, périmètre du bien, types sensibles refusés. Journal app_ged_journal (objet lecture, geste garder_type).';

-- ─────────────────────────────────────────────────────── ③ LES DROITS
revoke all on function public.app_ged_lecture_garder(uuid) from public, anon, authenticated;
grant execute on function public.app_ged_lecture_garder(uuid) to authenticated;

commit;

-- ═══════════════════════════════════════════════════════════════════════════════
-- LES CONTRÔLES — à lire après le COMMIT. Tout doit être VERT.
-- ═══════════════════════════════════════════════════════════════════════════════
select '① le journal accepte « lecture »' as controle, count(*) as trouve,
       case when count(*) = 1 then 'VERT' else 'ROUGE' end as verdict
  from pg_constraint where conrelid = 'public.app_ged_journal'::regclass and conname = 'app_ged_journal_objet'
   and pg_get_constraintdef(oid) like '%lecture%'
union all
select '② la porte : SECURITY DEFINER, fermée à anon, ouverte à authenticated', count(*),
       case when count(*) = 1 then 'VERT' else 'ROUGE' end
  from pg_proc p where p.proname = 'app_ged_lecture_garder' and p.prosecdef
   and not has_function_privilege('anon', p.oid, 'execute') and has_function_privilege('authenticated', p.oid, 'execute')
union all
select '③ ged_lecture_ia inchangé (toujours « admin »)', count(*),
       case when count(*) = 1 then 'VERT' else 'ROUGE' end
  from public.app_setting where key = 'ged_lecture_ia' and value = 'admin'
union all
select '④ aucune lecture n''a bougé (le patch n''écrit rien)', count(*),
       case when count(*) = 0 then 'VERT' else 'ROUGE' end
  from public.app_ged_journal where objet = 'lecture';
