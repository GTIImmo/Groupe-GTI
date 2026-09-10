-- ═══════════════════════════════════════════════════════════════════════════════
-- CE QUE SEUL L'ASSISTANT REND, ET QUE PERSONNE NE GARDAIT         10/09/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- Copie versionnée de la migration `app_affaire_console_lecture_assistant`.
--
-- ─── LE MANQUE, MESURÉ LE 10/09 ───
-- Il existe des champs que Hektor accepte d'écrire et qu'il ne rend JAMAIS par
-- l'API. On peut donc les envoyer sans jamais vérifier ce qu'on a écrit — ce
-- qu'interdit la règle 3 du projet, « une action a une fin visible ».
--
--     notairesAcquereur[] / notairesMandant[]        0 sur 10 586 compromis
--     unitesEntreePercent / unitesSortiePercent      le PARTAGE de la commission
--     conditionsSuspensivesSelected[]                absentes de toutes les charges
--     montantHonoraireEntree / tauxHonoraireEntree   le TAUX VENDEUR
--
-- Le dernier est le manque n°1 de la tâche 0.1 : « le taux VENDEUR détermine les
-- honoraires d'entrée, donc LA COMMISSION DE L'AGENCE ; il est aujourd'hui
-- invisible ET non modifiable depuis l'app ».
--
-- ─── LA SOURCE ÉTAIT DÉJÀ SOUS NOS YEUX ───
-- À chaque écriture, le worker ouvre l'assistant, reçoit le formulaire rendu
-- (50 000 à 86 000 caractères), en tire trois valeurs et jette le reste.
-- Le lire ne coûte AUCUNE requête de plus, et rafraîchit exactement la
-- transaction que l'utilisateur vient de toucher.
--
-- Preuve que la lecture est juste, sur la capture réelle du compromis 24933 :
--     node Console/test_lecture_console.js
--     notaire acquéreur 49708 · honoraires vendeur 10000.00 · taux 5.650
--
-- ⚠ CETTE TABLE N'EST PAS LE REGISTRE, ET C'EST DÉLIBÉRÉ. Le run de nuit pousse
--   `app_affaire_ledger` avec `SELECT *` : une colonne que le local ne sait pas
--   remplir y serait écrasée par des NULL, pour les 29 349 lignes d'un coup. Ici
--   le local n'écrit jamais, donc rien ne peut écraser. Le rattrapage console
--   (palier B) écrira dans la MÊME table, avec `source = 'rattrapage'`.
--
-- ⚠ `html_etapes` EST TEMPORAIRE, et il se tarit tout seul. On connaît la forme
--   HTML de l'étape 0 (capture du 03/09) mais PAS celle des étapes 2 et 3, où
--   vivent les unités et les conditions. On garde donc leur brut pour écrire les
--   sélecteurs sur du réel — deviner a coûté une demi-journée deux fois cette
--   semaine (acquéreurs multiples, 06 et 07/09). Le jour où la lecture trouve
--   quelque chose, la colonne cesse de se remplir : le worker ne conserve le
--   brut que lorsqu'il n'a rien su lire.
--
-- RETOUR ARRIÈRE : DROP TABLE public.app_affaire_console. Rien d'autre ne la lit.
-- ═══════════════════════════════════════════════════════════════════════════════

create table if not exists public.app_affaire_console (
  app_affaire_id           bigint primary key,
  hektor_annonce_id        bigint,
  kind                     text,
  hektor_affaire_id        text,
  notaires_acquereur       jsonb,
  notaires_mandant         jsonb,
  montant_honoraire_entree text,
  taux_honoraire_entree    text,
  unites_entree_percent    text,
  unites_sortie_percent    text,
  conditions_suspensives   jsonb,
  html_etapes              jsonb,
  source                   text,
  lu_le                    timestamptz not null default now()
);

comment on table public.app_affaire_console is
  'Ce que seul l''assistant de Hektor rend (notaires du compromis, unites de commission, conditions suspensives, taux vendeur). Ecrite par le worker a chaque ecriture, et plus tard par le rattrapage console. Le run de nuit n''y touche JAMAIS.';
comment on column public.app_affaire_console.notaires_acquereur is
  'Identifiants contact Hektor lus dans notairesAcquereur[]. L''API ne rend aucun notaire sur le compromis (0/10 586).';
comment on column public.app_affaire_console.notaires_mandant is
  'Identifiants contact Hektor lus dans notairesMandant[] -- le notaire du VENDEUR.';
comment on column public.app_affaire_console.html_etapes is
  'TEMPORAIRE : le brut des etapes 2 et 3, dont la forme HTML n''a jamais ete capturee. Sert a ecrire les selecteurs sur du reel. A retirer ensuite.';

alter table public.app_affaire_console enable row level security;

-- Même politique que le registre et que le carnet : lecture pour les utilisateurs
-- actifs de l'app, écriture réservée au service_role (le worker).
create policy app_affaire_console_select_active_users
  on public.app_affaire_console for select
  using (is_app_user_active());
