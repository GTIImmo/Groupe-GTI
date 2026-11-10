-- ===========================================================================
-- RETOUR ARRIERE du regel du 09/11/2026 -- les 9 lignes neuves
--
-- ⭐ IL NE JUGE QUE SA PART : il retire les 9 liens POSES PAR CE PATCH, et
--   rien d'autre. Il les reconnait par `gele_par = 'regel_2026-11-09'`, jamais
--   par une liste d'identifiants recopiee -- une liste peut se desynchroniser,
--   la marque du poseur, non.
--
-- ⛔⛔ 10/11/2026 -- LA SAUVEGARDE N'EXISTE PLUS. `app_classeur_lien_avant_regel_20261109`
--   a ete SUPPRIMEE le 10/11 avec l'accord de Frederic : elle faisait echouer la
--   descente chaque nuit (12 404 lues / 12 413 attendues -- elle n'a AUCUNE cle
--   primaire, donc le parcours par rang saute des lignes).
--   ⭐ ON N'A RIEN PERDU : elle se reconstitue EXACTEMENT par une requete, et ca a
--     ete verifie dans LES DEUX SENS avant de supprimer (0 ecart, 12 413 = 12 413) :
--       select * from public.app_classeur_lien where gele_par is distinct from 'regel_2026-11-09';
--   ➡ LES CONTROLES DE CE FICHIER qui comparent a la sauvegarde doivent donc la
--     RECONSTITUER par la requete ci-dessus avant de tourner.
--
-- ⭐ ET IL VERIFIE QU'IL NE RESTE AUCUNE TRACE : la table doit revenir
--   EXACTEMENT a la sauvegarde `app_classeur_lien_avant_regel_20261109`,
--   comparee dans les DEUX sens.
--
-- ⚠ CE QU'ON PERD EN REVENANT : les 9 dossiers EN COURS redeviennent non
--   relies. Ce sont des affaires vivantes (7 offres d'achat, 2 compromis en
--   attente) : le rattrapage ne les touchera jamais, et rien ne le signalera
--   tant que la sentinelle sur les lignes non reliees n'est pas posee.
--
-- ⚠ LE MIROIR LOCAL : si la descente de 07:30 est deja passee, phase2.sqlite
--   porte les 9 liens. Il reviendra de lui-meme a la descente SUIVANTE -- la
--   descente recopie Supabase, elle ne pousse rien. ⛔ Ne pas la lancer a la
--   main pour accelerer : c'est la tache la plus lourde de toutes.
-- ===========================================================================

begin;

delete from public.app_classeur_lien
 where gele_par = 'regel_2026-11-09';

-- LES CONTROLES DU RETOUR ARRIERE, dans la meme transaction
do $ctrl$
declare
  v_liens int; v_lignes int; v_reste int; v_manque int; v_trop int;
begin
  select count(*), count(distinct id_unique) into v_liens, v_lignes
    from public.app_classeur_lien;
  select count(*) into v_reste from public.app_classeur_lien
   where gele_par = 'regel_2026-11-09';

  -- la table doit redevenir IDENTIQUE a la sauvegarde, dans les DEUX sens
  select count(*) into v_manque from (
      select app_affaire_id, id_unique
        from public.app_classeur_lien_avant_regel_20261109
      except
      select app_affaire_id, id_unique from public.app_classeur_lien) d;
  select count(*) into v_trop from (
      select app_affaire_id, id_unique from public.app_classeur_lien
      except
      select app_affaire_id, id_unique
        from public.app_classeur_lien_avant_regel_20261109) d;

  if v_reste <> 0 then
    raise exception 'ROUGE : % lien(s) du regel du 09/11 restent', v_reste;
  end if;
  if v_manque <> 0 then
    raise exception 'ROUGE : % lien(s) de la sauvegarde MANQUENT -- le retour a trop retire', v_manque;
  end if;
  if v_trop <> 0 then
    raise exception 'ROUGE : % lien(s) EN TROP par rapport a la sauvegarde', v_trop;
  end if;
  if v_liens <> 12413 or v_lignes <> 4679 then
    raise exception 'ROUGE : % liens / % lignes, attendu 12 413 / 4 679', v_liens, v_lignes;
  end if;

  raise notice 'RETOUR ARRIERE VERT : % liens, % lignes, identique a la sauvegarde dans les deux sens',
               v_liens, v_lignes;
end
$ctrl$;

commit;

-- ⬜ LA SAUVEGARDE N'EST PAS SUPPRIMEE ICI, EXPRES : elle reste le temoin.
--   A retirer plus tard, a la main, quand le regel sera acquis :
--     drop table public.app_classeur_lien_avant_regel_20261109;
