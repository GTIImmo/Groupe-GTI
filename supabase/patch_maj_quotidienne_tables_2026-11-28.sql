-- patch_maj_quotidienne_tables_2026-11-28 -- LES DEUX TABLES NEUVES DE L'OUTIL DU MATIN, VIDES (son mot du 27/11 a la nuit :
-- « Le code et une table neuve et vide ne le genent pas » -- le temoin de la nuit ne regarde ni l'une ni l'autre).
-- ⭐ Ce que l'outil n'a PAS cree : son journal d'ecriture est le journal qui existe deja (app_classeur_realignement_journal,
--    une ligne par case, avec sa valeur d'avant) -- pas de table de plus.
--   1. app_champ_destination : LE ROUTEUR (D9) -- une ligne par colonne du Sheet, pour les deux sens ; sa graine est dans
--      phase2/checks/maj_quotidienne_du_classeur.py (ROUTEUR), posee par « routeur --poser » APRES le temoin.
--   2. app_classeur_difference : LE JOURNAL DES DIFFERENCES -- deux photos du Sheet, case par case ; ecrit avec le lot.
-- Retour arriere : patch_maj_quotidienne_tables_2026-11-28_INVERSE.sql (les deux tables, si elles sont encore vides).

begin;

do $$ begin
  if to_regclass('public.app_champ_destination') is not null or to_regclass('public.app_classeur_difference') is not null then
    raise exception '⛔ garde : une des deux tables existe deja -- ce patch ne se rejoue pas';
  end if;
end $$;

create table public.app_champ_destination (
  colonne_sheet text primary key,           -- l'en-tete exact de la colonne du Sheet
  ordre         int  not null,
  famille       text not null,              -- la regle de decision de l'outil (note_g, avis, parts, annulation, ...)
  destination   text not null,              -- la place chez nous (« (rien) » pour une colonne laissee dehors)
  regle         text not null,              -- vide -> Sheet ; differe -> Sheet gagne ; note neuve datee ; ...
  hektor        text not null default 'jamais',   -- ce qui part chez Hektor : « jamais » tant que l'etape 9 n'existe pas
  ecrit         boolean not null default false,   -- L'INTERRUPTEUR de la colonne
  raison        text,                       -- d'ou vient la regle (son mot, le lot, la decision)
  sens          text not null default 'sheet_vers_app' check (sens in ('sheet_vers_app', 'app_vers_sheet', 'les_deux')),
  pose_le       timestamptz not null default now()
);
alter table public.app_champ_destination enable row level security;
revoke all on public.app_champ_destination from public, anon, authenticated;

create table public.app_classeur_difference (
  photo_avant  text not null,
  photo_apres  text not null,
  id_unique    text not null,
  num          int,
  colonne      text not null,               -- l'en-tete, ou « (la ligne) » pour une ligne neuve ou disparue
  avant        text,
  apres        text,
  nature       text not null check (nature in ('neuve', 'modifiee', 'disparue', 'blancs', 'ligne neuve', 'ligne disparue')),
  lot          text,                        -- le lot de l'outil qui l'a ecrite
  constate_le  timestamptz not null default now(),
  primary key (photo_apres, id_unique, colonne)
);
alter table public.app_classeur_difference enable row level security;
revoke all on public.app_classeur_difference from public, anon, authenticated;

do $$ begin
  if (select count(*) from public.app_champ_destination) <> 0 or (select count(*) from public.app_classeur_difference) <> 0 then
    raise exception '⛔ controle : les tables neuves ne sont pas vides'; end if;
  raise notice '✅ les deux tables neuves existent, vides, RLS allumee, aucun droit ouvert';
end $$;

commit;
