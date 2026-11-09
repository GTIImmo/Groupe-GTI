-- ============================================================================
-- RETOUR ARRIERE du patch `patch_alias_negociateur_classeur_2026-11-09.sql`
--
-- ⭐ IL NE JUGE QUE SA PART : il retire la table d'alias, et il VERIFIE qu'il
--   n'en reste aucune trace. Il ne touche ni au registre des negociateurs, ni
--   au gel, ni au classeur.
--
-- ⭐ AUCUN RISQUE POUR LE CODE : `rapport_gel_tous_les_champs.py` retombe alors
--   sur `ALIAS_REPLI` (les deux memes alias, codes) et il L'ANNONCE a l'ecran --
--   « la table est VIDE -> REPLI sur les 2 alias codes ». Le rapport continue
--   de marcher a l'identique. ⛔ Un repli MUET aurait ete un faux vert ; c'est
--   pour ca que la phrase s'imprime.
--
-- ⚠ CE QU'ON PERD EN REVENANT : la decision retourne DANS LE CODE, donc elle
--   redevient non modifiable sans deploiement, et les deux autres lecteurs
--   prevus (l'apparieur et le rattrapage) n'ont plus de source commune.
-- ============================================================================

drop table if exists public.app_classeur_alias_negociateur;

-- ── LES DEUX CONTROLES DU RETOUR ARRIERE
select 'la table a bien disparu' as controle,
       case when not exists (
              select 1 from information_schema.tables
              where table_schema = 'public'
                and table_name = 'app_classeur_alias_negociateur')
            then 'VERT' else 'ROUGE : elle est encore la' end as resultat
union all
select 'le registre des negociateurs est INTACT',
       case when (select count(*) from app_negociateur_personne) = 185
             and (select count(*) from app_negociateur_fiche)   >= 244
            then 'VERT : 185 personnes, 244+ fiches'
            else 'A REGARDER : ' ||
                 (select count(*)::text from app_negociateur_personne) || ' personnes, ' ||
                 (select count(*)::text from app_negociateur_fiche) || ' fiches' end
union all
select 'le gel est INTACT',
       case when (select count(*) from app_classeur_lien) = 12413
            then 'VERT : 12 413 liens'
            else 'A REGARDER : ' ||
                 (select count(*)::text from app_classeur_lien) || ' liens' end;
