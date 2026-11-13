-- ═══════════════════════════════════════════════════════════════════════════════
-- CHANTIER GED — MORCEAU 9, LOT 9a : LE REGISTRE DES PIÈCES D'IDENTITÉ            13/11/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- Note du chantier : notice/CHANTIER_GED_DOCUMENTS_2026-11-06.md §12.19. Choix « B » et « Vas y » de Frédéric (13/11).
--
-- ─── CE QUE CE PATCH POSE ───
--   ① le schéma ged_prive et sa table piece_identite : le NUMÉRO d'une pièce d'identité lue, sa DATE et son AUTORITÉ
--      de délivrance (registre anti-blanchiment). Une ligne par valeur, rattachée à la lecture (app_ged_lecture),
--      avec sa date d'effacement (5 ans).
--   ② app_ged_piece_privee_ecrire()  la seule porte d'écriture, réservée à la CLÉ DE SERVICE (le serveur Render) ;
--   ③ app_ged_piece_privee_lire()    la seule porte de lecture : admin ou manager ACTIF, ou le bien dans le
--      portefeuille de l'appelant. Le rôle « lecture » N'Y A PAS accès (il lit le reste des documents).
--   ④ l'interrupteur ged_lecture_personnes, ÉTEINT (off / admin / on).
--
-- ─── POURQUOI UN SCHÉMA À PART ───
--   · l'API n'expose que public (et graphql_public) : une table de ged_prive n'est lisible par AUCUN rôle de l'app
--     directement, seulement par les deux fonctions ;
--   · la descente de 07:45 (phase2/sync/pull_from_supabase.py) découvre les tables par la spec de l'API : elle ne
--     voit pas ged_prive, donc ne recopie PAS ces numéros sur le serveur local ;
--   · loadGedLectures (écran des documents) ne les charge jamais.
--
-- ─── CE QUE CE PATCH NE FAIT PAS ───
-- ⛔ Il ne touche ni app_ged_lecture, ni app_ged_valeur, ni app_ged_type (les 4 types des personnes y sont déjà
--   « lue ») ; la porte reste le serveur et l'interrupteur. Il ne pose AUCUNE purge : la date d'effacement est écrite,
--   le geste qui efface viendra à part (rien à effacer avant 2031).
--
-- ─── RETOUR ARRIÈRE ───
-- supabase/patch_ged_m9a_pieces_personnes_2026-11-13_INVERSE.sql. Répétition sans rien garder :
-- supabase/patch_ged_m9a_pieces_personnes_2026-11-13_REPETITION.sql.
-- ═══════════════════════════════════════════════════════════════════════════════

begin;
set local lock_timeout = '3s';

do $garde$
begin
  if to_regclass('public.app_ged_lecture') is null then raise exception 'ARRET : morceau 6 absent'; end if;
  if exists (select 1 from pg_namespace where nspname = 'ged_prive') then raise exception 'ARRET : ged_prive existe deja -- patch deja applique ?'; end if;
  if exists (select 1 from pg_proc where proname in ('app_ged_piece_privee_ecrire', 'app_ged_piece_privee_lire') and pronamespace = 'public'::regnamespace) then
    raise exception 'ARRET : une des deux fonctions existe deja';
  end if;
  if exists (select 1 from public.app_setting where key = 'ged_lecture_personnes') then raise exception 'ARRET : ged_lecture_personnes existe deja'; end if;
end
$garde$;

-- ─────────────────────────────────────────────────────── ① LE SCHÉMA ET LA TABLE
create schema ged_prive;
revoke all on schema ged_prive from public, anon, authenticated;
comment on schema ged_prive is
  'GED morceau 9 (13/11/2026) : données personnelles à accès restreint. NON exposé par l''API : accès par les '
  'fonctions public.app_ged_piece_privee_* seulement. Non recopié par la descente.';

create table ged_prive.piece_identite (
  id                 bigint generated always as identity primary key,
  lecture_id         uuid not null references public.app_ged_lecture (id) on delete cascade,
  hektor_annonce_id  text not null,
  rang               integer not null default 0,
  cle                text not null,
  valeur             text,
  valeur_date        date,
  page               integer,
  etat               text not null,
  cree_le            timestamptz not null default now(),
  a_effacer_le       date not null default ((now() + interval '5 years')::date),
  constraint piece_identite_cle check (cle in ('pieces.numero', 'pieces.date_delivrance', 'pieces.autorite_delivrance')),
  constraint piece_identite_etat check (etat in ('lu', 'incertain')),
  constraint piece_identite_une_valeur check (valeur is not null or valeur_date is not null)
);
create index piece_identite_lecture_idx on ged_prive.piece_identite (lecture_id);
create index piece_identite_annonce_idx on ged_prive.piece_identite (hektor_annonce_id);
alter table ged_prive.piece_identite enable row level security;
revoke all on table ged_prive.piece_identite from public, anon, authenticated;
comment on table ged_prive.piece_identite is
  'GED morceau 9 (13/11/2026) : numéro, date et autorité de délivrance des pièces d''identité lues (registre '
  'anti-blanchiment). Écrite par app_ged_piece_privee_ecrire (clé de service seule), lue par app_ged_piece_privee_lire.';

-- ─────────────────────────────────────────────────────── ② LA PORTE D'ÉCRITURE (CLÉ DE SERVICE)
create function public.app_ged_piece_privee_ecrire(p_lecture_id uuid, p_lignes jsonb) returns integer
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  v_annonce text;
  v_type    text;
  v_n       integer;
begin
  -- GED morceau 9 (13/11/2026). Appelée par le serveur Render APRÈS avoir écrit la lecture. N'écrit que dans ged_prive.
  select l.hektor_annonce_id, l.type_code into v_annonce, v_type from public.app_ged_lecture l where l.id = p_lecture_id;
  if v_annonce is null then raise exception '%', 'Lecture introuvable.'; end if;
  if v_type <> 'justif.identite' then raise exception '%', 'Seule une pièce d''identité a un registre.'; end if;
  if jsonb_typeof(p_lignes) <> 'array' then raise exception '%', 'Lignes attendues en liste.'; end if;
  insert into ged_prive.piece_identite (lecture_id, hektor_annonce_id, rang, cle, valeur, valeur_date, page, etat)
  select p_lecture_id, v_annonce, coalesce((x ->> 'rang')::integer, 0), x ->> 'cle', x ->> 'valeur',
         (x ->> 'valeur_date')::date, (x ->> 'page')::integer, x ->> 'etat'
    from jsonb_array_elements(p_lignes) x;
  get diagnostics v_n = row_count;
  return v_n;
end
$function$;
comment on function public.app_ged_piece_privee_ecrire(uuid, jsonb) is
  'GED morceau 9 (13/11/2026) : écrit le registre d''une pièce d''identité lue (numéro, délivrance). Clé de service seule.';
revoke all on function public.app_ged_piece_privee_ecrire(uuid, jsonb) from public, anon, authenticated;
grant execute on function public.app_ged_piece_privee_ecrire(uuid, jsonb) to service_role;

-- ─────────────────────────────────────────────────────── ③ LA PORTE DE LECTURE
create function public.app_ged_piece_privee_lire(p_lecture_id uuid)
returns table (rang integer, cle text, valeur text, valeur_date date, page integer, etat text)
language plpgsql
stable
security definer
set search_path to 'public'
as $function$
declare
  v_annonce text;
begin
  -- GED morceau 9 (13/11/2026) : admin ou manager ACTIF, ou bien du portefeuille. Sinon : rien (pas d'erreur bavarde).
  select l.hektor_annonce_id into v_annonce from public.app_ged_lecture l where l.id = p_lecture_id;
  if v_annonce is null then return; end if;
  if not (exists (select 1 from public.app_user_profile p where p.id = auth.uid() and p.is_active and p.role in ('admin', 'manager'))
          or v_annonce in (select m.hid from public.app_mes_biens_portefeuille() m(id, hid))) then
    return;
  end if;
  return query
    select t.rang, t.cle, t.valeur, t.valeur_date, t.page, t.etat
      from ged_prive.piece_identite t where t.lecture_id = p_lecture_id order by t.rang, t.cle;
end
$function$;
comment on function public.app_ged_piece_privee_lire(uuid) is
  'GED morceau 9 (13/11/2026) : lit le registre d''une pièce d''identité : admin ou manager actif, ou bien du portefeuille.';
revoke all on function public.app_ged_piece_privee_lire(uuid) from public, anon, authenticated;
grant execute on function public.app_ged_piece_privee_lire(uuid) to authenticated;

-- ─────────────────────────────────────────────────────── ④ L'INTERRUPTEUR (ÉTEINT)
insert into public.app_setting (key, value, description, updated_at) values
  ('ged_lecture_personnes', 'off',
   'GED morceau 9 (13/11/2026) : lire par l''IA la pièce d''identité et la fiche de renseignements (le numéro de la '
   'pièce va au registre ged_prive). off / admin / on. Éteint = ces pièces ne sont pas lues.',
   now());

commit;

-- ALLUMER pour Frédéric seul : update public.app_setting set value = 'admin', updated_at = now() where key = 'ged_lecture_personnes';
-- ÉTEINDRE                  : update public.app_setting set value = 'off',   updated_at = now() where key = 'ged_lecture_personnes';

-- ═══════════════════════════════════════════════════════════════════════════════
-- LES CONTRÔLES — à lire après le COMMIT. Tout doit être VERT.
-- ═══════════════════════════════════════════════════════════════════════════════
select '① la table existe, RLS active' as controle, count(*) as trouve,
       case when count(*) = 1 then 'VERT' else 'ROUGE' end as verdict
  from pg_class where oid = 'ged_prive.piece_identite'::regclass and relrowsecurity
union all
select '② aucun rôle de l''app n''a un droit sur la table', count(*),
       case when count(*) = 0 then 'VERT' else 'ROUGE' end
  from information_schema.role_table_grants
 where table_schema = 'ged_prive' and grantee in ('authenticated', 'anon', 'PUBLIC')
union all
select '③ ni anon ni authenticated n''entrent dans le schéma', count(*),
       case when count(*) = 0 then 'VERT' else 'ROUGE' end
  from (values ('anon'), ('authenticated')) r(role) where has_schema_privilege(r.role, 'ged_prive', 'usage')
union all
select '④ écrire : clé de service seule', count(*),
       case when count(*) = 1 then 'VERT' else 'ROUGE' end
  from pg_proc p where p.proname = 'app_ged_piece_privee_ecrire' and p.prosecdef
   and has_function_privilege('service_role', p.oid, 'execute')
   and not has_function_privilege('authenticated', p.oid, 'execute') and not has_function_privilege('anon', p.oid, 'execute')
union all
select '⑤ lire : authenticated oui, anon non', count(*),
       case when count(*) = 1 then 'VERT' else 'ROUGE' end
  from pg_proc p where p.proname = 'app_ged_piece_privee_lire' and p.prosecdef
   and has_function_privilege('authenticated', p.oid, 'execute') and not has_function_privilege('anon', p.oid, 'execute')
union all
select '⑥ ged_lecture_personnes posé ÉTEINT', count(*),
       case when count(*) = 1 then 'VERT' else 'ROUGE' end
  from public.app_setting where key = 'ged_lecture_personnes' and value = 'off'
union all
select '⑦ la table est vide', count(*),
       case when count(*) = 0 then 'VERT' else 'ROUGE' end
  from ged_prive.piece_identite;
