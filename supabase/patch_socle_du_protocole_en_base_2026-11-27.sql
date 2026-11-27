-- patch_socle_du_protocole_en_base_2026-11-27 -- son mot du 27/11 : « Mets la memoire des decisions en base. »
-- Cree les 5 tables VIDES. La copie (393 449 verdicts, 185,7 Mo mesures a blanc) se fait ENSUITE par
--   python -u -X utf8 phase2/checks/socle_du_protocole_en_base_2026-11-27.py --ecrire
-- qui relit et compare chaque table AVANT son commit. Retour arriere : ..._INVERSE.sql . Controle : ..._REPETITION.sql

begin;

-- --- 1. LA GARDE : aucune des 5 tables n'existe ---------------------------------------------------------------------
do $$
begin
  if to_regclass('public.app_classeur_protocole_passage') is not null or to_regclass('public.app_classeur_protocole_verdict') is not null or to_regclass('public.app_classeur_protocole_temoin') is not null or to_regclass('public.app_classeur_protocole_motif') is not null or to_regclass('public.app_classeur_protocole_fichier') is not null then
    raise exception '⛔ garde : une table du socle existe deja -- ce patch ne se rejoue pas'; end if;
  raise notice '✅ garde : aucune des 5 tables n''existe';
end $$;

-- --- 2. LES 5 TABLES : le socle du protocole a l'identique (memes colonnes que socle.sqlite) + ses fichiers ----------
create table public.app_classeur_protocole_passage (
  id integer primary key, image text not null, image_code text not null, code text not null, version text not null,
  debut text not null, fin text, lignes integer, tranchees integer, en_attente integer, boucle integer, note text);
create table public.app_classeur_protocole_verdict (
  passage integer not null, id_unique text not null, num integer, biens text not null, verdict text not null,
  etiquette text, pieces text, preuves text, motif text, motif_texte text, epreuve text not null,
  primary key (passage, id_unique));
create table public.app_classeur_protocole_temoin (
  passage integer not null, rang integer not null, temoin text not null, id_unique text, attendu text, obtenu text,
  ecart integer not null, primary key (passage, rang));
create table public.app_classeur_protocole_motif (code text primary key, epreuve text not null, libelle text not null);
create table public.app_classeur_protocole_fichier (
  nom text primary key, origine text not null, octets bigint not null, md5 text not null, contenu bytea not null);
comment on table public.app_classeur_protocole_passage is 'La memoire des decisions du protocole du classeur (27/11) : copie a l''identique du socle.sqlite (table passage), faite et prouvee par phase2/checks/socle_du_protocole_en_base_2026-11-27.py';
comment on table public.app_classeur_protocole_verdict is 'Le verdict de chaque ligne du Sheet a chaque passage du protocole (copie a l''identique du socle, table verdict)';
comment on table public.app_classeur_protocole_temoin is 'Les ecarts des temoins de chaque passage (copie du socle, table temoin ; rang = rowid du socle)';
comment on table public.app_classeur_protocole_motif is 'Le catalogue des motifs du protocole (copie du socle, table motif)';
comment on table public.app_classeur_protocole_fichier is 'Les entrees vivantes du juge et la photo du Sheet du passage officiel, en octets avec leur md5';

-- --- 3. LA SECURITE : RLS allumee, aucun droit pour public, anon, authenticated ---------------------------------------
do $$
declare t text;
begin
  foreach t in array array['app_classeur_protocole_passage', 'app_classeur_protocole_verdict', 'app_classeur_protocole_temoin', 'app_classeur_protocole_motif', 'app_classeur_protocole_fichier'] loop
    execute format('alter table public.%I enable row level security', t);
    execute format('revoke all on public.%I from public, anon, authenticated', t);
  end loop;
end $$;

-- --- 4. LES CONTROLES ------------------------------------------------------------------------------------------------
do $$
declare n int;
begin
  select count(*) into n from pg_class c join pg_namespace s on s.oid = c.relnamespace
   where s.nspname = 'public' and c.relname like 'app_classeur_protocole_%' and c.relkind = 'r' and c.relrowsecurity;
  if n <> 5 then raise exception '⛔ controle : % table(s) sur 5 avec la RLS', n; end if;
  select count(*) into n from information_schema.role_table_grants
   where table_schema = 'public' and table_name like 'app_classeur_protocole_%' and grantee in ('PUBLIC', 'anon', 'authenticated');
  if n <> 0 then raise exception '⛔ controle : % droit(s) restent a public / anon / authenticated', n; end if;
  if (select count(*) from public.app_classeur_protocole_passage) + (select count(*) from public.app_classeur_protocole_verdict)
     + (select count(*) from public.app_classeur_protocole_temoin) + (select count(*) from public.app_classeur_protocole_motif)
     + (select count(*) from public.app_classeur_protocole_fichier) <> 0 then raise exception '⛔ controle : les tables ne sont pas vides'; end if;
  raise notice '✅ 5 tables creees, vides, RLS allumee, aucun droit pour public / anon / authenticated';
end $$;

commit;
