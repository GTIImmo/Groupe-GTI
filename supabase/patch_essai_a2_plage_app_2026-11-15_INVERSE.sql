-- ════════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIERE DE L'ESSAI A2 -- 15/11/2026
-- ════════════════════════════════════════════════════════════════════════════
--
-- ⛔ IL NE JUGE QUE SA PART (regle n0 31 du projet) : il retire LA SEULE ligne
--   d'essai, reconnue par son MARQUEUR dans payload_json, et il VERIFIE ensuite
--   qu'il ne reste aucune trace ET que les deux transactions d'origine du dossier
--   (le compromis 20217 et la vente 6544) sont INTACTES.
--
-- ⚠ ON NE SUPPRIME PAS « par app_affaire_id >= 1000000 » : ce serait viser large et
--   emporter les 340 lignes legitimes de la plage app. On vise le marqueur.
-- ════════════════════════════════════════════════════════════════════════════

begin;

-- ── ce qu'on va retirer, a lire AVANT
select app_affaire_id, kind, state, date, present_in_hektor
  from app_affaire_ledger
 where hektor_annonce_id = 28351
   and (payload_json ->> 'essai_a2_2026_11_15') = 'true';

delete from app_affaire_ledger
 where hektor_annonce_id = 28351
   and kind = 'offre'
   and hektor_affaire_id is null
   and (payload_json ->> 'essai_a2_2026_11_15') = 'true';

-- ── LES DEUX CONTROLES DU RETOUR ARRIERE
do $$
declare
  reste integer;
  origine integer;
begin
  select count(*) into reste from app_affaire_ledger
   where (payload_json ->> 'essai_a2_2026_11_15') = 'true';
  if reste <> 0 then
    raise exception 'ARRET : il reste % ligne(s) marquee(s) essai_a2 -- le retour est INCOMPLET', reste;
  end if;

  select count(*) into origine from app_affaire_ledger
   where hektor_annonce_id = 28351
     and hektor_affaire_id in ('20217', '6544');
  if origine <> 2 then
    raise exception 'ARRET : le dossier d origine ne porte plus ses 2 transactions (il en a %) -- NE PAS VALIDER', origine;
  end if;

  raise notice 'retour arriere OK : 0 trace d essai, et les 2 transactions d origine sont intactes';
end $$;

commit;
