-- =====================================================================
-- RETOUR ARRIERE du critere de coherence de la vitrine -- 04/11/2026
-- =====================================================================
-- CE QU'IL DEFAIT, ET RIEN D'AUTRE (regle du projet : un retour arriere
-- ne juge que SA part) : il remet app_photos_remplir_adresses_app dans
-- l'etat d'avant le 04/11, lu DEPUIS LA SAUVEGARDE EN BASE -- pas depuis
-- une recopie a la main.
--
-- ⚠ CE QU'IL NE DEFAIT PAS, ET C'EST VOULU :
--   . les vitrines de 63184 et 63073 restent REPAREES. Ce sont des
--     donnees justes : 63184 ne publie plus ses 12 photos masquees,
--     63073 montre ses 10 photos. Defaire le correctif ne doit pas
--     remettre des masquees sur le site.
--   . les 38 235 couvertures reecrites par ma 1re version gardent leur
--     adresses_app_le du 04/11. La valeur publiee est inchangee (meme
--     filtre tmp_principale), seule la date a bouge.
--   . le catalogue vitrine deja exporte n'est pas touche : le run le
--     refait chaque matin.
--
-- ⛔ APRES CE RETOUR ARRIERE, LE DEFAUT REVIENT : masquer ou demasquer
--   une photo d'une annonce aux derives anciens ne refera plus sa
--   vitrine. Le controle du matin le verra
--   (phase2/checks/controle_balayage_photos_masquees.py, point ⑦).
-- =====================================================================

do $$
declare
  src text; vue text;
begin
  -- 1. La sauvegarde existe-t-elle ?
  select definition into src from public.app_sauvegarde_fonction_20261104
   where nom = 'app_photos_remplir_adresses_app';
  if src is null then
    raise exception 'ARRET : aucune sauvegarde de app_photos_remplir_adresses_app dans app_sauvegarde_fonction_20261104';
  end if;

  -- 2. Est-ce bien la version d'avant ? (empreinte mesuree le 04/11)
  if md5(src) <> 'ec8066616381cdb90df38ec561f1441f' then
    raise exception 'ARRET : la sauvegarde ne porte pas l empreinte attendue (md5 %)', md5(src);
  end if;

  -- 3. La fonction en place est-elle bien MA version ? Si quelqu un est
  --    passe apres moi, on s arrete : on ne pietine pas son travail.
  select md5(pg_get_functiondef(p.oid)) into vue
    from pg_proc p join pg_namespace n on n.oid = p.pronamespace
   where p.proname = 'app_photos_remplir_adresses_app' and n.nspname = 'public';
  if vue <> 'cebcfc90fa80763492e2d9f71b298dca' then
    raise exception 'ARRET : la fonction en place n est pas celle du 04/11 (vue %) -- quelqu un est passe apres, relire avant de defaire', vue;
  end if;

  execute src;
end $$;

-- ---------------------------------------------------------------------
-- CONTROLE DU RETOUR ARRIERE : il ne reste AUCUNE trace de ce qu'il
-- devait retirer, et les voisines sont intactes.
-- ---------------------------------------------------------------------
select
  md5(pg_get_functiondef(p.oid)) = 'ec8066616381cdb90df38ec561f1441f'
    as A_la_version_d_avant_est_revenue,
  pg_get_functiondef(p.oid) not like '%tmp_incoherents%'
    as B_aucune_trace_du_critere,
  pg_get_functiondef(p.oid) not like '%vitrines_incoherentes%'
    as C_aucune_trace_du_compteur,
  pg_get_functiondef(p.oid) like '%vivantes < 5000%'
    as D_le_plancher_de_securite_est_intact,
  (select count(*) from pg_proc q join pg_namespace m on m.oid = q.pronamespace
    where q.proname = 'app_photos_remplir_adresses_registre' and m.nspname = 'public') = 1
    as E_la_fonction_soeur_du_registre_est_intacte,
  (select count(*) from pg_proc q where q.proname like '%essai0411%') = 0
    as F_aucune_fonction_d_essai_oubliee
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where p.proname = 'app_photos_remplir_adresses_app' and n.nspname = 'public';
