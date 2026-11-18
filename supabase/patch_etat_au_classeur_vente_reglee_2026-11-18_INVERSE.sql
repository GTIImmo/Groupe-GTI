-- INVERSE -- remettre 'Annulee' sur les 59 lignes du lot « offres vente reglee ».
-- ⛔ Il verifie d'abord que le redressement a bien eu lieu, et lui seul.
begin;
do $$
declare n int;
begin
  select count(*) into n from app_affaire_ledger
   where payload_json->>'classeur_lot'='C5 lot B -- offres vente reglee'
     and payload_json->>'etat_au_classeur'='Vente réglée';
  if n <> 59 then raise exception '⛔ % lignes redressees au lieu de 59 -- rien a defaire', n; end if;
end $$;
update app_affaire_ledger
   set payload_json = jsonb_set(payload_json, '{etat_au_classeur}', '"Annulee"'::jsonb)
 where payload_json->>'classeur_lot'='C5 lot B -- offres vente reglee';
do $$
declare n int;
begin
  select count(*) into n from app_affaire_ledger
   where transaction_origine='classeur' and payload_json->>'etat_au_classeur'='Annulee';
  if n <> 190 then raise exception '⛔ % lignes au lieu de 190', n; end if;
  raise notice '✅ retour arriere fait : les 190 portent de nouveau Annulee';
end $$;
commit;
