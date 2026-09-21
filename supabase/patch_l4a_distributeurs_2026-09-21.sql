-- ═══════════════════════════════════════════════════════════════════════════
-- L4-a — LES DISTRIBUTEURS : UN NUMERO A LA NAISSANCE             21/09/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- CE QUI MANQUE POUR QU'UN OBJET NAISSE DANS L'APP. Le numero de l'app est
-- aujourd'hui attribue par le SERVEUR LOCAL, et seulement APRES que Hektor a
-- cree l'objet. Tant que l'app ne sait pas s'en donner un elle-meme, elle ne
-- peut poser qu'une ligne « En creation… » -- 78 creations d'annonce et 14 de
-- contact sont passees par la, toutes via Hektor.
--
-- LA TRANSACTION EST LE MODELE, et il marche depuis le 20/08 :
--    app_affaire_id_app_seq   -> 330 transactions nees dans l'app
-- On pose ici les memes distributeurs pour l'annonce et la recherche. Le contact
-- a recu le sien hier (app_contact_identite_seq).
--
-- ⚠ LES PLAGES SONT CHOISIES SUR LES MAXIMA REELS, PAS AU HASARD :
--       annonce   : la serie locale est deja a 7 589 098  -> depart 10 000 000
--       recherche : la serie locale est a    77 068        -> depart  1 000 000
--       contact   : Hektor est a 605 433                   -> depart 10 000 000 (hier)
--   Une plage qui croiserait la serie existante ferait deux objets differents
--   portant le meme numero -- et rien ne le signalerait avant longtemps.
--
-- ⚠ CE PATCH NE CREE RIEN ET N'APPELLE RIEN. Personne ne tire encore de numero :
--   c'est le lot L4-b qui branchera la creation. Poser le distributeur d'abord
--   permet de verifier la plage a froid, sans urgence.
--
-- RETOUR ARRIERE : drop sequence public.app_dossier_id_app_seq;
--                  drop sequence public.app_search_id_app_seq;
-- ═══════════════════════════════════════════════════════════════════════════

create sequence if not exists public.app_dossier_id_app_seq
  as bigint start with 10000000 minvalue 10000000 no cycle;

create sequence if not exists public.app_search_id_app_seq
  as bigint start with 1000000 minvalue 1000000 no cycle;

grant usage, select on sequence public.app_dossier_id_app_seq to service_role, authenticated;
grant usage, select on sequence public.app_search_id_app_seq to service_role, authenticated;

comment on sequence public.app_dossier_id_app_seq is
  'L4-a 21/09/2026 : numero d''annonce attribue par l''APP. Depart 10 000 000, au-dessus de la serie locale (7 589 098). La case hektor_annonce_id reste vide jusqu''au retour du worker.';

comment on sequence public.app_search_id_app_seq is
  'L4-a 21/09/2026 : numero de recherche attribue par l''APP. Depart 1 000 000, au-dessus du registre local (77 068).';

-- ── LA SENTINELLE DES PLAGES ───────────────────────────────────────────────
-- Elle ne surveille pas un flux : elle surveille une HYPOTHESE. Le jour ou la
-- serie venue de Hektor s'approcherait d'une plage de l'app, deux objets
-- pourraient porter le meme numero -- et personne ne le verrait.
create or replace view public.app_v_plages_numeros as
  select 'annonce' as objet,
         (select max(app_dossier_id) from public.app_dossier_current where app_dossier_id < 10000000) as max_serie_existante,
         10000000::bigint as debut_plage_app,
         (select count(*) from public.app_dossier_current where app_dossier_id >= 10000000) as nes_dans_l_app
  union all
  select 'contact',
         (select max(nullif(hektor_contact_id,'')::bigint) from public.app_contact_current where hektor_contact_id ~ '^[0-9]+$' and hektor_contact_id::bigint < 10000000),
         10000000,
         (select count(*) from public.app_contact_current where hektor_contact_id ~ '^[0-9]+$' and hektor_contact_id::bigint >= 10000000)
  union all
  select 'recherche',
         (select max(app_search_id) from public.app_contact_search_current where app_search_id < 1000000),
         1000000,
         (select count(*) from public.app_contact_search_current where app_search_id >= 1000000);

comment on view public.app_v_plages_numeros is
  'L4-a 21/09/2026 : distance entre la serie venue de Hektor et la plage reservee a l''app, par objet. Tant que max_serie_existante reste tres loin de debut_plage_app, aucune collision n''est possible.';

grant select on public.app_v_plages_numeros to service_role, authenticated;
-- L4-a : la sonde ne compte que ce qui est ANORMAL -- une serie Hektor qui
-- s'approche a moins de 20 % de la plage reservee a l'app. Vide aujourd'hui.
create or replace view public.app_v_plages_trop_proches as
  select * from public.app_v_plages_numeros
   where coalesce(max_serie_existante, 0) > (debut_plage_app * 8 / 10);

comment on view public.app_v_plages_trop_proches is
  'L4-a 21/09/2026 : plages dont la serie existante approche celle de l''app (>80 %). Seuil de la sonde data.plages_numeros : 0. Ecarts au 21/09 : annonce 2 472 137, contact 9 394 567, recherche 922 932.';

grant select on public.app_v_plages_trop_proches to service_role, authenticated;
