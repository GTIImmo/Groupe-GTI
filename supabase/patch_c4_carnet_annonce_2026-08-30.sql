-- =====================================================================
-- C.4 — LE CARNET DE L'ANNONCE, côté app
-- Date : 2026-08-30
--
-- CE QUE C'EST, ET CE QUE CE N'EST PAS.
--
-- Ce n'est PAS une copie de la liste des annonces. Celle-ci existe déjà —
-- `app_dossier_current`, 13 374 lignes — et rien ne la double. C'est un carnet
-- d'EXCEPTIONS : une ligne par champ dont l'app est l'auteur, rien d'autre.
--
-- Ses deux frères le disent mieux que n'importe quelle explication :
--     app_mandat_champ_app     1 ligne
--     app_affaire_champ_app    2 lignes
--     le registre des annonces 13 374 lignes
--
-- POURQUOI IL MANQUAIT. C.6 a posé le domicile de l'annonce CÔTÉ SERVEUR
-- (`phase2.sqlite`, 0 ligne). Mais il n'avait pas de porte d'entrée côté app,
-- alors que le mandat et l'affaire ont les deux — et c'est précisément pour ça
-- qu'eux ont pu être convertis en C.13 et C.19, et pas les annonces.
--
-- IL EST DORMANT, ET C'EST VOULU. Tant que `CHAMPS_APP_ANNONCE` reste vide dans
-- `contrat_autorite.py`, ce carnet se remplit sans que rien ne change : le run
-- de nuit continue de laisser Hektor gagner. L'allumer est un arbitrage de
-- Frédéric, pas un effet de bord d'une migration.
--
-- LA CHAÎNE, une fois complète :
--     l'écran      -> RPC (à venir)      écrit ici + crée le travail
--     la nuit      -> magasin_annonce_app.py    descend le carnet chez nous
--     le contrat   -> CHAMPS_APP_ANNONCE        décide qui gagne  ← l'interrupteur
--
-- Appliqué en production via la migration `c4_carnet_annonce_champ_app`.
-- Éprouvé à vide le 30/08 : 61 099 annonces lues côté serveur, 0 saisie, 0 écrit.
-- =====================================================================

create table if not exists public.app_annonce_champ_app (
  app_dossier_id bigint not null,
  champ          text   not null,
  valeur_app     text,
  origine        text,
  ecrit_le       timestamptz not null default now(),
  ecrit_par      text,
  primary key (app_dossier_id, champ)
);

comment on table public.app_annonce_champ_app is
  'Carnet d''exceptions de l''annonce : une ligne par champ dont l''app est l''auteur. '
  'N''est PAS une copie de app_dossier_current. Dormant tant que CHAMPS_APP_ANNONCE est vide.';

create index if not exists app_annonce_champ_app_dossier_idx
  on public.app_annonce_champ_app (app_dossier_id);

create index if not exists app_annonce_champ_app_ecrit_le_idx
  on public.app_annonce_champ_app (ecrit_le desc);

alter table public.app_annonce_champ_app enable row level security;

-- Personne n'y touche directement : seules les RPC (SECURITY DEFINER) écriront,
-- et la descente lit avec la clé de service. Même régime que ses deux frères.
revoke all on public.app_annonce_champ_app from public;
revoke all on public.app_annonce_champ_app from anon;
grant select on public.app_annonce_champ_app to authenticated;
grant all    on public.app_annonce_champ_app to service_role;

drop policy if exists app_annonce_champ_app_lecture on public.app_annonce_champ_app;
create policy app_annonce_champ_app_lecture
  on public.app_annonce_champ_app for select
  to authenticated
  using (true);
