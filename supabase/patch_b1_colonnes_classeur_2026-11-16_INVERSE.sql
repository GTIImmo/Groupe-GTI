-- ════════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIERE DE B1 -- LES 6 COLONNES DU CLASSEUR            16/11/2026
-- ════════════════════════════════════════════════════════════════════════════
--
-- ⛔ IL NE JUGE QUE SA PART (regle n0 31) : il retire les TROIS colonnes neuves
--   et la table des avis, puis il VERIFIE qu il ne reste aucune trace ET que ce
--   qu il ne devait pas toucher est intact.
--
-- ⛔⛔ ET IL REFUSE DE DETRUIRE UNE DONNEE : si une seule valeur a ete posee dans
--   l une des colonnes neuves ou dans la table des avis, IL S ARRETE. Retirer une
--   colonne de classe A qui porte deja des valeurs du classeur, c est perdre ce
--   que C8 ou C9 vient d ecrire -- sans sauvegarde et sans journal.
--   ➡ Pour defaire APRES avoir ecrit, il faut d abord retirer les donnees avec
--     l inverse de C8 / C9, puis seulement rejouer celui-ci.
--
-- ⚠ ON NE TOUCHE PAS `numero_mandat` (classe C, de Hektor) ni
--   `transaction_origine` (classe A, posee le 15/11, et 96 lignes la portent).
-- ════════════════════════════════════════════════════════════════════════════

begin;

-- ── LE REFUS DE DETRUIRE : a lire AVANT, et il arrete le patch
do $$
declare
  n_y integer := 0; n_aa integer := 0; n_m integer := 0; n_avis integer := 0;
begin
  if exists (select 1 from information_schema.columns
              where table_schema='public' and table_name='app_affaire_ledger'
                and column_name='vente_reglee_app') then
    execute 'select count(*) from app_affaire_ledger where vente_reglee_app is not null'
       into n_y;
  end if;
  if exists (select 1 from information_schema.columns
              where table_schema='public' and table_name='app_affaire_ledger'
                and column_name='numero_facture_app') then
    execute 'select count(*) from app_affaire_ledger where numero_facture_app is not null'
       into n_aa;
  end if;
  if exists (select 1 from information_schema.columns
              where table_schema='public' and table_name='app_affaire_ledger'
                and column_name='numero_mandat_app') then
    execute 'select count(*) from app_affaire_ledger where numero_mandat_app is not null'
       into n_m;
  end if;
  if exists (select 1 from information_schema.tables
              where table_schema='public' and table_name='app_classeur_avis') then
    execute 'select count(*) from app_classeur_avis' into n_avis;
  end if;

  raise notice 'valeurs posees : Y=%s  AA=%s  numero_mandat_app=%s  avis=%s',
               n_y, n_aa, n_m, n_avis;

  if (n_y + n_aa + n_m + n_avis) > 0 then
    raise exception 'ARRET : %s valeur(s) sont posees dans ces colonnes -- ce retour '
                    'arriere les DETRUIRAIT. Retirer d abord les donnees (inverse de '
                    'C8 / C9), puis rejouer celui-ci.', (n_y + n_aa + n_m + n_avis);
  end if;
end $$;

-- ── LE RETRAIT
drop table if exists public.app_classeur_avis;

alter table public.app_affaire_ledger
  drop column if exists vente_reglee_app,
  drop column if exists numero_facture_app,
  drop column if exists numero_mandat_app;

-- ── LES CONTROLES DU RETOUR ARRIERE
do $$
declare
  reste integer;
  lignes integer;
begin
  select count(*) into reste from information_schema.columns
   where table_schema='public' and table_name='app_affaire_ledger'
     and column_name in ('vente_reglee_app','numero_facture_app','numero_mandat_app');
  if reste <> 0 then
    raise exception 'ARRET : %s colonne(s) subsistent -- le retour est INCOMPLET', reste;
  end if;
  if exists (select 1 from information_schema.tables
              where table_schema='public' and table_name='app_classeur_avis') then
    raise exception 'ARRET : app_classeur_avis subsiste';
  end if;

  -- ⭐ CE QU IL NE DEVAIT PAS TOUCHER
  if not exists (select 1 from information_schema.columns
                  where table_schema='public' and table_name='app_affaire_ledger'
                    and column_name='numero_mandat') then
    raise exception 'ARRET : numero_mandat (classe C) a disparu -- NE PAS VALIDER';
  end if;
  if not exists (select 1 from information_schema.columns
                  where table_schema='public' and table_name='app_affaire_ledger'
                    and column_name='transaction_origine') then
    raise exception 'ARRET : transaction_origine a disparu -- NE PAS VALIDER';
  end if;
  select count(*) into lignes from app_affaire_ledger;
  if lignes <> 31253 then
    raise exception 'ARRET : le registre porte %s lignes au lieu de 31 253 -- NE PAS VALIDER', lignes;
  end if;

  raise notice 'retour arriere OK : 0 trace, numero_mandat et transaction_origine intacts, registre a %s lignes', lignes;
end $$;

commit;
