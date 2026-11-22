-- ═══════════════════════════════════════════════════════════════════════════════
-- INVERSE -- REPOSER LES 3 CICATRICES DE LA FAMILLE 1, A L'IDENTIQUE         22/11/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- ⛔ UN RETOUR ARRIERE NE JUGE QUE SA PART : il verifie d'abord qu'aucune des 3 n'est deja la et
--   que les gardes sont completes ; il ne touche a rien d'autre (ni aux jumelles, ni aux 187
--   autres copies, ni a Hektor).
-- ⚠ ET LE LOCAL : si le script local a ete joue --pour-de-vrai, le reposer AUSSI, le meme jour :
--     INSERT INTO app_affaire_ledger SELECT * FROM app_affaire_ledger_mise_de_cote_cicatrices_20261122_local;
-- ═══════════════════════════════════════════════════════════════════════════════
begin;

do $$
declare deja int; g1 int; g2 int;
begin
  select count(*) into deja from public.app_affaire_ledger where app_affaire_id in (1001482, 1001563, 1001580);
  if deja <> 0 then
    raise exception '⛔ % ligne(s) sont DEJA au registre -- le patch n''a pas ete joue, ou l''inverse deux fois', deja;
  end if;
  select count(*) into g1 from public.app_affaire_ledger_mise_de_cote_cicatrices_20261122;
  if g1 <> 3 then raise exception '⛔ garde incomplete : % ligne(s) au lieu de 3', g1; end if;
  select count(*) into g2 from public.app_affaire_note_mise_de_cote_cicatrices_20261122;
  raise notice 'a reposer : 3 lignes, % note(s)', g2;
end $$;

insert into public.app_affaire_ledger
  select * from public.app_affaire_ledger_mise_de_cote_cicatrices_20261122;
insert into public.app_affaire_note
  select * from public.app_affaire_note_mise_de_cote_cicatrices_20261122;
delete from public.app_classeur_cicatrice_mise_de_cote where app_affaire_id in (1001482, 1001563, 1001580);

do $$
declare n int; lot int; nums int;
begin
  select count(*) into n from public.app_affaire_ledger where app_affaire_id in (1001482, 1001563, 1001580);
  if n <> 3 then raise exception '⛔ % ligne(s) reposees au lieu de 3', n; end if;
  select count(*) into nums from public.app_affaire_ledger
   where (app_affaire_id, app_dossier_numero) in ((1001482, 'D2019-0649'), (1001563, 'D2024-0505'), (1001580, 'D2020-0607'));
  if nums <> 3 then raise exception '⛔ % ligne(s) seulement ont retrouve leur ancien numero', nums; end if;
  select count(*) into lot from public.app_affaire_ledger where transaction_origine = 'classeur';
  if lot <> 190 then raise exception '⛔ le lot compte % copies au lieu de 190', lot; end if;
  raise notice '✅ les 3 sont reposees avec leur numero, le lot est de nouveau a 190';
end $$;

commit;
