-- ═══════════════════════════════════════════════════════════════════════════
-- LA SENTINELLE DE LA TABLE DES PARTIES NE SE LIT PLUS EN DIRECT                         04/11/2026
-- Décision de Frédéric (04/11 soir) : « Oui, prépare-le ».
--
-- LE CONSTAT : la sentinelle data.affaire_partie_ecart (monitoring/check_gti_health.py) comptait la vue
-- app_v_affaire_partie_ecarts par l'API. Cette vue RECALCULE les parties des 31 128 transactions et les compare
-- aux 117 003 lignes de la table : 8,3 s mesurées le 04/11, pour une API coupée à 8 s (statement_timeout des
-- rôles authenticator / authenticated / service_role). Depuis sa naissance le 26/10, la sonde a basculé
-- 20 fois entre « ok » et « illisible » (app_monitor_event) — et chaque transaction neuve l'éloigne du vert.
-- Quand elle arrive au bout, elle trouve 0 écart : c'est le CONTRÔLE qui est trop lent, pas la table qui ment.
--
-- LE REMÈDE : la base fait elle-même le relevé, toutes les heures (pg_cron, rôle postgres, sans la limite des
-- 8 s de l'API), et range les écarts dans une petite table. La sentinelle lit cette table.
--   · la vue app_v_affaire_partie_ecarts NE CHANGE PAS (elle reste la définition de l'écart, et se lit à la main) ;
--   · le relevé se REMPLACE en entier à chaque passage, dans une seule transaction (jamais à moitié) ;
--   · la fraîcheur est surveillée par cron.health (la tâche apparaît d'elle-même dans app_cron_health) :
--     une tâche en échec ou en retard sonne là, donc un relevé vide ne peut pas mentir en silence ;
--   · passage à :40 — la surveillance tourne vers :49 toutes les deux heures, elle lit un relevé de 9 minutes.
-- ⛔ RIEN N'EST ÉCRIT CHEZ HEKTOR. Retour arrière : _INVERSE.sql (la tâche, la fonction et la table partent ;
-- remettre "table": "app_v_affaire_partie_ecarts" dans la sonde).
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

-- ── 1. LE RELEVÉ ────────────────────────────────────────────────────────────────────────────────────────
create table if not exists public.app_affaire_partie_ecart_releve (
    ecart           text        not null,
    app_affaire_id  bigint,
    role            text,
    rang            integer,
    app_contact_id  bigint,
    detail          text,
    releve_le       timestamptz not null default now()
);
comment on table public.app_affaire_partie_ecart_releve is
  '04/11/2026 : le relevé HORAIRE de app_v_affaire_partie_ecarts (tâche pg_cron affaire-partie-releve-ecarts). La sentinelle data.affaire_partie_ecart lit cette table : la vue prend 8,3 s, l''API coupe à 8 s. Doit être VIDE. Remplacé en entier à chaque passage.';
alter table public.app_affaire_partie_ecart_releve enable row level security;
revoke all on public.app_affaire_partie_ecart_releve from public, anon, authenticated;
grant select on public.app_affaire_partie_ecart_releve to service_role;

-- ── 2. LA FONCTION QUI LE REFAIT ────────────────────────────────────────────────────────────────────────
create or replace function public.app_affaire_partie_relever_ecarts()
returns integer
language plpgsql
security definer
set search_path to 'public'
as $$
declare
    n integer;
begin
    -- Un seul passage à la fois : un relevé qui traînerait ne se fait pas doubler par le suivant.
    if not pg_try_advisory_xact_lock(hashtext('app_affaire_partie_relever_ecarts')) then
        return null;
    end if;
    delete from public.app_affaire_partie_ecart_releve where true;
    insert into public.app_affaire_partie_ecart_releve (ecart, app_affaire_id, role, rang, app_contact_id, detail)
    select ecart, app_affaire_id, role, rang, app_contact_id, detail
      from public.app_v_affaire_partie_ecarts;
    get diagnostics n = row_count;
    return n;
end
$$;
comment on function public.app_affaire_partie_relever_ecarts() is
  '04/11/2026 : refait le relevé app_affaire_partie_ecart_releve depuis la vue app_v_affaire_partie_ecarts (8,3 s). Appelée par pg_cron toutes les heures ; rend le nombre d''écarts (0 attendu), ou null si un passage tournait déjà.';
-- ⛔ `revoke ... from public` NE FERME PAS authenticated (droit par défaut posé sur chaque fonction) : on nomme les rôles.
revoke all on function public.app_affaire_partie_relever_ecarts() from public, anon, authenticated;
grant execute on function public.app_affaire_partie_relever_ecarts() to service_role;

-- ── 3. LA TÂCHE HORAIRE ─────────────────────────────────────────────────────────────────────────────────
select cron.schedule('affaire-partie-releve-ecarts', '40 * * * *',
                     'select public.app_affaire_partie_relever_ecarts();');

-- ── 4. LE PREMIER RELEVÉ, tout de suite (sinon la sentinelle lirait une table vide et neuve) ─────────────
select public.app_affaire_partie_relever_ecarts() as ecarts_au_premier_releve;

COMMIT;
