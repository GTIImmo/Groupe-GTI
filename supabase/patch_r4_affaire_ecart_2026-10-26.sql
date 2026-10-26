-- ═══════════════════════════════════════════════════════════════════════════
-- CHANTIER ⑧ · R4 — LES ÉCARTS DU CARNET DES TRANSACTIONS, ET LA RÉPONSE DE L'HUMAIN      26/10/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Note : notice/ARCHITECTURE_REGISTRE_TRANSACTIONS_CHEZ_NOUS_2026-10-22.md §54-55
-- Fichier GÉNÉRÉ (phase2/checks/gen_patch_r4_affaire_ecart.py).
--
-- POURQUOI. Avec R2 et la décision A (« pas de durée maximale »), un « conflit » garde notre valeur au
-- registre : il peut cacher une correction faite ensuite dans Hektor. Il doit SONNER, et l'humain doit
-- pouvoir répondre. Aujourd'hui un conflit ou un échec n'existe que dans le journal du travail.
--
-- CE QUE FAIT CE PATCH — ADDITIF, aucune fonction existante retouchée, le carnet n'est pas modifié :
--   1. app_affaire_carnet_decision : la réponse de l'humain, et notre saisie rangée quand on prend Hektor ;
--   2. app_v_affaire_carnet_ecarts : une ligne par champ en conflit, en échec, ou en attente depuis > 48 h ;
--   3. app_affaire_carnet_ecart_trancher(affaire, champ, 'hektor' | 'app' | 'attendre') — admin seulement.
-- La sentinelle data.affaire_ecart (monitoring/check_gti_health.py) lit la vue (a_traiter) ; la rubrique
-- des affaires porte les deux gestes. Pas d'interrupteur : ces objets n'écrivent que sur un geste de l'admin.
--
-- RETOUR ARRIÈRE : supabase/patch_r4_affaire_ecart_2026-10-26_INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $garde$
BEGIN
    IF to_regclass('public.app_affaire_carnet_decision') IS NOT NULL THEN
        RAISE EXCEPTION '%', 'ARRET : la table app_affaire_carnet_decision existe deja. Rien n''est ecrit.';
    END IF;
    IF to_regclass('public.app_v_affaire_carnet_ecarts') IS NOT NULL THEN
        RAISE EXCEPTION '%', 'ARRET : la vue app_v_affaire_carnet_ecarts existe deja. Rien n''est ecrit.';
    END IF;
    IF to_regprocedure('public.app_affaire_carnet_ecart_trancher(bigint,text,text)') IS NOT NULL THEN
        RAISE EXCEPTION '%', 'ARRET : la fonction app_affaire_carnet_ecart_trancher existe deja. Rien n''est ecrit.';
    END IF;
    IF to_regclass('public.app_affaire_champ_app') IS NULL OR to_regprocedure('public.app_console_current_role()') IS NULL THEN
        RAISE EXCEPTION '%', 'ARRET : le carnet ou app_console_current_role() manque. Rien n''est ecrit.';
    END IF;
END
$garde$;

-- 1. LES DÉCISIONS DE L'HUMAIN — une table à part : le carnet n'est pas touché (il a déjà quatre écrivains :
--    la création, la modification, R3, R2). « Une saisie ne se perd jamais » : quand l'humain prend la
--    valeur de Hektor, notre saisie est RANGÉE ici avant d'être retirée du carnet.
create table public.app_affaire_carnet_decision (
  id              bigserial primary key,
  app_affaire_id  bigint      not null,
  champ           text        not null,
  ecrit_le        timestamptz,                  -- la saisie DÉCIDÉE : une saisie réécrite après sonne de nouveau
  decision        text        not null check (decision in ('hektor', 'app', 'attendre')),
  valeur_app      text,                         -- notre valeur, telle que le carnet la portait
  valeur_hektor   text,                         -- celle que R3 a relue chez Hektor
  etat            text,                         -- le verdict au moment de la décision
  origine         text,
  decide_le       timestamptz not null default now(),
  decide_par      uuid
);
create index app_affaire_carnet_decision_ligne on public.app_affaire_carnet_decision (app_affaire_id, champ);
comment on table public.app_affaire_carnet_decision is
  'Chantier 8 / R4 (26/10/2026) : la reponse de l''humain a un ecart du carnet des transactions (conflit, echec, attente de plus de 48 h). hektor = notre saisie rangee ici puis retiree du carnet (la nuit reprend Hektor) ; app = on garde la notre (l''alerte se tait) ; attendre = idem pour une attente. Ecrite uniquement par app_affaire_carnet_ecart_trancher.';
alter table public.app_affaire_carnet_decision enable row level security;
revoke all on public.app_affaire_carnet_decision from public, anon, authenticated;
revoke all on sequence public.app_affaire_carnet_decision_id_seq from public, anon, authenticated;
grant select on public.app_affaire_carnet_decision to authenticated;
grant select, insert, update, delete on public.app_affaire_carnet_decision to service_role;
create policy app_affaire_carnet_decision_lecture on public.app_affaire_carnet_decision
  for select to authenticated using (public.is_app_user_active());

-- 2. LES ÉCARTS — une ligne par transaction ET par champ, jamais « N sur M » (leçon du 14/10).
--    Une saisie PARTIE chez Hektor (création ou modification) dont le verdict est « conflit » ou « échec »,
--    ou « en attente » / « inconnu » depuis plus de 48 h (le rattrapage de R3 passe chaque matin : après deux
--    matins, la preuve n'arrivera pas seule). a_traiter = aucune décision pour CETTE saisie (cet ecrit_le).
--    security_invoker : elle ne montre que ce que le lecteur a déjà le droit de lire (carnet, registre).
create view public.app_v_affaire_carnet_ecarts
  with (security_invoker = true) as
select c.app_affaire_id, l.kind, l.hektor_annonce_id, l.hektor_affaire_id, c.champ,
       c.valeur_app, c.valeur_hektor_relue as valeur_hektor, c.etat, c.origine, c.ecrit_le, c.constate_le,
       case when c.etat in ('conflit', 'echec') then c.etat else 'attente_longue' end as ecart,
       d.decision, d.decide_le,
       (d.id is null) as a_traiter
  from public.app_affaire_champ_app c
  join public.app_affaire_ledger l on l.app_affaire_id = c.app_affaire_id
  left join lateral (
        select x.id, x.decision, x.decide_le
          from public.app_affaire_carnet_decision x
         where x.app_affaire_id = c.app_affaire_id and x.champ = c.champ
           and x.ecrit_le is not distinct from c.ecrit_le
         order by x.decide_le desc
         limit 1) d on true
 where c.origine in ('creation_app', 'modification_app')
   and (c.etat in ('conflit', 'echec')
        or (c.etat in ('en_attente', 'inconnu') and c.ecrit_le < now() - interval '48 hours'));
comment on view public.app_v_affaire_carnet_ecarts is
  'Chantier 8 / R4 (26/10/2026) : les ecarts du carnet des transactions, une ligne par champ. Lue par la sentinelle data.affaire_ecart (a_traiter) et par la rubrique Affaires (les deux gestes).';
revoke all on public.app_v_affaire_carnet_ecarts from public, anon;
grant select on public.app_v_affaire_carnet_ecarts to authenticated, service_role;

-- 3. LA RÉPONSE DE L'HUMAIN — admin seulement.
--    hektor   : la saisie est rangée, puis RETIRÉE du carnet -> R2 ne la protège plus, l'écran retombe sur le
--               registre, la nuit met la valeur de Hektor. Rien n'est envoyé chez Hektor.
--    app      : (conflit, échec) la décision est rangée, l'alerte se tait ; la saisie reste, R2 la protège.
--               Corriger AUSSI Hektor, c'est le geste « Modifier », quand il est disponible.
--    attendre : (attente) la décision est rangée, l'alerte se tait ; R3 continue d'essayer chaque matin.
create or replace function public.app_affaire_carnet_ecart_trancher(p_app_affaire_id bigint, p_champ text, p_decision text)
 returns jsonb
 language plpgsql
 security definer
 set search_path to 'public'
as $f$
declare
  c public.app_affaire_champ_app%rowtype;
  v_id bigint;
begin
  if coalesce(public.app_console_current_role(), '') <> 'admin' then
    raise exception 'admin_requis' using errcode = '42501';
  end if;
  if p_decision is null or p_decision not in ('hektor', 'app', 'attendre') then
    raise exception 'decision_inconnue' using errcode = '22023';
  end if;
  select * into c from public.app_affaire_champ_app
   where app_affaire_id = p_app_affaire_id and champ = p_champ
   for update;
  if not found then
    raise exception 'ligne_introuvable' using errcode = '22023';
  end if;
  if coalesce(c.origine, '') not in ('creation_app', 'modification_app')
     or coalesce(c.etat, '') not in ('conflit', 'echec', 'en_attente', 'inconnu') then
    raise exception 'pas_un_ecart' using errcode = '22023';
  end if;
  if p_decision = 'attendre' and c.etat not in ('en_attente', 'inconnu') then
    raise exception 'attendre_reserve_a_l_attente' using errcode = '22023';
  end if;
  if p_decision = 'app' and c.etat not in ('conflit', 'echec') then
    raise exception 'garder_reserve_au_conflit_et_a_l_echec' using errcode = '22023';
  end if;
  insert into public.app_affaire_carnet_decision
         (app_affaire_id, champ, ecrit_le, decision, valeur_app, valeur_hektor, etat, origine, decide_par)
  values (c.app_affaire_id, c.champ, c.ecrit_le, p_decision, c.valeur_app, c.valeur_hektor_relue, c.etat, c.origine, auth.uid())
  returning id into v_id;
  if p_decision = 'hektor' then
    delete from public.app_affaire_champ_app where app_affaire_id = p_app_affaire_id and champ = p_champ;
  end if;
  return jsonb_build_object('decision_id', v_id, 'decision', p_decision, 'retiree_du_carnet', p_decision = 'hektor');
end
$f$;
revoke all on function public.app_affaire_carnet_ecart_trancher(bigint, text, text) from public, anon;
grant execute on function public.app_affaire_carnet_ecart_trancher(bigint, text, text) to authenticated;

-- LES CONTRÔLES — tous doivent dire OK
SELECT 1 AS "#", 'la table des decisions existe, vide ; lecture seule pour les connectes, fermee a anon' AS controle,
       CASE WHEN (SELECT count(*) FROM public.app_affaire_carnet_decision) = 0
             AND has_table_privilege('authenticated', 'public.app_affaire_carnet_decision', 'SELECT')
             AND NOT has_table_privilege('authenticated', 'public.app_affaire_carnet_decision', 'INSERT')
             AND NOT has_table_privilege('anon', 'public.app_affaire_carnet_decision', 'SELECT') THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'la vue des ecarts est lisible par les connectes et la cle de service, fermee a anon',
       CASE WHEN has_table_privilege('authenticated', 'public.app_v_affaire_carnet_ecarts', 'SELECT')
             AND has_table_privilege('service_role', 'public.app_v_affaire_carnet_ecarts', 'SELECT')
             AND NOT has_table_privilege('anon', 'public.app_v_affaire_carnet_ecarts', 'SELECT') THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'la fonction trancher : ouverte aux connectes, fermee a anon',
       CASE WHEN has_function_privilege('authenticated', 'public.app_affaire_carnet_ecart_trancher(bigint,text,text)', 'EXECUTE')
             AND NOT has_function_privilege('anon', 'public.app_affaire_carnet_ecart_trancher(bigint,text,text)', 'EXECUTE') THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 4, 'la vue se lit',
       CASE WHEN (SELECT count(*) FROM public.app_v_affaire_carnet_ecarts) >= 0 THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
