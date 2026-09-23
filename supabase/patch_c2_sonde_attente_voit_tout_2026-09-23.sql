-- ═══════════════════════════════════════════════════════════════════════════
-- C-2  23/09/2026 — LA SONDE D'ATTENTE VOIT CE QU'ELLE NE VOYAIT PAS
-- ═══════════════════════════════════════════════════════════════════════════
--
-- CE QU'ELLE FAISAIT : un JOIN sur app_contact_current. Elle ne montrait donc
-- que les saisies dont le contact EXISTE dans l'index, et qui attendent leur
-- numero Hektor. C'est l'attente NORMALE -- celle qui se resout toute seule.
--
-- CE QU'ELLE NE VOYAIT PAS : la fonction app_contact_enqueue_due_pushes fait
-- `continue` quand le contact est ABSENT de l'index (patch_5b:65, :150). La
-- saisie reste alors dans la bannette pour toujours, sans travail, sans erreur,
-- sans alerte. La sonde etait aveugle EXACTEMENT au cas qu'elle devait voir.
--
-- ET CE N'EST PAS THEORIQUE : app_contact_current ne porte que le PERIMETRE
-- ELIGIBLE (61 984 contacts au 23/09, pas les 356 000 de l'app), et ce
-- perimetre RETRECIT chaque nuit (elargir_perimetre_console.py). Un contact qui
-- en sort pendant que sa saisie attend voit cette saisie abandonnee en silence.
-- C'est le contraire de la regle C.1' : « une saisie ne se perd jamais ».
--
-- CE QUI CHANGE : rien au comportement. La sonde montre desormais les DEUX cas
-- et les NOMME.
--
--    en_attente_du_numero        normal, se resout seul quand Hektor repond
--    contact_absent_de_l_index   ANORMAL, la saisie se perd, il faut un humain
--
-- LA JOINTURE ACCEPTE LES DEUX NUMEROS (identite ou cible). Aujourd'hui ils
-- sont egaux, cela ne change rien ; le jour de la bascule, une ligne de
-- bannette posee juste avant se retrouve quand meme.
--
-- ⚠ CREATE OR REPLACE, colonne ajoutee EN FIN de liste : les GRANT sont
--   conserves. On ne DROP pas -- un DROP effacerait les droits, et ils ne sont
--   pas uniformes sur ce projet.
--
-- LE SEUL LECTEUR : monitoring/check_gti_health.py:426, qui compte les lignes
-- (seuil 0, severite warning). Il continue de fonctionner a l'identique ; il
-- verra simplement des lignes qu'il ne voyait pas.
--
-- RETOUR ARRIERE : rejouer la definition d'avant, conservee dans
--   supabase/patch_5b_barriere_attente_2026-09-21.sql:190-198
-- ═══════════════════════════════════════════════════════════════════════════

create or replace view public.app_v_envois_en_attente_hektor as
  select 'recherche'::text                as objet,
         p.hektor_contact_id,
         p.search_index::text             as detail,
         p.dirty_at,
         case when c.hektor_contact_id is null
              then 'contact_absent_de_l_index'
              else 'en_attente_du_numero' end as cause
    from public.app_search_pending p
    left join lateral (
           select x.hektor_contact_id, x.hektor_target_id
             from public.app_contact_current x
            where x.hektor_contact_id = p.hektor_contact_id
               or x.hektor_target_id  = p.hektor_contact_id
            limit 1) c on true
   where p.push_search is not null
     and (c.hektor_contact_id is null or coalesce(c.hektor_target_id, '') = '')

  union all

  select 'contact'::text                  as objet,
         p.hektor_contact_id,
         null::text                       as detail,
         p.dirty_at,
         case when c.hektor_contact_id is null
              then 'contact_absent_de_l_index'
              else 'en_attente_du_numero' end as cause
    from public.app_contact_pending p
    left join lateral (
           select x.hektor_contact_id, x.hektor_target_id
             from public.app_contact_current x
            where x.hektor_contact_id = p.hektor_contact_id
               or x.hektor_target_id  = p.hektor_contact_id
            limit 1) c on true
   where c.hektor_contact_id is null or coalesce(c.hektor_target_id, '') = '';

comment on view public.app_v_envois_en_attente_hektor is
  'C-2 23/09/2026 : les saisies qui attendent de partir chez Hektor, avec LA CAUSE. en_attente_du_numero = normal, se resout seul. contact_absent_de_l_index = ANORMAL, la fonction d''enfilement saute cette ligne en silence et la saisie se perd. La version du 21/09 faisait un JOIN et ne montrait que le premier cas -- elle etait aveugle au second, qui est justement celui qui demande un geste humain.';
