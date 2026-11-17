-- ═══════════════════════════════════════════════════════════════════════════
-- LE RETOUR ARRIERE DU RE-GEL ADDITIF -- 17/11/2026
--
-- ⭐⭐ IL NE VISE QUE LA MARQUE `gele_par = 'c5 re-gel additif 2026-11-17'`.
--   Il ne PEUT PAS toucher les 12 595 liens d'origine, qui portent tous
--   `gele_par = 'apparier_classeur.py'`.
--
-- ⛔ ET IL JUGE SA PROPRE PART (lecon 31) : il verifie qu'il ne reste AUCUN lien
--   marque, ET que le gel est revenu A L'IDENTIQUE de sa sauvegarde -- pas
--   seulement au bon NOMBRE.
-- ═══════════════════════════════════════════════════════════════════════════
begin;

delete from app_classeur_lien where gele_par = 'c5 re-gel additif 2026-11-17';

do $$
declare n integer;
begin
  select count(*) into n from app_classeur_lien
   where gele_par = 'c5 re-gel additif 2026-11-17';
  if n <> 0 then raise exception '⛔ il reste % liens marques', n; end if;

  select count(*) into n from app_classeur_lien;
  if n <> 12595 then
    raise exception '⛔ LE GEL PORTE % liens au lieu de 12 595', n;
  end if;

  -- ⭐⭐ A L'IDENTIQUE, pas seulement au bon nombre : on compare DANS LES DEUX
  --   SENS avec la sauvegarde. Un lien disparu et un lien en trop se
  --   compenseraient dans un simple compte.
  select count(*) into n
    from app_classeur_lien_avant_regel_20261117 s
    left join app_classeur_lien k
           on k.ligne_classeur = s.ligne_classeur and k.app_affaire_id = s.app_affaire_id
   where k.app_affaire_id is null;
  if n <> 0 then raise exception '⛔ % liens d origine MANQUENT', n; end if;
  select count(*) into n
    from app_classeur_lien k
    left join app_classeur_lien_avant_regel_20261117 s
           on s.ligne_classeur = k.ligne_classeur and s.app_affaire_id = k.app_affaire_id
   where s.app_affaire_id is null;
  if n <> 0 then raise exception '⛔ % liens EN TROP', n; end if;

  -- ⭐ et les 195 transactions elles-memes sont INTACTES : l'inverse retire des
  --   LIENS, jamais des transactions.
  select count(*) into n from app_affaire_ledger where transaction_origine = 'classeur';
  if n <> 195 then raise exception '⛔ LES 195 TRANSACTIONS ONT BOUGE : %', n; end if;

  raise notice '✅ RETOUR ARRIERE COMPLET : le gel est a l identique, les 195 intactes';
end $$;

commit;
