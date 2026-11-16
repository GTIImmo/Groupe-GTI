-- ═══════════════════════════════════════════════════════════════════════════
-- C9 -- L ETIQUETTE SUR LA TABLE DES AVIS : RETOUR ARRIERE      16/11/2026
--
-- ⭐ « Un retour arriere ne juge que SA part » (lecon 31) : il retire les DEUX
--   colonnes que ce patch a ajoutees, et RIEN d'autre. Les 2 588 avis
--   eux-memes ne sont PAS touches -- ils viennent du patch precedent.
--
-- ⛔ IL REFUSE DE SE JOUER si une valeur a ete posee autrement que par C9, c'est-a-dire
--   si le compte des etiquettes remplies n'est plus 2 560 : cela voudrait dire
--   qu'un humain ou un geste de l'app a rattache une ligne a la main, et
--   supprimer la colonne perdrait cette saisie.
-- ═══════════════════════════════════════════════════════════════════════════

begin;

do $$
declare remplies integer; avis integer;
begin
  select count(*) into avis from public.app_classeur_avis;
  select count(app_dossier_uuid) into remplies from public.app_classeur_avis;
  if remplies <> 2560 then
    raise exception '⛔ ARRET : % etiquettes remplies au lieu de 2 560. Quelqu''un '
      'a rattache une ligne apres nous -- ne RIEN supprimer sans relire.', remplies;
  end if;
  raise notice '✅ 2 560 etiquettes, aucune saisie etrangere (% avis en tout).', avis;
end $$;

drop index if exists public.app_classeur_avis_dossier_uuid_idx;

alter table public.app_classeur_avis
  drop column if exists app_dossier_uuid,
  drop column if exists app_dossier_numero;

do $$
declare reste integer; avis integer;
begin
  select count(*) into reste from information_schema.columns
   where table_schema='public' and table_name='app_classeur_avis'
     and column_name in ('app_dossier_uuid', 'app_dossier_numero');
  if reste <> 0 then
    raise exception '⛔ il reste % colonne(s) d''etiquette.', reste;
  end if;
  -- ⭐ SA PART, ET SEULEMENT SA PART : les avis doivent etre INTACTS.
  select count(*) into avis from public.app_classeur_avis;
  if avis <> 2588 then
    raise exception '⛔⛔ % avis au lieu de 2 588 : le retour arriere a deborde '
      'sur les donnees. GRAVE.', avis;
  end if;
  raise notice '✅ les 2 colonnes retirees . LES 2 588 AVIS SONT INTACTS.';
end $$;

commit;
