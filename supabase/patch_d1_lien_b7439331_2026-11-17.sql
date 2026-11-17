-- ═══════════════════════════════════════════════════════════════════════════
-- D1-1.5 -- LE SEUL LIEN FRANC DES 6 : b7439331 -> 30809      17/11/2026
--
-- ⭐ SUR LES 6 LIENS QUE LE PLAN ANNONCAIT (liste du 13/11), REMESURES LE 17/11 :
--     d7cbb8fa  DEJA LIEE  (« regel additif 13/11 -- lot C »)
--     c67ccc6a  DEJA LIEE  (meme re-gel)
--     Z3DYDC4X  ⛔ INTERDITE -- sa cible 14111 est DEJA liee a la ligne 1932 /
--               AYIHPHF5, et AUCUNE transaction du gel n'est liee a deux lignes
--               (0 sur 12 790). La poser creerait la premiere violation.
--     ME6S0TR9  ⬜ rien a geler : la transaction n'existe pas chez Hektor (1.4)
--     6a259cce  ⬜ idem
--     b7439331  ✅ LE SEUL POSABLE, et c'est lui que ce patch pose.
--
-- CE QU'ON SAIT DE LUI, MESURE :
--     ligne 4791 du Sheet (et de la table, remise a jour juste avant)
--     cible 30809 : offre / accepted / 2026-11-10 / annonce 63299 / chaine 30809
--     elle ne porte AUCUN lien aujourd'hui -> aucun conflit
--     ses deux voisines de lignes (4790 d7cbb8fa, 4792 c67ccc6a) ont ete liees
--     le 13/11 de la meme facon : ce lien complete une serie, il ne l'invente pas.
--
-- ⭐ `confiance` = « sûre » : c'est la valeur que le plan donnait, et les deux
--   voisines posees le 13/11 la portent aussi. On ne la releve pas d'un cran.
-- ⭐ `preuves` = 0 et `etage` nomme la provenance : comme pour les 195, il n'y a
--   eu AUCUN rapprochement a faire -- la cible etait ecrite dans le plan.
--
-- RETOUR ARRIERE : patch_d1_lien_b7439331_2026-11-17_INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════
begin;

-- ① LE GARDE-FOU : ni la ligne ni la cible ne doivent deja etre liees
do $$
declare n integer;
begin
  select count(*) into n from app_classeur_lien where id_unique = 'b7439331';
  if n > 0 then raise exception '⛔ la ligne b7439331 porte deja % lien(s)', n; end if;
  select count(*) into n from app_classeur_lien where app_affaire_id = 30809;
  if n > 0 then
    raise exception '⛔ la transaction 30809 est deja liee (% lien(s)) -- une '
      'transaction liee a deux lignes serait une premiere', n;
  end if;
  -- ⭐ et la ligne doit exister dans la table des lignes
  select count(*) into n from app_classeur_ligne_id
   where id_unique = 'b7439331' and ligne_classeur = 4791;
  if n <> 1 then
    raise exception '⛔ la ligne 4791 / b7439331 est inconnue de la table des lignes';
  end if;
  -- ⭐ et la cible doit etre une OFFRE, comme le lien va le dire
  select count(*) into n from app_affaire_ledger
   where app_affaire_id = 30809 and kind = 'offre';
  if n <> 1 then raise exception '⛔ la transaction 30809 n est pas une offre'; end if;
end $$;

-- ② LE LIEN
insert into app_classeur_lien
    (ligne_classeur, app_affaire_id, role, confiance, preuves, etage,
     gele_par, id_unique)
values
    (4791, 30809, 'offre', 'sûre', 0,
     '0 cible nommee par le plan (D1-1.5)', 'd1 1.5 du 2026-11-17', 'b7439331');

-- ③ LES CONTROLES
do $$
declare n integer;
begin
  select count(*) into n from app_classeur_lien where id_unique = 'b7439331';
  if n <> 1 then raise exception '⛔ % lien(s) pour b7439331 au lieu de 1', n; end if;

  select count(*) into n from app_classeur_lien;
  if n <> 12791 then raise exception '⛔ LE GEL PORTE % liens au lieu de 12 791', n; end if;

  -- ⭐⭐ LA REGLE DE FAIT TIENT TOUJOURS : aucune transaction liee a deux lignes
  select count(*) into n from (select app_affaire_id from app_classeur_lien
    group by app_affaire_id having count(distinct id_unique) > 1) s;
  if n <> 0 then
    raise exception '⛔ % transaction(s) liee(s) a plusieurs lignes -- la regle est '
      'rompue', n;
  end if;

  -- ⭐ le role du lien est celui de la transaction
  select count(*) into n from app_classeur_lien k
    join app_affaire_ledger l on l.app_affaire_id = k.app_affaire_id
   where k.id_unique = 'b7439331' and k.role <> l.kind;
  if n <> 0 then raise exception '⛔ le role du lien ne suit pas la transaction'; end if;

  -- ⛔ TEMOIN INVERSE : la sentinelle du gel ne bouge pas
  select count(*) into n from app_v_classeur_lien_casse;
  if n <> 9 then raise exception '⛔ la vue des liens casses passe a % (etait 9)', n; end if;

  raise notice '✅ 1 lien pose . le gel passe a 12 791 . la regle « une transaction, '
    'une ligne » tient';
end $$;

commit;
