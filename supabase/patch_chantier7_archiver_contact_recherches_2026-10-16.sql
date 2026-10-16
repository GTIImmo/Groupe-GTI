-- ============================================================================
-- CHANTIER ⑦-1 bis -- ARCHIVER UN CONTACT ARCHIVE AUSSI SES RECHERCHES, CHEZ NOUS
-- 16/10/2026
-- ============================================================================
-- POURQUOI, et c'est Frederic qui l'a redresse : « nous sommes en plein dev
-- d'autonomie, donc il faut faire d'abord le geste CHEZ NOUS puis attendre une
-- confirmation, comme les autres gestes ». J'avais propose l'inverse (« laissons
-- Hektor le faire, sa reponse nous reviendra ») -- c'etait contre la direction du
-- projet.
--
-- CE QU'ON A MESURE EN REEL LE 16/10, sur un vrai client (Gladys DURIEUX) :
--   07:30:08  relecture chez Hektor REUSSIE          -> sa recherche n°1 ACTIVE
--   07:56:26  on ARCHIVE la fiche                    -> Hektor : « ok »
--   08:14:39  relecture chez Hektor REUSSIE          -> sa recherche n°1 ARCHIVEE
-- et reactiver la fiche ne l'a PAS rendue : il a fallu la desarchiver a la main
-- dans Hektor (menu « ... » de la recherche). Consequences : 0 recherche active,
-- 0 rapprochement (elle en avait 2, dont un a 100/100).
-- ➡ HEKTOR ARCHIVE LES RECHERCHES QUAND ON ARCHIVE LA FICHE. Notre copie doit le
--   dire TOUT DE SUITE, sinon pendant ~30 secondes l'app propose encore des biens
--   a quelqu'un qu'on vient d'archiver.
--
-- LE PATRON N'EST PAS INVENTE : c'est celui de C.4 (30/08), deja en production dans
-- `app_console_create_delete_contact_search_job` -- ecrire chez nous dans la MEME
-- transaction, garder l'ETAT D'AVANT, et poser un VERROU qui porte le numero du
-- travail (le balayage l'efface au succes, le rearme a l'echec).
--
-- ⭐ ET ICI, AUCUN PROBLEME D'IDENTIFICATION. Le geste par recherche doit designer
--   UNE ligne (idCritere), et ce reperage est casse -- 992 contacts ont 2 recherches
--   ou plus. Nous, on prend TOUTES les recherches actives du contact : aucun index a
--   deviner, aucune « premiere ligne » prise par defaut.
--
-- ⚠ AU DESARCHIVAGE, ON NE TOUCHE A RIEN : Hektor ne rend pas les recherches
--   (mesure du 16/10). Les ecrire actives serait un mensonge d'ecran. Les etats
--   d'avant restent dans app_search_pending pour une reparation a la main.
--
-- CE PATCH NE RECOPIE PAS LA FONCTION : il la LIT dans la base, verifie son
-- empreinte et que son ancre est unique, insere APRES l'ancre et reexecute.
-- Ancres multi-lignes : ZERO.
-- ============================================================================

begin;

set local lock_timeout = '5s';

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

  if v_src is null then
    raise exception 'STOP : app_console_archiver_contact_optimistic introuvable';
  end if;

  if position('BLOC RECHERCHES ARCHIVEES' in v_src) > 0 then
    raise notice 'DEJA FAIT : la fonction archive deja les recherches';
    return;
  end if;

  -- Empreinte attendue (sans retours chariot) : celle du 16/10 apres nettoyage.
  if md5(v_src) <> '85e3c91dc701b4a60d9e2fb07d805e4d' then
    raise notice 'ATTENTION : empreinte % (attendue 85e3c91d...) -- un autre patch est passe. On continue : l''ancre et l''absence du texte sont les vrais garde-fous.', md5(v_src);
  end if;

  v_vu := (length(v_src) - length(replace(v_src, v_ancre, ''))) / length(v_ancre);
  if v_vu <> 1 then
    raise exception 'STOP : l''ancre apparait % fois (attendu 1)', v_vu;
  end if;

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
  raise notice 'POSE : la fonction archive desormais les recherches actives du contact';
end
$do$;

commit;
