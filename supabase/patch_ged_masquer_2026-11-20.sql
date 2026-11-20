-- ═══════════════════════════════════════════════════════════════════════════════
-- CHANTIER GED — VISUEL V3, MORCEAU 1 : « MASQUER » UN POINT D'ATTENTION            20/11/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- Notes : notice/AUDIT_GRAPHIQUE_GED_2026-11-18.md §8-9 ; notice/CHANTIER_GED_DOCUMENTS_2026-11-06.md §12.59.
-- Décisions de Frédéric (20/11) : la période de test est retirée (« Vrai / Faux / Déjà su » disparaît), un point
-- d'attention s'écarte par « Masquer » (réversible par « Réafficher »), et le masquage vaut POUR TOUT LE MONDE sur le bien.
-- « Oui, vas-y » (20/11) pour ce morceau.
--
-- ─── CE QUE CE PATCH CHANGE ───
--   ① app_ged_jugement   son CHECK `verdict` accepte deux mots de plus : « masque » et « reaffiche ».
--   ② app_ged_juger()    sa garde du verdict accepte les mêmes ; RIEN d'autre ne bouge dans la fonction (mêmes
--                        portes : compte actif, interrupteur ged_propositions, périmètre du bien ; auteur = auth.uid()).
--   La règle de lecture ne change pas : le jugement le PLUS RÉCENT d'une ligne fait foi. L'écran (morceau 4) lira :
--   « reaffiche » -> visible ; tout autre dernier mot (vrai, faux, deja_su, masque) -> masqué.
--
-- ─── CE QUE CE PATCH NE FAIT PAS ───
-- ⛔ Aucune ligne existante n'est touchée (8 jugements au 20/11 : 7 vrai, 1 faux, 2 biens). Rien sur la fiche, rien chez
--   Hektor. Pas d'interrupteur neuf. L'écran d'aujourd'hui n'écrit jamais ces deux mots : tant que le morceau 4 n'est pas
--   en ligne, ce patch ne change RIEN à ce que voit un utilisateur.
--
-- ─── CE QUE ÇA POURRAIT TOUCHER AILLEURS ───
--   · loadGedJugements (lib/ged.ts) lit `verdict` sans le filtrer : l'écran d'aujourd'hui afficherait « Jugé masque » si
--     une telle ligne existait -- elle ne peut naître que par l'écran du morceau 4 (ou un appel à la main).
--   · supabase/requete_mesure_ged_m10_2026-11-16.sql compte les verdicts : « masque » et « reaffiche » y apparaîtraient
--     comme des verdicts de plus (c'est une mesure, pas une règle).
--   · La descente de 07:45 recopie la table telle quelle (texte libre, pas de contrainte côté local).
--
-- ─── RETOUR ARRIÈRE ───
-- supabase/patch_ged_masquer_2026-11-20_INVERSE.sql (il REFUSE s'il existe déjà des « masque » / « reaffiche » : le
-- journal ne s'efface pas). Répétition sans rien garder : supabase/patch_ged_masquer_2026-11-20_REPETITION.sql.
-- ═══════════════════════════════════════════════════════════════════════════════

begin;
set local lock_timeout = '3s';

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

commit;

-- ═══════════════════════════════════════════════════════════════════════════════
-- LES CONTRÔLES — à lire après le COMMIT. Tout doit être VERT.
-- ═══════════════════════════════════════════════════════════════════════════════
select '① le CHECK accepte masque et reaffiche' as controle, count(*) as trouve,
       case when count(*) = 1 then 'VERT' else 'ROUGE' end as verdict
  from pg_constraint where conname = 'app_ged_jugement_verdict'
   and pg_get_constraintdef(oid) like '%masque%' and pg_get_constraintdef(oid) like '%reaffiche%'
union all
select '② la porte accepte masque et reaffiche', count(*),
       case when count(*) = 1 then 'VERT' else 'ROUGE' end
  from pg_proc where oid = 'public.app_ged_juger(text, text, text, text, text, text, text)'::regprocedure
   and prosrc like '%''masque'', ''reaffiche''%'
union all
select '③ la porte : SECURITY DEFINER, fermée à anon, ouverte à authenticated', count(*),
       case when count(*) = 1 then 'VERT' else 'ROUGE' end
  from pg_proc p where p.oid = 'public.app_ged_juger(text, text, text, text, text, text, text)'::regprocedure
   and p.prosecdef and not has_function_privilege('anon', p.oid, 'execute')
   and has_function_privilege('authenticated', p.oid, 'execute')
union all
select '④ les jugements d''avant sont intacts (8 au 20/11, aucun masque / reaffiche)', count(*),
       case when count(*) >= 8 and count(*) filter (where verdict in ('masque', 'reaffiche')) = 0 then 'VERT' else 'ROUGE' end
  from public.app_ged_jugement
union all
select '⑤ ged_propositions inchangé (toujours « admin »)', count(*),
       case when count(*) = 1 then 'VERT' else 'ROUGE' end
  from public.app_setting where key = 'ged_propositions' and value = 'admin';
