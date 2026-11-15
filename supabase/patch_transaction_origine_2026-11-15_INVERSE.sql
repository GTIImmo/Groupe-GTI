-- ════════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIERE de patch_transaction_origine_2026-11-15.sql            15/11/2026
-- ════════════════════════════════════════════════════════════════════════════
-- ⚠⚠ UN RETOUR ARRIERE NE JUGE QUE SA PART (lecon 31) : il verifie d'abord
--   qu'il ne reste aucune trace de ce qu'il doit retirer, et il REFUSE de
--   retirer une colonne que quelqu'un a remplie.
--
-- CE QU'IL REMET :
--   1. la vue dans sa forme du 20/08/2026 (le seul filtre : pas de numero Hektor)
--   2. la colonne transaction_origine, SEULEMENT si elle est entierement vide
--
-- ⚠ IL NE TOUCHE NI AU MONITEUR (son seuil n'a pas bouge), NI AU WORKER (la
--   piece 3 n'est pas dans ce patch), NI A `present_in_hektor`.
-- ════════════════════════════════════════════════════════════════════════════

-- ─── 1. LA VUE, DANS SA FORME D'ORIGINE ───
create or replace view public.app_affaires_sans_numero_hektor as
  select app_affaire_id, app_dossier_id, kind, state, montant, date, first_seen_at
    from public.app_affaire_ledger
   where hektor_affaire_id is null;

comment on view public.app_affaires_sans_numero_hektor is
  'Sentinelle : rien ne doit produire d''affaire sans numero Hektor avant la '
  'tache 13 (saisie directe dans l''app). Une seule ligne ici = un bug qui '
  'ecrit en silence. Branchee dans monitoring/check_gti_health.py, seuil 0.';

-- ─── 2. LA COLONNE, SI ET SEULEMENT SI ELLE EST VIDE ───
do $$
declare
  n bigint;
begin
  select count(*) into n
    from public.app_affaire_ledger
   where transaction_origine is not null;
  if n > 0 then
    raise notice 'LA COLONNE EST GARDEE : % ligne(s) sont marquees. Les retirer serait PERDRE une information que rien ne reconstruit (ni Hektor ni le classeur ne disent qu''une transaction est une reprise). Pour forcer : vider la colonne d''abord, puis rejouer.', n;
  else
    alter table public.app_affaire_ledger drop column if exists transaction_origine;
    raise notice 'COLONNE RETIREE : elle etait entierement vide.';
  end if;
end $$;

-- ─── 3. LE CONTROLE DU RETOUR ARRIERE ───
do $$
declare
  d text;
begin
  select pg_get_viewdef('public.app_affaires_sans_numero_hektor'::regclass, true) into d;
  if position('transaction_origine' in d) > 0 then
    raise exception 'RATE : la vue filtre encore sur transaction_origine.';
  end if;
  if position('hektor_affaire_id IS NULL' in d) = 0 then
    raise exception 'RATE : la vue a perdu son filtre d''origine. Definition lue : %', d;
  end if;
  raise notice 'RETOUR ARRIERE VERIFIE : la vue est revenue a sa forme du 20/08.';
end $$;
