-- ═══════════════════════════════════════════════════════════════════════════════
-- L'ETIQUETTE QUI DISAIT LE CONTRAIRE DU CLASSEUR                      18/11/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- `etat_au_classeur` etait ecrit EN DUR a 'Annulee' dans le generateur des quatre
-- familles (poser_offres_annulees_classeur_2026-11-16.py). Les lignes du lot
-- « offres vente reglee » viennent pourtant de l'etat « Vente réglée » : leur trace
-- disait l'inverse de leur origine.
--
-- ⭐ CE N'EST PAS UNE DONNEE QUI DECIDE : aucun code ne lit `etat_au_classeur`
--   (mesure du 18/11 sur phase2, Console, apps, supabase, backend). C'est une trace,
--   et une trace fausse coute un contresens a la premiere relecture.
-- ⛔ LES DEUX AUTRES LOTS NE SONT PAS TOUCHES : « offres annulees » et « compromis
--   annules » viennent bien de l'etat « Annulée ». Leur etiquette est juste.
-- ⛔ `classeur_lot` N'EST PAS TOUCHE : c'est par lui que l'INVERSE du lot retrouve
--   ses lignes.
--
-- RETOUR ARRIERE : ..._INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════════
begin;

do $$
declare n int;
begin
  select count(*) into n from app_affaire_ledger
   where transaction_origine='classeur'
     and payload_json->>'classeur_lot'='C5 lot B -- offres vente reglee'
     and payload_json->>'etat_au_classeur'='Annulee';
  if n <> 59 then raise exception '⛔ garde : % lignes a redresser au lieu de 59', n; end if;
end $$;

update app_affaire_ledger
   set payload_json = jsonb_set(payload_json, '{etat_au_classeur}', '"Vente réglée"'::jsonb)
 where transaction_origine='classeur'
   and payload_json->>'classeur_lot'='C5 lot B -- offres vente reglee';

do $$
declare juste int; autres int; lot int;
begin
  select count(*) into juste from app_affaire_ledger
   where payload_json->>'classeur_lot'='C5 lot B -- offres vente reglee'
     and payload_json->>'etat_au_classeur'='Vente réglée';
  if juste <> 59 then raise exception '⛔ % redressees au lieu de 59', juste; end if;

  -- ⭐ TEMOIN INVERSE : les deux autres lots gardent leur « Annulee », qui est juste.
  select count(*) into autres from app_affaire_ledger
   where transaction_origine='classeur'
     and payload_json->>'classeur_lot' <> 'C5 lot B -- offres vente reglee'
     and payload_json->>'etat_au_classeur'='Annulee';
  if autres <> 131 then raise exception '⛔ temoin inverse : % au lieu de 131', autres; end if;

  -- ⛔ Et le libelle du lot, par lequel l'INVERSE retrouve ses lignes, n'a pas bouge.
  select count(*) into lot from app_affaire_ledger
   where payload_json->>'classeur_lot'='C5 lot B -- offres vente reglee';
  if lot <> 59 then raise exception '⛔ classeur_lot abime : % lignes', lot; end if;

  raise notice '✅ 59 etiquettes redressees, 131 intactes, le libelle du lot inchange';
end $$;

commit;
