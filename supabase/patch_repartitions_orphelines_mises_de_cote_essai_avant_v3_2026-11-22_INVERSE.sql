-- RETOUR ARRIERE DES ORPHELINES MISES DE COTE (essai_avant_v3_2026-11-22) -- il ne juge que SA part (lecon 31) : il repose les parts
-- de CE geste, a l'identique, sous leur ancien numero, et ne touche rien d'autre. La table de garde reste (elle est au projet).
begin;
do $$
declare n int;
begin
  select count(*) into n from app_affaire_repartition_mise_de_cote where mise_de_cote_par = 'orphelines_mises_de_cote_essai_avant_v3_2026-11-22';
  if n <> 24 then raise exception '⛔ % part(s) de ce geste dans la garde, attendu 24', n; end if;
  select count(*) into n from app_affaire_repartition_mise_de_cote g join app_affaire_repartition r
      on r.app_chaine_id = g.app_chaine_id and r.cote = g.cote and r.rang = g.rang where g.mise_de_cote_par = 'orphelines_mises_de_cote_essai_avant_v3_2026-11-22';
  if n <> 0 then raise exception '⛔ % emplacement(s) deja repris -- quelqu''un est passe apres', n; end if;
end $$;
insert into app_affaire_repartition (app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage,
                                     origine, ecrit_le, ecrit_par)
select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
  from app_affaire_repartition_mise_de_cote where mise_de_cote_par = 'orphelines_mises_de_cote_essai_avant_v3_2026-11-22';
delete from app_affaire_repartition_mise_de_cote where mise_de_cote_par = 'orphelines_mises_de_cote_essai_avant_v3_2026-11-22';
do $$
declare n int; emp text;
begin
  select count(*), md5(coalesce(string_agg(app_chaine_id||':'||cote||':'||rang||':'||hektor_user_id||':'||coalesce(nom_au_moment,'')||':'||pourcentage||':'||coalesce(origine,''), ',' order by app_chaine_id, cote, rang), '')) into n, emp from app_affaire_repartition;
  if n <> 17907 or emp <> 'b4ab8dc88f54a8cc69116db7a55a166a' then raise exception '⛔ inverse : les repartitions ne reviennent pas a l''etat d''avant (% %)', n, emp; end if;
  raise notice '✅ 24 parts reposees ; repartitions revenues a 17907, empreinte d''avant.';
end $$;
commit;
