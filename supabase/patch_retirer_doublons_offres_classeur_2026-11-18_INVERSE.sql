-- ═══════════════════════════════════════════════════════════════════════════════
-- INVERSE -- REMETTRE LES 5 OFFRES DU CLASSEUR                         18/11/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- ⛔ UN RETOUR ARRIERE NE JUGE QUE SA PART : il verifie d'abord qu'il ne reste
--   AUCUNE trace de ce qu'il devait retirer, et que les sauvegardes sont completes.
--   Il ne touche a rien d'autre -- ni au lot, ni aux offres de Hektor.
-- ═══════════════════════════════════════════════════════════════════════════════
begin;

do $$
declare reste int; g1 int; g2 int; g3 int;
begin
  select count(*) into reste from app_affaire_ledger
   where app_affaire_id in (1001575,1001576,1001577,1001604,1001619);
  if reste <> 0 then
    raise exception '⛔ % ligne(s) sont DEJA la -- le patch n''a pas ete joue, ou l''a ete deux fois', reste;
  end if;
  select count(*) into g1 from app_affaire_ledger_avant_doublons_classeur_20261118;
  select count(*) into g2 from app_affaire_note_avant_doublons_classeur_20261118;
  select count(*) into g3 from app_classeur_lien_avant_doublons_classeur_20261118;
  if g1 <> 5 or g2 <> 5 or g3 <> 5 then
    raise exception '⛔ sauvegardes incompletes : ledger %, notes %, liens %', g1, g2, g3;
  end if;
end $$;

insert into app_affaire_ledger
  select * from app_affaire_ledger_avant_doublons_classeur_20261118;
insert into app_affaire_note
  select * from app_affaire_note_avant_doublons_classeur_20261118;
insert into app_classeur_lien
  select * from app_classeur_lien_avant_doublons_classeur_20261118;

do $$
declare n int; lot int;
begin
  select count(*) into n from app_affaire_ledger
   where app_affaire_id in (1001575,1001576,1001577,1001604,1001619);
  if n <> 5 then raise exception '⛔ % ligne(s) remises au lieu de 5', n; end if;
  select count(*) into lot from app_affaire_ledger
   where transaction_origine='classeur'
     and payload_json->>'classeur_lot' = 'C5 lot B -- offres vente reglee';
  if lot <> 64 then raise exception '⛔ le lot compte % lignes au lieu de 64', lot; end if;
  raise notice '✅ les 5 sont revenues, le lot est de nouveau a 64';
end $$;

commit;
