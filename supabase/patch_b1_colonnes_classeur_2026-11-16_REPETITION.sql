-- ════════════════════════════════════════════════════════════════════════════
-- CONTROLES DE B1 -- 16/11/2026 . A REJOUER QUAND ON VEUT
-- ⛔ AUCUNE ECRITURE. Tout est en select.
-- ════════════════════════════════════════════════════════════════════════════

-- ① LES TROIS COLONNES DE CLASSE A, ET LEUR TYPE
select 'Y  vente_reglee_app' as controle,
       coalesce(max(data_type), '⛔ ABSENTE') as valeur, 'text' as attendu
  from information_schema.columns
 where table_schema='public' and table_name='app_affaire_ledger'
   and column_name='vente_reglee_app'
union all
select 'AA numero_facture_app',
       coalesce(max(data_type), '⛔ ABSENTE'), 'text'
  from information_schema.columns
 where table_schema='public' and table_name='app_affaire_ledger'
   and column_name='numero_facture_app'
union all
select 'C  numero_mandat_app',
       coalesce(max(data_type), '⛔ ABSENTE'), 'text'
  from information_schema.columns
 where table_schema='public' and table_name='app_affaire_ledger'
   and column_name='numero_mandat_app'
union all
-- ② ⭐ CE QU ON NE DEVAIT PAS TOUCHER : la classe C et la marque du 15/11
select '⭐ numero_mandat (classe C) INTACT',
       coalesce(max(data_type), '⛔ DISPARUE'), 'text'
  from information_schema.columns
 where table_schema='public' and table_name='app_affaire_ledger'
   and column_name='numero_mandat'
union all
select '⭐ transaction_origine INTACTE',
       coalesce(max(data_type), '⛔ DISPARUE'), 'text'
  from information_schema.columns
 where table_schema='public' and table_name='app_affaire_ledger'
   and column_name='transaction_origine'
union all
-- ③ LA TABLE DES AVIS
select 'app_classeur_avis : colonnes',
       count(*)::text, '7'
  from information_schema.columns
 where table_schema='public' and table_name='app_classeur_avis'
union all
select 'app_classeur_avis : cle primaire',
       coalesce(max(kcu.column_name), '⛔ AUCUNE'), 'id_unique'
  from information_schema.table_constraints tc
  join information_schema.key_column_usage kcu
    on kcu.constraint_name = tc.constraint_name
 where tc.table_schema='public' and tc.table_name='app_classeur_avis'
   and tc.constraint_type='PRIMARY KEY'
union all
select 'app_classeur_avis : RLS active',
       (select relrowsecurity::text from pg_class
         where relname='app_classeur_avis' and relnamespace='public'::regnamespace), 'true'
union all
-- ④ ⛔ LE TEMOIN QUI COMPTE : RIEN N A ETE ECRIT
select '⛔ lignes du registre (rien touche)',
       count(*)::text, '31253'
  from app_affaire_ledger
union all
select '⛔ valeurs posees dans les 3 neuves (doit etre 0)',
       count(*)::text, '0'
  from app_affaire_ledger
 where vente_reglee_app is not null or numero_facture_app is not null
    or numero_mandat_app is not null
union all
select '⛔ lignes dans app_classeur_avis (doit etre 0)',
       count(*)::text, '0'
  from app_classeur_avis
union all
select '⭐ les 96 du classeur sont intactes',
       count(*)::text, '96'
  from app_affaire_ledger where transaction_origine = 'classeur'
order by 1;
